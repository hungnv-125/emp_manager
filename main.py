import json

from flask import Flask, session, redirect, \
    url_for, make_response, request, render_template, jsonify, abort
from flaskext.mysql import MySQL
from flask_bcrypt import Bcrypt
from datetime import date
from flask_socketio import SocketIO, emit, join_room, leave_room

app = Flask(__name__)
app.secret_key = 'a_SECRET_KEY'

app.config['MYSQL_DATABASE_USER'] = 'root'
app.config['MYSQL_DATABASE_PASSWORD'] = '12051999'
app.config['MYSQL_DATABASE_DB'] = 'schema_httt'
app.config['MYSQL_DATABASE_HOST'] = 'localhost'
mysql = MySQL()
mysql.init_app(app)
socketio = SocketIO(app)
bcrypt = Bcrypt()

@app.route('/')
def index():
    if 'emp' in session:
        return redirect(url_for('home'))


    return render_template('login.html')

@app.route('/chat')
def sessions():
    if 'emp' in session:
        return render_template('session.html')
    abort(401)

def messageReceived(methods=['GET', 'POST']):
    print('message was received!!!')

# @socketio.on('joined', namespace='/a')
# def joined(message):
#     # room = session['emp']['id']
#
#     join_room(room, namespace='/a')

@socketio.on('my event', namespace='/a')
def handle_my_custom_event(json, methods=['GET', 'POST']):
    print('received my event: ' + str(json))
    socketio.emit('my response', json, callback=messageReceived)




@app.route('/login', methods=['POST'])
def login():
    mail = request.form['mail']
    password = request.form['password']

    cursor = mysql.get_db().cursor()
    query = "SELECT * from employee where mail = '{}'"

    cursor.execute(query.format(mail))
    data = cursor.fetchone()

    if data is None:
        return jsonify(emp_id = None)
    else:
        if (bcrypt.check_password_hash(data[3], password)):
            data_dict = dict()
            data_dict['id'] = data[0]
            data_dict['name'] = data[1]
            data_dict['mail'] = data[2]
            session['emp'] = data_dict

            resp = make_response(jsonify({'emp_id' :data[0]}))
            resp.set_cookie('emp', json.dumps(data_dict))

            return resp

            # return jsonify(emp_id=data[0])
        return jsonify(emp_id=None)


@app.route('/logout', methods=['POST', 'GET'])
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/ajax', methods=['POST', 'GET'])
def ajax():
    return render_template('ajax.html')

# @app.route('/_add_numbers', methods=['POST', 'GET'])
# def add():
#     a = request.args.get('a', 0, type=int)
#     b = request.args.get('b', 0, type=int)
#     if a > 0:
#         return jsonify(result=a + b, check=True)
#     return jsonify(result=a + b, check=False)
#     # return redirect(url_for('index'))
#     return render_template('home.html')

@app.route('/home', methods=['POST', 'GET'])
def home():
    if 'emp' in session:
        return render_template('home.html', user=session['emp']['name'])
    abort(401)

@app.route('/update_pass', methods=['PUT'])
def update_pass():
    if 'emp' in session:
        emp_id = request.form['emp_id']
        new_pass = request.form['new_pass']

        connect = mysql.connect()
        cursor = connect.cursor()

        try:
            query = "update employee set password = '{}' where id = {}"
            cursor.execute(query.format(bcrypt.generate_password_hash(new_pass).decode('utf-8'), emp_id))
            connect.commit()
            return jsonify(success=True)
        except Exception as e:
            print(e)
            return jsonify(success=False)
        finally:
            if connect != None:
                cursor.close()
                connect.close()
    else:
        abort(401)


@app.route('/get_profile')
def get_profile():
    if 'emp' in session:
        connect = mysql.connect()
        cursor = connect.cursor()
        try:
            query = "select * from employee where id={}"
            cursor.execute(query.format(session['emp']['id']))
            employee = cursor.fetchone()
            result = dict()
            for i in range(0, len(cursor.description)):
                result[cursor.description[i][0]] = employee[i]
            result.pop('password')
            return json.loads(json.dumps(result, indent=4, sort_keys=True, default=str))
        except Exception as e:
            print(e)
            return jsonify(error=True)
        finally:
            if connect != None:
                cursor.close()
                connect.close()
    else:
        abort(401)

@app.route('/update_profile', methods=['PUT'])
def update_profile():
    if 'emp' in session:
        connect = mysql.connect()
        connect.autocommit(False)
        cursor = connect.cursor()
        query = "update employee set {} where id = {}"

        try:
            if 'name' in request.form:
                cursor.execute(query.format("name = '" + request.form['name'] +"' " , session['emp']['id']))
            if 'phone' in request.form:
                cursor.execute(query.format("phone = '" + request.form['phone'] + "' ", session['emp']['id']))
            if 'dateOfBirth' in request.form:
                cursor.execute(query.format("dateOfBirth = '" + request.form['dateOfBirth'] + "' ", session['emp']['id']))

            connect.commit()
            return jsonify(error= False)
        except Exception as e:
            print(e)
            connect.rollback()
            print("rollback")
            return jsonify(error=True)
        finally:
            if connect != None:
                cursor.close()
                connect.close()
    else:
        abort(401)



@app.route('/get_salary', methods=['GET'])
def get_salary():
    if 'emp' in session:
        emp_id = request.args.get('emp_id')
        connect = mysql.connect()
        cursor = connect.cursor()

        try:
            query = "select salary, start_date, end_date from salary where emp_id = {} order by start_date desc"
            cursor.execute(query.format(emp_id))
            data = cursor.fetchall()
            result = dict()
            for i in range(0, len(cursor.description)):
                result[cursor.description[i][0]] = data[i]
            return json.loads(json.dumps(result, sort_keys=True, indent=4 ,default=str))
        except Exception as e:
            print(e)
            return jsonify(error=True)
        finally:
            if connect != None:
                cursor.close()
                connect.close()
    else:
        abort(401)

@app.route('/get_log', methods=['GET'])
def get_log():
    if 'emp' in session:
        date = request.args.get('date')
        connect = mysql.connect()
        cursor = connect.cursor()
        try:
            query = "select * from log where date='{}' and emp_id = {}"
            cursor.execute(query.format(date,session['emp']['id']))
            log = cursor.fetchone()

            result = dict()
            for i in range(0, len(cursor.description)):
                result[cursor.description[i][0]] = log[i]
            connect.commit()

            return json.loads(json.dumps(result, sort_keys=True, indent=4 ,default=str))
        except Exception as e:
            print(e)
            return jsonify(error= True)
        finally:
            if connect != None:
                cursor.close()
                connect.close()

    else:
        abort(401)

@app.route('/admin/search_emp', methods=['GET'])
def ad_search_emp():
    key_search = request.args.get('key')
    connect = mysql.connect()
    cursor = connect.cursor()

    try:
        query = "select id, mail, name, avatar from employee where id like '{}%' or mail like '{}%' limit 10"
        cursor.execute(query.format(key_search, key_search))
        emp_list = cursor.fetchall()

        result = dict()
        result['data'] = []
        for i in range(0,len(emp_list)):
            result['data'].append(dict())
            for j in range(0, len(cursor.description)):
                result['data'][i][cursor.description[j][0]] = emp_list[i][j]

        connect.commit()
        return json.loads(json.dumps(result ,indent=4, sort_keys=True, default=str))

    except Exception as e:
        print(e)
        return jsonify(error=True)
    finally:
        if connect != None:
            cursor.close()
            connect.close()

@app.route('/admin/get_emp_profile', methods=['GET'])
def ad_get_emp_profile():
    emp_id = request.args.get('emp_id')
    connect = mysql.connect()
    cursor = connect.cursor()
    try:
        query = "select * from employee where id={}"
        cursor.execute(query.format(emp_id))
        employee = cursor.fetchone()

        result = dict()
        for i in range(0, len(cursor.description)):
            result[cursor.description[i][0]] = employee[i]
        result.pop('password')
        print('a')
        return json.loads(json.dumps(result, indent=4, sort_keys=True, default=str))
    except Exception as e:
        print(e)
        return jsonify(error=True)
    finally:
        if connect != None:
            cursor.close()
            connect.close()


@app.route('/admin/delete_emp', methods=['DELETE'])
def ad_delete_emp():
    connect = mysql.connect()
    cursor = connect.cursor()

    try:
        emp_id = request.args.get('emp_id')
        query = "delete employee where id = {}"
        cursor.execute(query.format(emp_id))
        connect.commit()
        return jsonify(error= False)
    except Exception as e:
        print(e)
        return jsonify(error=True)
    finally:
        if connect != None:
            cursor.close()
            connect.close()

@app.route('/admin/get_list_emp', methods=['GET'])
def ad_get_list_emp():
    connect = mysql.connect()
    cursor = connect.cursor()

    try:
        query = "select id, mail, name, salary, phone from employee order by id desc"
        cursor.execute(query)
        emp_list = cursor.fetchall()

        result = dict()
        result['data'] = []
        for i in range(0,len(emp_list)):
            result['data'].append(dict())
            for j in range(0, len(cursor.description)):
                result['data'][i][cursor.description[j][0]] = emp_list[i][j]

        connect.commit()
        return json.loads(json.dumps(result ,indent=4, sort_keys=True, default=str))

    except Exception as e:
        print(e)
        return jsonify(error=True)
    finally:
        if connect != None:
            cursor.close()
            connect.close()


@app.route('/admin/register')
def register_emp():
    return render_template('register.html')

# @app.route('/register_handle', methods=['POST'])
# def register():
#     mail = request.form['mail']
#     password = request.form['password']
#     name = request.form['name']
#     salary = request.form['salary']
#     phone = request.form['phone']
#     date_of_birth = request.form['dateOfBirth']
#     start_date = date.today()
#
#     connect =  mysql.connect()
#     connect.autocommit(False)
#     cursor = connect.cursor()
#
#     try:
#         insert_emp = "insert into employee (name,mail, password, salary, phone, dateOfBirth) values ('{}', '{}','{}', {},'{}','{}')"
#         pass_hash = bcrypt.generate_password_hash(password).decode('utf-8')
#
#         insert_salary = "insert into salary (emp_id, salary, start_date)" \
#                         "values ({}, {}, '{}')"
#
#         # add emp
#         cursor.execute(insert_emp.format(name, mail, pass_hash, salary, phone, date_of_birth))
#
#         # get emp_id
#         emp_id = connect.insert_id()
#
#         # add salary
#         cursor.execute(insert_salary.format(emp_id, salary, start_date ))
#
#         connect.commit()
#         return 'success'
#     except Exception as e:
#         print(e)
#         connect.rollback()
#         return 'error'
#     finally:
#         if connect != None:
#             cursor.close()
#             connect.close()

@app.route('/admin/add_emp', methods=['POST'])
def ad_add_emp():
    mail = request.form['mail']
    password = request.form['password']
    name = request.form['name']
    salary = request.form['salary']
    phone = request.form['phone']
    date_of_birth = request.form['dateOfBirth']
    start_date = date.today()

    connect = mysql.connect()
    connect.autocommit(False)
    cursor = connect.cursor()

    try:
        insert_emp = "insert into employee (name,mail, password, salary, phone, dateOfBirth) values ('{}', '{}','{}', {},'{}','{}')"
        pass_hash = bcrypt.generate_password_hash(password).decode('utf-8')

        insert_salary = "insert into salary (emp_id, salary, start_date)" \
                        "values ({}, {}, '{}')"

        # add emp
        cursor.execute(insert_emp.format(name, mail, pass_hash, salary, phone, date_of_birth))

        # get emp_id
        emp_id = connect.insert_id()

        # add salary
        cursor.execute(insert_salary.format(emp_id, salary, start_date))

        connect.commit()
        return 'success'
    except Exception as e:
        print(e)
        connect.rollback()
        return 'error'
    finally:
        if connect != None:
            cursor.close()
            connect.close()

@app.route('/admin/add_schedule', methods=['POST'])
def ad_add_schedule():
    try:
        connect = mysql.connect()
        cursor = connect.cursor()

        start_date = request.form['start_date']
        start_tine_in = request.form['start_time_in']
        start_tine_out = request.form['start_time_out']
        end_tine_in = request.form['end_time_in']
        end_tine_out = request.form['end_time_out']
        correct_time_in = request.form['correct_time_in']
        correct_time_out = request.form['correct_time_out']

        check_start_date = "select * from timekeeping_schedule where start_date <= '{}' and end_date >= '{}'"
        update_end_date = "update timekeeping_schedule set end_date = '{}' where id = (select max(id) from timekeeping_schedule)"
        insert = "insert into timekeeping_schedule " \
                 "(start_date, start_time_in, start_time_out, end_time_in, end_time_out, correct_time_in, correct_time_out)"

        cursor.execute(check_start_date.format(start_date))
        if cursor.fetchone() == None:
            return jsonify(error =True)

        cursor.execute(update_end_date.format(start_date))
        cursor.execute(insert.format(start_date, start_tine_in, start_tine_out, end_tine_in, end_tine_out, correct_time_in, correct_time_out))

        connect.commit()
        return jsonify(error=False)

    except Exception as e:
        print(e)
        return jsonify(error = True)
    finally:
        if connect != None:
            cursor.close()
            connect.close()

@app.route('/admin/get_log', methods=['GET'])
def ad_get_log():
    # connect = mysql.connect()
    # cursor = connect.cursor()

    try:
        connect = mysql.connect()
        cursor = connect.cursor()
        emp_id = request.args.get('emp_id')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')

        query = "select date, tag_in, tag_out, is_correct_face_in, is_correct_face_out  from log " \
                "where emp_id = {} and (date between '{}' and '{}') order by date desc"
        cursor.execute(query.format(emp_id, start_date, end_date))
        log_list = cursor.fetchall()

        result = dict()
        result['data'] = []
        for i in range(0, len(log_list)):
            result['data'].append(dict())
            for j in range(0, len(cursor.description)):
                result['data'][i][cursor.description[j][0]] = log_list[i][j]

        connect.commit()
        return json.loads(json.dumps(result ,indent=4, sort_keys=True, default=str))

    except Exception as e:
        print(e)
        return jsonify(error= True)
    finally:
        if connect !=None:
            cursor.close()
            connect.close()


@app.route('/admin/get_log_detail', methods=['GET'])
def ad_get_log_detail():
    connect = mysql.connect()
    cursor = connect.cursor()

    try:
        emp_id = request.args.get('emp_id')
        date = request.args.get('date')

        query = "select * from log where emp_id = {} and date = '{}'"
        cursor.execute(query.format(emp_id, date))
        log = cursor.fetchone()

        result =dict()
        for i in range(0, len(cursor.description)):
            result[cursor.description[i][0]] = log[i]

        timekeeping_schedule_id = result['schedule_id']

        query_schedule = "select correct_time_in, correct_time_out from timekeeping_schedule where id = {}"
        cursor.execute(query_schedule.format(timekeeping_schedule_id))
        schedule_time = cursor.fetchone()

        result['correct_time_in'] = schedule_time[0]
        result['correct_time_out'] = schedule_time[1]

        connect.commit()

        return json.loads(json.dumps(result, indent=4, sort_keys=True, default=str))

    except Exception as e:
        print(e)
        return jsonify(error=True)
    finally:
        if connect != None:
            cursor.close()
            connect.close()

@app.route('/admin/get_log_all', methods=['GET'])
def ad_get_log_all():
    try:
        connect = mysql.connect()
        cursor = connect.cursor()

        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')

        query = "select employee.id, employee.name , date, tag_in, tag_out, is_correct_face_in, is_correct_face_out  from  employee ,log " \
                "where employee.id = log.emp_id and (date between '{}' and '{}') order by employee.id ,date"
        cursor.execute(query.format(start_date, end_date))
        logs = cursor.fetchall()

        result = dict()
        result['data'] = []
        for i in range(0, len(logs)):
            result['data'].append(dict())
            for j in range(0, len(cursor.description)):
                result['data'][i][cursor.description[j][0]] = logs[i][j]

        connect.commit()
        return json.loads(json.dumps(result, indent=4, sort_keys=True, default=str))

    except Exception as e:
        print(e)
        return jsonify(error=True)
    finally:
        if connect !=None:
            cursor.close()
            connect.close()

@app.route('/admin/get_salary', methods=['GET'])
def ad_get_salary():
    connect = mysql.connect()
    cursor = connect.cursor()

    try:
        emp_id = request.args.get('emp_id')
        today= date.today()

        query = "select emp_id, salary from schema_httt.salary where emp_id = {} and '{}' >= start_date and '{}' < end_date"
        cursor.execute(query.format(emp_id, today, today))
        data = cursor.fetchone()

        result = dict()
        for i in range(0, len(cursor.description)):
            result[cursor.description[i][0]] = data[i]

        connect.commit()

        return json.loads(json.dumps(result, indent=4, sort_keys=True, default=str))
    except Exception as e:
        print(e)
        return jsonify(error=True)
    finally:
        if connect != None:
            cursor.close()
            connect.close()

@app.route('/admin/update_salary', methods=['PUT'])
def ad_update_salary():
    connect = mysql.connect()
    cursor = connect.cursor()

    try:
        emp_id = request.args.get('emp_id')
        salary = request.args.get('salary')
        start_date = request.args.get('start_date')

        check_date = "select * from salary where emp_id = {} and start_date > '{}'"
        cursor.execute(check_date.format(emp_id, start_date))

        if cursor.fetchone() != None:
            return jsonify(error = True)

        update_salary = "update salary set end_date = '{}' where emp_id= {} and end_date ='9999-01-01'"
        cursor.execute(update_salary.format(start_date, emp_id))

        insert_salary = "insert into salary (emp_id, salary, start_date) values ({}, {}, '{}')"
        cursor.execute(insert_salary.format(emp_id, salary, start_date))

        connect.commit()
        return jsonify(error=False)
    except Exception as e:
        print(e)
        connect.rollback()
        print("rollback")
        return jsonify(error=True)
    finally:
        if connect != None:
            cursor.close()
            connect.close()





if __name__ == '__main__':
   socketio.run(app, debug = True)
import sqlite3
from io import BytesIO
import uuid
import qrcode
import base64
import json
from flask import Flask, session, render_template, redirect, url_for, request, jsonify, flash, make_response

app = Flask(__name__)

# Change this to your secret key (can be anything, it's for extra protection)
app.secret_key = 'mysecretkey'

# create database connection
conn = sqlite3.connect('./database/wp3.db')
c = conn.cursor()

# render index template
@app.route('/')
def index():
    return render_template('index.html')

# Render calendar template
@app.route('/calendar')
def calendar():
    return render_template('calendar.html')

# Render meetings template
@app.route('/meetings')
def meetings():
    return render_template('meetings.html')

# Render students template
@app.route('/students')
def students():
    return render_template('students.html')

# Render teachers template
@app.route('/teachers')
def teachers():
    return render_template('teachers.html')

# Render classes template
@app.route('/classes')
def classes():
    return render_template('classes.html')

# login
LOGIN_ROUTE = '/login'
@app.route('/dashboard')
def dashboard():
    if session.get('username') is None:
        return redirect(LOGIN_ROUTE)
    else:
        username = session.get('username', '')
        return render_template('dashboard.html', user=username)

# register
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = sqlite3.connect('./database/wp3.db')
        c = conn.cursor()
        c.execute('SELECT * FROM students WHERE username = ?', (username,))
        existing_user = c.fetchone()
        if existing_user:
            return 'That username is already taken!'
        else:
            c.execute('INSERT INTO students VALUES (?, ?)', (username, password))
            conn.commit()
            conn.close()
            return redirect('/')
    return render_template('register.html')

# login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '')
        password = request.form.get('password', '')
        with sqlite3.connect('./database/wp3.db') as conn:
            c = conn.cursor()
            c.execute('SELECT * FROM students WHERE username = ? AND password = ?', (username, password))
            user = c.fetchone()
        if user is None:
            return render_template('login.html', error='Invalid username or password')
        else:
            session['username'] = username
            return redirect('/dashboard')
    return render_template('login.html')

# Handle GET requests to fetch events
@app.route('/events')
def get_events():
    conn = sqlite3.connect('./database/wp3.db')
    c = conn.cursor()
    c.execute('SELECT id, title, start, end FROM events')
    events = [{'id': row[0], 'title': row[1], 'start': row[2], 'end': row[3]} for row in c.fetchall()]
    conn.close()
    return jsonify(events)

# Handle POST requests to create or update events
@app.route('/events', methods=['POST'])
def create_event():
    data = request.get_json()
    title = data['title']
    start = data['start']
    end = data['end']
    if data.get('id'):
        id = data['id']
        conn = sqlite3.connect('./database/wp3.db')
        c = conn.cursor()
        c.execute('UPDATE events SET title=?, start=?, end=? WHERE id=?', (title, start, end, id))
        conn.commit()
        conn.close()
    else:
        conn = sqlite3.connect('./database/wp3.db')
        c = conn.cursor()
        c.execute('INSERT INTO events (title, start, end) VALUES (?, ?, ?)', (title, start, end))
        id = c.lastrowid
        conn.commit()
        conn.close()
        data['id'] = id
    return jsonify(data)

# Get a specific event by ID
@app.route('/events/<int:event_id>', methods=['GET'])
def get_event(event_id):
    conn = sqlite3.connect('./database/wp3.db')
    cur = conn.cursor()
    cur.execute('SELECT * FROM events WHERE id = ?', (event_id,))
    event = cur.fetchone()
    if event:
        event_dict = {
            'id': event[0],
            'title': event[1],
            'start': event[2],
            'end': event[3]
        }
        return jsonify(event_dict)
    else:
        return jsonify({'error': 'Event not found'}), 404

# Delete an event by id
@app.route('/events/<int:event_id>', methods=['DELETE'])
def delete_event(event_id):
    # Connect to the database
    conn = sqlite3.connect('./database/wp3.db')
    c = conn.cursor()
    
    # Delete the event with the given id
    c.execute('DELETE FROM events WHERE id = ?', (event_id,))
    conn.commit()
    
    # Check if an event was deleted
    if c.rowcount > 0:
        result = {'message': 'Event deleted successfully'}
        status = 200
    else:
        result = {'error': 'Event not found'}
        status = 404
    
    # Close the database connection
    conn.close()
    
    # Return a JSON response
    return jsonify(result), status

# Create a new meeting
@app.route('/meeting', methods=['POST'])
def create_meeting():
    data = request.get_json()
    conn = sqlite3.connect('./database/wp3.db')
    c = conn.cursor()
    c.execute("INSERT INTO meetings (title, teacher, date, time) VALUES (?, ?, ?, ?)",
              (data['title'], data['teacher'], data['date'], data['time']))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Meeting created successfully'})

# Get a specific meeting
@app.route('/meeting/<id>', methods=['GET'])
def get_meeting(id):
    conn = sqlite3.connect('./database/wp3.db')
    c = conn.cursor()
    c.execute("SELECT * FROM meetings WHERE id=?", (id,))
    meeting = c.fetchone()
    conn.close()

    if meeting:
        meeting_dict = {
            'id': meeting[0],
            'title': meeting[1],
            'teacher': meeting[2],
            'date': meeting[3],
            'time': meeting[4]
        }
        return jsonify(meeting_dict)
    else:
        return jsonify({'error': 'Meeting not found'})

# Show all meetings
@app.route('/meeting', methods=['GET'])
def get_all_meetings():
    conn = sqlite3.connect('./database/wp3.db')
    c = conn.cursor()
    c.execute("SELECT * FROM meetings")
    meetings = c.fetchall()
    conn.close()
    # Convert the list of tuples to a list of dictionaries
    meetings_dict = [dict(zip(('id', 'title', 'teacher', 'date', 'time'), m)) for m in meetings]
    return jsonify(meetings_dict)

# Show all meetings for a teacher
@app.route('/meeting/<teacher>', methods=['GET'])
def get_meetings_by_teacher(teacher):
    conn = sqlite3.connect('./database/wp3.db')
    c = conn.cursor()
    c.execute("SELECT * FROM meetings WHERE teacher=?", (teacher,))
    meetings = c.fetchall()
    conn.close()
    return jsonify(meetings)

# Update a meeting
@app.route('/meeting/<id>', methods=['PUT'])
def update_meeting(id):
    data = request.get_json()
    if isinstance(data, dict):
        conn = sqlite3.connect('./database/wp3.db')
        c = conn.cursor()
        c.execute("""
            UPDATE meetings
            SET title=?, teacher=?, date=?, time=?
            WHERE id=?
        """, (data['title'], data['teacher'], data['date'], data['time'], id))
        conn.commit()
        conn.close()
        return jsonify({'message': 'Meeting updated successfully'})
    else:
        return jsonify({'error': 'Invalid data format'})

# Checkin?
# @app.route('/meeting/<id>/checkin', methods=['PUT'])
# def update_meeting_checkin(id):
#     data = request.get_json()
#     conn = sqlite3.connect('./database/wp3.db')
#     c = conn.cursor()
#     c.execute("UPDATE meetings SET student_checkin=? WHERE id=?",
#               (data['student_checkin'], id))
#     conn.commit()
#     conn.close()
#     return jsonify({'message': 'Meeting check-in updated successfully'})

# delete meeting
@app.route('/meeting/<id>', methods=['DELETE'])
def delete_meeting(id):
    conn = sqlite3.connect('./database/wp3.db')
    c = conn.cursor()
    c.execute("DELETE FROM meetings WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Meeting deleted successfully'})

# show student
@app.route('/student', methods=['GET'])
def get_students():
    conn = sqlite3.connect('./database/wp3.db')
    conn.cursor()
    students = conn.execute('SELECT * FROM students').fetchall()
    conn.commit()
    conn.close()
    return jsonify([{'id': row[0], 'name': row[1]} for row in students])

# save a student
@app.route('/student', methods=['POST'])
def create_student():
    conn = sqlite3.connect('./database/wp3.db')
    data = request.json
    conn.execute('INSERT INTO students (username) VALUES (?)', (data['name'],))
    conn.commit()
    student_id = conn.execute('SELECT last_insert_rowid()').fetchone()[0]
    conn.close()
    message = f"Student {data['name']} has been created"
    response = {'id': student_id, 'name': data['name'], 'message': message}
    return jsonify(response)

# show a specific student with all their checkins?
# @app.route('/student/<int:student_id>', methods=['GET'])
# def get_student(student_id):
#     conn = sqlite3.connect('./database/wp3.db')
#     student = conn.execute('SELECT * FROM students WHERE id = ?', (student_id,)).fetchone()
#     checkins = conn.execute('SELECT * FROM checkins WHERE student_id = ?', (student_id,)).fetchall()
#     conn.close()
#     if student is None:
#         return jsonify({'error': 'Student not found'}), 404
#     return jsonify({
#         'id': student['id'],
#         'name': student['name'],
#         'checkins': [dict(row) for row in checkins]
#     })

# delete student
@app.route('/student/<int:student_id>', methods=['DELETE'])
def delete_student(student_id):
    conn = sqlite3.connect('./database/wp3.db')
    conn.execute('DELETE FROM students WHERE id = ?', (student_id,))
    conn.commit()
    conn.close()
    message = f"Student with ID {student_id} has been deleted."
    response = {'message': message}
    return jsonify(response), 204

# get teacher
@app.route('/teacher', methods=['GET'])
def get_teachers():
    conn = sqlite3.connect('./database/wp3.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM teachers')
    rows = cursor.fetchall()
    conn.close()
    return jsonify(rows)

# save teacher
@app.route('/teacher', methods=['POST'])
def save_teacher():
    conn = sqlite3.connect('./database/wp3.db')
    cursor = conn.cursor()
    cursor.execute('INSERT INTO teachers (username, password, name) VALUES (?, ?, ?)', (request.json['username'], request.json['password'], request.json['name']))
    conn.commit()
    new_teacher_id = cursor.lastrowid
    conn.close()
    return jsonify({'id': new_teacher_id})

# show specific teacher
@app.route('/teacher/<int:id>', methods=['GET'])
def get_teacher(id):
    conn = sqlite3.connect('./database/wp3.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM teachers WHERE id = ?', (id,))
    row = cursor.fetchone()
    conn.close()
    if row is None:
        return jsonify({'error': 'Teacher not found'}), 404
    return jsonify(row)

# update teacher
@app.route('/teacher/<int:id>', methods=['PUT'])
def update_teacher(id):
    conn = sqlite3.connect('./database/wp3.db')
    cursor = conn.cursor()
    cursor.execute('UPDATE teachers SET username = ?, password = ?, name = ? WHERE id = ?', (request.json['username'], request.json['password'], request.json['name'], id))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

# delete teacher
@app.route('/teacher/<int:id>', methods=['DELETE'])
def delete_teacher(id):
    conn = sqlite3.connect('./database/wp3.db')
    cursor = conn.cursor()
    cursor.execute('DELETE FROM teachers WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

# get all classes
@app.route('/class', methods=['GET'])
def get_all_classes():
    conn = sqlite3.connect('./database/wp3.db')
    c = conn.cursor()

    c.execute("SELECT * FROM classes")
    classes = c.fetchall()

    conn.close()
    return jsonify(classes)

# save classes
@app.route('/class', methods=['POST'])
def save_class():
    class_name = request.json['class_name']

    conn = sqlite3.connect('./database/wp3.db')
    c = conn.cursor()

    c.execute("INSERT INTO classes (class_name) VALUES (?)", (class_name,))
    class_id = c.lastrowid

    conn.commit()
    conn.close()
    return jsonify({'class_id': class_id, 'class_name': class_name})

# get classes
@app.route('/class/<int:class_id>', methods=['GET'])
def get_class(class_id):
    conn = sqlite3.connect('./database/wp3.db')
    c = conn.cursor()

    c.execute("SELECT * FROM classes WHERE class_id=?", (class_id,))
    class_info = c.fetchone()

    c.execute("SELECT * FROM students WHERE class_id=?", (class_id,))
    students = c.fetchall()

    conn.close()
    return jsonify({'class_info': class_info, 'students': students})

# update classes
@app.route('/class/<int:class_id>', methods=['PUT'])
def update_class(class_id):
    class_name = request.json['class_name']
    students = request.json['students']

    conn = sqlite3.connect('./database/wp3.db')
    c = conn.cursor()

    c.execute("UPDATE classes SET class_name=? WHERE class_id=?", (class_name, class_id))

    c.execute("DELETE FROM students WHERE class_id=?", (class_id,))
    for student in students:
        c.execute("INSERT INTO students (student_name, class_id) VALUES (?, ?)", (student, class_id))

    conn.commit()
    conn.close()
    return jsonify({'class_id': class_id, 'class_name': class_name, 'students': students})

# delete classes
@app.route('/class/<int:class_id>', methods=['DELETE'])
def delete_class(class_id):
    conn = sqlite3.connect('./database/wp3.db')
    c = conn.cursor()

    c.execute("DELETE FROM classes WHERE class_id=?", (class_id,))
    c.execute("DELETE FROM students WHERE class_id=?", (class_id,))

    conn.commit()
    conn.close()
    return jsonify({'message': 'Class deleted successfully'})

# QR code
@app.route("/checkin")
def check_in():
    connection = sqlite3.connect('./database/wp3.db')
    # Generate a new QR code with a unique ID and URL
    code = str(uuid.uuid4())
    url = "http://127.0.0.1:5000/form/" + code

    cursor = connection.cursor()
    try:
        cursor.execute("INSERT INTO qr_codes (id, data) VALUES (?, ?)", (code, "example"))
        connection.commit()
    except Exception as e:
        connection.rollback()
        raise e
    finally:
        cursor.close()

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = BytesIO()
    img.save(buffer, "PNG")
    qr_code = base64.b64encode(buffer.getvalue()).decode("utf-8")

    return render_template("checkin.html", qr_code=qr_code, url=url)

# Insert QR code data
# @app.route("/form/<code>", methods=["GET", "POST"])
# def form(code):
#     connection = sqlite3.connect('./database/wp3.db', check_same_thread = False)
#     connection.row_factory = sqlite3.Row

#     # Check if the code has already been used
#     cursor = connection.cursor()
#     used = cursor.execute("SELECT * FROM attendance WHERE qr_code_id=?", (code,)).fetchone()
#     if used:
#         connection.close()
#         return render_template("failure.html", message="QR code has already been used.")

#     if request.method == "POST":
#         username = request.form["username"]
#         password = request.form["password"]
#         #
#         student = cursor.execute("SELECT * FROM students WHERE username=?", (username,)).fetchone()
#         #
#         # Check if the student's information is correct
#         if student and student[1] == password:
#             check_in_time = datetime.datetime.now()
#             connection.execute("INSERT INTO attendance (qr_code_id, student_id, check_in_time) VALUES (?, ?, ?)", (code, username, check_in_time))
#             connection.commit()
#             connection.close()
#             return render_template("success.html")
#         else:
#             connection.close()
#             return render_template("failure.html", message="Incorrect username or password.")
#     else:
#         return render_template("form.html", code=code)

# logout page
@app.route('/logout')
def logout():
   # remove session data, this will log the user out
   session.pop('loggedin', None)
   session.pop('id', None)
   session.pop('username', None)
   # session.pop('role', None)
   # redirect to login page
   return redirect(url_for('login'))

# run python application
if __name__ == '__main__':
    app.run(debug=True)
    app.run()


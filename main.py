import sqlite3
from io import BytesIO
import uuid
import qrcode
import base64
from flask import Flask, session, render_template, redirect, url_for, request, jsonify, flash, make_response

app = Flask(__name__)

# Change this to your secret key (can be anything, it's for extra protection)
app.secret_key = 'mysecretkey'

# create database connection
conn = sqlite3.connect('./database/wp3.db')
c = conn.cursor()

# login
LOGIN_ROUTE = '/login'
@app.route('/dashboard')
def dashboard():
    if session.get('username') is None:
        return redirect(LOGIN_ROUTE)
    else:
        username = session.get('username', '')
        return render_template('dashboard.html', user=username)

# Render meetings template
@app.route('/meetings')
def meetings():
    if session.get('username') is None:
        return redirect(LOGIN_ROUTE)
    else:
        username = session.get('username', '')
        return render_template('meetings.html', user=username)

# Render students template
@app.route('/students')
def students():
    if session.get('username') is None:
        return redirect(LOGIN_ROUTE)
    else:
        username = session.get('username', '')
        return render_template('students.html', user=username)

# @app.route('/checkin')
# def checkin():
#     code = request.args.get('code')
#     return render_template('checkin.html', code=code)


# render index template
# @app.route('/')
# def index():
#     return render_template('index.html')

# render index template
# @app.route('/attendance')
# def attendance():
#     return render_template('attendance.html')

# Render calendar template
@app.route('/calendar')
def calendar():
    return render_template('calendar.html')

# Render teachers template
@app.route('/teachers')
def teachers():
    return render_template('teachers.html')

# Render classes template
@app.route('/classes')
def classes():
    return render_template('classes.html')

# Render form template
@app.route("/form")
def show_form():
    return render_template("form.html")

# Render attendance template
@app.route('/attendance')
def attendance():
    return render_template('attendance.html')

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
@app.route('/v1/events')
def get_events():
    conn = sqlite3.connect('./database/wp3.db')
    c = conn.cursor()
    c.execute('SELECT id, title, start, end FROM events')
    events = [{'id': row[0], 'title': row[1], 'start': row[2], 'end': row[3]} for row in c.fetchall()]
    conn.close()
    return jsonify(events)

# Handle POST requests to create or update events
@app.route('/v1/events', methods=['POST'])
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
@app.route('/v1/events/<int:event_id>', methods=['GET'])
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
@app.route('/v1/events/<int:event_id>', methods=['DELETE'])
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
@app.route('/v1/meeting', methods=['POST'])
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
@app.route('/v1/meeting/<id>', methods=['GET'])
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

# get meetings
@app.route("/v1/meeting")
def get_meetings():
    connection = sqlite3.connect("./database/wp3.db")
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()

    # Fetch meetings data along with check-ins for each meeting using a JOIN query
    cursor.execute("""
         SELECT m.id, m.title, m.teacher, m.date, m.time,
       GROUP_CONCAT(CASE WHEN a.status = 'present' THEN c.student_id ELSE NULL END) AS present,
       GROUP_CONCAT(CASE WHEN a.status = 'absent' THEN c.student_id ELSE NULL END) AS absent
FROM meetings m
LEFT JOIN checkins a ON m.id = a.meeting_id
LEFT JOIN checkins c ON a.id = c.id AND a.meeting_id = c.meeting_id
GROUP BY m.id
    """)

    # Convert data to a list of dictionaries and return as JSON
    meetings = [dict(row) for row in cursor.fetchall()]
    data = {"meetings": meetings}
    return jsonify(data)


# Show all meetings
# @app.route('/v1/meeting', methods=['GET'])
# def get_all_meetings():
#     conn = sqlite3.connect('./database/wp3.db')
#     c = conn.cursor()
#     c.execute("SELECT m.id, m.title, m.teacher, m.date, m.time, COUNT(c.id) AS total_checkins, COUNT(CASE WHEN c.status = 'present' THEN 1 END) AS present_count FROM meetings m LEFT JOIN checkins c ON m.id = c.meeting_id LEFT JOIN students s ON c.student_id = s.id GROUP BY m.id")
#     meetings = c.fetchall()
#     conn.close()
#     # Convert the list of tuples to a list of dictionaries
#     meetings_dict = [dict(zip(('id', 'title', 'teacher', 'date', 'time', 'total_checkins', 'present_count'), m)) for m in meetings]
#     return jsonify(meetings_dict)

# Show all meetings for a teacher
@app.route('/v1/meeting/<teacher>', methods=['GET'])
def get_meetings_by_teacher(teacher):
    conn = sqlite3.connect('./database/wp3.db')
    c = conn.cursor()
    c.execute("SELECT * FROM meetings WHERE teacher=?", (teacher,))
    meetings = c.fetchall()
    conn.close()
    return jsonify(meetings)

# Update a meeting
@app.route('/v1/meeting/<id>', methods=['PUT'])
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
# Update a meeting with a checkin from a student
# @app.route('/meeting/<meetingId>', methods=['PATCH'])
# def update_meeting_checkin(meetingId):
#     data = request.get_json()
#     if isinstance(data, dict):
#         conn = sqlite3.connect('./database/wp3.db')
#         c = conn.cursor()
#         c.execute("""
#             UPDATE meetings
#             SET checkin=?
#             WHERE id=?
#         """, (data['checkin'], meetingId))
#         conn.commit()
#         conn.close()
#         return jsonify({'message': 'Check-in updated successfully'})
#     else:
#         return jsonify({'error': 'Invalid data format'})

# delete meeting
@app.route('/v1/meeting/<id>', methods=['DELETE'])
def delete_meeting(id):
    conn = sqlite3.connect('./database/wp3.db')
    c = conn.cursor()
    c.execute("DELETE FROM meetings WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Meeting deleted successfully'})

# show student
@app.route('/v1/student', methods=['GET'])
def get_students():
    conn = sqlite3.connect('./database/wp3.db')
    conn.cursor()
    students = conn.execute('SELECT * FROM students').fetchall()
    conn.commit()
    conn.close()
    return jsonify([{'id': row[0], 'name': row[1], 'password': row[2], 'student_name': row[3] , 'class_id': [row[4]]} for row in students])

# create a student
@app.route('/v1/student', methods=['POST'])
def create_student():
    conn = sqlite3.connect('./database/wp3.db')
    data = request.json
    conn.execute('INSERT INTO students (username, password, email, class_id) VALUES (?, ?, ?, ?)', (data['username'], data['password'], data['email'], data['class_id']))
    conn.commit()
    student_id = conn.execute('SELECT last_insert_rowid()').fetchone()[0]
    conn.close()
    message = f"Student {data['username']} has been created"
    response = {'id': student_id, 'name': data['username'],  'password': data['password'], 'message': message}
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
@app.route('/v1/student/<int:student_id>', methods=['DELETE'])
def delete_student(student_id):
    conn = sqlite3.connect('./database/wp3.db')
    conn.execute('DELETE FROM students WHERE id = ?', (student_id,))
    conn.commit()
    conn.close()
    message = f"Student with ID {student_id} has been deleted."
    response = {'message': message}
    return jsonify(response), 204

# get teacher
@app.route('/v1/teacher', methods=['GET'])
def get_teachers():
    conn = sqlite3.connect('./database/wp3.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM teachers')
    rows = cursor.fetchall()
    conn.close()

    # Convert rows to a list of dictionaries
    teachers = []
    for row in rows:
        teacher = {'id': row[0], 'username': row[1], 'password': row[2], 'email': row[3]}
        teachers.append(teacher)

    return jsonify(teachers)

# save teacher
@app.route('/v1/teacher', methods=['POST'])
def save_teacher():
    conn = sqlite3.connect('./database/wp3.db')
    cursor = conn.cursor()
    cursor.execute('INSERT INTO teachers (username, password, email) VALUES (?, ?, ?)', (request.json['username'], request.json['password'], request.json['email']))
    conn.commit()
    new_teacher_id = conn.execute('SELECT last_insert_rowid()').fetchone()[0]
    conn.close()
    return jsonify({'id': new_teacher_id})

# show specific teacher
@app.route('/v1/teacher/<int:id>', methods=['GET'])
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
@app.route('/v1/teacher/<int:id>', methods=['PUT'])
def update_teacher(id):
    conn = sqlite3.connect('./database/wp3.db')
    cursor = conn.cursor()
    cursor.execute('UPDATE teachers SET username = ?, password = ?, name = ? WHERE id = ?', (request.json['username'], request.json['password'], request.json['name'], id))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

# delete teacher
@app.route('/v1/teacher/<int:id>', methods=['DELETE'])
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
@app.route('/')
@app.route("/checkin", methods=["GET"])
def check_in():
    connection = sqlite3.connect('./database/wp3.db')
    cursor = connection.cursor()

    # Generate a new QR code with a unique ID and URL
    code = str(uuid.uuid4())
    url = "/form?code=" + code

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
        box_size=12,
        border=2,
    )
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = BytesIO()
    img.save(buffer, "PNG")
    qr_code = base64.b64encode(buffer.getvalue()).decode("utf-8")

    return render_template("checkin.html", qr_code=qr_code, url=url)

# route for submitting the check-in form
@app.route("/v1/form/<code>", methods=['POST'])
def submit_form(code):
    
        request_data = request.get_json()

        meeting_id = request_data["meeting_id"]
        student_id = request_data["student_id"]
        checkin_time = request_data["checkin_time"]
        question_answer = request_data["question_answer"]
        
        status = request_data["status"]
        
        connection = sqlite3.connect("./database/wp3.db")
        cursor = connection.cursor()
        cursor.execute("INSERT INTO checkins (student_id, checkin_time, question_answer, qr_code_id, meeting_id, status) VALUES (?, ?, ?, ?, ?, ?)", (student_id, checkin_time, question_answer, code, meeting_id, status))
        connection.commit()
        cursor.close()
        
        return jsonify({'message': f'Student {student_id} checked in at {checkin_time} with status {status}'}), 200

@app.route('/v1/attendance', methods=['GET'])
def get_attendance():
    conn = sqlite3.connect('./database/wp3.db')
    conn.cursor()
    checkins = conn.execute('SELECT * FROM checkins').fetchall()
    conn.commit()
    conn.close()
    return jsonify([{'id': row[0], 'student_id': row[2], 'qr_code_id': row[1], 'checkin_time': row[3] , 'question_answer': row[4], 'meeting_id': row[5],'status': [row[6]]} for row in checkins])

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

# show attendance
# @app.route('/v1/attendance', methods=['GET'])
# def get_attendance():
#     conn = sqlite3.connect('./database/wp3.db')
#     conn.cursor()
#     attendance = conn.execute('SELECT * FROM attendance').fetchall()
#     conn.commit()
#     conn.close()
#     return jsonify([{'id': row[0], 'student_id': row[1], 'qr_code_id': row[2], 'check_in_time': row[3] , 'status': [row[4]]} for row in attendance])

# run python application
if __name__ == '__main__':
    app.run(debug=True)
    app.run()




from flask import Flask, request, jsonify
from addFaces import add_new_face
from demo1 import recognize_and_mark_attendance
from flask_cors import CORS
import threading
import time
import globals  
import os
from flask import send_from_directory
from datetime import datetime
from authMiddleware import token_required
import psycopg2
import dotenv
import os
dotenv.load_dotenv()
import pandas as pd
import os


app = Flask(__name__)
CORS(app)


camera_thread_instance = None


# def camera_thread(subject_name):
#     globals.camera_active = True  
#     while globals.camera_active:
#         result = recognize_and_mark_attendance(subject_name)
#         print(f"Attendance Updated: {result}")  
#         time.sleep(2)  


def camera_thread(subject, dept, division, session_id):
    globals.camera_active = True  

    while globals.camera_active:
        result = recognize_and_mark_attendance(
            subject, dept, division, session_id
        )
        print("Updated:", result)
        time.sleep(2)


@app.route("/add-face", methods=["POST"])
@token_required(roles=["faculty"])
def api_add_face():
    data = request.json
    print(data)

    roll_no = data.get("roll_no")
    name = data.get("stud_name")
    dept = data.get("stud_dept")       
    division = data.get("stud_div") 

    # 🔥 validation
    if not roll_no or not name or not dept or not division:
        return jsonify({
            "error": "roll_no, name, dept, and division are required"
        }), 400

    # 🔥 call updated function
    result = add_new_face(roll_no, name, dept, division)

    return jsonify(result)





@app.route("/camera-on", methods=["POST"])
@token_required(roles=["faculty"])
def camera_on():
    global camera_thread_instance

    data = request.json
    subject = data.get("subject")
    division = data.get("division")

    # 🔥 get from JWT
    dept = request.user.get("fac_dept")
    faculty_id = request.user.get("fac_id")

    print(dept, subject, division, faculty_id)

    if not subject or not division:
        return jsonify({"error": "Subject and division required"}), 400

    if globals.camera_active:
        return jsonify({"message": "Camera already running"}), 400

    conn = None
    cursor = None

    try:
        conn = psycopg2.connect(
    dbname=os.getenv("DB_NAME"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    host=os.getenv("DB_HOST"),
    port=os.getenv("DB_PORT")
)
        cursor = conn.cursor()

        # 🔥 create attendance session
        cursor.execute("""
            INSERT INTO attendance_sessions (subject, dept, division, faculty_id)
            VALUES (%s, %s, %s, %s)
            RETURNING id
        """, (subject, dept, division, faculty_id))

        session_id = cursor.fetchone()[0]
        conn.commit()

        print(f"✅ Session created: {session_id}")

    except Exception as e:
        if conn:
            conn.rollback()
        return jsonify({"error": str(e)}), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

    # 🔥 start camera thread
    globals.camera_active = True

    camera_thread_instance = threading.Thread(
        target=camera_thread,
        args=(subject, dept, division, session_id),
        daemon=True   # ✅ important (auto cleanup)
    )
    camera_thread_instance.start()

    return jsonify({
        "message": "Camera started successfully",
        "session_id": session_id,
        "subject": subject,
        "dept": dept,
        "division": division
    })


@app.route("/camera-off", methods=["POST"])
@token_required(roles=["faculty"])  # Only faculty and admin can stop the camera
def camera_off():
    global camera_thread_instance

    if not globals.camera_active:
        return jsonify({"message": "Camera is not running."})

    globals.camera_active = False  

    if camera_thread_instance:
        camera_thread_instance.join()  

    return jsonify({"message": "Camera stopped and attendance updated."})


@app.route("/attendance-report", methods=["POST"])
@token_required(roles=["faculty"])
def generate_report():
    print("route hit")

    data = request.json
    subject = data.get("subject")
    division = data.get("division")
    dept = request.user.get("fac_dept")
    print(dept, subject, division)

    conn = psycopg2.connect(
    dbname=os.getenv("DB_NAME"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    host=os.getenv("DB_HOST"),
    port=os.getenv("DB_PORT")
)
    cursor = conn.cursor()
    print("DB_NAME:", os.getenv("DB_NAME"))
    print("DB_USER:", os.getenv("DB_USER"))
    print("DB_PASSWORD:", os.getenv("DB_PASSWORD"))
    print("DB_HOST:", os.getenv("DB_HOST"))
    print("DB_PORT:", os.getenv("DB_PORT"))

    
    cursor.execute("""
        SELECT roll_no, stud_name
        FROM student_info
        WHERE stud_dept = %s AND stud_div = %s
        ORDER BY roll_no
    """, (dept, division))
    students = cursor.fetchall()

    cursor.execute("""
        SELECT id, session_date
        FROM attendance_sessions
        WHERE subject = %s AND dept = %s AND division = %s
        ORDER BY session_date, id
    """, (subject, dept, division))
    sessions = cursor.fetchall()

    

    df = pd.DataFrame(students, columns=["Roll No", "Name"])

    
    present_count_map = {roll_no: 0 for roll_no, _ in students}

   
    for idx, (session_id, session_date) in enumerate(sessions):
        col_name = f"{session_date}_S{idx+1}"

        cursor.execute("""
            SELECT roll_no FROM attendance_records
            WHERE session_id = %s
        """, (session_id,))
        present = set(r[0] for r in cursor.fetchall())

        df[col_name] = df["Roll No"].apply(
            lambda x: "Present" if x in present else "Absent"
        )

        
        for roll in present:
            if roll in present_count_map:
                present_count_map[roll] += 1

    total_sessions = len(sessions)

    
    df["Total Sessions"] = total_sessions
    df["Present Count"] = df["Roll No"].map(present_count_map)

    df["Attendance %"] = df["Present Count"].apply(
        lambda x: round((x / total_sessions) * 100, 2) if total_sessions else 0
    )

    
    os.makedirs("reports", exist_ok=True)

    file_path = f"reports/{subject}_{dept}_{division}.xlsx"
    df.to_excel(file_path, index=False)

    cursor.close()
    conn.close()

    return jsonify({
        "message": "Report generated with analytics",
        "file": file_path,
        "total_sessions": total_sessions
    })


from flask import send_file, jsonify
import os

@app.route("/download-report", methods=["POST"])
@token_required(roles=["faculty"])
def download_report():

    data = request.json
    subject = data.get("subject")
    division = data.get("division")

    faculty_id = request.user.get("fac_id")
    dept = request.user.get("fac_dept")
    print(dept, subject, division, faculty_id)

    if not subject or not division:
        return jsonify({"error": "Subject and division required"}), 400

    conn = psycopg2.connect(
    dbname=os.getenv("DB_NAME"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    host=os.getenv("DB_HOST"),
    port=os.getenv("DB_PORT")
)
    cursor = conn.cursor()

    try:
       
        cursor.execute("""
            SELECT 1
            FROM attendance_sessions
            WHERE subject = %s AND dept = %s AND division = %s AND faculty_id = %s
            LIMIT 1
        """, (subject, dept, division, faculty_id))

        if cursor.fetchone() is None:
            return jsonify({"error": "Unauthorized access"}), 403

        file_path = f"reports/{subject}_{dept}_{division}.xlsx"

        # ensure file exists
        if not os.path.exists(file_path):
            return jsonify({"error": "Report not found"}), 404

        # send file
        return send_file(
        file_path,
        as_attachment=True,
        download_name=f"{subject}_{division}_report.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        cursor.close()
        conn.close()


@app.route("/excel-files", methods=["GET"])
@token_required(roles=["faculty"])  # Only faculty and admin can view Excel files
def list_excel_files():
    files = [f for f in os.listdir() if f.endswith(".xlsx") and f != "students.xlsx"]
    return jsonify({"files": files})







@app.route("/student-attendance", methods=["GET"])
@token_required(roles=["student"])
def student_attendance():

    roll_no = request.user.get("roll_no")
    division = request.user.get("stud_div")
    dept = request.user.get("stud_dept")

    conn = psycopg2.connect(
    dbname=os.getenv("DB_NAME"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    host=os.getenv("DB_HOST"),
    port=os.getenv("DB_PORT")
)
    cursor = conn.cursor()

    try:
        # get total sessions per subject
        cursor.execute("""
    SELECT subject, COUNT(*) as total_classes
    FROM attendance_sessions
    WHERE dept = %s AND division = %s
    GROUP BY subject
""", (dept, division))
        
        total_sessions = cursor.fetchall()

        attendance_data = []

        for subject, total_classes in total_sessions:

            #  get present count
            cursor.execute("""
        SELECT COUNT(*)
        FROM attendance_records ar
        JOIN attendance_sessions s ON ar.session_id = s.id
        WHERE ar.roll_no = %s 
        AND s.subject = %s
        AND s.dept = %s
        AND s.division = %s
    """, (roll_no, subject, dept, division))

            present_days = cursor.fetchone()[0]
            

            attendance_percent = (
                (present_days / total_classes) * 100
                if total_classes else 0
            )

            attendance_data.append({
                "subject": subject,
                "present_days": present_days,
                "total_classes": total_classes,
                "attendance_percent": round(attendance_percent, 2)
            })

        if not attendance_data:
            return jsonify({"message": "No attendance data found"}), 404

        return jsonify({
            "roll_no": roll_no,
            "attendance_summary": attendance_data
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        cursor.close()
        conn.close()


@app.route("/student-sessions", methods=["GET"])
@token_required(roles=["student"])
def get_student_sessions():

    roll_no = request.user.get("roll_no")

    conn = psycopg2.connect(
    dbname=os.getenv("DB_NAME"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    host=os.getenv("DB_HOST"),
    port=os.getenv("DB_PORT")
)
    cursor = conn.cursor()

    #  get student dept + division
    cursor.execute("""
        SELECT stud_dept, stud_div
        FROM student_info
        WHERE roll_no = %s
    """, (roll_no,))
    
    student = cursor.fetchone()

    if not student:
        return jsonify({"error": "Student not found"}), 404

    dept, division = student

    #  get all sessions for their class
    cursor.execute("""
        SELECT id, subject, session_date
        FROM attendance_sessions
        WHERE dept = %s AND division = %s
        ORDER BY session_date DESC
    """, (dept, division))

    sessions = cursor.fetchall()

    result = []
    for s in sessions:
        result.append({
            "session_id": s[0],
            "subject": s[1],
            "date": str(s[2])
        })

    cursor.close()
    conn.close()

    return jsonify(result)




import json
from flask import Flask, request, jsonify
import os
import json
from werkzeug.utils import secure_filename
from datetime import datetime

import psycopg2

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route("/mark-attendance-request", methods=["POST"])
@token_required(roles=["student"])
def request_attendance():

    roll_no = request.user.get("roll_no")

    session_id = request.form.get("session_id")
    reason = request.form.get("reason")
    letter_file = request.files.get("letter")

    if not session_id or not reason or not letter_file:
        return jsonify({"error": "Missing required fields"}), 400

    conn = psycopg2.connect(
    dbname=os.getenv("DB_NAME"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    host=os.getenv("DB_HOST"),
    port=os.getenv("DB_PORT")
)
    cursor = conn.cursor()

    try:
        #  verify session exists
        cursor.execute("""
            SELECT id FROM attendance_sessions WHERE id = %s
        """, (session_id,))
        if not cursor.fetchone():
            return jsonify({"error": "Invalid session_id"}), 400

        #  prevent duplicate request
        cursor.execute("""
            SELECT id FROM attendance_requests
            WHERE session_id = %s AND roll_no = %s
        """, (session_id, roll_no))

        if cursor.fetchone():
            return jsonify({"error": "Request already submitted"}), 400

        #  save file
        filename = secure_filename(f"{roll_no}_{session_id}_{letter_file.filename}")
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        letter_file.save(file_path)

        #  insert request
        cursor.execute("""
            INSERT INTO attendance_requests (session_id, roll_no, reason, letter_path)
            VALUES (%s, %s, %s, %s)
        """, (session_id, roll_no, reason, file_path))

        conn.commit()

        return jsonify({"message": "Request submitted successfully"})

    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500

    finally:
        cursor.close()
        conn.close()



@app.route('/uploads/<filename>', methods=['GET'])
@token_required(roles=["faculty"])
def get_uploaded_file(filename):
    filename = secure_filename(filename)
    return send_from_directory(UPLOAD_FOLDER, filename)


@app.route("/attendance-requests", methods=["GET"])
@token_required(roles=["faculty"])
def get_attendance_requests():

    faculty_id = request.user.get("fac_id")

    conn = psycopg2.connect(
    dbname=os.getenv("DB_NAME"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    host=os.getenv("DB_HOST"),
    port=os.getenv("DB_PORT")
)
    cursor = conn.cursor()

    try:
        #  fetch only requests belonging to this faculty
        cursor.execute("""
            SELECT 
                ar.id,
                ar.roll_no,
                ar.reason,
                ar.status,
                ar.letter_path,
                s.subject,
                s.session_date
            FROM attendance_requests ar
            JOIN attendance_sessions s ON ar.session_id = s.id
            WHERE s.faculty_id = %s
            ORDER BY ar.created_at DESC
        """, (faculty_id,))

        rows = cursor.fetchall()

        result = []

        for r in rows:
            request_id, roll_no, reason, status, letter_path, subject, session_date = r

            letter_url = None
            if letter_path:
                filename = os.path.basename(letter_path)
                letter_url = request.host_url + "uploads/" + filename

            result.append({
                "request_id": request_id,
                "roll_no": roll_no,
                "subject": subject,
                "date": str(session_date),
                "reason": reason,
                "status": status,
                "letter_url": letter_url
            })

        return jsonify(result), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        cursor.close()
        conn.close()
    

    
import pandas as pd
from datetime import datetime
import pandas as pd
from datetime import datetime



@app.route("/attendance-requests/<int:request_id>", methods=["PATCH"])
@token_required(roles=["faculty"])
def update_request(request_id):

    faculty_id = request.user.get("fac_id")
    status = request.json.get("status")

    if status not in ["Approved", "Rejected"]:
        return jsonify({"error": "Invalid status"}), 400

    conn = psycopg2.connect(
    dbname=os.getenv("DB_NAME"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    host=os.getenv("DB_HOST"),
    port=os.getenv("DB_PORT")
)
    cursor = conn.cursor()

    try:
        #  verify ownership
        cursor.execute("""
            SELECT ar.roll_no, ar.session_id
            FROM attendance_requests ar
            JOIN attendance_sessions s ON ar.session_id = s.id
            WHERE ar.id = %s AND s.faculty_id = %s
        """, (request_id, faculty_id))

        req = cursor.fetchone()

        if not req:
            return jsonify({"error": "Unauthorized"}), 403

        roll_no, session_id = req

        #  update request status
        cursor.execute("""
            UPDATE attendance_requests
            SET status = %s
            WHERE id = %s
        """, (status, request_id))

        #  if approved → mark attendance
        if status == "Approved":
            cursor.execute("""
                INSERT INTO attendance_records (session_id, roll_no)
                VALUES (%s, %s)
                ON CONFLICT DO NOTHING
            """, (session_id, roll_no))

        conn.commit()

        return jsonify({"message": f"Request {status}"})

    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500

    finally:
        cursor.close()
        conn.close()









if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)























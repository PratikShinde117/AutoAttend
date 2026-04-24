

import cv2
import face_recognition
import psycopg2
import json
import pandas as pd
import dotenv
import os
dotenv.load_dotenv()


def add_new_face(roll_no, stud_name, stud_dept, stud_div):

    conn = psycopg2.connect(
    dbname=os.getenv("DB_NAME"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    host=os.getenv("DB_HOST"),
    port=os.getenv("DB_PORT")
)
    cursor = conn.cursor()

    try:
        # Check if face already exists
        cursor.execute("SELECT * FROM faces WHERE roll_no = %s", (roll_no,))
        if cursor.fetchone():
            return {"error": "Face already registered for this student"}

        # Insert student first
        cursor.execute("""
            INSERT INTO student_info (roll_no, stud_name, stud_dept, stud_div)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (roll_no) DO NOTHING
        """, (roll_no, stud_name, stud_dept, stud_div))

        #  Capture Face
        video_capture = cv2.VideoCapture(0)
        if not video_capture.isOpened():
            return {"error": "Could not open camera"}

        print("Capturing face... Look at the camera.")
        face_encoding = None

        while True:
            ret, frame = video_capture.read()
            if not ret:
                continue

            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            face_locations = face_recognition.face_locations(rgb_frame)
            face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

            if face_encodings:
                face_encoding = face_encodings[0]
                print(" Face captured!")
                break

        video_capture.release()
        cv2.destroyAllWindows()

        if face_encoding is None:
            return {"error": "No face detected"}

        face_encoding_json = json.dumps(face_encoding.tolist())

        #  Insert face encoding
        cursor.execute("""
            INSERT INTO faces (roll_no, name, encoding)
            VALUES (%s, %s, %s)
        """, (roll_no, stud_name, face_encoding_json))

        conn.commit()

    except Exception as e:
        conn.rollback()
        return {"error": str(e)}

    finally:
        cursor.close()
        conn.close()

    return {"success": f"{stud_name} added successfully"}

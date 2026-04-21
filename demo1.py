

import os 
import cv2
import json
import time
import numpy as np
import pandas as pd
import psycopg2
import face_recognition
from datetime import datetime
import globals  # Import the shared global state
import dotenv
import os
dotenv.load_dotenv()









def recognize_and_mark_attendance(subject, dept, division, session_id):

    conn = psycopg2.connect(
    dbname=os.getenv("DB_NAME"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    host=os.getenv("DB_HOST"),
    port=os.getenv("DB_PORT")
)
    cursor = conn.cursor()

    
    cursor.execute("""
        SELECT f.roll_no, f.encoding, s.stud_name, s.stud_dept, s.stud_div
        FROM faces f
        JOIN student_info s ON f.roll_no = s.roll_no
        WHERE s.stud_dept = %s AND s.stud_div = %s
    """, (dept, division))

    rows = cursor.fetchall()

    known_faces = []
    known_students = []

    for roll_no, encoding_str, stud_name, stud_dept, stud_div in rows:
        encoding = np.array(json.loads(encoding_str), dtype=np.float32)
        known_faces.append(encoding)
        known_students.append({
            "roll_no": roll_no,
            "name": stud_name,
            "dept": stud_dept,
            "div": stud_div
        })

    print(f"✅ Loaded {len(known_faces)} faces from database")

    # 📸 Start Camera
    video_capture = cv2.VideoCapture(0)
    time.sleep(2)

    if not video_capture.isOpened():
        return {"error": "Could not open camera"}

    marked_rolls = set()

    try:
        while globals.camera_active:
            ret, frame = video_capture.read()
            if not ret:
                continue

            small_frame = cv2.resize(frame, (0, 0), fx=0.5, fy=0.5)
            rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

            face_locations = face_recognition.face_locations(rgb_small_frame)
            face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)

            for face_encoding, face_location in zip(face_encodings, face_locations):

                matches = face_recognition.compare_faces(known_faces, face_encoding, tolerance=0.5)
                face_distances = face_recognition.face_distance(known_faces, face_encoding)

                label = "Unknown"

                if len(face_distances) > 0:
                    best_match_index = np.argmin(face_distances)

                    if matches[best_match_index]:
                        student = known_students[best_match_index]

                        roll_no = student["roll_no"]
                        stud_name = student["name"]
                        stud_dept = student["dept"]
                        stud_div = student["div"]

                        if stud_dept != dept:
                            print(f"❌ WRONG DEPT: Roll No {roll_no} | {stud_name} | Dept: {stud_dept}")
                            label = "Wrong Dept"

                        elif stud_div != division:
                            print(f"⚠️ WRONG DIVISION: Roll No {roll_no} | {stud_name} | Division: {stud_div}")
                            label = "Wrong Div"

                        else:
                            label = str(roll_no)

                            
                            if roll_no not in marked_rolls:
                                marked_rolls.add(roll_no)

                                cursor.execute("""
                                    INSERT INTO attendance_records (session_id, roll_no)
                                    VALUES (%s, %s)
                                    ON CONFLICT DO NOTHING
                                """, (session_id, roll_no))

                                conn.commit()
                    else:
                        print("❌ UNKNOWN FACE DETECTED")
                else:
                    print("❌ UNKNOWN FACE DETECTED")

                # 📌 Draw box
                top, right, bottom, left = [v * 2 for v in face_location]
                cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
                cv2.putText(frame, label,
                            (left, top - 10),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.8, (0, 255, 0), 2)

            cv2.imshow('Face Recognition', frame)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    except Exception as e:
        return {"error": str(e)}

    finally:
        video_capture.release()
        cv2.destroyAllWindows()
        cursor.close()
        conn.close()

    return {"marked_students": list(marked_rolls)}
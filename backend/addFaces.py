

import cv2
import face_recognition
import psycopg2
import json
import pandas as pd
import dotenv
import os
dotenv.load_dotenv()

# def add_new_face(roll_number, student_name):
    
#     conn = psycopg2.connect(
#         dbname="project",
#         user="postgres",
#         password="pratik115",
#         host="localhost",
#         port="5432"
#     )
#     cursor = conn.cursor()

#     # 📌 Capture Face from Webcam
#     video_capture = cv2.VideoCapture(0)
#     if not video_capture.isOpened():
#         return {"error": "Could not open camera"}

#     print("📸 Capturing face... Look at the camera.")
#     face_encoding = None

#     while True:
#         ret, frame = video_capture.read()
#         if not ret:
#             continue

#         # Convert frame to RGB
#         rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

#         # Detect face
#         face_locations = face_recognition.face_locations(rgb_frame)
#         face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

#         if face_encodings:
#             face_encoding = face_encodings[0]
#             print("✅ Face captured!")
#             break

#     video_capture.release()
#     cv2.destroyAllWindows()

#     if face_encoding is None:
#         return {"error": "No face detected"}

#     # 📌 Store Encoded Face in Database
#     face_encoding_json = json.dumps(face_encoding.tolist())

#     cursor.execute("INSERT INTO faces (roll_no, name, encoding) VALUES (%s, %s, %s)", 
#                    (roll_number, student_name, face_encoding_json))
#     conn.commit()
#     cursor.close()
#     conn.close()

#     # 📌 Save to Excel File
#     save_student_to_excel(roll_number, student_name)

#     return {"success": f"{student_name} (Roll No. {roll_number}) added to the database and Excel sheet!"}

# def save_student_to_excel(roll_number, student_name):
#     students_file = "students.xlsx"

#     # 📌 Load Excel File
#     if os.path.exists(students_file):
#         df_students = pd.read_excel(students_file, engine="openpyxl", dtype=str)
#         df_students.columns = df_students.columns.str.strip()  # Remove unwanted spaces
#     else:
#         print("📂 Creating new students.xlsx file...")
#         df_students = pd.DataFrame(columns=["Roll No.", "Name"])

#     # ✅ Debugging: Print column names
#     print("🔍 Column Names in Excel:", df_students.columns)

#     # Ensure correct column name is used
#     if "Roll No." not in df_students.columns:
#         print("⚠️ 'Roll No.' column not found! Fixing it.")
#         df_students = pd.DataFrame(columns=["Roll No.", "Name"])

#     # Check if student already exists
#     if roll_number in df_students["Roll No."].values:
#         return {"error": f"Student {roll_number} already exists in the sheet."}

#     # Append & Save
#     new_student = pd.DataFrame([[roll_number, student_name]], columns=["Roll No.", "Name"])
#     df_students = pd.concat([df_students, new_student], ignore_index=True)
#     df_students.to_excel(students_file, index=False, engine="openpyxl")

#     print(f"✅ {student_name} (Roll No. {roll_number}) added to students.xlsx")



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
        # 🔍 Check if face already exists
        cursor.execute("SELECT * FROM faces WHERE roll_no = %s", (roll_no,))
        if cursor.fetchone():
            return {"error": "Face already registered for this student"}

        # 🔥 Insert student first
        cursor.execute("""
            INSERT INTO student_info (roll_no, stud_name, stud_dept, stud_div)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (roll_no) DO NOTHING
        """, (roll_no, stud_name, stud_dept, stud_div))

        # 📌 Capture Face
        video_capture = cv2.VideoCapture(0)
        if not video_capture.isOpened():
            return {"error": "Could not open camera"}

        print("📸 Capturing face... Look at the camera.")
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
                print("✅ Face captured!")
                break

        video_capture.release()
        cv2.destroyAllWindows()

        if face_encoding is None:
            return {"error": "No face detected"}

        face_encoding_json = json.dumps(face_encoding.tolist())

        # 🔥 Insert face encoding
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
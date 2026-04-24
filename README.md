# AutoAttend Backend

AutoAttend is an AI-powered attendance management system that uses **face recognition** to automate student attendance. This backend is built using a **microservice architecture** combining **Node.js** and **Flask (Python)**.

---

## Architecture Overview

The system is divided into two main services:

###  Node.js (API Gateway)

* Handles authentication & authorization
* Implements Role-Based Access Control (RBAC)
* Acts as a secure gateway between frontend and Flask service
* Forwards requests to Flask with JWT + internal API key

###  Flask (AI Service)

* Handles face recognition using OpenCV + face_recognition
* Manages attendance marking
* Generates reports and analytics
* Processes attendance requests

---

##  Security Features

* JWT-based authentication
* Role-based access (Student, Faculty)
* Resource-level authorization (dept + division based)
* Internal service authentication (`x-internal-key`)
* Protected routes across services

---

##  Key Features

###  Faculty

* Start/Stop camera for attendance
* Add student face data
* Generate attendance reports (Excel)
* Download reports (authorized access only)
* Review & approve attendance requests

###  Student

* View subject-wise attendance
* Request attendance for missed sessions (with proof upload)
* Track approval/rejection status

---

##  Project Structure

```
backend/
│
├── nodebackend/           # Node.js service
│   ├── routes/
│   ├── middlewares/
│   ├── login.js
│   ├── .env
│
├── face_recognition_api.py  # Flask main service
├── addface.py
├── demo1.py
├── .env
│
├── uploads/              # Uploaded documents (ignored)
├── reports/              # Generated Excel reports (ignored)
```

---

##  Environment Variables

###  Flask `.env`

```
DB_NAME=
DB_USER=
DB_PASSWORD=
DB_HOST=
DB_PORT=
JWT_SECRET=
INTERNAL_API_KEY=
```

###  Node `.env`

```
JWT_SECRET=
INTERNAL_API_KEY=
```

---

##  API Flow

1. Client → Node.js
2. Node validates JWT & role
3. Node forwards request to Flask with:

   * Authorization token
   * Internal API key
4. Flask verifies request and executes logic
5. Response → Node → Client

---

##  Core Modules

### 1. Face Recognition

* Uses `face_recognition` library
* Encodes faces and stores in PostgreSQL
* Matches real-time camera input

### 2. Attendance System

* Session-based attendance
* Prevents duplicate marking
* Dept + Division filtering

### 3. Report Generation

* Generates Excel reports using pandas
* Includes:

  * Session-wise attendance
  * Total sessions
  * Attendance percentage

### 4. Attendance Requests

* Students submit requests with proof
* Faculty reviews and approves/rejects
* Updates attendance dynamically

---

##  Performance Optimizations

* Frame skipping (process every N frames)
* Image resizing for faster detection
* Batch database inserts
* Filtered face loading (dept + division)

---

##  Security Enhancements

* Internal API key validation between services
* Input validation on routes
* Controlled file uploads
* Restricted access to reports

---

##  Getting Started

### 1. Clone Repository

```
git clone https://github.com/your-username/AutoAttend.git
```

### 2. Install Dependencies

#### Node

```
cd nodebackend
npm install
```

#### Flask

```
pip install -r requirements.txt
```

---

### 3. Setup Database

* PostgreSQL required
* Create database: `project`
* Setup tables: `student_info`, `faces`, `attendance_sessions`, `attendance_records`, `attendance_requests`

---

### 4. Run Services

#### Start Node

```
npm start
```

#### Start Flask

```
python face_recognition_api.py
```

---

##  Tech Stack

* Node.js + Express
* Python + Flask
* PostgreSQL
* OpenCV
* face_recognition
* Pandas

---

##  Future Improvements

* Deploy microservices (Docker + cloud)
* Add WebSocket for real-time updates
* Improve UI dashboard
* Add analytics visualization
* Optimize face recognition using GPU

---

## 👨‍💻 Author

**Pratik Shinde**

---

## ⭐ Contribution

Feel free to fork, contribute, and improve the system.

---

## 📄 License

This project is for educational purposes.

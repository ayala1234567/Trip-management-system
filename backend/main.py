from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import psycopg2
from psycopg2.extras import RealDictCursor
import os
from dotenv import load_dotenv
from fastapi.responses import HTMLResponse

load_dotenv()


app = FastAPI(title="Trip management system")

class Teacher(BaseModel):
    teacher_id: str
    full_name: str
    grade_class: str

class Student(BaseModel):
    student_id: str
    full_name: str
    grade_class: str
    assigned_teacher_id: str

# Connecting to the database:
def get_db_connection():
    try:
        conn = psycopg2.connect(
            host=os.getenv('DB_HOST'),
            database=os.getenv('DB_NAME'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            port=os.getenv('DB_PORT'),
            cursor_factory=RealDictCursor 
        )
        return conn
    except Exception as e:
        print(f"Database connection error: {e}")
        raise HTTPException(status_code=500, detail="Database connection failed")
    
def is_teacher_exists(teacher_id: str):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT * FROM teachers WHERE teacher_id = %s;', (teacher_id,))
    teacher = cur.fetchone()
    cur.close()
    conn.close()
    return teacher is not None

@app.get("/", response_class=HTMLResponse)
def read_root():
    try:
        with open("../frontend/index.html", "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return HTMLResponse(content="Error: index.html not found", status_code=404)

@app.get("/map.html", response_class=HTMLResponse)
def read_map():
    try:
        with open("../frontend/map.html", "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return HTMLResponse(content="Error: map.html not found", status_code=404)


# ==========================================
# Paths for teachers
# ==========================================

@app.get("/api/teachers")
def get_teachers(requesting_teacher_id: str):
    """Retrieving all the teachers"""
    if not is_teacher_exists(requesting_teacher_id):
        raise HTTPException(status_code=403, detail="Access denied")
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT * FROM teachers;')
    teachers = cur.fetchall()
    cur.close()
    conn.close()
    return teachers

@app.post("/api/teachers", status_code=201)
def add_teacher(teacher: Teacher):
    """"Adding a teacher"""
   
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            'INSERT INTO teachers (teacher_id, full_name, grade_class) VALUES (%s, %s, %s)',
            (teacher.teacher_id, teacher.full_name, teacher.grade_class)
        )
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        cur.close()
        conn.close()
    return {"message": "Teacher added successfully"}

@app.get("/api/teachers/{teacher_id}")
def get_teacher(teacher_id: str):
    """Retrieving a specific teacher by ID"""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT * FROM teachers WHERE teacher_id = %s;', (teacher_id,))
    teacher = cur.fetchone() 
    cur.close()
    conn.close()
    
    if not teacher:
        raise HTTPException(status_code=404, detail="Teacher not found")
    return teacher

@app.get("/api/teachers/{teacher_id}/students")
def get_students_by_teacher(teacher_id: str):
    if not is_teacher_exists(teacher_id):
        raise HTTPException(status_code=403, detail="Access denied")

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute('SELECT * FROM students WHERE assigned_teacher_id = %s;', (teacher_id,))
    students = cur.fetchall()
    cur.close()
    conn.close()
    
    return students

# ==========================================
# Paths for students
# ==========================================


@app.get("/api/students")
def get_students(requesting_teacher_id: str):
    """Retrieving all the students"""
    if not is_teacher_exists(requesting_teacher_id):
        raise HTTPException(status_code=403, detail="Access denied")

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT * FROM students;')
    students = cur.fetchall()
    cur.close()
    conn.close()
    return students


@app.post("/api/students", status_code=201)
def add_student(student: Student):
    """Adding a student"""
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            'INSERT INTO students (student_id, full_name, grade_class, assigned_teacher_id) VALUES (%s, %s, %s, %s)',
            (student.student_id, student.full_name, student.grade_class, student.assigned_teacher_id)
        )
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        cur.close()
        conn.close()
    return {"message": "Student added successfully"}


@app.get("/api/students/{student_id}")
def get_student(student_id: str, requesting_teacher_id: str):
    """Student retrieval by ID"""
    if not is_teacher_exists(requesting_teacher_id):
        raise HTTPException(status_code=403, detail="Access denied")
    
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT * FROM students WHERE student_id = %s;', (student_id,))
    student = cur.fetchone()
    cur.close()
    conn.close()
    
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    return student





# ==========================================
# --- Models for Location Tracking  ---
# ==========================================
class DMS(BaseModel):
    Degrees: str
    Minutes: str
    Seconds: str

class Coordinates(BaseModel):
    Longitude: DMS
    Latitude: DMS

class LocationPing(BaseModel):
    ID: str
    Coordinates: Coordinates
    Time: str


active_locations = {}

def dms_to_decimal(dms: DMS) -> float:
    """Converts Degrees, Minutes, Seconds to Decimal Degrees"""
    d = float(dms.Degrees)
    m = float(dms.Minutes)
    s = float(dms.Seconds)
    return d + (m / 60) + (s / 3600)


# ==========================================
# Paths for Location Tracking 
# ==========================================

@app.post("/api/location", status_code=201)
def receive_location(ping: LocationPing):
    """Receives location data from the student's physical device"""
    try:
        lat_dec = dms_to_decimal(ping.Coordinates.Latitude)
        lng_dec = dms_to_decimal(ping.Coordinates.Longitude)
        
        active_locations[ping.ID] = {
            "lat": lat_dec,
            "lng": lng_dec,
            "time": ping.Time
        }
        return {"message": "Location updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid coordinate format: {str(e)}")

@app.get("/api/locations")
def get_all_active_locations():
    """Retrieves all active locations (Restricted to teachers)"""
    return active_locations



# ==========================================
# Paths for Location Tracking & Bonus 
# ==========================================

@app.get("/api/tracking/{teacher_id}")
def get_teacher_tracking_data(teacher_id: str):
    
    if not is_teacher_exists(teacher_id):
        raise HTTPException(status_code=403, detail="Access denied: Teacher not found")

    teacher_location = active_locations.get(teacher_id)
    if not teacher_location:
        raise HTTPException(status_code=400, detail="Cannot start tracking: Teacher's device is not sending location")

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT student_id, full_name FROM students WHERE assigned_teacher_id = %s;', (teacher_id,))
    my_students = cur.fetchall()
    cur.close()
    conn.close()

    students_locations = {}
    for student in my_students:
        s_id = student['student_id']
        if s_id in active_locations:
            students_locations[s_id] = {
                "full_name": student['full_name'],
                "lat": active_locations[s_id]["lat"],
                "lng": active_locations[s_id]["lng"],
                "time": active_locations[s_id]["time"]
            }

    return {
        "teacher_location": teacher_location,
        "students": students_locations
    }
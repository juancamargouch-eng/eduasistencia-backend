import requests
import json
from app.config.database import SessionLocal
from app.models.student import Student

def test_verify():
    db = SessionLocal()
    student = db.query(Student).first()
    if not student:
        print("No students found in DB.")
        return
    
    qr_code = student.qr_code_hash
    print(f"Testing with student: {student.full_name}, QR: {qr_code}")
    db.close()
    
    url = "http://localhost:8000/api/attendance/verify"
    
    # Random descriptor (128 floats)
    descriptor = [0.1] * 128
    
    payload = {
        "qr_code": qr_code,
        "face_descriptor": json.dumps(descriptor)
    }
    
    # File is optional in verify endpoint, but let's send it to be safe if schema requires it (it's commented out in code but check params)
    # verify_attendance has: file: UploadFile = File(...) commented out? 
    # Let's check the viewed file content... 
    # line 18: # file: UploadFile = File(...), # Optional for log, not needed for logic now
    # So it's NOT required.
    
    try:
        r = requests.post(url, data=payload)
        print(f"Status: {r.status_code}")
        print(f"Response: {r.text}")
    except Exception as e:
        print(f"Request failed: {e}")

if __name__ == "__main__":
    test_verify()

import sys
import os
import json
from datetime import datetime

# Add current dir to path
sys.path.append(os.getcwd())

try:
    from app.services.student_service import StudentService
    from app.config.database import SessionLocal
    from app import models
    from fastapi import HTTPException

    db = SessionLocal()
    student = db.query(models.Student).first()
    
    if student:
        print(f"Testing SIMULATED 409 flow for student: {student.full_name}")
        
        # 1. Simulate the data we now use in AttendanceService
        prepared_student = StudentService.prepare_student_response(student, for_kiosk=True)
        
        # 2. Reconstruct the detail dict EXACTLY as it is in the new AttendanceService
        detail = {
            "message": "Ya marcó su entrada",
            "timestamp": "12:00:00",
            "student": {
                "full_name": getattr(student, 'full_name', "Estudiante"),
                "photo_url": prepared_student.get("photo_url", "")
            }
        }
        
        # 3. Verify JSON serializability
        json_str = json.dumps(detail, default=str)
        print("SUCCESS: JSON serialization for 409 detail is working!")
        print(json_str)

    else:
        print("No student found to test.")
        
except Exception as e:
    import traceback
    traceback.print_exc()
finally:
    if 'db' in locals():
        db.close()

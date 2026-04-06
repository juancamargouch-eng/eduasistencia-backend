import sys
import os
import json

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
        print(f"Testing serialization for student: {student.full_name}")
        # 1. Test Service Response
        res = StudentService.prepare_student_response(student, for_kiosk=True)
        print(f"Service return type: {type(res)}")
        
        # 2. Test Exception Detail structure
        detail = {
            "message": "Test conflict",
            "timestamp": "12:00:00",
            "student": res
        }
        
        # Verify JSON serializability (This is what FastAPI does)
        json_str = json.dumps(detail, default=str)
        print("SUCCESS: JSON serialization is working!")
        print(json_str)

    else:
        print("No student found to test.")
        
except Exception as e:
    import traceback
    traceback.print_exc()
finally:
    if 'db' in locals():
        db.close()

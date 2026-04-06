import sys
import os
import json
from datetime import datetime

# Add current dir to path
sys.path.append(os.getcwd())

try:
    from app.services.student_service import StudentService
    from app.config.database import SessionLocal
    from app import models, schemas

    db = SessionLocal()
    
    # Simulate the Dashboard's /api/attendance/logs logic
    print("Testing SIMULATED Dashboard Logs flow...")
    logs = db.query(models.AttendanceLog).order_by(models.AttendanceLog.timestamp.desc()).limit(5).all()
    
    items_out = []
    for log in logs:
        student_data = StudentService.prepare_student_response(log.student) if log.student else None
        log_data = {
            "id": log.id,
            "student_id": log.student_id,
            "verification_status": log.verification_status,
            "confidence_score": log.confidence_score,
            "failure_reason": log.failure_reason,
            "device_source": log.device_source,
            "timestamp": log.timestamp,
            "event_type": log.event_type,
            "status": log.status,
            "student": student_data
        }
        # Try to validate with Pydantic AttendanceLog schema
        validated = schemas.AttendanceLog.model_validate(log_data)
        items_out.append(validated.model_dump(mode='json'))
        
    print("SUCCESS: Attendance logs are now perfectly serializable!")
    print(f"Validated {len(items_out)} log entries.")

except Exception as e:
    import traceback
    traceback.print_exc()
finally:
    if 'db' in locals():
        db.close()

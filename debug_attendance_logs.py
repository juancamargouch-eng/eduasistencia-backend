import sys
import os
from datetime import datetime

# Add the current directory to sys.path so we can import 'app'
sys.path.append(os.getcwd())

from app.config.database import SessionLocal
from app.models.attendance import AttendanceLog
from sqlalchemy import func

def debug_logs():
    db = SessionLocal()
    try:
        print(f"Current Python Time: {datetime.now()}")
        print("-" * 50)
        
        # Get last 10 logs
        logs = db.query(AttendanceLog).order_by(AttendanceLog.timestamp.desc()).limit(10).all()
        
        if not logs:
            print("No logs found in DB.")
            return

        for log in logs:
            print(f"ID: {log.id}")
            print(f"Timestamp: {log.timestamp} (Type: {type(log.timestamp)})")
            print(f"Event Type: {log.event_type}")
            print(f"Status: {log.verification_status}")
            print(f"Reason: {log.failure_reason}")
            print(f"Student ID: {log.student_id}")
            
            # Check what func.date() would return for this log
            # We can't easily execute func.date in python, but we can query it
            db_date = db.query(func.date(AttendanceLog.timestamp)).filter(AttendanceLog.id == log.id).scalar()
            print(f"DB Date Function Returns: {db_date}")
            print("-" * 30)
            
    finally:
        db.close()

if __name__ == "__main__":
    debug_logs()

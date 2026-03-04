from datetime import datetime, date
from sqlalchemy import func
from app import models, schemas
from app.api import deps
from app.config.database import SessionLocal

def test_daily_attendance_logic():
    db = SessionLocal()
    grade = "1ro Primaria"
    section = "A"
    date_str = "2026-02-16"
    
    print(f"Testing with grade={grade}, section={section}, date={date_str}")
    
    try:
        # 1. Parse Date
        if date_str:
            try:
                query_date = datetime.strptime(date_str, "%Y-%m-%d").date()
                print(f"Parsed Date: {query_date} (Type: {type(query_date)})")
            except ValueError:
                print("Date parse error")
                return
        else:
            query_date = datetime.now().date()

        # 2. Check Holiday/Weekend (Peru)
        is_weekend = query_date.weekday() >= 5 
        print(f"Is Weekend: {is_weekend}")
        
        holidays_pe = {
            (1, 1): "Año Nuevo",
            (5, 1): "Día del Trabajo",
            (6, 29): "San Pedro y San Pablo",
            (7, 28): "Fiestas Patrias",
            (7, 29): "Fiestas Patrias",
            (8, 6): "Batalla de Junín",
            (8, 30): "Santa Rosa de Lima",
            (10, 8): "Combate de Angamos",
            (11, 1): "Día de Todos los Santos",
            (12, 8): "Inmaculada Concepción",
            (12, 9): "Batalla de Ayacucho",
            (12, 25): "Navidad"
        }
        
        holiday_name = holidays_pe.get((query_date.month, query_date.day))
        print(f"Holiday Name: {holiday_name}")
        
        is_non_working_day = is_weekend or (holiday_name is not None)
        
        # 3. Fetch Students
        print("Querying students...")
        students = db.query(models.Student).filter(
            models.Student.grade == grade,
            models.Student.section == section,
            models.Student.is_active == True
        ).all()
        print(f"Found {len(students)} students")
        
        # 4. Fetch Logs for that day
        print("Querying logs...")
        # CRITICAL: verifying this query logic
        logs = db.query(models.AttendanceLog).filter(
            models.AttendanceLog.verification_status == True,
            models.AttendanceLog.event_type == "ENTRY",
            func.date(models.AttendanceLog.timestamp) == query_date
        ).all()
        print(f"Found {len(logs)} logs")
        
        # Verify comparison manually in python if SQL fails?
        # Just checking if the above line crashes.
        
        logs_map = {log.student_id: log for log in logs}
        
        results = []
        present_count = 0
        absent_count = 0
        
        for student in students:
            log = logs_map.get(student.id)
            if log:
                present_count += 1
            else:
                absent_count += 1
                
        print("Success! Results calculated.")
        
    except Exception as e:
        print(f"CRASHED: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    test_daily_attendance_logic()

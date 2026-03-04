from typing import Any
from fastapi import APIRouter, Depends, HTTPException, File, Form, UploadFile
from sqlalchemy.orm import Session
from datetime import datetime
import json

from app import models, schemas
from app.api import deps
from app.services.face_recognition import compare_faces
from app.core.websocket_manager import manager

router = APIRouter()

from app.services.attendance_service import AttendanceService

@router.post("/verify", response_model=schemas.AttendanceLogKiosk)
async def verify_attendance(
    *,
    db: Session = Depends(deps.get_db),
    qr_code: str = Form(None),
    dni: str = Form(None),
    face_descriptor: str = Form(...),
    event_type: str = Form("ENTRY"),
) -> Any:
    return await AttendanceService.verify_attendance(
        db=db,
        qr_code=qr_code,
        dni=dni,
        face_descriptor=face_descriptor,
        event_type=event_type
    )

@router.get("/logs", response_model=list[schemas.AttendanceLog])
def read_attendance_logs(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    logs = db.query(models.AttendanceLog).order_by(models.AttendanceLog.timestamp.desc()).offset(skip).limit(limit).all()
    return logs

@router.post("/logs/{log_id}/validate", response_model=schemas.AttendanceLog)
async def validate_log(
    *,
    db: Session = Depends(deps.get_db),
    log_id: int,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    return await AttendanceService.validate_log(db, log_id)

@router.get("/stats/occupancy")
def get_occupancy_stats(
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    # Simple calculation: Count ENTRY - Count EXIT for today
    from sqlalchemy import func
    # Use naive usage of now() might be tricky with timezone, so let's stick to date() via SQL
    
    # Check dialect to see if we need cast. SQLite/Postgres usually handle func.date(timestamp) ok.
    # But let's use python date to filter range if we want to be safe or just use SQL func.
    
    today = datetime.now().date()
    
    # For SQLite, func.date might need string format. Postgres works.
    # Given environment is likely Windows/SQLite now? Or Postgres? 
    # Ah, config is DATABASE_URL... likely PostgreSQL from earlier context (psycopg2 installed).
    
    entries = db.query(func.count(models.AttendanceLog.id)).filter(
        func.date(models.AttendanceLog.timestamp) == today,
        models.AttendanceLog.event_type == "ENTRY",
        models.AttendanceLog.verification_status == True
    ).scalar()
    
    exits = db.query(func.count(models.AttendanceLog.id)).filter(
        func.date(models.AttendanceLog.timestamp) == today,
        models.AttendanceLog.event_type == "EXIT",
        models.AttendanceLog.verification_status == True
    ).scalar()
    
    return {
        "entries": entries,
        "exits": exits,
        "current_occupancy": entries - exits
    }

@router.get("/daily-status")
def get_daily_attendance_status(
    grade: str,
    section: str,
    date_str: str = None, # YYYY-MM-DD
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    try:
        from datetime import date
        from sqlalchemy import func
        
        # 1. Parse Date
        if date_str:
            try:
                query_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
        else:
            query_date = datetime.now().date()

        # 2. Check Holiday/Weekend (Peru)
        is_weekend = query_date.weekday() >= 5 # 5=Sat, 6=Sun
        
        # Simple hardcoded list for 2024-2026 (Extend as needed or move to DB/Config)
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
        is_non_working_day = is_weekend or (holiday_name is not None)
        
        # 3. Fetch Students
        students = db.query(models.Student).filter(
            models.Student.grade == grade,
            models.Student.section == section,
            models.Student.is_active == True
        ).all()
        
        # 4. Fetch Logs for that day
        # We want successful entries primarily
        logs = db.query(models.AttendanceLog).filter(
            models.AttendanceLog.verification_status == True,
            models.AttendanceLog.event_type == "ENTRY", # Only care about arriving for "Present"
            func.date(models.AttendanceLog.timestamp) == query_date
        ).all()
        
        # Create a map of student_id -> log
        logs_map = {log.student_id: log for log in logs}
        
        results = []
        
        present_count = 0
        late_count = 0
        absent_count = 0
        
        for student in students:
            log = logs_map.get(student.id)
            status = "ABSENT"
            entry_time = None
            
            if log:
                status = log.status # Get real status (PRESENT or LATE)
                if status == "LATE":
                    late_count += 1
                else:
                    present_count += 1
                entry_time = log.timestamp
            else:
                absent_count += 1
                
            schedule_info = None
            if student.schedule:
                schedule_info = {
                     "id": student.schedule.id,
                     "name": student.schedule.name,
                     "start_time": student.schedule.start_time.strftime("%H:%M") if student.schedule.start_time else None
                }

            results.append({
                "id": student.id,
                "full_name": student.full_name,
                "photo_url": student.photo_url,
                "status": status,
                "entry_time": entry_time,
                "schedule": schedule_info
            })
            
        return {
            "date": query_date.isoformat(),
            "is_non_working_day": is_non_working_day,
            "holiday_name": "Fin de Semana" if is_weekend and not holiday_name else holiday_name,
            "summary": {
                "total": len(students),
                "present": present_count,
                "late": late_count,
                "absent": absent_count
            },
            "students": results
        }
    except Exception as e:
        print(f"ERROR in daily-status: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=f"Server Error: {str(e)}")
@router.get("/student/{dni}/absences")
def get_student_absences(
    dni: str,
    days_back: int = 30,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    from datetime import date, timedelta
    from sqlalchemy import func
    
    # 1. Find Student
    student = db.query(models.Student).filter(models.Student.dni == dni).first()
    if not student:
        raise HTTPException(status_code=404, detail="Estudiante no encontrado")
        
    # 2. Define Range (e.g., last 30 days)
    today = date.today()
    start_date = today - timedelta(days=days_back)
    
    # 3. Get all logs in range
    logs = db.query(models.AttendanceLog).filter(
        models.AttendanceLog.student_id == student.id,
        models.AttendanceLog.verification_status == True,
        models.AttendanceLog.event_type == "ENTRY",
        models.AttendanceLog.timestamp >= start_date
    ).all()
    
    # Set of dates with attendance
    attendance_dates = {log.timestamp.date() for log in logs}
    
    # 4. Get all justifications in range
    justifications = db.query(models.Justification).filter(
        models.Justification.student_id == student.id,
        models.Justification.date >= start_date
    ).all()
    
    justification_dates = {j.date for j in justifications}
    
    # 5. Calculate Absences
    absences = []
    
    # Iterate from start_date to yesterday (today is not an absence yet unless day is over, keep simple)
    current_date = start_date
    while current_date < today:
        # Check Weekend
        if current_date.weekday() >= 5: # Sat/Sun
            current_date += timedelta(days=1)
            continue
            
        # Check Holidays (Reuse hardcoded list for MVP)
        holidays_pe = {
            (1, 1), (5, 1), (6, 29), (7, 28), (7, 29),
            (8, 6), (8, 30), (10, 8), (11, 1), (12, 8), (12, 9), (12, 25)
        }
        if (current_date.month, current_date.day) in holidays_pe:
            current_date += timedelta(days=1)
            continue
            
        # Check if attended or justified
        if current_date not in attendance_dates and current_date not in justification_dates:
            absences.append({
                "date": current_date.isoformat(),
                "day_name": current_date.strftime("%A"), # English for now, can localize
                "status": "UNJUSTIFIED"
            })
            
        current_date += timedelta(days=1)
        
    return {
        "student": {
            "id": student.id,
            "full_name": student.full_name,
            "grade": student.grade,
            "section": student.section,
            "photo_url": student.photo_url,
            "schedule": {
                "name": student.schedule.name,
                "start_time": student.schedule.start_time.strftime("%H:%M")
            } if student.schedule else None
        },
        "absences": absences
    }
@router.get("/stats/monthly")
def get_monthly_stats(
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    from datetime import date, timedelta
    from sqlalchemy import func
    
    # 1. Define Range (Last 30 days)
    today = date.today()
    start_date = today - timedelta(days=29) # Total 30 days including today
    
    # 2. Get active students count
    total_students = db.query(func.count(models.Student.id)).filter(models.Student.is_active == True).scalar() or 0
    
    # 3. Get all logs in range
    logs = db.query(
        func.date(models.AttendanceLog.timestamp).label('date'),
        models.AttendanceLog.status,
        func.count(models.AttendanceLog.id).label('count')
    ).filter(
        models.AttendanceLog.verification_status == True,
        models.AttendanceLog.event_type == "ENTRY",
        models.AttendanceLog.timestamp >= start_date
    ).group_by(
        func.date(models.AttendanceLog.timestamp),
        models.AttendanceLog.status
    ).all()
    
    # Organize logs by date
    daily_data = {}
    current_dt = start_date
    while current_dt <= today:
        # Check if it's a non-working day (simple check)
        is_weekend = current_dt.weekday() >= 5
        holidays_pe = {
            (1, 1), (5, 1), (6, 29), (7, 28), (7, 29),
            (8, 6), (8, 30), (10, 8), (11, 1), (12, 8), (12, 9), (12, 25)
        }
        is_holiday = (current_dt.month, current_dt.day) in holidays_pe
        
        if not (is_weekend or is_holiday):
            daily_data[current_dt.isoformat()] = {
                "date": current_dt.strftime("%d/%m"),
                "full_date": current_dt.isoformat(),
                "present": 0,
                "late": 0,
                "absent": total_students
            }
        current_dt += timedelta(days=1)
        
    # Fill with real data
    for log_date, status, count in logs:
        date_str = log_date.isoformat() if hasattr(log_date, 'isoformat') else str(log_date)
        if date_str in daily_data:
            if status == "PRESENT":
                daily_data[date_str]["present"] += count
                daily_data[date_str]["absent"] -= count
            elif status == "LATE":
                daily_data[date_str]["late"] += count
                daily_data[date_str]["absent"] -= count
                
    # 4. Breakdown by Grade (Current Day or Monthly Avg)
    grade_stats = db.query(
        models.Student.grade,
        models.AttendanceLog.status,
        func.count(models.AttendanceLog.id)
    ).join(models.AttendanceLog, models.Student.id == models.AttendanceLog.student_id).filter(
        models.AttendanceLog.verification_status == True,
        models.AttendanceLog.event_type == "ENTRY",
        models.AttendanceLog.timestamp >= start_date
    ).group_by(models.Student.grade, models.AttendanceLog.status).all()
    
    # Calculate performance by grade
    grades_perf = {}
    for grade, status, count in grade_stats:
        if grade not in grades_perf:
            # Get total students in this grade
            count_in_grade = db.query(func.count(models.Student.id)).filter(
                models.Student.grade == grade,
                models.Student.is_active == True
            ).scalar() or 1
            grades_perf[grade] = {"name": grade, "present": 0, "late": 0, "total": count_in_grade}
            
        if status == "PRESENT":
            grades_perf[grade]["present"] += count
        elif status == "LATE":
            grades_perf[grade]["late"] += count

    return {
        "daily": sorted(list(daily_data.values()), key=lambda x: x["full_date"]),
        "grades": sorted(list(grades_perf.values()), key=lambda x: x["name"]),
        "summary": {
            "total_students": total_students,
            "period_days": len(daily_data)
        }
    }

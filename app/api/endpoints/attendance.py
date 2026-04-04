from typing import Any, Optional
from fastapi import APIRouter, Depends, HTTPException, File, Form, UploadFile, Request, Query
from sqlalchemy.orm import Session
from datetime import datetime
import json

from app import models, schemas
from app.api import deps
from app.services.face_recognition import compare_faces
from app.core.websocket_manager import manager

router = APIRouter()

from app.services.attendance_service import AttendanceService
from app.services.student_service import StudentService

@router.post("/verify", response_model=schemas.AttendanceLogKiosk)
@deps.limiter.limit("60/minute")
async def verify_attendance(
    *,
    request: Request,
    db: Session = Depends(deps.get_db),
    qr_code: str = Form(None),
    dni: str = Form(None),
    face_descriptor: str = Form(...),
    event_type: str = Form("ENTRY"),
    device_source: str = Form(None),
    file: UploadFile = File(None),
) -> Any:
    # Solo permitir bypass si se envía el header secreto (para pruebas)
    skip_bio = request.headers.get("X-Stress-Test") == "true"
    
    return await AttendanceService.verify_attendance(
        db=db,
        qr_code=qr_code,
        dni=dni,
        face_descriptor=face_descriptor,
        event_type=event_type,
        device_source=device_source,
        skip_biometrics=skip_bio
    )

@router.get("/logs", response_model=schemas.AttendancePagination)
def read_attendance_logs(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    query = db.query(models.AttendanceLog)
    total = query.count()
    logs = query.order_by(models.AttendanceLog.timestamp.desc()).offset(skip).limit(limit).all()
    
    for log in logs:
        if log.student:
            StudentService.prepare_student_response(log.student)
            
    return {
        "total": total,
        "items": logs,
        "skip": skip,
        "limit": limit
    }

@router.post("/logs/{log_id}/validate", response_model=schemas.AttendanceLog)
async def validate_log(
    *,
    db: Session = Depends(deps.get_db),
    log_id: int,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    return await AttendanceService.validate_log(db, log_id)

@router.get("/stats/occupancy", response_model=schemas.OccupancyPagination)
def get_occupancy_stats(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    grade: Optional[str] = None,
    section: Optional[str] = None,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user)
):
    """
    Retorna la ocupación en tiempo real y flujo neto del día. Solo Admin.
    """
    return AttendanceService.get_occupancy_stats(
        db, skip=skip, limit=limit, grade=grade, section=section
    )

@router.get("/stats/percentages", response_model=schemas.AttendancePercentage)
def get_attendance_percentages(
    period: str = Query("month", description="Filtro temporal: 'day', 'week', 'month'"),
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user)
):
    """
    Retorna los porcentajes de asistencia (Presente, Tardanza, Ausente) calculados 
    estrictamente para el mes actual, excluyendo feriados. Solo Admin.
    """
    return AttendanceService.get_attendance_percentages(db=db, period=period)

@router.get("/daily-status", response_model=schemas.DailyAttendancePagination)
def get_daily_attendance_status(
    grade: str,
    section: str,
    skip: int = 0,
    limit: int = 50,
    schedule_id: int = None,
    date_str: str = None, # YYYY-MM-DD
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    return AttendanceService.get_daily_status(db, grade, section, skip, limit, schedule_id, date_str)
@router.get("/student/{dni}/absences")
def get_student_absences(
    dni: str,
    days_back: int = 30,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    return AttendanceService.get_student_absences(db, dni, days_back)
@router.get("/stats/monthly")
def get_monthly_stats(
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    return AttendanceService.get_monthly_stats(db)

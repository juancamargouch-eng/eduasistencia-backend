from typing import Optional, Tuple
from sqlalchemy.orm import Session
from datetime import datetime, date, timedelta
from sqlalchemy import func
import json

from app import models, schemas
from app.services.face_recognition import compare_faces
from app.core.websocket_manager import manager
from app.services.telegram_service import TelegramService

class AttendanceService:
    @staticmethod
    async def verify_attendance(
        db: Session,
        qr_code: Optional[str] = None,
        dni: Optional[str] = None,
        face_descriptor: str = "",
        event_type: str = "ENTRY"
    ) -> models.AttendanceLog:
        # 1. Look up student
        student = None
        if qr_code:
            student = db.query(models.Student).filter(models.Student.qr_code_hash == qr_code).first()
        elif dni:
            student = db.query(models.Student).filter(models.Student.dni == dni).first()
        
        if not student:
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail="Estudiante no encontrado")

        if not student.is_active:
            from fastapi import HTTPException
            raise HTTPException(status_code=400, detail="Estudiante inactivo")

        failure_reason = None
        verification_status = False
        confidence_score = 0.0
        status = "PRESENT"

        # 2. Process Face Descriptor
        try:
            descriptor = json.loads(face_descriptor)
        except:
            failure_reason = "Descriptor Facial Inválido"
            
        if not failure_reason:
            # 3. Compare with stored encoding
            if student.face_encoding:
                match, distance = compare_faces(student.face_encoding, descriptor)
                if match:
                    verification_status = True
                    confidence_score = max(0.0, min(1.0, 1.0 - (distance / 0.9))) 
                    
                    # CHECK FOR DUPLICATES
                    today = date.today()
                    existing_log = db.query(models.AttendanceLog).filter(
                        models.AttendanceLog.student_id == student.id,
                        models.AttendanceLog.event_type == event_type,
                        models.AttendanceLog.verification_status == True,
                        func.date(models.AttendanceLog.timestamp) == today
                    ).first()
                    
                    if existing_log:
                        from fastapi import HTTPException
                        # FOR TESTING: Trigger notification even if it's a duplicate
                        await TelegramService.send_attendance_notification(db, student, existing_log)
                        
                        raise HTTPException(
                            status_code=409, 
                            detail={
                                "message": f"Asistencia ya registrada para hoy",
                                "timestamp": existing_log.timestamp.strftime("%H:%M:%S"),
                                "student": {
                                    "full_name": student.full_name,
                                    "photo_url": student.photo_url,
                                    "grade": student.grade,
                                    "section": student.section
                                }
                            }
                        )

                    # 4. CHECK SCHEDULE / TOLERANCE
                    if event_type == "ENTRY" and student.schedule:
                        current_time = datetime.now().time()
                        schedule_start = student.schedule.start_time
                        tolerance = student.schedule.tolerance_minutes or 0
                        
                        dummy_date = datetime.now().date()
                        start_dt = datetime.combine(dummy_date, schedule_start)
                        deadline_dt = start_dt + timedelta(minutes=tolerance)
                        
                        if datetime.now() > deadline_dt:
                            status = "LATE"
                else:
                    failure_reason = "Rostro No Coincide"
            else:
                 failure_reason = "Estudiante sin datos faciales"
        
        # 5. Log Attendance
        log = models.AttendanceLog(
            student_id=student.id,
            verification_status=verification_status,
            confidence_score=confidence_score,
            failure_reason=failure_reason,
            event_type=event_type,
            status=status if verification_status else "ABSENT" 
        )
        db.add(log)
        db.commit()
        db.refresh(log)
        
        # 6. Notify via Telegram (if successful)
        if verification_status:
            await TelegramService.send_attendance_notification(db, student, log)
            
        # 7. Broadcast via WebSocket
        await manager.broadcast({
            "event": "new_attendance",
            "data": {
                "id": log.id,
                "student_name": student.full_name,
                "photo_url": student.photo_url,
                "status": log.status,
                "timestamp": log.timestamp.isoformat(),
                "confidence_score": log.confidence_score,
                "verification_status": log.verification_status
            }
        })
        
        return log

    @staticmethod
    async def validate_log(db: Session, log_id: int) -> models.AttendanceLog:
        from fastapi import HTTPException
        log = db.query(models.AttendanceLog).filter(models.AttendanceLog.id == log_id).first()
        if not log:
            raise HTTPException(status_code=404, detail="Log not found")
        
        log.verification_status = True
        log.confidence_score = 1.0
        log.failure_reason = "Validado Manualmente por Admin"
        db.commit()
        db.refresh(log)
        
        # Notify via Telegram upon manual validation
        await TelegramService.send_attendance_notification(db, log.student, log)
        
        # Broadcast update via WebSocket
        await manager.broadcast({
            "event": "log_validated",
            "data": {
                "id": log.id,
                "student_name": log.student.full_name,
                "status": log.status,
                "confidence_score": log.confidence_score,
                "verification_status": log.verification_status
            }
        })
        
        return log

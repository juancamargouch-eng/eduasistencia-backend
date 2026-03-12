from typing import Optional, Tuple
from sqlalchemy.orm import Session
from datetime import datetime, date, timedelta
from sqlalchemy import func
import json

from app import models, schemas
from app.services.face_recognition import compare_faces
from app.core.websocket_manager import manager
from app.services.telegram_service import TelegramService
from app.services.student_service import StudentService

class AttendanceService:
    @staticmethod
    async def verify_attendance(
        db: Session,
        qr_code: Optional[str] = None,
        dni: Optional[str] = None,
        face_descriptor: str = "",
        event_type: Optional[str] = None # Agnosticism
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

        # 2. DETERMINAR TIPO DE EVENTO (ENTRY o EXIT)
        today = date.today()
        # Buscar el registro de entrada del día de hoy
        existing_entry = db.query(models.AttendanceLog).filter(
            models.AttendanceLog.student_id == student.id,
            models.AttendanceLog.event_type == "ENTRY",
            models.AttendanceLog.verification_status == True,
            func.date(models.AttendanceLog.timestamp) == today
        ).first()

        current_event_type = "ENTRY"
        if existing_entry:
            # Si ya hay entrada, verificar salida
            existing_exit = db.query(models.AttendanceLog).filter(
                models.AttendanceLog.student_id == student.id,
                models.AttendanceLog.event_type == "EXIT",
                models.AttendanceLog.verification_status == True,
                func.date(models.AttendanceLog.timestamp) == today
            ).first()

            if existing_exit:
                from fastapi import HTTPException
                raise HTTPException(
                    status_code=409,
                    detail={
                        "message": "Jornada completada por hoy",
                        "timestamp": f"E: {existing_entry.timestamp.strftime('%H:%M')} | S: {existing_exit.timestamp.strftime('%H:%M')}",
                        "student": StudentService.prepare_student_response(student, for_kiosk=True).dict()
                    }
                )

            # BLOQUEO DE 2 HORAS (Cool-down)
            time_diff = datetime.now() - existing_entry.timestamp
            if time_diff < timedelta(hours=2):
                from fastapi import HTTPException
                raise HTTPException(
                    status_code=409,
                    detail={
                        "message": "Ya marcó su entrada",
                        "timestamp": existing_entry.timestamp.strftime("%H:%M:%S"),
                        "student": StudentService.prepare_student_response(student, for_kiosk=True).dict()
                    }
                )
            
            # Si pasaron más de 2 horas, es una Salida
            current_event_type = "EXIT"

        failure_reason = None
        verification_status = False
        confidence_score = 0.0
        status = "PRESENT"

        # 3. Process Face Descriptor
        try:
            descriptor = json.loads(face_descriptor)
        except:
            failure_reason = "Descriptor Facial Inválido"
            
        if not failure_reason:
            # 4. Compare with stored encoding
            if student.face_encoding:
                match, distance = compare_faces(student.face_encoding, descriptor)
                if match:
                    verification_status = True
                    confidence_score = max(0.0, min(1.0, 1.0 - (distance / 0.9))) 
                    
                    # 5. CHECK SCHEDULE / TOLERANCE (Solo para ENTRADAS)
                    if current_event_type == "ENTRY" and student.schedule:
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
        
        # 6. Log Attendance
        log = models.AttendanceLog(
            student_id=student.id,
            verification_status=verification_status,
            confidence_score=confidence_score,
            failure_reason=failure_reason,
            event_type=current_event_type,
            status=status if verification_status else "ABSENT" 
        )
        db.add(log)
        db.commit()
        db.refresh(log)
        
        # 7. Notify via Telegram (if successful)
        if verification_status:
            await TelegramService.send_attendance_notification(db, student, log)
            
        # 8. Broadcast via WebSocket
        await manager.broadcast({
            "event": "new_attendance",
            "data": {
                "id": log.id,
                "student_name": student.full_name,
                "photo_url": StudentService.prepare_student_response(student, for_kiosk=True).photo_url,
                "status": log.status,
                "event_type": log.event_type,
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

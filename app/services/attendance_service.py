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
        event_type: Optional[str] = None,
        device_source: Optional[str] = None,
        skip_biometrics: bool = False
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
            if skip_biometrics:
                verification_status = True
                confidence_score = 1.0
            # 4. Compare with stored encoding
            elif student.face_encoding:
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
            status=status if verification_status else "ABSENT",
            device_source=device_source
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

    @staticmethod
    def get_occupancy_stats(
        db: Session,
        skip: int = 0,
        limit: int = 50,
        grade: Optional[str] = None,
        section: Optional[str] = None,
    ):
        """
        Returns the current occupancy status avoiding N+1 queries.
        """
        from sqlalchemy import func, and_, not_, exists
        today = datetime.now().date()
        
        # 1. Encontrar todos los ENTRY de hoy
        entries_today = db.query(
            models.AttendanceLog.student_id,
            func.max(models.AttendanceLog.timestamp).label("entry_time") # Usar la última hora de entrada
        ).filter(
            models.AttendanceLog.event_type == "ENTRY",
            models.AttendanceLog.verification_status == True,
            func.date(models.AttendanceLog.timestamp) == today
        ).group_by(models.AttendanceLog.student_id).subquery()

        # 2. Encontrar todos los EXIT de hoy
        exits_today = db.query(
            models.AttendanceLog.student_id
        ).filter(
            models.AttendanceLog.event_type == "EXIT",
            models.AttendanceLog.verification_status == True,
            func.date(models.AttendanceLog.timestamp) == today
        ).group_by(models.AttendanceLog.student_id).subquery()

        # 3. Base de Estudiantes activos
        base_query = db.query(models.Student, entries_today.c.entry_time).join(
            entries_today, models.Student.id == entries_today.c.student_id
        ).outerjoin(
            exits_today, models.Student.id == exits_today.c.student_id
        ).filter(
            models.Student.is_active == True,
            exits_today.c.student_id == None  # Solamente los que NO tienen salida
        )
        
        # Filtros opcionales
        if grade:
            base_query = base_query.filter(models.Student.grade == grade)
        if section:
            base_query = base_query.filter(models.Student.section == section)

        # Totales
        total_in_campus = base_query.count()
        results = base_query.order_by(entries_today.c.entry_time.desc()).offset(skip).limit(limit).all()

        # Contadores Globales de la sede (por grado/sección)
        entries_query = db.query(func.count(models.AttendanceLog.id)).join(
            models.Student, models.AttendanceLog.student_id == models.Student.id
        ).filter(
            func.date(models.AttendanceLog.timestamp) == today,
            models.AttendanceLog.event_type == "ENTRY",
            models.AttendanceLog.verification_status == True
        )
        
        exits_query = db.query(func.count(models.AttendanceLog.id)).join(
            models.Student, models.AttendanceLog.student_id == models.Student.id
        ).filter(
            func.date(models.AttendanceLog.timestamp) == today,
            models.AttendanceLog.event_type == "EXIT",
            models.AttendanceLog.verification_status == True
        )
        
        if grade:
            entries_query = entries_query.filter(models.Student.grade == grade)
            exits_query = exits_query.filter(models.Student.grade == grade)
        if section:
            entries_query = entries_query.filter(models.Student.section == section)
            exits_query = exits_query.filter(models.Student.section == section)
            
        total_entries = entries_query.scalar() or 0
        total_exits = exits_query.scalar() or 0

        # Formateando sin tocar N+1 (porque entry_time ya vino en el tuple)
        present_students = []
        for student, entry_time in results:
            s_processed = StudentService.prepare_student_response(student, for_kiosk=True)
            present_students.append({
                "id": s_processed.id,
                "first_name": s_processed.first_name,
                "last_name": s_processed.last_name,
                "full_name": s_processed.full_name,
                "photo_url": s_processed.photo_url,
                "grade": s_processed.grade,
                "section": s_processed.section,
                "dni": s_processed.dni,
                "entry_time": entry_time
            })

        return {
            "total_entries": total_entries,
            "total_exits": total_exits,
            "current_count": total_in_campus,
            "items": present_students,
            "total": total_in_campus,
            "skip": skip,
            "limit": limit
        }

    @staticmethod
    def get_daily_status(
        db: Session,
        grade: str,
        section: str,
        skip: int = 0,
        limit: int = 50,
        schedule_id: Optional[int] = None,
        date_str: Optional[str] = None
    ):
        """
        O(1) approach for daily attendance.
        """
        from app.utils.calendar import is_non_working_day, get_holiday_name, is_weekend
        
        if date_str:
            try:
                query_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            except ValueError:
                from fastapi import HTTPException
                raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
        else:
            query_date = datetime.now().date()

        _is_holiday = is_non_working_day(query_date)
        _name = get_holiday_name(query_date)
        holiday_label = "Fin de Semana" if is_weekend(query_date) and not _name else _name
        
        base_query = db.query(models.Student).filter(
            models.Student.grade == grade,
            models.Student.section == section,
            models.Student.is_active == True
        )
        
        if schedule_id:
            base_query = base_query.filter(models.Student.schedule_id == schedule_id)
            
        total_students_count = base_query.count()
        students = base_query.offset(skip).limit(limit).all()
        student_ids = [s.id for s in students]

        # Logs summary global
        all_students_ids_subquery = base_query.with_entities(models.Student.id).subquery()
        summary_logs = db.query(
            models.AttendanceLog.status, func.count(models.AttendanceLog.id)
        ).filter(
            models.AttendanceLog.student_id.in_(all_students_ids_subquery),
            models.AttendanceLog.verification_status == True,
            models.AttendanceLog.event_type == "ENTRY",
            func.date(models.AttendanceLog.timestamp) == query_date
        ).group_by(models.AttendanceLog.status).all()

        present_count = 0
        late_count = 0
        for status, count in summary_logs:
            if status == "LATE": late_count += count
            if status == "PRESENT": present_count += count
        
        absent_count = total_students_count - (present_count + late_count)

        # Logs específicos de los estudiantes paginados
        page_logs = db.query(models.AttendanceLog).filter(
            models.AttendanceLog.student_id.in_(student_ids),
            models.AttendanceLog.verification_status == True,
            models.AttendanceLog.event_type == "ENTRY",
            func.date(models.AttendanceLog.timestamp) == query_date
        ).all()
        logs_map = {log.student_id: log for log in page_logs}

        results = []
        for s in students:
            log = logs_map.get(s.id)
            status = log.status if log else "ABSENT"
            entry_time = log.timestamp if log else None
            
            results.append({
                "id": s.id,
                "full_name": s.full_name,
                "photo_url": StudentService.prepare_student_response(s).photo_url,
                "status": status,
                "entry_time": entry_time
            })
            
        return {
            "date": query_date.isoformat(),
            "is_non_working_day": _is_holiday,
            "holiday_name": holiday_label,
            "summary": {"total": total_students_count, "present": present_count, "late": late_count, "absent": absent_count},
            "items": results,
            "total": total_students_count,
            "skip": skip,
            "limit": limit
        }

    @staticmethod
    def get_monthly_stats(db: Session):
        """
        Genera el dashboard chart sin procesar bucles Pythonicos pesados.
        """
        from app.utils.calendar import is_non_working_day
        
        today = date.today()
        start_date = today - timedelta(days=29) 
        
        total_students = db.query(func.count(models.Student.id)).filter(models.Student.is_active == True).scalar() or 0
        
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
        
        daily_data = {}
        current_dt = start_date
        while current_dt <= today:
            if not is_non_working_day(current_dt):
                daily_data[current_dt.isoformat()] = {
                    "date": current_dt.strftime("%d/%m"),
                    "full_date": current_dt.isoformat(),
                    "present": 0, "late": 0, "absent": total_students
                }
            current_dt += timedelta(days=1)
            
        for log_date, status, count in logs:
            date_str = log_date.isoformat() if hasattr(log_date, 'isoformat') else str(log_date)
            if date_str in daily_data:
                 if status == "PRESENT":
                     daily_data[date_str]["present"] += count
                     daily_data[date_str]["absent"] -= count
                 elif status == "LATE":
                     daily_data[date_str]["late"] += count
                     daily_data[date_str]["absent"] -= count
                    
        grade_stats = db.query(
            models.Student.grade,
            models.AttendanceLog.status,
            func.count(models.AttendanceLog.id)
        ).join(models.AttendanceLog, models.Student.id == models.AttendanceLog.student_id).filter(
            models.AttendanceLog.verification_status == True,
            models.AttendanceLog.event_type == "ENTRY",
            models.AttendanceLog.timestamp >= start_date
        ).group_by(models.Student.grade, models.AttendanceLog.status).all()
        
        grades_perf = {}
        # Pre-cargar cantidad de alumnos activos por grado
        grade_counts = db.query(
            models.Student.grade, func.count(models.Student.id)
        ).filter(models.Student.is_active == True).group_by(models.Student.grade).all()
        grade_counts_map = {gc[0]: gc[1] for gc in grade_counts}

        for grade, status, count in grade_stats:
            if grade not in grades_perf:
                grades_perf[grade] = {"name": grade, "present": 0, "late": 0, "total": grade_counts_map.get(grade, 1)}
            if status == "PRESENT": grades_perf[grade]["present"] += count
            if status == "LATE": grades_perf[grade]["late"] += count

        return {
            "daily": sorted(list(daily_data.values()), key=lambda x: x["full_date"]),
            "grades": sorted(list(grades_perf.values()), key=lambda x: x["name"]),
            "summary": {"total_students": total_students, "period_days": len(daily_data)}
        }

    @staticmethod
    def get_attendance_percentages(db: Session, period: str):
        """
        Calcula porcentajes de Presentes, Tardanzas y Faltas strictly para el MES ACTUAL.
        Determina días laborables excluyendo Feriados de Perú y Fines de semana.
        """
        from app.utils.calendar import is_non_working_day
        from fastapi import HTTPException
        
        now = datetime.now()
        today_date = now.date()
        
        if period not in ["day", "week", "month"]:
            raise HTTPException(status_code=400, detail="Periodo inválido. Use 'day', 'week' o 'month'")
            
        first_day_of_month = today_date.replace(day=1)
        
        if period == "month":
            start_date = first_day_of_month
            end_date = today_date
        elif period == "week":
            # Monday of the current week
            start_date = today_date - timedelta(days=today_date.weekday())
            # Enforce current month boundary
            if start_date < first_day_of_month:
                start_date = first_day_of_month
            end_date = today_date
        else: # "day"
            start_date = today_date
            end_date = today_date

        # Total de estudiantes activos
        total_active_students = db.query(models.Student).filter(models.Student.is_active == True).count()
        
        # Encontrar días laborables en ese bloque del mes
        working_days = 0
        current_date = start_date
        while current_date <= end_date:
            if not is_non_working_day(current_date):
                working_days += 1
            current_date += timedelta(days=1)
            
        total_expected_attendances = total_active_students * working_days
        
        # Caso borde (Fin de semana / feriado y modo "day")
        if total_expected_attendances == 0:
            return {
                "present": 0.0,
                "late": 0.0,
                "absent": 0.0,
                "total_expected": 0,
                "period": period
            }
            
        summary_logs = db.query(
            models.AttendanceLog.status, func.count(models.AttendanceLog.id)
        ).filter(
            models.AttendanceLog.verification_status == True,
            models.AttendanceLog.event_type == "ENTRY",
            func.date(models.AttendanceLog.timestamp) >= start_date,
            func.date(models.AttendanceLog.timestamp) <= end_date
        ).group_by(models.AttendanceLog.status).all()
        
        present_count = 0
        late_count = 0
        
        for status, count in summary_logs:
            if status == "PRESENT":
                present_count += count
            elif status == "LATE":
                late_count += count
                
        absent_count = total_expected_attendances - (present_count + late_count)
        if absent_count < 0:
            absent_count = 0
            
        perc_present = round((present_count / total_expected_attendances) * 100, 1)
        perc_late = round((late_count / total_expected_attendances) * 100, 1)
        perc_absent = round((absent_count / total_expected_attendances) * 100, 1)
        
        return {
            "present": perc_present,
            "late": perc_late,
            "absent": perc_absent,
            "total_expected": total_expected_attendances,
            "period": period
        }

    @staticmethod
    def get_student_absences(db: Session, dni: str, days_back: int = 30):
        from app.utils.calendar import is_non_working_day

        student = db.query(models.Student).filter(models.Student.dni == dni).first()
        if not student:
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail="Estudiante no encontrado")
            
        today = date.today()
        start_date = today - timedelta(days=days_back)
        
        logs = db.query(func.date(models.AttendanceLog.timestamp)).filter(
            models.AttendanceLog.student_id == student.id,
            models.AttendanceLog.verification_status == True,
            models.AttendanceLog.event_type == "ENTRY",
            models.AttendanceLog.timestamp >= start_date
        ).all()
        attendance_dates = {log[0] for log in logs}
        
        justifications = db.query(models.Justification.date).filter(
            models.Justification.student_id == student.id,
            models.Justification.date >= start_date
        ).all()
        justification_dates = {j[0] for j in justifications}
        
        absences = []
        current_date = start_date
        while current_date < today:
            if is_non_working_day(current_date):
                 current_date += timedelta(days=1)
                 continue
                
            if current_date not in attendance_dates and current_date not in justification_dates:
                absences.append({
                    "date": current_date.isoformat(),
                    "day_name": current_date.strftime("%A"),
                    "status": "UNJUSTIFIED"
                })
            current_date += timedelta(days=1)
            
        return {
            "student": {
                "id": student.id,
                "full_name": student.full_name,
                "grade": student.grade,
                "section": student.section,
                "photo_url": StudentService.prepare_student_response(student).photo_url,
                "schedule": {"name": student.schedule.name, "start_time": student.schedule.start_time.strftime("%H:%M")} if student.schedule else None
            },
            "absences": absences
        }

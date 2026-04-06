"""
Diagnóstico preciso del Error 500 en /api/attendance/verify
Simula exactamente lo que ocurre cuando un alumno marca por segunda vez.
"""
import sys, os
sys.path.append(os.getcwd())

from datetime import datetime, date, timedelta
from sqlalchemy import func
from app.config.database import SessionLocal
from app import models
from app.services.student_service import StudentService

db = SessionLocal()

try:
    # 1. Buscar un alumno con entrada hoy
    today = date.today()
    existing_entry = db.query(models.AttendanceLog).filter(
        models.AttendanceLog.event_type == "ENTRY",
        models.AttendanceLog.verification_status == True,
        func.date(models.AttendanceLog.timestamp) == today
    ).first()

    if not existing_entry:
        print("No hay entradas hoy. No se puede reproducir el error.")
        sys.exit(0)

    student = existing_entry.student
    print(f"Alumno: {student.full_name}")
    print(f"Timestamp de entrada: {existing_entry.timestamp}")
    print(f"Tipo de timestamp: {type(existing_entry.timestamp)}")
    print(f"Timezone info: {existing_entry.timestamp.tzinfo}")
    print()

    # 2. Reproducir la operación que causa el Error 500
    print("--- PRUEBA 1: Resta de datetime (línea 81 del servicio) ---")
    try:
        time_diff = datetime.now() - existing_entry.timestamp
        print(f"OK: time_diff = {time_diff}")
    except TypeError as e:
        print(f"ERROR ENCONTRADO: {e}")
        print("CAUSA RAÍZ: datetime.now() no tiene timezone, pero el timestamp de la DB sí.")
        print("SOLUCIÓN: Usar datetime.now(existing_entry.timestamp.tzinfo) o .replace(tzinfo=None)")

    # 3. Reproducir la generación de la foto firmada
    print()
    print("--- PRUEBA 2: Generación de photo_url para el modal ---")
    try:
        prepared = StudentService.prepare_student_response(student, for_kiosk=True)
        print(f"OK: photo_url = {prepared.get('photo_url', 'N/A')}")
    except Exception as e:
        print(f"ERROR ENCONTRADO: {e}")

    # 4. Reproducir la serialización del detalle 409
    print()
    print("--- PRUEBA 3: Serialización del detalle del error 409 ---")
    try:
        import json
        entry_time = existing_entry.timestamp.strftime("%H:%M:%S") if hasattr(existing_entry.timestamp, 'strftime') else str(existing_entry.timestamp)
        detail = {
            "message": "Ya marcó su entrada",
            "timestamp": entry_time,
            "student": {
                "full_name": getattr(student, 'full_name', "Estudiante"),
                "photo_url": prepared.get("photo_url", "")
            }
        }
        json_str = json.dumps(detail, default=str)
        print(f"OK: JSON serializable. Longitud: {len(json_str)} chars")
    except Exception as e:
        print(f"ERROR ENCONTRADO: {e}")

    # 5. Reproducir la validación de Pydantic del response_model
    print()
    print("--- PRUEBA 4: Validación Pydantic de AttendanceLogKiosk ---")
    try:
        from app.schemas import AttendanceLogKiosk
        test_data = {
            "id": 999,
            "timestamp": datetime.now(),
            "verification_status": True,
            "failure_reason": None,
            "device_source": None,
            "event_type": "ENTRY",
            "status": "PRESENT",
            "student": {
                "full_name": "TEST",
                "first_name": "TEST",
                "last_name": "TEST",
                "grade": "1",
                "section": "A",
                "photo_url": None
            }
        }
        validated = AttendanceLogKiosk.model_validate(test_data)
        print(f"OK: Pydantic validation passed")
    except Exception as e:
        print(f"ERROR ENCONTRADO: {e}")

    print()
    print("=== DIAGNÓSTICO COMPLETO ===")

except Exception as e:
    import traceback
    traceback.print_exc()
finally:
    db.close()

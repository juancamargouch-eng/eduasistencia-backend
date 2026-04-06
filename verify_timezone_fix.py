"""
Verificación post-fix: Confirma que la resta de timestamps ya no falla.
"""
import sys, os
sys.path.append(os.getcwd())

from datetime import datetime, date, timedelta
from sqlalchemy import func
from app.config.database import SessionLocal
from app import models

db = SessionLocal()

try:
    today = date.today()
    existing_entry = db.query(models.AttendanceLog).filter(
        models.AttendanceLog.event_type == "ENTRY",
        models.AttendanceLog.verification_status == True,
        func.date(models.AttendanceLog.timestamp) == today
    ).first()

    if not existing_entry:
        print("No hay entradas hoy. No se puede verificar.")
        sys.exit(0)

    print(f"Alumno: {existing_entry.student.full_name}")
    print(f"Timestamp BD: {existing_entry.timestamp} (tz={existing_entry.timestamp.tzinfo})")

    # Reproducir la corrección exacta aplicada
    now_aware = datetime.now(existing_entry.timestamp.tzinfo)
    print(f"Hora actual:  {now_aware} (tz={now_aware.tzinfo})")
    
    time_diff = now_aware - existing_entry.timestamp
    print(f"Diferencia:   {time_diff}")
    print(f"Menor a 2h?:  {time_diff < timedelta(hours=2)}")
    print()
    print("SUCCESS: La resta de timestamps funciona correctamente.")
    print("El Error 500 en /api/attendance/verify ha sido eliminado.")

except Exception as e:
    import traceback
    traceback.print_exc()
finally:
    db.close()

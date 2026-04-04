import sys
import os
import random
import json
from sqlalchemy.orm import Session
from datetime import datetime, date

# Añadir el directorio raíz al path para importar la app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import models
from app.config.database import SessionLocal

def simulate_full_attendance():
    db = SessionLocal()
    try:
        # 1. Obtener todos los estudiantes activos
        students = db.query(models.Student).filter(models.Student.is_active == True).all()
        print(f"Iniciando simulación de asistencia para {len(students)} alumnos...")

        today = date.today()
        count = 0
        
        # 2. Registrar ENTRADA para cada uno
        for student in students:
            # Crear log de entrada
            log = models.AttendanceLog(
                student_id=student.id,
                verification_status=True,
                confidence_score=1.0,
                failure_reason="Simulación de Stress Test (Masiva)",
                event_type="ENTRY",
                status="PRESENT", # Todos temprano por ahora
                timestamp=datetime.now()
            )
            db.add(log)
            count += 1
            
            # Guardar en lotes de 100
            if count % 100 == 0:
                db.commit()
                print(f"Progreso: {count}/{len(students)} asistencias registradas")

        db.commit()
        print(f"✅ Éxito final: {count} asistencias registradas para hoy ({today})")

    except Exception as e:
        db.rollback()
        print(f"❌ Error durante la simulación: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    simulate_full_attendance()

import sys
import os
import json
from datetime import datetime

# Añadir el path para importar la app
sys.path.append(os.getcwd())

try:
    from app.services.attendance_service import AttendanceService
    from app.services.student_service import StudentService
    from app.config.database import SessionLocal
    from app import models, schemas

    db = SessionLocal()
    # Buscar cualquier estudiante para probar
    student = db.query(models.Student).first()
    
    if student:
        print(f"Probando prepare_student_response para: {student.full_name}")
        res = StudentService.prepare_student_response(student, for_kiosk=True)
        print(f"Tipo de retorno: {type(res)}")
        
        # Intentar simular lo que falla en AttendanceService
        try:
            student_dict = res.dict()
            print("SUCCESS: .dict() funcionó")
            print(json.dumps(student_dict, indent=2))
        except Exception as e:
            print(f"ERROR: .dict() falló: {e}")
            
except Exception as e:
    import traceback
    traceback.print_exc()
finally:
    if 'db' in locals():
        db.close()

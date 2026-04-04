from app.config.database import SessionLocal
from app.models.student import Student

db = SessionLocal()
try:
    student = db.query(Student).filter(Student.dni == "11223344").first()
    if student:
        print(f"--- Datos del Estudiante ---")
        print(f"Nombre: {student.full_name}")
        print(f"DNI: {student.dni}")
        print(f"Photo URL: {student.photo_url}")
    else:
        print("Estudiante no encontrado con DNI 11223344")
finally:
    db.close()

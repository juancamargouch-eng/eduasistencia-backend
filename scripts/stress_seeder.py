import sys
import os
import random
import uuid
import json
from sqlalchemy.orm import Session
from datetime import datetime

# Añadir el directorio raíz al path para importar la app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import models
from app.config.database import SessionLocal

def generate_fake_descriptor():
    # Genera un vector de 224 floats aleatorios entre -0.1 y 0.2
    return [random.uniform(-0.1, 0.2) for _ in range(224)]

def seed_stress_data(num_students=2000):
    db = SessionLocal()
    try:
        # 0. Limpiar datos de prueba previos
        print("Limpiando datos de prueba anteriores...")
        # Primero borrar logs asociados a estudiantes de prueba
        test_student_ids = [s.id for s in db.query(models.Student.id).filter(models.Student.photo_url == "eduasistencia/fotos-estudiantes/placeholder.jpg").all()]
        if test_student_ids:
            db.query(models.AttendanceLog).filter(models.AttendanceLog.student_id.in_(test_student_ids)).delete(synchronize_session=False)
            db.commit()
            
        db.query(models.Student).filter(models.Student.photo_url == "eduasistencia/fotos-estudiantes/placeholder.jpg").delete(synchronize_session=False)
        db.commit()

        # 1. Obtener horarios disponibles
        schedules = db.query(models.Schedule).all()
        if not schedules:
            print("Error: No hay horarios en la base de datos.")
            return
        
        schedule_ids = [s.id for s in schedules]
        
        grades = [
            "1 PRIMARIA", "2 PRIMARIA", "3 PRIMARIA", "4 PRIMARIA", "5 PRIMARIA", "6 PRIMARIA",
            "1 SECUNDARIA", "2 SECUNDARIA", "3 SECUNDARIA", "4 SECUNDARIA", "5 SECUNDARIA"
        ]
        sections = ["A", "B", "C"]
        
        first_names = ["JUAN", "MARIA", "LUIS", "ANA", "CARLOS", "ELENA", "PEDRO", "SOFIA", "DIEGO", "LUCIA", "MIGUEL", "VALERIA"]
        last_names = ["GARCIA", "RODRIGUEZ", "LOPEZ", "MARTINEZ", "PEREZ", "GONZALEZ", "SANCHEZ", "ROMERO", "TORRES", "RUIZ"]
        
        print(f"Iniciando seeding de {num_students} alumnos...")
        
        students_to_add = []
        for i in range(num_students):
            fn = random.choice(first_names)
            ln = f"{random.choice(last_names)} {random.choice(last_names)}"
            full_name = f"{ln}, {fn}"
            dni = f"{random.randint(10000000, 99999999)}"
            
            student = models.Student(
                first_name=fn,
                last_name=ln,
                full_name=full_name,
                grade=random.choice(grades),
                section=random.choice(sections),
                dni=dni,
                qr_code_hash=str(uuid.uuid4()),
                face_encoding=generate_fake_descriptor(),
                is_active=True,
                schedule_id=random.choice(schedule_ids),
                photo_url="eduasistencia/fotos-estudiantes/placeholder.jpg",
                notify_telegram=False
            )
            students_to_add.append(student)
            
            if len(students_to_add) >= 100:
                db.bulk_save_objects(students_to_add)
                db.commit()
                students_to_add = []
                print(f"Progreso: {i+1}/{num_students}")
                
        if students_to_add:
            db.bulk_save_objects(students_to_add)
            db.commit()
            
        print(f"✅ Éxito: {num_students} alumnos creados correctamente.")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error durante el seeding: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_stress_data(2000)

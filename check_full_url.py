from app.config.database import SessionLocal
from app.models.student import Student
import os
from dotenv import load_dotenv

load_dotenv()

db = SessionLocal()
try:
    student = db.query(Student).filter(Student.dni == "11223344").first()
    if student:
        print(f"--- Datos del Estudiante ---")
        print(f"Nombre Completo: {student.full_name}")
        print(f"Photo URL Almacenada: {student.photo_url}")
        
        # Simular cómo se construye la URL en el frontend/backend
        bucket = os.getenv("S3_BUCKET")
        region = os.getenv("S3_REGION", "us-east-1")
        
        if student.photo_url:
            if student.photo_url.startswith("http"):
                print(f"URL Completa (desde DB): {student.photo_url}")
            else:
                # Si solo es el nombre del archivo
                full_url = f"https://{bucket}.s3.{region}.amazonaws.com/{student.photo_url}"
                print(f"URL Completa (construida): {full_url}")
    else:
        print("Estudiante no encontrado")
finally:
    db.close()

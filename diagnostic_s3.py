import os
from dotenv import load_dotenv
from app.services.storage_service import StorageService
from app.config.database import SessionLocal
from app.models.student import Student

load_dotenv()

def diagnostic():
    db = SessionLocal()
    try:
        student = db.query(Student).filter(Student.dni == "11223344").first()
        if not student:
            print("ERROR: Estudiante no encontrado.")
            return

        print(f"--- Diagnóstico para {student.full_name} ---")
        key = student.photo_url
        base_path = os.getenv("STORAGE_BASE_PATH", "eduasistencia/fotos-estudiantes")
        
        # El endpoint photo-proxy añade el prefijo si no lo tiene
        if not key.startswith(base_path):
            full_key = f"{base_path}/{key}".replace("//", "/")
        else:
            full_key = key
            
        print(f"Key a verificar en S3: {full_key}")
        
        exists = StorageService.check_file_exists(full_key)
        print(f"¿Existe el archivo en S3?: {'SÍ' if exists else 'NO'}")
        
        if exists:
            url = StorageService.get_presigned_url(full_key)
            print(f"URL Firmada generada: {url}")
        else:
            print("PROBLEMA: La foto está registrada en la DB pero el archivo NO existe en el almacenamiento.")

    finally:
        db.close()

if __name__ == "__main__":
    diagnostic()

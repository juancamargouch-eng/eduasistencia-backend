import os
from dotenv import load_dotenv
from app.config.database import SessionLocal
from app.models.student import Student
from app.services.storage_service import StorageService

load_dotenv()

def audit_photos():
    db = SessionLocal()
    try:
        students = db.query(Student).all()
        print(f"Auditoría de {len(students)} estudiantes...")
        
        base_path = os.getenv("STORAGE_BASE_PATH", "eduasistencia/fotos-estudiantes")
        missing_count = 0
        found_count = 0
        
        for s in students:
            if not s.photo_url:
                continue
                
            key = s.photo_url
            if not key.startswith(base_path):
                full_key = f"{base_path}/{key}".replace("//", "/")
            else:
                full_key = key
                
            exists = StorageService.check_file_exists(full_key)
            if exists:
                found_count += 1
            else:
                missing_count += 1
                print(f"MISSING: {s.full_name} (DNI: {s.dni}) | Key: {full_key}")
                
        print(f"--- RESULTADOS ---")
        print(f"Encontrados en S3: {found_count}")
        print(f"No encontrados: {missing_count}")
    finally:
        db.close()

if __name__ == "__main__":
    audit_photos()

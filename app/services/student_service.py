import os
import uuid
import shutil
import json
import io
from typing import Optional, List, Any
from fastapi import UploadFile, HTTPException
from sqlalchemy.orm import Session
import pandas as pd

from app import models, schemas
from app.services.telegram_service import TelegramService
from app.services.storage_service import StorageService
from app.models.telegram import TelegramConfig

class StudentService:
    @staticmethod
    def prepare_student_response(student: models.Student, for_kiosk: bool = False) -> dict:
        """
        Calculates a signed photo_url without modifying the persistent database object.
        Returns a dictionary for safe JSON serialization.
        """
        if not student:
            return None
            
        # Extract base photo_url
        photo_url = getattr(student, 'photo_url', "")
        
        if photo_url:
            # If it's a full legacy URL, extract the key
            if isinstance(photo_url, str) and photo_url.startswith("http"):
                bucket = os.getenv("AWS_STORAGE_BUCKET_NAME", "pegasus")
                endpoint = os.getenv("AWS_S3_ENDPOINT_URL", "").replace("https://", "")
                marker = f"{bucket}.{endpoint}/"
                if marker in photo_url:
                    photo_url = photo_url.split(marker)[1]
            
            # Convert key to signed proxy URL
            photo_url = StorageService.get_signed_proxy_url(photo_url)
            
        # Return a dictionary instead of a Pydantic object for maximum stability
        # in exception details and WebSocket broadcasts.
        if for_kiosk:
            return {
                "first_name": getattr(student, 'first_name', ""),
                "last_name": getattr(student, 'last_name', ""),
                "full_name": getattr(student, 'full_name', ""),
                "grade": getattr(student, 'grade', ""),
                "section": getattr(student, 'section', ""),
                "photo_url": photo_url
            }
        
        # Default full response for regular API
        return {
            "id": getattr(student, 'id', None),
            "first_name": getattr(student, 'first_name', ""),
            "last_name": getattr(student, 'last_name', ""),
            "full_name": getattr(student, 'full_name', ""),
            "dni": getattr(student, 'dni', ""),
            "grade": getattr(student, 'grade', ""),
            "section": getattr(student, 'section', ""),
            "photo_url": photo_url,
            "qr_code_hash": getattr(student, 'qr_code_hash', ""),
            "is_active": getattr(student, 'is_active', True),
            "created_at": getattr(student, 'created_at', None),
            "schedule_id": getattr(student, 'schedule_id', None),
            "telegram_chat_id": getattr(student, 'telegram_chat_id', None),
            "notify_telegram": getattr(student, 'notify_telegram', True)
        }

    @staticmethod
    def prepare_students_response(students: List[models.Student], for_kiosk: bool = False) -> List[dict]:
        """
        Signs photo_urls for a list of students and returns a list of dictionaries.
        """
        return [StudentService.prepare_student_response(s, for_kiosk) for s in students]

    @staticmethod
    async def create_student(
        db: Session,
        first_name: str,
        last_name: str,
        grade: str,
        section: str,
        file: UploadFile,
        face_descriptor: str,
        dni: str,
        schedule_id: Optional[int] = None,
        telegram_chat_id: Optional[str] = None,
        notify_telegram: bool = True
    ) -> models.Student:
        # Normalization
        first_name = first_name.strip().upper()
        last_name = last_name.strip().upper()
        full_name = f"{last_name}, {first_name}"
        
        # DNI: Only numbers
        dni = "".join(filter(str.isdigit, dni))
        
        # Grade: UPPERCASE and clean
        grade = grade.strip().upper()
        section = section.strip().upper()
        # Face Descriptor: Parse JSON
        try:
            encoding = json.loads(face_descriptor)
            if not isinstance(encoding, list) or len(encoding) != 128:
                raise ValueError("El descriptor debe ser una lista de 128 números")
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Descriptor facial inválido: {str(e)}")

        # Save file to S3
        photo_url = await StorageService.upload_file(file)
            
        qr_code_hash = str(uuid.uuid4())
        
        # Resolve Telegram User ID
        telegram_user_id = None
        if telegram_chat_id:
            config = db.query(TelegramConfig).filter(TelegramConfig.is_active == True).first()
            if config and config.api_id and config.api_hash:
                try:
                    telegram_user_id = await TelegramService.resolve_and_add_contact(
                        config.api_id, config.api_hash, telegram_chat_id, full_name
                    )
                except Exception as e:
                    print(f"DEBUG ERROR resolving Telegram ID: {e}")
        
        student = models.Student(
            first_name=first_name,
            last_name=last_name,
            full_name=full_name,
            grade=grade,
            section=section,
            qr_code_hash=qr_code_hash,
            face_encoding=encoding,
            photo_url=photo_url,
            dni=dni,
            schedule_id=schedule_id,
            telegram_chat_id=telegram_chat_id,
            telegram_user_id=telegram_user_id,
            notify_telegram=notify_telegram
        )
        
        db.add(student)
        db.commit()
        db.refresh(student)
        return student

    @staticmethod
    async def update_student(
        db: Session,
        student_id: int,
        student_in: Optional[schemas.StudentUpdate] = None,
        file: Optional[UploadFile] = None,
        face_descriptor: Optional[str] = None
    ) -> models.Student:
        student = db.query(models.Student).filter(models.Student.id == student_id).first()
        if not student:
            raise HTTPException(status_code=404, detail="Student not found")
            
        if student_in:
            update_data = student_in.dict(exclude_unset=True)
            
            # Resolve Telegram User ID if chat_id changed
            if "telegram_chat_id" in update_data:
                if update_data["telegram_chat_id"]:
                    config = db.query(TelegramConfig).filter(TelegramConfig.is_active == True).first()
                    if config and config.api_id and config.api_hash:
                        try:
                            resolved_user_id = await TelegramService.resolve_and_add_contact(
                                config.api_id, config.api_hash, update_data["telegram_chat_id"], student.full_name
                            )
                            if resolved_user_id:
                                student.telegram_user_id = resolved_user_id
                        except Exception as e:
                            print(f"DEBUG ERROR resolving Telegram ID on update: {e}")
                else:
                    student.telegram_user_id = None

            # Avoid overwriting with manual provided ID if we managed it
            if "telegram_user_id" in update_data and student.telegram_user_id:
                del update_data["telegram_user_id"]

            for field, value in update_data.items():
                if value is None:
                    continue
                    
                if field == "first_name" and isinstance(value, str):
                    value = value.strip().upper()
                elif field == "last_name" and isinstance(value, str):
                    value = value.strip().upper()
                elif field == "dni" and isinstance(value, str):
                    value = "".join(filter(str.isdigit, value))
                
                setattr(student, field, value)
            
            # Update full_name if parts changed
            if "first_name" in update_data or "last_name" in update_data:
                # Ensure we have strings to avoid None + string error
                ln = (student.last_name or "").strip()
                fn = (student.first_name or "").strip()
                student.full_name = f"{ln}, {fn}"

        # Handle Photo Update
        if file:
            # Delete old photo if it exists in S3 (optional, but good practice)
            # if student.photo_url:
            #     StorageService.delete_file(student.photo_url)
            
            new_photo_url = await StorageService.upload_file(file)
            student.photo_url = new_photo_url

        # Handle Face Encoding Update
        if face_descriptor:
            try:
                encoding = json.loads(face_descriptor)
                if isinstance(encoding, list) and len(encoding) == 128:
                    student.face_encoding = encoding
            except:
                pass

        db.add(student)
        db.commit()
        db.refresh(student)
        return student

    @staticmethod
    def delete_student(db: Session, student_id: int) -> models.Student:
        student = db.query(models.Student).filter(models.Student.id == student_id).first()
        if not student:
            raise HTTPException(status_code=404, detail="Student not found")

        try:
            # Delete dependent data
            db.query(models.AttendanceLog).filter(models.AttendanceLog.student_id == student_id).delete()
            db.query(models.Justification).filter(models.Justification.student_id == student_id).delete()

            # Delete photo from S3
            if student.photo_url:
                StorageService.delete_file(student.photo_url)

            db.delete(student)
            db.commit()
            return student
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Error deleting student: {str(e)}")

    @staticmethod
    async def import_students(db: Session, file: UploadFile) -> Any:
        if not file.filename.endswith(('.xlsx', '.xls', '.csv')):
            raise HTTPException(status_code=400, detail="Invalid file format")
            
        contents = await file.read()
        try:
            if file.filename.endswith('.csv'):
                df = pd.read_csv(io.BytesIO(contents))
            else:
                df = pd.read_excel(io.BytesIO(contents))
                
            df.columns = [c.lower().strip() for c in df.columns]
            
            # Map columns
            mapping = {
                'nombre': 'nombre', 'nombres': 'nombre', 'first_name': 'nombre',
                'apellido': 'apellido', 'apellidos': 'apellido', 'last_name': 'apellido',
                'grado': 'grado', 'grade': 'grado',
                'seccion': 'seccion', 'section': 'seccion',
                'dni': 'dni'
            }
            
            df = df.rename(columns=mapping)
            
            # Check for either single 'nombre' (legacy/simple) or 'nombre' + 'apellido'
            if 'apellido' in df.columns and 'nombre' in df.columns:
                required = ['nombre', 'apellido', 'grado', 'seccion', 'dni']
            else:
                required = ['nombre', 'grado', 'seccion', 'dni']

            for col in required:
                if col not in df.columns:
                    raise ValueError(f"Missing column: {col}")

            created_count = 0
            errors = []
            
            for index, row in df.iterrows():
                try:
                    # Normalization for Import
                    fn = str(row['nombre']).strip().upper()
                    ln = str(row.get('apellido', '')).strip().upper()
                    
                    if ln:
                        full_name = f"{ln}, {fn}"
                    else:
                        # Fallback for single name column
                        full_name = fn 
                        # Try to split if contains comma
                        if ',' in fn:
                            ln_part, fn_part = [p.strip() for p in fn.split(',', 1)]
                            ln, fn = ln_part, fn_part
                        else:
                            ln, fn = "", fn
                    
                    dni_clean = "".join(filter(str.isdigit, str(row['dni'])))
                    grade_norm = str(row['grado']).strip().upper()
                    section_norm = str(row['seccion']).strip().upper()

                    new_student = models.Student(
                        first_name=fn,
                        last_name=ln,
                        full_name=full_name,
                        grade=grade_norm,
                        section=section_norm,
                        qr_code_hash=str(uuid.uuid4()),
                        is_active=True,
                        dni=dni_clean
                    )
                    db.add(new_student)
                    created_count += 1
                except Exception as e:
                    errors.append(f"Row {index + 1}: {str(e)}")
                    
            db.commit()
            return {"total_created": created_count, "errors": errors}
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    @staticmethod
    async def enroll_student_by_dni(
        db: Session,
        dni: str,
        file: UploadFile,
        face_descriptor: str
    ) -> models.Student:
        # Clean DNI
        dni = "".join(filter(str.isdigit, dni))
        
        student = db.query(models.Student).filter(models.Student.dni == dni).first()
        if not student:
            raise HTTPException(status_code=404, detail=f"Estudiante con DNI {dni} no encontrado")
            
        try:
            encoding = json.loads(face_descriptor)
            if not isinstance(encoding, list) or len(encoding) != 128:
                raise ValueError("El descriptor debe ser una lista de 128 números")
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Descriptor facial inválido: {str(e)}")

        # Save file to S3
        # Delete old photo if exists
        if student.photo_url:
            StorageService.delete_file(student.photo_url)
        
        new_photo_url = await StorageService.upload_file(file)
            
        student.photo_url = new_photo_url
        student.face_encoding = encoding
        
        db.add(student)
        db.commit()
        db.refresh(student)
        return StudentService.prepare_student_response(student)

    @staticmethod
    async def check_s3_photos(dnis: List[str]) -> List[dict]:
        """
        Checks which DNI.jpg files exist in S3 and returns their presigned URLs.
        """
        results = []
        base_path = os.getenv("STORAGE_BASE_PATH", "eduasistencia/fotos-estudiantes")
        
        for dni in dnis:
            # Clean DNI to be sure
            clean_dni = "".join(filter(str.isdigit, str(dni)))
            if not clean_dni:
                continue
                
            key = f"{base_path}/{clean_dni}.jpg"
            # Also check png just in case
            if not StorageService.check_file_exists(key):
                key = f"{base_path}/{clean_dni}.png"
                if not StorageService.check_file_exists(key):
                    continue
            
            # If exists, generate presigned URL
            url = StorageService.get_presigned_url(key)
            results.append({
                "dni": clean_dni,
                "photo_url": url,
                "s3_key": key
            })
            
        return results

    @staticmethod
    async def enroll_student_by_s3_key(
        db: Session,
        dni: str,
        s3_key: str,
        face_descriptor: str
    ) -> models.Student:
        """
        Enrolls a student using a photo already in S3.
        """
        dni = "".join(filter(str.isdigit, dni))
        student = db.query(models.Student).filter(models.Student.dni == dni).first()
        if not student:
            raise HTTPException(status_code=404, detail=f"Estudiante con DNI {dni} no encontrado")

        try:
            encoding = json.loads(face_descriptor)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Descriptor facial inválido: {str(e)}")

        # No need to delete old photo if we are just "claiming" one from S3 
        # (Though usually the UI will check if it's already there)
        
        student.photo_url = s3_key
        student.face_encoding = encoding
        
        db.add(student)
        db.commit()
        db.refresh(student)
        return StudentService.prepare_student_response(student)

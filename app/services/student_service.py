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
from app.models.telegram import TelegramConfig

class StudentService:
    @staticmethod
    async def create_student(
        db: Session,
        full_name: str,
        grade: str,
        section: str,
        file: UploadFile,
        face_descriptor: str,
        dni: str,
        schedule_id: Optional[int] = None,
        telegram_chat_id: Optional[str] = None,
        notify_telegram: bool = True
    ) -> models.Student:
        try:
            encoding = json.loads(face_descriptor)
            if not isinstance(encoding, list) or len(encoding) != 128:
                raise ValueError("Formato de descriptor inválido")
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Descriptor facial inválido: {str(e)}")

        # Save file to disk
        os.makedirs("backend/static/students", exist_ok=True)
        file_ext = file.filename.split(".")[-1]
        filename = f"{uuid.uuid4()}.{file_ext}"
        file_path = f"backend/static/students/{filename}"
        
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
            
        qr_code_hash = str(uuid.uuid4())
        photo_url = f"/static/students/{filename}"
        
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
        student_in: schemas.StudentUpdate
    ) -> models.Student:
        student = db.query(models.Student).filter(models.Student.id == student_id).first()
        if not student:
            raise HTTPException(status_code=404, detail="Student not found")
            
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
            setattr(student, field, value)

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

            # Delete photo
            if student.photo_url:
                filename = os.path.basename(student.photo_url)
                file_path = f"backend/static/students/{filename}"
                if os.path.exists(file_path):
                    os.remove(file_path)

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
                'nombre': 'nombre', 'full_name': 'nombre',
                'grado': 'grado', 'grade': 'grado',
                'seccion': 'seccion', 'section': 'seccion',
                'dni': 'dni'
            }
            
            df = df.rename(columns=mapping)
            required = ['nombre', 'grado', 'seccion', 'dni']
            for col in required:
                if col not in df.columns:
                    raise ValueError(f"Missing column: {col}")

            created_count = 0
            errors = []
            
            for index, row in df.iterrows():
                try:
                    new_student = models.Student(
                        full_name=str(row['nombre']).strip(),
                        grade=str(row['grado']).strip(),
                        section=str(row['seccion']).strip(),
                        qr_code_hash=str(uuid.uuid4()),
                        is_active=True,
                        dni=str(row['dni']).strip()
                    )
                    db.add(new_student)
                    created_count += 1
                except Exception as e:
                    errors.append(f"Row {index + 1}: {str(e)}")
                    
            db.commit()
            return {"total_created": created_count, "errors": errors}
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

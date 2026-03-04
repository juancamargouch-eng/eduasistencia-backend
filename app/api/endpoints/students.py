from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
import uuid
import json
import asyncio

from app import models, schemas
from app.api import deps
# from ..services.face_recognition import decode_image, get_face_embedding 
# We don't need detection here anymore, client does it.

router = APIRouter()

from app.services.student_service import StudentService

@router.get("/", response_model=List[schemas.Student])
def read_students(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    students = db.query(models.Student).offset(skip).limit(limit).all()
    return students

@router.post("/register", response_model=schemas.Student)
async def create_student(
    *,
    db: Session = Depends(deps.get_db),
    full_name: str = Form(...),
    grade: str = Form(...),
    section: str = Form(...),
    file: UploadFile = File(...),
    face_descriptor: str = Form(...),
    dni: str = Form(...),
    schedule_id: Optional[int] = Form(None),
    telegram_chat_id: Optional[str] = Form(None),
    notify_telegram: bool = Form(True),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    return await StudentService.create_student(
        db=db,
        full_name=full_name,
        grade=grade,
        section=section,
        file=file,
        face_descriptor=face_descriptor,
        dni=dni,
        schedule_id=schedule_id,
        telegram_chat_id=telegram_chat_id,
        notify_telegram=notify_telegram
    )

@router.put("/{student_id}", response_model=schemas.Student)
async def update_student(
    *,
    db: Session = Depends(deps.get_db),
    student_id: int,
    student_in: schemas.StudentUpdate,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    return await StudentService.update_student(db, student_id, student_in)

@router.delete("/{student_id}", response_model=schemas.Student)
def delete_student(
    *,
    db: Session = Depends(deps.get_db),
    student_id: int,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    return StudentService.delete_student(db, student_id)

@router.post("/import")
async def import_students(
    file: UploadFile = File(...),
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
):
    return await StudentService.import_students(db, file)

from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
import uuid
import json
import asyncio
import os

from app import models, schemas
from app.api import deps
# from ..services.face_recognition import decode_image, get_face_embedding 
# We don't need detection here anymore, client does it.

router = APIRouter()

from app.services.student_service import StudentService
from app.services.storage_service import StorageService
from fastapi.responses import StreamingResponse, RedirectResponse

@router.get("/", response_model=schemas.student.StudentPagination)
def read_students(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 50,
    grade: Optional[str] = None,
    section: Optional[str] = None,
    search: Optional[str] = None,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    query = db.query(models.Student)
    if grade:
        query = query.filter(models.Student.grade == grade)
    if section:
        query = query.filter(models.Student.section == section)
    if search:
        search_filter = f"%{search}%"
        query = query.filter(
            (models.Student.full_name.ilike(search_filter)) |
            (models.Student.dni.like(search_filter))
        )
        
    total = query.count()
    students = query.offset(skip).limit(limit).all()
    
    return {
        "total": total,
        "items": StudentService.prepare_students_response(students),
        "skip": skip,
        "limit": limit
    }

@router.post("/register", response_model=schemas.Student)
async def create_student(
    *,
    db: Session = Depends(deps.get_db),
    first_name: str = Form(...),
    last_name: str = Form(...),
    grade: str = Form(...),
    section: str = Form(...),
    file: UploadFile = File(...),
    face_descriptor: str = Form(...),
    dni: str = Form(...),
    schedule_id: Optional[int] = Form(None),
    telegram_chat_id: Optional[str] = Form(None),
    notify_telegram: bool = Form(True),
    current_user: models.User = Depends(deps.get_current_active_admin),
) -> Any:
    return await StudentService.create_student(
        db=db,
        first_name=first_name,
        last_name=last_name,
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
    first_name: Optional[str] = Form(None),
    last_name: Optional[str] = Form(None),
    grade: Optional[str] = Form(None),
    section: Optional[str] = Form(None),
    dni: Optional[str] = Form(None),
    is_active: Optional[bool] = Form(None),
    schedule_id: Optional[int] = Form(None),
    telegram_chat_id: Optional[str] = Form(None),
    notify_telegram: Optional[bool] = Form(None),
    file: Optional[UploadFile] = File(None),
    face_descriptor: Optional[str] = Form(None),
    current_user: models.User = Depends(deps.get_current_active_admin),
) -> Any:
    # Build a temporary StudentUpdate schema to reuse validation
    # Extract only provided fields to avoid sending Nones to service
    update_dict = {
        "first_name": first_name,
        "last_name": last_name,
        "grade": grade,
        "section": section,
        "dni": dni,
        "is_active": is_active,
        "schedule_id": schedule_id,
        "telegram_chat_id": telegram_chat_id,
        "notify_telegram": notify_telegram
    }
    
    # Filter out None values
    filtered_update = {k: v for k, v in update_dict.items() if v is not None}
    student_in = schemas.StudentUpdate(**filtered_update)
    
    student = await StudentService.update_student(
        db, 
        student_id, 
        student_in=student_in, 
        file=file, 
        face_descriptor=face_descriptor
    )
    return StudentService.prepare_student_response(student)

@router.delete("/{student_id}", response_model=schemas.Student)
def delete_student(
    *,
    db: Session = Depends(deps.get_db),
    student_id: int,
    current_user: models.User = Depends(deps.get_current_active_admin),
) -> Any:
    return StudentService.delete_student(db, student_id)

@router.post("/import")
async def import_students(
    file: UploadFile = File(...),
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_admin),
):
    return await StudentService.import_students(db, file)

@router.patch("/enroll-by-dni")
async def enroll_by_dni(
    *,
    db: Session = Depends(deps.get_db),
    dni: str = Form(...),
    file: UploadFile = File(...),
    face_descriptor: str = Form(...),
    current_user: models.User = Depends(deps.get_current_active_admin),
) -> Any:
    return await StudentService.enroll_student_by_dni(
        db=db,
        dni=dni,
        file=file,
        face_descriptor=face_descriptor
    )

@router.post("/check-photos")
async def check_photos(
    *,
    db: Session = Depends(deps.get_db),
    dnis: List[str],
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    return await StudentService.check_s3_photos(dnis)

@router.post("/enroll-by-s3-key", response_model=schemas.Student)
async def enroll_by_s3_key(
    *,
    db: Session = Depends(deps.get_db),
    dni: str = Form(...),
    s3_key: str = Form(...),
    face_descriptor: str = Form(...),
    current_user: models.User = Depends(deps.get_current_active_admin),
) -> Any:
    return await StudentService.enroll_student_by_s3_key(
        db=db,
        dni=dni,
        s3_key=s3_key,
        face_descriptor=face_descriptor
    )
@router.get("/photo-proxy")
async def photo_proxy(
    key: str,
    sig: Optional[str] = None,
    token: Optional[str] = None,
    db: Session = Depends(deps.get_db),
):
    """
    Proxy seguro para servir fotos desde S3.
    """
    is_authenticated = False
    
    # 1. Validar Autenticación (JWT o Firma)
    if token:
        try:
            from app.core import security
            payload = security.decode_access_token(token)
            if payload:
                is_authenticated = True
        except:
            pass
            
    if not is_authenticated and sig:
        if StorageService.validate_proxy_signature(key, sig):
            is_authenticated = True
            
    if not is_authenticated:
        # Intento final: si hay un header Authorization Bearer (aunque en img tag es raro)
        # Pero no lo forzamos para evitar 500 si falla el Depends
        raise HTTPException(status_code=401, detail="No autorizado")

    # 2. Resolver Key de S3
    s3_key = key
    if s3_key.startswith("/static/students/"):
        s3_key = s3_key.replace("/static/students/", "")
    elif s3_key.startswith("static/students/"):
        s3_key = s3_key.replace("static/students/", "")
        
    # Añadir prefijo de S3 si no lo tiene
    base_path = os.getenv("STORAGE_BASE_PATH", "eduasistencia/fotos-estudiantes")
    if not s3_key.startswith(base_path):
        s3_key = f"{base_path}/{s3_key}".replace("//", "/")

    # 4. Generar URL Firmada y Redirigir
    try:
        presigned_url = StorageService.get_presigned_url(s3_key, expires_in=3600)
        if not presigned_url:
            raise HTTPException(status_code=404, detail="Error al generar acceso a la foto")
            
        return RedirectResponse(
            presigned_url, 
            status_code=307,
            headers={"Cache-Control": "public, max-age=3600"}
        )
    except Exception as e:
        print(f"DEBUG PROXY ERROR: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

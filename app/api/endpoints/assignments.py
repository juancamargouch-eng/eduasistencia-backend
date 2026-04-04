from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from datetime import datetime

from app import models, schemas
from app.api import deps
from app.services.storage_service import StorageService

router = APIRouter()

@router.get("/", response_model=List[schemas.assignment.Assignment])
def read_assignments(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: models.User = Depends(deps.get_current_active_docente),
) -> Any:
    """
    Retrieve assignments.
    Teachers see their own assignments. Admins see all.
    """
    if current_user.is_superuser or current_user.role == "ADMIN":
        assignments = db.query(models.Assignment).offset(skip).limit(limit).all()
    else:
        assignments = db.query(models.Assignment).filter(
            models.Assignment.teacher_id == current_user.id
        ).offset(skip).limit(limit).all()
    return assignments

@router.post("/", response_model=schemas.assignment.Assignment)
async def create_assignment(
    *,
    db: Session = Depends(deps.get_db),
    title: str = Form(...),
    description: Optional[str] = Form(None),
    due_date: Optional[str] = Form(None),
    grade: str = Form(...),
    section: str = Form(...),
    file: Optional[UploadFile] = File(None),
    current_user: models.User = Depends(deps.get_current_active_docente),
) -> Any:
    """
    Create new assignment.
    """
    file_url = None
    if file:
        file_url = await StorageService.upload_file(file, folder="assignments")

    # Parse due_date if provided
    parsed_due_date = None
    if due_date:
        try:
            parsed_due_date = datetime.fromisoformat(due_date.replace('Z', '+00:00'))
        except ValueError:
            pass

    assignment = models.Assignment(
        title=title,
        description=description,
        due_date=parsed_due_date,
        grade=grade,
        section=section,
        file_url=file_url,
        teacher_id=current_user.id
    )
    db.add(assignment)
    db.commit()
    db.refresh(assignment)
    return assignment

@router.delete("/{id}", response_model=schemas.assignment.Assignment)
def delete_assignment(
    *,
    db: Session = Depends(deps.get_db),
    id: int,
    current_user: models.User = Depends(deps.get_current_active_docente),
) -> Any:
    """
    Delete an assignment.
    """
    assignment = db.query(models.Assignment).filter(models.Assignment.id == id).first()
    if not assignment:
        raise HTTPException(status_code=404, detail="Tarea no encontrada")
    
    if not current_user.is_superuser and current_user.role != "ADMIN" and assignment.teacher_id != current_user.id:
        raise HTTPException(status_code=403, detail="No tienes permisos para eliminar esta tarea")
    
    if assignment.file_url:
        StorageService.delete_file(assignment.file_url)
        
    db.delete(assignment)
    db.commit()
    return assignment

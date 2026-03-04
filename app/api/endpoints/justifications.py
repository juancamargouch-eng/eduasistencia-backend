from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from ...config.database import get_db
from ...models.justification import Justification
from ...schemas.justification import JustificationCreate, JustificationUpdate, Justification as JustificationSchema

from ...models import student as student_models
from ...api import deps
from ...models.user import User

router = APIRouter()

@router.post("/", response_model=JustificationSchema)
def create_justification(
    justification: JustificationCreate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    from ...models.student import Student
    
    student_id = justification.student_id
    
    if not student_id and justification.dni:
        student = db.query(Student).filter(Student.dni == justification.dni).first()
        if not student:
             raise HTTPException(status_code=404, detail="Student with this DNI not found")
        student_id = student.id
        
    if not student_id:
        raise HTTPException(status_code=400, detail="Either Student ID or DNI must be provided")

    # Create dict but exclude dni as it's not in DB model, and ensure student_id is set
    justification_data = justification.dict(exclude={"dni"})
    justification_data["student_id"] = student_id
    
    db_justification = Justification(**justification_data)
    db.add(db_justification)
    db.commit()
    db.refresh(db_justification)
    return db_justification

@router.get("/", response_model=List[JustificationSchema])
def read_justifications(
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    from sqlalchemy.orm import joinedload
    justifications = db.query(Justification).options(joinedload(Justification.student)).offset(skip).limit(limit).all()
    return justifications

@router.put("/{justification_id}/status", response_model=JustificationSchema)
def update_justification_status(
    justification_id: int, 
    status_update: JustificationUpdate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    db_justification = db.query(Justification).filter(Justification.id == justification_id).first()
    if not db_justification:
        raise HTTPException(status_code=404, detail="Justification not found")
    
    db_justification.status = status_update.status
    db.commit()
    db.refresh(db_justification)
    return db_justification

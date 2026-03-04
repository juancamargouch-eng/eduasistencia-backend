from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from ...config.database import get_db
from ...models.schedule import Schedule
from ...schemas.schedule import ScheduleCreate, ScheduleUpdate, Schedule as ScheduleSchema

from ...api import deps
from ...models.user import User

router = APIRouter()

@router.post("/", response_model=ScheduleSchema)
def create_schedule(
    schedule: ScheduleCreate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    db_schedule = Schedule(**schedule.dict())
    db.add(db_schedule)
    db.commit()
    db.refresh(db_schedule)
    return db_schedule

@router.get("/", response_model=List[ScheduleSchema])
def read_schedules(
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    schedules = db.query(Schedule).offset(skip).limit(limit).all()
    return schedules

@router.put("/{schedule_id}", response_model=ScheduleSchema)
def update_schedule(
    schedule_id: int, 
    schedule: ScheduleUpdate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    db_schedule = db.query(Schedule).filter(Schedule.id == schedule_id).first()
    if not db_schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")
    
    update_data = schedule.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_schedule, key, value)
    
    db.commit()
    db.refresh(db_schedule)
    return db_schedule

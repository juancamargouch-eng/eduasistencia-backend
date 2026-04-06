from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class AssignmentBase(BaseModel):
    title: str
    description: Optional[str] = None
    due_date: Optional[datetime] = None
    grade: str
    section: str

class AssignmentCreate(AssignmentBase):
    pass

class AssignmentUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    due_date: Optional[datetime] = None
    grade: Optional[str] = None
    section: Optional[str] = None

class Assignment(AssignmentBase):
    id: int
    teacher_id: Optional[int] = None
    file_url: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True

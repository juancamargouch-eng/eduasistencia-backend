from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class AttendanceLogBase(BaseModel):
    student_id: int
    verification_status: bool
    confidence_score: float
    failure_reason: Optional[str] = None

class AttendanceLogCreate(AttendanceLogBase):
    pass

from .student import Student

class AttendanceLog(AttendanceLogBase):
    id: int
    timestamp: datetime
    event_type: str
    status: str
    student: Optional[Student] = None

    class Config:
        from_attributes = True

from .student import StudentKiosk

class AttendanceLogKiosk(BaseModel):
    id: int
    timestamp: datetime
    verification_status: bool
    failure_reason: Optional[str] = None
    event_type: str
    status: str
    student: Optional[StudentKiosk] = None

    class Config:
        from_attributes = True

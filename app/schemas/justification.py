from pydantic import BaseModel
from typing import Optional
from datetime import date

class JustificationBase(BaseModel):
    student_id: Optional[int] = None
    dni: Optional[str] = None
    date: date
    reason: str
    evidence_url: Optional[str] = None

class JustificationCreate(JustificationBase):
    pass

class JustificationUpdate(BaseModel):
    status: str # "APPROVED" | "REJECTED"

class Justification(JustificationBase):
    id: int
    status: str
    student: Optional['StudentSummary'] = None

    class Config:
        from_attributes = True

from .student import StudentSummary
Justification.update_forward_refs()

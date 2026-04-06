from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class StudentBase(BaseModel):
    first_name: Optional[str] = ""
    last_name: Optional[str] = ""
    full_name: Optional[str] = ""
    grade: Optional[str] = ""
    section: Optional[str] = ""
    telegram_chat_id: Optional[str] = None
    telegram_user_id: Optional[str] = None
    notify_telegram: Optional[bool] = True

class StudentKiosk(BaseModel):
    first_name: Optional[str] = ""
    last_name: Optional[str] = ""
    full_name: Optional[str] = ""
    grade: Optional[str] = ""
    section: Optional[str] = ""
    photo_url: Optional[str] = None

    class Config:
        from_attributes = True

class StudentSummary(BaseModel):
    id: int
    first_name: Optional[str] = ""
    last_name: Optional[str] = ""
    full_name: Optional[str] = ""
    dni: Optional[str] = None
    grade: Optional[str] = ""
    section: Optional[str] = ""

    class Config:
        from_attributes = True

class StudentCreate(StudentBase):
    pass

class StudentUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    full_name: Optional[str] = None
    grade: Optional[str] = None
    section: Optional[str] = None
    is_active: Optional[bool] = None
    dni: Optional[str] = None
    schedule_id: Optional[int] = None
    telegram_chat_id: Optional[str] = None
    telegram_user_id: Optional[str] = None
    notify_telegram: Optional[bool] = None

class Student(StudentBase):
    id: int
    qr_code_hash: Optional[str] = ""
    is_active: Optional[bool] = True
    created_at: Optional[datetime] = None
    photo_url: Optional[str] = None
    dni: Optional[str] = None
    schedule_id: Optional[int] = None

    class Config:
        from_attributes = True

class StudentPagination(BaseModel):
    total: int
    items: List[Student]
    skip: int
    limit: int

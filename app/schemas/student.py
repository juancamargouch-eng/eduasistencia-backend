from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class StudentBase(BaseModel):
    first_name: str
    last_name: str
    full_name: Optional[str] = None
    grade: str
    section: str
    telegram_chat_id: Optional[str] = None
    telegram_user_id: Optional[str] = None
    notify_telegram: bool = True

class StudentKiosk(BaseModel):
    first_name: str
    last_name: str
    full_name: str
    grade: str
    section: str
    photo_url: Optional[str] = None

    class Config:
        from_attributes = True

class StudentSummary(BaseModel):
    id: int
    first_name: str
    last_name: str
    full_name: str
    dni: Optional[str] = None
    grade: str
    section: str

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
    qr_code_hash: str
    is_active: bool
    created_at: datetime
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

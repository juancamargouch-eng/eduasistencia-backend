from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class AnnouncementBase(BaseModel):
    title: str
    content: str
    target_grade: Optional[str] = "TODOS"
    target_section: Optional[str] = "TODOS"

class AnnouncementCreate(AnnouncementBase):
    pass

class AnnouncementUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    target_grade: Optional[str] = None
    target_section: Optional[str] = None

class Announcement(AnnouncementBase):
    id: int
    author_id: int
    created_at: datetime

    class Config:
        from_attributes = True

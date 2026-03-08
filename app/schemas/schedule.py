from pydantic import BaseModel
from typing import Optional, List
from datetime import time

class ScheduleBase(BaseModel):
    name: str
    slug: str
    start_time: time
    end_time: Optional[time] = None
    tolerance_minutes: int = 0
    late_limit_minutes: int = 0
    is_active: bool = True

class ScheduleCreate(ScheduleBase):
    pass

class ScheduleUpdate(ScheduleBase):
    name: Optional[str] = None
    slug: Optional[str] = None
    start_time: Optional[time] = None
    end_time: Optional[time] = None

class Schedule(ScheduleBase):
    id: int

    class Config:
        from_attributes = True

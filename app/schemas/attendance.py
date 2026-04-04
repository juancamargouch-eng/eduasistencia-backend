from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class AttendanceLogBase(BaseModel):
    student_id: int
    verification_status: bool
    confidence_score: float
    failure_reason: Optional[str] = None
    device_source: Optional[str] = None

class AttendanceLogCreate(AttendanceLogBase):
    pass

from .student import Student, StudentKiosk, StudentSummary

class AttendanceLog(AttendanceLogBase):
    id: int
    timestamp: datetime
    event_type: str
    status: str
    student: Optional[Student] = None

    class Config:
        from_attributes = True


class AttendanceLogKiosk(BaseModel):
    id: int
    timestamp: datetime
    verification_status: bool
    failure_reason: Optional[str] = None
    device_source: Optional[str] = None
    event_type: str

    status: str
    student: Optional[StudentKiosk] = None

    class Config:
        from_attributes = True

class AttendancePagination(BaseModel):
    total: int
    items: list[AttendanceLog]
    skip: int
    limit: int

class DailyAttendanceStudent(BaseModel):
    id: int
    full_name: str
    photo_url: Optional[str] = None
    status: str
    entry_time: Optional[datetime] = None

class DailyAttendanceSummary(BaseModel):
    total: int
    present: int
    late: int
    absent: int

class AttendancePercentage(BaseModel):
    present: float
    late: float
    absent: float
    total_expected: int
    period: str


class DailyAttendancePagination(BaseModel):
    date: str
    is_non_working_day: bool
    holiday_name: Optional[str] = None
    summary: DailyAttendanceSummary
    items: list[DailyAttendanceStudent]
    total: int
    skip: int
    limit: int

class OccupancyStudent(StudentSummary):
    entry_time: Optional[datetime] = None
    photo_url: Optional[str] = None

class OccupancyPagination(BaseModel):
    total_entries: int
    total_exits: int
    current_count: int
    items: list[OccupancyStudent]
    total: int
    skip: int
    limit: int
    
    class Config:
        from_attributes = True

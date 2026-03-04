from sqlalchemy import Column, Integer, String, Time, Boolean
from sqlalchemy.orm import relationship
from ..config.database import Base

class Schedule(Base):
    __tablename__ = "schedules"

    id = Column(Integer, primary_key=True, index=True)
    slug = Column(String, unique=True, index=True) # e.g. "morning_shift"
    name = Column(String) # e.g. "Turno Mañana"
    start_time = Column(Time) # e.g. 08:00:00
    tolerance_minutes = Column(Integer, default=0) # e.g. 15
    late_limit_minutes = Column(Integer, default=0) # e.g. 30 (After this, it's Absent)
    is_active = Column(Boolean, default=True)

    students = relationship("Student", back_populates="schedule")

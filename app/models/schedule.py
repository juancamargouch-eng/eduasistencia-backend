from sqlalchemy import Column, Integer, String, Time, Boolean, CheckConstraint
from sqlalchemy.orm import relationship
from ..config.database import Base

class Schedule(Base):
    __tablename__ = "schedules"

    id = Column(Integer, primary_key=True, index=True)
    slug = Column(String(50), unique=True, index=True) # e.g. "morning_shift"
    name = Column(String(100)) # e.g. "Turno Mañana"
    start_time = Column(Time) # e.g. 08:00:00
    end_time = Column(Time) # e.g. 14:00:00
    tolerance_minutes = Column(Integer, CheckConstraint('tolerance_minutes >= 0'), default=0) 
    late_limit_minutes = Column(Integer, CheckConstraint('late_limit_minutes >= 0'), default=0) 
    is_active = Column(Boolean, default=True)

    students = relationship("Student", back_populates="schedule")

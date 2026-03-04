from sqlalchemy import Column, Integer, String, Boolean, Float, TIMESTAMP, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from ..config.database import Base

class AttendanceLog(Base):
    __tablename__ = "attendance_logs"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"))
    timestamp = Column(TIMESTAMP(timezone=True), server_default=func.now(), index=True)
    verification_status = Column(Boolean, default=False)
    confidence_score = Column(Float)
    failure_reason = Column(String, nullable=True) # e.g. "Low Confidence", "QR Invalid", "Face Mismatch"
    event_type = Column(String, default="ENTRY") # ENTRY, EXIT
    status = Column(String, default="PRESENT") # PRESENT, LATE, ABSENT

    student = relationship("Student")

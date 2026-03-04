from sqlalchemy import Column, Integer, String, Date, ForeignKey, Enum
from sqlalchemy.orm import relationship
from ..config.database import Base
import enum

class JustificationStatus(str, enum.Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"

class Justification(Base):
    __tablename__ = "justifications"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"))
    date = Column(Date, index=True)
    reason = Column(String)
    status = Column(String, default=JustificationStatus.PENDING) # stored as string for simplicity in SQLite/Postgres compatibility
    evidence_url = Column(String, nullable=True)
    
    student = relationship("Student", back_populates="justifications")

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, TIMESTAMP
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from ..config.database import Base

class Assignment(Base):
    __tablename__ = "assignments"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    file_url = Column(String(500), nullable=True)  # S3 Key for the attachment
    due_date = Column(DateTime, nullable=True)
    grade = Column(String(50), nullable=False)
    section = Column(String(10), nullable=False)
    
    teacher_id = Column(Integer, ForeignKey("users.id"))
    teacher = relationship("User", backref="assignments")
    
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), onupdate=func.now())

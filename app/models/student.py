from sqlalchemy import Column, Integer, String, ARRAY, Float, Boolean, TIMESTAMP, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..config.database import Base

class Student(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, index=True)
    grade = Column(String)
    section = Column(String)
    dni = Column(String, unique=True, index=True, nullable=True)
    qr_code_hash = Column(String, unique=True, index=True)
    face_encoding = Column(ARRAY(Float)) # Storing embedding as array of floats
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    is_active = Column(Boolean, default=True)
    schedule_id = Column(Integer, ForeignKey("schedules.id"), nullable=True)
    photo_url = Column(String, nullable=True)
    telegram_chat_id = Column(String, nullable=True)
    telegram_user_id = Column(String, nullable=True)
    notify_telegram = Column(Boolean, default=True)

    schedule = relationship("Schedule", back_populates="students")
    justifications = relationship("Justification", back_populates="student")

from sqlalchemy import Column, Integer, String, Text, ForeignKey, TIMESTAMP
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from ..config.database import Base

class Announcement(Base):
    __tablename__ = "announcements"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    target_grade = Column(String(50), nullable=True)   # "TODOS" or specific grade
    target_section = Column(String(10), nullable=True) # "TODOS" or specific section
    
    author_id = Column(Integer, ForeignKey("users.id"))
    author = relationship("User", backref="announcements")
    
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), onupdate=func.now())

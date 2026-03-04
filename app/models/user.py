from sqlalchemy import Column, Integer, String, Boolean, TIMESTAMP
from sqlalchemy.sql import func
from ..config.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    email = Column(String, unique=True, index=True, nullable=True)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

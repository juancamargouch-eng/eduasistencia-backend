from sqlalchemy import Column, Integer, String, Boolean, TIMESTAMP
from sqlalchemy.sql import func
from ..config.database import Base

class Device(Base):
    __tablename__ = "devices"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, index=True) # e.g. "Main Entrance Kiosk"
    ip_address = Column(String(45), nullable=True)
    last_heartbeat = Column(TIMESTAMP(timezone=True), server_default=func.now())
    is_active = Column(Boolean, default=True)
    location = Column(String(255), nullable=True) # e.g. "Gate A"
    device_type = Column(String(50), default="KIOSK") # KIOSK, TURNSTILE, etc.

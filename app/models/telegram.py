from sqlalchemy import Column, Integer, String, Boolean, TIMESTAMP
from sqlalchemy.sql import func
from ..config.database import Base

class TelegramConfig(Base):
    __tablename__ = "telegram_configs"

    id = Column(Integer, primary_key=True, index=True)
    bot_token = Column(String, nullable=True)
    api_id = Column(String, nullable=True)
    api_hash = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    is_active = Column(Boolean, default=False)
    updated_at = Column(TIMESTAMP(timezone=True), onupdate=func.now(), server_default=func.now())

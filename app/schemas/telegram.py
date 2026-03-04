from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class TelegramConfigBase(BaseModel):
    bot_token: Optional[str] = None
    api_id: Optional[str] = None
    api_hash: Optional[str] = None
    phone: Optional[str] = None
    is_active: bool = False

class TelegramConfigCreate(TelegramConfigBase):
    pass

class TelegramConfig(TelegramConfigBase):
    id: int
    updated_at: datetime

    class Config:
        from_attributes = True

class TelegramCodeRequest(BaseModel):
    phone: str

class TelegramLoginRequest(BaseModel):
    phone: str
    code: str
    phone_code_hash: str
    password: Optional[str] = None

from sqlalchemy import Column, Integer, String, Boolean, TIMESTAMP
from sqlalchemy.sql import func
from ..config.database import Base

class ModulePermission(Base):
    __tablename__ = "module_permissions"

    id = Column(Integer, primary_key=True, index=True)
    role = Column(String(20), index=True) # ADMIN, DIRECTOR, DOCENTE
    module_name = Column(String(50), index=True) # TabName: "dashboard", "reports", etc.
    is_enabled = Column(Boolean, default=True)
    updated_at = Column(TIMESTAMP(timezone=True), onupdate=func.now(), server_default=func.now())

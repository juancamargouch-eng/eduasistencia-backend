from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class ModulePermissionBase(BaseModel):
    role: str
    module_name: str
    is_enabled: bool

class ModulePermissionCreate(ModulePermissionBase):
    pass

class ModulePermission(ModulePermissionBase):
    id: int
    updated_at: datetime

    class Config:
        from_attributes = True

class RolePermissionUpdate(BaseModel):
    role: str
    permissions: List[ModulePermissionBase] # Update all permissions for a certain role

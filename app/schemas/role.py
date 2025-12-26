from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime

# Shared properties
class RoleBase(BaseModel):
    name: str
    code: str
    description: Optional[str] = None
    menu_keys: List[str] = []
    data_scope: int = 2
    is_system: bool = False

# Properties to receive on creation
class RoleCreate(RoleBase):
    pass

# Properties to receive on update
class RoleUpdate(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None
    description: Optional[str] = None
    menu_keys: Optional[List[str]] = None
    data_scope: Optional[int] = None
    is_system: Optional[bool] = None

# Properties to return to client
class RoleRead(RoleBase):
    id: str
    created_at: datetime

    class Config:
        from_attributes = True

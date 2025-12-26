from typing import Optional
from pydantic import BaseModel
import uuid
from datetime import datetime
from .role import RoleRead

# Shared properties
class UserBase(BaseModel):
    username: str
    nickname: str
    avatar: Optional[str] = None
    role_id: Optional[str] = None
    is_active: bool = True

# Properties to receive on creation
class UserCreate(UserBase):
    password: str

# Properties to receive on update
class UserUpdate(BaseModel):
    nickname: Optional[str] = None
    avatar: Optional[str] = None
    role_id: Optional[str] = None
    is_active: Optional[bool] = None
    password: Optional[str] = None

# Properties to return to client
class UserRead(UserBase):
    id: uuid.UUID
    created_at: datetime
    role: Optional[RoleRead] = None

    class Config:
        from_attributes = True

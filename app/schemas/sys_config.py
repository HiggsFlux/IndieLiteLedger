from typing import Optional
from pydantic import BaseModel
from datetime import datetime
import uuid

# Shared properties
class SysConfigBase(BaseModel):
    config_key: str
    config_value: Optional[str] = None
    group_code: str
    is_public: bool = False
    description: Optional[str] = None

# Properties to receive on creation
class SysConfigCreate(SysConfigBase):
    pass

# Properties to receive on update
class SysConfigUpdate(BaseModel):
    config_value: Optional[str] = None
    is_public: Optional[bool] = None
    description: Optional[str] = None
    group_code: Optional[str] = None

# Properties to return to client
class SysConfigRead(SysConfigBase):
    id: str
    updated_at: datetime

    class Config:
        from_attributes = True

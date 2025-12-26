from typing import List, Optional, Any
from pydantic import BaseModel
from datetime import datetime

# Shared properties
class ClientBase(BaseModel):
    type: int
    status: int
    source: Optional[str] = None
    level: Optional[int] = 1
    tags: Optional[List[str] | Any] = None 
    extra_info: Optional[dict | Any] = None
    name: str
    contact_person: Optional[str] = None
    position: Optional[str] = None
    wechat: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    tax_info: Optional[dict | Any] = None
    remark: Optional[str] = None

# Properties to receive on item creation
class ClientCreate(ClientBase):
    pass

# Properties to receive on item update
class ClientUpdate(BaseModel):
    type: Optional[int] = None
    status: Optional[int] = None
    source: Optional[str] = None
    level: Optional[int] = None
    tags: Optional[List[str] | Any] = None 
    extra_info: Optional[dict | Any] = None
    name: Optional[str] = None
    contact_person: Optional[str] = None
    position: Optional[str] = None
    wechat: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    tax_info: Optional[dict | Any] = None
    remark: Optional[str] = None

# Properties shared by models stored in DB
class ClientInDBBase(ClientBase):
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# Properties to return to client
class ClientResponse(ClientInDBBase):
    pass

class ClientDetailResponse(ClientResponse):
    # Flattened Extra Fields
    website: Optional[str] = None
    tech_tags: List[str] = []
    telegram: Optional[str] = None
    contact_role: Optional[str] = None
    tax_code: Optional[str] = None
    bank_name: Optional[str] = None
    bank_account: Optional[str] = None
    reg_address: Optional[str] = None
    
    # Statistics
    license_count: int = 0
    last_active: Optional[datetime] = None

# --- FollowUp ---

class FollowUpBase(BaseModel):
    method: str
    content: str
    next_time: Optional[datetime] = None
    recorder_id: Optional[str] = None

class FollowUpCreate(FollowUpBase):
    client_id: str

class FollowUpResponse(FollowUpBase):
    id: str
    client_id: str
    created_at: datetime

    class Config:
        from_attributes = True

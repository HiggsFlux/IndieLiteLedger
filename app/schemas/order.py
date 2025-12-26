from typing import Optional
from pydantic import BaseModel
from datetime import datetime
from decimal import Decimal

# Shared properties
class OrderBase(BaseModel):
    client_id: str
    product_info: str
    amount: Decimal = 0.00
    actual_amount: Decimal = 0.00 # Deprecated, use total_paid
    status: str = "PENDING"
    order_type: str = "NEW"
    pay_method: str = "BANK" # Deprecated
    pay_time: Optional[datetime] = None # Deprecated
    contract_no: Optional[str] = None
    is_invoiced: bool = False
    invoice_time: Optional[datetime] = None
    remark: Optional[str] = None
    attachments: Optional[str] = "[]"
    total_paid: Decimal = 0.00

# Properties to receive on item creation
class OrderCreate(BaseModel):
    client_id: str
    order_type: str
    product_info: str
    amount: Decimal
    contract_no: Optional[str] = None
    remark: Optional[str] = None
    attachments: Optional[str] = "[]"

# Properties to receive on item update
class OrderUpdate(BaseModel):
    product_info: Optional[str] = None
    amount: Optional[Decimal] = None
    actual_amount: Optional[Decimal] = None
    status: Optional[str] = None
    order_type: Optional[str] = None
    pay_method: Optional[str] = None
    pay_time: Optional[datetime] = None
    external_transaction_no: Optional[str] = None
    contract_no: Optional[str] = None
    is_invoiced: Optional[bool] = None
    invoice_time: Optional[datetime] = None
    remark: Optional[str] = None
    attachments: Optional[str] = None

# Properties shared by models stored in DB
class OrderInDBBase(OrderBase):
    id: str
    order_no: str
    client_name: str
    creator_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# Properties to return to client
class OrderResponse(OrderInDBBase):
    client_type: Optional[int] = None

class OrderStats(BaseModel):
    monthly_revenue: Decimal
    pending_amount: Decimal
    monthly_count: int

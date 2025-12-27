from typing import Optional
from pydantic import BaseModel
from datetime import datetime
from decimal import Decimal

# Shared properties
class PaymentRecordBase(BaseModel):
    amount: Decimal
    type: int = 1 # 1: Collection, 2: Refund
    pay_method: str
    transaction_id: Optional[str] = None
    remark: Optional[str] = None

# Properties to receive on creation
class PaymentRecordCreate(PaymentRecordBase):
    order_id: str

# Properties shared by models stored in DB
class PaymentRecordInDBBase(PaymentRecordBase):
    id: str
    order_id: str
    pay_time: datetime
    creator_id: int

    class Config:
        from_attributes = True

# Properties to return to client
class PaymentRecordResponse(PaymentRecordInDBBase):
    pass

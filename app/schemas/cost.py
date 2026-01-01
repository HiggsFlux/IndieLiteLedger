from pydantic import BaseModel
from decimal import Decimal
from datetime import date, datetime
from typing import Optional, Dict, List
import uuid

class CostBase(BaseModel):
    title: str
    amount: Decimal
    category: str
    pay_time: date
    pay_account: str = "ALIPAY"
    remark: Optional[str] = None
    invoice_url: Optional[str] = None

class CostCreate(CostBase):
    pass

class CostUpdate(BaseModel):
    title: Optional[str] = None
    amount: Optional[Decimal] = None
    category: Optional[str] = None
    pay_time: Optional[date] = None
    pay_account: Optional[str] = None
    remark: Optional[str] = None
    invoice_url: Optional[str] = None

class CostRead(CostBase):
    id: uuid.UUID
    created_at: datetime
    creator_id: Optional[str] = None

    class Config:
        from_attributes = True

class CategoryStat(BaseModel):
    name: str
    amount: float
    percent: float

class CostStats(BaseModel):
    month_cost: float
    month_cost_last: float
    month_growth: float
    year_cost: float
    year_cost_last: float
    year_growth: float
    category_breakdown: List[CategoryStat]

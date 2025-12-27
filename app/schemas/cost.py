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

class CostRead(CostBase):
    id: uuid.UUID
    created_at: datetime
    creator_id: Optional[str] = None

    class Config:
        from_attributes = True

class MonthlyStat(BaseModel):
    month: str
    revenue: float
    cost: float
    profit: float

class CostStats(BaseModel):
    total_revenue: float
    total_cost: float
    net_profit: float
    profit_margin: str
    cost_breakdown: Dict[str, float]
    trend: List[MonthlyStat]

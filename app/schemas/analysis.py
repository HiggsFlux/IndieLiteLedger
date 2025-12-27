from typing import List, Optional
from pydantic import BaseModel

class AnalysisTrendRequest(BaseModel):
    time_dimension: str # 'year' or 'month'
    year: str
    month_range: Optional[List[str]] = None # ['2025-01', '2025-12']
    order_type: str = 'all'

class TrendDataPoint(BaseModel):
    date: str
    sales_amount: float
    collection_amount: float
    trial_count: int

class AnalysisTrendResponse(BaseModel):
    xAxis: List[str]
    series: List[TrendDataPoint]

class ComparisonDataPoint(BaseModel):
    date: str
    enterprise_sales: float
    personal_sales: float
    enterprise_trial: int
    personal_trial: int

class AnalysisComparisonResponse(BaseModel):
    xAxis: List[str]
    series: List[ComparisonDataPoint]

class AnalysisSummaryResponse(BaseModel):
    trial_count: int
    trial_growth: float # Growth rate or just diff? Usually growth rate or value. Let's provide growth value or rate. User asked for "Same Period Amount" for Sales. Let's provide previous values for flexibility.
    
    order_count: int
    order_growth: float
    
    sales_amount: float
    sales_compare_amount: float # "Same Period Amount"
    
    collection_amount: float
    collection_growth: float
    
    pending_amount: float
    pending_growth: float # Maybe not needed but for consistency

class DistributionItem(BaseModel):
    name: str
    value: float

class ActivityItem(BaseModel):
    id: str
    content: str
    timestamp: str # ISO format
    color: str = "#3b82f6"
    avatar: Optional[str] = None
    client_name: str
    client_type: int
    method: str

class AnalysisActivitiesResponse(BaseModel):
    activities: List[ActivityItem]

class AnalysisDistributionResponse(BaseModel):
    order_type: List[DistributionItem]
    order_status: List[DistributionItem]

class AnalysisNewCustomersResponse(BaseModel):
    xAxis: List[str]
    series: List[int]

class WorkbenchSummary(BaseModel):
    total_income: float
    income_growth: float
    total_expense: float
    expense_growth: float
    new_customers: int
    new_customers_growth: float
    deal_customers: int
    deal_customers_conversion_rate: float
    total_profit: float
    profit_margin: float

class WorkbenchResponse(BaseModel):
    summary: WorkbenchSummary
    trend_xAxis: List[str]
    trend_income: List[float]
    trend_expense: List[float]
    trend_profit: List[float]
    trend_margin: List[float]
    expense_pie: List[DistributionItem]

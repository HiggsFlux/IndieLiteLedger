from typing import Any, List, Optional, Dict
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select, func, extract
from sqlalchemy import text
from app.api import deps
from app.models.cost import Cost
from app.models.order import Order
from app.models.user import User
from app.schemas.cost import CostCreate, CostRead, CostStats, MonthlyStat
from app.schemas.response import ResponseModel, success
import uuid
from datetime import date, datetime

router = APIRouter()

@router.get("/list", response_model=ResponseModel[List[CostRead]])
def read_costs(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    skip: int = 0,
    limit: int = 100,
    category: Optional[str] = None,
    pay_time_start: Optional[date] = None,
    pay_time_end: Optional[date] = None,
) -> Any:
    """
    Retrieve costs.
    """
    query = select(Cost)
    
    # RBAC: Staff can only see their own costs
    if current_user.role == "STAFF":
        query = query.where(Cost.creator_id == current_user.id)
        
    if category:
        query = query.where(Cost.category == category)
    if pay_time_start:
        query = query.where(Cost.pay_time >= pay_time_start)
    if pay_time_end:
        query = query.where(Cost.pay_time <= pay_time_end)
    
    query = query.order_by(Cost.pay_time.desc()).offset(skip).limit(limit)
    costs = db.execute(query).scalars().all()
    return success(costs)

@router.post("/", response_model=ResponseModel[CostRead])
def create_cost(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    cost_in: CostCreate,
) -> Any:
    """
    Create new cost.
    """
    cost_data = cost_in.dict()
    cost_data["creator_id"] = current_user.id
    cost = Cost(**cost_data)
    db.add(cost)
    db.commit()
    db.refresh(cost)
    return success(cost)

@router.delete("/{id}", response_model=ResponseModel[CostRead])
def delete_cost(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    id: str,
) -> Any:
    """
    Delete cost.
    """
    cost = db.get(Cost, id)
    if not cost:
        raise HTTPException(status_code=404, detail="Cost not found")
        
    # RBAC: Staff can only delete their own costs
    if current_user.role == "STAFF" and cost.creator_id != current_user.id:
         raise HTTPException(status_code=403, detail="Not authorized to delete this cost")
         
    db.delete(cost)
    db.commit()
    return success(cost)

@router.get("/stats", response_model=ResponseModel[CostStats])
def get_cost_stats(
    db: Session = Depends(deps.get_db),
    year: Optional[str] = None
) -> Any:
    """
    Get aggregated finance stats (Revenue, Cost, Profit).
    If year is not provided, defaults to current year.
    """
    if not year:
        year = str(datetime.now().year)
        
    start_date = f"{year}-01-01"
    end_date = f"{year}-12-31 23:59:59"

    # Revenue: Sum of Order.amount for the year
    revenue_query = select(func.sum(Order.amount)).where(
        Order.created_at >= start_date,
        Order.created_at <= end_date,
        Order.status == 'PAID' # Only count PAID orders
    )
    total_revenue = db.scalar(revenue_query) or 0.0
    
    # Cost: Sum of Cost.amount for the year
    cost_query = select(func.sum(Cost.amount)).where(
        Cost.pay_time >= start_date,
        Cost.pay_time <= end_date
    )
    total_cost = db.scalar(cost_query) or 0.0
    
    net_profit = float(total_revenue) - float(total_cost)
    
    if total_revenue > 0:
        profit_margin = f"{(net_profit / float(total_revenue)) * 100:.1f}%"
    else:
        profit_margin = "0%"
        
    # Cost Breakdown by Category (Yearly)
    breakdown_query = select(Cost.category, func.sum(Cost.amount)).where(
        Cost.pay_time >= start_date,
        Cost.pay_time <= end_date
    ).group_by(Cost.category)
    breakdown_results = db.execute(breakdown_query).all()
    
    cost_breakdown = {category: float(amount) for category, amount in breakdown_results}
    
    # Trend Logic (Monthly for the selected year)
    # Revenue Trend
    rev_trend_query = select(
        func.strftime('%Y-%m', Order.created_at).label('month'),
        func.sum(Order.amount).label('revenue')
    ).where(
        Order.created_at >= start_date,
        Order.created_at <= end_date,
        Order.status == 'PAID'
    ).group_by(text('month')).order_by(text('month'))
    rev_trend = db.execute(rev_trend_query).all()
    
    # Cost Trend
    cost_trend_query = select(
        func.strftime('%Y-%m', Cost.pay_time).label('month'),
        func.sum(Cost.amount).label('cost')
    ).where(
        Cost.pay_time >= start_date,
        Cost.pay_time <= end_date
    ).group_by(text('month')).order_by(text('month'))
    cost_trend = db.execute(cost_trend_query).all()
    
    # Merge Data
    trend_map: Dict[str, MonthlyStat] = {}
    
    for r in rev_trend:
        month = r.month
        if month not in trend_map:
            trend_map[month] = MonthlyStat(month=month, revenue=0, cost=0, profit=0)
        trend_map[month].revenue = float(r.revenue or 0)
        
    for c in cost_trend:
        month = c.month
        if month not in trend_map:
            trend_map[month] = MonthlyStat(month=month, revenue=0, cost=0, profit=0)
        trend_map[month].cost = float(c.cost or 0)
        
    # Calculate Profit
    trend_list = []
    for month in sorted(trend_map.keys()):
        stat = trend_map[month]
        stat.profit = stat.revenue - stat.cost
        trend_list.append(stat)
    
    return success(CostStats(
        total_revenue=float(total_revenue),
        total_cost=float(total_cost),
        net_profit=net_profit,
        profit_margin=profit_margin,
        cost_breakdown=cost_breakdown,
        trend=trend_list
    ))

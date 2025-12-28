from typing import Any, List, Optional, Dict
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select, func, extract
from sqlalchemy import text
from app.api import deps
from app.models.cost import Cost
from app.models.order import Order
from app.models.user import User
from app.schemas.cost import CostCreate, CostRead, CostStats, CategoryStat
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
    current_user: User = Depends(deps.get_current_user),
    year: Optional[str] = None
) -> Any:
    """
    Get aggregated cost stats (Monthly, Yearly, Breakdown).
    """
    now = datetime.now()
    current_year = int(year) if year else now.year
    current_month = now.month
    
    def apply_filters(query):
        # RBAC: Staff can only see their own costs
        if current_user.role == "STAFF":
            return query.where(Cost.creator_id == current_user.id)
        return query

    # --- 1. Monthly Stats ---
    # Current Month
    month_cost_query = select(func.sum(Cost.amount)).where(
        extract('year', Cost.pay_time) == current_year,
        extract('month', Cost.pay_time) == current_month
    )
    month_cost_query = apply_filters(month_cost_query)
    month_cost = db.scalar(month_cost_query) or 0.0
    
    # Last Month
    last_month_year = current_year
    last_month = current_month - 1
    if last_month == 0:
        last_month = 12
        last_month_year -= 1
        
    month_cost_last_query = select(func.sum(Cost.amount)).where(
        extract('year', Cost.pay_time) == last_month_year,
        extract('month', Cost.pay_time) == last_month
    )
    month_cost_last_query = apply_filters(month_cost_last_query)
    month_cost_last = db.scalar(month_cost_last_query) or 0.0
    
    month_growth = 0.0
    if month_cost_last > 0:
        month_growth = ((month_cost - month_cost_last) / month_cost_last) * 100
    elif month_cost > 0:
        month_growth = 100.0
    
    # --- 2. Yearly Stats ---
    # Current Year
    year_cost_query = select(func.sum(Cost.amount)).where(
        extract('year', Cost.pay_time) == current_year
    )
    year_cost_query = apply_filters(year_cost_query)
    year_cost = db.scalar(year_cost_query) or 0.0
    
    # Last Year
    last_year = current_year - 1
    year_cost_last_query = select(func.sum(Cost.amount)).where(
        extract('year', Cost.pay_time) == last_year
    )
    year_cost_last_query = apply_filters(year_cost_last_query)
    year_cost_last = db.scalar(year_cost_last_query) or 0.0
    
    year_growth = 0.0
    if year_cost_last > 0:
        year_growth = ((year_cost - year_cost_last) / year_cost_last) * 100
    elif year_cost > 0:
        year_growth = 100.0
        
    # --- 3. Category Breakdown (Yearly) ---
    breakdown_query = select(Cost.category, func.sum(Cost.amount)).where(
        extract('year', Cost.pay_time) == current_year
    )
    breakdown_query = apply_filters(breakdown_query)
    breakdown_query = breakdown_query.group_by(Cost.category).order_by(func.sum(Cost.amount).desc())
    
    breakdown_results = db.execute(breakdown_query).all()
    
    category_breakdown = []
    total_breakdown_amount = sum([float(amount) for _, amount in breakdown_results])
    
    for category, amount in breakdown_results:
        amount_float = float(amount)
        percent = (amount_float / total_breakdown_amount * 100) if total_breakdown_amount > 0 else 0.0
        category_breakdown.append(CategoryStat(
            name=category,
            amount=amount_float,
            percent=round(percent, 1)
        ))
        
    return success(CostStats(
        month_cost=float(month_cost),
        month_cost_last=float(month_cost_last),
        month_growth=round(month_growth, 1),
        year_cost=float(year_cost),
        year_cost_last=float(year_cost_last),
        year_growth=round(year_growth, 1),
        category_breakdown=category_breakdown
    ))

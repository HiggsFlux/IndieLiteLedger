from typing import Any, List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, extract, and_, or_
from datetime import datetime, timedelta
import calendar

from app.api import deps
from app.schemas import analysis as schemas
from app.schemas.response import ResponseModel, success
from app.models.order import Order
from app.models.payment import PaymentRecord
from app.models.client import Client, FollowUp
# Try import Plugin Model
try:
    from app.modules.plugins.commercial_kit.models import LicenseRecord
except ImportError:
    LicenseRecord = None
from app.models.cost import Cost

router = APIRouter()

def get_date_range_and_grouping(time_dimension: str, year: str, month_range: List[str]):
    """
    Determine the date range and grouping strategy (day or month).
    Returns: (start_date, end_date, group_by_mode, labels)
    group_by_mode: 'day' or 'month'
    labels: list of strings (e.g. ['2025-01-01', ...] or ['2025-01', ...])
    """
    labels = []
    
    if time_dimension == 'year':
        start_date = datetime.strptime(f"{year}-01-01", "%Y-%m-%d")
        end_date = datetime.strptime(f"{year}-12-31 23:59:59", "%Y-%m-%d %H:%M:%S")
        group_by_mode = 'month'
        for i in range(1, 13):
            labels.append(f"{year}-{i:02d}")
            
    else: # month
        if not month_range or len(month_range) != 2:
            # Default to current month if missing
            now = datetime.now()
            month_range = [now.strftime("%Y-%m"), now.strftime("%Y-%m")]

        start_str, end_str = month_range
        
        if start_str == end_str:
            # Same month -> Show days
            y, m = map(int, start_str.split('-'))
            _, last_day = calendar.monthrange(y, m)
            start_date = datetime(y, m, 1)
            end_date = datetime(y, m, last_day, 23, 59, 59)
            group_by_mode = 'day'
            
            for d in range(1, last_day + 1):
                labels.append(f"{y}-{m:02d}-{d:02d}")
        else:
            # Different months -> Show months
            start_y, start_m = map(int, start_str.split('-'))
            end_y, end_m = map(int, end_str.split('-'))
            
            start_date = datetime(start_y, start_m, 1)
            _, last_day_end = calendar.monthrange(end_y, end_m)
            end_date = datetime(end_y, end_m, last_day_end, 23, 59, 59)
            group_by_mode = 'month'
            
            # Generate month labels
            curr = start_date
            while curr <= end_date:
                labels.append(curr.strftime("%Y-%m"))
                # Move to next month
                if curr.month == 12:
                    curr = datetime(curr.year + 1, 1, 1)
                else:
                    curr = datetime(curr.year, curr.month + 1, 1)

    return start_date, end_date, group_by_mode, labels

def get_prev_date_range(start_date: datetime, end_date: datetime, time_dimension: str):
    """
    Get previous period date range.
    If year: Same period last year.
    If month: Previous month.
    """
    try:
        if time_dimension == 'year':
            prev_start = start_date.replace(year=start_date.year - 1)
            try:
                prev_end = end_date.replace(year=end_date.year - 1)
            except ValueError:
                # Handle leap year (Feb 29 -> Feb 28)
                prev_end = end_date.replace(year=end_date.year - 1, day=28)
            return prev_start, prev_end
        else:
            # Shift back by 1 month
            # Calculate previous start date
            year = start_date.year
            month = start_date.month - 1
            if month == 0:
                month = 12
                year -= 1
            prev_start = start_date.replace(year=year, month=month)
            
            # Calculate previous end date
            # Logic: If end_date is the last day of the month, prev_end should be the last day of the previous month.
            # If end_date is not the last day (e.g. current partial month), try to keep the same day.
            
            end_year = end_date.year
            end_month = end_date.month - 1
            if end_month == 0:
                end_month = 12
                end_year -= 1
                
            # Check if original end_date was the last day of its month
            _, original_last_day = calendar.monthrange(end_date.year, end_date.month)
            is_last_day = (end_date.day == original_last_day)
            
            _, prev_last_day = calendar.monthrange(end_year, end_month)
            
            if is_last_day:
                day = prev_last_day
            else:
                day = min(end_date.day, prev_last_day)
                
            prev_end = end_date.replace(year=end_year, month=end_month, day=day)
            
            return prev_start, prev_end

    except Exception:
        # Fallback
        return start_date, end_date

def get_order_filters(order_type: str):
    filters = []
    if order_type and order_type != 'all':
        if order_type == 'new':
            filters.append(Order.order_type == 'NEW')
        elif order_type == 'renew':
            filters.append(Order.order_type == 'RENEW')
        elif order_type == 'upsell':
            filters.append(Order.order_type == 'UPSELL')
        elif order_type == 'service':
            filters.append(Order.order_type == 'SERVICE')
        elif order_type == 'implementation':
            filters.append(Order.order_type == 'IMPLEMENTATION')
        elif order_type == 'renewal': # Backward compatibility
            filters.append(Order.order_type.in_(['RENEW', 'UPSELL']))
    return filters

@router.post("/summary", response_model=ResponseModel[schemas.AnalysisSummaryResponse])
def get_summary(
    request: schemas.AnalysisTrendRequest,
    db: Session = Depends(deps.get_db)
) -> Any:
    """
    Get Summary Cards Data.
    Trial Count: From LicenseRecord
    Order Count: From Order (created_at)
    Sales Amount: From Order (amount)
    Collection Amount: From PaymentRecord (amount, type=1)
    Pending Amount: Cumulative (Total Order Amount <= EndDate - Total Collection Amount <= EndDate)
    """
    start_date, end_date, _, _ = get_date_range_and_grouping(
        request.time_dimension, request.year, request.month_range
    )
    prev_start_date, prev_end_date = get_prev_date_range(start_date, end_date, request.time_dimension)
    
    # --- Helper Queries ---
    def get_count(model, start, end):
        q = db.query(func.count(model.id)).filter(
            model.created_at >= start,
            model.created_at <= end
        )
        return q.scalar() or 0

    def get_sum(model, field, start, end, filters=[]):
        q = db.query(func.sum(field)).filter(
            model.created_at >= start,
            model.created_at <= end,
            *filters
        )
        return q.scalar() or 0.0
    
    def get_payment_sum(start, end):
        q = db.query(func.sum(PaymentRecord.amount)).filter(
            PaymentRecord.pay_time >= start,
            PaymentRecord.pay_time <= end,
            PaymentRecord.type == 1
        )
        return q.scalar() or 0.0

    # 1. Trial Count (LicenseRecord)
    if LicenseRecord:
        trial_count = get_count(LicenseRecord, start_date, end_date)
        prev_trial_count = get_count(LicenseRecord, prev_start_date, prev_end_date)
    else:
        trial_count = 0
        prev_trial_count = 0
    trial_growth = trial_count - prev_trial_count # Value difference
    
    # 2. Order Count
    # Filter by order_type if needed? Usually summary includes all unless specified.
    # Request has order_type. Let's respect it.
    order_filters = get_order_filters(request.order_type)
            
    order_count = get_count(Order, start_date, end_date) # Note: get_count helper doesn't take filters
    # Refined get_count with filters
    order_q = db.query(func.count(Order.id)).filter(
        Order.created_at >= start_date,
        Order.created_at <= end_date,
        *order_filters
    )
    order_count = order_q.scalar() or 0
    
    prev_order_q = db.query(func.count(Order.id)).filter(
        Order.created_at >= prev_start_date,
        Order.created_at <= prev_end_date,
        *order_filters
    )
    prev_order_count = prev_order_q.scalar() or 0
    order_growth = order_count - prev_order_count
    
    # 3. Sales Amount
    sales_amount = get_sum(Order, Order.amount, start_date, end_date, order_filters)
    sales_compare_amount = get_sum(Order, Order.amount, prev_start_date, prev_end_date, order_filters)
    
    # 4. Collection Amount (PaymentRecord)
    # Payment doesn't have order_type directly. Need join if filtering.
    coll_q = db.query(func.sum(PaymentRecord.amount)).join(Order).filter(
        PaymentRecord.pay_time >= start_date,
        PaymentRecord.pay_time <= end_date,
        PaymentRecord.type == 1,
        *order_filters
    )
    collection_amount = coll_q.scalar() or 0.0
    
    prev_coll_q = db.query(func.sum(PaymentRecord.amount)).join(Order).filter(
        PaymentRecord.pay_time >= prev_start_date,
        PaymentRecord.pay_time <= prev_end_date,
        PaymentRecord.type == 1,
        *order_filters
    )
    prev_collection_amount = prev_coll_q.scalar() or 0.0
    collection_growth = float(collection_amount) - float(prev_collection_amount)

    # 5. Pending Amount (Cumulative Logic)
    # Total Order Amount (created <= end_date) - Total Collection Amount (pay_time <= end_date)
    # Filtered by order_type if requested
    
    # Total Sales up to End Date
    cum_sales_q = db.query(func.sum(Order.amount)).filter(
        Order.created_at <= end_date,
        *order_filters
    )
    cum_sales = cum_sales_q.scalar() or 0.0
    
    # Total Collection up to End Date (for those orders? Or just total collection?)
    # "All these orders' collection amounts"
    # If filtered by order type, we need to join Order.
    # If we filter Orders by creation date <= EndDate, we should sum payments FOR THOSE ORDERS.
    # But usually, just "Total Payments <= EndDate" is easier and functionally close if we assume payments come after orders.
    # However, strict interpretation: Payments linked to orders created <= EndDate.
    # Let's stick to simple: Total Payments <= EndDate.
    
    cum_coll_q = db.query(func.sum(PaymentRecord.amount)).join(Order).filter(
        PaymentRecord.pay_time <= end_date,
        PaymentRecord.type == 1,
        *order_filters
    )
    cum_coll = cum_coll_q.scalar() or 0.0
    
    pending_amount = float(cum_sales) - float(cum_coll)
    pending_growth = 0.0 # Not really applicable or complex to calc previous pending
    
    return success(schemas.AnalysisSummaryResponse(
        trial_count=trial_count,
        trial_growth=trial_growth,
        order_count=order_count,
        order_growth=order_growth,
        sales_amount=float(sales_amount),
        sales_compare_amount=float(sales_compare_amount),
        collection_amount=float(collection_amount),
        collection_growth=collection_growth,
        pending_amount=pending_amount,
        pending_growth=pending_growth
    ))

@router.post("/trend", response_model=ResponseModel[schemas.AnalysisTrendResponse])
def get_trend(
    request: schemas.AnalysisTrendRequest,
    db: Session = Depends(deps.get_db)
) -> Any:
    """
    Get Sales & Collection Trend data.
    Sales: Order Amount (created_at, status != VOID/CANCELLED)
    Collection: Payment Amount (pay_time, type=1)
    Trial: LicenseRecord Count (created_at)
    """
    start_date, end_date, group_by_mode, labels = get_date_range_and_grouping(
        request.time_dimension, request.year, request.month_range
    )
    
    # Initialize data dictionary
    data_map = {label: {"sales": 0.0, "collection": 0.0, "trial": 0} for label in labels}
    
    # 1. Sales (Orders)
    order_filters = get_order_filters(request.order_type)
    orders_query = db.query(Order).filter(
        Order.created_at >= start_date,
        Order.created_at <= end_date,
        Order.status.notin_(['VOID', 'CANCELLED']),
        *order_filters
    )

    orders = orders_query.all()
    
    for order in orders:
        if not order.created_at: continue
        key = order.created_at.strftime("%Y-%m" if group_by_mode == 'month' else "%Y-%m-%d")
        if key in data_map:
            data_map[key]["sales"] += float(order.amount or 0)

    # 2. Collection (PaymentRecords)
    payments_query = db.query(PaymentRecord).join(Order).filter(
        PaymentRecord.pay_time >= start_date,
        PaymentRecord.pay_time <= end_date,
        PaymentRecord.type == 1, # Collection
        *order_filters
    )
            
    payments = payments_query.all()
    
    for payment in payments:
        if not payment.pay_time: continue
        key = payment.pay_time.strftime("%Y-%m" if group_by_mode == 'month' else "%Y-%m-%d")
        if key in data_map:
            data_map[key]["collection"] += float(payment.amount or 0)
            
    # 3. Trial (LicenseRecord)
    # Trials are count of LicenseRecords
    if LicenseRecord:
        trials_query = db.query(LicenseRecord).filter(
            LicenseRecord.created_at >= start_date,
            LicenseRecord.created_at <= end_date
        )
        # LicenseRecord has no order_type link, so we ignore order_type filter for trials
        trials = trials_query.all()
    else:
        trials = []
    
    for trial in trials:
        if not trial.created_at: continue
        key = trial.created_at.strftime("%Y-%m" if group_by_mode == 'month' else "%Y-%m-%d")
        if key in data_map:
            data_map[key]["trial"] += 1
            
    # Format response
    series = []
    for label in labels:
        item = data_map[label]
        series.append(schemas.TrendDataPoint(
            date=label,
            sales_amount=round(item["sales"], 2),
            collection_amount=round(item["collection"], 2),
            trial_count=item["trial"]
        ))
        
    return success(schemas.AnalysisTrendResponse(
        xAxis=labels,
        series=series
    ))

@router.post("/comparison", response_model=ResponseModel[schemas.AnalysisComparisonResponse])
def get_comparison(
    request: schemas.AnalysisTrendRequest,
    db: Session = Depends(deps.get_db)
) -> Any:
    """
    Get Customer Comparison (Enterprise vs Personal).
    """
    start_date, end_date, group_by_mode, labels = get_date_range_and_grouping(
        request.time_dimension, request.year, request.month_range
    )
    
    data_map = {label: {
        "ent_sales": 0.0, "per_sales": 0.0, 
        "ent_trial": 0, "per_trial": 0
    } for label in labels}
    
    # 1. Sales (Orders joined with Client)
    order_filters = get_order_filters(request.order_type)
    orders = db.query(Order).join(Client).filter(
        Order.created_at >= start_date,
        Order.created_at <= end_date,
        Order.status.notin_(['VOID', 'CANCELLED']),
        *order_filters
    ).all()
    
    for order in orders:
        if not order.created_at: continue
        key = order.created_at.strftime("%Y-%m" if group_by_mode == 'month' else "%Y-%m-%d")
        if key in data_map:
            if order.client.type == 1: # Enterprise
                data_map[key]["ent_sales"] += float(order.amount or 0)
            else: # Personal (0)
                data_map[key]["per_sales"] += float(order.amount or 0)
                
    # 2. Trials (LicenseRecords joined with Client)
    # Join LicenseRecord with Client on name to get client type
    if LicenseRecord:
        trials = db.query(LicenseRecord, Client.type).join(
            Client, LicenseRecord.customer_name == Client.name
        ).filter(
            LicenseRecord.created_at >= start_date,
            LicenseRecord.created_at <= end_date
        ).all()
    else:
        trials = []
    
    for trial, client_type in trials:
        if not trial.created_at: continue
        key = trial.created_at.strftime("%Y-%m" if group_by_mode == 'month' else "%Y-%m-%d")
        if key in data_map:
            if client_type == 1: # Enterprise
                data_map[key]["ent_trial"] += 1
            else: # Personal
                data_map[key]["per_trial"] += 1
                
    series = []
    for label in labels:
        item = data_map[label]
        series.append(schemas.ComparisonDataPoint(
            date=label,
            enterprise_sales=round(item["ent_sales"], 2),
            personal_sales=round(item["per_sales"], 2),
            enterprise_trial=item["ent_trial"],
            personal_trial=item["per_trial"]
        ))
        
    return success(schemas.AnalysisComparisonResponse(
        xAxis=labels,
        series=series
    ))

@router.post("/distribution", response_model=ResponseModel[schemas.AnalysisDistributionResponse])
def get_distribution(
    request: schemas.AnalysisTrendRequest,
    db: Session = Depends(deps.get_db)
) -> Any:
    """
    Get Order Distribution (Type & Status).
    """
    start_date, end_date, _, _ = get_date_range_and_grouping(
        request.time_dimension, request.year, request.month_range
    )
    
    # 1. Order Type Distribution (Sum of Amount)
    # Types: NEW, RENEW, UPSELL
    order_filters = get_order_filters(request.order_type)
    
    type_query = db.query(
        Order.order_type, 
        func.sum(Order.amount)
    ).filter(
        Order.created_at >= start_date,
        Order.created_at <= end_date,
        Order.status.notin_(['VOID', 'CANCELLED']),
        *order_filters
    ).group_by(Order.order_type).all()
    
    type_map = {
        "NEW": "新购",
        "RENEW": "续费",
        "UPSELL": "增购",
        "SERVICE": "人工服务",
        "IMPLEMENTATION": "项目实施"
    }
    
    type_data = []
    for type_code, amount in type_query:
        if type_code in type_map:
            type_data.append(schemas.DistributionItem(
                name=type_map[type_code],
                value=float(amount or 0)
            ))
            
    # 2. Order Status Distribution (Count of Orders)
    status_query = db.query(
        Order.status,
        func.count(Order.id)
    ).filter(
        Order.created_at >= start_date,
        Order.created_at <= end_date,
        *order_filters
    ).group_by(Order.status).all()
    
    status_map = {
        "PAID": "已成交",
        "PENDING": "待付款",
        "PARTIAL": "部分付款",
        "REFUNDED": "已退款",
        "REFUNDING": "退款中",
        "REFUND_PART": "部分退款",
        "VOID": "已作废",
        "CANCELLED": "已取消"
    }
    
    status_data = []
    for status_code, count in status_query:
        name = status_map.get(status_code, status_code)
        status_data.append(schemas.DistributionItem(
            name=name,
            value=int(count or 0)
        ))
        
    return success(schemas.AnalysisDistributionResponse(
        order_type=type_data,
        order_status=status_data
    ))

@router.get("/activities", response_model=ResponseModel[schemas.AnalysisActivitiesResponse])
def get_activities(
    db: Session = Depends(deps.get_db)
) -> Any:
    """
    Get latest follow-up activities.
    Rule: Latest 1 per client, total 20.
    """
    # Subquery: Max created_at per client
    subq = db.query(
        FollowUp.client_id,
        func.max(FollowUp.created_at).label('max_time')
    ).group_by(FollowUp.client_id).subquery()
    
    # Main Query
    query = db.query(FollowUp, Client.name, Client.type).join(
        subq,
        and_(
            FollowUp.client_id == subq.c.client_id,
            FollowUp.created_at == subq.c.max_time
        )
    ).join(Client, FollowUp.client_id == Client.id)\
    .order_by(FollowUp.created_at.desc())\
    .limit(20)
    
    results = query.all()
    
    activities = []
    for followup, client_name, client_type in results:
        # Determine color based on method or content? Default to blue.
        activities.append(schemas.ActivityItem(
            id=followup.id,
            content=followup.content,
            timestamp=followup.created_at.isoformat() if followup.created_at else "",
            color="#3b82f6", 
            avatar=None,
            client_name=client_name,
            client_type=client_type,
            method=followup.method
        ))
        
    return success(schemas.AnalysisActivitiesResponse(activities=activities))

@router.post("/new-customers", response_model=ResponseModel[schemas.AnalysisNewCustomersResponse])
def get_new_customers(
    request: schemas.AnalysisTrendRequest,
    db: Session = Depends(deps.get_db)
) -> Any:
    """
    Get New Customer Count for the last 6 months.
    """
    end_date_ref = None
    
    if request.time_dimension == 'year':
        # Find max created_at in that year
        year_int = int(request.year)
        max_date = db.query(func.max(Client.created_at)).filter(
            extract('year', Client.created_at) == year_int
        ).scalar()
        
        if max_date:
            end_date_ref = max_date
        else:
            # No data in that year? Fallback to now if current year, or Dec 31
            now = datetime.now()
            if year_int == now.year:
                end_date_ref = now
            else:
                end_date_ref = datetime(year_int, 12, 31, 23, 59, 59)
                
    else: # month
        if request.month_range and len(request.month_range) == 2:
            end_str = request.month_range[1]
            y, m = map(int, end_str.split('-'))
            _, last_day = calendar.monthrange(y, m)
            end_date_ref = datetime(y, m, last_day, 23, 59, 59)
        else:
            end_date_ref = datetime.now()
            
    # Calculate 6 months window ending at end_date_ref month
    labels = []
    curr = end_date_ref
    for _ in range(6):
        labels.insert(0, curr.strftime("%Y-%m"))
        # Move to previous month
        # Set day to 1 to safely subtract month
        first_day_curr = curr.replace(day=1)
        prev_month = first_day_curr - timedelta(days=1)
        curr = prev_month
            
    # Define query range
    start_str = labels[0]
    end_str = labels[-1]
    
    start_y, start_m = map(int, start_str.split('-'))
    start_date = datetime(start_y, start_m, 1)
    
    end_y, end_m = map(int, end_str.split('-'))
    _, last_day_end = calendar.monthrange(end_y, end_m)
    end_date = datetime(end_y, end_m, last_day_end, 23, 59, 59)
    
    # Query Clients
    clients = db.query(Client.created_at).filter(
        Client.created_at >= start_date,
        Client.created_at <= end_date
    ).all()
    
    data_map = {label: 0 for label in labels}
    
    for client in clients:
        if client.created_at:
            key = client.created_at.strftime("%Y-%m")
            if key in data_map:
                data_map[key] += 1
                
    series = [data_map[label] for label in labels]
    
    # Format labels to short month name (e.g. "2025-01" -> "1月" or "25年1月")
    # Or keep standard YYYY-MM. 
    # Existing mock used "7月". Let's try to match user preference for "Month" if same year, else "Year-Month"?
    # For API consistency, let's return YYYY-MM. Frontend can format.
    
    return success(schemas.AnalysisNewCustomersResponse(
        xAxis=labels,
        series=series
    ))

@router.post("/workbench", response_model=ResponseModel[schemas.WorkbenchResponse])
def get_workbench_data(
    request: schemas.AnalysisTrendRequest,
    db: Session = Depends(deps.get_db)
) -> Any:
    """
    Get Workbench Dashboard Data.
    Includes Summary Cards, Trend Chart, and Expense Pie Chart.
    """
    # 1. Date Range
    start_date, end_date, group_mode, labels = get_date_range_and_grouping(
        request.time_dimension, request.year, request.month_range
    )
    
    # 2. Previous Date Range
    # Comparison only shown for 'year' mode (User Request)
    calc_growth = (request.time_dimension == 'year')
    prev_start_date, prev_end_date = get_prev_date_range(start_date, end_date, request.time_dimension)
    
    # --- Helper Functions ---
    def get_net_income(start, end):
        # Income: PaymentRecord type=1 (Collection)
        income_q = db.query(func.sum(PaymentRecord.amount)).filter(
            PaymentRecord.pay_time >= start,
            PaymentRecord.pay_time <= end,
            PaymentRecord.type == 1
        )
        income_val = float(income_q.scalar() or 0.0)
        
        # Refund: PaymentRecord type=2 (Refund)
        refund_q = db.query(func.sum(PaymentRecord.amount)).filter(
            PaymentRecord.pay_time >= start,
            PaymentRecord.pay_time <= end,
            PaymentRecord.type == 2
        )
        refund_val = float(refund_q.scalar() or 0.0)
        
        return income_val - refund_val

    def get_expense(start, end):
        q = db.query(func.sum(Cost.amount)).filter(
            Cost.pay_time >= start,
            Cost.pay_time <= end
        )
        return float(q.scalar() or 0.0)
        
    def get_new_customers_count(start, end):
        q = db.query(func.count(Client.id)).filter(
            Client.created_at >= start,
            Client.created_at <= end
        )
        return int(q.scalar() or 0)
        
    def get_deal_customers_count(start, end):
        # Unique customers from PAID orders in range (based on pay_time)
        q = db.query(func.count(func.distinct(Order.client_id))).filter(
            Order.status == 'PAID',
            Order.pay_time >= start,
            Order.pay_time <= end
        )
        return int(q.scalar() or 0)
        
    # --- Summary Data ---
    
    # 1. Total Income (Net)
    income = get_net_income(start_date, end_date)
    prev_income = get_net_income(prev_start_date, prev_end_date) if calc_growth else 0
    income_growth = ((income - prev_income) / prev_income * 100) if prev_income != 0 else (100.0 if income > 0 and calc_growth else 0.0)
    
    # 2. Total Expense
    expense = get_expense(start_date, end_date)
    prev_expense = get_expense(prev_start_date, prev_end_date) if calc_growth else 0
    expense_growth = ((expense - prev_expense) / prev_expense * 100) if prev_expense != 0 else (100.0 if expense > 0 and calc_growth else 0.0)
    
    # 3. New Customers
    new_customers = get_new_customers_count(start_date, end_date)
    prev_new_customers = get_new_customers_count(prev_start_date, prev_end_date) if calc_growth else 0
    new_customers_growth = ((new_customers - prev_new_customers) / prev_new_customers * 100) if prev_new_customers != 0 else (100.0 if new_customers > 0 and calc_growth else 0.0)
    
    # 4. Deal Customers
    deal_customers = get_deal_customers_count(start_date, end_date)
    # Conversion Rate: Deal Customers / New Customers (in this period)
    # Note: This definition of conversion rate is slightly loose (deals might come from old customers), 
    # but based on standard "Funnel in Period" logic, it's Deal Count / New Lead Count.
    deal_customers_conversion_rate = (deal_customers / new_customers * 100) if new_customers > 0 else 0.0
    
    # 5. Total Profit
    profit = income - expense
    profit_margin = (profit / income * 100) if income > 0 else 0.0
    
    # --- Trend Data ---
    trend_map = {label: {"income": 0.0, "expense": 0.0} for label in labels}
    date_format = "%Y-%m" if group_mode == 'month' else "%Y-%m-%d"
    
    # Detect database type
    is_sqlite = "sqlite" in str(db.get_bind().url)
    
    # Income Trend (From PaymentRecord)
    # Collections
    if is_sqlite:
        date_func = func.strftime(date_format, PaymentRecord.pay_time)
    else:
        # MySQL DATE_FORMAT mapping
        mysql_format = date_format.replace('%Y', '%Y').replace('%m', '%m').replace('%d', '%d')
        date_func = func.date_format(PaymentRecord.pay_time, mysql_format)

    income_trend_q = db.query(
        date_func.label('d'),
        func.sum(PaymentRecord.amount)
    ).filter(
        PaymentRecord.pay_time >= start_date,
        PaymentRecord.pay_time <= end_date,
        PaymentRecord.type == 1
    ).group_by('d')
    
    for date_str, amt in income_trend_q.all():
        if date_str in trend_map:
            trend_map[date_str]["income"] += float(amt or 0)
            
    # Refunds (Subtract from Income)
    if is_sqlite:
        date_func_refund = func.strftime(date_format, PaymentRecord.pay_time)
    else:
        date_func_refund = func.date_format(PaymentRecord.pay_time, mysql_format)

    refund_trend_q = db.query(
        date_func_refund.label('d'),
        func.sum(PaymentRecord.amount)
    ).filter(
        PaymentRecord.pay_time >= start_date,
        PaymentRecord.pay_time <= end_date,
        PaymentRecord.type == 2
    ).group_by('d')
    
    for date_str, amt in refund_trend_q.all():
        if date_str in trend_map:
            trend_map[date_str]["income"] -= float(amt or 0)
            
    # Expense Trend
    if is_sqlite:
        date_func_expense = func.strftime(date_format, Cost.pay_time)
    else:
        date_func_expense = func.date_format(Cost.pay_time, mysql_format)

    expense_trend_q = db.query(
        date_func_expense.label('d'),
        func.sum(Cost.amount)
    ).filter(
        Cost.pay_time >= start_date,
        Cost.pay_time <= end_date
    ).group_by('d')
    
    for date_str, amt in expense_trend_q.all():
        if date_str in trend_map:
            trend_map[date_str]["expense"] = float(amt or 0)
            
    # Build Series
    t_income = []
    t_expense = []
    t_profit = []
    t_margin = []
    
    for label in labels:
        d = trend_map[label]
        inc = d["income"]
        exp = d["expense"]
        prof = inc - exp
        marg = (prof / inc * 100) if inc > 0 else 0.0
        
        t_income.append(round(inc, 2))
        t_expense.append(round(exp, 2))
        t_profit.append(round(prof, 2))
        t_margin.append(round(marg, 1))
        
    # --- Expense Pie ---
    pie_q = db.query(
        Cost.category,
        func.sum(Cost.amount)
    ).filter(
        Cost.pay_time >= start_date,
        Cost.pay_time <= end_date
    ).group_by(Cost.category)
    
    # Category Mapping
    category_map = {
        "LABOR": "人力成本",
        "MARKETING": "市场推广",
        "CLOUD": "服务器资源",
        "OFFICE": "办公用品",
        "TRAVEL": "差旅费",
        "OTHER": "其他",
        "AI_API": "AI资源",
        "SAAS": "软件订阅"
    }

    pie_data = []
    for cat, amt in pie_q.all():
        # Use mapped name if available, otherwise use original code
        name = category_map.get(cat, cat)
        pie_data.append(schemas.DistributionItem(name=name, value=float(amt or 0)))
        
    return success(schemas.WorkbenchResponse(
        summary=schemas.WorkbenchSummary(
            total_income=round(income, 2),
            income_growth=round(income_growth, 1),
            total_expense=round(expense, 2),
            expense_growth=round(expense_growth, 1),
            new_customers=new_customers,
            new_customers_growth=round(new_customers_growth, 1),
            deal_customers=deal_customers,
            deal_customers_conversion_rate=round(deal_customers_conversion_rate, 1),
            total_profit=round(profit, 2),
            profit_margin=round(profit_margin, 1)
        ),
        trend_xAxis=labels,
        trend_income=t_income,
        trend_expense=t_expense,
        trend_profit=t_profit,
        trend_margin=t_margin,
        expense_pie=pie_data
    ))

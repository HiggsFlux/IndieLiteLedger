from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, extract
from app.api import deps
from app.models.order import Order
from app.models.client import Client
from app.models.payment import PaymentRecord
from app.models.user import User
from app.schemas import order as schemas
from app.schemas import payment as payment_schemas
from app.schemas.response import ResponseModel, success
import datetime
import random

router = APIRouter()

def generate_order_no():
    """生成格式: ORD-20251224-1022-8848"""
    now_str = datetime.datetime.now().strftime("%Y%m%d-%H%M")
    random_str = str(random.randint(1000, 9999))
    return f"ORD-{now_str}-{random_str}"

@router.post("", response_model=ResponseModel[schemas.OrderResponse])
def create_order(
    order_in: schemas.OrderCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    """
    Create new order.
    """
    # Check client
    client = db.query(Client).filter(Client.id == order_in.client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    order_no = generate_order_no()
    # Ensure uniqueness
    while db.query(Order).filter(Order.order_no == order_no).first():
        order_no = generate_order_no()

    db_order = Order(
        **order_in.model_dump(),
        order_no=order_no,
        client_name=client.name,
        creator_id=current_user.id,
        status="PENDING", # Default status
        actual_amount=0.00, # Default paid
        total_paid=0.00
    )
    db.add(db_order)
    db.commit()
    db.refresh(db_order)
    return success(db_order)

@router.get("", response_model=ResponseModel[List[schemas.OrderResponse]])
def read_orders(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    client_name: Optional[str] = None,
    order_no: Optional[str] = None,
    pay_method: Optional[str] = None
) -> Any:
    """
    Retrieve orders.
    """
    query = db.query(Order)
    
    # RBAC
    if current_user.role and current_user.role.code == "STAFF":
        query = query.filter(Order.creator_id == current_user.id)
    
    if status:
        query = query.filter(Order.status == status)
    if client_name:
        query = query.filter(Order.client_name.ilike(f"%{client_name}%"))
    if order_no:
        query = query.filter(Order.order_no.ilike(f"%{order_no}%"))
    if pay_method:
        query = query.filter(Order.pay_method == pay_method)
        
    orders = query.order_by(Order.created_at.desc()).offset(skip).limit(limit).all()
    return success(orders)

@router.get("/stats", response_model=ResponseModel[schemas.OrderStats])
def get_stats(
    db: Session = Depends(deps.get_db)
) -> Any:
    """
    Get order statistics.
    """
    now = datetime.datetime.now()
    start_of_month = datetime.datetime(now.year, now.month, 1)
    
    # 1. Monthly Revenue (Net collection in this month)
    monthly_collection = db.query(func.sum(PaymentRecord.amount)).filter(
        PaymentRecord.type == 1,
        PaymentRecord.pay_time >= start_of_month
    ).scalar() or 0
    
    monthly_refund = db.query(func.sum(PaymentRecord.amount)).filter(
        PaymentRecord.type == 2,
        PaymentRecord.pay_time >= start_of_month
    ).scalar() or 0
    
    monthly_revenue = monthly_collection - monthly_refund
    
    # 2. Pending Amount (Total uncollected amount for non-void orders)
    pending_amount = db.query(func.sum(Order.amount - Order.total_paid)).filter(
        Order.status != "VOID",
        Order.status != "REFUNDED"
    ).scalar() or 0
    
    # 3. Monthly Count (Orders created in this month)
    monthly_count = db.query(func.count(Order.id)).filter(
        Order.created_at >= start_of_month
    ).scalar() or 0
    
    return success({
        "monthly_revenue": monthly_revenue,
        "pending_amount": pending_amount,
        "monthly_count": monthly_count
    })

def calculate_order_status(order: Order, db: Session):
    """
    Calculate and update order status based on payment records.
    Status Logic:
    - PENDING: Net Paid == 0
    - PARTIAL: 0 < Net Paid < Total Price
    - PAID: Net Paid >= Total Price
    - REFUND_PART: Has refunds AND 0 < Net Paid < Total Price
    - REFUNDED: Has refunds AND Net Paid == 0
    """
    # 1. Get all payment records
    records = db.query(PaymentRecord).filter(PaymentRecord.order_id == order.id).all()
    
    total_collection = sum(r.amount for r in records if r.type == 1)
    total_refund = sum(r.amount for r in records if r.type == 2)
    net_paid = total_collection - total_refund
    has_refund = any(r.type == 2 for r in records)
    
    order.total_paid = net_paid
    order.actual_amount = net_paid # Sync legacy field
    
    # 2. Determine status
    if net_paid >= order.amount:
        order.status = "PAID"
        if not order.pay_time:
            order.pay_time = datetime.datetime.now()
    elif net_paid > 0:
        if has_refund:
            order.status = "REFUND_PART"
        else:
            order.status = "PARTIAL"
    else:
        # Net paid == 0 (or less, though shouldn't happen if validation is correct)
        if has_refund:
             order.status = "REFUNDED"
        else:
             order.status = "PENDING"
             order.pay_time = None # Reset pay time

    db.add(order)
    db.flush()

# Payment Records API
@router.post("/{id}/payments", response_model=ResponseModel[payment_schemas.PaymentRecordResponse])
def create_payment_record(
    id: str,
    payment_in: payment_schemas.PaymentRecordBase,
    db: Session = Depends(deps.get_db)
) -> Any:
    """Create a new payment record (Collection or Refund) and update order status"""
    order = db.query(Order).filter(Order.id == id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    # Validation for Refund
    if payment_in.type == 2:
        if order.total_paid < payment_in.amount:
            raise HTTPException(status_code=400, detail="退款金额不能大于已收金额")
            
    payment = PaymentRecord(
        order_id=id,
        **payment_in.model_dump(),
        creator_id=1
    )
    db.add(payment)
    db.flush() # Get ID
    
    # Recalculate order status
    calculate_order_status(order, db)
    
    db.commit()
    db.refresh(payment)
    return success(payment)

@router.get("/{id}/payments", response_model=ResponseModel[List[payment_schemas.PaymentRecordResponse]])
def read_payment_records(
    id: str,
    db: Session = Depends(deps.get_db)
) -> Any:
    """List payment records for an order"""
    payments = db.query(PaymentRecord).filter(PaymentRecord.order_id == id).order_by(PaymentRecord.pay_time.desc()).all()
    return success(payments)

@router.delete("/{id}/payments/{payment_id}", response_model=ResponseModel[schemas.OrderResponse])
def delete_payment_record(
    id: str,
    payment_id: str,
    db: Session = Depends(deps.get_db)
) -> Any:
    """Delete a payment record and update order status"""
    payment = db.query(PaymentRecord).filter(PaymentRecord.id == payment_id, PaymentRecord.order_id == id).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment record not found")
        
    db.delete(payment)
    db.flush()
    
    order = db.query(Order).filter(Order.id == id).first()
    calculate_order_status(order, db)
    
    db.commit()
    db.refresh(order)
    return success(order)

@router.post("/{id}/void", response_model=ResponseModel[schemas.OrderResponse])
def void_order(
    id: str,
    db: Session = Depends(deps.get_db)
) -> Any:
    """
    Void an order.
    Only allowed if Net Paid (total_paid) == 0.
    """
    order = db.query(Order).filter(Order.id == id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    if order.total_paid > 0:
        raise HTTPException(status_code=400, detail="该订单已产生资金流水，请先将款项全部退回/删除收款记录后，再进行作废操作。")
        
    order.status = "VOID"
    db.add(order)
    db.commit()
    db.refresh(order)
    return success(order)

@router.get("/{id}", response_model=ResponseModel[schemas.OrderResponse])
def read_order(
    id: str,
    db: Session = Depends(deps.get_db)
) -> Any:
    """
    Get order by ID.
    """
    order = db.query(Order).filter(Order.id == id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return success(order)

@router.patch("/{id}", response_model=ResponseModel[schemas.OrderResponse])
def update_order(
    id: str,
    order_in: schemas.OrderUpdate,
    db: Session = Depends(deps.get_db)
) -> Any:
    order = db.query(Order).filter(Order.id == id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    update_data = order_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(order, field, value)
    
    db.add(order)
    db.commit()
    db.refresh(order)
    return success(order)

@router.patch("/{id}/status", response_model=ResponseModel[schemas.OrderResponse])
def update_order_status(
    id: str,
    status: str = Query(..., description="New status"),
    external_transaction_no: Optional[str] = Query(None, description="External transaction number"),
    db: Session = Depends(deps.get_db)
) -> Any:
    order = db.query(Order).filter(Order.id == id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
        
    order.status = status
    if status == "PAID" and not order.pay_time:
        order.pay_time = datetime.datetime.now()
        
    if external_transaction_no:
        order.external_transaction_no = external_transaction_no
        
    db.add(order)
    db.commit()
    db.refresh(order)
    return success(order)

@router.patch("/{id}/invoice", response_model=ResponseModel[schemas.OrderResponse])
def update_order_invoice(
    id: str,
    is_invoiced: bool = Query(..., description="Is invoiced"),
    db: Session = Depends(deps.get_db)
) -> Any:
    order = db.query(Order).filter(Order.id == id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
        
    order.is_invoiced = is_invoiced
    if is_invoiced and not order.invoice_time:
        order.invoice_time = datetime.datetime.now()
        
    db.add(order)
    db.commit()
    db.refresh(order)
    return success(order)

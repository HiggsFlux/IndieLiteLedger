from sqlalchemy import Column, String, Integer, DateTime, Numeric, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.db.base_class import Base
import uuid
from datetime import datetime

def generate_uuid():
    return str(uuid.uuid4())

class PaymentRecord(Base):
    __tablename__ = "sys_payment_record"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    
    order_id = Column(String(36), ForeignKey("sys_order.id"), nullable=False, index=True)
    
    amount = Column(Numeric(10, 2), nullable=False)
    type = Column(Integer, default=1, nullable=False) # 1: Collection (收款), 2: Refund (退款)
    pay_method = Column(String(20), nullable=False) # WECHAT, ALIPAY, BANK
    transaction_id = Column(String(100), nullable=True) # External Transaction No
    pay_time = Column(DateTime, default=datetime.now)
    
    remark = Column(Text, nullable=True)
    creator_id = Column(Integer, default=1)
    
    # Relationships
    order = relationship("Order", back_populates="payment_records")

from sqlalchemy import Column, String, Integer, DateTime, Text, Boolean, Numeric, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base_class import Base
import uuid
from datetime import datetime

def generate_uuid():
    return str(uuid.uuid4())

class Order(Base):
    __tablename__ = "sys_order"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    order_no = Column(String(50), unique=True, index=True, nullable=False)
    
    client_id = Column(String(36), ForeignKey("client.id"), nullable=False, index=True)
    client_name = Column(String(100), nullable=False) # Redundant
    
    product_info = Column(Text, nullable=False)
    amount = Column(Numeric(10, 2), default=0.00, nullable=False)
    actual_amount = Column(Numeric(10, 2), default=0.00, nullable=False)
    
    status = Column(String(20), default="PENDING", nullable=False) # PENDING, PAID, CANCELLED, REFUNDING
    order_type = Column(String(20), default="NEW", nullable=False) # NEW, RENEW, UPSELL, SERVICE, IMPLEMENTATION
    pay_method = Column(String(20), default="BANK", nullable=False) # WECHAT, ALIPAY, BANK, CASH
    pay_time = Column(DateTime, nullable=True)
    external_transaction_no = Column(String(100), nullable=True) # External Transaction ID
    
    contract_no = Column(String(50), nullable=True)
    is_invoiced = Column(Boolean, default=False)
    invoice_time = Column(DateTime, nullable=True)
    
    remark = Column(Text, nullable=True)
    creator_id = Column(String(36), ForeignKey("sys_user.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # New fields for V2
    attachments = Column(Text, default="[]") # JSON string: [{"name": "x", "url": "x", "type": "x"}]
    total_paid = Column(Numeric(10, 2), default=0.00)

    # Relationships
    client = relationship("Client", backref="orders")
    payment_records = relationship("PaymentRecord", back_populates="order", cascade="all, delete-orphan")

    @property
    def client_type(self):
        return self.client.type if self.client else None

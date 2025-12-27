from sqlalchemy import Column, String, Integer, DateTime, Text, JSON, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base_class import Base
import uuid
from datetime import datetime

def generate_uuid():
    return str(uuid.uuid4())

class Client(Base):
    id = Column(String(36), primary_key=True, default=generate_uuid)
    type = Column(Integer, nullable=False)  # 0: Individual, 1: Enterprise
    status = Column(Integer, nullable=False, default=0) # 0:Lead, 1:Trial, 2:Deal, 3:Churn, 9:Block
    source = Column(String(50), nullable=True)
    level = Column(Integer, default=1) # 1-5
    tags = Column(JSON, nullable=True)
    extra_info = Column(JSON, default={})
    
    name = Column(String(100), nullable=False) # Name or Company Name
    contact_person = Column(String(50), nullable=True) # Enterprise only
    position = Column(String(50), nullable=True) # Enterprise only
    wechat = Column(String(50), nullable=True)
    phone = Column(String(20), nullable=True)
    email = Column(String(100), nullable=True)
    tax_info = Column(JSON, nullable=True) # Enterprise only
    remark = Column(Text, nullable=True)
    
    creator_id = Column(String(36), ForeignKey("sys_user.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    follow_ups = relationship("FollowUp", back_populates="client", cascade="all, delete-orphan")

class FollowUp(Base):
    __tablename__ = "sys_client_followup" # As per doc
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    client_id = Column(String(36), ForeignKey("client.id"), nullable=False)
    method = Column(String(20), nullable=False) # Wechat, Phone, Visit, Email
    content = Column(Text, nullable=False)
    next_time = Column(DateTime, nullable=True)
    recorder_id = Column(String(36), nullable=True) 
    
    created_at = Column(DateTime, default=datetime.now)
    
    client = relationship("Client", back_populates="follow_ups")

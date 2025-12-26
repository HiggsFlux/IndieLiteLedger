from sqlalchemy import Column, String, Boolean, DateTime, JSON, Integer
from app.db.base_class import Base
import uuid
from datetime import datetime

def generate_uuid():
    return str(uuid.uuid4())

class Role(Base):
    __tablename__ = "sys_role"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    
    # Basic Info
    name = Column(String(50), index=True, nullable=False) # e.g. Sales
    code = Column(String(50), unique=True, index=True, nullable=False) # e.g. SALES
    description = Column(String(255), nullable=True)
    
    # 1. Menu Permissions
    # Store list of route names, e.g., ["dashboard", "order_list"]
    menu_keys = Column(JSON, default=[])
    
    # 2. Data Scope
    # 1: All Data, 2: Self Data
    data_scope = Column(Integer, default=2)
    
    # System roles cannot be deleted
    is_system = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=datetime.now)

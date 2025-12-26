from sqlalchemy import Column, String, Boolean, DateTime, Text
from app.db.base_class import Base
import uuid
from datetime import datetime

def generate_uuid():
    return str(uuid.uuid4())

class SysConfig(Base):
    __tablename__ = "sys_config"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    config_key = Column(String(50), unique=True, nullable=False, index=True)
    config_value = Column(Text, nullable=True)
    group_code = Column(String(20), nullable=False, index=True) # basic, license, security, theme
    is_public = Column(Boolean, default=False) # 0: Admin only, 1: Public
    description = Column(String(100), nullable=True)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

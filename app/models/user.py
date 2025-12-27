from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base_class import Base
import uuid
from datetime import datetime

def generate_uuid():
    return str(uuid.uuid4())

class User(Base):
    __tablename__ = "sys_user"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    
    # --- Login Info ---
    username = Column(String(50), unique=True, index=True, nullable=False)
    hashed_password = Column(String(100), nullable=False)
    
    # --- Identity Info ---
    nickname = Column(String(50), nullable=False)
    avatar = Column(String(255), nullable=True)
    
    # --- Permission Core ---
    # Replace role string with foreign key
    role_id = Column(String(36), ForeignKey("sys_role.id"), nullable=True)
    role = relationship("Role", backref="users")
    
    # --- Status Control ---
    is_active = Column(Boolean, default=True)
    
    created_at = Column(DateTime, default=datetime.now)

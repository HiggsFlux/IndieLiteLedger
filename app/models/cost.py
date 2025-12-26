from sqlalchemy import Column, String, Integer, Text, Numeric, DateTime, ForeignKey, Date
from app.db.base_class import Base
import uuid
from datetime import datetime

def generate_uuid():
    return str(uuid.uuid4())

class Cost(Base):
    __tablename__ = "sys_cost"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    
    # --- 基础信息 ---
    title = Column(String(255), index=True, nullable=False, doc="摘要，如: 阿里云12月ECS续费")
    amount = Column(Numeric(10, 2), nullable=False, doc="支出金额(正数)")
    
    # --- 核心分类 ---
    # CLOUD, AI_API, LABOR, SAAS, MARKETING, OTHER
    category = Column(String(50), index=True, nullable=False, doc="支出类别")
    
    # --- 资金流向 ---
    pay_time = Column(Date, nullable=False, doc="实际付款日期")
    pay_account = Column(String(50), default="ALIPAY", doc="支出账户: ALIPAY/WECHAT/BANK")
    
    # --- 审计与凭证 ---
    invoice_url = Column(String(500), nullable=True, doc="发票/回单截图 URL")
    remark = Column(Text, nullable=True, doc="详细备注")
    
    creator_id = Column(String(36), ForeignKey("sys_user.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.now)

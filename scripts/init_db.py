import sys
import os
import uuid
from datetime import datetime

# 将后端目录添加到 sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.session import SessionLocal, engine
from app.db.base import Base
from app.models.user import User
from app.models.role import Role
from app.models.sys_config import SysConfig
from app.core.security import get_password_hash

def generate_uuid():
    return str(uuid.uuid4())

def init_db():
    print("正在创建数据库表...")
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        # 1. 初始化角色
        print("正在初始化角色...")
        roles_data = [
            {
                "id": generate_uuid(),
                "name": "超级管理员",
                "code": "SUPER",
                "description": "系统最高权限，拥有所有功能访问权限",
                "menu_keys": ["*"],
                "data_scope": 1,
                "is_system": True
            },
            {
                "id": generate_uuid(),
                "name": "管理员",
                "code": "ADMIN",
                "description": "普通管理员权限",
                "menu_keys": [],
                "data_scope": 1,
                "is_system": True
            },
            {
                "id": generate_uuid(),
                "name": "普通用户",
                "code": "USER",
                "description": "普通用户权限",
                "menu_keys": [],
                "data_scope": 2,
                "is_system": True
            }
        ]
        
        created_roles = {}
        for r_data in roles_data:
            role = db.query(Role).filter(Role.code == r_data["code"]).first()
            if not role:
                role = Role(**r_data)
                db.add(role)
                db.commit()
                db.refresh(role)
                print(f"角色已创建: {role.name}")
            created_roles[role.code] = role

        # 2. 初始化管理员用户
        print("正在检查管理员用户...")
        admin_user = db.query(User).filter(User.username == "admin").first()
        if not admin_user:
            print("正在创建默认管理员 (admin / 123456)...")
            admin_user = User(
                id=generate_uuid(),
                username="admin",
                hashed_password=get_password_hash("123456"),
                nickname="系统管理员",
                role_id=created_roles["SUPER"].id,
                is_active=True
            )
            db.add(admin_user)
            db.commit()
            print("管理员用户已创建。")
        else:
            print("管理员用户已存在。")

        # 3. 初始化基础系统配置
        print("正在初始化系统配置...")
        initial_configs = [
            {
                "config_key": "system.app_name",
                "config_value": "IndieLiteLedger",
                "group_code": "basic",
                "is_public": True,
                "description": "系统名称"
            },
            {
                "config_key": "system.logo",
                "config_value": "",
                "group_code": "basic",
                "is_public": True,
                "description": "系统 Logo 地址"
            },
            {
                "config_key": "security.session_timeout",
                "config_value": "60",
                "group_code": "security",
                "is_public": True,
                "description": "会话超时时间 (分钟)"
            }
        ]
        
        for config_data in initial_configs:
            existing = db.query(SysConfig).filter(SysConfig.config_key == config_data["config_key"]).first()
            if not existing:
                config = SysConfig(id=generate_uuid(), **config_data)
                db.add(config)
                print(f"配置项已添加: {config_data['config_key']}")
            
        db.commit()
        print("数据库初始化完成！")

    except Exception as e:
        print(f"初始化过程中发生错误: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    init_db()

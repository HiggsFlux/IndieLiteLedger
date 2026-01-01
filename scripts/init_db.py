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

# Try to import plugin models so they are registered with Base
try:
    from app.modules.plugins.commercial_kit import models
    print("Loaded commercial_kit models for initialization")
except ImportError:
    pass

def generate_uuid():
    return str(uuid.uuid4())

def init_db():
    print("正在准备初始化数据库...")
    
    print("正在创建新数据库表 (如果不存在)...")
    try:
        Base.metadata.create_all(bind=engine)
        print("数据库表创建成功。")
    except Exception as e:
        print(f"创建数据库表失败: {e}")
        return # 如果表都建不成功，后面也没法跑了
    
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
                print(f"角色已创建: {role.name} ({role.code})")
            else:
                print(f"角色已存在: {role.name} ({role.code})")
            created_roles[role.code] = role

        # 2. 初始化管理员用户
        print("正在检查用户表...")
        user_count = db.query(User).count()
        if user_count == 0:
            print("数据库中尚无用户，正在创建默认管理员 (admin / 123456)...")
            if "SUPER" not in created_roles:
                print("错误: 未找到 SUPER 角色，无法创建管理员")
                return

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
            print(f"数据库中已存在 {user_count} 个用户，跳过管理员初始化。")

        # 3. 初始化基础系统配置
        print("正在初始化系统配置...")
        initial_configs = [
            # --- 基础设置 ---
            {
                "config_key": "system.app_name",
                "config_value": "TalkMyDataBoss",
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
                "config_key": "system.favicon",
                "config_value": "",
                "group_code": "basic",
                "is_public": True,
                "description": "浏览器图标地址"
            },
            # --- 安全设置 ---
            {
                "config_key": "security.session_timeout",
                "config_value": "60",
                "group_code": "security",
                "is_public": True,
                "description": "会话超时时间 (分钟)"
            },
            # --- 主题设置 (由前端 theme store 自动维护，这里提供初始结构) ---
            {
                "config_key": "system.theme",
                "config_value": "{}",
                "group_code": "theme",
                "is_public": True,
                "description": "系统主题配置 (JSON)"
            }
        ]
        
        # 4. 初始化商业版插件特定数据 (License 模块定义)
        print("正在检查商业版插件配置...")
        try:
            from app.modules.plugins.commercial_kit.models import LicenseConfig
            commercial_modules = [
                {
                    "module_code": "CORE",
                    "module_name": "System Core",
                    "module_name_cn": "系统核心模块",
                    "module_type": "SYSTEM",
                    "default_strategy": "PERMANENT",
                    "description": "系统运行的基础核心功能",
                    "sort_order": 1
                },
                {
                    "module_code": "PLUGIN_WORKFLOW",
                    "module_name": "Advanced Workflow",
                    "module_name_cn": "高级工作流插件",
                    "module_type": "PLUGIN",
                    "default_strategy": "TRIAL",
                    "description": "提供更高级的自动化工作流能力",
                    "sort_order": 10
                },
                {
                    "module_code": "PLUGIN_AI",
                    "module_name": "AI Assistant",
                    "module_name_cn": "AI 助手插件",
                    "module_type": "PLUGIN",
                    "default_strategy": "TRIAL",
                    "description": "集成大模型能力的 AI 辅助功能",
                    "sort_order": 20
                }
            ]
            
            for mod_data in commercial_modules:
                existing_mod = db.query(LicenseConfig).filter(LicenseConfig.module_code == mod_data["module_code"]).first()
                if not existing_mod:
                    new_mod = LicenseConfig(id=generate_uuid(), **mod_data)
                    db.add(new_mod)
                    print(f"License 模块已添加: {mod_data['module_name_cn']}")
        except (ImportError, Exception) as e:
            print(f"跳过商业版模块初始化: {e}")

        for config_data in initial_configs:
            existing = db.query(SysConfig).filter(SysConfig.config_key == config_data["config_key"]).first()
            if not existing:
                config = SysConfig(id=generate_uuid(), **config_data)
                db.add(config)
                print(f"配置项已添加: {config_data['config_key']}")
            else:
                # 更新已有的关键配置项，确保 app_name 等同步
                if config_data["config_key"] in ["system.app_name"]:
                    existing.config_value = config_data["config_value"]
                    db.add(existing)
            
        db.commit()
        print("数据库初始化完成！")

    except Exception as e:
        print(f"初始化过程中发生错误: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    init_db()

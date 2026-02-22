#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库初始化脚本
用于创建初始管理员账号和角色
"""

import sys
import os

# 获取当前脚本所在目录，并添加到Python路径中
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# 确保当前工作目录正确设置为y-sso-system目录
os.chdir(current_dir)


# 检查并创建数据库目录（如果使用的是SQLite）
def ensure_db_directory_exists():
    """确保数据库目录存在，避免engine初始化失败"""
    try:
        from app.config import settings
        db_url = settings.database.url

        if db_url.startswith("sqlite:///"):
            db_path = db_url[len("sqlite:///"):]
            abs_db_path = os.path.abspath(db_path)
            db_dir = os.path.dirname(abs_db_path)

            if not os.path.exists(db_dir):
                os.makedirs(db_dir, exist_ok=True)
                print(f"创建数据库目录: {db_dir}")
            else:
                print(f"数据库目录已存在: {db_dir}")
    except Exception as e:
        print(f"检查数据库目录时出错: {e}")


# 在导入数据库模块之前先确保数据库目录存在
ensure_db_directory_exists()

from yweb.log import get_logger
from yweb.auth import PasswordHelper

logger = get_logger()

# ======================== 统一模型注册 ========================
# 通过 models_registry 一次性注册全部模型（静态 + 动态），
# 避免手动维护散乱的 import 列表，详见 app/models_registry.py
from app.models_registry import User, ensure_dynamic_models

registry = ensure_dynamic_models()
Role = registry.role_model

from app.database import get_engine
from yweb.orm import BaseModel

try:
    BaseModel.metadata.create_all(bind=get_engine())
    logger.info("数据库表结构创建成功")
except Exception as e:
    logger.error(f"创建数据库表结构时出错: {e}")
    raise



# 初始化数据
def init_database():
    """初始化数据库，创建默认角色和管理员账户"""
    try:
        # 获取数据库会话
        from yweb.orm import db_manager
        db = db_manager.get_session()
        
        # 检查并创建管理员角色
        admin_role = db.query(Role).filter(Role.code == "admin").first()
        if not admin_role:
            # 创建管理员角色
            admin_role = Role(
                name="管理员",
                code="admin",
                description="系统管理员，拥有所有权限"
            )
            db.add(admin_role)
            db.flush()  # 刷新以获取ID
            logger.info("创建管理员角色成功")
        else:
            logger.info("管理员角色已存在")
        
        # 检查并创建内部员工角色
        user_role = db.query(Role).filter(Role.code == "user").first()
        if not user_role:
            # 创建内部员工角色
            user_role = Role(
                name="内部员工",
                code="user",
                description="内部员工，拥有业务相关权限"
            )
            db.add(user_role)
            db.flush()  # 刷新以获取ID
            logger.info("创建内部员工角色成功")
        else:
            logger.info("内部员工角色已存在")
            
        # 检查并创建外部用户角色
        external_role = db.query(Role).filter(Role.code == "external").first()
        if not external_role:
            # 创建外部用户角色
            external_role = Role(
                name="外部用户",
                code="external",
                description="外部用户，拥有受限权限"
            )
            db.add(external_role)
            db.flush()  # 刷新以获取ID
            logger.info("创建外部用户角色成功")
        else:
            logger.info("外部用户角色已存在")
        
        # 检查是否已经存在管理员账号
        admin_user = db.query(User).filter(User.username == "admin").first()
        if not admin_user:
            # 创建管理员账号，使用 pbkdf2_sha256 加密
            admin_user = User(
                username="admin",
                password_hash=PasswordHelper.hash("admin123"),
                email="admin@example.com",
                is_active=True
            )
            db.add(admin_user)
            db.flush()  # 刷新以获取ID
            logger.info("创建管理员账号成功")
            
            # 给管理员账号分配管理员角色
            admin_user.roles.append(admin_role)
            logger.info("给管理员账号分配管理员角色成功")
        else:
            logger.info("管理员账号已存在")
        
        # 提交事务
        db.commit()
        
        logger.info("数据库初始化完成")
        logger.info("管理员账号: admin")
        logger.info("管理员密码: admin123")
        
    except Exception as e:
        logger.error(f"数据库初始化过程中发生错误: {str(e)}")
        # 回滚事务
        db.rollback()
        raise e
    finally:
        # 关闭会话
        db.close()

if __name__ == "__main__":
    init_database()
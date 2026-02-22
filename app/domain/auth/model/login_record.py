from typing import Optional
from datetime import datetime
from sqlalchemy import Integer, DateTime, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column
from yweb.auth import AbstractLoginRecord


class LoginRecord(AbstractLoginRecord):
    """登录记录实体
    
    继承 AbstractLoginRecord 获得：
        - ORM 能力：id, created_at, updated_at, .add(), .query, 软删除等
        - 标准字段：user_id, username, ip_address, user_agent, status, failure_reason,
          login_at, location, device_info
        - 便捷方法：create_record(), get_recent_logins(), get_user_logins(), count_records()
    
    项目覆写：
        - user_id: 添加 ForeignKey 约束并设为非空
        - login_at: 使用不带 timezone 的 DateTime（兼容 SQLite）
        - __table_args__: 覆写索引定义以匹配实际表名
    """
    
    # 覆写 user_id：添加外键约束，设为非空
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("user.id", ondelete="CASCADE"),
        nullable=False, index=True, comment="用户ID"
    )
    
    # 覆写 login_at：不使用 timezone（SQLite 兼容）
    login_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
        default=datetime.now,
        index=True,
        comment="登录时间"
    )
    
    # 覆写 __table_args__：使用项目实际的表名和列名
    __table_args__ = (
        Index('ix_login_record_user_time', 'user_id', 'login_at'),
        Index('ix_login_record_ip_time', 'ip_address', 'login_at'),
    )

"""Alembic 迁移辅助：列已存在则跳过，避免 MySQL 1060 Duplicate column。"""

from alembic import op
from sqlalchemy import inspect


def column_exists(table_name: str, column_name: str) -> bool:
    inspector = inspect(op.get_bind())
    return any(col["name"] == column_name for col in inspector.get_columns(table_name))

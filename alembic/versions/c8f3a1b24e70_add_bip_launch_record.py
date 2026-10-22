"""add bip launch record

Revision ID: c8f3a1b24e70
Revises: b7e1c2a94d30
Create Date: 2026-10-22 09:10:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c8f3a1b24e70"
down_revision: Union[str, None] = "b7e1c2a94d30"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "bip_launch_record" in inspector.get_table_names():
        return
    op.create_table(
        "bip_launch_record",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True, comment="主键ID"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False, comment="创建时间"),
        sa.Column("updated_at", sa.DateTime(), nullable=True, comment="更新时间"),
        sa.Column("deleted_at", sa.DateTime(), nullable=True, comment="删除时间（软删除标记）"),
        sa.Column("ver", sa.Integer(), nullable=False, server_default="1", comment="版本号"),
        sa.Column(
            "application_id",
            sa.Integer(),
            sa.ForeignKey("application.id", ondelete="CASCADE"),
            nullable=False,
            comment="应用ID",
        ),
        sa.Column("called_at", sa.DateTime(timezone=True), nullable=False, comment="调用时间"),
    )
    op.create_index(
        "ix_bip_launch_record_app_called_at",
        "bip_launch_record",
        ["application_id", "called_at"],
    )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "bip_launch_record" not in inspector.get_table_names():
        return
    op.drop_index("ix_bip_launch_record_app_called_at", table_name="bip_launch_record")
    op.drop_table("bip_launch_record")

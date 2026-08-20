"""add id_card to employee

Revision ID: a1b2c3d4e5f6
Revises: 9b2c4d1e5f6a
Create Date: 2026-08-12 10:45:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = "9b2c4d1e5f6a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("employee", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("id_card", sa.String(length=18), nullable=True, comment="身份证号")
        )


def downgrade() -> None:
    with op.batch_alter_table("employee", schema=None) as batch_op:
        batch_op.drop_column("id_card")

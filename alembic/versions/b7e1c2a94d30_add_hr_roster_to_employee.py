"""add hr_roster to employee

Revision ID: b7e1c2a94d30
Revises: a1b2c3d4e5f6
Create Date: 2026-10-20 11:10:00.000000

"""
from typing import Sequence, Union
import sys
from pathlib import Path

from alembic import op
import sqlalchemy as sa

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from helpers import column_exists  # noqa: E402


revision: str = "b7e1c2a94d30"
down_revision: Union[str, None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    if column_exists("employee", "hr_roster"):
        return
    with op.batch_alter_table("employee", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("hr_roster", sa.JSON(), nullable=True, comment="人事助手花名册快照（JSON）")
        )


def downgrade() -> None:
    if not column_exists("employee", "hr_roster"):
        return
    with op.batch_alter_table("employee", schema=None) as batch_op:
        batch_op.drop_column("hr_roster")

"""add allowed_ip_cidrs to application

Revision ID: 9b2c4d1e5f6a
Revises: 6c1d8e4a7b21
Create Date: 2026-04-15 00:00:00.000000

"""
from typing import Sequence, Union
import sys
from pathlib import Path

from alembic import op
import sqlalchemy as sa

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from helpers import column_exists  # noqa: E402


# revision identifiers, used by Alembic.
revision: str = "9b2c4d1e5f6a"
down_revision: Union[str, None] = "6c1d8e4a7b21"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    if column_exists("application", "allowed_ip_cidrs"):
        return
    with op.batch_alter_table("application", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                "allowed_ip_cidrs",
                sa.Text(),
                nullable=True,
                comment="允许访问应用后向通道的IP白名单（JSON格式存储）",
            )
        )


def downgrade() -> None:
    with op.batch_alter_table("application", schema=None) as batch_op:
        batch_op.drop_column("allowed_ip_cidrs")

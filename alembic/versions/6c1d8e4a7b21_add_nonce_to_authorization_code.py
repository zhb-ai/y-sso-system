"""add nonce to authorization_code

Revision ID: 6c1d8e4a7b21
Revises: efc5e98f7dfa
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
revision: str = "6c1d8e4a7b21"
down_revision: Union[str, None] = "efc5e98f7dfa"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    if column_exists("authorization_code", "nonce"):
        return
    with op.batch_alter_table("authorization_code", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("nonce", sa.String(length=255), nullable=True, comment="OIDC nonce 参数")
        )


def downgrade() -> None:
    with op.batch_alter_table("authorization_code", schema=None) as batch_op:
        batch_op.drop_column("nonce")

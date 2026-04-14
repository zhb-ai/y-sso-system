"""add client_type to application and PKCE fields to authorization_code

Revision ID: a1b2c3d4e5f6
Revises: None
Create Date: 2026-04-14

Changes:
    - application: add column `client_type` (VARCHAR(20), default 'confidential')
    - authorization_code: add column `code_challenge` (VARCHAR(128), nullable)
    - authorization_code: add column `code_challenge_method` (VARCHAR(10), nullable)
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("application") as batch_op:
        batch_op.add_column(
            sa.Column(
                "client_type",
                sa.String(20),
                nullable=False,
                server_default="confidential",
                comment="客户端类型: confidential（机密）或 public（公开/SPA）",
            )
        )

    with op.batch_alter_table("authorization_code") as batch_op:
        batch_op.add_column(
            sa.Column(
                "code_challenge",
                sa.String(128),
                nullable=True,
                comment="PKCE code_challenge（BASE64URL-encoded）",
            )
        )
        batch_op.add_column(
            sa.Column(
                "code_challenge_method",
                sa.String(10),
                nullable=True,
                comment="PKCE 方法: S256 或 plain",
            )
        )


def downgrade() -> None:
    with op.batch_alter_table("authorization_code") as batch_op:
        batch_op.drop_column("code_challenge_method")
        batch_op.drop_column("code_challenge")

    with op.batch_alter_table("application") as batch_op:
        batch_op.drop_column("client_type")

"""add auth user role

Revision ID: 004_auth_role
Revises: 003_auth
Create Date: 2026-05-14
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "004_auth_role"
down_revision: Union[str, None] = "003_auth"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "auth_users",
        sa.Column("role", sa.String(50), nullable=False, server_default="tenant_user"),
    )
    op.create_index("ix_auth_users_role", "auth_users", ["role"])


def downgrade() -> None:
    op.drop_index("ix_auth_users_role", table_name="auth_users")
    op.drop_column("auth_users", "role")

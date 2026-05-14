"""create NextAuth auth tables

Revision ID: 003_auth
Revises: 002_billing
Create Date: 2026-05-14
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "003_auth"
down_revision: Union[str, None] = "002_billing"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "auth_users",
        sa.Column("id", sa.String(255), primary_key=True),
        sa.Column("name", sa.String(255), nullable=True),
        sa.Column("email", sa.String(255), nullable=True, unique=True),
        sa.Column("email_verified", sa.DateTime(timezone=True), nullable=True),
        sa.Column("image", sa.Text(), nullable=True),
        sa.Column("password_hash", sa.Text(), nullable=True),
        sa.Column("tenant_id", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_auth_users_email", "auth_users", ["email"])

    op.create_table(
        "auth_accounts",
        sa.Column("id", sa.String(255), primary_key=True),
        sa.Column("user_id", sa.String(255), sa.ForeignKey("auth_users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("type", sa.String(255), nullable=False),
        sa.Column("provider", sa.String(255), nullable=False),
        sa.Column("provider_account_id", sa.String(255), nullable=False),
        sa.Column("refresh_token", sa.Text(), nullable=True),
        sa.Column("access_token", sa.Text(), nullable=True),
        sa.Column("expires_at", sa.BigInteger(), nullable=True),
        sa.Column("token_type", sa.String(255), nullable=True),
        sa.Column("scope", sa.String(255), nullable=True),
        sa.Column("id_token", sa.Text(), nullable=True),
        sa.Column("session_state", sa.String(255), nullable=True),
        sa.UniqueConstraint("provider", "provider_account_id", name="uq_accounts_provider"),
    )

    op.create_table(
        "auth_sessions",
        sa.Column("id", sa.String(255), primary_key=True),
        sa.Column("session_token", sa.String(255), unique=True, nullable=False),
        sa.Column("user_id", sa.String(255), sa.ForeignKey("auth_users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("expires", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "auth_verification_tokens",
        sa.Column("identifier", sa.String(255), nullable=False),
        sa.Column("token", sa.String(255), unique=True, nullable=False),
        sa.Column("expires", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("identifier", "token"),
    )


def downgrade() -> None:
    op.drop_table("auth_verification_tokens")
    op.drop_table("auth_sessions")
    op.drop_table("auth_accounts")
    op.drop_index("ix_auth_users_email")
    op.drop_table("auth_users")

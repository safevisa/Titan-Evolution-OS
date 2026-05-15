"""Capability usage rollup per tenant per month.

Revision ID: 008_cap_usage
Revises: 007_cap_audit
Create Date: 2026-05-15
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "008_cap_usage"
down_revision: Union[str, None] = "007_cap_audit"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "capability_usage_rollup",
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("period_year", sa.Integer(), nullable=False),
        sa.Column("period_month", sa.Integer(), nullable=False),
        sa.Column("capability_ref", sa.String(length=180), nullable=False),
        sa.Column("invocation_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("estimated_cost_usd", sa.Numeric(12, 6), nullable=False, server_default="0"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint(
            "tenant_id", "period_year", "period_month", "capability_ref",
            name="pk_capability_usage_rollup",
        ),
    )


def downgrade() -> None:
    op.drop_table("capability_usage_rollup")

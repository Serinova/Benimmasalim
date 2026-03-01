"""Add billing fields for invoice support.

Revision ID: 099_billing_fields
Revises: 098_perf_indexes
Create Date: 2026-02-28
"""
from alembic import op
import sqlalchemy as sa

revision = "099_billing_fields"
down_revision = "098_perf_indexes"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("orders", sa.Column("billing_tax_office", sa.String(100), nullable=True))
    op.add_column("orders", sa.Column("billing_full_name", sa.String(200), nullable=True))
    op.add_column("orders", sa.Column("billing_email", sa.String(200), nullable=True))
    op.add_column("orders", sa.Column("billing_phone", sa.String(20), nullable=True))
    op.add_column(
        "orders",
        sa.Column("billing_address", sa.dialects.postgresql.JSONB(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("orders", "billing_address")
    op.drop_column("orders", "billing_phone")
    op.drop_column("orders", "billing_email")
    op.drop_column("orders", "billing_full_name")
    op.drop_column("orders", "billing_tax_office")

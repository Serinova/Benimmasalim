"""Add billing_tc_no column to orders table for individual invoices.

Bireysel (individual) faturalar için TC kimlik numarası alanı.

Revision ID: 111_add_billing_tc_no
Revises: 110_inner_yatay_caption
Create Date: 2026-03-01
"""

from alembic import op
import sqlalchemy as sa

revision = "111_add_billing_tc_no"
down_revision = "110_inner_yatay_caption"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "orders",
        sa.Column("billing_tc_no", sa.String(11), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("orders", "billing_tc_no")

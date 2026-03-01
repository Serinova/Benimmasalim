"""Add invoices table and invoice_serial sequence.

Revision ID: 100_invoice_table
Revises: 099_billing_fields
Create Date: 2026-02-28
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = "100_invoice_table"
down_revision = "099_billing_fields"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "invoices",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("order_id", UUID(as_uuid=True), sa.ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("invoice_number", sa.String(20), nullable=False, unique=True),
        sa.Column("invoice_status", sa.String(20), nullable=False, server_default="PENDING"),
        sa.Column("issued_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("pdf_url", sa.Text(), nullable=True),
        sa.Column("pdf_generated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("pdf_version", sa.Integer(), server_default="1", nullable=False),
        sa.Column("pdf_hash", sa.String(64), nullable=True),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("retry_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("needs_credit_note", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("idx_invoice_order", "invoices", ["order_id"], unique=True)
    op.create_index("idx_invoice_status", "invoices", ["invoice_status"])

    # Yearly sequence for invoice numbering (start from current year)
    op.execute("CREATE SEQUENCE IF NOT EXISTS invoice_serial_2026 START 1")


def downgrade() -> None:
    op.execute("DROP SEQUENCE IF EXISTS invoice_serial_2026")
    op.drop_index("idx_invoice_status", table_name="invoices")
    op.drop_index("idx_invoice_order", table_name="invoices")
    op.drop_table("invoices")

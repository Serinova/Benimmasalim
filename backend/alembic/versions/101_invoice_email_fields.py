"""Add email tracking fields to invoices table.

Revision ID: 101_invoice_email_fields
Revises: 100_invoice_table
Create Date: 2026-02-28
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = "101_invoice_email_fields"
down_revision = "100_invoice_table"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("invoices", sa.Column("email_sent_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("invoices", sa.Column("email_status", sa.String(20), nullable=True))
    op.add_column("invoices", sa.Column("email_error", sa.Text(), nullable=True))
    op.add_column("invoices", sa.Column("email_retry_count", sa.Integer(), server_default="0", nullable=False))
    op.add_column("invoices", sa.Column("email_resent_count", sa.Integer(), server_default="0", nullable=False))
    op.add_column("invoices", sa.Column("email_last_resent_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("invoices", sa.Column("email_resent_by_admin_id", UUID(as_uuid=True), nullable=True))


def downgrade() -> None:
    op.drop_column("invoices", "email_resent_by_admin_id")
    op.drop_column("invoices", "email_last_resent_at")
    op.drop_column("invoices", "email_resent_count")
    op.drop_column("invoices", "email_retry_count")
    op.drop_column("invoices", "email_error")
    op.drop_column("invoices", "email_status")
    op.drop_column("invoices", "email_sent_at")

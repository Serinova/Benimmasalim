"""Add invoice_download_tokens table for secure guest PDF access.

Revision ID: 102_invoice_download_tokens
Revises: 101_invoice_email_fields
Create Date: 2026-02-28
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = "102_invoice_download_tokens"
down_revision = "101_invoice_email_fields"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "invoice_download_tokens",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("token_hash", sa.String(64), nullable=False, unique=True),
        sa.Column("order_id", UUID(as_uuid=True), sa.ForeignKey("orders.id", ondelete="CASCADE"), nullable=False),
        sa.Column("invoice_id", UUID(as_uuid=True), sa.ForeignKey("invoices.id", ondelete="CASCADE"), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("max_uses", sa.Integer(), server_default="1", nullable=False),
        sa.Column("used_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("first_used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_by_admin_id", UUID(as_uuid=True), nullable=True),
        sa.Column("created_by", sa.String(20), server_default="system", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("idx_dl_token_hash", "invoice_download_tokens", ["token_hash"], unique=True)
    op.create_index("idx_dl_token_order", "invoice_download_tokens", ["order_id"])
    op.create_index("idx_dl_token_expires", "invoice_download_tokens", ["expires_at"])


def downgrade() -> None:
    op.drop_index("idx_dl_token_expires")
    op.drop_index("idx_dl_token_order")
    op.drop_index("idx_dl_token_hash")
    op.drop_table("invoice_download_tokens")

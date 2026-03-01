"""Add notification_outbox table for reliable email delivery.

Revision ID: 096_notification_outbox
Revises: 095_membership
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID


revision = "096_notification_outbox"
down_revision = "095_membership"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "notification_outbox",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("order_id", UUID(as_uuid=True),
                  sa.ForeignKey("orders.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="SET NULL")),
        sa.Column("channel", sa.String(20), server_default="email"),
        sa.Column("event_type", sa.String(50), nullable=False),
        sa.Column("order_status", sa.String(30), nullable=False),
        sa.Column("payload", JSONB),
        sa.Column("status", sa.String(20), server_default="PENDING", nullable=False),
        sa.Column("retry_count", sa.Integer, server_default="0"),
        sa.Column("max_retries", sa.Integer, server_default="3"),
        sa.Column("next_retry_at", sa.DateTime(timezone=True)),
        sa.Column("last_error", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("sent_at", sa.DateTime(timezone=True)),
        sa.UniqueConstraint("order_id", "order_status", "channel",
                            name="uq_outbox_order_status_channel"),
    )
    op.create_index(
        "idx_outbox_pending", "notification_outbox",
        ["status", "next_retry_at"],
        postgresql_where="status IN ('PENDING', 'FAILED')",
    )
    op.create_index("idx_outbox_order", "notification_outbox", ["order_id"])


def downgrade() -> None:
    op.drop_index("idx_outbox_order", table_name="notification_outbox")
    op.drop_index("idx_outbox_pending", table_name="notification_outbox")
    op.drop_table("notification_outbox")

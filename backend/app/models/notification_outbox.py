"""Notification outbox model — transactional outbox pattern for reliable email delivery.

Guarantees:
- Every status-change email is persisted in the same DB transaction as the audit log.
- A background worker polls PENDING/FAILED rows and sends them.
- Unique constraint (order_id, status, channel) prevents duplicate sends.
"""

import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class OutboxStatus(str, Enum):
    PENDING = "PENDING"
    SENT = "SENT"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"


class NotificationOutbox(Base):
    """Transactional outbox for order status email notifications."""

    __tablename__ = "notification_outbox"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("orders.id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
    )

    channel: Mapped[str] = mapped_column(String(20), default="email")
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    order_status: Mapped[str] = mapped_column(String(30), nullable=False)

    payload: Mapped[dict | None] = mapped_column(JSONB)

    status: Mapped[str] = mapped_column(
        String(20), default=OutboxStatus.PENDING.value, nullable=False,
    )
    retry_count: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    max_retries: Mapped[int] = mapped_column(Integer, default=3, server_default="3")
    next_retry_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_error: Mapped[str | None] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False,
    )
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    __table_args__ = (
        UniqueConstraint("order_id", "order_status", "channel", name="uq_outbox_order_status_channel"),
        Index("idx_outbox_pending", "status", "next_retry_at",
              postgresql_where="status IN ('PENDING', 'FAILED')"),
        Index("idx_outbox_order", "order_id"),
    )

    def __repr__(self) -> str:
        return f"<NotificationOutbox order={self.order_id} status={self.order_status} state={self.status}>"

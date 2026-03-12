"""Invoice model — one invoice per paid order.

Lifecycle:
  PENDING → ISSUED → PDF_READY
  PENDING → FAILED (retry up to 3 times)
  PDF_READY → CANCELLED (on order cancel/refund)

Idempotency: unique(order_id) ensures at most one invoice per order.
"""

import uuid
from datetime import datetime
from enum import StrEnum

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin


class InvoiceStatus(StrEnum):
    PENDING = "PENDING"
    ISSUED = "ISSUED"
    PDF_READY = "PDF_READY"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class Invoice(Base, UUIDMixin, TimestampMixin):
    """One-to-one invoice record for a paid order or trial preview."""

    __tablename__ = "invoices"

    # Legacy Order-flow: FK to orders.id (nullable — trial invoices have no Order row)
    order_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("orders.id", ondelete="CASCADE"),
        nullable=True,
        unique=True,
    )

    # Trial / "Try Before You Buy" flow: FK to story_previews.id
    story_preview_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("story_previews.id", ondelete="CASCADE"),
        nullable=True,
        unique=True,
    )

    invoice_number: Mapped[str] = mapped_column(
        String(20), nullable=False, unique=True,
    )
    invoice_status: Mapped[str] = mapped_column(
        String(20), default=InvoiceStatus.PENDING.value, nullable=False,
    )

    issued_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False,
    )
    pdf_url: Mapped[str | None] = mapped_column(Text)
    pdf_generated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    pdf_version: Mapped[int] = mapped_column(Integer, default=1, server_default="1")
    pdf_hash: Mapped[str | None] = mapped_column(String(64))

    last_error: Mapped[str | None] = mapped_column(Text)
    retry_count: Mapped[int] = mapped_column(Integer, default=0, server_default="0")

    needs_credit_note: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="false",
    )
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Email delivery tracking
    email_sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    email_status: Mapped[str | None] = mapped_column(
        String(20),  # PENDING / SENT / FAILED / SKIPPED
    )
    email_error: Mapped[str | None] = mapped_column(Text)
    email_retry_count: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    email_resent_count: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    email_last_resent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    email_resent_by_admin_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))

    order = relationship("Order", foreign_keys=[order_id], lazy="selectin")
    story_preview = relationship("StoryPreview", foreign_keys=[story_preview_id], lazy="selectin")

    __table_args__ = (
        Index("idx_invoice_order", "order_id", unique=True),
        Index("idx_invoice_story_preview", "story_preview_id", unique=True),
        Index("idx_invoice_status", "invoice_status"),
    )

    def __repr__(self) -> str:
        return f"<Invoice {self.invoice_number} order={self.order_id} status={self.invoice_status}>"

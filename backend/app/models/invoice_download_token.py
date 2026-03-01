"""Secure, single-use download token for guest invoice PDF access.

Design:
- Token is 32 random bytes (256-bit), URL-safe base64 encoded.
- DB stores sha256(token + INVOICE_TOKEN_SALT), never plaintext.
- Lookup by token_hash; verify with atomic SELECT FOR UPDATE.
- max_uses (default 1) enforces single-use; used_count tracks consumption.
- expires_at enforces TTL (default 48h).
- revoked_at allows admin revocation.
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDMixin


class InvoiceDownloadToken(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "invoice_download_tokens"

    token_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)

    # For legacy Order-flow. Nullable: trial-flow invoices have no Order row (used for logging only).
    order_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("orders.id", ondelete="CASCADE"),
        nullable=True,
    )
    invoice_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("invoices.id", ondelete="CASCADE"),
        nullable=False,
    )

    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    max_uses: Mapped[int] = mapped_column(Integer, default=1, server_default="1")
    used_count: Mapped[int] = mapped_column(Integer, default=0, server_default="0")

    first_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    revoked_by_admin_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))

    created_by: Mapped[str] = mapped_column(
        String(20), default="system", server_default="system",
    )

    __table_args__ = (
        Index("idx_dl_token_hash", "token_hash", unique=True),
        Index("idx_dl_token_order", "order_id"),
        Index("idx_dl_token_expires", "expires_at"),
    )

    def __repr__(self) -> str:
        return f"<InvoiceDownloadToken hash={self.token_hash[:8]}... order={self.order_id}>"

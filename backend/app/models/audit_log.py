"""Audit log model - Track all important actions."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import INET, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base

_FK_ON_DELETE = "SET NULL"


class AuditLog(Base):
    """
    Audit log for tracking all important actions.

    Actions:
    - LOGIN_SUCCESS, LOGIN_FAILED, LOGOUT, USER_REGISTERED
    - ORDER_STATUS_{X}, PAYMENT_CALLBACK_RECEIVED
    - PROMO_CODE_CREATED/CONSUMED/ROLLED_BACK/UPDATED/DEACTIVATED
    - KVKK_PHOTO_DELETED, USER_DATA_EXPORTED, USER_DATA_DELETED
    - DATA_REQUEST_SUBMITTED
    - ADMIN_POST/PUT/PATCH/DELETE (generic admin mutations)
    - AUDIT_LOG_RETENTION_CLEANUP
    """

    __tablename__ = "audit_logs"

    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Action info
    action: Mapped[str] = mapped_column(String(100), nullable=False)

    # Related entities (nullable for flexibility)
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete=_FK_ON_DELETE),
    )
    order_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("orders.id", ondelete=_FK_ON_DELETE),
    )
    admin_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete=_FK_ON_DELETE),
    )

    # Additional details (JSON)
    details: Mapped[dict | None] = mapped_column(JSONB)

    # Request info
    ip_address: Mapped[str | None] = mapped_column(INET)
    user_agent: Mapped[str | None] = mapped_column(Text)

    # Timestamp
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    __table_args__ = (
        Index("idx_logs_action", "action", "created_at"),
        Index("idx_logs_order", "order_id", postgresql_where="order_id IS NOT NULL"),
        Index("idx_logs_created", "created_at"),
        Index("idx_logs_user", "user_id", postgresql_where="user_id IS NOT NULL"),
        Index("idx_logs_admin", "admin_id", postgresql_where="admin_id IS NOT NULL"),
    )

    def __repr__(self) -> str:
        return f"<AuditLog {self.action} @ {self.created_at}>"

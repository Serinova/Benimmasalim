"""Consent record model — KVKK compliance.

Tracks when users give/withdraw consent for specific data processing purposes.
Each consent action (given, withdrawn) creates a new immutable record.
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Index, String, func
from sqlalchemy.dialects.postgresql import INET, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class ConsentRecord(Base):
    """Immutable consent record — one row per consent action.

    ConsentType examples:
      - PHOTO_PROCESSING: Child photo AI processing + 30-day deletion
      - KVKK_DISCLOSURE: KVKK aydınlatma metni kabul
      - MARKETING: Marketing communications (optional)
    """

    __tablename__ = "consent_records"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    # Who gave consent (email used as identifier for anonymous/lead users)
    user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), index=True)
    email: Mapped[str | None] = mapped_column(String(255))

    # What was consented to
    consent_type: Mapped[str] = mapped_column(String(50), nullable=False)

    # Action: "given" or "withdrawn"
    action: Mapped[str] = mapped_column(String(20), nullable=False)

    # Version of the consent text at the time of action
    consent_version: Mapped[str] = mapped_column(String(20), nullable=False, default="1.0")

    # Context: which page/component triggered the consent
    source: Mapped[str | None] = mapped_column(String(100))

    # IP address for audit trail
    ip_address: Mapped[str | None] = mapped_column(INET)

    # Additional metadata
    metadata_json: Mapped[dict | None] = mapped_column(JSONB)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    __table_args__ = (
        Index("idx_consent_user", "user_id", postgresql_where="user_id IS NOT NULL"),
        Index("idx_consent_email", "email", postgresql_where="email IS NOT NULL"),
        Index("idx_consent_type_action", "consent_type", "action", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<ConsentRecord {self.consent_type} {self.action} @ {self.created_at}>"

"""Child profile model — reusable child info across orders."""

import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin


class ChildProfile(Base, UUIDMixin, TimestampMixin):
    """Saved child profile for quick re-ordering (max 10 per user, app-level)."""

    __tablename__ = "child_profiles"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    age: Mapped[int] = mapped_column(Integer, nullable=False)
    gender: Mapped[str | None] = mapped_column(String(10))
    photo_url: Mapped[str | None] = mapped_column(Text)
    photo_uploaded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    user = relationship("User", back_populates="children")

    __table_args__ = (
        CheckConstraint("age >= 1 AND age <= 18", name="valid_child_profile_age"),
        Index("idx_child_profiles_user", "user_id"),
    )

    def __repr__(self) -> str:
        return f"<ChildProfile {self.name} age={self.age}>"

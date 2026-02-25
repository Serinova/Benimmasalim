"""User model - supports email, Google OAuth, and guest checkout."""

from enum import Enum

from sqlalchemy import Boolean, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin


class UserRole(str, Enum):
    """User roles for authorization."""

    USER = "user"
    EDITOR = "editor"
    ADMIN = "admin"


class User(Base, UUIDMixin, TimestampMixin):
    """User model supporting multiple auth methods."""

    __tablename__ = "users"

    # Basic info
    email: Mapped[str | None] = mapped_column(String(255), unique=True, index=True)
    hashed_password: Mapped[str | None] = mapped_column(String(255))
    full_name: Mapped[str | None] = mapped_column(String(255))
    phone: Mapped[str | None] = mapped_column(String(20))

    # OAuth (Google)
    google_id: Mapped[str | None] = mapped_column(String(255), unique=True)
    avatar_url: Mapped[str | None] = mapped_column(Text)

    # Guest checkout support
    is_guest: Mapped[bool] = mapped_column(Boolean, default=False)

    # Role & status
    role: Mapped[UserRole] = mapped_column(
        String(20),
        default=UserRole.USER,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Relationships
    orders = relationship("Order", back_populates="user", lazy="selectin")

    __table_args__ = (
        Index("idx_users_email", "email", postgresql_where="email IS NOT NULL"),
        Index("idx_users_google", "google_id", postgresql_where="google_id IS NOT NULL"),
    )

    def __repr__(self) -> str:
        return f"<User {self.email or self.id}>"

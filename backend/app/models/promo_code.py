"""PromoCode model - Coupon/discount code management."""

import uuid
from datetime import datetime
from decimal import Decimal
from enum import Enum

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDMixin


class DiscountType(str, Enum):
    """Discount type for promo codes."""

    PERCENT = "PERCENT"
    AMOUNT = "AMOUNT"


class PromoCode(Base, UUIDMixin, TimestampMixin):
    """
    Promo code / coupon for order discounts.

    Supports percentage or fixed-amount discounts with usage limits,
    validity dates, minimum order amounts, and maximum discount caps.
    """

    __tablename__ = "promo_codes"

    # Code (unique, uppercase, trimmed)
    code: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False, index=True
    )

    # Discount configuration
    discount_type: Mapped[str] = mapped_column(
        String(20), nullable=False
    )
    discount_value: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), nullable=False
    )

    # Usage limits
    usage_limit: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    used_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Active flag
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # Validity period (optional)
    valid_from: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    valid_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Constraints
    min_order_amount: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))
    max_discount_amount: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))

    # Admin notes
    notes: Mapped[str | None] = mapped_column(Text)

    # Created by (admin user)
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
    )

    __table_args__ = (
        CheckConstraint("used_count >= 0", name="promo_used_count_non_negative"),
        CheckConstraint("usage_limit >= 1", name="promo_usage_limit_positive"),
        CheckConstraint("discount_value > 0", name="promo_discount_value_positive"),
        CheckConstraint(
            "discount_type IN ('PERCENT', 'AMOUNT')",
            name="promo_valid_discount_type",
        ),
        CheckConstraint(
            "(discount_type != 'PERCENT') OR (discount_value >= 1 AND discount_value <= 100)",
            name="promo_percent_range",
        ),
        Index("idx_promo_codes_active", "is_active", "valid_until"),
        Index("idx_promo_codes_code", "code"),
    )

    def __repr__(self) -> str:
        return f"<PromoCode {self.code} ({self.discount_type} {self.discount_value})>"

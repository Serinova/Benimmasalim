"""BookCost model — per-book cost tracking for accounting.

Each record represents a cost line-item (e.g. printing, paper, shipping).
Costs can be per-unit (multiplied by order count) or fixed (one-time).
Optionally linked to a specific product; otherwise applies globally.
"""

import uuid
from decimal import Decimal
from enum import StrEnum

from sqlalchemy import Boolean, ForeignKey, Index, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDMixin


class CostCategory(StrEnum):
    """Cost category enum for book production costs."""

    PRINTING = "printing"
    PAPER = "paper"
    BINDING = "binding"
    SHIPPING = "shipping"
    PACKAGING = "packaging"
    AI_GENERATION = "ai_generation"
    PLATFORM_FEE = "platform_fee"
    OTHER = "other"


class BookCost(Base, UUIDMixin, TimestampMixin):
    """
    Book production cost record.

    Each row is a cost line-item that contributes to the total cost
    of producing and delivering a book.

    - is_per_unit=True  → amount is per order (multiplied by order count)
    - is_per_unit=False → fixed cost (e.g. monthly hosting, SaaS fee)
    - product_id=None   → applies to ALL products
    - product_id=<uuid> → only applies to that specific product
    """

    __tablename__ = "book_costs"

    category: Mapped[str] = mapped_column(
        String(50), nullable=False, comment="Maliyet kategorisi"
    )
    description: Mapped[str] = mapped_column(
        String(500), nullable=False, comment="Açıklama"
    )
    amount: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), nullable=False, comment="Tutar (TL)"
    )
    is_per_unit: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False,
        comment="Birim başına mı (sipariş × tutar) yoksa sabit maliyet mi",
    )
    product_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("products.id", ondelete="SET NULL"),
        nullable=True,
        comment="Belirli ürüne ait ise ürün ID, NULL = tüm ürünler",
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False,
        comment="Aktif mi (pasif maliyetler hesaplamaya dahil edilmez)",
    )
    notes: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="Ek notlar"
    )

    __table_args__ = (
        Index("idx_book_costs_active", "is_active", "category"),
        Index(
            "idx_book_costs_product",
            "product_id",
            postgresql_where="product_id IS NOT NULL",
        ),
    )

    def __repr__(self) -> str:
        return f"<BookCost {self.category}: {self.amount} TL>"

"""Coloring Book Product model."""

import uuid
from decimal import Decimal

from sqlalchemy import Boolean, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDMixin


class ColoringBookProduct(Base, UUIDMixin, TimestampMixin):
    """
    Boyama kitabı ürün ayarları.
    
    Fiyatlandırma ve line-art conversion parametrelerini tutar.
    Admin panelden düzenlenebilir.
    """

    __tablename__ = "coloring_book_products"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)

    # Pricing
    base_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    discounted_price: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))

    # Line-art conversion settings
    line_art_method: Mapped[str] = mapped_column(String(50), default="canny")
    edge_threshold_low: Mapped[int] = mapped_column(Integer, default=50)
    edge_threshold_high: Mapped[int] = mapped_column(Integer, default=150)

    # Page template reference (optional)
    page_template_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("page_templates.id", ondelete="SET NULL")
    )

    active: Mapped[bool] = mapped_column(Boolean, default=True)

"""Order page model - Individual pages of a book."""

import uuid
from enum import Enum

from sqlalchemy import Boolean, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class PageStatus(str, Enum):
    """Page generation status."""

    PENDING = "PENDING"  # Henüz işlenmedi
    PREVIEW_GENERATED = "PREVIEW_GENERATED"  # Önizleme görseli oluşturuldu (ödeme öncesi)
    FULL_GENERATED = "FULL_GENERATED"  # Tam kalite görsel oluşturuldu (ödeme sonrası)
    FAILED = "FAILED"  # Görsel oluşturulamadı


class OrderPage(Base, TimestampMixin):
    """
    Individual pages of an order/book.

    Stores text content, visual prompt (for AI image generation), and generated image URL.

    Page Flow:
    1. Text + visual_prompt created by Gemini (PENDING)
    2. Preview images generated for Cover + Page 1-2 (PREVIEW_GENERATED)
    3. After payment, full quality images generated (FULL_GENERATED)
    """

    __tablename__ = "order_pages"

    # Primary key (serial for simplicity)
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Order relationship
    order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("orders.id", ondelete="CASCADE"),
        nullable=False,
    )
    page_number: Mapped[int] = mapped_column(Integer, nullable=False)  # 0 = Cover, 1-16 = pages

    # Content from Gemini
    text_content: Mapped[str | None] = mapped_column(Text)  # Masal metni
    image_prompt: Mapped[str | None] = mapped_column(
        Text
    )  # Gemini'nin ürettiği sahne tasviri (visual prompt)

    # Generated image (Fal.ai/InstantID output)
    image_url: Mapped[str | None] = mapped_column(Text)  # GCS URL
    preview_image_url: Mapped[str | None] = mapped_column(Text)  # Düşük kalite önizleme (watermark)

    # Generation status
    status: Mapped[PageStatus] = mapped_column(
        String(30),
        default=PageStatus.PENDING,
        nullable=False,
    )

    # Metadata
    is_cover: Mapped[bool] = mapped_column(Boolean, default=False)
    is_back_cover: Mapped[bool] = mapped_column(Boolean, default=False)
    is_regenerated: Mapped[bool] = mapped_column(Boolean, default=False)
    generation_attempt: Mapped[int] = mapped_column(Integer, default=1)

    # V3: when True, image_prompt is final; do not re-compose (skip_compose=True)
    v3_composed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    negative_prompt: Mapped[str | None] = mapped_column(Text, nullable=True)
    pipeline_version: Mapped[str] = mapped_column(String(10), default="v3", nullable=False)

    # Relationship
    order = relationship("Order", back_populates="pages")

    __table_args__ = (
        UniqueConstraint("order_id", "page_number", name="unique_page_per_order"),
        Index("idx_pages_order", "order_id"),
        Index(
            "idx_pages_status",
            "status",
            postgresql_where="status != 'FULL_GENERATED'",
        ),
    )

    def __repr__(self) -> str:
        return f"<OrderPage {self.order_id} page {self.page_number} ({self.status})>"

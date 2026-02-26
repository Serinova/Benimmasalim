"""Product model - Dynamic product engine for different book formats.

Products are PHYSICAL ITEMS being sold (e.g., "A4 Hardcover", "A5 Softcover").
This is where marketing, pricing, urgency, and social proof belong.

PRODUCT TYPES:
- story_book: Traditional story books with scenarios
- coloring_book: Coloring books generated from story images
- audio_addon: Audio book feature addon (system or cloned voice)
"""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from uuid import UUID as PyUUID

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin


class ProductType(str, Enum):
    """Product type enum for different product categories."""

    STORY_BOOK = "story_book"
    COLORING_BOOK = "coloring_book"
    AUDIO_ADDON = "audio_addon"


class Product(Base, UUIDMixin, TimestampMixin):
    """
    Dynamic product model for different book formats.

    Links to PageTemplates for cover, inner pages, and back cover.
    CRITICAL: Never hard-code pixel values! Always calculate from mm dimensions.

    Also includes MARKETING fields (promo, ratings, features) to drive conversions.
    """

    __tablename__ = "products"

    # ============ BASIC INFO ============
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    slug: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    short_description: Mapped[str | None] = mapped_column(String(500))

    # Product type: story_book, coloring_book, audio_addon
    product_type: Mapped[str] = mapped_column(
        String(50),
        default=ProductType.STORY_BOOK.value,
        nullable=False,
        comment="Product type: story_book, coloring_book, audio_addon",
    )

    # Type-specific metadata (JSONB for flexibility)
    # For coloring_book: {"line_art_method": "canny", "edge_threshold_low": 50, ...}
    # For audio_addon: {"audio_type": "system" | "cloned", ...}
    type_specific_data: Mapped[dict | None] = mapped_column(
        JSONB, nullable=True, comment="Type-specific product data"
    )

    # ============ PAGE TEMPLATE REFERENCES ============
    cover_template_id: Mapped[PyUUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("page_templates.id", ondelete="SET NULL"), nullable=True
    )
    inner_template_id: Mapped[PyUUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("page_templates.id", ondelete="SET NULL"), nullable=True
    )
    back_template_id: Mapped[PyUUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("page_templates.id", ondelete="SET NULL"), nullable=True
    )

    # AI Generation Config Reference
    ai_config_id: Mapped[PyUUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("ai_generation_configs.id", ondelete="SET NULL"),
        nullable=True,
    )

    # ============ PAGE SETTINGS ============
    default_page_count: Mapped[int] = mapped_column(Integer, default=16)
    min_page_count: Mapped[int] = mapped_column(Integer, default=12)
    max_page_count: Mapped[int] = mapped_column(Integer, default=32)

    # ============ PAPER PROPERTIES ============
    paper_type: Mapped[str] = mapped_column(String(100), default="Kuşe 170gr")
    paper_finish: Mapped[str] = mapped_column(String(50), default="Mat")

    # ============ COVER PROPERTIES ============
    cover_type: Mapped[str] = mapped_column(String(50), default="Sert Kapak")
    lamination: Mapped[str | None] = mapped_column(String(50))

    # ============ PRICING ============
    base_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    discounted_price: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 2), nullable=True, comment="Sale price if active promo"
    )
    extra_page_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=5.0)
    production_cost: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))

    # AI & print settings
    print_specifications: Mapped[dict | None] = mapped_column(JSONB)

    # ============ VISIBILITY & STOCK ============
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_featured: Mapped[bool] = mapped_column(Boolean, default=False)
    display_order: Mapped[int] = mapped_column(Integer, default=0)
    stock_status: Mapped[str] = mapped_column(String(20), default="available")

    # ============ MEDIA ASSETS ============
    thumbnail_url: Mapped[str | None] = mapped_column(Text)
    gallery_images: Mapped[list | None] = mapped_column(JSONB)
    video_url: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="Product promo/demo video (YouTube/Vimeo)"
    )

    # Flipbook Preview Assets
    sample_images: Mapped[list | None] = mapped_column(
        JSONB,
        default=list,
        comment="Sample page images for flipbook preview [cover, page1, page2, ...]",
    )
    orientation: Mapped[str] = mapped_column(
        String(20), default="landscape", comment="Book orientation: portrait or landscape"
    )

    # ============ MARKETING & URGENCY ============
    # Promo badge text (e.g., "%20 İndirim", "En Çok Satan", "Yeni!")
    promo_badge: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Promo end date for countdown timer
    promo_end_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Special gift packaging option
    is_gift_wrapped: Mapped[bool] = mapped_column(Boolean, default=False)

    # ============ SOCIAL PROOF ============
    # Rating score (e.g., 4.8 out of 5)
    rating: Mapped[float | None] = mapped_column(Float, nullable=True, default=0.0)

    # Number of reviews/orders
    review_count: Mapped[int] = mapped_column(Integer, default=0)

    # Social proof display text (e.g., "500+ aile bayıldı!")
    social_proof_text: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # ============ PRODUCT FEATURES ============
    # Feature bullet points for product card (e.g., ["Hediye Paketi Dahil", "16 Sayfa"])
    feature_list: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True, default=list)

    # ============ RELATIONSHIPS ============
    cover_template = relationship("PageTemplate", foreign_keys=[cover_template_id])
    inner_template = relationship("PageTemplate", foreign_keys=[inner_template_id])
    back_template = relationship("PageTemplate", foreign_keys=[back_template_id])
    ai_config = relationship("AIGenerationConfig", foreign_keys=[ai_config_id])

    __table_args__ = (
        CheckConstraint("base_price > 0", name="check_positive_price"),
        CheckConstraint(
            "default_page_count >= 4 AND default_page_count <= 64",
            name="check_page_count_range",
        ),
        Index("idx_products_active", "is_active", "display_order"),
        Index("idx_products_featured", "is_featured", postgresql_where="is_featured = true"),
        Index("idx_products_slug", "slug"),
        Index("idx_products_promo_active", "promo_end_date", "is_active"),
        Index("idx_products_type", "product_type"),
    )

    def __repr__(self) -> str:
        return f"<Product {self.name}>"

    def calculate_price(self, page_count: int) -> Decimal:
        """Calculate total price based on page count."""
        extra_pages = max(0, page_count - self.default_page_count)
        base = self.discounted_price or self.base_price
        return base + (extra_pages * self.extra_page_price)

    @property
    def has_active_promo(self) -> bool:
        """Check if product has an active promotion."""
        if not self.promo_end_date:
            return False
        return self.promo_end_date > datetime.now(self.promo_end_date.tzinfo)

    @property
    def promo_days_remaining(self) -> int | None:
        """Calculate days remaining in promotion."""
        if not self.has_active_promo or not self.promo_end_date:
            return None
        delta = self.promo_end_date - datetime.now(self.promo_end_date.tzinfo)
        return max(0, delta.days)

    @property
    def discount_percentage(self) -> int | None:
        """Calculate discount percentage if discounted_price is set."""
        if not self.discounted_price or self.discounted_price >= self.base_price:
            return None
        return int(100 - (self.discounted_price / self.base_price * 100))

"""Order model - Main order table with state machine."""

import uuid
from datetime import datetime
from decimal import Decimal
from enum import StrEnum

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
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin


class OrderStatus(StrEnum):
    """Order status state machine."""

    DRAFT = "DRAFT"
    TEXT_APPROVED = "TEXT_APPROVED"
    COVER_APPROVED = "COVER_APPROVED"
    PAYMENT_PENDING = "PAYMENT_PENDING"
    PAID = "PAID"
    PROCESSING = "PROCESSING"
    READY_FOR_PRINT = "READY_FOR_PRINT"
    SHIPPED = "SHIPPED"
    DELIVERED = "DELIVERED"
    REFUNDED = "REFUNDED"
    CANCELLED = "CANCELLED"


class Order(Base, UUIDMixin, TimestampMixin):
    """
    Main order table containing all order information.

    State Machine Flow:
    DRAFT → TEXT_APPROVED → COVER_APPROVED → PAYMENT_PENDING → PAID
                                                                ↓
    DELIVERED ← SHIPPED ← READY_FOR_PRINT ← PROCESSING ←────────┘
    """

    __tablename__ = "orders"

    # Relationships
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        index=True,
    )
    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("products.id"),
        nullable=False,
    )
    scenario_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("scenarios.id"),
        nullable=False,
    )
    visual_style_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("visual_styles.id"),
        nullable=False,
    )

    # Child information
    child_name: Mapped[str] = mapped_column(String(255), nullable=False)
    child_age: Mapped[int] = mapped_column(Integer, nullable=False)
    child_gender: Mapped[str | None] = mapped_column(String(10))

    # Selected learning outcomes (max 3)
    selected_outcomes: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=False)

    # Status (State Machine)
    status: Mapped[OrderStatus] = mapped_column(
        String(50),
        default=OrderStatus.DRAFT,
        nullable=False,
    )

    # Payment information
    payment_id: Mapped[str | None] = mapped_column(String(100), unique=True)
    payment_amount: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))
    payment_status: Mapped[str | None] = mapped_column(String(50))
    payment_provider: Mapped[str] = mapped_column(String(50), default="iyzico")

    # Shipping information
    shipping_address: Mapped[dict | None] = mapped_column(JSONB)
    tracking_number: Mapped[str | None] = mapped_column(String(100))
    carrier: Mapped[str | None] = mapped_column(String(50))

    # Photo and files (GCS links)
    child_photo_url: Mapped[str | None] = mapped_column(Text)  # 30 day retention
    face_embedding: Mapped[list[float] | None] = mapped_column(
        ARRAY(Numeric)
    )  # pgvector alternative
    # Forensic face description for AI image generation (cached from FaceAnalyzerService)
    face_description: Mapped[str | None] = mapped_column(Text)
    final_pdf_url: Mapped[str | None] = mapped_column(Text)

    # Cover images
    back_cover_image_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Reserved for future full-spread (front+spine+back) single image
    cover_spread_image_url: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Audio book (optional)
    has_audio_book: Mapped[bool] = mapped_column(Boolean, default=False)
    audio_type: Mapped[str | None] = mapped_column(String(20))  # "system" or "cloned"
    audio_voice_id: Mapped[str | None] = mapped_column(String(100))
    audio_file_url: Mapped[str | None] = mapped_column(Text)
    qr_code_url: Mapped[str | None] = mapped_column(Text)

    # Regenerate limits
    cover_regenerate_count: Mapped[int] = mapped_column(Integer, default=0)
    max_cover_regenerate: Mapped[int] = mapped_column(Integer, default=3)

    # Progress tracking (for long-running generation tasks)
    completed_pages: Mapped[int] = mapped_column(Integer, default=0)
    total_pages: Mapped[int] = mapped_column(Integer, default=16)
    generation_started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    generation_error: Mapped[str | None] = mapped_column(Text)  # Last error message if failed

    # Promo code snapshot (audit trail)
    promo_code_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("promo_codes.id", ondelete="SET NULL"),
    )
    promo_code_text: Mapped[str | None] = mapped_column(String(50))
    promo_discount_type: Mapped[str | None] = mapped_column(String(20))
    promo_discount_value: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))
    discount_applied_amount: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))
    subtotal_amount: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))
    final_amount: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))

    # Dedication page note (custom message from parent)
    dedication_note: Mapped[str | None] = mapped_column(Text)

    # Coloring book relationship
    coloring_book_order_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("orders.id", ondelete="SET NULL"),
        nullable=True,
    )
    is_coloring_book: Mapped[bool] = mapped_column(Boolean, default=False)

    # V3: Magic items selected by user (e.g. ["sihirli pusula", "parlayan taş"])
    magic_items: Mapped[list | None] = mapped_column(
        JSONB, nullable=True, default=None, comment="V3: User-selected magic items"
    )
    # V3: Blueprint JSON from PASS-0 for debugging/audit
    blueprint_json: Mapped[dict | None] = mapped_column(
        JSONB, nullable=True, default=None, comment="V3: PASS-0 blueprint for audit"
    )

    # Child profile link (reusable child info)
    child_profile_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("child_profiles.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Billing / invoice
    billing_type: Mapped[str | None] = mapped_column(String(20))  # "individual" | "corporate"
    billing_tax_id: Mapped[str | None] = mapped_column(String(20))
    billing_company_name: Mapped[str | None] = mapped_column(String(200))
    billing_tax_office: Mapped[str | None] = mapped_column(String(100))
    billing_tc_no: Mapped[str | None] = mapped_column(String(11))  # TCKN — bireysel fatura
    billing_full_name: Mapped[str | None] = mapped_column(String(200))
    billing_email: Mapped[str | None] = mapped_column(String(200))
    billing_phone: Mapped[str | None] = mapped_column(String(20))
    billing_address: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Refund tracking
    refund_requested_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    refund_reason: Mapped[str | None] = mapped_column(Text)

    # KVKK (Auto deletion)
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    photo_deletion_scheduled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Relationships
    # user + child_profile: single-row FK — selectin is cheap and convenient
    # pages + coloring_book_order: potentially large / rarely needed in list views
    #   → lazy="select" (explicit selectinload() where needed to avoid N+1)
    user = relationship("User", back_populates="orders", lazy="selectin")
    child_profile = relationship("ChildProfile", foreign_keys=[child_profile_id], lazy="selectin")
    pages = relationship("OrderPage", back_populates="order", cascade="all, delete-orphan", lazy="select")
    coloring_book_order = relationship(
        "Order",
        foreign_keys=[coloring_book_order_id],
        remote_side="Order.id",
        uselist=False,
        lazy="select",
    )

    __table_args__ = (
        CheckConstraint(
            "status IN ('DRAFT', 'TEXT_APPROVED', 'COVER_APPROVED', 'PAYMENT_PENDING', "
            "'PAID', 'PROCESSING', 'READY_FOR_PRINT', 'SHIPPED', 'DELIVERED', "
            "'REFUNDED', 'CANCELLED')",
            name="valid_status",
        ),
        CheckConstraint("child_age >= 5 AND child_age <= 10", name="valid_child_age"),
        CheckConstraint(
            "array_length(selected_outcomes, 1) <= 3",
            name="max_three_outcomes",
        ),
        Index("idx_orders_status", "status"),
        Index("idx_orders_payment", "payment_id", postgresql_where="payment_id IS NOT NULL"),
        Index("idx_orders_delivered", "delivered_at", postgresql_where="delivered_at IS NOT NULL"),
        Index(
            "idx_kvkk_cleanup",
            "photo_deletion_scheduled_at",
            postgresql_where="photo_deletion_scheduled_at IS NOT NULL",
        ),
        # Performance: list pagination (WHERE user_id = ? ORDER BY created_at DESC)
        Index("idx_orders_user_created", "user_id", "created_at"),
        # Performance: filtered list (WHERE user_id = ? AND status IN (...))
        Index("idx_orders_user_status", "user_id", "status"),
    )

    def __repr__(self) -> str:
        return f"<Order {self.id} ({self.status.value})>"

"""Story Preview model - Stores pending orders before confirmation.

Implements "Try Before You Buy" flow:
1. LEAD_CAPTURED: User entered contact info
2. PREVIEW_GENERATED: Full story + 3 preview images ready
3. PAYMENT_PENDING: User wants to buy, awaiting payment
4. COMPLETED: Paid, full book generated
5. ABANDONED_TRIAL: User saw preview but didn't buy (auto-mark after 1 hour)
"""

import secrets
import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDMixin


class PreviewStatus(str, Enum):
    """Preview status - "Try Before You Buy" flow."""

    # New statuses for staged generation
    LEAD_CAPTURED = "LEAD_CAPTURED"  # User entered Name/Phone
    GENERATING = "GENERATING"  # Story generation in progress
    PREVIEW_GENERATED = "PREVIEW_GENERATED"  # Story + 3 images ready for preview
    PAYMENT_PENDING = "PAYMENT_PENDING"  # User wants to buy, awaiting payment
    COMPLETING = "COMPLETING"  # Generating remaining 13 images
    COMPLETED = "COMPLETED"  # Full book ready, payment received
    ABANDONED_TRIAL = "ABANDONED_TRIAL"  # User saw preview but didn't buy

    # Legacy statuses (kept for backward compatibility)
    PENDING = "PENDING"  # Waiting for confirmation
    CONFIRMED = "CONFIRMED"  # User confirmed, ready for production
    EXPIRED = "EXPIRED"  # Link expired (24 hours)
    CANCELLED = "CANCELLED"  # User cancelled
    PROCESSING = "PROCESSING"  # Background processing


class StoryPreview(Base, UUIDMixin, TimestampMixin):
    """
    Stores story previews before confirmation.

    Flow:
    1. User creates story, preview is sent to email
    2. Preview is saved with PENDING status
    3. Email contains confirmation link with token
    4. User clicks link -> status becomes CONFIRMED
    5. Admin sees confirmed orders in panel
    """

    __tablename__ = "story_previews"

    # Unique confirmation token (for URL)
    confirmation_token: Mapped[str] = mapped_column(
        String(64), unique=True, nullable=False, default=lambda: secrets.token_urlsafe(32)
    )

    # Status
    status: Mapped[str] = mapped_column(
        String(20), default=PreviewStatus.PENDING.value, nullable=False
    )

    # Lead user ID (CRITICAL for Concierge Support - captured at start of flow)
    lead_user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), index=True)

    # Parent info
    parent_name: Mapped[str] = mapped_column(String(255), nullable=False)
    parent_email: Mapped[str] = mapped_column(String(255), nullable=False)
    parent_phone: Mapped[str | None] = mapped_column(String(50))

    # Child info
    child_name: Mapped[str] = mapped_column(String(255), nullable=False)
    child_age: Mapped[int] = mapped_column(Integer, nullable=False)
    child_gender: Mapped[str | None] = mapped_column(String(20))
    child_photo_url: Mapped[str | None] = mapped_column(Text)  # GCS URL for PuLID face reference
    face_crop_url: Mapped[str | None] = mapped_column(Text)  # Cropped face for PuLID (better identity)
    face_embedding: Mapped[list | None] = mapped_column(JSONB)  # InsightFace 512-d embedding for quality gate
    clothing_description: Mapped[str | None] = mapped_column(String(500))  # Outfit lock for consistency

    # Product info (if selected)
    product_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    product_name: Mapped[str | None] = mapped_column(String(255))
    product_price: Mapped[float | None] = mapped_column(Numeric(10, 2))

    # Story content
    story_title: Mapped[str] = mapped_column(String(500), nullable=False)
    story_pages: Mapped[dict] = mapped_column(JSONB, nullable=False)  # Array of pages

    # Selected options
    scenario_name: Mapped[str | None] = mapped_column(String(255))
    visual_style_name: Mapped[str | None] = mapped_column(String(255))
    learning_outcomes: Mapped[list | None] = mapped_column(JSONB)  # Selected outcomes

    # Image URLs (from GCS)
    page_images: Mapped[dict | None] = mapped_column(JSONB)  # {page_num: url}

    # ============ "TRY BEFORE YOU BUY" FIELDS ============
    # Preview mode flag
    is_preview_mode: Mapped[bool] = mapped_column(Boolean, default=True)

    # CRITICAL: Cache of ALL generated prompts from Gemini (16 prompts)
    # This allows us to generate remaining images without calling Gemini again
    generated_prompts_cache: Mapped[dict | None] = mapped_column(JSONB)
    # Format: {
    #   "style_id": "uuid-of-visual-style",        # For cache invalidation
    #   "scenario_id": "uuid-of-scenario",         # For cache invalidation
    #   "outcomes_hash": "md5-of-outcomes",        # For cache invalidation
    #   "prompts": [{"page_number": 0, "text": "...", "scene_description": "...", "visual_prompt": "..."}, ...]
    # }
    # ⚠️ CACHE INVALIDATION: If style_id, scenario_id, or outcomes_hash changes, cache should be regenerated!

    # Preview images (first 3 images generated)
    preview_images: Mapped[dict | None] = mapped_column(JSONB)
    # Format: {"0": "https://...", "1": "https://...", "2": "https://..."}

    # Abandonment tracking
    preview_shown_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    abandoned_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Admin follow-up tracking
    followed_up_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    followed_up_by: Mapped[str | None] = mapped_column(String(255))
    follow_up_notes: Mapped[str | None] = mapped_column(Text)

    # Payment tracking
    payment_initiated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    payment_completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    payment_reference: Mapped[str | None] = mapped_column(String(255))

    # Audio book settings
    has_audio_book: Mapped[bool] = mapped_column(Boolean, default=False)
    audio_type: Mapped[str | None] = mapped_column(String(20))  # "system" or "cloned"
    audio_voice_id: Mapped[str | None] = mapped_column(String(100))  # ElevenLabs voice ID
    voice_sample_url: Mapped[str | None] = mapped_column(Text)  # GCS URL for voice sample
    audio_file_url: Mapped[str | None] = mapped_column(Text)  # GCS URL for generated audio file

    # Timestamps
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True)
    )  # 24 hours from creation

    # Promo code tracking
    promo_code_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("promo_codes.id", ondelete="SET NULL"),
    )
    promo_code_text: Mapped[str | None] = mapped_column(String(50))
    promo_discount_type: Mapped[str | None] = mapped_column(String(20))
    promo_discount_value: Mapped[float | None] = mapped_column(Numeric(10, 2))
    discount_applied_amount: Mapped[float | None] = mapped_column(Numeric(10, 2))

    # Dedication page note (custom message from parent)
    dedication_note: Mapped[str | None] = mapped_column(Text)

    # Admin notes
    admin_notes: Mapped[str | None] = mapped_column(Text)

    # Back cover image (AI-generated visual back cover)
    back_cover_image_url: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Debug: final prompt + negative prompt per page (when settings.debug=True)
    # Format: {"0": {"final_prompt": "...", "negative_prompt": "..."}, "1": {...}, ...}
    prompt_debug_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Generation manifest per page: proves pipeline consistency (provider, model, size, hashes)
    # Format: {"0": {"provider": "fal", "model": "...", "width": 768, "height": 1024, ...}, "1": {...}}
    generation_manifest_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Real-time generation progress (polled by frontend)
    # Format: {"current_page": 2, "total_pages": 3, "stage": "generating_images"}
    generation_progress: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Page image regeneration counter (max 3 per preview, customer-facing)
    page_regenerate_count: Mapped[int] = mapped_column(Integer, default=0, server_default="0")

    def __repr__(self) -> str:
        return f"<StoryPreview {self.id} - {self.child_name} ({self.status})>"

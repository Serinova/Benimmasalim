"""Pydantic schemas for Order API endpoints."""

from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class StoryPageData(BaseModel):
    """Story page data for email."""

    page_number: int
    text: str
    visual_prompt: str
    image_base64: str | None = None
    v3_composed: bool = False
    negative_prompt: str | None = None
    page_type: str = "inner"  # "cover" | "front_matter" | "inner"
    page_index: int = 0  # 0-based position in book
    story_page_number: int | None = None  # 1-based story page (None for cover)
    composer_version: str = "v3"
    pipeline_version: str | None = None  # MUST resolve to "v3"


class SendPreviewRequest(BaseModel):
    """Request to send story preview via email."""

    parent_name: str = Field(..., min_length=2)
    parent_email: EmailStr
    parent_phone: str | None = None
    child_name: str
    child_age: int
    child_gender: str | None = None
    story_title: str
    story_pages: list[StoryPageData]
    product_id: str | None = None
    product_name: str | None = None
    product_price: float | None = None
    scenario_name: str | None = None
    visual_style_name: str | None = None
    has_audio_book: bool = False
    audio_type: str | None = None
    audio_voice_id: str | None = None
    voice_sample_url: str | None = None


class AsyncPreviewRequest(BaseModel):
    """Request for async preview generation - returns immediately."""

    user_id: str | None = None
    parent_name: str = Field(..., min_length=2)
    parent_email: EmailStr
    parent_phone: str | None = None
    child_name: str
    child_age: int
    child_gender: str | None = None
    child_photo_url: str | None = None
    clothing_description: str | None = Field(
        default=None,
        max_length=300,
        description="Child's clothing description for consistent outfit across all pages",
    )
    story_title: str
    story_pages: list[StoryPageData]
    product_id: str | None = None
    product_name: str | None = None
    product_price: float | None = None
    scenario_name: str | None = None
    visual_style_name: str | None = None
    visual_style: str | None = None
    id_weight: float | None = None
    has_audio_book: bool = False
    audio_type: str | None = None
    audio_voice_id: str | None = None
    voice_sample_url: str | None = None
    dedication_note: str | None = Field(default=None, max_length=300)
    promo_code: str | None = Field(default=None, max_length=50)


class RegeneratePageRequest(BaseModel):
    page_number: int | str


class OrderInitRequest(BaseModel):
    """Order initialization request."""

    product_id: UUID
    scenario_id: UUID
    visual_style_id: UUID
    child_name: str = Field(..., min_length=2, max_length=100)
    child_age: int = Field(..., ge=5, le=10)
    child_gender: str | None = None


class ShippingAddressRequest(BaseModel):
    """Shipping address for order."""

    full_name: str
    phone: str
    address_line1: str
    address_line2: str | None = None
    city: str
    district: str
    postal_code: str


class ApproveTextRequest(BaseModel):
    """Approve or edit story text."""

    story_text: str | None = None


class OrderResponse(BaseModel):
    """Order response schema."""

    id: str
    status: str
    child_name: str
    child_age: int
    product_name: str
    scenario_name: str
    style_name: str
    cover_regenerate_count: int
    max_cover_regenerate: int
    story_text: str | None
    cover_url: str | None
    created_at: str

    class Config:
        from_attributes = True


class OrderInitResponse(BaseModel):
    """Order initialization response."""

    order_id: str
    status: str


class ProgressResponse(BaseModel):
    """Order generation progress response."""

    order_id: str
    status: str
    completed_pages: int
    total_pages: int
    progress_percent: int
    estimated_remaining_seconds: int | None = None
    error: str | None = None
    is_stuck: bool = False


class AddColoringBookRequest(BaseModel):
    """Request to add coloring book to existing order."""
    pass


class AddColoringBookResponse(BaseModel):
    """Response with coloring book order details."""

    coloring_order_id: str
    payment_url: str
    amount: float


class BillingUpdateRequest(BaseModel):
    billing_type: str = Field(..., pattern=r"^(individual|corporate)$")
    billing_full_name: str | None = None
    billing_email: str | None = None
    billing_phone: str | None = None
    billing_company_name: str | None = None
    billing_tax_id: str | None = None
    billing_tax_office: str | None = None
    billing_address: dict | None = None
    use_shipping_address: bool = True

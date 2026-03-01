"""Pydantic schemas for the Trial (Try Before You Buy) API."""

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.core.url_validator import validate_image_url


class StoryPageInput(BaseModel):
    """Story page from frontend."""

    page_number: int
    text: str
    visual_prompt: str
    negative_prompt: str | None = None
    v3_composed: bool | None = None
    page_type: str | None = None
    composer_version: str | None = None
    pipeline_version: str | None = None


class CreateTrialRequest(BaseModel):
    """Request to create a trial (Phase 1)."""

    # Lead info
    user_id: str | None = None
    parent_name: str = Field(..., min_length=2)
    parent_email: EmailStr
    parent_phone: str | None = None

    # Child info
    child_name: str
    child_age: int
    child_gender: str | None = None
    child_photo_url: str | None = None

    # Product info
    product_id: str | None = None
    product_name: str | None = None
    product_price: float | None = None

    # Story info
    scenario_name: str | None = None
    scenario_id: str | None = None
    visual_style: str | None = None
    visual_style_name: str | None = None
    learning_outcomes: list[str] | None = None

    # Custom variables
    custom_variables: dict | None = None

    # Explicit page count override (takes priority over product default)
    page_count: int | None = Field(default=None, ge=4, le=64)

    # V3: Magic items (sihirli malzemeler)
    magic_items: list[str] | None = None

    @field_validator("child_photo_url")
    @classmethod
    def validate_photo_url(cls, v: str | None) -> str | None:
        """Validate child photo URL to prevent SSRF."""
        return validate_image_url(v, field_name="child_photo_url")


class TrialResponse(BaseModel):
    """Response after creating/updating trial."""

    success: bool
    trial_id: str
    status: str
    message: str
    preview_url: str | None = None
    trial_token: str | None = None
    used_page_count: int | None = None
    order_id: str | None = None  # Main story order ID (if created)


class PreviewResponse(BaseModel):
    """Response with preview data."""

    success: bool
    trial_id: str
    status: str
    story_title: str
    story_pages: list[dict]
    preview_images: dict  # {page_num: url}
    child_name: str
    product_name: str | None
    product_price: float | None


class BillingData(BaseModel):
    """Billing info collected at checkout."""

    billing_type: str = "individual"  # "individual" | "corporate"
    billing_full_name: str | None = None
    billing_email: str | None = None
    billing_phone: str | None = None
    billing_company_name: str | None = None
    billing_tax_id: str | None = None
    billing_tax_office: str | None = None
    billing_address: dict | None = None
    use_shipping_address: bool = True


class CompleteTrialRequest(BaseModel):
    """Request to complete a trial after payment."""

    trial_id: str
    payment_reference: str  # "promo:{CODE}" veya iyzico ref
    parent_name: str | None = None
    parent_email: EmailStr | None = None
    parent_phone: str | None = None
    dedication_note: str | None = None
    promo_code: str | None = None
    has_audio_book: bool = False
    audio_type: str | None = None
    audio_voice_id: str | None = None
    voice_sample_url: str | None = None
    has_coloring_book: bool = False
    billing: BillingData | None = None

    @field_validator("parent_email", mode="before")
    @classmethod
    def empty_email_to_none(cls, v: object) -> object:
        if isinstance(v, str) and v.strip() == "":
            return None
        return v

    @field_validator("parent_name", "parent_phone", mode="before")
    @classmethod
    def empty_str_to_none(cls, v: object) -> object:
        if isinstance(v, str) and v.strip() == "":
            return None
        return v


class GeneratePreviewRequest(BaseModel):
    """Request to generate 3 preview images for an already-generated story."""

    # Lead info
    user_id: str | None = None
    parent_name: str = Field(..., min_length=2)
    parent_email: EmailStr
    parent_phone: str | None = None

    # Child info
    child_name: str
    child_age: int
    child_gender: str | None = None
    child_photo_url: str | None = None

    # Product info
    product_id: str | None = None
    product_name: str | None = None
    product_price: float | None = None

    # Story info (already generated)
    story_title: str
    story_pages: list[StoryPageInput]
    scenario_id: str | None = None
    scenario_name: str | None = None
    visual_style: str | None = None
    visual_style_name: str | None = None
    learning_outcomes: list[str] | None = None
    clothing_description: str | None = None
    id_weight: float | None = None

    @field_validator("child_photo_url")
    @classmethod
    def validate_photo_url(cls, v: str | None) -> str | None:
        """Validate child photo URL to prevent SSRF."""
        return validate_image_url(v, field_name="child_photo_url")


class CreatePaymentRequest(BaseModel):
    promo_code: str | None = None
    billing: BillingData | None = None


class VerifyTrialPaymentRequest(BaseModel):
    token: str = Field(..., min_length=1, max_length=500)

"""Pydantic schemas for AI service endpoints."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.services.ai.fal_ai_service import BookGenerationResult

from pydantic import BaseModel, Field, field_validator

from app.core.sanitizer import (
    detect_prompt_injection,
    sanitize_for_prompt,
    validate_child_name,
)
from app.core.url_validator import validate_image_url

# ---------------------------------------------------------------------------
# Upload constants (shared with upload endpoint)
# ---------------------------------------------------------------------------

_MAX_TEMP_IMAGE_BASE64 = 20_000_000  # ~15 MB binary
_ALLOWED_IMAGE_FORMATS = {"JPEG", "PNG", "WEBP", "GIF"}


# ---------------------------------------------------------------------------
# Story generation schemas
# ---------------------------------------------------------------------------


class TestStoryRequest(BaseModel):
    """Test story generation request."""

    child_name: str = "Ali"
    child_age: int = 7
    scenario: str = "Kapadokya Macerası"


class TestStructuredStoryRequest(BaseModel):
    """Test structured story generation with visual prompts."""

    child_name: str = Field(
        default="Ali",
        min_length=2,
        max_length=50,
        description="Child's name (2-50 characters, letters only)",
    )
    child_age: int = Field(default=7, ge=2, le=12, description="Child's age (2-12)")
    child_gender: str = "erkek"  # "erkek" | "kiz"
    child_photo_url: str | None = Field(
        default=None,
        description="URL to child's photo for AI facial analysis.",
    )
    scenario_id: str | None = None
    scenario_name: str = Field(default="Kapadokya Macerası", max_length=100, description="Scenario name")
    scenario_prompt: str = Field(
        default="Çocuk Kapadokya'da peri bacaları arasında macera yaşar",
        max_length=500,
        description="Scenario description (max 500 chars)",
    )
    learning_outcomes: list[str] = Field(
        ...,
        min_length=1,
        description="Eğitsel hedefler (zorunlu).",
    )
    visual_style: str = Field(
        default="children's book illustration, soft colors",
        max_length=2000,
        description="Visual style prompt for AI image generation",
    )
    visual_style_id: str | None = Field(
        default=None,
        description="UUID of VisualStyle row.",
    )
    page_count: int = Field(default=16, ge=1, le=64, description="Sayfa sayısı (kapak hariç)")
    clothing_description: str | None = Field(
        default=None,
        max_length=300,
        description="Child's clothing description for consistent outfit across all pages",
    )
    custom_variables: dict[str, str] | None = Field(
        default=None,
        description="User-provided values for scenario-specific custom inputs",
    )

    @field_validator("child_name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        is_valid, result = validate_child_name(v)
        if not is_valid:
            raise ValueError(result)
        return result

    @field_validator("scenario_prompt", "scenario_name")
    @classmethod
    def check_injection(cls, v: str) -> str:
        is_injection, _ = detect_prompt_injection(v)
        if is_injection:
            raise ValueError("Geçersiz içerik tespit edildi")
        return sanitize_for_prompt(v, max_length=500)

    @field_validator("visual_style")
    @classmethod
    def sanitize_style(cls, v: str) -> str:
        is_injection, _ = detect_prompt_injection(v)
        if is_injection:
            return "children's book illustration, soft colors"
        return sanitize_for_prompt(v, max_length=200)

    @field_validator("child_photo_url")
    @classmethod
    def validate_photo_url(cls, v: str | None) -> str | None:
        return validate_image_url(v, field_name="child_photo_url")

    @field_validator("custom_variables")
    @classmethod
    def sanitize_custom_vars(cls, v: dict[str, str] | None) -> dict[str, str] | None:
        if not v:
            return v
        sanitized: dict[str, str] = {}
        for key, val in v.items():
            clean_key = sanitize_for_prompt(key, max_length=50, field_name="custom_var_key")
            is_inj, _ = detect_prompt_injection(val)
            if is_inj:
                continue
            sanitized[clean_key] = sanitize_for_prompt(val, max_length=200, field_name=f"custom_var:{key}")
        return sanitized


# ---------------------------------------------------------------------------
# Image generation schemas
# ---------------------------------------------------------------------------


class TestImageRequest(BaseModel):
    """Test image generation request."""

    prompt: str = "A happy child astronaut floating in space with colorful planets"
    style: str = "cartoon, vibrant colors, children's book illustration"
    page_width_mm: float | None = None
    page_height_mm: float | None = None
    bleed_mm: float = 3.0
    product_id: str | None = None


class GenerateBookRequest(BaseModel):
    """
    Complete book generation request with Fal.ai PuLID face consistency.

    Recommended endpoint for production use.
    """

    child_name: str = Field(
        ...,
        min_length=2,
        max_length=50,
        description="Child's name for personalization (2-50 chars, letters only)",
    )
    child_age: int = Field(..., ge=2, le=12, description="Child's age (2-12)")
    child_gender: str = Field(..., description="'erkek' or 'kiz'")

    @field_validator("child_name")
    @classmethod
    def validate_book_child_name(cls, v: str) -> str:
        is_valid, result = validate_child_name(v)
        if not is_valid:
            raise ValueError(result)
        return result

    child_photo_url: str = Field(
        ..., description="URL to child's photo. CRITICAL for face consistency via PuLID."
    )
    scenario_id: str = Field(..., description="Scenario UUID from database")
    visual_style_id: str | None = Field(None, description="Visual style UUID (optional)")
    visual_style_modifier: str = Field(
        default="watercolor children's book illustration, soft colors, whimsical",
        description="Style modifier for image generation",
    )
    clothing_description: str | None = Field(
        None,
        description="What the child is wearing. If not provided, will be detected from photo.",
    )
    page_count: int = Field(
        default=10, ge=4, le=32, description="Number of story pages (excluding cover)"
    )
    ai_config_id: str | None = Field(None, description="AI config UUID for provider selection")


class GeneratedPageResponse(BaseModel):
    """Single generated page."""

    page_num: int
    text: str
    scene_description: str
    image_url: str
    is_cover: bool = False


class GenerateBookResponse(BaseModel):
    """Complete book generation response."""

    success: bool
    story_id: str
    title: str
    child_name: str
    pages: list[GeneratedPageResponse]
    cover_url: str
    clothing_description: str
    style_modifier: str
    total_pages: int
    face_consistency: str = "PuLID"
    message: str | None = None


class PageGenerationStatus(BaseModel):
    """Individual page generation status."""

    page_num: int
    status: str  # "success" | "failed" | "pending"
    url: str | None = None
    error: str | None = None
    is_cover: bool = False


class PartialSuccessResponse(BaseModel):
    """Response format for partial success scenarios."""

    success: bool
    partial_success: bool
    complete_success: bool
    total_pages: int
    success_count: int
    failed_count: int
    pages: list[PageGenerationStatus]
    successful_urls: dict[str, str]
    failed_pages: list[int]
    message: str

    @classmethod
    def from_book_result(cls, result: BookGenerationResult) -> PartialSuccessResponse:
        """Create response from BookGenerationResult."""
        pages = [
            PageGenerationStatus(
                page_num=page_num,
                status=data["status"],
                url=data.get("url"),
                error=data.get("error"),
                is_cover=data.get("is_cover", False),
            )
            for page_num, data in result.pages.items()
        ]

        if result.complete_success:
            message = f"Tüm {result.total_pages} sayfa başarıyla oluşturuldu!"
        elif result.partial_success:
            message = (
                f"{result.success_count}/{result.total_pages} sayfa başarıyla oluşturuldu. "
                f"{result.failed_count} sayfa yeniden denenebilir."
            )
        else:
            message = "Görsel oluşturma başarısız oldu. Lütfen tekrar deneyin."

        return cls(
            success=result.success_count > 0,
            partial_success=result.partial_success,
            complete_success=result.complete_success,
            total_pages=result.total_pages,
            success_count=result.success_count,
            failed_count=result.failed_count,
            pages=pages,
            successful_urls={str(k): v for k, v in result.get_successful_urls().items()},
            failed_pages=result.get_failed_pages(),
            message=message,
        )


class TestFalImageRequest(BaseModel):
    """Test Fal.ai image generation request."""

    prompt: str = "A happy child astronaut floating in space with colorful planets"
    style: str = "watercolor children's book illustration, soft colors"
    face_photo_url: str | None = Field(None, description="Child's photo URL for face consistency")
    clothing: str | None = Field(None, description="Clothing description for outfit consistency")
    id_weight: float = Field(default=0.4, ge=0.2, le=1.0, description="Face identity strength")
    width: int = 1024
    height: int = 724
    is_cover: bool = Field(default=False, description="Whether this is a cover page")
    page_number: int | None = Field(default=None, description="Page number (0=cover)")


# ---------------------------------------------------------------------------
# Temp upload schema
# ---------------------------------------------------------------------------


class TempImageUploadRequest(BaseModel):
    """Temporary image upload for Fal.ai PuLID access."""

    image_base64: str = Field(
        ..., max_length=_MAX_TEMP_IMAGE_BASE64,
        description="Base64 encoded image (with or without data: prefix, max ~15MB)",
    )


# ---------------------------------------------------------------------------
# Face analysis schemas
# ---------------------------------------------------------------------------


class TestFaceAnalysisRequest(BaseModel):
    """Test face analysis request."""

    photo_url: str = Field(..., description="URL to child's photo")
    child_name: str = "Test"
    child_age: int = 7
    child_gender: str = "erkek"


class TestMultiViewFaceAnalysisRequest(BaseModel):
    """Test multi-view face analysis request."""

    photo_urls: list[str] = Field(
        ..., description="List of photo URLs (2-5 recommended)", min_length=1, max_length=5
    )
    child_name: str = "Test"
    child_age: int = 7
    child_gender: str = "erkek"


# ---------------------------------------------------------------------------
# Audio / voice schemas
# ---------------------------------------------------------------------------


class SystemVoiceInfo(BaseModel):
    """System voice information."""

    id: str
    name: str
    gender: str
    description: str


class VoiceSampleUploadRequest(BaseModel):
    """Voice sample upload request."""

    audio_base64: str = Field(..., max_length=30_000_000, description="Base64 encoded audio (webm/mp3, max ~20MB)")
    order_id: str | None = Field(None, description="Optional order ID for association")


class VoiceSampleUploadResponse(BaseModel):
    """Voice sample upload response."""

    sample_url: str
    duration_seconds: float | None
    message: str


class CloneVoiceRequest(BaseModel):
    """Voice cloning request."""

    voice_name: str = Field(..., description="Name for the cloned voice")
    sample_url: str = Field(..., description="URL of uploaded voice sample")
    order_id: str | None = Field(None, description="Order ID to associate voice with")


class CloneVoiceDirectRequest(BaseModel):
    """Direct voice cloning request with base64 audio."""

    voice_name: str = Field(..., description="Name for the cloned voice")
    audio_base64: str = Field(..., max_length=30_000_000, description="Base64 encoded audio (webm/mp3, max ~20MB)")
    order_id: str | None = Field(None, description="Order ID to associate voice with")


class CloneVoiceResponse(BaseModel):
    """Voice cloning response."""

    voice_id: str
    message: str


class PreviewVoiceRequest(BaseModel):
    """Preview voice request."""

    voice_type: str = Field(
        "female", description="'female' or 'male' for system voices, or voice_id for cloned"
    )
    text: str = Field(
        default="Bir varmis bir yokmus, evvel zaman icinde...",
        description="Text to convert to speech",
    )


# ---------------------------------------------------------------------------
# Outfit suggestion schemas
# ---------------------------------------------------------------------------


class SuggestOutfitsRequest(BaseModel):
    """Request to generate AI outfit suggestions for the child."""

    child_name: str = Field(default="Ali", max_length=50)
    child_age: int = Field(default=7, ge=2, le=12)
    child_gender: str = Field(default="erkek")
    scenario_id: str | None = None
    visual_style_id: str | None = None


class SuggestOutfitsResponse(BaseModel):
    """Response with 6 outfit suggestions."""

    success: bool = True
    outfits: list[str] = []
    error: str | None = None

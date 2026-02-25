"""AI service endpoints - story and image generation."""

from __future__ import annotations

import base64
import uuid
from typing import TYPE_CHECKING
from uuid import UUID

if TYPE_CHECKING:
    from app.services.ai.fal_ai_service import BookGenerationResult

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import select

from app.api.v1.deps import AdminUser, DbSession
from app.core.exceptions import (
    AIServiceError,
    ContentPolicyError,
    ValidationError,
)
from app.core.sanitizer import (
    detect_prompt_injection,
    sanitize_for_prompt,
    validate_child_name,
)
from app.core.url_validator import validate_image_url
from app.models.order import Order
from app.services.ai import (
    ImageProvider,
    get_image_generator,
)

router = APIRouter()
_V3_BLOCK_MSG = "V2_LABEL_BLOCKED: expected v3"
_GENERATE_STORY_ROUTE = "/api/v1/ai/generate-story"


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
    # NEW: Child photo URL for forensic face analysis (maximizes likeness)
    child_photo_url: str | None = Field(
        default=None,
        description="URL to child's photo for AI facial analysis. If provided, generates detailed face description for better likeness.",
    )
    # Option 1: Use scenario_id to fetch from database (RECOMMENDED)
    scenario_id: str | None = None
    # Option 2: Provide scenario details manually (fallback for testing)
    scenario_name: str = Field(default="Kapadokya Macerası", max_length=100, description="Scenario name")
    scenario_prompt: str = Field(
        default="Çocuk Kapadokya'da peri bacaları arasında macera yaşar",
        max_length=500,
        description="Scenario description (max 500 chars)",
    )
    learning_outcomes: list[str] = Field(
        ...,
        min_length=1,
        description="Eğitsel hedefler (zorunlu). Örn: Diş fırçalama alışkanlığı: eğlenceli oyun + her gün yapma farkındalığı",
    )
    visual_style: str = Field(
        default="children's book illustration, soft colors",
        max_length=2000,
        description="Visual style prompt for AI image generation",
    )
    # V2: look up VisualStyle from DB by ID — overrides visual_style text when provided
    visual_style_id: str | None = Field(
        default=None,
        description="UUID of VisualStyle row. If provided, prompt_modifier + style_negative_en are read from DB.",
    )
    page_count: int = Field(default=16, ge=1, le=64, description="Sayfa sayısı (kapak hariç)")
    # V2: Clothing description for outfit lock (consistent across all pages)
    clothing_description: str | None = Field(
        default=None,
        max_length=300,
        description="Child's clothing description for consistent outfit across all pages (e.g., 'kırmızı mont, mavi pantolon')",
    )
    # NEW: Custom variables for scenario-specific inputs
    custom_variables: dict[str, str] | None = Field(
        default=None,
        description="User-provided values for scenario-specific custom inputs (e.g., {spaceship_name: 'Apollo'})",
    )

    @field_validator("child_name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate and sanitize child name."""
        is_valid, result = validate_child_name(v)
        if not is_valid:
            raise ValueError(result)
        return result

    @field_validator("scenario_prompt", "scenario_name")
    @classmethod
    def check_injection(cls, v: str) -> str:
        """Check for prompt injection attempts."""
        is_injection, _ = detect_prompt_injection(v)
        if is_injection:
            raise ValueError("Geçersiz içerik tespit edildi")
        return sanitize_for_prompt(v, max_length=500)

    @field_validator("visual_style")
    @classmethod
    def sanitize_style(cls, v: str) -> str:
        """Sanitize visual style input."""
        is_injection, _ = detect_prompt_injection(v)
        if is_injection:
            return "children's book illustration, soft colors"
        return sanitize_for_prompt(v, max_length=200)

    @field_validator("child_photo_url")
    @classmethod
    def validate_photo_url(cls, v: str | None) -> str | None:
        """Validate child photo URL to prevent SSRF."""
        return validate_image_url(v, field_name="child_photo_url")

    @field_validator("custom_variables")
    @classmethod
    def sanitize_custom_vars(cls, v: dict[str, str] | None) -> dict[str, str] | None:
        """Sanitize custom variable values against prompt injection."""
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


class TestImageRequest(BaseModel):
    """Test image generation request."""

    prompt: str = "A happy child astronaut floating in space with colorful planets"
    style: str = "cartoon, vibrant colors, children's book illustration"
    # Optional: page dimensions for dynamic resolution
    page_width_mm: float | None = None
    page_height_mm: float | None = None
    bleed_mm: float = 3.0
    product_id: str | None = None  # If provided, uses product's template



# =============================================================================
# FAL.AI INTEGRATED STORY GENERATION (SOTA Face Consistency)
# =============================================================================


class GenerateBookRequest(BaseModel):
    """
    Complete book generation request with Fal.ai PuLID face consistency.

    This is the RECOMMENDED endpoint for production use.
    Uses FalAIService with PuLID for face+outfit consistency across all pages.
    """

    # Child info
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
        """Validate and sanitize child name."""
        is_valid, result = validate_child_name(v)
        if not is_valid:
            raise ValueError(result)
        return result

    # CRITICAL: Photo URL for PuLID face consistency
    child_photo_url: str = Field(
        ..., description="URL to child's photo. CRITICAL for face consistency via PuLID."
    )

    # Scenario
    scenario_id: str = Field(..., description="Scenario UUID from database")

    # Visual style
    visual_style_id: str | None = Field(None, description="Visual style UUID (optional)")
    visual_style_modifier: str = Field(
        default="watercolor children's book illustration, soft colors, whimsical",
        description="Style modifier for image generation",
    )

    # Outfit consistency - CRITICAL for same clothes on all pages
    clothing_description: str | None = Field(
        None,
        description="What the child is wearing (e.g., 'red striped t-shirt and blue shorts'). If not provided, will be detected from photo.",
    )

    # Page count
    page_count: int = Field(
        default=10, ge=4, le=32, description="Number of story pages (excluding cover)"
    )

    # AI Config (optional - for selecting provider)
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
    """
    Response format for partial success scenarios.

    When some pages fail but others succeed, this response provides
    detailed information about which pages succeeded and which failed,
    allowing the frontend to display what's available and offer retry
    options for failed pages.
    """

    success: bool  # True if at least one page succeeded
    partial_success: bool  # True if some pages failed but some succeeded
    complete_success: bool  # True if all pages succeeded

    # Counts
    total_pages: int
    success_count: int
    failed_count: int

    # Page details
    pages: list[PageGenerationStatus]

    # Successful pages (for display)
    successful_urls: dict[str, str]  # page_num (str) -> url

    # Failed pages (for retry)
    failed_pages: list[int]

    # Message for user
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

        # Determine message
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
    # For face consistency
    face_photo_url: str | None = Field(None, description="Child's photo URL for face consistency")
    clothing: str | None = Field(None, description="Clothing description for outfit consistency")
    id_weight: float = Field(
        default=0.4,
        ge=0.2,
        le=1.0,
        description="Face identity strength (lower = better backgrounds)",
    )
    width: int = 1024  # Yatay A4 oranı
    height: int = 724  # 1024/724 ≈ A4 landscape
    is_cover: bool = Field(
        default=False, description="Whether this is a cover page (affects validation rules)"
    )
    page_number: int | None = Field(
        default=None, description="Page number (0=cover). Used for observability."
    )


# =============================================================================
# FAL.AI IMAGE GENERATION ENDPOINTS
# =============================================================================


@router.post("/test-image-fal")
async def test_fal_image_generation(request: TestFalImageRequest, admin: AdminUser):
    """
    Test Fal.ai Flux image generation with optional PuLID face consistency.

    If face_photo_url is provided:
    - Uses PuLID for face identity preservation
    - id_weight controls face likeness strength (0.5-1.0)

    If clothing is provided:
    - Appends to prompt for outfit consistency

    Returns: JSON with image_url (frontend fetches image separately)
    """
    import structlog

    from app.core.database import async_session_factory
    from app.services.ai.image_provider_dispatch import (
        get_effective_ai_config,
        get_image_provider_for_generation,
    )

    logger = structlog.get_logger()

    logger.info(
        "Testing image generation (effective provider from config)",
        has_face_ref=bool(request.face_photo_url),
        has_clothing=bool(request.clothing),
        id_weight=request.id_weight,
    )

    try:
        async with async_session_factory() as db:
            ai_config = await get_effective_ai_config(db, product_id=None)
            provider_name = (
                (ai_config.image_provider or "gemini").strip().lower() if ai_config else "gemini"
            )
            if not request.face_photo_url and provider_name in ("gemini", "gemini_flash"):
                provider_name = "fal"
            service = get_image_provider_for_generation(provider_name)

        provider_label = (
            "Gemini" if provider_name in ("gemini", "gemini_flash") else "Fal.ai Flux PuLID"
        )
        _is_cover = request.is_cover or (request.page_number == 0)

        from app.services.ai.face_service import resolve_face_reference
        from app.services.storage_service import storage_service as _ss_ai
        _effective_face_url, _face_embedding = await resolve_face_reference(
            request.face_photo_url or "", _ss_ai
        )

        result = await service.generate_consistent_image(
            prompt=request.prompt,
            child_face_url=_effective_face_url,
            clothing_prompt=request.clothing or "",
            style_modifier=request.style,
            width=request.width,
            height=request.height,
            id_weight=request.id_weight,
            is_cover=_is_cover,
            page_number=request.page_number,
            reference_embedding=_face_embedding,
        )
        image_url = result[0] if isinstance(result, tuple) else result
        logger.info(
            "Image generated successfully",
            image_url=(image_url[:80] + "...") if image_url else "",
            has_face_ref=bool(request.face_photo_url),
            provider=provider_name,
        )

        return {
            "success": True,
            "image_url": image_url,
            "provider": provider_label,
            "face_consistency": "enabled" if request.face_photo_url else "disabled",
        }

    except Exception as e:
        logger.exception("Image test failed", error=str(e))
        return {
            "success": False,
            "error": str(e),
            "provider": "Fal.ai / Gemini",
        }


# =============================================================================
# TEMP IMAGE UPLOAD (For Frontend → Fal.ai PuLID)
# =============================================================================


_MAX_TEMP_IMAGE_BASE64 = 7_000_000  # ~5 MB binary
_ALLOWED_IMAGE_FORMATS = {"JPEG", "PNG", "WEBP", "GIF"}


class TempImageUploadRequest(BaseModel):
    """Temporary image upload for Fal.ai PuLID access."""

    image_base64: str = Field(
        ..., max_length=_MAX_TEMP_IMAGE_BASE64,
        description="Base64 encoded image (with or without data: prefix, max ~5MB)",
    )


@router.post("/upload/temp-image")
async def upload_temp_image(request: TempImageUploadRequest) -> dict:
    """
    Upload a temporary image to GCS and return a public URL.

    Security:
    - Max ~5 MB (base64)
    - PIL validates actual image content (magic bytes)
    - Only JPEG/PNG/WEBP/GIF accepted

    Returns:
        url: Public GCS URL for the image
    """
    import io
    from uuid import uuid4

    import structlog
    from PIL import Image, UnidentifiedImageError

    from app.services.storage_service import StorageService

    logger = structlog.get_logger()

    try:
        image_data = request.image_base64
        if "," in image_data:
            image_data = image_data.split(",", 1)[1]

        image_bytes = base64.b64decode(image_data)

        # Validate image content with PIL (prevents non-image uploads)
        try:
            img = Image.open(io.BytesIO(image_bytes))
            img.verify()  # verify() checks headers without loading full data
            img_format = img.format
        except (UnidentifiedImageError, Exception):
            return {
                "success": False,
                "error": "Geçersiz görsel dosyası. Lütfen JPEG, PNG veya WEBP yükleyin.",
                "url": "",
            }

        if img_format not in _ALLOWED_IMAGE_FORMATS:
            return {
                "success": False,
                "error": f"Desteklenmeyen format: {img_format}. İzin verilen: JPEG, PNG, WEBP, GIF.",
                "url": "",
            }

        temp_id = str(uuid4())[:8]

        storage = StorageService()
        url = storage.upload_temp_image(
            image_bytes=image_bytes,
            temp_id=temp_id,
        )

        logger.info("Temp image uploaded for PuLID", temp_id=temp_id, size_kb=len(image_bytes) // 1024)

        # Face pre-validation: check if a face is detectable for PuLID
        face_quality: dict = {"detected": False, "score": 0.0, "warning": None}
        try:
            from app.services.ai.face_service import FaceService
            _face_svc = FaceService()
            _face_svc.SCORE_THRESHOLD = 0.3  # Very lenient for pre-check
            _face_svc.MIN_IMAGE_SIZE = 64
            _score, _, _ = await _face_svc.detect_and_extract(image_bytes)
            face_quality["detected"] = True
            face_quality["score"] = round(float(_score), 2)
            if _score < 0.6:
                face_quality["warning"] = "Yüz kalitesi düşük. Daha net bir fotoğraf daha iyi sonuç verir."
        except Exception:
            face_quality["warning"] = "Yüz tespit edilemedi. Yüzün net göründüğü bir fotoğraf seçin."

        return {
            "success": True,
            "url": url,
            "temp_id": temp_id,
            "face_quality": face_quality,
        }

    except Exception as e:
        logger.error("Temp image upload failed", error=str(e))
        return {
            "success": False,
            "error": "Görsel yüklenirken bir hata oluştu.",
            "url": "",
        }




# =============================================================================
# LEGACY TEST ENDPOINTS (Gemini-based)
# =============================================================================


@router.post("/test-story")
async def test_story_generation(request: TestStoryRequest, admin: AdminUser) -> dict:
    """
    Test Gemini story generation without database.
    Just to verify API is working.
    """
    import httpx

    from app.config import settings

    prompt = f"""
    Sen çocuk hikayesi yazarısın. {request.child_name} adında {request.child_age} yaşında 
    bir çocuk için "{request.scenario}" temalı kısa bir hikaye yaz.
    Hikaye 2-3 paragraf olsun, eğlenceli ve eğitici olsun.
    """

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={settings.gemini_api_key}",
                json={
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {
                        "temperature": 0.8,
                        "maxOutputTokens": 1024,
                    },
                },
            )
            response.raise_for_status()
            data = response.json()

            story = data["candidates"][0]["content"]["parts"][0]["text"]

            return {
                "success": True,
                "child_name": request.child_name,
                "scenario": request.scenario,
                "story": story,
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }


@router.post("/test-story-structured")
async def test_structured_story_generation(
    request: TestStructuredStoryRequest, db: DbSession,
) -> dict:
    """
    Generate STRUCTURED story with visual prompts using TWO-PASS GENERATION.
    Public create flow uses this; rate-limited in middleware. Auth optional.

    TWO-PASS STRATEGY (NEW!):
    ========================
    PASS 1 - "Pure Author" (gemini-1.5-pro):
      - 100% creative focus
      - Beautiful, emotional, immersive story
      - No JSON constraints

    PASS 2 - "Technical Director" (gemini-2.5-flash):
      - Takes the beautiful story
      - Splits into pages, generates visual prompts
      - Structured JSON output

    Returns JSON with title + pages (each with text and visual_prompt).
    """

    import structlog
    from sqlalchemy import select

    from app.models.scenario import Scenario
    from app.services.ai.face_analyzer_service import get_face_analyzer
    from app.services.ai.gemini_service import get_gemini_service

    logger = structlog.get_logger()
    logger.info("test-story-structured endpoint called", child_name=request.child_name)

    # Build child description - ENHANCED with face analysis if photo provided
    face_analysis_used = False
    face_analysis_error = None
    child_visual_desc = ""

    if request.child_photo_url:
        try:
            from app.core.pipeline_events import mask_photo_url
            logger.info(
                "Starting face analysis for DOUBLE LOCKING",
                child_photo_hash=mask_photo_url(request.child_photo_url),
            )
            face_analyzer = get_face_analyzer()
            child_visual_desc = await face_analyzer.analyze_for_ai_director(
                image_source=request.child_photo_url,
                child_name=request.child_name,
                child_age=request.child_age,
                child_gender=request.child_gender,
            )
            face_analysis_used = True
            logger.info("Face analysis complete", description=child_visual_desc[:100])
        except Exception as e:
            logger.warning(
                "FACE_ANALYSIS_FAIL",
                error=str(e),
                child_photo_hash=mask_photo_url(request.child_photo_url),
            )
            face_analysis_error = str(e)

    # Fetch scenario from database
    scenario = None

    if request.scenario_id:
        try:
            result = await db.execute(
                select(Scenario).where(Scenario.id == UUID(request.scenario_id))
            )
            scenario = result.scalar_one_or_none()
        except Exception as e:
            logger.warning("Failed to fetch scenario by ID", error=str(e))

    # Senaryo adıyla ara: önce TAM EŞLEŞME (Kapadokya / Yerebatan Sarnıcı karışmasın)
    if not scenario and request.scenario_name:
        name_stripped = (request.scenario_name or "").strip()
        if name_stripped:
            try:
                result = await db.execute(
                    select(Scenario).where(Scenario.name == name_stripped)
                )
                scenario = result.scalar_one_or_none()
                if scenario:
                    logger.info("Scenario matched by exact name", name=name_stripped)
            except Exception as e:
                logger.warning("Failed to fetch scenario by exact name", error=str(e))
            if not scenario:
                try:
                    result = await db.execute(
                        select(Scenario)
                        .where(Scenario.name.ilike(f"%{name_stripped}%"))
                        .order_by(Scenario.name)
                        .limit(1)
                    )
                    scenario = result.scalar_one_or_none()
                    if scenario:
                        logger.warning(
                            "Scenario matched by ilike (exact match preferred); possible cross-scenario leak",
                            requested=name_stripped,
                            matched=scenario.name,
                        )
                except Exception as e:
                    logger.warning("Failed to fetch scenario by ilike", error=str(e))

    # V2: Look up VisualStyle from DB by ID (overrides text when found)
    style_prompt_resolved = (request.visual_style or "").strip()
    style_negative_resolved = ""
    style_id_resolved: str | None = request.visual_style_id

    if request.visual_style_id:
        try:
            from app.models.visual_style import VisualStyle

            vs_result = await db.execute(
                select(VisualStyle).where(VisualStyle.id == UUID(request.visual_style_id))
            )
            vs_row = vs_result.scalar_one_or_none()
            if vs_row:
                style_prompt_resolved = (
                    vs_row.prompt_modifier or ""
                ).strip() or style_prompt_resolved
                style_negative_resolved = (vs_row.style_negative_en or "").strip()
                logger.info(
                    "[V2] VisualStyle loaded from DB",
                    visual_style_id=request.visual_style_id,
                    style_name=vs_row.name,
                    has_negative=bool(style_negative_resolved),
                )
            else:
                logger.warning(
                    "[V2] visual_style_id not found in DB, using text fallback",
                    visual_style_id=request.visual_style_id,
                )
        except Exception as e:
            logger.warning("[V2] Failed to fetch visual_style by ID", error=str(e))

    # V2: Resolve clothing_description — priority: request > scenario outfit > auto
    clothing_desc = (request.clothing_description or "").strip()
    if not clothing_desc and scenario:
        # Use scenario-specific outfit (gender-based)
        _gender = (request.child_gender or "erkek").lower()
        if _gender in ("kiz", "kız", "girl", "female"):
            clothing_desc = (getattr(scenario, "outfit_girl", None) or "").strip()
            if not clothing_desc:
                clothing_desc = (getattr(scenario, "outfit_boy", None) or "").strip()
        else:
            clothing_desc = (getattr(scenario, "outfit_boy", None) or "").strip()
            if not clothing_desc:
                clothing_desc = (getattr(scenario, "outfit_girl", None) or "").strip()
        if clothing_desc:
            logger.info(
                "clothing_from_scenario",
                scenario=scenario.name,
                gender=_gender,
                outfit=clothing_desc[:60],
            )
    if not clothing_desc:
        clothing_desc = await _auto_outfit_for_story(
            scenario_name=scenario.name if scenario else request.scenario_name or "macera",
            child_age=request.child_age or 7,
            child_gender=request.child_gender or "erkek",
        )

    # V2: Personalize style block so DB prompt_modifier never leaks wrong character (e.g. "Uras" / "boy")
    from app.prompt_engine import personalize_style_prompt

    style_prompt_resolved = personalize_style_prompt(
        style_prompt_resolved,
        child_name=request.child_name or "",
        child_age=request.child_age or 7,
        child_gender=request.child_gender or "",
    )

    # Build scenario info
    scenario_name = scenario.name if scenario else request.scenario_name
    scenario_description = scenario.description if scenario else request.scenario_prompt

    # =========================================================================
    # TWO-PASS GENERATION via GeminiService
    # =========================================================================
    try:
        gemini_service = get_gemini_service()

        logger.info(
            "Starting TWO-PASS story generation",
            pass1_model=gemini_service.story_model,
            pass2_model=gemini_service.technical_model,
            scenario=scenario_name,
            child_name=request.child_name,
        )

        # Create a mock scenario object if none found
        class MockScenario:
            def __init__(self, name, description):
                self.name = name
                self.description = description
                self.cover_prompt_template = None
                self.page_prompt_template = None
                self.ai_prompt_template = None
                self.location_constraints = None
                self.cultural_elements = None

            def get_cover_prompt(self, **kwargs) -> str | None:
                """Mock method - returns None since no template exists."""
                return None

            def get_page_prompt(self, **kwargs) -> str | None:
                """Mock method - returns None since no template exists."""
                return None

            def get_story_prompt(self, **kwargs) -> str | None:
                """Mock method - returns None since no template exists."""
                return None

        scenario_obj = scenario if scenario else MockScenario(scenario_name, scenario_description)

        # Fetch REAL LearningOutcome objects from DB for accurate ai_prompt instructions
        from app.models.learning_outcome import LearningOutcome

        outcomes: list[LearningOutcome] = []
        if request.learning_outcomes:
            lo_result = await db.execute(
                select(LearningOutcome).where(
                    LearningOutcome.name.in_(request.learning_outcomes),
                    LearningOutcome.is_active == True,  # noqa: E712
                )
            )
            outcomes = list(lo_result.scalars().all())

            # Log missing outcomes for debugging
            found_names = {o.name for o in outcomes}
            missing = [n for n in request.learning_outcomes if n not in found_names]
            if missing:
                logger.warning(
                    "Some learning outcomes not found in DB — using name as fallback",
                    missing=missing,
                )
                # Fallback: create lightweight mock with effective_ai_instruction
                class _FallbackOutcome:
                    def __init__(self, name: str):
                        self.name = name
                        self.ai_prompt = name
                        self.ai_prompt_instruction = None
                        self.banned_words_tr = None

                    @property
                    def effective_ai_instruction(self) -> str:
                        return self.ai_prompt_instruction or self.ai_prompt or self.name

                outcomes.extend(_FallbackOutcome(n) for n in missing)

        # ==================== SINGLE SOURCE OF TRUTH - DEBUG LOGGING ====================
        # Log all inputs BEFORE generation
        location_constraints = getattr(scenario_obj, "location_constraints", None)

        logger.info(
            "[STORY-GEN] SINGLE SOURCE OF TRUTH - Story Generation Start",
            scenario_id=request.scenario_id,
            scenario_name=scenario_name,
            scenario_from_db=bool(scenario),
            has_location_constraints=bool(location_constraints),
            location_constraints_preview=location_constraints[:100]
            if location_constraints
            else "none",
            visual_style_input=style_prompt_resolved[:80] if style_prompt_resolved else "default",
            visual_style_id=request.visual_style_id,
            clothing_description=clothing_desc[:50] if clothing_desc else "none",
            page_count=request.page_count,
        )

        # Call TWO-PASS generation with page_count from request
        logger.info(f"Calling TWO-PASS generation with page_count={request.page_count}")

        story_response, final_pages, _outfit, _blueprint = await gemini_service.generate_story_structured(
            scenario=scenario_obj,
            child_name=request.child_name,
            child_age=request.child_age,
            child_gender=request.child_gender,
            outcomes=outcomes,
            visual_style=style_prompt_resolved,
            visual_character_description=child_visual_desc,
            page_count=request.page_count,
            fixed_outfit=clothing_desc,
            requested_version="v3",
        )

        # ==================== TITLE SAFETY NET ====================
        # Gemini bazen generic title döndürüyor — son kontrol noktası
        from app.services.ai.gemini_service import (
            _get_possessive_suffix,
            _normalize_title_turkish,
        )

        _GENERIC_TITLES = {
            "hikaye", "masal", "hikâye", "öykü", "macera", "story",
            "bir hikaye", "bir masal", "yeni hikaye", "güzel hikaye",
        }
        _title = (story_response.title or "").strip()
        if _title.lower() in _GENERIC_TITLES or len(_title) < 4:
            _sn = scenario_name or "Büyülü Macera"
            _sfx = _get_possessive_suffix(request.child_name or "")
            story_response.title = f"{request.child_name}'{_sfx} {_sn}"
            logger.warning("ai.py: Generic title replaced", original=_title, new=story_response.title)

        # İngilizce/yanlış yer adlarını Türkçe'ye çevir
        story_response.title = _normalize_title_turkish(story_response.title)

        # Check if V3 pipeline produced these pages
        from app.core.build_meta import get_commit_hash
        from app.core.pipeline_version import (
            prompt_builder_name_for_version,
            require_v3_pipeline,
        )
        _job_id = str(uuid.uuid4())
        _non_v3_pages = [
            p
            for p in final_pages
            if getattr(p, "pipeline_version", "") != "v3"
            or getattr(p, "composer_version", "") != "v3"
            or not getattr(p, "v3_composed", False)
        ]
        if _non_v3_pages:
            logger.error(
                _V3_BLOCK_MSG,
                route="/api/v1/ai/test-story-structured",
                job_id=_job_id,
                non_v3_pages=len(_non_v3_pages),
            )
            raise HTTPException(
                status_code=400,
                detail=_V3_BLOCK_MSG,
            )
        _pipeline_version = "v3"
        try:
            require_v3_pipeline(
                pipeline_version=_pipeline_version,
                job_id=_job_id,
                route=_GENERATE_STORY_ROUTE,
            )
        except ValueError as _v3_err:
            logger.error(
                _V3_BLOCK_MSG,
                route=_GENERATE_STORY_ROUTE,
                job_id=_job_id,
                error=str(_v3_err),
            )
            raise HTTPException(
                status_code=400,
                detail=_V3_BLOCK_MSG,
            ) from _v3_err
        logger.info(
            "PIPELINE_AUDIT",
            job_id=_job_id,
            route=_GENERATE_STORY_ROUTE,
            pipeline_version=_pipeline_version,
            template_id=str(getattr(scenario_obj, "id", "") or ""),
            prompt_builder_name=prompt_builder_name_for_version(_pipeline_version),
            commit_hash=get_commit_hash(),
        )

        _any_enhancement_skipped = any(
            getattr(p, "v3_enhancement_skipped", False) for p in final_pages
        )
        if _any_enhancement_skipped:
            logger.warning(
                "ai.py: V3 enhancement was skipped — raw prompts used (graceful degradation)",
                skipped_pages=sum(1 for p in final_pages if getattr(p, "v3_enhancement_skipped", False)),
            )

        if _pipeline_version == "v3":
            # V3 path: pages already have fully composed prompts — pass through
            pages_with_prompts = []
            for page in final_pages:
                pages_with_prompts.append(
                    {
                        "page_number": page.page_number,
                        "text": page.text,
                        "visual_prompt": page.visual_prompt,
                        "negative_prompt": page.negative_prompt or "",
                        "v3_composed": True,
                        "v3_enhancement_skipped": getattr(page, "v3_enhancement_skipped", False),
                        "page_type": getattr(page, "page_type", "inner"),
                        "page_index": getattr(page, "page_index", 0),
                        "story_page_number": getattr(page, "story_page_number", None),
                        "composer_version": getattr(page, "composer_version", "v3"),
                        "pipeline_version": getattr(page, "pipeline_version", "v3"),
                    }
                )
            logger.info(
                "ai.py: V3 pages passed through (no V2 recomposition)",
                page_count=len(pages_with_prompts),
                enhancement_skipped=_any_enhancement_skipped,
            )
            for _i, page in enumerate(pages_with_prompts[:3]):
                logger.info(
                    f"[PROMPT-CHECK] V3 FINAL Page {page['page_number']}",
                    prompt_length=len(page["visual_prompt"]),
                    prompt_preview=page["visual_prompt"][:200] + "...",
                    has_style_block="\nSTYLE:\n" in page["visual_prompt"],
                    v3_composed=True,
                )

        return {
            "success": True,
            "pipeline_version": _pipeline_version,
            "pipeline_label": _pipeline_version,
            "v3_enhancement_skipped": _any_enhancement_skipped,
            "generation_method": "TWO-PASS (Pure Author + Technical Director)",
            "pass1_model": gemini_service.story_model,
            "pass2_model": gemini_service.technical_model,
            "face_analysis_used": face_analysis_used,
            "face_analysis_error": face_analysis_error,
            # Frontend expects "story" object with title and pages
            "story": {
                "title": story_response.title,
                "pages": pages_with_prompts,
            },
            "page_count": len(pages_with_prompts),
            "used_page_count": request.page_count,
            "metadata": {
                "scenario_name": scenario_name,
                "visual_style": style_prompt_resolved[:50] if style_prompt_resolved else "default",
                "visual_style_id": style_id_resolved,
                "clothing_description": clothing_desc or None,
                "child_visual_description": child_visual_desc[:100]
                if child_visual_desc
                else "basic",
                "cover_template_source": "v3_composed" if _pipeline_version == "v3" else "default",
                "inner_template_source": "v3_composed" if _pipeline_version == "v3" else "default",
            },
        }

    except ContentPolicyError:
        # Aile kelimesi ihlali — legacy fallback'e düşme, doğrudan hata dön!
        raise

    except AIServiceError as ai_exc:
        from app.core.pipeline_events import PipelineErrorCode, build_error_response

        _err_str = str(ai_exc)
        _is_rate_limit = "429" in _err_str or "rate limit" in _err_str.lower()
        _error_code = PipelineErrorCode.RATE_LIMIT if _is_rate_limit else "AI_GENERATION_FAIL"

        logger.error(
            "PIPELINE_FAIL",
            error_code=_error_code,
            reason_code=ai_exc.reason_code,
            trace_id=ai_exc.trace_id,
            request_id=structlog.contextvars.get_contextvars().get("request_id", ""),
            user_id="",
            product_id="",
            requested_page_count=request.page_count,
            used_page_count=0,
            pipeline_version="v3",
            error=_err_str[:300],
        )

        return build_error_response(
            error_code=_error_code,
            trace_id=ai_exc.trace_id,
            retry_after=60 if _is_rate_limit else None,
        )

    except Exception as e:
        import uuid as _uuid_err

        from app.core.pipeline_events import PipelineErrorCode, build_error_response

        error_str = str(e)
        _trace = _uuid_err.uuid4().hex[:12]
        _is_rate_limit = "429" in error_str or "rate limit" in error_str.lower()
        _error_code = PipelineErrorCode.RATE_LIMIT if _is_rate_limit else "PIPELINE_UNHANDLED"

        logger.exception(
            "PIPELINE_FAIL",
            error_code=_error_code,
            trace_id=_trace,
            request_id=structlog.contextvars.get_contextvars().get("request_id", ""),
            user_id="",
            product_id="",
            requested_page_count=request.page_count,
            used_page_count=0,
            pipeline_version="v3",
            error=error_str[:300],
        )

        if _is_rate_limit:
            return build_error_response(
                error_code=PipelineErrorCode.RATE_LIMIT,
                trace_id=_trace,
                retry_after=60,
            )

        # FALLBACK: Use legacy single-pass if TWO-PASS fails (non-rate-limit errors only)
        logger.warning(
            "LEGACY_FALLBACK_USED",
            trace_id=_trace,
            error_code=PipelineErrorCode.LEGACY_FALLBACK_USED,
            reason=error_str[:200],
        )
        return await _legacy_single_pass_generation(
            request,
            db,
            scenario,
            scenario_name,
            scenario_description,
            child_visual_desc,
            face_analysis_used,
            face_analysis_error,
            clothing_desc=clothing_desc,
        )


async def _legacy_single_pass_generation(
    request,
    db,
    scenario,
    scenario_name,
    scenario_description,
    child_visual_desc,
    face_analysis_used,
    face_analysis_error,
    clothing_desc: str = "",
):
    """Legacy single-pass generation - fallback if TWO-PASS fails.

    Includes retry logic with exponential backoff for rate limit errors.
    """
    import asyncio
    import json

    import httpx
    import structlog

    from app.config import settings

    logger = structlog.get_logger()

    inner_pages = request.page_count
    gender_word = (
        "boy"
        if request.child_gender == "erkek"
        else "girl"
        if request.child_gender == "kiz"
        else "child"
    )

    # Simplified prompt for fallback
    _outfit_line = f"KIYAFETİ (SABIT, DEĞİŞMEZ): {clothing_desc}" if clothing_desc else ""
    system_prompt = f"""Sen bir ÇOCUK KİTABI YAZARISIN.
{inner_pages} sayfalık büyülü bir hikaye yaz.

ÇOCUK: {request.child_name}, {request.child_age} yaşında {gender_word}
SENARYO: {scenario_name}
GÖRSEL STİL: {request.visual_style}
{_outfit_line}

🚫🚫 KESİN KURAL: Hikayede anne, baba, kardeş, abla, abi, dede, nine, babaanne,
anneanne, aile, ebeveyn kelimeleri ASLA GEÇMEYECEK!
Çocuk macerayı TEK BAŞINA veya hayvan/hayali arkadaşlarla yaşayacak!
Bu kural İHLAL EDİLEMEZ!

Her sayfa için:
- text: Türkçe hikaye metni (2-4 cümle, duygusal, büyülü)
- visual_prompt: İngilizce sahne açıklaması (SADECE sahne ve aksiyonu yaz — kıyafet bilgisi YAZMA, sistem otomatik ekler)

JSON döndür."""

    user_prompt = f"Hikaye başlat: {scenario_description}"

    # Retry configuration — eski değerler (30s base × 2^n) ekranı 4-8 dk donduruyordu
    max_retries = 4
    base_wait = 8  # seconds — free tier rate limit 15 RPM; daha uzun beklemek gerek

    for attempt in range(max_retries):
        try:
            async with httpx.AsyncClient(timeout=90.0) as client:
                response = await client.post(
                    f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={settings.gemini_api_key}",
                    json={
                        "contents": [{"parts": [{"text": system_prompt + "\n\n" + user_prompt}]}],
                        "generationConfig": {
                            "temperature": 0.9,
                            "maxOutputTokens": 12000,
                            "responseMimeType": "application/json",
                        },
                    },
                )
                response.raise_for_status()
                data = response.json()

                raw_text = data["candidates"][0]["content"]["parts"][0]["text"]

                try:
                    story_data = json.loads(raw_text)
                except json.JSONDecodeError as e:
                    return {
                        "success": False,
                        "error": "JSON parse error (legacy)",
                        "details": str(e),
                    }

                # Handle both dict format {"pages": [...]} and direct list format [...]
                if isinstance(story_data, list):
                    pages_list = story_data
                    title = "Hikaye"
                else:
                    pages_list = story_data.get("pages", [])
                    title = story_data.get("title", "Hikaye")

                # V2 compose: apply compose_visual_prompt to raw Gemini output
                from app.prompt_engine import compose_visual_prompt as _compose
                from app.prompt_engine.constants import (
                    DEFAULT_COVER_TEMPLATE_EN,
                    DEFAULT_INNER_TEMPLATE_EN,
                )
                from app.services.prompt_template_service import get_prompt_service

                _tpl_svc = get_prompt_service()
                _cover_tpl = await _tpl_svc.get_template_en(
                    db, "COVER_TEMPLATE", DEFAULT_COVER_TEMPLATE_EN
                )
                _inner_tpl = await _tpl_svc.get_template_en(
                    db, "INNER_TEMPLATE", DEFAULT_INNER_TEMPLATE_EN
                )

                _style = (request.visual_style or "").strip()
                # Priority: resolved clothing_desc (scenario outfit) > request field
                _clothing = clothing_desc or (getattr(request, "clothing_description", None) or "").strip()

                pages_with_prompts = []
                for idx, page in enumerate(pages_list):
                    if isinstance(page, dict):
                        _pn = page.get("page_number", idx)
                        _raw_vp = page.get("visual_prompt", "")
                    else:
                        _pn = idx
                        _raw_vp = ""

                    _is_cover = _pn == 0
                    _tpl_key = "COVER_TEMPLATE" if _is_cover else "INNER_TEMPLATE"
                    _tpl_en = _cover_tpl if _is_cover else _inner_tpl

                    if _raw_vp:
                        _composed, _neg = _compose(
                            _raw_vp,
                            is_cover=_is_cover,
                            template_en=_tpl_en,
                            clothing_description=_clothing,
                            style_prompt_en=_style,
                        )
                    else:
                        _composed, _neg = "", ""

                    _lower = _composed.lower()
                    pages_with_prompts.append(
                        {
                            "page_number": _pn,
                            "text": page.get("text", "") if isinstance(page, dict) else str(page),
                            "visual_prompt": _composed,
                            "negative_prompt": _neg,
                            "pipeline_version": "v2_fallback",
                            "composer_version": "v2_fallback",
                            "v3_composed": False,
                            "v2_debug": {
                                "template_key": _tpl_key,
                                "template_from_db": bool(_tpl_en),
                                "style_key": _style[:60] if _style else None,
                                "has_style_block": "\nSTYLE:\n" in _composed,
                                "has_negative": bool(_neg),
                                "has_safe_area": (
                                    "space for title at top" in _lower
                                    if _is_cover
                                    else "text space at bottom" in _lower
                                ),
                                "has_composition": "child not looking at camera" in _lower,
                                "is_cover": _is_cover,
                                "legacy_fallback": True,
                            },
                        }
                    )

                return {
                    "success": True,
                    "pipeline_version": "v2_fallback",
                    "pipeline_label": "v2_fallback",
                    "generation_method": "LEGACY FALLBACK (V2 composed)",
                    "model": "gemini-2.5-flash",
                    "face_analysis_used": face_analysis_used,
                    "story": {
                        "title": title,
                        "pages": pages_with_prompts,
                    },
                    "page_count": len(pages_with_prompts),
                    "used_page_count": request.page_count,
                }

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                # Rate limit - wait and retry
                wait_time = base_wait * (2**attempt)  # Exponential backoff

                # Check for Retry-After header
                retry_after = e.response.headers.get("Retry-After")
                if retry_after:
                    try:
                        wait_time = max(wait_time, int(retry_after))
                    except ValueError:
                        pass

                logger.warning(
                    "Rate limit hit in legacy fallback - retrying",
                    attempt=attempt + 1,
                    max_retries=max_retries,
                    wait_seconds=wait_time,
                )

                if attempt < max_retries - 1:
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    # All retries exhausted
                    return {
                        "success": False,
                        "error": "AI servisi şu an yoğun. Lütfen 1-2 dakika bekleyip tekrar deneyin.",
                        "error_code": "RATE_LIMIT",
                        "retry_after": 60,
                    }
            else:
                # Other HTTP error
                return {
                    "success": False,
                    "error": f"API hatası: {e.response.status_code}",
                }

        except httpx.TimeoutException:
            logger.warning("Timeout in legacy fallback", attempt=attempt + 1)
            if attempt < max_retries - 1:
                await asyncio.sleep(5)
                continue
            return {
                "success": False,
                "error": "İstek zaman aşımına uğradı. Lütfen tekrar deneyin.",
                "error_code": "TIMEOUT",
            }

        except Exception as e:
            logger.exception("Unexpected error in legacy fallback", error=str(e))
            return {
                "success": False,
                "error": f"Beklenmeyen hata: {str(e)}",
            }

    # Should not reach here, but just in case
    return {
        "success": False,
        "error": "Hikaye oluşturulamadı. Lütfen tekrar deneyin.",
    }


class TestFaceAnalysisRequest(BaseModel):
    """Test face analysis request."""

    photo_url: str = Field(..., description="URL to child's photo")
    child_name: str = "Test"
    child_age: int = 7
    child_gender: str = "erkek"  # "erkek" | "kiz"


@router.post("/test-face-analysis")
async def test_face_analysis(request: TestFaceAnalysisRequest, admin: AdminUser) -> dict:
    """
    Test the Forensic Face Analysis Service.

    Analyzes a child's photo and returns a detailed description optimized
    for AI image generation with maximum facial likeness.

    This is the key to improving facial resemblance in generated images.

    Returns:
        - basic_description: Simple description (old method)
        - forensic_description: Detailed forensic analysis (new method)
        - enhanced_description: Combined description for prompts
    """
    import structlog

    from app.services.ai.face_analyzer_service import get_face_analyzer

    logger = structlog.get_logger()

    # Basic description (old method)
    gender_word = (
        "boy"
        if request.child_gender == "erkek"
        else "girl"
        if request.child_gender == "kiz"
        else "child"
    )
    basic_description = f"a {request.child_age} year old {gender_word} named {request.child_name}"

    try:
        logger.info("Testing face analysis", photo_url=request.photo_url[:100])

        face_analyzer = get_face_analyzer()

        # Get forensic analysis
        forensic_description = await face_analyzer.analyze_face(
            image_source=request.photo_url,
            child_age=request.child_age,
            child_gender=request.child_gender,
        )

        # Get enhanced description (full)
        enhanced_description = await face_analyzer.get_enhanced_child_description(
            image_source=request.photo_url,
            child_name=request.child_name,
            child_age=request.child_age,
            child_gender=request.child_gender,
        )

        return {
            "success": True,
            "basic_description": basic_description,
            "basic_word_count": len(basic_description.split()),
            "forensic_description": forensic_description,
            "forensic_word_count": len(forensic_description.split()),
            "enhanced_description": enhanced_description,
            "enhanced_word_count": len(enhanced_description.split()),
            "improvement_factor": f"{len(enhanced_description.split()) / len(basic_description.split()):.1f}x more detail",
        }

    except Exception as e:
        logger.exception("Face analysis test failed", error=str(e))
        return {
            "success": False,
            "error": str(e),
            "basic_description": basic_description,
        }


class TestMultiViewFaceAnalysisRequest(BaseModel):
    """Test multi-view face analysis request."""

    photo_urls: list[str] = Field(
        ..., description="List of photo URLs (2-5 recommended)", min_length=1, max_length=5
    )
    child_name: str = "Test"
    child_age: int = 7
    child_gender: str = "erkek"  # "erkek" | "kiz"


@router.post("/test-face-analysis-multi")
async def test_multi_view_face_analysis(request: TestMultiViewFaceAnalysisRequest, admin: AdminUser) -> dict:
    """
    Test Multi-View Face Analysis (IMPROVED ACCURACY).

    Analyzes MULTIPLE photos of the same child to generate a more accurate
    and consistent facial description. Best results with 2-5 photos from
    different angles/lighting conditions.

    Benefits over single-photo analysis:
    - Confirms consistent features across photos
    - Reduces errors from lighting/angle variations
    - Captures features visible in different views

    Returns:
        - single_photo_description: Analysis from first photo only
        - multi_view_description: Combined analysis from all photos
        - comparison: Word count comparison
    """
    import structlog

    from app.services.ai.face_analyzer_service import get_face_analyzer

    logger = structlog.get_logger()

    gender_word = (
        "boy"
        if request.child_gender == "erkek"
        else "girl"
        if request.child_gender == "kiz"
        else "child"
    )
    basic_description = f"a {request.child_age} year old {gender_word} named {request.child_name}"

    try:
        logger.info(
            "Testing multi-view face analysis",
            photo_count=len(request.photo_urls),
        )

        face_analyzer = get_face_analyzer()

        # Single photo analysis (for comparison)
        single_description = await face_analyzer.analyze_face(
            image_source=request.photo_urls[0],
            child_age=request.child_age,
            child_gender=request.child_gender,
        )

        # Multi-view analysis
        multi_description = await face_analyzer.analyze_multiple_photos(
            image_sources=request.photo_urls,
            child_age=request.child_age,
            child_gender=request.child_gender,
        )

        # Enhanced multi-view description
        enhanced_multi = await face_analyzer.get_enhanced_child_description_multi(
            image_sources=request.photo_urls,
            child_name=request.child_name,
            child_age=request.child_age,
            child_gender=request.child_gender,
        )

        return {
            "success": True,
            "photo_count": len(request.photo_urls),
            "basic_description": basic_description,
            "single_photo_description": single_description,
            "single_photo_word_count": len(single_description.split()),
            "multi_view_description": multi_description,
            "multi_view_word_count": len(multi_description.split()),
            "enhanced_multi_description": enhanced_multi,
            "enhanced_word_count": len(enhanced_multi.split()),
            "improvement": f"Multi-view provides {len(multi_description.split()) - len(single_description.split())} more words of detail",
        }

    except Exception as e:
        logger.exception("Multi-view face analysis test failed", error=str(e))
        return {
            "success": False,
            "error": str(e),
            "photo_count": len(request.photo_urls),
        }


@router.post("/test-image")
async def test_image_generation(request: TestImageRequest, admin: AdminUser):
    """
    Test Gemini Imagen generation.
    Returns the generated image directly.
    """
    import httpx

    from app.config import settings
    from app.prompt_engine import compose_visual_prompt

    full_prompt, _ = compose_visual_prompt(
        f"{request.prompt}, {request.style}",
        template_vars=None,
        is_cover=False,
        style_text="",
        style_negative="",
    )
    try:
        # Try Imagen 3 first
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/imagen-3.0-generate-002:predict?key={settings.gemini_api_key}",
                json={
                    "instances": [{"prompt": full_prompt}],
                    "parameters": {
                        "sampleCount": 1,
                        "aspectRatio": "1:1",
                        "safetyFilterLevel": "block_some",
                    },
                },
            )

            if response.status_code == 200:
                data = response.json()
                if "predictions" in data and len(data["predictions"]) > 0:
                    image_b64 = data["predictions"][0].get("bytesBase64Encoded")
                    if image_b64:
                        image_bytes = base64.b64decode(image_b64)
                        return Response(
                            content=image_bytes,
                            media_type="image/png",
                            headers={"Content-Disposition": "inline; filename=generated.png"},
                        )

            # If Imagen fails, return error info
            return {
                "success": False,
                "error": f"Imagen API returned {response.status_code}",
                "details": response.text[:500],
                "note": "Imagen 3 requires billing enabled on Google Cloud. Try Gemini 2.0 Flash instead.",
            }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }


@router.post("/test-image-flash")
async def test_image_generation_flash(request: TestImageRequest, db: DbSession, admin: AdminUser):
    """
    Test image generation with Gemini 2.0 Flash.

    Model: gemini-2.5-flash-preview-image-generation
    Uses the MODULAR IMAGE GENERATOR (Strategy Pattern).

    Supports dynamic resolution:
    - If product_id provided: uses product's template dimensions
    - If page_width_mm/page_height_mm provided: uses those dimensions
    - Otherwise: uses default 1024x1024
    """

    from app.models.book_template import PageTemplate
    from app.models.product import Product

    # Yatay A4 varsayılan boyut
    from app.utils.resolution_calc import (
        DEFAULT_GENERATION_A4_LANDSCAPE,
        calculate_generation_params_from_mm,
        resize_image_bytes_to_target,
    )
    width, height = DEFAULT_GENERATION_A4_LANDSCAPE
    target_width = None
    target_height = None

    try:
        # Option 1: Use product's template
        if request.product_id:
            import structlog

            logger = structlog.get_logger()
            logger.info(f"Looking up product: {request.product_id}")

            product = await db.get(Product, UUID(request.product_id))
            if product:
                logger.info(
                    f"Found product: {product.name}, inner_template_id={product.inner_template_id}"
                )
                if product.inner_template_id:
                    template = await db.get(PageTemplate, product.inner_template_id)
                    if template:
                        logger.info(
                            f"Found template: {template.page_width_mm}x{template.page_height_mm}mm, bleed={template.bleed_mm}mm"
                        )
                        from app.utils.resolution_calc import get_effective_generation_params
                        params = get_effective_generation_params(template)
                        width = params["generation_width"]
                        height = params["generation_height"]
                        target_width = params["target_width"]
                        target_height = params["target_height"]
                        logger.info(
                            f"Calculated params: gen={width}x{height}, target={target_width}x{target_height}"
                        )
                    else:
                        logger.warning(f"Template not found for id: {product.inner_template_id}")
                else:
                    logger.warning("Product has no inner_template_id")
            else:
                logger.warning(f"Product not found: {request.product_id}")

        # Option 2: Use provided dimensions (dikeyse yatay A4 zorla)
        elif request.page_width_mm and request.page_height_mm:
            from app.utils.resolution_calc import A4_LANDSCAPE_HEIGHT_MM, A4_LANDSCAPE_WIDTH_MM
            _pw = request.page_width_mm
            _ph = request.page_height_mm
            if _pw < _ph:
                _pw, _ph = A4_LANDSCAPE_WIDTH_MM, A4_LANDSCAPE_HEIGHT_MM
            params = calculate_generation_params_from_mm(
                _pw,
                _ph,
                request.bleed_mm,
            )
            width = params["generation_width"]
            height = params["generation_height"]
            target_width = params["target_width"]
            target_height = params["target_height"]

        # Generate image
        generator = get_image_generator(ImageProvider.GEMINI_FLASH)

        image_bytes = await generator.generate(
            prompt=request.prompt,
            style_prompt=request.style,
            width=width,
            height=height,
        )

        # Resize to target if we have target dimensions
        if target_width and target_height:
            image_bytes = resize_image_bytes_to_target(
                image_bytes,
                target_width,
                target_height,
            )

        return Response(
            content=image_bytes,
            media_type="image/png",
            headers={
                "Content-Disposition": "inline; filename=generated.png",
                "X-Provider": generator.provider_name,
                "X-Target-Width": str(target_width or width),
                "X-Target-Height": str(target_height or height),
            },
        )

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "provider": "Gemini Flash (Modular Generator)",
        }


@router.post("/test-image-modular")
async def test_image_modular(
    request: TestImageRequest,
    admin: AdminUser,
    provider: str = "gemini_flash",
):
    """
    Test image generation with MODULAR GENERATOR.

    Supports multiple providers:
    - gemini_flash (default, fastest)
    - gemini (Imagen 3, higher quality)
    - fal (Fal.ai Flux - best for face consistency)

    Usage:
        POST /api/v1/ai/test-image-modular?provider=gemini_flash
        POST /api/v1/ai/test-image-modular?provider=fal

    Note: For face-consistent generation with Fal.ai, use /test-image-fal endpoint instead.
    """
    try:
        # Use string-based provider selection
        generator = get_image_generator(provider, with_face_consistency=False)

        from app.utils.resolution_calc import DEFAULT_GENERATION_A4_LANDSCAPE
        _w, _h = DEFAULT_GENERATION_A4_LANDSCAPE
        image_bytes = await generator.generate(
            prompt=request.prompt,
            style_prompt=request.style,
            width=_w,
            height=_h,
        )

        return Response(
            content=image_bytes,
            media_type="image/png",
            headers={
                "Content-Disposition": "inline; filename=generated.png",
                "X-Provider": generator.provider_name,
            },
        )

    except NotImplementedError as e:
        return {
            "success": False,
            "error": str(e),
            "note": "Bu provider henüz aktif değil",
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "provider": provider,
        }


# ============================================
# AUDIO / VOICE ENDPOINTS
# ============================================


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


@router.get("/system-voices", response_model=list[SystemVoiceInfo])
async def get_system_voices() -> list[SystemVoiceInfo]:
    """
    Get available system voices for audio book.
    """
    return [
        SystemVoiceInfo(
            id="female",
            name="Kadin Sesi",
            gender="female",
            description="Sicak ve yumusak bir kadin sesi",
        ),
        SystemVoiceInfo(
            id="male",
            name="Erkek Sesi",
            gender="male",
            description="Guvenilir ve sakin bir erkek sesi",
        ),
    ]


@router.post("/upload-voice-sample", response_model=VoiceSampleUploadResponse)
async def upload_voice_sample(request: VoiceSampleUploadRequest) -> VoiceSampleUploadResponse:
    """
    Upload a voice sample for cloning.
    Accepts base64 encoded audio (webm from browser recording or mp3).
    """
    import structlog

    from app.services.storage_service import storage_service

    logger = structlog.get_logger()

    try:
        order_id = request.order_id or "temp"
        sample_url, audio_bytes = storage_service.upload_voice_sample(
            audio_base64=request.audio_base64,
            order_id=order_id,
        )

        # Estimate duration (rough calculation for webm/mp3)
        # Average bitrate ~128kbps = 16KB/s
        duration_estimate = len(audio_bytes) / 16000

        logger.info(
            "Voice sample uploaded",
            sample_url=sample_url,
            size_bytes=len(audio_bytes),
            duration_estimate=duration_estimate,
        )

        return VoiceSampleUploadResponse(
            sample_url=sample_url,
            duration_seconds=duration_estimate,
            message="Ses ornegi basariyla yuklendi",
        )

    except Exception as e:
        logger.error("Voice sample upload failed", error=str(e))
        raise ValidationError(f"Ses ornegi yuklenemedi: {str(e)}")


@router.post("/clone-voice", response_model=CloneVoiceResponse)
async def clone_voice(request: CloneVoiceRequest, db: DbSession) -> CloneVoiceResponse:
    """
    Clone a voice from uploaded sample using ElevenLabs.
    """
    import httpx
    import structlog

    from app.services.ai.elevenlabs_service import ElevenLabsService

    logger = structlog.get_logger()
    elevenlabs = ElevenLabsService()

    try:
        # Download the audio sample
        async with httpx.AsyncClient() as client:
            response = await client.get(request.sample_url)
            response.raise_for_status()
            audio_bytes = response.content

        # Clone the voice
        voice_id = await elevenlabs.clone_voice(
            name=request.voice_name,
            audio_samples=[audio_bytes],
            description=f"Cloned voice for Benim Masalim - {request.voice_name}",
        )

        # If order_id provided, update the order
        if request.order_id:
            result = await db.execute(select(Order).where(Order.id == request.order_id))
            order = result.scalar_one_or_none()
            if order:
                order.audio_voice_id = voice_id
                order.audio_type = "cloned"
                await db.commit()

        logger.info(
            "Voice cloned successfully",
            voice_id=voice_id,
            voice_name=request.voice_name,
        )

        return CloneVoiceResponse(voice_id=voice_id, message="Ses basariyla klonlandi")

    except Exception as e:
        logger.error("Voice cloning failed", error=str(e))
        raise ValidationError(f"Ses klonlama basarisiz: {str(e)}")


@router.post("/clone-voice-direct", response_model=CloneVoiceResponse)
async def clone_voice_direct(request: CloneVoiceDirectRequest, db: DbSession) -> CloneVoiceResponse:
    """
    Clone a voice directly from base64 audio (without GCS upload).
    This is faster and doesn't require GCS credentials.
    """
    import base64

    import structlog

    from app.services.ai.elevenlabs_service import ElevenLabsService

    logger = structlog.get_logger()
    elevenlabs = ElevenLabsService()

    try:
        # Parse base64 data
        audio_base64 = request.audio_base64
        if "," in audio_base64:
            # Data URL format: data:audio/webm;base64,XXXXX
            audio_base64 = audio_base64.split(",", 1)[1]

        audio_bytes = base64.b64decode(audio_base64)

        logger.info(
            "Starting direct voice cloning",
            voice_name=request.voice_name,
            audio_size=len(audio_bytes),
        )

        # Clone the voice
        voice_id = await elevenlabs.clone_voice(
            name=request.voice_name,
            audio_samples=[audio_bytes],
            description=f"Cloned voice for Benim Masalim - {request.voice_name}",
        )

        # If order_id provided, update the order
        if request.order_id:
            result = await db.execute(select(Order).where(Order.id == request.order_id))
            order = result.scalar_one_or_none()
            if order:
                order.audio_voice_id = voice_id
                order.audio_type = "cloned"
                await db.commit()

        logger.info(
            "Voice cloned successfully (direct)",
            voice_id=voice_id,
            voice_name=request.voice_name,
        )

        return CloneVoiceResponse(voice_id=voice_id, message="Ses basariyla klonlandi")

    except Exception as e:
        logger.error("Direct voice cloning failed", error=str(e))
        raise ValidationError(f"Ses klonlama basarisiz: {str(e)}")


@router.post("/preview-system-voice")
async def preview_system_voice(request: PreviewVoiceRequest) -> Response:
    """
    Preview a system voice with sample text.
    Returns audio/mpeg (MP3) directly.
    """
    import structlog

    from app.services.ai.elevenlabs_service import ElevenLabsService

    logger = structlog.get_logger()
    elevenlabs = ElevenLabsService()

    try:
        # Limit preview text length
        preview_text = request.text[:200] if len(request.text) > 200 else request.text

        # Determine if it's a system voice or custom voice_id
        if request.voice_type in ("female", "male"):
            audio_bytes = await elevenlabs.text_to_speech(
                text=preview_text,
                voice_type=request.voice_type,
            )
        else:
            # Custom voice_id
            audio_bytes = await elevenlabs.text_to_speech(
                text=preview_text,
                voice_id=request.voice_type,
            )

        logger.info(
            "Voice preview generated",
            voice_type=request.voice_type,
            text_length=len(preview_text),
            audio_size=len(audio_bytes),
        )

        return Response(
            content=audio_bytes,
            media_type="audio/mpeg",
            headers={"Content-Disposition": "inline; filename=preview.mp3"},
        )

    except Exception as e:
        logger.error("Voice preview failed", error=str(e))
        raise ValidationError(f"Ses onizleme basarisiz: {str(e)}")


# ─── Outfit Suggestion Endpoint ──────────────────────────────────────


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


async def _auto_outfit_for_story(
    scenario_name: str,
    child_age: int,
    child_gender: str,
) -> str:
    """Pick ONE outfit for the child based on scenario, age, gender. Uses Gemini, falls back to default."""
    import httpx

    from app.config import settings
    from app.prompt_engine import normalize_clothing_description

    gender_en = (
        "boy" if (child_gender or "").strip().lower() in ("erkek", "boy", "male") else "girl"
    )
    prompt = (
        f"You are a children's book illustrator. Pick ONE outfit for a {child_age}-year-old {gender_en} "
        f"in a '{scenario_name}' themed storybook.\n\n"
        f"RULES:\n- Return exactly ONE outfit as a short English string.\n"
        f"- Include: top, bottom, footwear (e.g. 'red jacket, blue pants, white sneakers').\n"
        f"- Match the story theme (Kapadokya = adventure/sturdy, space = playful, etc.).\n"
        f"- Child-appropriate ONLY.\n- Return ONLY the outfit string, no quotes, no JSON."
    )
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"
                f"?key={settings.gemini_api_key}",
                json={
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {"temperature": 0.8, "maxOutputTokens": 128},
                },
            )
            resp.raise_for_status()
            data = resp.json()
            candidates = data.get("candidates") or [{}]
            first_candidate = candidates[0] if candidates else {}
            content = first_candidate.get("content", {})
            parts = content.get("parts") or [{}]
            first_part = parts[0] if parts else {}
            text = (first_part.get("text") or "").strip()
            if text and len(text) < 120:
                return normalize_clothing_description(text)
    except Exception as e:
        import structlog

        structlog.get_logger().warning("auto_outfit_failed", error=str(e))
    if gender_en == "girl":
        return "a colorful adventure dress and comfortable sneakers"
    return "an adventure jacket with comfortable pants and sneakers"


# Pre-defined fallback outfits per gender (English)
_FALLBACK_OUTFITS_BOY = [
    "blue jacket, gray pants, white sneakers",
    "red hooded sweatshirt, dark blue jeans, black sneakers",
    "green windbreaker, khaki cargo pants, brown boots",
    "yellow raincoat, navy blue pants, red rain boots",
    "orange fleece jacket, black sweatpants, gray sneakers",
    "white t-shirt, blue shorts, colorful sneakers",
]

_FALLBACK_OUTFITS_GIRL = [
    "pink jacket, navy blue leggings, white sneakers",
    "purple hooded sweatshirt, jeans, pink sneakers",
    "red windbreaker, black leggings, white boots",
    "turquoise raincoat, gray pants, yellow rain boots",
    "lilac fleece jacket, purple sweatpants, white sneakers",
    "white t-shirt, floral skirt, colorful sneakers",
]

_FALLBACK_OUTFITS_NEUTRAL = [
    "green jacket, black pants, white sneakers",
    "orange hooded sweatshirt, gray pants, black sneakers",
    "blue windbreaker, dark pants, brown boots",
    "yellow raincoat, navy blue pants, red rain boots",
    "red fleece jacket, black sweatpants, gray sneakers",
    "white t-shirt, blue shorts, colorful sneakers",
]


@router.post("/suggest-outfits", response_model=SuggestOutfitsResponse)
async def suggest_outfits(
    request: SuggestOutfitsRequest,
    db: DbSession,
) -> SuggestOutfitsResponse:
    """
    Generate 6 AI-powered outfit suggestions based on child info, scenario & style.
    Falls back to pre-defined outfits if Gemini call fails.
    """

    import structlog

    from app.config import settings
    from app.models.scenario import Scenario

    logger = structlog.get_logger()

    # --- Resolve scenario name for context ---
    scenario_name = "macera"
    if request.scenario_id:
        try:
            scenario_obj = await db.get(Scenario, UUID(request.scenario_id))
            if scenario_obj:
                scenario_name = scenario_obj.name or "macera"
        except Exception:
            pass

    # --- Resolve visual style name for context ---
    style_hint = ""
    if request.visual_style_id:
        try:
            from app.models.scenario import VisualStyle

            vs = await db.get(VisualStyle, UUID(request.visual_style_id))
            if vs:
                style_hint = f" Görsel stil: {vs.name or ''}."
        except Exception:
            pass

    # --- Gender label ---
    gender_en = (
        "boy"
        if request.child_gender == "erkek"
        else "girl"
        if request.child_gender == "kiz"
        else "child"
    )

    # --- Build prompt (English output for image generation compatibility) ---
    prompt = (
        f"You are a children's book illustrator. "
        f"Suggest outfit options for a {request.child_age}-year-old {gender_en} "
        f"in a '{scenario_name}' themed storybook.{style_hint}\n\n"
        f"RULES:\n"
        f"- Return exactly 6 different outfit suggestions.\n"
        f"- Each suggestion must include: top, bottom, footwear.\n"
        f"- Outfits must match the story theme (adventure = sturdy/comfortable, princess = elegant, etc.).\n"
        f"- Child-appropriate clothing ONLY (no bikini, underwear, lingerie).\n"
        f"- Each suggestion in ENGLISH, short and clear.\n"
        f"- Return ONLY a JSON array, no other text.\n\n"
        f'Example: ["red jacket, blue pants, white sneakers", ...]\n\n'
        f"Generate 6 suggestions now:"
    )

    # --- Try Gemini ---
    try:
        import json

        import httpx

        api_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"

        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 0.9,
                "maxOutputTokens": 1024,
            },
        }

        async with httpx.AsyncClient(timeout=45.0) as client:
            resp = await client.post(
                f"{api_url}?key={settings.gemini_api_key}",
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()

        # Extract text from Gemini response
        text = data["candidates"][0]["content"]["parts"][0]["text"]

        # Parse JSON array from response (strip markdown fences if present)
        text = text.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1] if "\n" in text else text[3:]
            if text.endswith("```"):
                text = text[:-3]
            text = text.strip()
            # Handle ```json prefix
            if text.startswith("json"):
                text = text[4:].strip()

        outfits = json.loads(text)

        if isinstance(outfits, list) and len(outfits) >= 6:
            from app.prompt_engine import normalize_clothing_description

            # Normalize any stray Turkish words in AI output
            clean: list[str] = [
                normalize_clothing_description(str(o)) for o in outfits[:6] if str(o).strip()
            ]
            if len(clean) >= 6:
                logger.info("AI outfit suggestions generated", count=len(clean))
                return SuggestOutfitsResponse(outfits=clean[:6])

    except Exception as e:
        logger.warning("AI outfit suggestion failed, using fallbacks", error=str(e))

    # --- Fallback (English) ---
    if request.child_gender == "erkek":
        fallback = _FALLBACK_OUTFITS_BOY
    elif request.child_gender == "kiz":
        fallback = _FALLBACK_OUTFITS_GIRL
    else:
        fallback = _FALLBACK_OUTFITS_NEUTRAL

    return SuggestOutfitsResponse(outfits=fallback)

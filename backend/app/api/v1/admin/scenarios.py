"""Admin scenarios management endpoints.

Scenarios are PURE CONTENT - story templates and illustrations.
Marketing/pricing fields have been moved to the Product model.

Prompt Templates:
- cover_prompt_template: For book covers (vertical, poster-style, title area)
- page_prompt_template: For inner pages (horizontal, text overlay space)
"""

from datetime import datetime
from uuid import UUID

import structlog
from fastapi import APIRouter, Query
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import select

from app.api.v1.deps import DbSession, SuperAdminUser
from app.core.exceptions import ConflictError, NotFoundError
from app.models.scenario import DEFAULT_COVER_TEMPLATE, DEFAULT_PAGE_TEMPLATE, Scenario
from app.services.storage_service import StorageService

logger = structlog.get_logger()
router = APIRouter()
storage_service = StorageService()

_URL_PREFIXES = ("http://", "https://", "/")


def _to_uuid(val: str | None) -> UUID | None:
    """Safely convert a string to UUID; return None on failure."""
    if not val:
        return None
    try:
        return UUID(str(val))
    except (ValueError, AttributeError):
        return None


def _is_base64(s: str) -> bool:
    """True if the string looks like base64 / data-URL (not a proper HTTP URL)."""
    return s.startswith("data:") or (len(s) > 500 and not s.startswith(_URL_PREFIXES))


def _upload_gallery_images(images: list[str] | None, scenario_name: str = "") -> list[str]:
    """Upload base64 gallery images to GCS and return list of URLs.

    Already-uploaded URLs are kept as-is.
    """
    if not images:
        return []
    result: list[str] = []
    for idx, img in enumerate(images):
        if not img:
            continue
        if _is_base64(img):
            try:
                url = storage_service.upload_base64_image(
                    base64_data=img,
                    folder="scenarios/gallery",
                )
                if url:
                    result.append(url)
                    logger.info("Gallery image uploaded to GCS", scenario=scenario_name, index=idx)
                    continue
            except Exception as e:
                logger.error("Gallery image upload failed", index=idx, error=str(e))
                continue
        elif img.startswith(_URL_PREFIXES):
            result.append(img)
    return result


def _safe_gallery(images: list | None) -> list[str]:
    """Filter gallery_images for response — strip any remaining base64 data."""
    if not images:
        return []
    return [img for img in images if isinstance(img, str) and img.startswith(_URL_PREFIXES)]


# ============ PYDANTIC SCHEMAS ============


class CustomInputFieldSchema(BaseModel):
    """Schema for custom input field definition."""

    key: str = Field(..., description="Variable key used in templates, e.g., spaceship_name")
    label: str = Field(..., description="Display label for users, e.g., Uzay Gemisi Adı")
    type: str = Field(default="text", description="Input type: text, number, select, textarea")
    default: str | None = None
    options: list[str] | None = Field(default=None, description="Options for select type")
    required: bool = True
    placeholder: str | None = None
    help_text: str | None = None


class ScenarioCreate(BaseModel):
    """Create scenario request with specialized prompt templates."""

    # Basic Info
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    thumbnail_url: str = Field(default="/img/default-scenario.jpg")
    thumbnail_base64: str | None = None  # Base64 encoded image

    # Prompt Templates
    cover_prompt_template: str = Field(
        default=DEFAULT_COVER_TEMPLATE,
        description="Template for book cover. Variables: {book_title}, {child_name}, {child_description}, {visual_style}",
    )
    page_prompt_template: str = Field(
        default=DEFAULT_PAGE_TEMPLATE,
        description="Template for inner pages. Variables: {child_name}, {child_description}, {visual_style}, {scene_description}",
    )

    # AI Story Generation Template (legacy — prefer story_prompt_tr)
    ai_prompt_template: str | None = Field(
        default=None,
        description="Template for AI story text generation (Gemini). Variables: {child_name}, {child_age}, {child_gender}, {outcomes}, plus custom inputs",
    )

    # V2 Fields
    story_prompt_tr: str | None = Field(
        default=None,
        description="V2: Turkish story-writing prompt for Gemini PASS-1 (replaces ai_prompt_template)",
    )
    location_en: str | None = Field(
        default=None, max_length=100, description="V2: English location tag (e.g. 'Cappadocia')"
    )
    flags: dict | None = Field(
        default=None, description='V2: Flexible flags JSON (e.g. {"no_family": true})'
    )
    default_page_count: int | None = Field(default=6, description="V2: Default story page count")

    # Dynamic Variables / Custom Inputs
    custom_inputs_schema: list[CustomInputFieldSchema] | None = Field(
        default=None,
        description="Custom input fields for this scenario that users fill during story creation",
    )

    # Media Assets (gallery for content preview)
    gallery_images: list[str] | None = Field(
        default=None, description="List of image URLs for content carousel"
    )

    # ============ MARKETING FIELDS ============
    marketing_video_url: str | None = Field(
        default=None, description="YouTube embed or direct video URL for scenario marketing"
    )
    marketing_gallery: list[str] | None = Field(
        default=None, description="Marketing gallery image URLs (separate from content gallery)"
    )
    marketing_price_label: str | None = Field(
        default=None, description="Display price label e.g. '299 TL'den başlayan fiyatlarla'"
    )
    marketing_features: list[str] | None = Field(
        default=None, description="Feature bullet points for scenario product cards"
    )
    marketing_badge: str | None = Field(
        default=None, description="Promo badge text e.g. 'Yeni!', 'En Çok Tercih Edilen'"
    )
    age_range: str | None = Field(default=None, description="Target age range e.g. '3-8 yaş'")
    estimated_duration: str | None = Field(
        default=None, description="Estimated duration e.g. '15 dakika'"
    )
    tagline: str | None = Field(default=None, description="Short tagline for scenario cards")
    rating: float | None = Field(default=None, ge=0, le=5, description="Rating score (0-5)")
    review_count: int | None = Field(default=None, ge=0, description="Number of reviews")

    # ============ PRODUCT LINK & OVERRIDE SETTINGS ============
    linked_product_id: str | None = Field(
        default=None, description="Base product UUID whose settings this scenario inherits"
    )
    price_override_base: float | None = Field(
        default=None, description="Override Product.base_price for this scenario"
    )
    price_override_extra_page: float | None = Field(
        default=None, description="Override Product.extra_page_price for this scenario"
    )
    cover_template_id_override: str | None = Field(
        default=None, description="Override Product.cover_template_id for this scenario"
    )
    inner_template_id_override: str | None = Field(
        default=None, description="Override Product.inner_template_id for this scenario"
    )
    back_template_id_override: str | None = Field(
        default=None, description="Override Product.back_template_id for this scenario"
    )
    ai_config_id_override: str | None = Field(
        default=None, description="Override Product.ai_config_id for this scenario"
    )
    paper_type_override: str | None = Field(
        default=None, description="Override Product.paper_type (e.g. 'Kuşe 200gr')"
    )
    paper_finish_override: str | None = Field(
        default=None, description="Override Product.paper_finish (e.g. 'Parlak')"
    )
    cover_type_override: str | None = Field(
        default=None, description="Override Product.cover_type (e.g. 'Yumuşak Kapak')"
    )
    lamination_override: str | None = Field(
        default=None, description="Override Product.lamination"
    )
    orientation_override: str | None = Field(
        default=None, description="Override Product.orientation ('portrait' or 'landscape')"
    )
    min_page_count_override: int | None = Field(
        default=None, description="Override Product.min_page_count"
    )
    max_page_count_override: int | None = Field(
        default=None, description="Override Product.max_page_count"
    )

    # ============ BOOK STRUCTURE (marketing display) ============
    story_page_count: int | None = Field(
        default=None, description="AI-generated story pages shown to customer (e.g. 22)"
    )
    cover_count: int | None = Field(
        default=2, description="Number of cover pages (front + back, default 2)"
    )
    greeting_page_count: int | None = Field(
        default=2, description="Number of karşılama/greeting pages (default 2)"
    )
    back_info_page_count: int | None = Field(
        default=1, description="Number of back-info pages (default 1)"
    )

    # ============ OUTFIT DESIGN (scenario-specific, gender-specific) ============
    outfit_girl: str | None = Field(
        default=None, description="Outfit description for girl characters (English, for AI prompts)"
    )
    outfit_boy: str | None = Field(
        default=None, description="Outfit description for boy characters (English, for AI prompts)"
    )

    # Display Settings
    is_active: bool = True
    display_order: int = 0

    @field_validator("gallery_images", mode="before")
    @classmethod
    def ensure_list(cls, v):
        """Ensure JSONB fields are lists."""
        if v is None:
            return []
        if isinstance(v, str):
            return [v]
        return list(v)

    @field_validator("custom_inputs_schema", mode="before")
    @classmethod
    def validate_custom_inputs(cls, v):
        """Ensure custom_inputs_schema is a list of dicts."""
        if v is None:
            return []
        return v


class ScenarioUpdate(BaseModel):
    """Update scenario request with specialized prompt templates."""

    # Basic Info
    name: str | None = None
    description: str | None = None
    thumbnail_url: str | None = None
    thumbnail_base64: str | None = None

    # Prompt Templates (legacy)
    cover_prompt_template: str | None = None
    page_prompt_template: str | None = None
    ai_prompt_template: str | None = None

    # V2 Fields
    story_prompt_tr: str | None = None
    location_en: str | None = None
    flags: dict | None = None
    default_page_count: int | None = None

    # Dynamic Variables / Custom Inputs
    custom_inputs_schema: list[CustomInputFieldSchema] | None = None

    # Media Assets
    gallery_images: list[str] | None = None

    # ============ MARKETING FIELDS ============
    marketing_video_url: str | None = None
    marketing_gallery: list[str] | None = None
    marketing_price_label: str | None = None
    marketing_features: list[str] | None = None
    marketing_badge: str | None = None
    age_range: str | None = None
    estimated_duration: str | None = None
    tagline: str | None = None
    rating: float | None = None
    review_count: int | None = None

    # ============ PRODUCT LINK & OVERRIDE SETTINGS ============
    linked_product_id: str | None = None
    price_override_base: float | None = None
    price_override_extra_page: float | None = None
    cover_template_id_override: str | None = None
    inner_template_id_override: str | None = None
    back_template_id_override: str | None = None
    ai_config_id_override: str | None = None
    paper_type_override: str | None = None
    paper_finish_override: str | None = None
    cover_type_override: str | None = None
    lamination_override: str | None = None
    orientation_override: str | None = None
    min_page_count_override: int | None = None
    max_page_count_override: int | None = None

    # ============ BOOK STRUCTURE (marketing display) ============
    story_page_count: int | None = None
    cover_count: int | None = None
    greeting_page_count: int | None = None
    back_info_page_count: int | None = None

    # ============ OUTFIT DESIGN (scenario-specific, gender-specific) ============
    outfit_girl: str | None = None
    outfit_boy: str | None = None

    # Display Settings
    is_active: bool | None = None
    display_order: int | None = None


class ScenarioResponse(BaseModel):
    """Scenario response with prompt templates."""

    id: str
    name: str
    description: str | None
    thumbnail_url: str

    # Prompt Templates (legacy)
    cover_prompt_template: str
    page_prompt_template: str
    ai_prompt_template: str | None = None

    # V2 Fields
    story_prompt_tr: str | None = None
    location_en: str | None = None
    flags: dict | None = None
    default_page_count: int | None = None

    # Dynamic Variables / Custom Inputs
    custom_inputs_schema: list[dict] | None = None
    available_variables: list[str] | None = None

    # Media
    gallery_images: list[str]

    # Marketing Fields
    marketing_video_url: str | None = None
    marketing_gallery: list[str] | None = None
    marketing_price_label: str | None = None
    marketing_features: list[str] | None = None
    marketing_badge: str | None = None
    age_range: str | None = None
    estimated_duration: str | None = None
    tagline: str | None = None
    rating: float | None = None
    review_count: int | None = None

    # Product Link & Override Settings
    linked_product_id: str | None = None
    linked_product_name: str | None = None  # denormalized for display
    price_override_base: float | None = None
    price_override_extra_page: float | None = None
    cover_template_id_override: str | None = None
    inner_template_id_override: str | None = None
    back_template_id_override: str | None = None
    ai_config_id_override: str | None = None
    paper_type_override: str | None = None
    paper_finish_override: str | None = None
    cover_type_override: str | None = None
    lamination_override: str | None = None
    orientation_override: str | None = None
    min_page_count_override: int | None = None
    max_page_count_override: int | None = None

    # Book Structure (marketing display)
    story_page_count: int | None = None
    cover_count: int | None = None
    greeting_page_count: int | None = None
    back_info_page_count: int | None = None
    total_page_count: int | None = None  # computed

    # Outfit Design (scenario-specific, gender-specific)
    outfit_girl: str | None = None
    outfit_boy: str | None = None

    # Display
    is_active: bool
    display_order: int

    # Timestamps
    created_at: datetime | None = None
    updated_at: datetime | None = None

    class Config:
        from_attributes = True


def scenario_to_response(scenario: Scenario) -> dict:
    """Convert Scenario model to response dict.

    IMPORTANT: gallery_images is filtered through _safe_gallery to ensure
    no base64 data leaks into the response (can be 30MB+ per scenario).
    """
    thumb = scenario.thumbnail_url
    if thumb and _is_base64(thumb):
        thumb = ""  # Don't send base64 thumbnails in response

    return {
        "id": str(scenario.id),
        "name": scenario.name,
        "description": scenario.description,
        "thumbnail_url": thumb,
        # Prompt Templates (legacy)
        "cover_prompt_template": scenario.cover_prompt_template,
        "page_prompt_template": scenario.page_prompt_template,
        "ai_prompt_template": scenario.ai_prompt_template,
        # V2 Fields
        "story_prompt_tr": getattr(scenario, "story_prompt_tr", None),
        "location_en": getattr(scenario, "location_en", None),
        "flags": getattr(scenario, "flags", None) or {},
        "default_page_count": getattr(scenario, "default_page_count", 6),
        # Dynamic Variables / Custom Inputs
        "custom_inputs_schema": scenario.custom_inputs_schema or [],
        "available_variables": scenario.get_available_variables(),
        # Media — FILTERED: no base64 data in responses
        "gallery_images": _safe_gallery(scenario.gallery_images),
        # Marketing Fields
        "marketing_video_url": getattr(scenario, "marketing_video_url", None),
        "marketing_gallery": _safe_gallery(getattr(scenario, "marketing_gallery", None) or []),
        "marketing_price_label": getattr(scenario, "marketing_price_label", None),
        "marketing_features": getattr(scenario, "marketing_features", None) or [],
        "marketing_badge": getattr(scenario, "marketing_badge", None),
        "age_range": getattr(scenario, "age_range", None),
        "estimated_duration": getattr(scenario, "estimated_duration", None),
        "tagline": getattr(scenario, "tagline", None),
        "rating": getattr(scenario, "rating", None),
        "review_count": getattr(scenario, "review_count", 0),
        # Product Link & Override Settings
        "linked_product_id": str(scenario.linked_product_id) if getattr(scenario, "linked_product_id", None) else None,
        "linked_product_name": scenario.linked_product.name if getattr(scenario, "linked_product", None) else None,
        "price_override_base": float(scenario.price_override_base) if getattr(scenario, "price_override_base", None) is not None else None,
        "price_override_extra_page": float(scenario.price_override_extra_page) if getattr(scenario, "price_override_extra_page", None) is not None else None,
        "cover_template_id_override": getattr(scenario, "cover_template_id_override", None),
        "inner_template_id_override": getattr(scenario, "inner_template_id_override", None),
        "back_template_id_override": getattr(scenario, "back_template_id_override", None),
        "ai_config_id_override": getattr(scenario, "ai_config_id_override", None),
        "paper_type_override": getattr(scenario, "paper_type_override", None),
        "paper_finish_override": getattr(scenario, "paper_finish_override", None),
        "cover_type_override": getattr(scenario, "cover_type_override", None),
        "lamination_override": getattr(scenario, "lamination_override", None),
        "orientation_override": getattr(scenario, "orientation_override", None),
        "min_page_count_override": getattr(scenario, "min_page_count_override", None),
        "max_page_count_override": getattr(scenario, "max_page_count_override", None),
        # Book Structure (marketing display)
        "story_page_count": getattr(scenario, "story_page_count", None),
        "cover_count": getattr(scenario, "cover_count", 2),
        "greeting_page_count": getattr(scenario, "greeting_page_count", 2),
        "back_info_page_count": getattr(scenario, "back_info_page_count", 1),
        "total_page_count": scenario.total_page_count,
        # Outfit Design
        "outfit_girl": getattr(scenario, "outfit_girl", None),
        "outfit_boy": getattr(scenario, "outfit_boy", None),
        # Display
        "is_active": scenario.is_active,
        "display_order": scenario.display_order,
        # Timestamps
        "created_at": scenario.created_at,
        "updated_at": scenario.updated_at,
    }


# ============ ENDPOINTS ============


@router.get("")
async def list_scenarios(
    db: DbSession,
    admin: SuperAdminUser,
    include_inactive: bool = False,
) -> list[dict]:
    """List all scenarios (admin view with full marketing data)."""
    query = select(Scenario).order_by(Scenario.display_order, Scenario.name)

    if not include_inactive:
        query = query.where(Scenario.is_active == True)

    result = await db.execute(query)
    scenarios = result.scalars().all()

    return [scenario_to_response(s) for s in scenarios]


@router.get("/{scenario_id}")
async def get_scenario(
    scenario_id: UUID,
    db: DbSession,
    admin: SuperAdminUser,
) -> dict:
    """Get a single scenario with full details."""
    result = await db.execute(select(Scenario).where(Scenario.id == scenario_id))
    scenario = result.scalar_one_or_none()

    if not scenario:
        raise NotFoundError("Senaryo", scenario_id)

    return scenario_to_response(scenario)


@router.post("")
async def create_scenario(
    request: ScenarioCreate,
    db: DbSession,
    admin: SuperAdminUser,
) -> dict:
    """Create a new scenario with marketing features."""
    # Check for duplicate name
    result = await db.execute(select(Scenario).where(Scenario.name == request.name))
    if result.scalar_one_or_none():
        raise ConflictError(f"'{request.name}' adında bir senaryo zaten var")

    thumbnail_url = request.thumbnail_url

    # Upload image if base64 provided
    if request.thumbnail_base64:
        logger.info("Uploading scenario image", base64_length=len(request.thumbnail_base64))
        try:
            uploaded_url = storage_service.upload_base64_image(
                base64_data=request.thumbnail_base64, folder="scenarios"
            )
            logger.info("Upload result", uploaded_url=uploaded_url)
            if uploaded_url:
                thumbnail_url = uploaded_url
        except Exception as e:
            logger.error("Failed to upload scenario image", error=str(e))

    # Convert custom_inputs_schema to list of dicts for JSONB storage
    custom_inputs_data = None
    if request.custom_inputs_schema:
        custom_inputs_data = [
            field.model_dump(exclude_none=True) for field in request.custom_inputs_schema
        ]

    # Upload base64 gallery images to GCS
    gallery_urls = _upload_gallery_images(request.gallery_images, request.name)

    # Upload base64 marketing gallery images to GCS
    marketing_gallery_urls = _upload_gallery_images(request.marketing_gallery, request.name)

    scenario = Scenario(
        # Basic Info
        name=request.name,
        description=request.description,
        thumbnail_url=thumbnail_url,
        # Prompt Templates (legacy)
        cover_prompt_template=request.cover_prompt_template,
        page_prompt_template=request.page_prompt_template,
        ai_prompt_template=request.ai_prompt_template,
        # V2 Fields
        story_prompt_tr=request.story_prompt_tr,
        location_en=request.location_en,
        flags=request.flags or {},
        default_page_count=request.default_page_count or 6,
        # Dynamic Variables / Custom Inputs
        custom_inputs_schema=custom_inputs_data or [],
        # Media — always store URLs, never base64
        gallery_images=gallery_urls,
        # Marketing Fields
        marketing_video_url=request.marketing_video_url,
        marketing_gallery=marketing_gallery_urls,
        marketing_price_label=request.marketing_price_label,
        marketing_features=request.marketing_features or [],
        marketing_badge=request.marketing_badge,
        age_range=request.age_range,
        estimated_duration=request.estimated_duration,
        tagline=request.tagline,
        rating=request.rating,
        review_count=request.review_count or 0,
        # Product Link & Override Settings
        linked_product_id=_to_uuid(request.linked_product_id),
        price_override_base=request.price_override_base,
        price_override_extra_page=request.price_override_extra_page,
        cover_template_id_override=request.cover_template_id_override,
        inner_template_id_override=request.inner_template_id_override,
        back_template_id_override=request.back_template_id_override,
        ai_config_id_override=request.ai_config_id_override,
        paper_type_override=request.paper_type_override,
        paper_finish_override=request.paper_finish_override,
        cover_type_override=request.cover_type_override,
        lamination_override=request.lamination_override,
        orientation_override=request.orientation_override,
        min_page_count_override=request.min_page_count_override,
        max_page_count_override=request.max_page_count_override,
        # Book Structure
        story_page_count=request.story_page_count,
        cover_count=request.cover_count if request.cover_count is not None else 2,
        greeting_page_count=request.greeting_page_count if request.greeting_page_count is not None else 2,
        back_info_page_count=request.back_info_page_count if request.back_info_page_count is not None else 1,
        # Outfit Design
        outfit_girl=request.outfit_girl,
        outfit_boy=request.outfit_boy,
        # Display
        is_active=request.is_active,
        display_order=request.display_order,
    )

    db.add(scenario)
    await db.commit()
    await db.refresh(scenario)

    logger.info(
        "Scenario created",
        scenario_id=str(scenario.id),
        name=scenario.name,
    )

    return {
        **scenario_to_response(scenario),
        "message": "Senaryo oluşturuldu",
    }


@router.patch("/{scenario_id}")
async def update_scenario(
    scenario_id: UUID,
    request: ScenarioUpdate,
    db: DbSession,
    admin: SuperAdminUser,
) -> dict:
    """Update a scenario with marketing features."""
    result = await db.execute(select(Scenario).where(Scenario.id == scenario_id))
    scenario = result.scalar_one_or_none()

    if not scenario:
        raise NotFoundError("Senaryo", scenario_id)

    # Check name conflict if changing
    if request.name and request.name != scenario.name:
        existing = await db.execute(select(Scenario).where(Scenario.name == request.name))
        if existing.scalar_one_or_none():
            raise ConflictError(f"'{request.name}' adında bir senaryo zaten var")

    # Upload image if base64 provided
    if request.thumbnail_base64:
        logger.info(
            "Uploading scenario image for update", base64_length=len(request.thumbnail_base64)
        )
        try:
            uploaded_url = storage_service.upload_base64_image(
                base64_data=request.thumbnail_base64, folder="scenarios"
            )
            logger.info("Upload result", uploaded_url=uploaded_url)
            if uploaded_url:
                scenario.thumbnail_url = uploaded_url
        except Exception as e:
            logger.error("Failed to upload scenario image", error=str(e))

    # Update fields (exclude thumbnail_base64 from direct assignment)
    update_data = request.model_dump(exclude_unset=True, exclude={"thumbnail_base64"})

    # Upload base64 gallery images to GCS before saving
    if "gallery_images" in update_data and update_data["gallery_images"]:
        update_data["gallery_images"] = _upload_gallery_images(
            update_data["gallery_images"], scenario.name
        )

    # Upload base64 marketing gallery images to GCS before saving
    if "marketing_gallery" in update_data and update_data["marketing_gallery"]:
        update_data["marketing_gallery"] = _upload_gallery_images(
            update_data["marketing_gallery"], scenario.name
        )

    # Convert custom_inputs_schema if present
    if "custom_inputs_schema" in update_data and update_data["custom_inputs_schema"]:
        update_data["custom_inputs_schema"] = [
            field if isinstance(field, dict) else field.model_dump(exclude_none=True)
            for field in update_data["custom_inputs_schema"]
        ]

    # Convert linked_product_id string → UUID
    if "linked_product_id" in update_data:
        update_data["linked_product_id"] = _to_uuid(update_data["linked_product_id"])

    for field, value in update_data.items():
        setattr(scenario, field, value)

    await db.commit()
    await db.refresh(scenario)

    logger.info(
        "Scenario updated",
        scenario_id=str(scenario.id),
        name=scenario.name,
        updated_fields=list(update_data.keys()),
    )

    return {
        **scenario_to_response(scenario),
        "message": "Senaryo güncellendi",
    }


@router.delete("/{scenario_id}")
async def delete_scenario(
    scenario_id: UUID,
    db: DbSession,
    admin: SuperAdminUser,
    hard_delete: bool = Query(default=True, description="Kalıcı olarak sil"),
) -> dict:
    """Delete a scenario (hard delete by default)."""
    result = await db.execute(select(Scenario).where(Scenario.id == scenario_id))
    scenario = result.scalar_one_or_none()

    if not scenario:
        raise NotFoundError("Senaryo", scenario_id)

    if hard_delete:
        # Hard delete - permanently remove from DB
        await db.delete(scenario)
        await db.commit()
        logger.info(
            "Scenario permanently deleted", scenario_id=str(scenario_id), name=scenario.name
        )
        return {"message": "Senaryo kalıcı olarak silindi"}
    else:
        # Soft delete - just set inactive
        scenario.is_active = False
        await db.commit()
        logger.info("Scenario soft-deleted", scenario_id=str(scenario_id))
        return {"message": "Senaryo pasife alındı"}


@router.post("/migrate-gallery-images")
async def migrate_gallery_images_to_gcs(
    db: DbSession,
    admin: SuperAdminUser,
) -> dict:
    """One-time migration: upload all base64 gallery images to GCS.

    Replaces inline base64 data in gallery_images JSONB with GCS URLs.
    Safe to run multiple times — already-uploaded URLs are skipped.
    """
    result = await db.execute(select(Scenario))
    scenarios = result.scalars().all()

    migrated = 0
    total_images_uploaded = 0

    for scenario in scenarios:
        changed = False

        # Migrate thumbnail if base64
        if scenario.thumbnail_url and _is_base64(scenario.thumbnail_url):
            try:
                url = storage_service.upload_base64_image(
                    base64_data=scenario.thumbnail_url, folder="scenarios"
                )
                if url:
                    scenario.thumbnail_url = url
                    changed = True
                    logger.info("Thumbnail migrated", scenario=scenario.name)
            except Exception as e:
                logger.error("Thumbnail migration failed", scenario=scenario.name, error=str(e))

        # Migrate gallery images
        raw = scenario.gallery_images or []
        has_base64 = any(_is_base64(img) for img in raw if isinstance(img, str))

        if has_base64:
            new_gallery = _upload_gallery_images(raw, scenario.name)
            scenario.gallery_images = new_gallery
            total_images_uploaded += len(new_gallery)
            changed = True
            logger.info(
                "Gallery migrated",
                scenario=scenario.name,
                before=len(raw),
                after=len(new_gallery),
            )

        if changed:
            migrated += 1

    if migrated:
        await db.commit()

    return {
        "scenarios_migrated": migrated,
        "total_images_uploaded": total_images_uploaded,
        "message": f"{migrated} senaryo galeri görselleri GCS'ye taşındı",
    }


@router.post("/{scenario_id}/duplicate")
async def duplicate_scenario(
    scenario_id: UUID,
    db: DbSession,
    admin: SuperAdminUser,
) -> dict:
    """Duplicate a scenario with a new name."""
    result = await db.execute(select(Scenario).where(Scenario.id == scenario_id))
    original = result.scalar_one_or_none()

    if not original:
        raise NotFoundError("Senaryo", scenario_id)

    # Generate unique name
    base_name = f"{original.name} (Kopya)"
    new_name = base_name
    counter = 1

    while True:
        existing = await db.execute(select(Scenario).where(Scenario.name == new_name))
        if not existing.scalar_one_or_none():
            break
        counter += 1
        new_name = f"{base_name} {counter}"

    # Create duplicate
    duplicate = Scenario(
        name=new_name,
        description=original.description,
        thumbnail_url=original.thumbnail_url,
        # Copy prompt templates (legacy)
        cover_prompt_template=original.cover_prompt_template,
        page_prompt_template=original.page_prompt_template,
        ai_prompt_template=original.ai_prompt_template,
        # V2 Fields
        story_prompt_tr=getattr(original, "story_prompt_tr", None),
        location_en=getattr(original, "location_en", None),
        flags=(getattr(original, "flags", None) or {}).copy(),
        default_page_count=getattr(original, "default_page_count", 6),
        # Copy custom inputs schema
        custom_inputs_schema=original.custom_inputs_schema.copy()
        if original.custom_inputs_schema
        else [],
        gallery_images=original.gallery_images.copy() if original.gallery_images else [],
        # Copy marketing fields
        marketing_video_url=getattr(original, "marketing_video_url", None),
        marketing_gallery=(getattr(original, "marketing_gallery", None) or []).copy(),
        marketing_price_label=getattr(original, "marketing_price_label", None),
        marketing_features=(getattr(original, "marketing_features", None) or []).copy(),
        marketing_badge=getattr(original, "marketing_badge", None),
        age_range=getattr(original, "age_range", None),
        estimated_duration=getattr(original, "estimated_duration", None),
        tagline=getattr(original, "tagline", None),
        rating=getattr(original, "rating", None),
        review_count=getattr(original, "review_count", 0),
        is_active=False,  # Start as draft
        display_order=original.display_order + 1,
    )

    db.add(duplicate)
    await db.commit()
    await db.refresh(duplicate)

    logger.info(
        "Scenario duplicated",
        original_id=str(scenario_id),
        duplicate_id=str(duplicate.id),
        new_name=new_name,
    )

    return {
        **scenario_to_response(duplicate),
        "message": f"Senaryo '{new_name}' olarak kopyalandı",
    }


@router.post("/scripts/update-amazon")
async def run_amazon_scenario_update(
    db: DbSession,
    _admin: SuperAdminUser,
) -> dict:
    """Run the Amazon Ormanları Keşfediyorum scenario update script."""
    try:
        # Import the constants from the script
        from scripts import update_amazon_scenario as amazon_script
        
        # Find or create the scenario
        result = await db.execute(
            select(Scenario).where(Scenario.name.ilike("%Amazon%Ormanlar%"))
        )
        scenario = result.scalar_one_or_none()
        
        if not scenario:
            logger.info("Creating new Amazon Ormanları scenario")
            scenario = Scenario(
                name="Amazon Ormanları Keşfediyorum",
                is_active=True
            )
            db.add(scenario)
        else:
            logger.info(f"Updating existing scenario: {scenario.name} (ID: {scenario.id})")
        
        # Update all fields
        scenario.description = "Dünyanın en zengin ekosistemi Amazon yağmur ormanlarında büyülü bir keşif! Renkli papağanlar, pembe nehir yunusları, ağaç tembelleri ve dev kapok ağaçları arasında biyolojik çeşitliliği keşfet. Yardımlaşma ve doğayı koruma değerlerini öğren."
        scenario.cover_prompt_template = amazon_script.AMAZON_COVER_PROMPT
        scenario.page_prompt_template = amazon_script.AMAZON_PAGE_PROMPT
        scenario.story_prompt_tr = amazon_script.AMAZON_STORY_PROMPT_TR
        scenario.ai_prompt_template = None
        scenario.location_en = "Amazon Rainforest"
        scenario.theme_key = "amazon_rainforest"
        scenario.cultural_elements = amazon_script.AMAZON_CULTURAL_ELEMENTS
        scenario.custom_inputs_schema = amazon_script.AMAZON_CUSTOM_INPUTS
        scenario.outfit_girl = amazon_script.OUTFIT_GIRL
        scenario.outfit_boy = amazon_script.OUTFIT_BOY
        scenario.default_page_count = 22
        scenario.display_order = 12
        
        await db.commit()
        await db.refresh(scenario)
        
        logger.info("Amazon scenario updated successfully", scenario_id=str(scenario.id))
        
        return {
            "status": "success",
            "message": "Amazon Ormanları senaryosu başarıyla güncellendi",
            "scenario_id": str(scenario.id),
            "name": scenario.name
        }
    except Exception as e:
        logger.error("Amazon scenario update failed", error=str(e))
        raise ConflictError(f"Script çalıştırılamadı: {str(e)}")

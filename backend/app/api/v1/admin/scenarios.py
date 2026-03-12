"""Admin scenarios management endpoints.

HYBRID ARCHITECTURE:
  - Technical content (prompts, outfits, companions, bible) lives in code
    via the Scenario Registry (`app.scenarios`).
  - Marketing/display fields (gallery, badge, tagline, pricing) live in the DB.
  - Admin can only edit DB-owned fields; code-managed fields are read-only.

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
from sqlalchemy.orm import selectinload

from app.api.v1.deps import DbSession, SuperAdminUser
from app.core.exceptions import ConflictError, NotFoundError
from app.models.product import Product
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


def _safe_get_variables(scenario) -> list[str]:
    """Safely get available variables — guards against malformed custom_inputs_schema in DB."""
    import json

    standard = [
        "book_title", "child_name", "child_age", "child_gender",
        "scene_description", "clothing_description", "visual_style",
    ]
    schema = scenario.custom_inputs_schema or []
    # Guard: if schema is a JSON string (malformed DB data), parse it
    if isinstance(schema, str):
        try:
            schema = json.loads(schema)
        except Exception:
            schema = []
    # Guard: if schema is not iterable, skip
    if not isinstance(schema, list):
        return standard
    custom = []
    for field in schema:
        if isinstance(field, dict):
            key = field.get("key")
            if key:
                custom.append(str(key))
        # Skip string or other non-dict elements gracefully
    return standard + custom


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

    @field_validator("options", mode="before")
    @classmethod
    def coerce_options(cls, v: object) -> list[str] | None:
        """Allow options stored as comma-separated string (legacy) or list."""
        if v is None:
            return None
        if isinstance(v, str):
            return [s.strip() for s in v.split(",") if s.strip()]
        return list(v)


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


# Fields managed by the code registry — admin cannot overwrite these
_CODE_MANAGED_FIELDS = frozenset({
    "story_prompt_tr", "cover_prompt_template", "page_prompt_template",
    "outfit_girl", "outfit_boy",
    "custom_inputs_schema", "location_en", "flags", "default_page_count",
})


def scenario_to_response(scenario: Scenario) -> dict:
    """Convert Scenario model to response dict.

    HYBRID: If the scenario has a code-registry entry, code-managed fields
    (prompts, outfits, companions, bible) are taken from the registry.
    Marketing/display fields always come from the DB.

    IMPORTANT: gallery_images is filtered through _safe_gallery to ensure
    no base64 data leaks into the response (can be 30MB+ per scenario).
    """
    from app.scenarios import get_scenario_content
    from app.services.scenario_health_service import score_scenario

    thumb = scenario.thumbnail_url
    if thumb and _is_base64(thumb):
        thumb = ""  # Don't send base64 thumbnails in response

    # Try to fetch code-managed content from the registry
    theme_key = getattr(scenario, "theme_key", None) or ""
    registry_content = get_scenario_content(theme_key) if theme_key else None

    # Health score (from registry content if available)
    health_score: int | None = None
    health_grade: str | None = None
    if registry_content:
        _health = score_scenario(registry_content)
        health_score = _health.total_score
        health_grade = _health.grade

    # Decide source for each code-managed field
    if registry_content:
        story_prompt_tr = registry_content.story_prompt_tr
        cover_prompt = registry_content.cover_prompt_template
        page_prompt = registry_content.page_prompt_template
        outfit_girl = registry_content.outfit_girl
        outfit_boy = registry_content.outfit_boy
        location_en = registry_content.location_en
        flags = registry_content.flags
        default_page_count = registry_content.default_page_count
        custom_inputs = registry_content.custom_inputs_schema
        # Extra registry-only data for admin display
        companions = [
            {"name_tr": c.name_tr, "name_en": c.name_en, "species": c.species,
             "appearance": c.appearance, "short_name": c.short_name}
            for c in registry_content.companions
        ]
        objects = [
            {"name_tr": o.name_tr, "appearance_en": o.appearance_en,
             "prompt_suffix": o.prompt_suffix}
            for o in registry_content.objects
        ]
        scenario_bible = registry_content.scenario_bible
        cultural_elements = registry_content.cultural_elements
        location_constraints = registry_content.location_constraints
        is_code_managed = True
    else:
        story_prompt_tr = getattr(scenario, "story_prompt_tr", None)
        cover_prompt = scenario.cover_prompt_template
        page_prompt = scenario.page_prompt_template
        outfit_girl = getattr(scenario, "outfit_girl", None)
        outfit_boy = getattr(scenario, "outfit_boy", None)
        location_en = getattr(scenario, "location_en", None)
        flags = getattr(scenario, "flags", None) or {}
        default_page_count = getattr(scenario, "default_page_count", 6)
        custom_inputs = (
            scenario.custom_inputs_schema
            if isinstance(scenario.custom_inputs_schema, list)
            else []
        )
        companions = []
        objects = []
        scenario_bible = getattr(scenario, "scenario_bible", None)
        cultural_elements = getattr(scenario, "cultural_elements", None)
        location_constraints = getattr(scenario, "location_constraints", None)
        is_code_managed = False

    # Sayfa sayısı: linked product varsa tek kaynak ürün
    _lp = getattr(scenario, "linked_product", None)
    _story_page = getattr(scenario, "story_page_count", None)
    effective_default_page_count = (
        (_lp.default_page_count if _lp and _lp.default_page_count else default_page_count) or 6
    )
    effective_story_page_count = (
        _lp.default_page_count if _lp and _lp.default_page_count else _story_page
    )

    return {
        "id": str(scenario.id),
        "name": scenario.name,
        "description": scenario.description,
        "thumbnail_url": thumb,
        "theme_key": theme_key,
        # Code-managed content (from registry if available)
        "cover_prompt_template": cover_prompt,
        "page_prompt_template": page_prompt,
        "ai_prompt_template": scenario.ai_prompt_template,
        "story_prompt_tr": story_prompt_tr,
        "location_en": location_en,
        "flags": flags,
        "default_page_count": default_page_count,
        "effective_default_page_count": effective_default_page_count,
        "effective_story_page_count": effective_story_page_count,
        "custom_inputs_schema": custom_inputs,
        "available_variables": _safe_get_variables(scenario),
        # Registry-only companion + object anchors
        "companions": companions,
        "objects": objects,
        "scenario_bible": scenario_bible,
        "cultural_elements": cultural_elements,
        "location_constraints": location_constraints,
        # Outfit Design (from registry if available)
        "outfit_girl": outfit_girl,
        "outfit_boy": outfit_boy,
        # Media — FILTERED: no base64 data in responses
        "gallery_images": _safe_gallery(scenario.gallery_images),
        # Marketing Fields (always from DB)
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
        # Display
        "is_active": scenario.is_active,
        "display_order": scenario.display_order,
        # Timestamps
        "created_at": scenario.created_at,
        "updated_at": scenario.updated_at,
        # Registry metadata — tells the frontend which fields are read-only
        "is_code_managed": is_code_managed,
        "code_managed_fields": sorted(_CODE_MANAGED_FIELDS) if is_code_managed else [],
        # Health score
        "health_score": health_score,
        "health_grade": health_grade,
    }


# ============ ENDPOINTS ============


@router.get("/companions")
async def list_companions(_user: SuperAdminUser):
    """Companion kütüphanesindeki tüm companion'ları listele."""
    from app.scenarios._companions import COMPANIONS
    from app.scenarios._registry import get_all_scenarios

    # Hangi companion hangi senaryolarda kullanılıyor?
    scenario_map: dict[str, list[str]] = {}
    for theme_key, sc in get_all_scenarios().items():
        for comp in sc.companions:
            key = comp.name_tr.lower().strip()
            scenario_map.setdefault(key, []).append(theme_key)

    result = []
    for cid, anchor in COMPANIONS.all().items():
        used_in = scenario_map.get(anchor.name_tr.lower().strip(), [])
        result.append({
            "companion_id": cid,
            "name_tr": anchor.name_tr,
            "name_en": anchor.name_en,
            "species": anchor.species,
            "short_name": anchor.short_name,
            "appearance": anchor.appearance,
            "used_in_scenarios": used_in,
        })

    return {
        "total": len(result),
        "companions": result,
    }


@router.get("/health")
async def scenario_health_dashboard(
    admin: SuperAdminUser,
) -> dict:
    """Get health dashboard for all registered scenarios.

    Returns aggregate stats + per-scenario health reports.
    No DB access — reads from the in-memory Scenario Registry.
    """
    from dataclasses import asdict

    from app.services.scenario_health_service import get_all_scenario_health, get_health_summary

    summary = get_health_summary()
    reports = get_all_scenario_health()

    return {
        "summary": summary,
        "reports": [asdict(r) for r in reports],
    }


class DryRunRequest(BaseModel):
    """Optional parameters for dry-run."""

    child_name: str = "Yusuf"
    child_age: int = Field(default=7, ge=3, le=12)
    child_gender: str = Field(default="erkek", pattern="^(erkek|kiz|girl|boy)$")


@router.post("/{scenario_id}/dry-run")
async def run_dry_run(
    scenario_id: UUID,
    db: DbSession,
    admin: SuperAdminUser,
    request: DryRunRequest | None = None,
) -> dict:
    """Run V3 pipeline dry-run for a scenario (no image generation).

    ⚠️ This calls the real Gemini API and takes 30-60 seconds.
    """
    # Resolve theme_key from scenario ID
    result = await db.execute(select(Scenario).where(Scenario.id == scenario_id))
    scenario = result.scalar_one_or_none()
    if not scenario:
        raise NotFoundError("Senaryo", scenario_id)

    theme_key = scenario.theme_key
    if not theme_key:
        raise ConflictError("Bu senaryonun theme_key'i tanımlı değil, dry-run çalıştırılamaz")

    params = request or DryRunRequest()

    from app.services.scenario_dry_run_service import run_scenario_dry_run

    try:
        result_data = await run_scenario_dry_run(
            db=db,
            theme_key=theme_key,
            child_name=params.child_name,
            child_age=params.child_age,
            child_gender=params.child_gender,
        )
        return result_data
    except ValueError as e:
        raise NotFoundError("Senaryo", str(e))
    except Exception as e:
        logger.error("Dry-run failed", scenario_id=str(scenario_id), error=str(e))
        raise ConflictError(f"Dry-run başarısız: {str(e)[:200]}")


@router.get("")
async def list_scenarios(
    db: DbSession,
    admin: SuperAdminUser,
    include_inactive: bool = False,
) -> list[dict]:
    """List all scenarios (admin view with full marketing data)."""
    query = (
        select(Scenario)
        .options(selectinload(Scenario.linked_product))
        .order_by(Scenario.display_order, Scenario.name)
    )

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
    result = await db.execute(
        select(Scenario)
        .options(selectinload(Scenario.linked_product))
        .where(Scenario.id == scenario_id)
    )
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

    # Linked product varsa sayfa sayısını üründen al (tutarlılık: yatay A4 = 22 vb.)
    resolved_default_page = request.default_page_count
    resolved_story_page = request.story_page_count
    linked_product_id = _to_uuid(request.linked_product_id)
    if linked_product_id:
        result_p = await db.execute(select(Product).where(Product.id == linked_product_id))
        linked_product = result_p.scalar_one_or_none()
        if linked_product and linked_product.default_page_count and linked_product.default_page_count >= 4:
            if resolved_default_page is None or resolved_default_page == 6:
                resolved_default_page = linked_product.default_page_count
            if resolved_story_page is None:
                resolved_story_page = linked_product.default_page_count

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
        default_page_count=resolved_default_page or 6,
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
        linked_product_id=linked_product_id,
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
        # Book Structure (resolved from product when linked)
        story_page_count=resolved_story_page,
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

    # ── HYBRID GUARD: Block code-managed fields if this scenario is in the registry ──
    from app.scenarios import get_scenario_content

    theme_key = getattr(scenario, "theme_key", None) or ""
    registry_content = get_scenario_content(theme_key) if theme_key else None

    if registry_content:
        blocked = [f for f in _CODE_MANAGED_FIELDS if f in update_data]
        if blocked:
            logger.warning(
                "ADMIN_BLOCKED_CODE_MANAGED_FIELDS",
                scenario=scenario.name,
                blocked_fields=blocked,
            )
            for f in blocked:
                del update_data[f]

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

    # linked_product değiştiyse veya sayfa sayısı boş/6 ise üründen senkronize et
    _lid = getattr(scenario, "linked_product_id", None)
    if _lid:
        res_lp = await db.execute(select(Product).where(Product.id == _lid))
        _lp = res_lp.scalar_one_or_none()
        if _lp and _lp.default_page_count and _lp.default_page_count >= 4:
            if (getattr(scenario, "default_page_count", None) is None or scenario.default_page_count == 6):
                scenario.default_page_count = _lp.default_page_count
            if getattr(scenario, "story_page_count", None) is None:
                scenario.story_page_count = _lp.default_page_count

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

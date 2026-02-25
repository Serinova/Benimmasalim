"""Scenario and learning outcomes endpoints.

Scenarios are PURE CONTENT - story templates and illustrations.
Marketing/pricing fields have been moved to the Product model.
"""

import logging
from uuid import UUID

from fastapi import APIRouter, Query
from pydantic import BaseModel
from sqlalchemy import select

from app.api.v1.deps import DbSession
from app.core.database import async_session_factory
from app.core.exceptions import NotFoundError
from app.models.learning_outcome import LearningOutcome
from app.models.scenario import Scenario
from app.models.visual_style import VisualStyle

router = APIRouter()
logger = logging.getLogger(__name__)


# ============ SCENARIO SCHEMAS ============


class ScenarioResponse(BaseModel):
    """Scenario response schema with marketing fields for product cards."""

    id: str
    name: str
    description: str | None
    thumbnail_url: str
    gallery_images: list[str]

    # Marketing fields for scenario product cards
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

    # Product override settings (pricing — templates are backend-only)
    price_override_base: float | None = None
    price_override_extra_page: float | None = None

    # Page count
    default_page_count: int | None = None
    # Linked product'ın default_page_count'ı — frontend'de öncelikli kullanılır
    linked_product_page_count: int | None = None

    # Outfit design (scenario-specific, gender-specific)
    outfit_girl: str | None = None
    outfit_boy: str | None = None
    
    # Custom inputs schema for user personalization
    custom_inputs_schema: list[dict] | None = None

    # Linked product info (for display)
    linked_product_id: str | None = None
    linked_product_name: str | None = None

    # Book structure (for marketing display on product cards)
    story_page_count: int | None = None
    cover_count: int | None = None
    greeting_page_count: int | None = None
    back_info_page_count: int | None = None
    total_page_count: int | None = None  # computed

    # Scenario metadata (for filtering/display)
    is_active: bool | None = None
    theme_key: str | None = None
    location_en: str | None = None
    display_order: int | None = None

    class Config:
        from_attributes = True


# ============ LEARNING OUTCOME SCHEMAS ============


class LearningOutcomeItem(BaseModel):
    """Single learning outcome item with visual assets (public-safe)."""

    id: str
    name: str
    description: str | None

    # Visual Assets
    icon_url: str | None
    color_theme: str | None

    # AI prompts intentionally excluded from public API for IP protection

    class Config:
        from_attributes = True


class LearningOutcomeCategoryGroup(BaseModel):
    """Learning outcomes grouped by category."""

    category: str
    category_label: str
    items: list[LearningOutcomeItem]


class LearningOutcomeResponse(BaseModel):
    """Learning outcome response schema (flat) — public-safe."""

    id: str
    name: str
    description: str | None

    # Visual Assets
    icon_url: str | None
    color_theme: str | None

    # Categorization
    category: str
    category_label: str | None
    age_group: str

    # AI prompts intentionally excluded from public API for IP protection

    class Config:
        from_attributes = True


# ============ VISUAL STYLE SCHEMAS ============


class VisualStyleResponse(BaseModel):
    """Visual style response schema — public-safe."""

    id: str
    name: str
    display_name: str | None = None
    thumbnail_url: str
    # prompt_modifier intentionally excluded from public API for IP protection
    id_weight: float = 0.90

    class Config:
        from_attributes = True


# ============ HELPER FUNCTIONS ============


def _is_url(s: str) -> bool:
    """True if s looks like an HTTP(S) URL (not base64 or inline data)."""
    return s.startswith(("http://", "https://", "/"))


def _normalize_gallery_images(raw: list | None) -> list[str]:
    """Ensure gallery_images is list[str] of URLs; filter out base64/inline data to prevent huge responses."""
    if not raw:
        return []
    out: list[str] = []
    for item in raw:
        url: str | None = None
        if isinstance(item, str) and item:
            url = item
        elif isinstance(item, dict):
            url = str(item.get("url") or item.get("src") or "")
        if url and _is_url(url):
            out.append(url)
    return out


def _safe_thumb(val: str | None) -> str:
    """Return thumbnail_url only if it's a real URL, not base64."""
    if val and isinstance(val, str) and _is_url(val):
        return val
    return ""


def scenario_to_response(scenario: Scenario) -> ScenarioResponse:
    """Convert Scenario model to response. Tolerates None/malformed thumbnail_url and gallery_images."""
    gallery = _normalize_gallery_images(
        scenario.gallery_images if isinstance(scenario.gallery_images, list) else None
    )
    marketing_gallery = _normalize_gallery_images(
        getattr(scenario, "marketing_gallery", None)
        if isinstance(getattr(scenario, "marketing_gallery", None), list)
        else None
    )
    return ScenarioResponse(
        id=str(scenario.id),
        name=scenario.name or "",
        description=scenario.description,
        thumbnail_url=_safe_thumb(scenario.thumbnail_url),
        gallery_images=gallery,
        marketing_video_url=getattr(scenario, "marketing_video_url", None),
        marketing_gallery=marketing_gallery,
        marketing_price_label=getattr(scenario, "marketing_price_label", None),
        marketing_features=getattr(scenario, "marketing_features", None) or [],
        marketing_badge=getattr(scenario, "marketing_badge", None),
        age_range=getattr(scenario, "age_range", None),
        estimated_duration=getattr(scenario, "estimated_duration", None),
        tagline=getattr(scenario, "tagline", None),
        rating=getattr(scenario, "rating", None),
        review_count=getattr(scenario, "review_count", 0),
        price_override_base=float(scenario.price_override_base) if getattr(scenario, "price_override_base", None) is not None else None,
        price_override_extra_page=float(scenario.price_override_extra_page) if getattr(scenario, "price_override_extra_page", None) is not None else None,
        default_page_count=getattr(scenario, "default_page_count", None),
        outfit_girl=getattr(scenario, "outfit_girl", None),
        outfit_boy=getattr(scenario, "outfit_boy", None),
        linked_product_page_count=(
            scenario.linked_product.default_page_count
            if getattr(scenario, "linked_product", None) and scenario.linked_product.default_page_count
            else None
        ),
        linked_product_id=str(scenario.linked_product_id) if getattr(scenario, "linked_product_id", None) else None,
        linked_product_name=scenario.linked_product.name if getattr(scenario, "linked_product", None) else None,
        story_page_count=getattr(scenario, "story_page_count", None),
        cover_count=getattr(scenario, "cover_count", 2),
        greeting_page_count=getattr(scenario, "greeting_page_count", 2),
        back_info_page_count=getattr(scenario, "back_info_page_count", 1),
        total_page_count=scenario.total_page_count,
        is_active=getattr(scenario, "is_active", None),
        theme_key=getattr(scenario, "theme_key", None),
        location_en=getattr(scenario, "location_en", None),
        display_order=getattr(scenario, "display_order", None),
    )


# ============ ENDPOINTS ============


@router.get("", response_model=list[ScenarioResponse])
async def list_scenarios() -> list[ScenarioResponse]:
    """
    List active scenarios. If none are active, returns all scenarios (fallback).
    Session is created inside handler so DB connection errors are caught and we return []
    (never 500), ensuring CORS headers are always sent.
    """
    try:
        async with async_session_factory() as db:
            result = await db.execute(
                select(Scenario)
                .where(Scenario.is_active == True)
                .order_by(Scenario.display_order, Scenario.name)
            )
            scenarios = result.scalars().all()
            if not scenarios:
                result_all = await db.execute(
                    select(Scenario).order_by(Scenario.display_order, Scenario.name)
                )
                scenarios = result_all.scalars().all()

            out: list[ScenarioResponse] = []
            for s in scenarios:
                try:
                    out.append(scenario_to_response(s))
                except Exception as e:
                    logger.warning("list_scenarios: skip scenario %s: %s", getattr(s, "id", None), e)
            return out
    except Exception as e:
        logger.exception("list_scenarios failed: %s", e)
        return []


@router.get("/featured", response_model=list[ScenarioResponse])
async def list_featured_scenarios(
    db: DbSession,
    limit: int = Query(default=3, ge=1, le=10),
) -> list[ScenarioResponse]:
    """
    List featured scenarios.
    Returns top scenarios by display order.
    """
    result = await db.execute(
        select(Scenario)
        .where(Scenario.is_active == True)
        .order_by(Scenario.display_order)
        .limit(limit)
    )
    scenarios = result.scalars().all()

    out: list[ScenarioResponse] = []
    for s in scenarios:
        try:
            out.append(scenario_to_response(s))
        except Exception as e:
            logger.warning("list_featured_scenarios: skip scenario %s: %s", getattr(s, "id", None), e)
    return out


# IMPORTANT: Static routes MUST come before dynamic /{id} routes!
@router.get("/learning-outcomes", response_model=list[LearningOutcomeCategoryGroup])
async def list_learning_outcomes_grouped(
    db: DbSession,
) -> list[LearningOutcomeCategoryGroup]:
    """
    List all active learning outcomes GROUPED BY CATEGORY.
    Returns data structured for accordion/grouped list display.
    """
    result = await db.execute(
        select(LearningOutcome)
        .where(LearningOutcome.is_active == True)
        .order_by(LearningOutcome.category, LearningOutcome.display_order)
    )
    outcomes = result.scalars().all()

    # Group by category
    grouped: dict[str, dict] = {}

    # Define category order
    category_order = ["SelfCare", "PersonalGrowth", "SocialSkills", "EducationNature"]

    for outcome in outcomes:
        cat = outcome.category
        if cat not in grouped:
            grouped[cat] = {
                "category": cat,
                "category_label": outcome.category_label or cat,
                "items": [],
            }
        grouped[cat]["items"].append(
            LearningOutcomeItem(
                id=str(outcome.id),
                name=outcome.name,
                description=outcome.description,
                icon_url=outcome.icon_url,
                color_theme=outcome.color_theme,
                ai_prompt=outcome.ai_prompt,
                ai_prompt_instruction=outcome.ai_prompt_instruction,
            )
        )

    # Sort by predefined order
    result_list = []
    for cat in category_order:
        if cat in grouped:
            result_list.append(LearningOutcomeCategoryGroup(**grouped[cat]))

    # Add any remaining categories not in predefined order
    for cat in grouped:
        if cat not in category_order:
            result_list.append(LearningOutcomeCategoryGroup(**grouped[cat]))

    return result_list


@router.get("/learning-outcomes/flat", response_model=list[LearningOutcomeResponse])
async def list_learning_outcomes_flat(
    db: DbSession,
    category: str | None = Query(None, description="Filter by category"),
) -> list[LearningOutcomeResponse]:
    """List all active learning outcomes as flat list (for filtering)."""
    query = select(LearningOutcome).where(LearningOutcome.is_active == True)

    if category:
        query = query.where(LearningOutcome.category == category)

    result = await db.execute(
        query.order_by(LearningOutcome.category, LearningOutcome.display_order)
    )
    outcomes = result.scalars().all()

    return [
        LearningOutcomeResponse(
            id=str(o.id),
            name=o.name,
            description=o.description,
            icon_url=o.icon_url,
            color_theme=o.color_theme,
            category=o.category,
            category_label=o.category_label,
            age_group=o.age_group,
            ai_prompt=o.ai_prompt,
            ai_prompt_instruction=o.ai_prompt_instruction,
        )
        for o in outcomes
    ]


@router.get("/visual-styles", response_model=list[VisualStyleResponse])
async def list_visual_styles(db: DbSession) -> list[VisualStyleResponse]:
    """List all active visual styles."""
    result = await db.execute(
        select(VisualStyle).where(VisualStyle.is_active == True).order_by(VisualStyle.name)
    )
    styles = result.scalars().all()

    return [
        VisualStyleResponse(
            id=str(s.id),
            name=s.name,
            display_name=getattr(s, "display_name", None),
            thumbnail_url=s.thumbnail_url,
            id_weight=s.id_weight if s.id_weight is not None else 0.90,
        )
        for s in styles
    ]


# Dynamic route MUST be last to avoid matching static routes
@router.get("/{scenario_id}", response_model=ScenarioResponse)
async def get_scenario(scenario_id: UUID, db: DbSession) -> ScenarioResponse:
    """Get a single scenario by ID."""
    result = await db.execute(select(Scenario).where(Scenario.id == scenario_id))
    scenario = result.scalar_one_or_none()

    if not scenario:
        raise NotFoundError("Senaryo", scenario_id)

    return scenario_to_response(scenario)

"""Scenario and learning outcomes endpoints.

Scenarios are PURE CONTENT - story templates and illustrations.
Marketing/pricing fields have been moved to the Product model.
"""

import logging
from uuid import UUID

from fastapi import APIRouter, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.api.v1.deps import DbSession
from app.core.database import async_session_factory
from app.core.exceptions import NotFoundError
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
    """True if s is a full absolute HTTP(S) URL (not relative paths or base64)."""
    return s.startswith(("http://", "https://"))


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
    """Return thumbnail_url only if it's an absolute http(s) URL; filter out relative paths and base64."""
    if val and isinstance(val, str) and val.startswith(("http://", "https://")):
        return val
    return ""


def _normalize_options(opts: object) -> list[str] | None:
    """Normalize options field to list[str] regardless of source format."""
    if opts is None:
        return None
    if isinstance(opts, str):
        return [o.strip() for o in opts.split(",") if o.strip()]
    if isinstance(opts, list):
        result: list[str] = []
        for item in opts:
            if isinstance(item, str):
                result.append(item)
            elif isinstance(item, dict):
                result.append(item.get("label_tr") or item.get("label") or item.get("label_en") or str(item.get("value", "")))
            else:
                result.append(str(item))
        return result
    return None


def _normalize_custom_inputs(raw: list | dict | None) -> list[dict] | None:
    """Ensure custom_inputs_schema is list[dict] with options always as list[str]."""
    if raw is None:
        return None
    items: list[dict] = []
    if isinstance(raw, list):
        items = raw
    elif isinstance(raw, dict):
        items = [{"key": k, **v} if isinstance(v, dict) else {"key": k, "value": v} for k, v in raw.items()]
    else:
        return None

    for field in items:
        if "options" in field:
            field["options"] = _normalize_options(field["options"])
        if "label" not in field:
            field["label"] = field.get("label_tr") or field.get("label_en") or field.get("key", "")
    return items


def _resolve_price_label(scenario: Scenario) -> str | None:
    """Resolve the marketing price label for a scenario.

    Priority:
    1. Linked product's base_price (always up-to-date from product management)
    2. scenario.marketing_price_label as manual override/fallback
    3. None if neither is available

    This ensures the displayed price on scenario cards always reflects
    the actual product price rather than a cached/stale static label.
    """
    linked = getattr(scenario, "linked_product", None)
    if linked is not None:
        price = getattr(linked, "base_price", None)
        if price is not None:
            try:
                price_float = float(price)
                if price_float > 0:
                    # Format as Turkish currency, e.g. "549 TL'den başlayan fiyatlarla"
                    formatted = f"{price_float:,.0f}".replace(",", ".")
                    return f"{formatted} TL'den başlayan fiyatlarla"
            except (TypeError, ValueError):
                pass
    # Fallback to manually stored label
    return getattr(scenario, "marketing_price_label", None)


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
        marketing_price_label=_resolve_price_label(scenario),
        marketing_features=getattr(scenario, "marketing_features", None) or [],
        marketing_badge=getattr(scenario, "marketing_badge", None),
        age_range=getattr(scenario, "age_range", None),
        estimated_duration=getattr(scenario, "estimated_duration", None),
        tagline=getattr(scenario, "tagline", None),
        rating=getattr(scenario, "rating", None),
        review_count=getattr(scenario, "review_count", 0),
        # Scenarios are topics, not products — pricing always comes from the Product model
        price_override_base=None,
        price_override_extra_page=None,
        default_page_count=getattr(scenario, "default_page_count", None),
        outfit_girl=getattr(scenario, "outfit_girl", None),
        outfit_boy=getattr(scenario, "outfit_boy", None),
        custom_inputs_schema=_normalize_custom_inputs(scenario.custom_inputs_schema),
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
async def list_scenarios(include_all: bool = False) -> list[ScenarioResponse]:
    """
    List active scenarios. If none are active, returns all scenarios (fallback).
    Pass ?include_all=true to include inactive scenarios (for debugging).
    Session is created inside handler so DB connection errors are caught and we return []
    (never 500), ensuring CORS headers are always sent.
    """
    try:
        async with async_session_factory() as db:
            if include_all:
                query = (
                    select(Scenario)
                    .options(selectinload(Scenario.linked_product))
                    .order_by(Scenario.display_order, Scenario.name)
                )
            else:
                query = (
                    select(Scenario)
                    .where(Scenario.is_active == True)
                    .options(selectinload(Scenario.linked_product))
                    .order_by(Scenario.display_order, Scenario.name)
                )
            result = await db.execute(query)
            scenarios = result.scalars().all()
            
            if not scenarios:
                query_all = (
                    select(Scenario)
                    .options(selectinload(Scenario.linked_product))
                    .order_by(Scenario.display_order, Scenario.name)
                )
                result_all = await db.execute(query_all)
                scenarios = result_all.scalars().all()

            out: list[ScenarioResponse] = []
            for s in scenarios:
                try:
                    out.append(scenario_to_response(s))
                except Exception as e:
                    logger.warning("list_scenarios: skip scenario %s (%s): %s", getattr(s, "id", None), getattr(s, "name", "?"), str(e)[:500])
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

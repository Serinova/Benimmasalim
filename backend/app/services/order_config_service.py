"""Effective order configuration resolver.

Merges Product defaults with Scenario-level overrides so that all order
creation paths (trials, direct orders) use a single source of truth.

Priority chain (highest → lowest):
  1. Scenario explicit override field (price_override_base, cover_template_id_override …)
  2. Scenario.linked_product settings (the product the scenario is linked to)
  3. Explicitly passed product_id settings
  4. Hard-coded system fallback
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from decimal import Decimal
from typing import TYPE_CHECKING

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

if TYPE_CHECKING:
    from app.models.product import Product
    from app.models.scenario import Scenario

logger = structlog.get_logger()


@dataclass(frozen=True)
class EffectiveOrderConfig:
    """Resolved configuration for a single order/trial."""

    # Pricing
    base_price: Decimal
    extra_page_price: Decimal

    # Page count
    page_count: int
    min_page_count: int
    max_page_count: int

    # Template IDs (may be None if not configured)
    cover_template_id: uuid.UUID | None
    inner_template_id: uuid.UUID | None
    back_template_id: uuid.UUID | None

    # AI config
    ai_config_id: uuid.UUID | None

    # Physical settings
    paper_type: str
    paper_finish: str
    cover_type: str
    lamination: str | None
    orientation: str

    # Source tracking (for logging / debugging)
    price_source: str   # "scenario_override" | "linked_product" | "product" | "fallback"
    page_count_source: str  # "request" | "scenario" | "linked_product" | "product" | "fallback"
    product_source: str  # which product was ultimately used


def _safe_uuid(val: str | uuid.UUID | None) -> uuid.UUID | None:
    if val is None:
        return None
    try:
        return uuid.UUID(str(val))
    except (ValueError, AttributeError):
        return None


async def get_effective_order_config(
    db: AsyncSession,
    product_id: uuid.UUID | str | None,
    scenario_id: uuid.UUID | str | None,
    *,
    requested_page_count: int | None = None,
) -> EffectiveOrderConfig:
    """Return the merged Product + Scenario configuration for an order.

    Priority:
      request page_count > scenario override > linked_product > explicit product_id > fallback

    Args:
        db: Async SQLAlchemy session.
        product_id: UUID of the explicitly selected Product (may be None).
        scenario_id: UUID of the selected Scenario (may be None).
        requested_page_count: Explicit page count from the request (highest priority).
    """
    from sqlalchemy import select

    from app.models.product import Product
    from app.models.scenario import Scenario

    explicit_product: Product | None = None
    scenario: Scenario | None = None

    if product_id:
        pid = _safe_uuid(product_id)
        if pid:
            result = await db.execute(select(Product).where(Product.id == pid))
            explicit_product = result.scalar_one_or_none()

    if scenario_id:
        sid = _safe_uuid(scenario_id)
        if sid:
            result = await db.execute(select(Scenario).where(Scenario.id == sid))
            scenario = result.scalar_one_or_none()

    # Determine the "base product" — scenario's linked_product takes priority over explicit product_id
    linked_product: Product | None = getattr(scenario, "linked_product", None) if scenario else None
    base_product: Product | None = linked_product or explicit_product
    product_source = (
        "linked_product" if linked_product else ("explicit_product" if explicit_product else "none")
    )

    # ── Page count: request > linked_product > scenario.default_page_count > explicit_product > fallback ──
    # linked_product atanmışsa onun default_page_count'ı senaryo default'undan önce gelir.
    # Senaryo default_page_count server_default=6 ile geldiğinden linked_product'ı ezmemeli.
    page_count_source = "fallback"
    if requested_page_count and requested_page_count >= 4:
        page_count = requested_page_count
        page_count_source = "request"
    elif linked_product and linked_product.default_page_count and linked_product.default_page_count >= 4:
        page_count = linked_product.default_page_count
        page_count_source = "linked_product"
    elif scenario and scenario.default_page_count and scenario.default_page_count >= 4:
        page_count = scenario.default_page_count
        page_count_source = "scenario"
    elif explicit_product and explicit_product.default_page_count and explicit_product.default_page_count >= 4:
        page_count = explicit_product.default_page_count
        page_count_source = "explicit_product"
    else:
        page_count = 16

    # ── Min/max page count ──
    if scenario and getattr(scenario, "min_page_count_override", None):
        min_page_count = scenario.min_page_count_override
    elif base_product:
        min_page_count = base_product.min_page_count
    else:
        min_page_count = 4

    if scenario and getattr(scenario, "max_page_count_override", None):
        max_page_count = scenario.max_page_count_override
    elif base_product:
        max_page_count = base_product.max_page_count
    else:
        max_page_count = 64

    # ── Pricing: scenario override > base_product > fallback ──
    price_source = "fallback"
    if scenario and getattr(scenario, "price_override_base", None) is not None:
        base_price = Decimal(str(scenario.price_override_base))
        price_source = "scenario_override"
    elif base_product and base_product.base_price is not None:
        # Use discounted_price if active
        effective = base_product.discounted_price or base_product.base_price
        base_price = Decimal(str(effective))
        price_source = product_source
    else:
        base_price = Decimal("0")

    if scenario and getattr(scenario, "price_override_extra_page", None) is not None:
        extra_page_price = Decimal(str(scenario.price_override_extra_page))
    elif base_product:
        extra_page_price = Decimal(str(base_product.extra_page_price))
    else:
        extra_page_price = Decimal("0")

    # ── Templates: scenario override > base_product ──
    cover_template_id = _safe_uuid(
        getattr(scenario, "cover_template_id_override", None) or
        (base_product.cover_template_id if base_product else None)
    )
    inner_template_id = _safe_uuid(
        getattr(scenario, "inner_template_id_override", None) or
        (base_product.inner_template_id if base_product else None)
    )
    back_template_id = _safe_uuid(
        getattr(scenario, "back_template_id_override", None) or
        (base_product.back_template_id if base_product else None)
    )

    # ── AI config ──
    ai_config_id = _safe_uuid(
        getattr(scenario, "ai_config_id_override", None) or
        (base_product.ai_config_id if base_product else None)
    )

    # ── Physical settings: scenario override > base_product > defaults ──
    paper_type = (
        getattr(scenario, "paper_type_override", None) or
        (base_product.paper_type if base_product else "Kuşe 170gr")
    )
    paper_finish = (
        getattr(scenario, "paper_finish_override", None) or
        (base_product.paper_finish if base_product else "Mat")
    )
    cover_type = (
        getattr(scenario, "cover_type_override", None) or
        (base_product.cover_type if base_product else "Sert Kapak")
    )
    lamination = (
        getattr(scenario, "lamination_override", None) or
        (base_product.lamination if base_product else None)
    )
    orientation = (
        getattr(scenario, "orientation_override", None) or
        (base_product.orientation if base_product else "landscape")
    )

    config = EffectiveOrderConfig(
        base_price=base_price,
        extra_page_price=extra_page_price,
        page_count=page_count,
        min_page_count=min_page_count,
        max_page_count=max_page_count,
        cover_template_id=cover_template_id,
        inner_template_id=inner_template_id,
        back_template_id=back_template_id,
        ai_config_id=ai_config_id,
        paper_type=paper_type,
        paper_finish=paper_finish,
        cover_type=cover_type,
        lamination=lamination,
        orientation=orientation,
        price_source=price_source,
        page_count_source=page_count_source,
        product_source=product_source,
    )

    logger.debug(
        "EffectiveOrderConfig resolved",
        product_id=str(product_id),
        scenario_id=str(scenario_id),
        linked_product_id=str(linked_product.id) if linked_product else None,
        page_count=page_count,
        page_count_source=page_count_source,
        base_price=str(base_price),
        price_source=price_source,
        product_source=product_source,
    )

    return config

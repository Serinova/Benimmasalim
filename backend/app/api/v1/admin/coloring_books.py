"""Admin API for coloring book product management.

Reads from the unified `products` table with `product_type = 'coloring_book'`.
Legacy `coloring_book_products` table is deprecated (migration 092 copied data).
"""

from decimal import Decimal
from uuid import UUID

import structlog
from fastapi import APIRouter
from pydantic import BaseModel
from sqlalchemy import select

from app.api.v1.deps import DbSession, SuperAdminUser
from app.models.product import Product, ProductType

logger = structlog.get_logger()

router = APIRouter(
    prefix="/admin/coloring-books",
    tags=["Admin: Coloring Books"],
)

# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class ColoringBookProductResponse(BaseModel):
    """Coloring book product response."""

    id: str
    name: str
    slug: str
    description: str | None
    base_price: Decimal
    discounted_price: Decimal | None
    line_art_method: str
    edge_threshold_low: int
    edge_threshold_high: int
    is_active: bool


class UpdateColoringBookRequest(BaseModel):
    """Request to update coloring book product."""

    base_price: Decimal | None = None
    discounted_price: Decimal | None = None
    line_art_method: str | None = None
    edge_threshold_low: int | None = None
    edge_threshold_high: int | None = None
    is_active: bool | None = None


def _to_response(p: Product) -> ColoringBookProductResponse:
    """Map a Product (coloring_book type) to response schema."""
    tsd = p.type_specific_data or {}
    return ColoringBookProductResponse(
        id=str(p.id),
        name=p.name,
        slug=p.slug,
        description=p.description,
        base_price=p.base_price,
        discounted_price=p.discounted_price,
        line_art_method=tsd.get("line_art_method", "canny"),
        edge_threshold_low=tsd.get("edge_threshold_low", 80),
        edge_threshold_high=tsd.get("edge_threshold_high", 200),
        is_active=p.is_active,
    )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("", response_model=list[ColoringBookProductResponse])
async def list_coloring_book_products(
    db: DbSession,
    admin: SuperAdminUser,
):
    """List all coloring book products."""
    stmt = (
        select(Product)
        .where(Product.product_type == ProductType.COLORING_BOOK.value)
        .order_by(Product.created_at.desc())
    )
    result = await db.execute(stmt)
    products = result.scalars().all()

    return [_to_response(p) for p in products]


@router.patch("/{product_id}", response_model=ColoringBookProductResponse)
async def update_coloring_book_product(
    product_id: UUID,
    request: UpdateColoringBookRequest,
    db: DbSession,
    admin: SuperAdminUser,
):
    """Update coloring book product configuration."""
    stmt = select(Product).where(
        Product.id == product_id,
        Product.product_type == ProductType.COLORING_BOOK.value,
    )
    result = await db.execute(stmt)
    product = result.scalar_one_or_none()

    if not product:
        from app.core.exceptions import NotFoundError
        raise NotFoundError("Boyama kitabı ürünü", product_id)

    # Update pricing fields directly on Product
    if request.base_price is not None:
        product.base_price = request.base_price
    if request.discounted_price is not None:
        product.discounted_price = request.discounted_price
    if request.is_active is not None:
        product.is_active = request.is_active

    # Update type-specific fields in JSONB
    tsd = product.type_specific_data or {}
    if request.line_art_method is not None:
        tsd["line_art_method"] = request.line_art_method
    if request.edge_threshold_low is not None:
        tsd["edge_threshold_low"] = request.edge_threshold_low
    if request.edge_threshold_high is not None:
        tsd["edge_threshold_high"] = request.edge_threshold_high
    product.type_specific_data = tsd

    await db.commit()
    await db.refresh(product)

    logger.info(
        "Coloring book product updated",
        product_id=str(product.id),
        changes={
            k: v
            for k, v in request.model_dump().items()
            if v is not None
        },
    )

    return _to_response(product)

"""Admin API for coloring book product management."""

from decimal import Decimal
from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.coloring_book import ColoringBookProduct

logger = structlog.get_logger()

router = APIRouter(
    prefix="/admin/coloring-books",
    tags=["Admin: Coloring Books"],
)


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
    active: bool


class UpdateColoringBookRequest(BaseModel):
    """Request to update coloring book product."""

    base_price: Decimal | None = None
    discounted_price: Decimal | None = None
    line_art_method: str | None = None
    edge_threshold_low: int | None = None
    edge_threshold_high: int | None = None
    active: bool | None = None


@router.get("", response_model=list[ColoringBookProductResponse])
async def list_coloring_book_products(db: AsyncSession = Depends(get_db)):
    """List all coloring book products."""
    stmt = select(ColoringBookProduct).order_by(ColoringBookProduct.created_at.desc())
    result = await db.execute(stmt)
    products = result.scalars().all()

    return [
        ColoringBookProductResponse(
            id=str(p.id),
            name=p.name,
            slug=p.slug,
            description=p.description,
            base_price=p.base_price,
            discounted_price=p.discounted_price,
            line_art_method=p.line_art_method,
            edge_threshold_low=p.edge_threshold_low,
            edge_threshold_high=p.edge_threshold_high,
            active=p.active,
        )
        for p in products
    ]


@router.patch("/{product_id}", response_model=ColoringBookProductResponse)
async def update_coloring_book_product(
    product_id: str,
    request: UpdateColoringBookRequest,
    db: AsyncSession = Depends(get_db),
):
    """Update coloring book product configuration."""
    try:
        product_uuid = UUID(product_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid product ID")

    stmt = select(ColoringBookProduct).where(ColoringBookProduct.id == product_uuid)
    result = await db.execute(stmt)
    product = result.scalar_one_or_none()

    if not product:
        raise HTTPException(status_code=404, detail="Coloring book product not found")

    # Update fields
    if request.base_price is not None:
        product.base_price = request.base_price
    if request.discounted_price is not None:
        product.discounted_price = request.discounted_price
    if request.line_art_method is not None:
        product.line_art_method = request.line_art_method
    if request.edge_threshold_low is not None:
        product.edge_threshold_low = request.edge_threshold_low
    if request.edge_threshold_high is not None:
        product.edge_threshold_high = request.edge_threshold_high
    if request.active is not None:
        product.active = request.active

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

    return ColoringBookProductResponse(
        id=str(product.id),
        name=product.name,
        slug=product.slug,
        description=product.description,
        base_price=product.base_price,
        discounted_price=product.discounted_price,
        line_art_method=product.line_art_method,
        edge_threshold_low=product.edge_threshold_low,
        edge_threshold_high=product.edge_threshold_high,
        active=product.active,
    )

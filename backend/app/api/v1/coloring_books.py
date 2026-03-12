"""Coloring book API endpoints.

Public endpoint for storefront — reads from the unified `products` table
with `product_type = 'coloring_book'`.
"""

from decimal import Decimal

import structlog
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlalchemy import select

from app.api.v1.deps import DbSession
from app.models.product import Product, ProductType

logger = structlog.get_logger()

router = APIRouter(prefix="/coloring-books", tags=["Coloring Books"])


class ColoringBookResponse(BaseModel):
    """Coloring book product response."""

    id: str
    name: str
    slug: str
    description: str | None
    base_price: Decimal
    discounted_price: Decimal | None
    active: bool


@router.get("/active", response_model=ColoringBookResponse)
async def get_active_coloring_book_product(db: DbSession):
    """
    Get active coloring book product configuration.

    Used by frontend to display pricing and availability.

    Returns:
        ColoringBookResponse: Active coloring book product
    """
    stmt = (
        select(Product)
        .where(
            Product.product_type == ProductType.COLORING_BOOK.value,
            Product.is_active == True,
        )
        .limit(1)
    )
    result = await db.execute(stmt)
    product = result.scalar_one_or_none()

    if not product:
        raise HTTPException(status_code=404, detail="Coloring book product not found")

    logger.info("Fetched active coloring book product", product_id=str(product.id))

    return ColoringBookResponse(
        id=str(product.id),
        name=product.name,
        slug=product.slug,
        description=product.description,
        base_price=product.base_price,
        discounted_price=product.discounted_price,
        active=product.is_active,
    )

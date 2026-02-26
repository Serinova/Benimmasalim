"""Coloring book API endpoints."""

from decimal import Decimal

import structlog
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.coloring_book import ColoringBookProduct

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
async def get_active_coloring_book_product(db: AsyncSession = Depends(get_db)):
    """
    Get active coloring book product configuration.

    Used by frontend to display pricing and availability.

    Returns:
        ColoringBookResponse: Active coloring book product
    """
    stmt = select(ColoringBookProduct).where(ColoringBookProduct.active == True).limit(1)
    result = await db.execute(stmt)
    config = result.scalar_one_or_none()

    if not config:
        raise HTTPException(status_code=404, detail="Coloring book product not found")

    logger.info("Fetched active coloring book product", config_id=str(config.id))

    return ColoringBookResponse(
        id=str(config.id),
        name=config.name,
        slug=config.slug,
        description=config.description,
        base_price=config.base_price,
        discounted_price=config.discounted_price,
        active=config.active,
    )

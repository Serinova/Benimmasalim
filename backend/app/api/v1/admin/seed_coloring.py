"""Emergency seed endpoint for coloring book - ADMIN ONLY"""

from decimal import Decimal

import structlog
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.coloring_book import ColoringBookProduct

logger = structlog.get_logger()

router = APIRouter(prefix="/admin/seed", tags=["Admin - Seed"])


@router.post("/coloring-book")
async def seed_coloring_book_product(db: AsyncSession = Depends(get_db)):
    """
    Emergency seed endpoint for coloring book product.
    
    WARNING: This is a one-time setup endpoint.
    Call this if coloring book is not visible in checkout.
    """
    # Check if already exists
    result = await db.execute(
        select(ColoringBookProduct).where(ColoringBookProduct.active == True)
    )
    existing = result.scalar_one_or_none()
    
    if existing:
        logger.info("Coloring book product already exists", config_id=str(existing.id))
        return {
            "status": "already_exists",
            "message": "Boyama kitabı zaten mevcut",
            "data": {
                "id": str(existing.id),
                "name": existing.name,
                "base_price": float(existing.base_price),
                "discounted_price": float(existing.discounted_price) if existing.discounted_price else None,
                "active": existing.active,
            }
        }
    
    # Create new
    config = ColoringBookProduct(
        name="Boyama Kitabı",
        slug="boyama-kitabi",
        description="Hikayenizdeki görsellerin boyama kitabı versiyonu. Metin içermez, sadece boyama için optimize edilmiş basit çizgiler.",
        base_price=Decimal("200.00"),
        discounted_price=Decimal("150.00"),
        line_art_method="canny",
        edge_threshold_low=80,
        edge_threshold_high=200,
        active=True,
    )
    
    db.add(config)
    await db.commit()
    await db.refresh(config)
    
    logger.info("Coloring book product created", config_id=str(config.id))
    
    return {
        "status": "created",
        "message": "Boyama kitabı başarıyla oluşturuldu!",
        "data": {
            "id": str(config.id),
            "name": config.name,
            "base_price": float(config.base_price),
            "discounted_price": float(config.discounted_price),
            "edge_thresholds": f"{config.edge_threshold_low}/{config.edge_threshold_high}",
            "active": config.active,
        }
    }

"""Emergency seed endpoint for coloring book - ADMIN ONLY.

Creates a coloring book entry in the `products` table with product_type = 'coloring_book'.
"""

from decimal import Decimal

import structlog
from fastapi import APIRouter
from sqlalchemy import select

from app.api.v1.deps import DbSession, SuperAdminUser
from app.models.product import Product, ProductType

logger = structlog.get_logger()

router = APIRouter(prefix="/admin/seed", tags=["Admin - Seed"])


@router.post("/coloring-book")
async def seed_coloring_book_product(
    db: DbSession,
    admin: SuperAdminUser,
):
    """
    Emergency seed endpoint for coloring book product.
    
    WARNING: This is a one-time setup endpoint.
    Call this if coloring book is not visible in checkout.
    """
    # Check if already exists in products table
    result = await db.execute(
        select(Product).where(
            Product.product_type == ProductType.COLORING_BOOK.value,
            Product.is_active == True,
        )
    )
    existing = result.scalar_one_or_none()
    
    if existing:
        logger.info("Coloring book product already exists", product_id=str(existing.id))
        return {
            "status": "already_exists",
            "message": "Boyama kitabı zaten mevcut",
            "data": {
                "id": str(existing.id),
                "name": existing.name,
                "base_price": float(existing.base_price),
                "discounted_price": float(existing.discounted_price) if existing.discounted_price else None,
                "is_active": existing.is_active,
            }
        }
    
    # Create new coloring book product in the unified products table
    product = Product(
        name="Boyama Kitabı",
        slug="boyama-kitabi",
        description="Hikayenizdeki görsellerin boyama kitabı versiyonu. Metin içermez, sadece boyama için optimize edilmiş basit çizgiler.",
        product_type=ProductType.COLORING_BOOK.value,
        type_specific_data={
            "line_art_method": "canny",
            "edge_threshold_low": 80,
            "edge_threshold_high": 200,
        },
        base_price=Decimal("200.00"),
        discounted_price=Decimal("150.00"),
        is_active=True,
        display_order=100,
    )
    
    db.add(product)
    await db.commit()
    await db.refresh(product)
    
    logger.info("Coloring book product created", product_id=str(product.id))
    
    tsd = product.type_specific_data or {}
    return {
        "status": "created",
        "message": "Boyama kitabı başarıyla oluşturuldu!",
        "data": {
            "id": str(product.id),
            "name": product.name,
            "base_price": float(product.base_price),
            "discounted_price": float(product.discounted_price) if product.discounted_price else None,
            "edge_thresholds": f"{tsd.get('edge_threshold_low', 80)}/{tsd.get('edge_threshold_high', 200)}",
            "is_active": product.is_active,
        }
    }

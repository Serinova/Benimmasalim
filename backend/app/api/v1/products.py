"""Product endpoints - Public product listing for storefront."""

from uuid import UUID

from fastapi import APIRouter, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.api.v1.deps import DbSession
from app.core.exceptions import NotFoundError
from app.models.product import Product

router = APIRouter()


def _to_response(p: Product) -> "ProductResponse":
    """Map a Product ORM instance to ProductResponse."""
    return ProductResponse(
        id=str(p.id),
        name=p.name,
        slug=p.slug,
        description=p.description,
        short_description=p.short_description,
        cover_width_mm=p.cover_template.page_width_mm if p.cover_template else None,
        cover_height_mm=p.cover_template.page_height_mm if p.cover_template else None,
        inner_width_mm=p.inner_template.page_width_mm if p.inner_template else None,
        inner_height_mm=p.inner_template.page_height_mm if p.inner_template else None,
        default_page_count=p.default_page_count,
        min_page_count=p.min_page_count,
        max_page_count=p.max_page_count,
        paper_type=p.paper_type,
        paper_finish=p.paper_finish,
        cover_type=p.cover_type,
        base_price=float(p.base_price),
        discounted_price=float(p.discounted_price) if p.discounted_price else None,
        extra_page_price=float(p.extra_page_price) if p.extra_page_price else 5.0,
        thumbnail_url=p.thumbnail_url,
        sample_images=p.sample_images or [],
        orientation=p.orientation or "landscape",
        is_featured=p.is_featured,
        stock_status=p.stock_status,
        promo_badge=p.promo_badge,
        promo_end_date=p.promo_end_date.isoformat() if p.promo_end_date else None,
        feature_list=p.feature_list or [],
        rating=p.rating,
        review_count=p.review_count or 0,
        social_proof_text=p.social_proof_text,
        gallery_images=p.gallery_images or [],
        video_url=p.video_url,
        lamination=p.lamination,
        is_gift_wrapped=p.is_gift_wrapped,
    )


class ProductResponse(BaseModel):
    """Product response schema for public API."""

    id: str
    name: str
    slug: str
    description: str | None
    short_description: str | None
    # Page dimensions from templates (for display)
    cover_width_mm: float | None
    cover_height_mm: float | None
    inner_width_mm: float | None
    inner_height_mm: float | None
    # Page settings
    default_page_count: int
    min_page_count: int
    max_page_count: int
    # Paper & Cover
    paper_type: str
    paper_finish: str
    cover_type: str
    # Pricing
    base_price: float
    discounted_price: float | None
    extra_page_price: float
    # Media
    thumbnail_url: str | None
    # Flipbook Preview
    sample_images: list[str]
    orientation: str
    # Status
    is_featured: bool
    stock_status: str
    # Marketing
    promo_badge: str | None
    promo_end_date: str | None
    feature_list: list[str]
    rating: float | None
    review_count: int
    social_proof_text: str | None
    # Extended media
    gallery_images: list[str]
    video_url: str | None
    # Cover details
    lamination: str | None
    is_gift_wrapped: bool

    class Config:
        from_attributes = True


@router.get("")
async def list_products(
    db: DbSession,
    featured: bool | None = Query(None, description="Filter by featured status"),
) -> list[ProductResponse]:
    """
    List all active products for storefront.
    Products are sorted by display_order, then by name.
    """
    query = (
        select(Product)
        .where(Product.is_active == True)
        .options(
            selectinload(Product.cover_template),
            selectinload(Product.inner_template),
        )
    )

    if featured is not None:
        query = query.where(Product.is_featured == featured)

    query = query.order_by(Product.display_order, Product.name)

    result = await db.execute(query)
    products = result.scalars().all()

    return [_to_response(p) for p in products]


@router.get("/{product_id}")
async def get_product(product_id: UUID, db: DbSession) -> ProductResponse:
    """Get a single product by ID."""
    result = await db.execute(
        select(Product)
        .where(Product.id == product_id, Product.is_active == True)
        .options(
            selectinload(Product.cover_template),
            selectinload(Product.inner_template),
        )
    )
    product = result.scalar_one_or_none()

    if not product:
        raise NotFoundError("Ürün", product_id)

    return _to_response(product)


@router.get("/by-slug/{slug}")
async def get_product_by_slug(slug: str, db: DbSession) -> ProductResponse:
    """Get a product by slug for SEO-friendly URLs."""
    result = await db.execute(
        select(Product)
        .where(Product.slug == slug, Product.is_active == True)
        .options(
            selectinload(Product.cover_template),
            selectinload(Product.inner_template),
        )
    )
    product = result.scalar_one_or_none()

    if not product:
        raise NotFoundError("Ürün", slug)

    return _to_response(product)

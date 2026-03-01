"""Admin endpoints for product management.

Products are PHYSICAL ITEMS being sold. This is where marketing,
pricing, urgency, and social proof belong.

Supports multiple product types:
- story_book: Traditional story books with scenarios
- coloring_book: Coloring books with line-art conversion
- audio_addon: Audio book feature addons
"""

import re
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Query
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.api.v1.deps import DbSession, SuperAdminUser
from app.core.exceptions import ConflictError, NotFoundError
from app.models.book_template import AIGenerationConfig, PageTemplate
from app.models.product import Product, ProductType

router = APIRouter()


# =============================================================================
# REQUEST/RESPONSE SCHEMAS
# =============================================================================


class ProductCreate(BaseModel):
    """Create product request with technical and marketing fields."""

    # ===== BASIC INFO =====
    name: str = Field(..., min_length=2, max_length=255)
    slug: str | None = None  # Auto-generated if not provided
    description: str | None = None
    short_description: str | None = None
    
    # ===== PRODUCT TYPE =====
    product_type: str = Field(default=ProductType.STORY_BOOK.value, description="story_book, coloring_book, or audio_addon")
    type_specific_data: dict | None = Field(None, description="Type-specific metadata (JSONB)")

    # ===== TEMPLATE REFERENCES =====
    cover_template_id: UUID | None = None
    inner_template_id: UUID | None = None
    back_template_id: UUID | None = None
    ai_config_id: UUID | None = None

    # ===== PAGE SETTINGS =====
    default_page_count: int = Field(default=16, ge=4, le=64)
    min_page_count: int = Field(default=12, ge=4)
    max_page_count: int = Field(default=32, ge=4, le=64)

    # ===== PAPER & COVER =====
    paper_type: str = "Kuşe 170gr"
    paper_finish: str = "Mat"
    cover_type: str = "Sert Kapak"
    lamination: str | None = None

    # ===== PRICING =====
    base_price: Decimal = Field(..., gt=0)
    discounted_price: Decimal | None = Field(None, description="Sale price if promo active")
    extra_page_price: Decimal = Field(default=Decimal("5.0"), ge=0)
    production_cost: Decimal | None = None
    vat_rate: Decimal = Field(default=Decimal("10.00"), ge=0, le=100, description="KDV oranı (%)")

    # ===== VISIBILITY =====
    is_active: bool = True
    is_featured: bool = False
    display_order: int = 0

    # ===== MEDIA =====
    thumbnail_url: str | None = None
    gallery_images: list[str] | None = None
    video_url: str | None = Field(None, description="Product promo video URL")

    # ===== FLIPBOOK PREVIEW =====
    sample_images: list[str] | None = Field(
        default=None,
        description="Sample page images for flipbook preview [cover, page1, page2, ...]",
    )
    orientation: str = Field(
        default="landscape", description="Book orientation: portrait or landscape"
    )

    # ===== MARKETING & URGENCY =====
    promo_badge: str | None = Field(
        None, max_length=100, description="E.g., '%20 İndirim', 'En Çok Satan'"
    )
    promo_end_date: datetime | None = Field(None, description="Countdown timer end date")
    is_gift_wrapped: bool = Field(default=False, description="Hediye paketi seçeneği")

    # ===== SOCIAL PROOF =====
    rating: float | None = Field(None, ge=0, le=5, description="Product rating (0-5)")
    review_count: int = Field(default=0, ge=0, description="Number of reviews")
    social_proof_text: str | None = Field(
        None, max_length=255, description="E.g., '500+ aile bayıldı!'"
    )

    # ===== FEATURES =====
    feature_list: list[str] | None = Field(
        default=None, description="Feature bullet points for product card"
    )

    @field_validator("gallery_images", "feature_list", "sample_images", mode="before")
    @classmethod
    def ensure_list(cls, v):
        """Ensure JSONB fields are lists."""
        if v is None:
            return []
        if isinstance(v, str):
            return [v]
        return list(v)


class ProductUpdate(BaseModel):
    """Update product request with all fields optional."""

    # ===== BASIC INFO =====
    name: str | None = None
    slug: str | None = None
    description: str | None = None
    short_description: str | None = None
    
    # ===== PRODUCT TYPE =====
    product_type: str | None = None
    type_specific_data: dict | None = None

    # ===== TEMPLATE REFERENCES =====
    cover_template_id: UUID | None = None
    inner_template_id: UUID | None = None
    back_template_id: UUID | None = None
    ai_config_id: UUID | None = None

    # ===== PAGE SETTINGS =====
    default_page_count: int | None = Field(default=None, ge=4, le=64)
    min_page_count: int | None = Field(default=None, ge=4)
    max_page_count: int | None = Field(default=None, ge=4, le=64)

    # ===== PAPER & COVER =====
    paper_type: str | None = None
    paper_finish: str | None = None
    cover_type: str | None = None
    lamination: str | None = None

    # ===== PRICING =====
    base_price: Decimal | None = Field(default=None, gt=0)
    discounted_price: Decimal | None = None
    extra_page_price: Decimal | None = Field(default=None, ge=0)
    production_cost: Decimal | None = None
    vat_rate: Decimal | None = Field(default=None, ge=0, le=100, description="KDV oranı (%)")

    # ===== VISIBILITY =====
    is_active: bool | None = None
    is_featured: bool | None = None
    display_order: int | None = None

    # ===== MEDIA =====
    thumbnail_url: str | None = None
    gallery_images: list[str] | None = None
    video_url: str | None = None

    # ===== FLIPBOOK PREVIEW =====
    sample_images: list[str] | None = None
    orientation: str | None = None

    # ===== MARKETING & URGENCY =====
    promo_badge: str | None = None
    promo_end_date: datetime | None = None
    is_gift_wrapped: bool | None = None

    # ===== SOCIAL PROOF =====
    rating: float | None = Field(None, ge=0, le=5)
    review_count: int | None = Field(None, ge=0)
    social_proof_text: str | None = None

    # ===== FEATURES =====
    feature_list: list[str] | None = None


def slugify(text: str) -> str:
    """Convert text to URL-friendly slug."""
    # Turkish character mapping
    tr_map = {
        "ı": "i",
        "İ": "i",
        "ğ": "g",
        "Ğ": "g",
        "ü": "u",
        "Ü": "u",
        "ş": "s",
        "Ş": "s",
        "ö": "o",
        "Ö": "o",
        "ç": "c",
        "Ç": "c",
    }
    for tr_char, en_char in tr_map.items():
        text = text.replace(tr_char, en_char)

    # Convert to lowercase and replace spaces/special chars
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    text = re.sub(r"-+", "-", text)
    return text.strip("-")


# =============================================================================
# PRODUCT ENDPOINTS
# =============================================================================


@router.get("")
async def list_products(
    db: DbSession,
    admin: SuperAdminUser,
    include_inactive: bool = False,
    product_type: str | None = Query(None, description="Filter by product type: story_book, coloring_book, audio_addon"),
) -> list[dict]:
    """List all products with template info. Optionally filter by product_type."""
    query = (
        select(Product)
        .options(
            selectinload(Product.cover_template),
            selectinload(Product.inner_template),
            selectinload(Product.back_template),
            selectinload(Product.ai_config),
        )
        .order_by(Product.display_order, Product.name)
    )

    if not include_inactive:
        query = query.where(Product.is_active == True)
    
    if product_type:
        query = query.where(Product.product_type == product_type)

    result = await db.execute(query)
    products = result.scalars().all()

    return [
        {
            "id": str(p.id),
            "name": p.name,
            "slug": p.slug,
            "description": p.description,
            "short_description": p.short_description,
            # Product Type
            "product_type": p.product_type,
            "type_specific_data": p.type_specific_data,
            # Templates
            "cover_template": {
                "id": str(p.cover_template.id),
                "name": p.cover_template.name,
                "page_width_mm": p.cover_template.page_width_mm,
                "page_height_mm": p.cover_template.page_height_mm,
            }
            if p.cover_template
            else None,
            "inner_template": {
                "id": str(p.inner_template.id),
                "name": p.inner_template.name,
                "page_width_mm": p.inner_template.page_width_mm,
                "page_height_mm": p.inner_template.page_height_mm,
            }
            if p.inner_template
            else None,
            "back_template": {
                "id": str(p.back_template.id),
                "name": p.back_template.name,
                "page_width_mm": p.back_template.page_width_mm,
                "page_height_mm": p.back_template.page_height_mm,
            }
            if p.back_template
            else None,
            "ai_config": {
                "id": str(p.ai_config.id),
                "name": p.ai_config.name,
            }
            if p.ai_config
            else None,
            # Page settings
            "default_page_count": p.default_page_count,
            "min_page_count": p.min_page_count,
            "max_page_count": p.max_page_count,
            # Paper & Cover
            "paper_type": p.paper_type,
            "paper_finish": p.paper_finish,
            "cover_type": p.cover_type,
            "lamination": p.lamination,
            # Pricing
            "base_price": float(p.base_price),
            "discounted_price": float(p.discounted_price) if p.discounted_price else None,
            "extra_page_price": float(p.extra_page_price) if p.extra_page_price else 5.0,
            "production_cost": float(p.production_cost) if p.production_cost else None,
            "vat_rate": float(p.vat_rate) if p.vat_rate is not None else 10.0,
            "discount_percentage": p.discount_percentage,
            # Visibility
            "is_active": p.is_active,
            "is_featured": p.is_featured,
            "display_order": p.display_order,
            # Media
            "thumbnail_url": p.thumbnail_url,
            "gallery_images": p.gallery_images,
            "video_url": p.video_url,
            # Flipbook Preview
            "sample_images": p.sample_images or [],
            "orientation": p.orientation or "landscape",
            # Marketing & Urgency
            "promo_badge": p.promo_badge,
            "promo_end_date": p.promo_end_date.isoformat() if p.promo_end_date else None,
            "promo_days_remaining": p.promo_days_remaining,
            "is_gift_wrapped": p.is_gift_wrapped,
            # Social Proof
            "rating": p.rating,
            "review_count": p.review_count,
            "social_proof_text": p.social_proof_text,
            # Features
            "feature_list": p.feature_list or [],
            # Timestamps
            "created_at": p.created_at.isoformat() if p.created_at else None,
        }
        for p in products
    ]


@router.get("/{product_id}")
async def get_product(
    product_id: UUID,
    db: DbSession,
    admin: SuperAdminUser,
) -> dict:
    """Get a single product with full details."""
    result = await db.execute(
        select(Product)
        .options(
            selectinload(Product.cover_template),
            selectinload(Product.inner_template),
            selectinload(Product.back_template),
            selectinload(Product.ai_config),
        )
        .where(Product.id == product_id)
    )
    product = result.scalar_one_or_none()

    if not product:
        raise NotFoundError("Ürün", product_id)

    return {
        "id": str(product.id),
        "name": product.name,
        "slug": product.slug,
        "description": product.description,
        "short_description": product.short_description,
        # Product Type
        "product_type": product.product_type,
        "type_specific_data": product.type_specific_data,
        # Template IDs
        "cover_template_id": str(product.cover_template_id) if product.cover_template_id else None,
        "inner_template_id": str(product.inner_template_id) if product.inner_template_id else None,
        "back_template_id": str(product.back_template_id) if product.back_template_id else None,
        "ai_config_id": str(product.ai_config_id) if product.ai_config_id else None,
        # Page settings
        "default_page_count": product.default_page_count,
        "min_page_count": product.min_page_count,
        "max_page_count": product.max_page_count,
        # Paper & Cover
        "paper_type": product.paper_type,
        "paper_finish": product.paper_finish,
        "cover_type": product.cover_type,
        "lamination": product.lamination,
        # Pricing
        "base_price": float(product.base_price),
        "discounted_price": float(product.discounted_price) if product.discounted_price else None,
        "extra_page_price": float(product.extra_page_price) if product.extra_page_price else 5.0,
        "production_cost": float(product.production_cost) if product.production_cost else None,
        "vat_rate": float(product.vat_rate) if product.vat_rate is not None else 10.0,
        # Visibility
        "is_active": product.is_active,
        "is_featured": product.is_featured,
        "display_order": product.display_order,
        # Media
        "thumbnail_url": product.thumbnail_url,
        "gallery_images": product.gallery_images,
        "video_url": product.video_url,
        # Flipbook Preview
        "sample_images": product.sample_images or [],
        "orientation": product.orientation or "landscape",
        # Marketing & Urgency
        "promo_badge": product.promo_badge,
        "promo_end_date": product.promo_end_date.isoformat() if product.promo_end_date else None,
        "is_gift_wrapped": product.is_gift_wrapped,
        # Social Proof
        "rating": product.rating,
        "review_count": product.review_count,
        "social_proof_text": product.social_proof_text,
        # Features
        "feature_list": product.feature_list or [],
    }


@router.post("")
async def create_product(
    request: ProductCreate,
    db: DbSession,
    admin: SuperAdminUser,
) -> dict:
    """Create a new product."""
    # Generate slug if not provided
    slug = request.slug or slugify(request.name)

    # Check for duplicate name or slug
    result = await db.execute(
        select(Product).where((Product.name == request.name) | (Product.slug == slug))
    )
    if result.scalar_one_or_none():
        raise ConflictError(f"'{request.name}' adında veya '{slug}' slug'ında bir ürün zaten var")

    # Validate template references
    if request.cover_template_id:
        cover = await db.execute(
            select(PageTemplate).where(PageTemplate.id == request.cover_template_id)
        )
        if not cover.scalar_one_or_none():
            raise NotFoundError("Ön kapak şablonu", request.cover_template_id)

    if request.inner_template_id:
        inner = await db.execute(
            select(PageTemplate).where(PageTemplate.id == request.inner_template_id)
        )
        if not inner.scalar_one_or_none():
            raise NotFoundError("İç sayfa şablonu", request.inner_template_id)

    if request.back_template_id:
        back = await db.execute(
            select(PageTemplate).where(PageTemplate.id == request.back_template_id)
        )
        if not back.scalar_one_or_none():
            raise NotFoundError("Arka kapak şablonu", request.back_template_id)

    product_data = request.model_dump()
    product_data["slug"] = slug

    product = Product(**product_data)
    db.add(product)
    await db.commit()
    await db.refresh(product)

    return {
        "id": str(product.id),
        "name": product.name,
        "slug": product.slug,
        "message": "Ürün oluşturuldu",
    }


@router.patch("/{product_id}")
async def update_product(
    product_id: UUID,
    request: ProductUpdate,
    db: DbSession,
    admin: SuperAdminUser,
) -> dict:
    """Update a product."""
    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()

    if not product:
        raise NotFoundError("Ürün", product_id)

    # Check for slug conflict if changing
    if request.slug and request.slug != product.slug:
        existing = await db.execute(
            select(Product).where(Product.slug == request.slug, Product.id != product_id)
        )
        if existing.scalar_one_or_none():
            raise ConflictError(f"'{request.slug}' slug'ı zaten kullanılıyor")

    update_data = request.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(product, field, value)

    await db.commit()

    return {
        "id": str(product.id),
        "name": product.name,
        "message": "Ürün güncellendi",
    }


@router.delete("/{product_id}")
async def delete_product(
    product_id: UUID,
    db: DbSession,
    admin: SuperAdminUser,
) -> dict:
    """Delete a product."""
    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()

    if not product:
        raise NotFoundError("Ürün", product_id)

    await db.delete(product)
    await db.commit()

    return {"message": "Ürün silindi"}


@router.post("/{product_id}/duplicate")
async def duplicate_product(
    product_id: UUID,
    db: DbSession,
    admin: SuperAdminUser,
) -> dict:
    """Duplicate a product."""
    result = await db.execute(select(Product).where(Product.id == product_id))
    original = result.scalar_one_or_none()

    if not original:
        raise NotFoundError("Ürün", product_id)

    # Create new name and slug
    new_name = f"{original.name} (Kopya)"
    new_slug = f"{original.slug}-kopya"

    # Find unique name/slug
    counter = 1
    while True:
        result = await db.execute(
            select(Product).where((Product.name == new_name) | (Product.slug == new_slug))
        )
        if not result.scalar_one_or_none():
            break
        counter += 1
        new_name = f"{original.name} (Kopya {counter})"
        new_slug = f"{original.slug}-kopya-{counter}"

    # Create duplicate
    new_product = Product(
        # Basic Info
        name=new_name,
        slug=new_slug,
        description=original.description,
        short_description=original.short_description,
        # Product Type
        product_type=original.product_type,
        type_specific_data=original.type_specific_data.copy() if original.type_specific_data else None,
        # Templates
        cover_template_id=original.cover_template_id,
        inner_template_id=original.inner_template_id,
        back_template_id=original.back_template_id,
        ai_config_id=original.ai_config_id,
        # Page settings
        default_page_count=original.default_page_count,
        min_page_count=original.min_page_count,
        max_page_count=original.max_page_count,
        # Paper & Cover
        paper_type=original.paper_type,
        paper_finish=original.paper_finish,
        cover_type=original.cover_type,
        lamination=original.lamination,
        # Pricing (copy prices but not promo)
        base_price=original.base_price,
        discounted_price=None,  # Don't copy promo price
        extra_page_price=original.extra_page_price,
        production_cost=original.production_cost,
        # Visibility
        is_active=False,  # Start as inactive
        is_featured=False,
        display_order=original.display_order + 1,
        # Media
        thumbnail_url=original.thumbnail_url,
        gallery_images=original.gallery_images,
        video_url=original.video_url,
        # Flipbook Preview
        sample_images=original.sample_images.copy() if original.sample_images else [],
        orientation=original.orientation or "landscape",
        # Marketing (don't copy promo, but keep features)
        promo_badge=None,  # Don't copy badge
        promo_end_date=None,  # Don't copy countdown
        is_gift_wrapped=original.is_gift_wrapped,
        # Social Proof (reset for new product)
        rating=None,
        review_count=0,
        social_proof_text=None,
        # Features (copy the list)
        feature_list=original.feature_list.copy() if original.feature_list else [],
    )

    db.add(new_product)
    await db.commit()
    await db.refresh(new_product)

    return {
        "id": str(new_product.id),
        "name": new_product.name,
        "message": "Ürün kopyalandı",
    }


# =============================================================================
# TEMPLATE & CONFIG DROPDOWNS
# =============================================================================


@router.get("/options/templates")
async def get_template_options(
    db: DbSession,
    admin: SuperAdminUser,
) -> dict:
    """Get available templates for dropdown selections."""
    # Get page templates grouped by type
    result = await db.execute(
        select(PageTemplate).where(PageTemplate.is_active == True).order_by(PageTemplate.name)
    )
    templates = result.scalars().all()

    cover_templates = []
    inner_templates = []
    back_templates = []

    for t in templates:
        template_data = {
            "id": str(t.id),
            "name": t.name,
            "page_width_mm": t.page_width_mm,
            "page_height_mm": t.page_height_mm,
        }
        if t.page_type == "cover":
            cover_templates.append(template_data)
        elif t.page_type == "inner":
            inner_templates.append(template_data)
        elif t.page_type == "back":
            back_templates.append(template_data)

    # Get AI configs
    result = await db.execute(
        select(AIGenerationConfig)
        .where(AIGenerationConfig.is_active == True)
        .order_by(AIGenerationConfig.name)
    )
    ai_configs = [
        {"id": str(c.id), "name": c.name, "image_provider": c.image_provider}
        for c in result.scalars().all()
    ]

    return {
        "cover_templates": cover_templates,
        "inner_templates": inner_templates,
        "back_templates": back_templates,
        "ai_configs": ai_configs,
    }

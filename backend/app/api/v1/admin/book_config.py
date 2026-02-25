"""Admin endpoints for book configuration management."""

from uuid import UUID

from fastapi import APIRouter
from pydantic import BaseModel, Field
from sqlalchemy import select

from app.api.v1.deps import DbSession, SuperAdminUser
from app.core.exceptions import ConflictError, NotFoundError
from app.models.book_template import AIGenerationConfig, BookTemplate, PageTemplate

router = APIRouter()


# =============================================================================
# REQUEST/RESPONSE SCHEMAS
# =============================================================================


class BookTemplateCreate(BaseModel):
    """Create book template request."""

    name: str = Field(..., min_length=2, max_length=100)
    description: str | None = None
    page_width_mm: float = Field(default=210.0, gt=0)
    page_height_mm: float = Field(default=210.0, gt=0)
    bleed_mm: float = Field(default=3.0, ge=0)
    image_dpi: int = Field(default=300, ge=72, le=600)
    default_page_count: int = Field(default=16, ge=8, le=64)
    min_page_count: int = Field(default=12, ge=8)
    max_page_count: int = Field(default=32, le=64)
    is_active: bool = True
    is_default: bool = False


class BookTemplateUpdate(BaseModel):
    """Update book template request."""

    name: str | None = None
    description: str | None = None
    page_width_mm: float | None = Field(default=None, gt=0)
    page_height_mm: float | None = Field(default=None, gt=0)
    bleed_mm: float | None = Field(default=None, ge=0)
    image_dpi: int | None = Field(default=None, ge=72, le=600)
    default_page_count: int | None = Field(default=None, ge=8, le=64)
    is_active: bool | None = None
    is_default: bool | None = None


class PageTemplateCreate(BaseModel):
    """Create page template request."""

    name: str = Field(..., min_length=2, max_length=100)
    page_type: str = "inner"  # cover, inner, back, dedication

    # Physical dimensions (mm) - each page type can have different size
    page_width_mm: float = Field(default=297.0, gt=0)
    page_height_mm: float = Field(default=210.0, gt=0)
    bleed_mm: float = Field(default=3.0, ge=0)

    # Image area
    image_width_percent: float = Field(default=100.0, ge=0, le=100)
    image_height_percent: float = Field(default=70.0, ge=0, le=100)
    image_x_percent: float = Field(default=0.0, ge=0, le=100)
    image_y_percent: float = Field(default=0.0, ge=0, le=100)
    image_aspect_ratio: str = "1:1"

    # Text visibility - allows hiding text completely (e.g., for covers)
    text_enabled: bool = True

    # Text area (only used if text_enabled=True)
    text_width_percent: float = Field(default=90.0, ge=0, le=100)
    text_height_percent: float = Field(default=25.0, ge=0, le=100)
    text_x_percent: float = Field(default=5.0, ge=0, le=100)
    text_y_percent: float = Field(default=72.0, ge=0, le=100)
    text_position: str = "bottom"

    # Text styling
    font_family: str = "Nunito"
    font_size_pt: int = Field(default=14, ge=8, le=732)
    font_color: str = "#333333"
    font_weight: str = "normal"
    text_align: str = "center"
    line_height: float = Field(default=1.5, ge=1.0, le=3.0)

    # Background
    background_color: str = "#FFFFFF"

    # Text Stroke (Outline)
    text_stroke_enabled: bool = False
    text_stroke_color: str = "#000000"
    text_stroke_width: float = Field(default=1.0, ge=0, le=10)

    # Text Background Gradient (metin arkası gölge)
    text_bg_enabled: bool = True
    text_bg_color: str = "#000000"
    text_bg_opacity: int = Field(default=180, ge=0, le=255)
    text_bg_shape: str = "soft_vignette"
    text_bg_blur: int = Field(default=30, ge=0, le=80)

    # Cover Title — WordArt kapak başlığı
    cover_title_enabled: bool = True
    cover_title_font_family: str = "Lobster"
    cover_title_font_size_pt: int = Field(default=48, ge=16, le=96)
    cover_title_font_color: str = "#FFD700"
    cover_title_arc_intensity: int = Field(default=35, ge=0, le=100)
    cover_title_shadow_enabled: bool = True
    cover_title_shadow_color: str = "#000000"
    cover_title_shadow_offset: int = Field(default=3, ge=0, le=15)
    cover_title_stroke_width: float = Field(default=2.0, ge=0, le=10)
    cover_title_stroke_color: str = "#8B6914"
    cover_title_y_percent: float = Field(default=5.0, ge=0, le=50)
    cover_title_preset: str = "premium"
    cover_title_effect: str = "gold_shine"
    cover_title_letter_spacing: int = Field(default=0, ge=-5, le=20)

    # Margins
    margin_top_mm: float = Field(default=10.0, ge=0)
    margin_bottom_mm: float = Field(default=10.0, ge=0)
    margin_left_mm: float = Field(default=10.0, ge=0)
    margin_right_mm: float = Field(default=10.0, ge=0)

    # Dedication page default text (only for page_type="dedication")
    dedication_default_text: str | None = None

    is_active: bool = True


class PageTemplateUpdate(BaseModel):
    """Update page template request."""

    name: str | None = None
    page_type: str | None = None
    # Physical dimensions
    page_width_mm: float | None = Field(default=None, gt=0)
    page_height_mm: float | None = Field(default=None, gt=0)
    bleed_mm: float | None = Field(default=None, ge=0)
    # Image area
    image_width_percent: float | None = Field(default=None, ge=0, le=100)
    image_height_percent: float | None = Field(default=None, ge=0, le=100)
    image_x_percent: float | None = Field(default=None, ge=0, le=100)
    image_y_percent: float | None = Field(default=None, ge=0, le=100)
    image_aspect_ratio: str | None = None
    # Text visibility
    text_enabled: bool | None = None
    # Text area
    text_width_percent: float | None = Field(default=None, ge=0, le=100)
    text_height_percent: float | None = Field(default=None, ge=0, le=100)
    text_x_percent: float | None = Field(default=None, ge=0, le=100)
    text_y_percent: float | None = Field(default=None, ge=0, le=100)
    text_position: str | None = None
    font_family: str | None = None
    font_size_pt: int | None = Field(default=None, ge=8, le=732)
    font_color: str | None = None
    font_weight: str | None = None
    text_align: str | None = None
    line_height: float | None = Field(default=None, ge=1.0, le=3.0)
    background_color: str | None = None
    # Text Stroke (Outline)
    text_stroke_enabled: bool | None = None
    text_stroke_color: str | None = None
    text_stroke_width: float | None = Field(default=None, ge=0, le=10)
    # Text Background Gradient
    text_bg_enabled: bool | None = None
    text_bg_color: str | None = None
    text_bg_opacity: int | None = Field(default=None, ge=0, le=255)
    text_bg_shape: str | None = None
    text_bg_blur: int | None = Field(default=None, ge=0, le=80)
    # Cover Title — WordArt kapak başlığı
    cover_title_enabled: bool | None = None
    cover_title_font_family: str | None = None
    cover_title_font_size_pt: int | None = Field(default=None, ge=16, le=96)
    cover_title_font_color: str | None = None
    cover_title_arc_intensity: int | None = Field(default=None, ge=0, le=100)
    cover_title_shadow_enabled: bool | None = None
    cover_title_shadow_color: str | None = None
    cover_title_shadow_offset: int | None = Field(default=None, ge=0, le=15)
    cover_title_stroke_width: float | None = Field(default=None, ge=0, le=10)
    cover_title_stroke_color: str | None = None
    cover_title_y_percent: float | None = Field(default=None, ge=0, le=50)
    cover_title_preset: str | None = None
    cover_title_effect: str | None = None
    cover_title_letter_spacing: int | None = Field(default=None, ge=-5, le=20)
    # Margins
    margin_top_mm: float | None = None
    margin_bottom_mm: float | None = None
    margin_left_mm: float | None = None
    margin_right_mm: float | None = None
    # Dedication page default text
    dedication_default_text: str | None = None
    is_active: bool | None = None


class AIConfigCreate(BaseModel):
    """Create AI config request."""

    name: str = Field(..., min_length=2, max_length=100)
    description: str | None = None

    # Image generation
    image_provider: str = "fal"
    image_model: str = "gemini-2.5-flash-exp-image-generation"
    image_width: int = Field(default=1024, ge=256, le=4096)
    image_height: int = Field(default=1024, ge=256, le=4096)
    image_quality: str = "high"

    # Prompts
    style_prefix: str = "children's book illustration, vibrant colors, safe for children"
    style_suffix: str = "high quality, detailed, professional artwork"
    negative_prompt: str | None = None

    # Story generation
    story_provider: str = "gemini"
    story_model: str = "gemini-2.5-flash"
    story_temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    story_max_tokens: int = Field(default=8192, ge=1000, le=32000)

    is_active: bool = True
    is_default: bool = False


class AIConfigUpdate(BaseModel):
    """Update AI config request."""

    name: str | None = None
    description: str | None = None
    image_provider: str | None = None
    image_model: str | None = None
    image_width: int | None = Field(default=None, ge=256, le=4096)
    image_height: int | None = Field(default=None, ge=256, le=4096)
    style_prefix: str | None = None
    style_suffix: str | None = None
    negative_prompt: str | None = None
    story_provider: str | None = None
    story_model: str | None = None
    story_temperature: float | None = Field(default=None, ge=0.0, le=2.0)
    story_max_tokens: int | None = Field(default=None, ge=1000, le=32000)
    is_active: bool | None = None
    is_default: bool | None = None


# =============================================================================
# BOOK TEMPLATE ENDPOINTS
# =============================================================================


@router.get("/book-templates")
async def list_book_templates(
    db: DbSession,
    admin: SuperAdminUser,
) -> list[dict]:
    """List all book templates."""
    result = await db.execute(select(BookTemplate).order_by(BookTemplate.created_at.desc()))
    templates = result.scalars().all()

    return [
        {
            "id": str(t.id),
            "name": t.name,
            "description": t.description,
            "page_width_mm": t.page_width_mm,
            "page_height_mm": t.page_height_mm,
            "bleed_mm": t.bleed_mm,
            "image_dpi": t.image_dpi,
            "default_page_count": t.default_page_count,
            "is_active": t.is_active,
            "is_default": t.is_default,
            "created_at": t.created_at.isoformat() if t.created_at else None,
        }
        for t in templates
    ]


@router.post("/book-templates")
async def create_book_template(
    request: BookTemplateCreate,
    db: DbSession,
    admin: SuperAdminUser,
) -> dict:
    """Create a new book template."""
    # Check for duplicate
    result = await db.execute(select(BookTemplate).where(BookTemplate.name == request.name))
    if result.scalar_one_or_none():
        raise ConflictError(f"'{request.name}' adında bir şablon zaten var")

    # If this is default, unset other defaults
    if request.is_default:
        await db.execute(BookTemplate.__table__.update().values(is_default=False))

    template = BookTemplate(**request.model_dump())
    db.add(template)
    await db.commit()
    await db.refresh(template)

    return {
        "id": str(template.id),
        "name": template.name,
        "message": "Kitap şablonu oluşturuldu",
    }


@router.patch("/book-templates/{template_id}")
async def update_book_template(
    template_id: UUID,
    request: BookTemplateUpdate,
    db: DbSession,
    admin: SuperAdminUser,
) -> dict:
    """Update a book template."""
    result = await db.execute(select(BookTemplate).where(BookTemplate.id == template_id))
    template = result.scalar_one_or_none()

    if not template:
        raise NotFoundError("Kitap şablonu", template_id)

    # If setting as default, unset others
    if request.is_default:
        await db.execute(BookTemplate.__table__.update().values(is_default=False))

    update_data = request.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(template, field, value)

    await db.commit()

    return {
        "id": str(template.id),
        "name": template.name,
        "message": "Kitap şablonu güncellendi",
    }


@router.delete("/book-templates/{template_id}")
async def delete_book_template(
    template_id: UUID,
    db: DbSession,
    admin: SuperAdminUser,
) -> dict:
    """Delete a book template."""
    result = await db.execute(select(BookTemplate).where(BookTemplate.id == template_id))
    template = result.scalar_one_or_none()

    if not template:
        raise NotFoundError("Kitap şablonu", template_id)

    await db.delete(template)
    await db.commit()

    return {"message": "Kitap şablonu silindi"}


# =============================================================================
# PAGE TEMPLATE ENDPOINTS
# =============================================================================


@router.get("/page-templates")
async def list_page_templates(
    db: DbSession,
    admin: SuperAdminUser,
) -> list[dict]:
    """List all page templates. Include updated_at so frontend can show the same template used in composition (latest per page_type)."""
    result = await db.execute(
        select(PageTemplate).order_by(PageTemplate.page_type, PageTemplate.name)
    )
    templates = result.scalars().all()

    def _serialize(t: PageTemplate) -> dict:
        return {
            "id": str(t.id),
            "name": t.name,
            "page_type": t.page_type,
            "updated_at": t.updated_at.isoformat() if getattr(t, "updated_at", None) else None,
            "page_width_mm": t.page_width_mm,
            "page_height_mm": t.page_height_mm,
            "bleed_mm": t.bleed_mm,
            "image_width_percent": t.image_width_percent,
            "image_height_percent": t.image_height_percent,
            "image_x_percent": t.image_x_percent,
            "image_y_percent": t.image_y_percent,
            "image_aspect_ratio": t.image_aspect_ratio,
            "text_enabled": t.text_enabled,
            "text_width_percent": t.text_width_percent,
            "text_height_percent": t.text_height_percent,
            "text_x_percent": t.text_x_percent,
            "text_y_percent": t.text_y_percent,
            "text_position": t.text_position,
            "font_family": t.font_family,
            "font_size_pt": t.font_size_pt,
            "font_color": t.font_color,
            "font_weight": getattr(t, "font_weight", "normal") or "normal",
            "text_align": t.text_align,
            "background_color": t.background_color,
            "text_stroke_enabled": t.text_stroke_enabled,
            "text_stroke_color": t.text_stroke_color,
            "text_stroke_width": t.text_stroke_width,
            "text_bg_enabled": t.text_bg_enabled,
            "text_bg_color": t.text_bg_color,
            "text_bg_opacity": t.text_bg_opacity,
            "text_bg_shape": t.text_bg_shape,
            "text_bg_blur": t.text_bg_blur,
            "cover_title_enabled": t.cover_title_enabled,
            "cover_title_font_family": t.cover_title_font_family,
            "cover_title_font_size_pt": t.cover_title_font_size_pt,
            "cover_title_font_color": t.cover_title_font_color,
            "cover_title_arc_intensity": t.cover_title_arc_intensity,
            "cover_title_shadow_enabled": t.cover_title_shadow_enabled,
            "cover_title_shadow_color": t.cover_title_shadow_color,
            "cover_title_shadow_offset": t.cover_title_shadow_offset,
            "cover_title_stroke_width": t.cover_title_stroke_width,
            "cover_title_stroke_color": t.cover_title_stroke_color,
            "cover_title_y_percent": t.cover_title_y_percent,
            "cover_title_preset": getattr(t, "cover_title_preset", "premium") or "premium",
            "cover_title_effect": getattr(t, "cover_title_effect", "gold_shine") or "gold_shine",
            "cover_title_letter_spacing": getattr(t, "cover_title_letter_spacing", 0) or 0,
            "dedication_default_text": getattr(t, "dedication_default_text", None),
            "is_active": t.is_active,
        }

    return [_serialize(t) for t in templates]


@router.post("/page-templates")
async def create_page_template(
    request: PageTemplateCreate,
    db: DbSession,
    admin: SuperAdminUser,
) -> dict:
    """Create a new page template."""
    template = PageTemplate(**request.model_dump())
    db.add(template)
    await db.commit()
    await db.refresh(template)

    return {
        "id": str(template.id),
        "name": template.name,
        "message": "Sayfa şablonu oluşturuldu",
    }


@router.patch("/page-templates/{template_id}")
async def update_page_template(
    template_id: UUID,
    request: PageTemplateUpdate,
    db: DbSession,
    admin: SuperAdminUser,
) -> dict:
    """Update a page template."""
    result = await db.execute(select(PageTemplate).where(PageTemplate.id == template_id))
    template = result.scalar_one_or_none()

    if not template:
        raise NotFoundError("Sayfa şablonu", template_id)

    # Get all fields that are not None
    update_data = {k: v for k, v in request.model_dump().items() if v is not None}

    for field, value in update_data.items():
        setattr(template, field, value)

    await db.commit()

    return {
        "id": str(template.id),
        "name": template.name,
        "message": "Sayfa şablonu güncellendi",
    }


@router.delete("/page-templates/{template_id}")
async def delete_page_template(
    template_id: UUID,
    db: DbSession,
    admin: SuperAdminUser,
) -> dict:
    """Delete a page template."""
    result = await db.execute(select(PageTemplate).where(PageTemplate.id == template_id))
    template = result.scalar_one_or_none()

    if not template:
        raise NotFoundError("Sayfa şablonu", template_id)

    await db.delete(template)
    await db.commit()

    return {"message": "Sayfa şablonu silindi"}


# =============================================================================
# AI CONFIGURATION ENDPOINTS
# =============================================================================


@router.get("/ai-configs")
async def list_ai_configs(
    db: DbSession,
    admin: SuperAdminUser,
) -> list[dict]:
    """List all AI configurations."""
    result = await db.execute(
        select(AIGenerationConfig).order_by(AIGenerationConfig.created_at.desc())
    )
    configs = result.scalars().all()

    return [
        {
            "id": str(c.id),
            "name": c.name,
            "description": c.description,
            "image_provider": c.image_provider,
            "image_model": c.image_model,
            "image_width": c.image_width,
            "image_height": c.image_height,
            "story_provider": c.story_provider,
            "story_model": c.story_model,
            "story_temperature": c.story_temperature,
            "is_active": c.is_active,
            "is_default": c.is_default,
        }
        for c in configs
    ]


@router.post("/ai-configs")
async def create_ai_config(
    request: AIConfigCreate,
    db: DbSession,
    admin: SuperAdminUser,
) -> dict:
    """Create a new AI configuration."""
    # Check for duplicate
    result = await db.execute(
        select(AIGenerationConfig).where(AIGenerationConfig.name == request.name)
    )
    if result.scalar_one_or_none():
        raise ConflictError(f"'{request.name}' adında bir yapılandırma zaten var")

    # If this is default, unset other defaults
    if request.is_default:
        await db.execute(AIGenerationConfig.__table__.update().values(is_default=False))

    config = AIGenerationConfig(**request.model_dump())
    db.add(config)
    await db.commit()
    await db.refresh(config)

    return {
        "id": str(config.id),
        "name": config.name,
        "message": "AI yapılandırması oluşturuldu",
    }


@router.patch("/ai-configs/{config_id}")
async def update_ai_config(
    config_id: UUID,
    request: AIConfigUpdate,
    db: DbSession,
    admin: SuperAdminUser,
) -> dict:
    """Update an AI configuration."""
    result = await db.execute(select(AIGenerationConfig).where(AIGenerationConfig.id == config_id))
    config = result.scalar_one_or_none()

    if not config:
        raise NotFoundError("AI yapılandırması", config_id)

    # If setting as default, unset others
    if request.is_default:
        await db.execute(AIGenerationConfig.__table__.update().values(is_default=False))

    update_data = request.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(config, field, value)

    await db.commit()

    return {
        "id": str(config.id),
        "name": config.name,
        "message": "AI yapılandırması güncellendi",
    }


@router.delete("/ai-configs/{config_id}")
async def delete_ai_config(
    config_id: UUID,
    db: DbSession,
    admin: SuperAdminUser,
) -> dict:
    """Delete an AI configuration."""
    result = await db.execute(select(AIGenerationConfig).where(AIGenerationConfig.id == config_id))
    config = result.scalar_one_or_none()

    if not config:
        raise NotFoundError("AI yapılandırması", config_id)

    await db.delete(config)
    await db.commit()

    return {"message": "AI yapılandırması silindi"}


# =============================================================================
# QUICK PREVIEW
# =============================================================================


@router.get("/preview-config")
async def get_preview_config(db: DbSession, admin: SuperAdminUser) -> dict:
    """Get current active configuration for preview."""

    # Get default book template
    result = await db.execute(
        select(BookTemplate).where(BookTemplate.is_active == True, BookTemplate.is_default == True)
    )
    book_template = result.scalar_one_or_none()

    # Get page templates
    result = await db.execute(select(PageTemplate).where(PageTemplate.is_active == True))
    page_templates = result.scalars().all()

    # Get default AI config
    result = await db.execute(
        select(AIGenerationConfig).where(
            AIGenerationConfig.is_active == True, AIGenerationConfig.is_default == True
        )
    )
    ai_config = result.scalar_one_or_none()

    return {
        "book_template": {
            "id": str(book_template.id) if book_template else None,
            "name": book_template.name if book_template else "Varsayılan",
            "page_width_mm": book_template.page_width_mm if book_template else 297,
            "page_height_mm": book_template.page_height_mm if book_template else 210,
            "image_dpi": book_template.image_dpi if book_template else 300,
        }
        if book_template
        else None,
        "page_templates": [
            {
                "id": str(pt.id),
                "name": pt.name,
                "page_type": pt.page_type,
                "page_width_mm": pt.page_width_mm,
                "page_height_mm": pt.page_height_mm,
                "image_aspect_ratio": pt.image_aspect_ratio,
            }
            for pt in page_templates
        ],
        "ai_config": {
            "id": str(ai_config.id) if ai_config else None,
            "name": ai_config.name if ai_config else "Varsayılan",
            "image_provider": ai_config.image_provider if ai_config else "fal",
            "image_width": ai_config.image_width if ai_config else 1024,
            "image_height": ai_config.image_height if ai_config else 1024,
        }
        if ai_config
        else None,
    }

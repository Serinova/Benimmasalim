"""Admin endpoints for back cover configuration."""

from uuid import UUID

import structlog
from fastapi import APIRouter
from pydantic import BaseModel, Field
from sqlalchemy import select

from app.api.v1.admin.book_config import _ensure_single_default
from app.api.v1.deps import DbSession, SuperAdminUser
from app.core.exceptions import NotFoundError
from app.models.book_template import BackCoverConfig

logger = structlog.get_logger()
router = APIRouter()


# ─────────────────────────────────────────────────────────────────────────────
# SHARED helper — DB satırını dict'e çevirir (response builder tekrarını önler)
# ─────────────────────────────────────────────────────────────────────────────

def _to_response(c: BackCoverConfig) -> "BackCoverConfigResponse":
    return BackCoverConfigResponse(
        id=str(c.id),
        name=c.name,
        company_name=c.company_name,
        company_website=c.company_website,
        company_email=c.company_email,
        company_phone=c.company_phone,
        background_color=c.background_color,
        background_gradient_end=c.background_gradient_end,
        primary_color=c.primary_color,
        accent_color=c.accent_color,
        text_color=c.text_color,
        qr_enabled=c.qr_enabled,
        qr_size_mm=c.qr_size_mm,
        qr_position=c.qr_position,
        qr_label=c.qr_label,
        tips_title=c.tips_title,
        tips_content=c.tips_content,
        tips_font_size=c.tips_font_size,
        tagline=c.tagline,
        dedication_text=c.dedication_text,
        copyright_text=c.copyright_text,
        show_stars=c.show_stars,
        show_border=c.show_border,
        border_color=c.border_color,
        show_decorative_lines=c.show_decorative_lines,
        is_active=c.is_active,
        is_default=c.is_default,
    )


# ─────────────────────────────────────────────────────────────────────────────
# SCHEMAS
# ─────────────────────────────────────────────────────────────────────────────

class BackCoverConfigCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    company_name: str = "Benim Masalım"
    company_website: str = "www.benimmasalim.com.tr"
    company_email: str = "info@benimmasalim.com.tr"
    company_phone: str | None = None

    background_color: str = "#FDF6EC"
    background_gradient_end: str = "#EDE4F8"
    primary_color: str = "#6B21A8"
    accent_color: str = "#F59E0B"
    text_color: str = "#2D1B4E"

    qr_enabled: bool = True
    qr_size_mm: float = 32.0
    qr_position: str = "bottom_right"
    qr_label: str = "Sesli Kitabı Dinle"

    tips_title: str = "Sevgili Ebeveyn,"
    tips_content: str = (
        "• Çocuğunuzla her gün düzenli okuma saati oluşturun\n"
        "• Okurken soru sorun: 'Sence ne olur?' diye merak uyandırın\n"
        "• Hikayedeki karakterleri birlikte canlandırın ve sesler çıkarın\n"
        "• Okuma sonrası çocuğunuzun hikayeyi kendi sözleriyle anlatmasını isteyin\n"
        "• Kitaptaki yerleri ve konuları günlük hayatla ilişkilendirin\n"
        "• Hayal gücünü desteklemek için birlikte resim çizin"
    )
    tips_font_size: int = 9

    tagline: str = "Her çocuk kendi masalının kahramanıdır."
    dedication_text: str = (
        "Bu kitap, senin için; merakın, cesaretinle büyüyen "
        "ve hayal dünyasıyla sınırları zorlayan sen için..."
    )
    copyright_text: str = "© 2025 Benim Masalım. Tüm hakları saklıdır."

    show_stars: bool = True
    show_border: bool = True
    border_color: str = "#C4B5FD"
    show_decorative_lines: bool = True

    is_active: bool = True
    is_default: bool = False


class BackCoverConfigUpdate(BaseModel):
    name: str | None = None
    company_name: str | None = None
    company_website: str | None = None
    company_email: str | None = None
    company_phone: str | None = None

    background_color: str | None = None
    background_gradient_end: str | None = None
    primary_color: str | None = None
    accent_color: str | None = None
    text_color: str | None = None

    qr_enabled: bool | None = None
    qr_size_mm: float | None = None
    qr_position: str | None = None
    qr_label: str | None = None

    tips_title: str | None = None
    tips_content: str | None = None
    tips_font_size: int | None = None

    tagline: str | None = None
    dedication_text: str | None = None
    copyright_text: str | None = None

    show_stars: bool | None = None
    show_border: bool | None = None
    border_color: str | None = None
    show_decorative_lines: bool | None = None

    is_active: bool | None = None
    is_default: bool | None = None


class BackCoverConfigResponse(BaseModel):
    id: str
    name: str
    company_name: str
    company_website: str
    company_email: str
    company_phone: str | None

    background_color: str
    background_gradient_end: str
    primary_color: str
    accent_color: str
    text_color: str

    qr_enabled: bool
    qr_size_mm: float
    qr_position: str
    qr_label: str

    tips_title: str
    tips_content: str
    tips_font_size: int

    tagline: str
    dedication_text: str
    copyright_text: str

    show_stars: bool
    show_border: bool
    border_color: str
    show_decorative_lines: bool

    is_active: bool
    is_default: bool

    class Config:
        from_attributes = True


# ─────────────────────────────────────────────────────────────────────────────
# ENDPOINTS
# ─────────────────────────────────────────────────────────────────────────────

@router.get("", response_model=list[BackCoverConfigResponse])
async def list_back_cover_configs(
    db: DbSession,
    admin: SuperAdminUser,
    include_inactive: bool = False,
):
    """List all back cover configurations."""
    query = select(BackCoverConfig)
    if not include_inactive:
        query = query.where(BackCoverConfig.is_active == True)  # noqa: E712
    query = query.order_by(BackCoverConfig.is_default.desc(), BackCoverConfig.name)
    result = await db.execute(query)
    return [_to_response(c) for c in result.scalars().all()]


@router.get("/default", response_model=BackCoverConfigResponse | None)
async def get_default_back_cover_config(db: DbSession, _admin: SuperAdminUser):
    """Get the default back cover configuration."""
    result = await db.execute(
        select(BackCoverConfig)
        .where(BackCoverConfig.is_default == True)  # noqa: E712
        .where(BackCoverConfig.is_active == True)  # noqa: E712
    )
    config = result.scalar_one_or_none()
    return _to_response(config) if config else None


@router.post("", response_model=BackCoverConfigResponse)
async def create_back_cover_config(
    request: BackCoverConfigCreate,
    db: DbSession,
    admin: SuperAdminUser,
):
    """Create a new back cover configuration."""
    if request.is_default:
        await _ensure_single_default(db, BackCoverConfig)

    config = BackCoverConfig(**request.model_dump())
    db.add(config)
    await db.commit()
    await db.refresh(config)

    logger.info("Back cover config created", config_id=str(config.id), name=config.name)
    return _to_response(config)


@router.get("/{config_id}", response_model=BackCoverConfigResponse)
async def get_back_cover_config(config_id: UUID, db: DbSession, admin: SuperAdminUser):
    """Get a specific back cover configuration."""
    config = await db.get(BackCoverConfig, config_id)
    if not config:
        raise NotFoundError("BackCoverConfig", config_id)
    return _to_response(config)


@router.patch("/{config_id}", response_model=BackCoverConfigResponse)
async def update_back_cover_config(
    config_id: UUID,
    request: BackCoverConfigUpdate,
    db: DbSession,
    admin: SuperAdminUser,
):
    """Update a back cover configuration."""
    config = await db.get(BackCoverConfig, config_id)
    if not config:
        raise NotFoundError("BackCoverConfig", config_id)

    if request.is_default:
        await _ensure_single_default(db, BackCoverConfig, exclude_id=config_id)

    update_data = request.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(config, field, value)

    await db.commit()
    await db.refresh(config)

    logger.info("Back cover config updated", config_id=str(config.id))
    return _to_response(config)


@router.delete("/{config_id}")
async def delete_back_cover_config(config_id: UUID, db: DbSession, admin: SuperAdminUser):
    """Delete (soft) a back cover configuration."""
    config = await db.get(BackCoverConfig, config_id)
    if not config:
        raise NotFoundError("BackCoverConfig", config_id)

    config.is_active = False
    await db.commit()

    logger.info("Back cover config deleted", config_id=str(config_id))
    return {"message": "İç kapak arkası yapılandırması silindi"}

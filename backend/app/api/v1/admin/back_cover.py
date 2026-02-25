"""Admin endpoints for back cover configuration."""

from uuid import UUID

import structlog
from fastapi import APIRouter
from pydantic import BaseModel, Field
from sqlalchemy import select

from app.api.v1.deps import AdminUser, DbSession
from app.core.exceptions import NotFoundError
from app.models.book_template import BackCoverConfig

logger = structlog.get_logger()
router = APIRouter()


class BackCoverConfigCreate(BaseModel):
    """Create back cover config request."""

    name: str = Field(..., min_length=1, max_length=100)
    company_name: str = "Benim Masalım"
    company_logo_url: str | None = None
    company_website: str = "www.benimmasalim.com"
    company_email: str = "info@benimmasalim.com"
    company_phone: str | None = None
    company_address: str | None = None

    background_color: str = "#F8F4F0"
    primary_color: str = "#6B46C1"
    text_color: str = "#333333"

    qr_enabled: bool = True
    qr_size_mm: float = 30.0
    qr_position: str = "bottom_right"
    qr_label: str = "Sesli Kitabı Dinle"

    tips_title: str = "Ebeveynlere Öneriler"
    tips_content: str = """• Çocuğunuzla birlikte okuyun, soru sorun
• Her gün düzenli okuma alışkanlığı oluşturun
• Hikayedeki karakterleri birlikte canlandırın
• Çocuğunuzun hayal gücünü destekleyin
• Okuma sonrası hikayeyi birlikte çizin"""
    tips_font_size: int = 10

    tagline: str = "Her çocuk kendi masalının kahramanı!"
    copyright_text: str = "© 2024 Benim Masalım. Tüm hakları saklıdır."

    show_stars: bool = True
    show_border: bool = True
    border_color: str = "#E0D4F7"

    is_active: bool = True
    is_default: bool = False


class BackCoverConfigUpdate(BaseModel):
    """Update back cover config request."""

    name: str | None = None
    company_name: str | None = None
    company_logo_url: str | None = None
    company_website: str | None = None
    company_email: str | None = None
    company_phone: str | None = None
    company_address: str | None = None

    background_color: str | None = None
    primary_color: str | None = None
    text_color: str | None = None

    qr_enabled: bool | None = None
    qr_size_mm: float | None = None
    qr_position: str | None = None
    qr_label: str | None = None

    tips_title: str | None = None
    tips_content: str | None = None
    tips_font_size: int | None = None

    tagline: str | None = None
    copyright_text: str | None = None

    show_stars: bool | None = None
    show_border: bool | None = None
    border_color: str | None = None

    is_active: bool | None = None
    is_default: bool | None = None


class BackCoverConfigResponse(BaseModel):
    """Back cover config response."""

    id: str
    name: str
    company_name: str
    company_logo_url: str | None
    company_website: str
    company_email: str
    company_phone: str | None
    company_address: str | None

    background_color: str
    primary_color: str
    text_color: str

    qr_enabled: bool
    qr_size_mm: float
    qr_position: str
    qr_label: str

    tips_title: str
    tips_content: str
    tips_font_size: int

    tagline: str
    copyright_text: str

    show_stars: bool
    show_border: bool
    border_color: str

    is_active: bool
    is_default: bool

    class Config:
        from_attributes = True


@router.get("", response_model=list[BackCoverConfigResponse])
async def list_back_cover_configs(
    db: DbSession,
    admin: AdminUser,
    include_inactive: bool = False,
):
    """List all back cover configurations."""
    query = select(BackCoverConfig)
    if not include_inactive:
        query = query.where(BackCoverConfig.is_active == True)
    query = query.order_by(BackCoverConfig.is_default.desc(), BackCoverConfig.name)

    result = await db.execute(query)
    configs = result.scalars().all()

    return [
        BackCoverConfigResponse(
            id=str(c.id),
            name=c.name,
            company_name=c.company_name,
            company_logo_url=c.company_logo_url,
            company_website=c.company_website,
            company_email=c.company_email,
            company_phone=c.company_phone,
            company_address=c.company_address,
            background_color=c.background_color,
            primary_color=c.primary_color,
            text_color=c.text_color,
            qr_enabled=c.qr_enabled,
            qr_size_mm=c.qr_size_mm,
            qr_position=c.qr_position,
            qr_label=c.qr_label,
            tips_title=c.tips_title,
            tips_content=c.tips_content,
            tips_font_size=c.tips_font_size,
            tagline=c.tagline,
            copyright_text=c.copyright_text,
            show_stars=c.show_stars,
            show_border=c.show_border,
            border_color=c.border_color,
            is_active=c.is_active,
            is_default=c.is_default,
        )
        for c in configs
    ]


@router.get("/default", response_model=BackCoverConfigResponse | None)
async def get_default_back_cover_config(db: DbSession, _admin: AdminUser):
    """Get the default back cover configuration."""
    result = await db.execute(
        select(BackCoverConfig)
        .where(BackCoverConfig.is_default == True)
        .where(BackCoverConfig.is_active == True)
    )
    config = result.scalar_one_or_none()

    if not config:
        return None

    return BackCoverConfigResponse(
        id=str(config.id),
        name=config.name,
        company_name=config.company_name,
        company_logo_url=config.company_logo_url,
        company_website=config.company_website,
        company_email=config.company_email,
        company_phone=config.company_phone,
        company_address=config.company_address,
        background_color=config.background_color,
        primary_color=config.primary_color,
        text_color=config.text_color,
        qr_enabled=config.qr_enabled,
        qr_size_mm=config.qr_size_mm,
        qr_position=config.qr_position,
        qr_label=config.qr_label,
        tips_title=config.tips_title,
        tips_content=config.tips_content,
        tips_font_size=config.tips_font_size,
        tagline=config.tagline,
        copyright_text=config.copyright_text,
        show_stars=config.show_stars,
        show_border=config.show_border,
        border_color=config.border_color,
        is_active=config.is_active,
        is_default=config.is_default,
    )


@router.post("", response_model=BackCoverConfigResponse)
async def create_back_cover_config(
    request: BackCoverConfigCreate,
    db: DbSession,
    admin: AdminUser,
):
    """Create a new back cover configuration."""
    # If setting as default, unset other defaults
    if request.is_default:
        await db.execute(select(BackCoverConfig).where(BackCoverConfig.is_default == True))
        existing_defaults = (
            (await db.execute(select(BackCoverConfig).where(BackCoverConfig.is_default == True)))
            .scalars()
            .all()
        )
        for existing in existing_defaults:
            existing.is_default = False

    config = BackCoverConfig(**request.model_dump())
    db.add(config)
    await db.commit()
    await db.refresh(config)

    logger.info("Back cover config created", config_id=str(config.id), name=config.name)

    return BackCoverConfigResponse(
        id=str(config.id),
        name=config.name,
        company_name=config.company_name,
        company_logo_url=config.company_logo_url,
        company_website=config.company_website,
        company_email=config.company_email,
        company_phone=config.company_phone,
        company_address=config.company_address,
        background_color=config.background_color,
        primary_color=config.primary_color,
        text_color=config.text_color,
        qr_enabled=config.qr_enabled,
        qr_size_mm=config.qr_size_mm,
        qr_position=config.qr_position,
        qr_label=config.qr_label,
        tips_title=config.tips_title,
        tips_content=config.tips_content,
        tips_font_size=config.tips_font_size,
        tagline=config.tagline,
        copyright_text=config.copyright_text,
        show_stars=config.show_stars,
        show_border=config.show_border,
        border_color=config.border_color,
        is_active=config.is_active,
        is_default=config.is_default,
    )


@router.get("/{config_id}", response_model=BackCoverConfigResponse)
async def get_back_cover_config(
    config_id: UUID,
    db: DbSession,
    admin: AdminUser,
):
    """Get a specific back cover configuration."""
    config = await db.get(BackCoverConfig, config_id)
    if not config:
        raise NotFoundError("BackCoverConfig", config_id)

    return BackCoverConfigResponse(
        id=str(config.id),
        name=config.name,
        company_name=config.company_name,
        company_logo_url=config.company_logo_url,
        company_website=config.company_website,
        company_email=config.company_email,
        company_phone=config.company_phone,
        company_address=config.company_address,
        background_color=config.background_color,
        primary_color=config.primary_color,
        text_color=config.text_color,
        qr_enabled=config.qr_enabled,
        qr_size_mm=config.qr_size_mm,
        qr_position=config.qr_position,
        qr_label=config.qr_label,
        tips_title=config.tips_title,
        tips_content=config.tips_content,
        tips_font_size=config.tips_font_size,
        tagline=config.tagline,
        copyright_text=config.copyright_text,
        show_stars=config.show_stars,
        show_border=config.show_border,
        border_color=config.border_color,
        is_active=config.is_active,
        is_default=config.is_default,
    )


@router.patch("/{config_id}", response_model=BackCoverConfigResponse)
async def update_back_cover_config(
    config_id: UUID,
    request: BackCoverConfigUpdate,
    db: DbSession,
    admin: AdminUser,
):
    """Update a back cover configuration."""
    config = await db.get(BackCoverConfig, config_id)
    if not config:
        raise NotFoundError("BackCoverConfig", config_id)

    # If setting as default, unset other defaults
    if request.is_default:
        existing_defaults = (
            (
                await db.execute(
                    select(BackCoverConfig)
                    .where(BackCoverConfig.is_default == True)
                    .where(BackCoverConfig.id != config_id)
                )
            )
            .scalars()
            .all()
        )
        for existing in existing_defaults:
            existing.is_default = False

    # Update fields
    update_data = request.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(config, field, value)

    await db.commit()
    await db.refresh(config)

    logger.info("Back cover config updated", config_id=str(config.id))

    return BackCoverConfigResponse(
        id=str(config.id),
        name=config.name,
        company_name=config.company_name,
        company_logo_url=config.company_logo_url,
        company_website=config.company_website,
        company_email=config.company_email,
        company_phone=config.company_phone,
        company_address=config.company_address,
        background_color=config.background_color,
        primary_color=config.primary_color,
        text_color=config.text_color,
        qr_enabled=config.qr_enabled,
        qr_size_mm=config.qr_size_mm,
        qr_position=config.qr_position,
        qr_label=config.qr_label,
        tips_title=config.tips_title,
        tips_content=config.tips_content,
        tips_font_size=config.tips_font_size,
        tagline=config.tagline,
        copyright_text=config.copyright_text,
        show_stars=config.show_stars,
        show_border=config.show_border,
        border_color=config.border_color,
        is_active=config.is_active,
        is_default=config.is_default,
    )


@router.delete("/{config_id}")
async def delete_back_cover_config(
    config_id: UUID,
    db: DbSession,
    admin: AdminUser,
):
    """Delete (soft) a back cover configuration."""
    config = await db.get(BackCoverConfig, config_id)
    if not config:
        raise NotFoundError("BackCoverConfig", config_id)

    config.is_active = False
    await db.commit()

    logger.info("Back cover config deleted", config_id=str(config_id))

    return {"message": "Arka kapak yapılandırması silindi"}

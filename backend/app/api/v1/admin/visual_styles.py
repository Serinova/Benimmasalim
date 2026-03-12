"""Admin visual styles management endpoints."""

from uuid import UUID

import structlog
from fastapi import APIRouter, Query
from pydantic import BaseModel, Field
from sqlalchemy import select

from app.api.v1.deps import DbSession, SuperAdminUser
from app.core.exceptions import ConflictError, NotFoundError
from app.models.visual_style import VisualStyle
from app.services.storage_service import StorageService

logger = structlog.get_logger()
router = APIRouter()
storage_service = StorageService()

# Tek sayfa test sahnesi — 5 sayfa üretmeden stili görmek için.
STYLE_TEST_SCENE = (
    "A young child in Cappadocia with fairy chimneys and hot air balloons in the sky, "
    "wide shot, looking up in amazement. Bright daylight."
)
STYLE_TEST_CLOTHING = "turquoise t-shirt, denim shorts, brown hiking boots"


class VisualStyleCreate(BaseModel):
    """Create visual style request.

    Stil efektleri (prompt, negative, PuLID parametreleri) style_config.py'den
    yönetilir. Admin panelden sadece görüntü ayarları yapılır.
    """

    name: str = Field(..., min_length=1, max_length=255)
    display_name: str | None = Field(
        default=None,
        max_length=255,
        description="Kullanıcıya gösterilen isim (boşsa name kullanılır)",
    )
    thumbnail_url: str = Field(default="/img/default-style.jpg")
    thumbnail_base64: str | None = None  # Base64 encoded image
    # prompt_modifier: eşleşme keyword'ü — yeni stil eklerken gerekli
    prompt_modifier: str = Field(
        default="",
        description="style_config.py ile eşleşme keyword'ü (ör: 'Pixar 3D animation')",
    )
    is_active: bool = True


class VisualStyleUpdate(BaseModel):
    """Update visual style request (admin-managed fields only)."""

    name: str | None = None
    display_name: str | None = None
    thumbnail_url: str | None = None
    thumbnail_base64: str | None = None
    is_active: bool | None = None


class VisualStyleResponse(BaseModel):
    """Visual style response — sadece admin panelde görüntülenen alanlar."""

    id: str
    name: str
    display_name: str | None = None
    thumbnail_url: str
    prompt_modifier: str  # readonly — style_config.py eşleşme bilgisi
    is_active: bool

    class Config:
        from_attributes = True


def _style_to_response(s: VisualStyle) -> VisualStyleResponse:
    """Convert a VisualStyle ORM object to a response model."""
    return VisualStyleResponse(
        id=str(s.id),
        name=s.name,
        display_name=s.display_name,
        thumbnail_url=s.thumbnail_url,
        prompt_modifier=s.prompt_modifier or "",
        is_active=s.is_active,
    )


@router.get("")
async def list_visual_styles(
    db: DbSession,
    admin: SuperAdminUser,
    include_inactive: bool = False,
) -> list[VisualStyleResponse]:
    """List all visual styles (admin view)."""
    query = select(VisualStyle).order_by(VisualStyle.name)

    if not include_inactive:
        query = query.where(VisualStyle.is_active == True)

    result = await db.execute(query)
    styles = result.scalars().all()

    return [_style_to_response(s) for s in styles]


@router.get("/{style_id}")
async def get_visual_style(
    style_id: UUID,
    db: DbSession,
    admin: SuperAdminUser,
) -> VisualStyleResponse:
    """Get a single visual style."""
    result = await db.execute(select(VisualStyle).where(VisualStyle.id == style_id))
    style = result.scalar_one_or_none()

    if not style:
        raise NotFoundError("Çizim Tarzı", style_id)

    return _style_to_response(style)


@router.post("")
async def create_visual_style(
    request: VisualStyleCreate,
    db: DbSession,
    admin: SuperAdminUser,
) -> dict:
    """Create a new visual style."""
    # Check for duplicate name
    result = await db.execute(select(VisualStyle).where(VisualStyle.name == request.name))
    if result.scalar_one_or_none():
        raise ConflictError(f"'{request.name}' adında bir çizim tarzı zaten var")

    thumbnail_url = request.thumbnail_url

    # Upload image if base64 provided (GCS optional; on failure keep default thumbnail)
    if request.thumbnail_base64:
        logger.info("Uploading visual style image", base64_length=len(request.thumbnail_base64))
        try:
            uploaded_url = storage_service.upload_base64_image(
                base64_data=request.thumbnail_base64, folder="visual-styles"
            )
            if uploaded_url:
                thumbnail_url = uploaded_url
                logger.info("Upload result", uploaded_url=uploaded_url)
        except Exception as e:
            logger.warning(
                "Visual style image upload failed, using default thumbnail", error=str(e)
            )

    style = VisualStyle(
        name=request.name,
        display_name=request.display_name,
        thumbnail_url=thumbnail_url,
        prompt_modifier=request.prompt_modifier,
        is_active=request.is_active,
    )

    db.add(style)
    await db.commit()
    await db.refresh(style)

    return {
        "id": str(style.id),
        "name": style.name,
        "thumbnail_url": style.thumbnail_url,
        "message": "Çizim tarzı oluşturuldu",
    }


@router.patch("/{style_id}")
async def update_visual_style(
    style_id: UUID,
    request: VisualStyleUpdate,
    db: DbSession,
    admin: SuperAdminUser,
) -> dict:
    """Update a visual style."""
    result = await db.execute(select(VisualStyle).where(VisualStyle.id == style_id))
    style = result.scalar_one_or_none()

    if not style:
        raise NotFoundError("Çizim Tarzı", style_id)

    # Check name conflict if changing
    if request.name and request.name != style.name:
        existing = await db.execute(select(VisualStyle).where(VisualStyle.name == request.name))
        if existing.scalar_one_or_none():
            raise ConflictError(f"'{request.name}' adında bir çizim tarzı zaten var")

    # Upload image if base64 provided
    if request.thumbnail_base64:
        logger.info(
            "Uploading visual style image for update", base64_length=len(request.thumbnail_base64)
        )
        try:
            uploaded_url = storage_service.upload_base64_image(
                base64_data=request.thumbnail_base64, folder="visual-styles"
            )
            logger.info("Upload result", uploaded_url=uploaded_url)
            if uploaded_url:
                style.thumbnail_url = uploaded_url
        except Exception as e:
            logger.error("Failed to upload visual style image", error=str(e))

    # Update fields
    update_data = request.model_dump(exclude_unset=True, exclude={"thumbnail_base64"})

    # DEBUG LOG
    logger.info(
        "Updating visual style",
        style_id=str(style_id),
        style_name=style.name,
        update_data=update_data,
    )

    for field, value in update_data.items():
        setattr(style, field, value)

    await db.commit()
    await db.refresh(style)

    # DEBUG LOG after commit
    logger.info(
        "Visual style updated",
        style_id=str(style_id),
    )

    return {
        **_style_to_response(style).model_dump(),
        "message": "Çizim tarzı güncellendi",
    }


@router.delete("/{style_id}")
async def delete_visual_style(
    style_id: UUID,
    db: DbSession,
    admin: SuperAdminUser,
    hard_delete: bool = Query(default=True, description="Kalıcı olarak sil"),
) -> dict:
    """Delete a visual style (hard delete by default)."""
    result = await db.execute(select(VisualStyle).where(VisualStyle.id == style_id))
    style = result.scalar_one_or_none()

    if not style:
        raise NotFoundError("Çizim Tarzı", style_id)

    if hard_delete:
        # Hard delete - permanently remove from DB
        await db.delete(style)
        await db.commit()
        logger.info("Visual style permanently deleted", style_id=str(style_id), name=style.name)
        return {"message": "Çizim tarzı kalıcı olarak silindi"}
    else:
        # Soft delete - just set inactive
        style.is_active = False
        await db.commit()
        return {"message": "Çizim tarzı pasife alındı"}




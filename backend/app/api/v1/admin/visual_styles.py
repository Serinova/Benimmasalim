"""Admin visual styles management endpoints."""

import base64
from uuid import UUID

import structlog
from fastapi import APIRouter, File, Form, Query, UploadFile
from pydantic import BaseModel, Field
from sqlalchemy import select

from app.api.v1.deps import DbSession, SuperAdminUser
from app.core.exceptions import ConflictError, NotFoundError
from app.models.visual_style import VisualStyle
from app.services.storage_service import StorageService
from app.utils.resolution_calc import DEFAULT_GENERATION_A4_LANDSCAPE

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
    """Create visual style request."""

    name: str = Field(..., min_length=1, max_length=255)
    display_name: str | None = Field(
        default=None,
        max_length=255,
        description="Kullanıcıya gösterilen isim (boşsa name kullanılır)",
    )
    thumbnail_url: str = Field(default="/img/default-style.jpg")
    thumbnail_base64: str | None = None  # Base64 encoded image
    prompt_modifier: str = Field(..., min_length=1)
    # V2: optional style-specific negative prompt
    style_negative_en: str | None = Field(
        default=None, description="V2: Style-specific negative prompt tokens (EN)"
    )
    leading_prefix_override: str | None = Field(
        default=None, description="Stil leading prefix (doluysa kod sabiti yerine kullanılır)"
    )
    style_block_override: str | None = Field(
        default=None, description="STYLE: bloğu (doluysa kod sabiti yerine kullanılır)"
    )
    cover_aspect_ratio: str = "3:2"
    page_aspect_ratio: str = "3:2"
    # PuLID parameters — NULL = use style_config.py fallback
    id_weight: float = Field(default=0.90, ge=0.10, le=1.50)
    true_cfg: float | None = Field(default=None, ge=0.5, le=3.0, description="PuLID true_cfg (NULL = kod fallback)")
    start_step: int | None = Field(default=None, ge=0, le=5, description="PuLID start_step (NULL = kod fallback)")
    # FLUX generation parameters — NULL = use GenerationConfig defaults (28 / 3.5)
    num_inference_steps: int | None = Field(default=None, ge=10, le=60, description="FLUX steps (NULL = 28)")
    guidance_scale: float | None = Field(default=None, ge=1.0, le=10.0, description="CFG scale (NULL = 3.5)")
    is_active: bool = True


class VisualStyleUpdate(BaseModel):
    """Update visual style request."""

    name: str | None = None
    display_name: str | None = None
    thumbnail_url: str | None = None
    thumbnail_base64: str | None = None
    prompt_modifier: str | None = None
    style_negative_en: str | None = None
    leading_prefix_override: str | None = None
    style_block_override: str | None = None
    cover_aspect_ratio: str | None = None
    page_aspect_ratio: str | None = None
    id_weight: float | None = Field(default=None, ge=0.10, le=1.50)
    true_cfg: float | None = Field(default=None, ge=0.5, le=3.0)
    start_step: int | None = Field(default=None, ge=0, le=5)
    num_inference_steps: int | None = Field(default=None, ge=10, le=60)
    guidance_scale: float | None = Field(default=None, ge=1.0, le=10.0)
    is_active: bool | None = None


class VisualStyleResponse(BaseModel):
    """Visual style response."""

    id: str
    name: str
    thumbnail_url: str
    prompt_modifier: str
    style_negative_en: str | None = None
    leading_prefix_override: str | None = None
    style_block_override: str | None = None
    cover_aspect_ratio: str
    page_aspect_ratio: str
    id_weight: float
    true_cfg: float | None = None
    start_step: int | None = None
    num_inference_steps: int | None = None
    guidance_scale: float | None = None
    is_active: bool

    class Config:
        from_attributes = True


@router.get("")
async def list_visual_styles(
    db: DbSession,
    admin: SuperAdminUser,
    include_inactive: bool = False,
) -> list[dict]:
    """List all visual styles (admin view)."""
    query = select(VisualStyle).order_by(VisualStyle.name)

    if not include_inactive:
        query = query.where(VisualStyle.is_active == True)

    result = await db.execute(query)
    styles = result.scalars().all()

    return [
        {
            "id": str(s.id),
            "name": s.name,
            "display_name": getattr(s, "display_name", None),
            "thumbnail_url": s.thumbnail_url,
            "prompt_modifier": s.prompt_modifier,
            "style_negative_en": getattr(s, "style_negative_en", None),
            "leading_prefix_override": getattr(s, "leading_prefix_override", None),
            "style_block_override": getattr(s, "style_block_override", None),
            "cover_aspect_ratio": s.cover_aspect_ratio,
            "page_aspect_ratio": s.page_aspect_ratio,
            "id_weight": s.id_weight,
            "true_cfg": getattr(s, "true_cfg", None),
            "start_step": getattr(s, "start_step", None),
            "num_inference_steps": getattr(s, "num_inference_steps", None),
            "guidance_scale": getattr(s, "guidance_scale", None),
            "is_active": s.is_active,
        }
        for s in styles
    ]


@router.get("/{style_id}")
async def get_visual_style(
    style_id: UUID,
    db: DbSession,
    admin: SuperAdminUser,
) -> dict:
    """Get a single visual style."""
    result = await db.execute(select(VisualStyle).where(VisualStyle.id == style_id))
    style = result.scalar_one_or_none()

    if not style:
        raise NotFoundError("Çizim Tarzı", style_id)

    return {
        "id": str(style.id),
        "name": style.name,
        "display_name": getattr(style, "display_name", None),
        "thumbnail_url": style.thumbnail_url,
        "prompt_modifier": style.prompt_modifier,
        "style_negative_en": getattr(style, "style_negative_en", None),
        "leading_prefix_override": getattr(style, "leading_prefix_override", None),
        "style_block_override": getattr(style, "style_block_override", None),
        "cover_aspect_ratio": style.cover_aspect_ratio,
        "page_aspect_ratio": style.page_aspect_ratio,
        "id_weight": style.id_weight,
        "true_cfg": getattr(style, "true_cfg", None),
        "start_step": getattr(style, "start_step", None),
        "num_inference_steps": getattr(style, "num_inference_steps", None),
        "guidance_scale": getattr(style, "guidance_scale", None),
        "is_active": style.is_active,
    }


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
        style_negative_en=request.style_negative_en,
        leading_prefix_override=request.leading_prefix_override,
        style_block_override=request.style_block_override,
        cover_aspect_ratio=request.cover_aspect_ratio,
        page_aspect_ratio=request.page_aspect_ratio,
        id_weight=request.id_weight,
        true_cfg=request.true_cfg,
        start_step=request.start_step,
        num_inference_steps=request.num_inference_steps,
        guidance_scale=request.guidance_scale,
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
        old_id_weight=style.id_weight,
        new_id_weight=update_data.get("id_weight"),
    )

    for field, value in update_data.items():
        setattr(style, field, value)

    await db.commit()
    await db.refresh(style)

    # DEBUG LOG after commit
    logger.info(
        "Visual style updated",
        style_id=str(style_id),
        final_id_weight=style.id_weight,
    )

    return {
        "id": str(style.id),
        "name": style.name,
        "thumbnail_url": style.thumbnail_url,
        "id_weight": style.id_weight,
        "true_cfg": getattr(style, "true_cfg", None),
        "start_step": getattr(style, "start_step", None),
        "num_inference_steps": getattr(style, "num_inference_steps", None),
        "guidance_scale": getattr(style, "guidance_scale", None),
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


@router.post("/{style_id}/test")
async def test_visual_style(
    style_id: UUID,
    db: DbSession,
    admin: SuperAdminUser,
    image: UploadFile | None = File(
        default=None, description="Opsiyonel: çocuk fotoğrafı (yüz için PuLID)"
    ),
    image_provider_override: str | None = Form(
        default=None,
        description="Bu test için sağlayıcı: fal, gemini, gemini_flash. Boş = ayarlardaki varsayılan.",
    ),
) -> dict:
    """Stil testi: 1 görsel üretir. Sağlayıcı ayarlardan veya image_provider_override ile seçilir."""
    result = await db.execute(select(VisualStyle).where(VisualStyle.id == style_id))
    style = result.scalar_one_or_none()
    if not style:
        raise NotFoundError("Çizim Tarzı", style_id)

    child_face_url = ""
    if image and image.filename:
        try:
            body = await image.read()
            b64 = base64.b64encode(body).decode("utf-8")
            content_type = image.content_type or "image/jpeg"
            data_url = f"data:{content_type};base64,{b64}"
            child_face_url = storage_service.upload_base64_image(
                base64_data=data_url, folder="style-test"
            )
        except Exception as e:
            logger.warning("Style test: could not upload face image", error=str(e))

    from app.prompt_engine.constants import (
        DEFAULT_INNER_TEMPLATE_EN,
        NEGATIVE_PROMPT,
    )
    from app.services.ai.image_provider_dispatch import (
        get_effective_ai_config,
        get_image_provider_for_generation,
    )
    from app.services.prompt_template_service import get_prompt_service

    tpl_svc = get_prompt_service()
    inner_tpl = await tpl_svc.get_template_en(db, "INNER_TEMPLATE", DEFAULT_INNER_TEMPLATE_EN)
    base_neg = await tpl_svc.get_prompt(db, "NEGATIVE_PROMPT", NEGATIVE_PROMPT)

    effective_provider = (image_provider_override or "").strip().lower()
    if not effective_provider:
        _cfg = await get_effective_ai_config(db, product_id=None)
        effective_provider = (_cfg.image_provider or "fal").strip().lower() if _cfg else "fal"
    if not child_face_url and effective_provider in ("gemini", "gemini_flash"):
        effective_provider = "fal"

    # Kitap yatay A4: her zaman yatay A4 oranı kullan (ai_config square/portrait override'ını engelle)
    width, height = DEFAULT_GENERATION_A4_LANDSCAPE

    image_provider = get_image_provider_for_generation(effective_provider)
    style_modifier = (style.prompt_modifier or "").strip()
    style_negative_en = (getattr(style, "style_negative_en", None) or "").strip()
    id_weight = float(style.id_weight) if style.id_weight is not None else 0.35
    true_cfg_override = float(style.true_cfg) if getattr(style, "true_cfg", None) is not None else None
    start_step_override = int(style.start_step) if getattr(style, "start_step", None) is not None else None
    num_inference_steps_override = int(style.num_inference_steps) if getattr(style, "num_inference_steps", None) is not None else None
    guidance_scale_override = float(style.guidance_scale) if getattr(style, "guidance_scale", None) is not None else None

    from app.services.ai.face_service import resolve_face_reference
    _effective_face_url, _face_embedding = await resolve_face_reference(
        child_face_url, storage_service
    )

    try:
        out = await image_provider.generate_consistent_image(
            prompt=STYLE_TEST_SCENE,
            child_face_url=_effective_face_url,
            clothing_prompt=STYLE_TEST_CLOTHING,
            style_modifier=style_modifier,
            width=width,
            height=height,
            id_weight=id_weight,
            true_cfg_override=true_cfg_override,
            start_step_override=start_step_override,
            num_inference_steps_override=num_inference_steps_override,
            guidance_scale_override=guidance_scale_override,
            is_cover=False,
            page_number=1,
            template_en=inner_tpl,
            child_gender="",
            child_age=7,
            style_negative_en=style_negative_en,
            base_negative_en=base_neg or "",
            leading_prefix_override=getattr(style, "leading_prefix_override", None) or None,
            style_block_override=getattr(style, "style_block_override", None) or None,
            reference_embedding=_face_embedding,
        )
    except Exception:
        logger.exception("Style test image generation failed", style_id=str(style_id))
        raise

    if isinstance(out, tuple):
        image_url, info = out
        final_prompt = (info or {}).get("final_prompt", "")
        negative_prompt = (info or {}).get("negative_prompt", "")
        fal_params = (info or {}).get("fal_params") or {}
        gemini_params = (info or {}).get("gemini_params") or {}
    else:
        image_url = out
        final_prompt = ""
        negative_prompt = ""
        fal_params = {}
        gemini_params = {}

    return {
        "image_url": image_url,
        "final_prompt": final_prompt,
        "negative_prompt": negative_prompt,
        "fal_params": fal_params,
        "gemini_params": gemini_params,
        "message": "Test görseli oluşturuldu",
    }

"""Order management endpoints."""

import asyncio
import re
from datetime import UTC
from typing import Any
from uuid import UUID

import structlog
from fastapi import APIRouter, BackgroundTasks, File, HTTPException, UploadFile, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import select

from app.api.v1.deps import CurrentUser, CurrentUserOptional, DbSession
from app.config import get_settings
from app.core.exceptions import ForbiddenError, NotFoundError, ValidationError
from app.core.image_dimensions import get_page_image_dimensions
from app.models.order import Order, OrderStatus
from app.prompt_engine import VisualPromptValidationError
from app.prompt_engine import personalize_style_prompt

_logger = structlog.get_logger()
settings = get_settings()
router = APIRouter()
_V3_BLOCK_MSG = "V2_LABEL_BLOCKED: expected v3"

# ---------------------------------------------------------------------------
# Concurrency guard (BackgroundTasks fallback): max 2 parallel generations
# per process when Redis/Arq is unavailable.  Arq worker handles global
# queue ordering; this semaphore only limits the in-process fallback path.
# ---------------------------------------------------------------------------
_IMAGE_GEN_SEMAPHORE = asyncio.Semaphore(settings.order_concurrency_slots)


# ===================== DETERMINISTIC TITLE HELPER =====================
def _force_deterministic_title(
    child_name: str | None,
    scenario_name: str | None,
    original_title: str | None = None,
) -> str:
    """
    Her zaman '{ÇocukAdı}'ın/in/un/ün {SenaryoAdı}' formatında başlık üret.
    Gemini'ye güvenme — tüm senaryolar için tutarlı başlık garanti et.
    """
    from app.services.ai.gemini_service import (
        _get_possessive_suffix,
        _normalize_title_turkish,
    )

    child = (child_name or "").strip()
    if child:
        child = child[0].upper() + child[1:].lower() if len(child) > 1 else child.upper()

    scenario = (scenario_name or "").strip()
    if not scenario:
        scenario = "Büyülü Macera"

    suffix = _get_possessive_suffix(child)
    forced = f"{child}'{suffix} {scenario}"

    original = (original_title or "").strip()
    if original.lower() != forced.lower():
        _logger.warning(
            "🔒 DETERMINISTIC TITLE",
            original=original,
            forced=forced,
            child=child,
            scenario=scenario,
        )

    return _normalize_title_turkish(forced)
# ===================== END DETERMINISTIC TITLE =====================


# ============== Send Preview (Test Mode) ==============


class StoryPageData(BaseModel):
    """Story page data for email."""

    page_number: int
    text: str
    visual_prompt: str
    image_base64: str | None = None  # Base64 encoded image data
    v3_composed: bool = False  # V3 pipeline flag
    negative_prompt: str | None = None  # V3 pre-composed negative
    page_type: str = "inner"  # "cover" | "front_matter" | "inner"
    page_index: int = 0  # 0-based position in book
    story_page_number: int | None = None  # 1-based story page (None for cover)
    composer_version: str = "v3"  # V3 only
    pipeline_version: str | None = None  # MUST resolve to "v3"


def _page_version_flags(p: "StoryPageData") -> tuple[str, str]:
    """Resolve pipeline/composer flags and hard-block non-v3 payloads."""
    pipe = (getattr(p, "pipeline_version", "") or "").strip().lower()
    comp = (getattr(p, "composer_version", "") or "").strip().lower() or "v3"
    if pipe != "v3" or comp != "v3":
        _logger.error(
            _V3_BLOCK_MSG,
            page_number=getattr(p, "page_number", None),
            pipeline_version=pipe or None,
            composer_version=comp or None,
            route="/api/v1/orders",
        )
        raise ValidationError(
            f"{_V3_BLOCK_MSG}. "
            f"page={getattr(p, 'page_number', '?')}, pipeline_version={pipe or 'empty'}, composer_version={comp or 'empty'}"
        )
    return ("v3", "v3")


def _page_to_dict(p: "StoryPageData", *, include_image: bool = False) -> dict:
    """Build story page dict for persistence / worker payload (with pipeline_version)."""
    pipe, comp = _page_version_flags(p)
    d: dict = {
        "page_number": p.page_number,
        "text": p.text,
        "visual_prompt": p.visual_prompt,
        "page_type": p.page_type,
        "page_index": p.page_index,
        "story_page_number": p.story_page_number,
        "composer_version": comp,
        "pipeline_version": pipe,
        **({"v3_composed": True, "negative_prompt": p.negative_prompt or ""} if p.v3_composed else {}),
    }
    if include_image and getattr(p, "image_base64", None):
        d["image_base64"] = p.image_base64
    return d


def _ensure_v3_story_pages(story_pages: list["StoryPageData"], *, route: str) -> None:
    """Hard-fail non-v3 page payloads with explicit 400 error."""
    for p in story_pages:
        try:
            _page_version_flags(p)
        except ValidationError as exc:
            _logger.error(
                _V3_BLOCK_MSG,
                route=route,
                page_number=getattr(p, "page_number", None),
            )
            raise HTTPException(
                status_code=400,
                detail=_V3_BLOCK_MSG,
            ) from exc


class SendPreviewRequest(BaseModel):
    """Request to send story preview via email."""

    parent_name: str = Field(..., min_length=2)
    parent_email: EmailStr
    parent_phone: str | None = None
    child_name: str
    child_age: int
    child_gender: str | None = None
    story_title: str
    story_pages: list[StoryPageData]
    # Optional product/scenario info
    product_id: str | None = None
    product_name: str | None = None
    product_price: float | None = None
    scenario_name: str | None = None
    visual_style_name: str | None = None
    learning_outcomes: list[str] | None = None
    # Audio book settings
    has_audio_book: bool = False
    audio_type: str | None = None  # "system" or "cloned"
    audio_voice_id: str | None = None  # ElevenLabs voice ID for cloned voice
    voice_sample_url: str | None = None  # GCS URL of uploaded voice sample


class AsyncPreviewRequest(BaseModel):
    """Request for async preview generation - returns immediately."""

    # Lead user ID from contact form (CRITICAL for Concierge Support)
    user_id: str | None = None
    parent_name: str = Field(..., min_length=2)
    parent_email: EmailStr
    parent_phone: str | None = None
    child_name: str
    child_age: int
    child_gender: str | None = None
    child_photo_url: str | None = None  # For image generation
    # V2: Clothing description for outfit lock (consistent across all pages)
    clothing_description: str | None = Field(
        default=None,
        max_length=300,
        description="Child's clothing description for consistent outfit across all pages",
    )
    story_title: str
    story_pages: list[StoryPageData]  # Pages with text and visual_prompt
    # Product/scenario info
    product_id: str | None = None
    product_name: str | None = None
    product_price: float | None = None
    scenario_name: str | None = None
    visual_style_name: str | None = None
    learning_outcomes: list[str] | None = None
    # Style info for image generation
    visual_style: str | None = None  # Full style prompt
    id_weight: float | None = None  # PuLID face weight — None = auto-detect from style
    # Audio book settings
    has_audio_book: bool = False
    audio_type: str | None = None
    audio_voice_id: str | None = None
    voice_sample_url: str | None = None
    # Dedication page note (custom message from parent)
    dedication_note: str | None = Field(default=None, max_length=300)
    # Promo code (optional — validated + consumed atomically)
    promo_code: str | None = Field(default=None, max_length=50)


@router.post("/send-preview")
async def send_preview_email(request: SendPreviewRequest, db: DbSession) -> dict:
    """
    Send story preview to parent's email with confirmation link.

    Flow:
    1. Save preview to database
    2. Generate confirmation token
    3. Compose pages with templates
    4. Upload to GCS
    5. Send email with confirmation button
    """
    import secrets
    import uuid
    from datetime import datetime, timedelta

    import structlog
    from sqlalchemy import select

    from app.models.book_template import PageTemplate
    from app.models.story_preview import StoryPreview
    from app.services.email_service import email_service
    from app.services.page_composer import (
        build_template_config,
        effective_page_dimensions_mm,
        page_composer,
    )
    from app.services.storage_service import storage_service

    logger = structlog.get_logger()

    try:
        _ensure_v3_story_pages(request.story_pages, route="/api/v1/orders/send-preview")
        # Generate unique story ID and confirmation token
        story_id = str(uuid.uuid4())[:8]
        confirmation_token = secrets.token_urlsafe(32)

        # Count pages with images
        pages_with_images = sum(1 for p in request.story_pages if p.image_base64)

        logger.info(
            "Received send-preview request",
            story_id=story_id,
            total_pages=len(request.story_pages),
            pages_with_images=pages_with_images,
            parent_email=request.parent_email,
        )

        # Debug: Log first page image status
        if request.story_pages:
            first_page = request.story_pages[0]
            has_image = bool(first_page.image_base64)
            image_len = len(first_page.image_base64) if first_page.image_base64 else 0
            logger.info(f"First page image status: has_image={has_image}, length={image_len}")

        # Şablon: ürün atanmışsa ürünün şablonu, yoksa en son güncellenen
        inner_template = None
        cover_template = None
        if request.product_id:
            from sqlalchemy.orm import selectinload

            from app.models.product import Product
            r = await db.execute(
                select(Product)
                .where(Product.id == UUID(request.product_id))
                .options(
                    selectinload(Product.inner_template),
                    selectinload(Product.cover_template),
                )
            )
            product = r.scalar_one_or_none()
            if product:
                inner_template = product.inner_template
                cover_template = product.cover_template
        if not inner_template:
            result = await db.execute(
                select(PageTemplate)
                .where(PageTemplate.is_active == True)
                .order_by(PageTemplate.updated_at.desc().nulls_last())
            )
            templates = {}
            for t in result.scalars().all():
                if t.page_type not in templates:
                    templates[t.page_type] = t
            inner_template = templates.get("inner")
            cover_template = templates.get("cover")

        # Deterministic title (must be computed before page composition loop)
        _det_title_sp = _force_deterministic_title(
            child_name=request.child_name,
            scenario_name=request.scenario_name,
            original_title=request.story_title,
        )

        # Compose pages with templates (text on image)
        composed_pages = []
        for p in request.story_pages:
            page_data = {
                "page_number": p.page_number,
                "text": p.text,
                "visual_prompt": p.visual_prompt,
                "image_base64": p.image_base64,
            }

            # Choose template based on page type
            if p.page_number == 0 and cover_template:
                template = cover_template
            elif inner_template:
                template = inner_template
            else:
                template = None

            # Compose page with template (render text on image)
            # Kapak (page 0): hikaye metni değil, kitap başlığı kullan
            compose_text = p.text
            if p.page_number == 0 and _det_title_sp:
                compose_text = _det_title_sp

            if p.image_base64 and template:
                template_config = build_template_config(template)
                _pw, _ph = effective_page_dimensions_mm(template.page_width_mm, template.page_height_mm)
                composed_image = page_composer.compose_page(
                    image_base64=p.image_base64,
                    text=compose_text,
                    template_config=template_config,
                    page_width_mm=_pw,
                    page_height_mm=_ph,
                    dpi=300,
                )
                page_data["image_base64"] = composed_image

            composed_pages.append(page_data)

        # Upload composed images to GCS and get URLs
        images_to_upload = {
            p["page_number"]: p["image_base64"] for p in composed_pages if p.get("image_base64")
        }

        logger.info(f"Images to upload count: {len(images_to_upload)}")
        for page_num, img_data in images_to_upload.items():
            logger.info(f"Page {page_num}: image data length = {len(img_data) if img_data else 0}")

        uploaded_urls: dict[int, str] = {}

        if images_to_upload:
            logger.info("Starting storage upload (with retry)...")
            try:
                uploaded_urls = storage_service.upload_multiple_images(
                    images=images_to_upload,
                    story_id=story_id,
                )
                logger.info(f"Uploaded {len(uploaded_urls)} images successfully")
                for page_num, url in uploaded_urls.items():
                    logger.info(f"Page {page_num} URL: {url[:100]}...")
            except Exception as upload_err:
                import traceback

                logger.error(
                    "Image upload failed after retries — images NOT saved to DB",
                    error=str(upload_err),
                    traceback=traceback.format_exc(),
                )
                # Do NOT fall back to base64 in DB — it bloats Cloud SQL
        else:
            logger.warning("No images to upload!")

        page_images_data = uploaded_urls
        logger.info(f"Final page_images_data count: {len(page_images_data)}")

        # Build prompts cache for regeneration support
        _prompts_for_cache = [
            {
                "page_number": p.page_number,
                "visual_prompt": p.visual_prompt,
                "v3_composed": bool(p.v3_composed),
                "negative_prompt": p.negative_prompt or "",
                "pipeline_version": getattr(p, "pipeline_version", "v3"),
            }
            for p in request.story_pages
            if p.visual_prompt
        ]

        # Save preview to database
        story_preview = StoryPreview(
            confirmation_token=confirmation_token,
            status="PENDING",
            parent_name=request.parent_name,
            parent_email=request.parent_email,
            parent_phone=request.parent_phone,
            child_name=request.child_name,
            child_age=request.child_age,
            child_gender=request.child_gender,
            product_name=request.product_name,
            product_price=request.product_price,
            story_title=_det_title_sp,
            story_pages=[
                _page_to_dict(p) for p in request.story_pages
            ],
            scenario_name=request.scenario_name,
            visual_style_name=request.visual_style_name,
            learning_outcomes=request.learning_outcomes,
            page_images=page_images_data,
            generated_prompts_cache={
                "prompts": _prompts_for_cache,
                "clothing_description": getattr(request, "clothing_description", "") or "",
                "pipeline_version": "v3",
            },
            expires_at=datetime.now(UTC) + timedelta(hours=48),
            # Audio book settings
            has_audio_book=request.has_audio_book,
            audio_type=request.audio_type,
            audio_voice_id=request.audio_voice_id,
            voice_sample_url=request.voice_sample_url,
        )

        if request.product_id:
            try:
                story_preview.product_id = uuid.UUID(request.product_id)
            except ValueError:
                pass  # Invalid UUID format, ignore

        db.add(story_preview)
        await db.commit()
        await db.refresh(story_preview)

        logger.info(f"Saved preview with token: {confirmation_token[:10]}...")

        # Convert pages to dict format with image URLs
        pages_data = [
            {
                "page_number": p["page_number"],
                "text": "",
                "visual_prompt": p["visual_prompt"],
                "image_url": uploaded_urls.get(p["page_number"]),
                "image_base64": p["image_base64"]
                if p["page_number"] not in uploaded_urls
                else None,
            }
            for p in composed_pages
        ]

        # Send email with confirmation button
        confirmation_url = f"{settings.frontend_url}/confirm/{confirmation_token}"

        email_service.send_story_email_with_confirmation(
            recipient_email=request.parent_email,
            recipient_name=request.parent_name,
            child_name=request.child_name,
            story_title=_det_title_sp,
            story_pages=pages_data,
            confirmation_url=confirmation_url,
            product_price=request.product_price,
        )

        return {
            "success": True,
            "message": f"Hikaye {request.parent_email} adresine gönderildi",
            "recipient": request.parent_email,
            "story_id": story_id,
            "preview_id": str(story_preview.id),
            "images_uploaded": len(uploaded_urls),
        }

    except Exception as e:
        import traceback

        logger.error("Failed to send preview", error=str(e), traceback=traceback.format_exc())
        return {
            "success": False,
            "error": str(e),
        }


# ============== ASYNC Preview Generation (Background Processing) ==============


@router.post("/submit-preview-async")
async def submit_preview_async(
    request: AsyncPreviewRequest,
    background_tasks: BackgroundTasks,
    db: DbSession,
) -> dict:
    """
    Submit preview for ASYNC processing - returns immediately!

    User can close the page. Images will be generated in background
    and email will be sent when complete (within 5-10 minutes).

    Flow:
    1. Save preview to database with PROCESSING status
    2. Return immediately to user
    3. Background task generates remaining images
    4. Background task composes pages with templates
    5. Background task uploads to GCS
    6. Background task sends email
    """
    import secrets
    import uuid
    from datetime import datetime, timedelta

    import structlog

    from app.models.story_preview import StoryPreview
    from app.services.storage_service import storage_service

    logger = structlog.get_logger()

    try:
        _ensure_v3_story_pages(request.story_pages, route="/api/v1/orders/submit-preview-async")
        # Generate unique story ID and confirmation token
        story_id = str(uuid.uuid4())[:8]
        confirmation_token = secrets.token_urlsafe(32)

        logger.info(
            "Received async preview request",
            story_id=story_id,
            total_pages=len(request.story_pages),
            parent_email=request.parent_email,
        )

        # İlk 3 sayfa görseli varsa hemen GCS'e yükle ve kaydet (arka plan verisi kaybolmasın diye)
        initial_page_images: dict[str, str] = {}
        pages_with_b64 = {
            p.page_number: p.image_base64 for p in request.story_pages if p.image_base64
        }
        if pages_with_b64:
            try:
                uploaded_first = storage_service.upload_multiple_images(
                    images=pages_with_b64,
                    story_id=story_id,
                )
                initial_page_images = {str(k): v for k, v in uploaded_first.items()}
                logger.info(f"Uploaded {len(initial_page_images)} initial preview images to GCS")
            except Exception as e:
                logger.warning(f"Initial image upload failed (background will retry): {e}")

        # ===== DETERMINISTIC TITLE: Gemini'ye güvenme =====
        _det_title = _force_deterministic_title(
            child_name=request.child_name,
            scenario_name=request.scenario_name,
            original_title=request.story_title,
        )

        # ── Promo code: validate + consume atomically ──
        promo = None
        discount_amount = None
        if request.promo_code:
            from decimal import Decimal

            from app.services.promo_code_service import (
                calculate_discount,
                consume_promo_code,
                validate_promo_code,
            )

            promo_code_str = request.promo_code.strip().upper()
            subtotal = Decimal(str(request.product_price or 0))

            try:
                promo = await validate_promo_code(promo_code_str, subtotal, db)
                discount_amount = calculate_discount(promo, subtotal)

                consumed = await consume_promo_code(promo.id, db)
                if not consumed:
                    return {
                        "success": False,
                        "error": "Kupon kodunun kullanım limiti dolmuş, lütfen başka bir kod deneyin",
                    }

                logger.info(
                    "promo_code_consumed_in_preview",
                    code=promo.code,
                    discount=str(discount_amount),
                    story_id=story_id,
                )
            except ValidationError as e:
                return {"success": False, "error": str(e.detail)}

        # Build prompts cache for regeneration support
        _async_prompts_for_cache = [
            {
                "page_number": p.page_number,
                "visual_prompt": p.visual_prompt,
                "v3_composed": bool(p.v3_composed),
                "negative_prompt": p.negative_prompt or "",
                "pipeline_version": getattr(p, "pipeline_version", "v3"),
            }
            for p in request.story_pages
            if p.visual_prompt
        ]

        # Save preview to database with PROCESSING status
        story_preview = StoryPreview(
            confirmation_token=confirmation_token,
            status="PROCESSING",  # New status for async processing
            # Lead user ID from contact form (CRITICAL for Concierge Support)
            lead_user_id=uuid.UUID(request.user_id) if request.user_id else None,
            parent_name=request.parent_name,
            parent_email=request.parent_email,
            parent_phone=request.parent_phone,
            child_name=request.child_name,
            child_age=request.child_age,
            child_gender=request.child_gender,
            product_name=request.product_name,
            product_price=request.product_price,
            story_title=_det_title,
            story_pages=[_page_to_dict(p) for p in request.story_pages],
            scenario_name=request.scenario_name,
            visual_style_name=request.visual_style_name,
            learning_outcomes=request.learning_outcomes,
            page_images=initial_page_images or {},  # İlk 3 hemen; kalanı arka planda
            generated_prompts_cache={
                "prompts": _async_prompts_for_cache,
                "clothing_description": (request.clothing_description or "").strip(),
                "pipeline_version": "v3",
            },
            expires_at=datetime.now(UTC) + timedelta(hours=48),
            # Audio book settings
            has_audio_book=request.has_audio_book,
            audio_type=request.audio_type,
            audio_voice_id=request.audio_voice_id,
            voice_sample_url=request.voice_sample_url,
            child_photo_url=request.child_photo_url,
            clothing_description=(request.clothing_description or "").strip() or None,
            # Promo code snapshot
            promo_code_id=promo.id if promo else None,
            promo_code_text=promo.code if promo else None,
            promo_discount_type=promo.discount_type if promo else None,
            promo_discount_value=promo.discount_value if promo else None,
            discount_applied_amount=discount_amount,
            # Dedication page note
            dedication_note=request.dedication_note,
        )

        if request.product_id:
            try:
                story_preview.product_id = uuid.UUID(request.product_id)
            except ValueError:
                pass

        db.add(story_preview)
        await db.commit()
        await db.refresh(story_preview)

        preview_id = str(story_preview.id)
        logger.info(f"Saved preview for async processing: {preview_id}")

        # Mark as queued so frontend can show "waiting in queue" state
        story_preview.generation_progress = {"stage": "queued", "current_page": 0, "total_pages": 0}
        await db.commit()

        # Enqueue via Arq (preferred) or fall back to FastAPI BackgroundTasks
        _req_data = {
            "parent_name": request.parent_name,
            "parent_email": request.parent_email,
            "child_name": request.child_name,
            "child_age": request.child_age,
            "child_gender": request.child_gender,
            "child_photo_url": request.child_photo_url,
            "clothing_description": (request.clothing_description or "").strip(),
            "story_title": _det_title,
            "story_pages": [_page_to_dict(p, include_image=True) for p in request.story_pages],
            "visual_style": request.visual_style,
            "visual_style_name": request.visual_style_name,
            "id_weight": request.id_weight,
            "product_price": request.product_price,
            "dedication_note": request.dedication_note,
        }

        _arq_ok = False
        try:
            from app.workers.enqueue import enqueue_preview_generation

            job_id = await enqueue_preview_generation(
                preview_id=preview_id,
                story_id=story_id,
                confirmation_token=confirmation_token,
                request_data=_req_data,
            )
            if job_id:
                _arq_ok = True
                _logger.info("Preview generation enqueued via Arq", job_id=job_id, preview_id=preview_id)
            else:
                _logger.warning("Arq enqueue returned None (Redis down or job exists)", preview_id=preview_id)
        except Exception as _arq_err:
            _logger.warning(
                "Arq unavailable, falling back to BackgroundTasks",
                error=str(_arq_err),
                preview_id=preview_id,
            )
        if not _arq_ok:
            background_tasks.add_task(
                process_preview_background,
                preview_id=preview_id,
                story_id=story_id,
                confirmation_token=confirmation_token,
                request_data=_req_data,
            )

        return {
            "success": True,
            "message": "İşleminiz alındı! Görseller oluşturulup e-posta gönderilecek.",
            "estimated_time": "5-10 dakika",
            "preview_id": preview_id,
            "can_close_page": True,
        }

    except Exception as e:
        import traceback

        logger.error(
            "Failed to submit async preview", error=str(e), traceback=traceback.format_exc()
        )
        return {
            "success": False,
            "error": str(e),
        }


async def process_preview_background(
    preview_id: str,
    story_id: str,
    confirmation_token: str,
    request_data: dict,
):
    """
    Background task to generate images and send email.
    Runs after the API returns to user.
    """

    import structlog


    logger = structlog.get_logger()
    logger.info(
        "Background task queued, waiting for semaphore",
        preview_id=preview_id,
    )

    async with _IMAGE_GEN_SEMAPHORE:
        logger.info(f"Starting background processing for preview {preview_id}")
        await _process_preview_background_inner(
            preview_id, story_id, confirmation_token, request_data,
        )


async def _process_preview_background_inner(
    preview_id: str,
    story_id: str,
    confirmation_token: str,
    request_data: dict,
):
    """Actual implementation, runs inside the semaphore guard."""
    import asyncio
    import base64

    import httpx
    import structlog
    from sqlalchemy import select

    from app.core.database import async_session_factory
    from app.models.book_template import PageTemplate
    from app.models.story_preview import StoryPreview
    from app.services.ai.image_provider_dispatch import (
        get_effective_ai_config,
        get_image_provider_for_generation,
    )
    from app.services.page_composer import (
        build_template_config,
        effective_page_dimensions_mm,
        page_composer,
    )
    from app.services.storage_service import storage_service

    logger = structlog.get_logger()

    try:
        preview_uuid = UUID(preview_id)
        async with async_session_factory() as db:
            # Get preview from database
            result = await db.execute(select(StoryPreview).where(StoryPreview.id == preview_uuid))
            preview = result.scalar_one_or_none()

            if not preview:
                logger.error("Preview not found", preview_id=preview_id)
                return

            ai_config = await get_effective_ai_config(
                db, product_id=getattr(preview, "product_id", None)
            )
            provider_name = (
                (ai_config.image_provider or "gemini").strip().lower() if ai_config else "gemini"
            )
            image_provider = get_image_provider_for_generation(provider_name)

            logger.info(
                "IMAGE_ENGINE_USED",
                provider=provider_name,
                model=getattr(ai_config, "image_model", "") if ai_config else "",
                preview_id=preview_id,
                source="process_preview_background",
            )

            story_pages = request_data["story_pages"]
            child_photo_url = request_data.get("child_photo_url") or getattr(
                preview, "child_photo_url", None
            )
            visual_style = request_data.get("visual_style", "children's book illustration")
            id_weight = request_data.get("id_weight")  # None = auto-detect from style
            
            # Resolve child_gender FIRST (needed for clothing resolution below)
            child_gender = (
                request_data.get("child_gender") or getattr(preview, "child_gender", None) or ""
            ).strip()

            # Resolve clothing from scenario (gender-specific, priority over request_data)
            clothing_desc = ""
            _scenario_id = getattr(preview, "scenario_id", None) or request_data.get("scenario_id")
            if _scenario_id:
                try:
                    from app.models.scenario import Scenario
                    
                    _sc_res = await db.execute(select(Scenario).where(Scenario.id == UUID(str(_scenario_id))))
                    _sc = _sc_res.scalar_one_or_none()
                    if _sc:
                        _g = (child_gender or request_data.get("child_gender") or "erkek").lower()
                        if _g in ("kiz", "kız", "girl", "female"):
                            clothing_desc = (getattr(_sc, "outfit_girl", None) or "").strip() or (getattr(_sc, "outfit_boy", None) or "").strip()
                        else:
                            clothing_desc = (getattr(_sc, "outfit_boy", None) or "").strip() or (getattr(_sc, "outfit_girl", None) or "").strip()
                        if clothing_desc:
                            logger.info("front_cover: clothing resolved from scenario (priority)", scenario_id=str(_scenario_id), outfit=clothing_desc[:60])
                except Exception as _ce:
                    logger.warning("front_cover: failed to resolve clothing from scenario", error=str(_ce))
            
            # Fallback to request_data if scenario didn't have outfit
            if not clothing_desc:
                clothing_desc = (request_data.get("clothing_description") or "").strip()
                if clothing_desc:
                    logger.info("front_cover: using request_data clothing_description (fallback)", outfit=clothing_desc[:60])
            visual_style = personalize_style_prompt(
                visual_style,
                child_name=getattr(preview, "child_name", None)
                or request_data.get("child_name")
                or "",
                child_age=request_data.get("child_age") or getattr(preview, "child_age", None) or 7,
                child_gender=child_gender,
            )

            # V2: Fetch style_negative_en, id_weight, overrides from VisualStyle by name (for preview)
            style_negative_en = ""
            _vs_leading_prefix_override: str | None = None
            _vs_style_block_override: str | None = None
            vs_name = request_data.get("visual_style_name")
            if vs_name:
                from app.models.visual_style import VisualStyle

                r = await db.execute(select(VisualStyle).where(VisualStyle.name == vs_name))
                vs = r.scalar_one_or_none()
                if vs is None:
                    r = await db.execute(
                        select(VisualStyle).where(VisualStyle.display_name == vs_name)
                    )
                    vs = r.scalar_one_or_none()
                if vs:
                    if vs.style_negative_en:
                        style_negative_en = (vs.style_negative_en or "").strip()
                    if id_weight is None and vs.id_weight is not None:
                        id_weight = float(vs.id_weight)
                    _vs_leading_prefix_override = (vs.leading_prefix_override or "").strip() or None
                    _vs_style_block_override = (vs.style_block_override or "").strip() or None
                    # PuLID + FLUX generation overrides
                    _vs_true_cfg_override = float(vs.true_cfg) if getattr(vs, "true_cfg", None) is not None else None
                    _vs_start_step_override = int(vs.start_step) if getattr(vs, "start_step", None) is not None else None
                    _vs_num_inference_steps_override = int(vs.num_inference_steps) if getattr(vs, "num_inference_steps", None) is not None else None
                    _vs_guidance_scale_override = float(vs.guidance_scale) if getattr(vs, "guidance_scale", None) is not None else None
                else:
                    _vs_true_cfg_override = None
                    _vs_start_step_override = None
                    _vs_num_inference_steps_override = None
                    _vs_guidance_scale_override = None
            else:
                _vs_true_cfg_override = None
                _vs_start_step_override = None
                _vs_num_inference_steps_override = None
                _vs_guidance_scale_override = None

            # V2: Fetch COVER/INNER templates and NEGATIVE_PROMPT from DB
            from app.prompt_engine.constants import (
                DEFAULT_COVER_TEMPLATE_EN,
                DEFAULT_INNER_TEMPLATE_EN,
                NEGATIVE_PROMPT,
            )
            from app.services.prompt_template_service import get_prompt_service

            _tpl_svc = get_prompt_service()
            cover_tpl = await _tpl_svc.get_template_en(
                db, "COVER_TEMPLATE", DEFAULT_COVER_TEMPLATE_EN
            )
            inner_tpl = await _tpl_svc.get_template_en(
                db, "INNER_TEMPLATE", DEFAULT_INNER_TEMPLATE_EN
            )
            base_neg = await _tpl_svc.get_prompt(db, "NEGATIVE_PROMPT", NEGATIVE_PROMPT)

            from app.services.ai.face_service import resolve_face_reference
            from app.services.storage_service import storage_service as _ss_ord
            _face_ref_url, _face_embedding = await resolve_face_reference(child_photo_url, _ss_ord)
            if not child_photo_url:
                logger.warning(
                    "child_photo_url missing, PuLID disabled for remaining pages",
                    preview_id=preview_id,
                )

            # Ürün şablonları: görsel üretim boyutu için (şablona göre gen_w x gen_h)
            preview_product = None
            preview_cover_template = None
            preview_inner_template = None
            if getattr(preview, "product_id", None):
                from sqlalchemy.orm import selectinload

                from app.models.product import Product
                rp = await db.execute(
                    select(Product)
                    .where(Product.id == preview.product_id)
                    .options(
                        selectinload(Product.inner_template),
                        selectinload(Product.cover_template),
                    )
                )
                preview_product = rp.scalar_one_or_none()
                if preview_product:
                    preview_cover_template = preview_product.cover_template
                    preview_inner_template = preview_product.inner_template

            # Generate images for pages that don't have them (retry for remaining pages)
            page_images: dict[int, str] = {}
            prompt_debug_collector: dict[
                int, dict
            ] = {}  # page_index -> {final_prompt, negative_prompt} when debug
            generation_manifest_collector: dict[int, dict] = {}  # page_index -> manifest
            max_retries = 3

            # -- Preview: sadece ilk 3 sayfa gorsellestirilir, kalan odeme sonrasi uretilir --
            PREVIEW_PAGE_LIMIT = 3

            # -- Separate pages into existing and to-generate lists --
            pages_to_generate: list[dict] = []
            for page in story_pages:
                page_num = int(page["page_number"]) if page.get("page_number") is not None else None
                if page_num is None:
                    continue
                # Skip front_matter pages (text-only, no image generation)
                if page.get("page_type") == "front_matter":
                    logger.info(f"Page {page_num}: Skipping front_matter (no image)")
                    continue
                if page.get("image_base64"):
                    page_images[page_num] = page["image_base64"]
                    logger.info(f"Page {page_num}: Using existing image")
                    continue
                # Sadece ilk 3 sayfa (0, 1, 2) onizleme icin uretilir
                if page_num < PREVIEW_PAGE_LIMIT:
                    pages_to_generate.append(page)

            # --- Progress tracking: only preview pages ---
            _total_pages_to_gen = len(pages_to_generate)
            _pages_generated = 0
            preview.generation_progress = {
                "current_page": 0,
                "total_pages": _total_pages_to_gen,
                "stage": "generating_images",
            }
            await db.commit()

            # -- Parallel image generation with concurrency limit --
            _img_sem = asyncio.Semaphore(settings.image_concurrency)

            async def _gen_page_image(page: dict) -> dict:
                """Generate a single page image with retry. Returns result dict."""
                page_num = int(page["page_number"])
                async with _img_sem:
                    # Debug log for page 1
                    if page_num == 1:
                        logger.info(
                            "PROMPT_DEBUG_PAGE_1",
                            style_prompt=visual_style,
                            scenario_prompt=request_data.get("story_title")
                            or "(not passed to image gen)",
                            visual_prompt=page.get("visual_prompt", "")[:500],
                            emotion_prompt="(not passed to image gen)",
                            cover_prompt_used=False,
                            negative_prompt="(built in FAL; see PROMPT_DEBUG_FAL)",
                        )

                    last_error = None
                    for attempt in range(max_retries):
                        try:
                            logger.info(
                                f"Page {page_num}: Generating image (attempt {attempt + 1}/{max_retries})..."
                            )
                            if page_num == 0 and preview_cover_template:
                                from app.utils.resolution_calc import (
                                    get_effective_generation_params,
                                )
                                _params = get_effective_generation_params(preview_cover_template)
                                w, h = _params["generation_width"], _params["generation_height"]
                            elif preview_inner_template:
                                from app.utils.resolution_calc import (
                                    get_effective_generation_params,
                                )
                                _params = get_effective_generation_params(preview_inner_template)
                                w, h = _params["generation_width"], _params["generation_height"]
                            else:
                                w, h = get_page_image_dimensions(page_num)
                            _is_cover = page_num == 0
                            _child_age = (
                                request_data.get("child_age")
                                or getattr(preview, "child_age", None)
                                or 7
                            )
                            scene_for_fal = (
                                page.get("visual_prompt") or page.get("text") or ""
                            ).strip()
                            _is_v3 = page.get("v3_composed", False)
                            result = await image_provider.generate_consistent_image(
                                prompt=scene_for_fal,
                                child_face_url=_face_ref_url or "",
                                clothing_prompt=clothing_desc,
                                style_modifier=visual_style,
                                width=w,
                                height=h,
                                id_weight=id_weight,
                                true_cfg_override=_vs_true_cfg_override,
                                start_step_override=_vs_start_step_override,
                                num_inference_steps_override=_vs_num_inference_steps_override,
                                guidance_scale_override=_vs_guidance_scale_override,
                                is_cover=_is_cover,
                                page_number=page_num,
                                preview_id=str(preview_id) if preview_id else None,
                                order_id=None,
                                template_en=cover_tpl if _is_cover else inner_tpl,
                                story_title=(request_data.get("story_title") or "").strip()
                                if _is_cover
                                else "",
                                child_gender=child_gender,
                                child_age=_child_age,
                                style_negative_en=style_negative_en,
                                base_negative_en=base_neg or "",
                                leading_prefix_override=_vs_leading_prefix_override,
                                style_block_override=_vs_style_block_override,
                                skip_compose=_is_v3,
                                precomposed_negative=page.get("negative_prompt", "") if _is_v3 else "",
                                reference_embedding=_face_embedding,
                            )
                            image_url = result[0] if isinstance(result, tuple) else result
                            _debug_info: dict = {}
                            if isinstance(result, tuple) and len(result) == 2 and result[1]:
                                _debug_info = result[1]
                            if image_url:
                                async with httpx.AsyncClient(timeout=60.0) as http_client:
                                    img_response = await http_client.get(image_url)
                                    img_response.raise_for_status()
                                    image_base64 = base64.b64encode(img_response.content).decode(
                                        "utf-8"
                                    )
                                logger.info(f"Page {page_num}: Image generated successfully")
                                return {
                                    "page_num": page_num,
                                    "image_base64": image_base64,
                                    "debug_info": _debug_info,
                                }
                            last_error = ValueError("No image URL returned")
                        except VisualPromptValidationError as e:
                            logger.error(
                                "Visual prompt validation failed", page_num=page_num, detail=str(e)
                            )
                            return {"page_num": page_num, "error": e, "validation_error": True}
                        except Exception as e:
                            last_error = e
                            logger.warning(f"Page {page_num}: Attempt {attempt + 1} failed - {e}")
                            if attempt < max_retries - 1:
                                await asyncio.sleep(3)

                    logger.error(
                        f"Page {page_num}: All {max_retries} attempts failed - {last_error}"
                    )
                    return {"page_num": page_num, "error": last_error}

            # Launch all page generations in parallel (limited by semaphore)
            gen_results = await asyncio.gather(
                *[_gen_page_image(p) for p in pages_to_generate],
                return_exceptions=True,
            )

            # Process results and update progress per-page (granular)
            for r in gen_results:
                if isinstance(r, Exception):
                    logger.error("Unexpected generation exception", error=str(r))
                    continue
                if not isinstance(r, dict):
                    continue
                page_num = r["page_num"]
                if r.get("validation_error"):
                    raise ValueError(f"Gorsel prompt dogrulama hatasi: {r['error']}")
                if "image_base64" in r:
                    page_images[page_num] = r["image_base64"]
                    _pages_generated += 1
                    # Collect debug/manifest info
                    info = r.get("debug_info") or {}
                    if info.get("manifest") and info.get("page_index") is not None:
                        manifest_entry = dict(info["manifest"])
                        if info.get("final_prompt") is not None:
                            manifest_entry["final_prompt"] = info["final_prompt"]
                        if info.get("negative_prompt") is not None:
                            manifest_entry["negative_prompt"] = info["negative_prompt"]
                        generation_manifest_collector[str(info["page_index"])] = manifest_entry
                    if info.get("final_prompt") is not None and info.get("page_index") is not None:
                        prompt_debug_collector[str(info["page_index"])] = {
                            "final_prompt": info["final_prompt"],
                            "negative_prompt": info["negative_prompt"],
                        }

                    # Granular progress update per page
                    preview.generation_progress = {
                        "current_page": _pages_generated,
                        "total_pages": _total_pages_to_gen,
                        "stage": "generating_images",
                    }
                    await db.commit()

            # Şablon: önizlemenin ürünü atanmışsa ürünün şablonu, yoksa en son güncellenen
            inner_template = None
            cover_template = None
            if getattr(preview, "product_id", None):
                from sqlalchemy.orm import selectinload

                from app.models.product import Product
                r = await db.execute(
                    select(Product)
                    .where(Product.id == preview.product_id)
                    .options(
                        selectinload(Product.inner_template),
                        selectinload(Product.cover_template),
                    )
                )
                product = r.scalar_one_or_none()
                if product:
                    inner_template = product.inner_template
                    cover_template = product.cover_template
            if not inner_template:
                result = await db.execute(
                    select(PageTemplate)
                    .where(PageTemplate.is_active == True)
                    .order_by(PageTemplate.updated_at.desc().nulls_last())
                )
                templates = {}
                for t in result.scalars().all():
                    if t.page_type not in templates:
                        templates[t.page_type] = t
                inner_template = templates.get("inner")
                cover_template = templates.get("cover")

            # User-visible visual_prompt = composed (prompt_debug final_prompt) so UI shows Cappadocia + style
            def _display_visual_prompt(page: dict, page_num: int) -> str:
                if prompt_debug_collector and str(page_num) in prompt_debug_collector:
                    return prompt_debug_collector[str(page_num)].get("final_prompt") or page.get(
                        "visual_prompt", ""
                    )
                return page.get("visual_prompt", "")

            # --- Progress: composing stage ---
            preview.generation_progress = {
                "current_page": _pages_generated,
                "total_pages": _total_pages_to_gen,
                "stage": "composing",
            }
            await db.commit()

            # Compose only pages that have generated images (preview: first 3)
            composed_pages = []
            for page in story_pages:
                page_num = int(page["page_number"]) if page.get("page_number") is not None else None
                if page_num is None:
                    continue
                image_base64 = page_images.get(page_num)
                if not image_base64:
                    # Gorseli olmayan sayfayi onizleme/email'e dahil etme
                    continue
                display_prompt = _display_visual_prompt(page, page_num)
                page_data = {
                    "page_number": page_num,
                    "text": page["text"],
                    "visual_prompt": display_prompt,
                    "image_base64": image_base64,
                }

                # Choose template
                if page_num == 0 and cover_template:
                    template = cover_template
                elif inner_template:
                    template = inner_template
                else:
                    template = None

                # Compose with template
                # Kapak (page 0): hikaye metni degil, kitap basligi kullan
                _compose_text = page["text"]
                if page_num == 0:
                    _compose_text = (request_data.get("story_title") or "").strip() or _compose_text

                if template:
                    template_config = build_template_config(template)
                    _pw, _ph = effective_page_dimensions_mm(template.page_width_mm, template.page_height_mm)
                    composed_image = page_composer.compose_page(
                        image_base64=image_base64,
                        text=_compose_text,
                        template_config=template_config,
                        page_width_mm=_pw,
                        page_height_mm=_ph,
                        dpi=300,
                    )
                    page_data["image_base64"] = composed_image

                composed_pages.append(page_data)

            # --- Compose dedication page (if dedication_note provided) ---
            # Single DB query for dedication template (used for both default text and config)
            _ded_tpl_result = await db.execute(
                select(PageTemplate).where(PageTemplate.page_type == "dedication", PageTemplate.is_active == True)
            )
            _ded_tpl = _ded_tpl_result.scalar_one_or_none()

            dedication_note = request_data.get("dedication_note")
            if not dedication_note:
                # Try AI-generated dedication text from front_matter page
                for _sp in request_data.get("story_pages", []):
                    if _sp.get("page_type") == "front_matter" and (_sp.get("text") or "").strip():
                        dedication_note = _sp["text"].strip()
                        break
            if not dedication_note and _ded_tpl and getattr(_ded_tpl, "dedication_default_text", None):
                dedication_note = _ded_tpl.dedication_default_text.replace(
                    "{child_name}", request_data.get("child_name", "")
                )

            dedication_image_b64: str | None = None
            if dedication_note:
                try:
                    ded_cfg = build_template_config(_ded_tpl) if _ded_tpl else {}
                    dedication_image_b64 = page_composer.compose_dedication_page(
                        text=dedication_note,
                        template_config=ded_cfg,
                        dpi=300,
                    )
                    logger.info("Dedication page composed", preview_id=preview_id)
                except Exception as ded_err:
                    logger.warning("Failed to compose dedication page: %s", ded_err)

            # --- Progress: uploading stage ---
            preview.generation_progress = {
                "current_page": _pages_generated,
                "total_pages": _total_pages_to_gen,
                "stage": "uploading",
            }
            await db.commit()

            # Upload to GCS
            images_to_upload = {
                p["page_number"]: p["image_base64"] for p in composed_pages if p.get("image_base64")
            }
            # Add dedication page with special key
            if dedication_image_b64:
                images_to_upload["dedication"] = dedication_image_b64

            uploaded_urls: dict[int | str, str] = {}
            if images_to_upload:
                try:
                    uploaded_urls = storage_service.upload_multiple_images(
                        images=images_to_upload,
                        story_id=story_id,
                    )
                    logger.info(f"Uploaded {len(uploaded_urls)} images successfully")
                except Exception as e:
                    logger.error(f"Image upload failed after retries: {e}")
                    # Do NOT fall back to base64 — it bloats Cloud SQL

            # JSONB keys string; mevcut (ilk 3) ile birleştir ki kaybolmasın
            page_images_for_db = {str(k): v for k, v in uploaded_urls.items()}
            existing_images = preview.page_images or {}
            if isinstance(existing_images, dict):
                existing_str = {str(k): v for k, v in existing_images.items()}
                page_images_for_db = {**existing_str, **page_images_for_db}
            preview.page_images = page_images_for_db
            if prompt_debug_collector:
                preview.prompt_debug_json = {str(k): v for k, v in prompt_debug_collector.items()}
                # Persist composed prompt (Cappadocia + style) so UI/email/admin see same text
                existing_pages = list(preview.story_pages or [])
                for i, p in enumerate(existing_pages):
                    if not isinstance(p, dict):
                        continue
                    pn = p.get("page_number")
                    if pn is not None and str(pn) in prompt_debug_collector:
                        existing_pages[i] = {
                            **p,
                            "visual_prompt": prompt_debug_collector[str(pn)]["final_prompt"],
                        }
                preview.story_pages = existing_pages
            if generation_manifest_collector:
                existing_manifest = preview.generation_manifest_json or {}
                preview.generation_manifest_json = {
                    **existing_manifest,
                    **{str(k): v for k, v in generation_manifest_collector.items()},
                }
            # Update generated_prompts_cache with final prompts (composed style+visual)
            _existing_cache = preview.generated_prompts_cache or {}
            _cached_prompts = list(_existing_cache.get("prompts") or [])
            if prompt_debug_collector:
                for _pn_str, _dbg in prompt_debug_collector.items():
                    _pn_int = int(_pn_str)
                    _found = False
                    for _cp in _cached_prompts:
                        if _cp.get("page_number") == _pn_int:
                            _cp["visual_prompt"] = _dbg.get("final_prompt", _cp.get("visual_prompt", ""))
                            if _dbg.get("negative_prompt"):
                                _cp["negative_prompt"] = _dbg["negative_prompt"]
                            _found = True
                            break
                    if not _found:
                        _cached_prompts.append({
                            "page_number": _pn_int,
                            "visual_prompt": _dbg.get("final_prompt", ""),
                            "negative_prompt": _dbg.get("negative_prompt", ""),
                            "v3_composed": True,
                            "pipeline_version": "v3",
                        })
                _existing_cache["prompts"] = _cached_prompts
                preview.generated_prompts_cache = _existing_cache

            # 3 önizleme sayfası hazır — status PROCESSING kalsin, onay e-postası GÖNDERME.
            # Hemen kalan sayfaların üretimini tetikle (ödeme zaten yapılmış).
            preview.generation_progress = None  # Clear progress — preview generation complete
            await db.commit()

            # Kalan sayfaları arka planda üret
            from app.workers.enqueue import enqueue_remaining_pages

            _remaining_job = await enqueue_remaining_pages(preview_id)
            if _remaining_job:
                logger.info(
                    "PREVIEW_DONE_REMAINING_ENQUEUED",
                    preview_id=preview_id,
                    arq_job_id=_remaining_job,
                )
            else:
                # Arq kuyruğuna eklenemedi — admin müdahalesi gerekli
                preview.status = "QUEUE_FAILED"
                preview.admin_notes = (
                    "3 önizleme sayfası tamamlandı ama kalan sayfalar kuyruğa eklenemedi. "
                    "Admin panelden 'Eksik Sayfa Oluştur' ile yeniden deneyin."
                )
                await db.commit()
                logger.critical(
                    "PREVIEW_DONE_REMAINING_QUEUE_FAILED",
                    preview_id=preview_id,
                )

            logger.info(f"Background processing complete for {preview_id}")

    except Exception as e:
        import traceback

        tb = traceback.format_exc()
        logger.error("Background processing failed", error=str(e), traceback=tb)
        err_msg = f"{type(e).__name__}: {str(e)}"
        if len(err_msg) > 400:
            err_msg = err_msg[:397] + "..."
        err_msg += "\n\n(Backend loglarında tam traceback var.)"
        try:
            preview_uuid = UUID(preview_id)
            async with async_session_factory() as db:
                result = await db.execute(
                    select(StoryPreview).where(StoryPreview.id == preview_uuid)
                )
                preview = result.scalar_one_or_none()
                if preview:
                    preview.status = "FAILED"
                    preview.admin_notes = err_msg
                    await db.commit()
        except Exception:
            pass


async def process_remaining_pages(preview_id: str) -> None:
    """
    Generate and save missing page images for a preview (e.g. after confirm when
    initial background run did not complete). Uses only DB data; does not send email.
    """
    import structlog

    logger = structlog.get_logger()
    logger.info("REMAINING_PAGES_QUEUED", preview_id=preview_id)

    async with _IMAGE_GEN_SEMAPHORE:
        logger.info("REMAINING_PAGES_START", preview_id=preview_id)
        await _process_remaining_pages_inner(preview_id)


async def _process_remaining_pages_inner(preview_id: str) -> None:
    """Actual implementation, runs inside the semaphore guard."""
    import asyncio
    import base64

    import httpx
    import structlog
    from sqlalchemy import select

    from app.core.database import async_session_factory
    from app.models.book_template import PageTemplate
    from app.models.story_preview import StoryPreview
    from app.services.ai.image_provider_dispatch import (
        get_effective_ai_config,
        get_image_provider_for_generation,
    )
    from app.services.page_composer import (
        build_template_config,
        effective_page_dimensions_mm,
        page_composer,
    )
    from app.services.storage_service import storage_service

    logger = structlog.get_logger()

    try:
        preview_uuid = UUID(preview_id)
        async with async_session_factory() as db:
            result = await db.execute(select(StoryPreview).where(StoryPreview.id == preview_uuid))
            preview = result.scalar_one_or_none()
            if not preview:
                logger.error("REMAINING_PAGES_PREVIEW_NOT_FOUND", preview_id=preview_id)
                return

            # Status'u PROCESSING yap — admin panelde "İşleniyor" görünsün
            preview.status = "PROCESSING"
            await db.commit()
            logger.info("REMAINING_PAGES_PROCESSING", preview_id=preview_id)

            ai_config_rem = await get_effective_ai_config(
                db, product_id=getattr(preview, "product_id", None)
            )
            provider_name_rem = (
                (ai_config_rem.image_provider or "fal").strip().lower() if ai_config_rem else "fal"
            )
            image_provider_rem = get_image_provider_for_generation(provider_name_rem)

            logger.info(
                "IMAGE_ENGINE_USED",
                provider=provider_name_rem,
                model=getattr(ai_config_rem, "image_model", "") if ai_config_rem else "",
                preview_id=preview_id,
                source="process_remaining_pages",
            )

            story_pages_raw = preview.story_pages or []
            existing = preview.page_images or {}
            if not isinstance(existing, dict):
                existing = {}

            # Build story_pages with image_base64 for existing (download from URL)
            story_pages: list[dict] = []
            for p in story_pages_raw:
                page_num = p.get("page_number") if isinstance(p, dict) else None
                if page_num is None:
                    continue
                entry = {
                    "page_number": page_num,
                    "text": p.get("text", ""),
                    "visual_prompt": p.get("visual_prompt", ""),
                    "image_base64": None,
                }
                url = existing.get(str(page_num)) or existing.get(page_num)
                if (
                    url
                    and isinstance(url, str)
                    and (url.startswith("http://") or url.startswith("https://"))
                ):
                    try:
                        async with httpx.AsyncClient(timeout=30.0) as client:
                            r = await client.get(url)
                            r.raise_for_status()
                            entry["image_base64"] = base64.b64encode(r.content).decode("utf-8")
                    except Exception as e:
                        logger.warning(
                            "REMAINING_PAGES_DOWNLOAD_FAILED",
                            preview_id=preview_id,
                            page_num=page_num,
                            error=str(e),
                        )
                story_pages.append(entry)

            if not story_pages:
                logger.warning("REMAINING_PAGES_NO_STORY_PAGES", preview_id=preview_id)
                return

            child_photo_url = getattr(preview, "child_photo_url", None) or ""
            child_gender = (getattr(preview, "child_gender", None) or "").strip()
            story_id = str(preview.id)[:8]

            from app.services.ai.face_service import resolve_face_reference
            from app.services.storage_service import storage_service as _ss_rem_ord
            _face_ref_url_rem, _face_embedding_rem = await resolve_face_reference(child_photo_url, _ss_rem_ord)

            # Stil: önce cache'teki style_id (sızıntı yok), yoksa visual_style_name ile tam eşleşme
            from app.models.visual_style import VisualStyle

            vs_rem = None
            cache_rem = getattr(preview, "generated_prompts_cache", None) or {}
            style_id_rem = cache_rem.get("style_id")
            if style_id_rem:
                try:
                    r_rem = await db.execute(
                        select(VisualStyle).where(VisualStyle.id == UUID(style_id_rem))
                    )
                    vs_rem = r_rem.scalar_one_or_none()
                except (ValueError, TypeError):
                    pass
            if vs_rem is None and getattr(preview, "visual_style_name", None):
                r_rem = await db.execute(
                    select(VisualStyle).where(VisualStyle.name == preview.visual_style_name)
                )
                vs_rem = r_rem.scalar_one_or_none()
                if vs_rem is None:
                    r_rem = await db.execute(
                        select(VisualStyle).where(VisualStyle.display_name == preview.visual_style_name)
                    )
                    vs_rem = r_rem.scalar_one_or_none()
            style_negative_rem = ""
            id_weight = None
            _rem_leading_prefix_override: str | None = None
            _rem_style_block_override: str | None = None
            _rem_true_cfg_override: float | None = None
            _rem_start_step_override: int | None = None
            _rem_num_inference_steps_override: int | None = None
            _rem_guidance_scale_override: float | None = None
            if vs_rem:
                if vs_rem.style_negative_en:
                    style_negative_rem = (vs_rem.style_negative_en or "").strip()
                if vs_rem.id_weight is not None:
                    id_weight = float(vs_rem.id_weight)
                _rem_leading_prefix_override = (vs_rem.leading_prefix_override or "").strip() or None
                _rem_style_block_override = (vs_rem.style_block_override or "").strip() or None
                _rem_true_cfg_override = float(vs_rem.true_cfg) if getattr(vs_rem, "true_cfg", None) is not None else None
                _rem_start_step_override = int(vs_rem.start_step) if getattr(vs_rem, "start_step", None) is not None else None
                _rem_num_inference_steps_override = int(vs_rem.num_inference_steps) if getattr(vs_rem, "num_inference_steps", None) is not None else None
                _rem_guidance_scale_override = float(vs_rem.guidance_scale) if getattr(vs_rem, "guidance_scale", None) is not None else None
            visual_style = (
                (vs_rem.prompt_modifier or "").strip()
                if vs_rem
                else (getattr(preview, "visual_style_name", None) or "children's book illustration")
            )
            visual_style = personalize_style_prompt(
                visual_style,
                child_name=getattr(preview, "child_name", None) or "",
                child_age=getattr(preview, "child_age", None) or 7,
                child_gender=child_gender,
            )

            # V2: Fetch COVER/INNER templates and NEGATIVE_PROMPT from DB
            from app.prompt_engine.constants import (
                DEFAULT_COVER_TEMPLATE_EN,
                DEFAULT_INNER_TEMPLATE_EN,
                NEGATIVE_PROMPT,
            )
            from app.services.prompt_template_service import get_prompt_service

            _tpl_svc = get_prompt_service()
            cover_tpl = await _tpl_svc.get_template_en(
                db, "COVER_TEMPLATE", DEFAULT_COVER_TEMPLATE_EN
            )
            inner_tpl = await _tpl_svc.get_template_en(
                db, "INNER_TEMPLATE", DEFAULT_INNER_TEMPLATE_EN
            )
            base_neg_rem = await _tpl_svc.get_prompt(db, "NEGATIVE_PROMPT", NEGATIVE_PROMPT)

            # Ürün şablonları (remaining pages boyutları için)
            rem_cover_tpl = None
            rem_inner_tpl = None
            if getattr(preview, "product_id", None):
                from sqlalchemy.orm import selectinload

                from app.models.product import Product
                r_rem = await db.execute(
                    select(Product)
                    .where(Product.id == preview.product_id)
                    .options(
                        selectinload(Product.inner_template),
                        selectinload(Product.cover_template),
                    )
                )
                rem_product = r_rem.scalar_one_or_none()
                if rem_product:
                    rem_cover_tpl = rem_product.cover_template
                    rem_inner_tpl = rem_product.inner_template

            # Clothing: DB'den oku, yoksa visual_prompt'tan regex ile cikar (fallback)
            clothing_desc = (getattr(preview, "clothing_description", None) or "").strip()
            if not clothing_desc:
                for p in story_pages:
                    vp = (p.get("visual_prompt") or "").strip()
                    if "wearing" in vp.lower():
                        m = re.search(
                            r"(?:A young child wearing|The child is wearing)\s+([^.]+?)(?:\.|$)",
                            vp,
                            re.IGNORECASE,
                        )
                        if m:
                            clothing_desc = m.group(1).strip()
                            break

            page_images: dict[int, str] = {}
            prompt_debug_collector: dict[int, dict] = {}
            generation_manifest_collector: dict[int, dict] = {}

            # Separate existing and to-generate pages
            rem_pages_to_generate: list[dict] = []
            for page in story_pages:
                page_num = int(page["page_number"])
                # Skip front_matter pages (text-only, no image generation)
                if page.get("page_type") == "front_matter":
                    logger.info("REMAINING_PAGES_SKIP_FRONT_MATTER", page_num=page_num)
                    continue
                if page.get("image_base64"):
                    page_images[page_num] = page["image_base64"]
                    logger.info("REMAINING_PAGES_USE_EXISTING", page_num=page_num)
                    continue
                rem_pages_to_generate.append(page)

            # Calculate upscale params from template (print quality)
            from app.utils.resolution_calc import (
                get_effective_generation_params as _get_gen_params_rem,
            )
            from app.utils.resolution_calc import (
                resize_image_bytes_to_target,
            )

            _rem_upscale_params: dict | None = None
            if rem_inner_tpl:
                _rem_upscale_params = _get_gen_params_rem(rem_inner_tpl)
            elif rem_cover_tpl:
                _rem_upscale_params = _get_gen_params_rem(rem_cover_tpl)

            # Parallel generation with concurrency limit
            _rem_sem = asyncio.Semaphore(settings.image_concurrency)

            async def _gen_rem_page(page: dict) -> dict:
                """Generate a single remaining page with retry + upscale for print."""
                page_num = int(page["page_number"])
                async with _rem_sem:
                    last_error = None
                    for attempt in range(3):
                        try:
                            logger.info(
                                "REMAINING_PAGES_GENERATE", page_num=page_num, attempt=attempt + 1
                            )
                            if page_num == 0 and rem_cover_tpl:
                                _p = _get_gen_params_rem(rem_cover_tpl)
                                w, h = _p["generation_width"], _p["generation_height"]
                            elif rem_inner_tpl:
                                _p = _get_gen_params_rem(rem_inner_tpl)
                                w, h = _p["generation_width"], _p["generation_height"]
                            else:
                                w, h = get_page_image_dimensions(page_num)
                            _is_cover_r = page_num == 0
                            _child_age_r = getattr(preview, "child_age", None) or 7
                            scene_for_fal = (
                                page.get("visual_prompt") or page.get("text") or ""
                            ).strip()
                            _is_v3_rem = page.get("v3_composed", False)
                            result = await image_provider_rem.generate_consistent_image(
                                prompt=scene_for_fal,
                                child_face_url=_face_ref_url_rem or "",
                                clothing_prompt=clothing_desc,
                                style_modifier=visual_style,
                                width=w,
                                height=h,
                                id_weight=id_weight,
                                true_cfg_override=_rem_true_cfg_override,
                                start_step_override=_rem_start_step_override,
                                num_inference_steps_override=_rem_num_inference_steps_override,
                                guidance_scale_override=_rem_guidance_scale_override,
                                is_cover=_is_cover_r,
                                page_number=page_num,
                                preview_id=preview_id,
                                order_id=None,
                                template_en=cover_tpl if _is_cover_r else inner_tpl,
                                story_title=(getattr(preview, "story_title", None) or "").strip()
                                if _is_cover_r
                                else "",
                                child_gender=child_gender,
                                child_age=_child_age_r,
                                style_negative_en=style_negative_rem,
                                base_negative_en=base_neg_rem or "",
                                leading_prefix_override=_rem_leading_prefix_override,
                                style_block_override=_rem_style_block_override,
                                skip_compose=_is_v3_rem,
                                precomposed_negative=page.get("negative_prompt", "") if _is_v3_rem else "",
                                reference_embedding=_face_embedding_rem,
                            )
                            image_url = result[0] if isinstance(result, tuple) else result
                            _debug_info: dict = {}
                            if isinstance(result, tuple) and len(result) == 2 and result[1]:
                                _debug_info = result[1]
                            if image_url:
                                # Start upscale task concurrently but don't await immediately if we want pure parallelism
                                # However, within a single page generation, we need the upscaled result to resize and save.
                                # The parallelism comes from the fact that _gen_rem_page is called for ALL pages concurrently via asyncio.gather.
                                # So page 1 upscale and page 2 generation CAN happen at the same time.

                                # Download image
                                async with httpx.AsyncClient(timeout=120.0) as client:
                                    r = await client.get(image_url)
                                    r.raise_for_status()
                                    raw_bytes = r.content

                                # Upscale for print quality (Real-ESRGAN if configured)
                                if _rem_upscale_params and _rem_upscale_params.get("needs_upscale") and _rem_upscale_params.get("upscale_factor", 1) > 1:
                                    try:
                                        from app.services.upscale_service import upscale_image_bytes_safe
                                        raw_bytes = await upscale_image_bytes_safe(
                                            raw_bytes,
                                            upscale_factor=_rem_upscale_params["upscale_factor"],
                                        )
                                        logger.info(
                                            "PREVIEW_UPSCALE_APPLIED",
                                            page_num=page_num,
                                            factor=_rem_upscale_params["upscale_factor"],
                                        )
                                    except Exception as up_err:
                                        logger.warning(
                                            "PREVIEW_UPSCALE_FAILED",
                                            page_num=page_num,
                                            error=str(up_err),
                                        )

                                # Resize to exact print target if params available
                                if _rem_upscale_params:
                                    try:
                                        raw_bytes = await asyncio.to_thread(
                                            resize_image_bytes_to_target,
                                            raw_bytes,
                                            _rem_upscale_params["target_width"],
                                            _rem_upscale_params["target_height"],
                                        )
                                    except Exception as rsz_err:
                                        logger.warning(
                                            "REMAINING_PAGE_RESIZE_FAILED",
                                            page_num=page_num,
                                            error=str(rsz_err),
                                        )

                                img_b64 = base64.b64encode(raw_bytes).decode("utf-8")
                                logger.info("REMAINING_PAGES_GENERATED", page_num=page_num)
                                return {
                                    "page_num": page_num,
                                    "image_base64": img_b64,
                                    "debug_info": _debug_info,
                                }
                            last_error = ValueError("No image URL returned")
                        except VisualPromptValidationError as e:
                            logger.error(
                                "Visual prompt validation failed", page_num=page_num, detail=str(e)
                            )
                            return {"page_num": page_num, "error": e, "validation_error": True}
                        except Exception as e:
                            last_error = e
                            logger.warning(
                                "REMAINING_PAGES_GENERATE_FAILED", page_num=page_num, error=str(e)
                            )
                            if attempt < 2:
                                await asyncio.sleep(3)
                    logger.error(
                        "REMAINING_PAGES_ALL_FAILED", page_num=page_num, error=str(last_error)
                    )
                    return {"page_num": page_num, "error": last_error}

            rem_gen_results = await asyncio.gather(
                *[_gen_rem_page(p) for p in rem_pages_to_generate],
                return_exceptions=True,
            )

            # Process results
            for r in rem_gen_results:
                if isinstance(r, Exception):
                    logger.error("Unexpected remaining page generation error", error=str(r))
                    continue
                if not isinstance(r, dict):
                    continue
                page_num = r["page_num"]
                if r.get("validation_error"):
                    raise ValueError(f"Gorsel prompt dogrulama hatasi: {r['error']}")
                if "image_base64" in r:
                    page_images[page_num] = r["image_base64"]
                    info = r.get("debug_info") or {}
                    if info.get("manifest") and info.get("page_index") is not None:
                        manifest_entry = dict(info["manifest"])
                        if info.get("final_prompt") is not None:
                            manifest_entry["final_prompt"] = info["final_prompt"]
                        if info.get("negative_prompt") is not None:
                            manifest_entry["negative_prompt"] = info["negative_prompt"]
                        generation_manifest_collector[str(info["page_index"])] = manifest_entry
                    if info.get("final_prompt") is not None and info.get("page_index") is not None:
                        prompt_debug_collector[str(info["page_index"])] = {
                            "final_prompt": info["final_prompt"],
                            "negative_prompt": info["negative_prompt"],
                        }

            # Başarısızlık kontrolü: hiçbir yeni sayfa üretilemezse Arq retry tetikle
            _new_images_count = sum(
                1 for r in rem_gen_results
                if isinstance(r, dict) and "image_base64" in r
            )
            _failed_count = len(rem_pages_to_generate) - _new_images_count
            if _new_images_count == 0 and len(rem_pages_to_generate) > 0:
                raise RuntimeError(
                    f"Kalan {len(rem_pages_to_generate)} sayfanın HİÇBİRİ üretilemedi. "
                    f"Arq retry yapacak."
                )
            if _failed_count > 0:
                logger.warning(
                    "REMAINING_PAGES_PARTIAL_FAILURE",
                    preview_id=preview_id,
                    generated=_new_images_count,
                    failed=_failed_count,
                    total_requested=len(rem_pages_to_generate),
                )

            # Aynı şablon kaynağı: ürün şablonu veya en son güncellenen
            inner_template_r = None
            cover_template_r = None
            if getattr(preview, "product_id", None):
                from sqlalchemy.orm import selectinload

                from app.models.product import Product
                rp = await db.execute(
                    select(Product)
                    .where(Product.id == preview.product_id)
                    .options(
                        selectinload(Product.inner_template),
                        selectinload(Product.cover_template),
                    )
                )
                product_r = rp.scalar_one_or_none()
                if product_r:
                    inner_template_r = product_r.inner_template
                    cover_template_r = product_r.cover_template
            if not inner_template_r:
                result = await db.execute(
                    select(PageTemplate)
                    .where(PageTemplate.is_active == True)
                    .order_by(PageTemplate.updated_at.desc().nulls_last())
                )
                templates = {}
                for t in result.scalars().all():
                    if t.page_type not in templates:
                        templates[t.page_type] = t
                inner_template_r = templates.get("inner")
                cover_template_r = templates.get("cover")
            inner_template = inner_template_r
            cover_template = cover_template_r

            def _display_prompt_remaining(page: dict, page_num: int) -> str:
                if prompt_debug_collector and str(page_num) in prompt_debug_collector:
                    return prompt_debug_collector[str(page_num)].get("final_prompt") or page.get(
                        "visual_prompt", ""
                    )
                return page.get("visual_prompt", "")

            composed_pages = []
            for page in story_pages:
                page_num = int(page["page_number"])
                image_base64 = page_images.get(page_num)
                display_prompt = _display_prompt_remaining(page, page_num)
                page_data = {
                    "page_number": page_num,
                    "text": page["text"],
                    "visual_prompt": display_prompt,
                    "image_base64": image_base64,
                }
                template = cover_template if (page_num == 0 and cover_template) else inner_template
                # Kapak (page 0): hikaye metni değil, kitap başlığı kullan
                _comp_text = page["text"]
                if page_num == 0:
                    _comp_text = (getattr(preview, "story_title", "") or "").strip() or _comp_text

                if image_base64 and template:
                    template_config = build_template_config(template)
                    _pw, _ph = effective_page_dimensions_mm(template.page_width_mm, template.page_height_mm)
                    page_data["image_base64"] = page_composer.compose_page(
                        image_base64=image_base64,
                        text=_comp_text,
                        template_config=template_config,
                        page_width_mm=_pw,
                        page_height_mm=_ph,
                        dpi=300,
                    )
                composed_pages.append(page_data)

            images_to_upload = {
                p["page_number"]: p["image_base64"] for p in composed_pages if p.get("image_base64")
            }
            uploaded_urls: dict[int, str] = {}
            if images_to_upload:
                try:
                    uploaded_urls = storage_service.upload_multiple_images(
                        images=images_to_upload,
                        story_id=story_id,
                    )
                except Exception as e:
                    logger.error("REMAINING_PAGES_UPLOAD_FAILED (no base64 fallback)", error=str(e))
                    # Do NOT fall back to base64 — it bloats Cloud SQL

            page_images_for_db = {str(k): v for k, v in uploaded_urls.items()}
            existing_str = {
                str(k): v
                for k, v in (preview.page_images or {}).items()
                if isinstance(preview.page_images, dict)
            }
            preview.page_images = {**existing_str, **page_images_for_db}
            if prompt_debug_collector:
                existing_debug = preview.prompt_debug_json or {}
                preview.prompt_debug_json = {
                    **existing_debug,
                    **{str(k): v for k, v in prompt_debug_collector.items()},
                }
                existing_pages = list(preview.story_pages or [])
                for i, p in enumerate(existing_pages):
                    if not isinstance(p, dict):
                        continue
                    pn = p.get("page_number")
                    if pn is not None and str(pn) in prompt_debug_collector:
                        existing_pages[i] = {
                            **p,
                            "visual_prompt": prompt_debug_collector[str(pn)]["final_prompt"],
                        }
                preview.story_pages = existing_pages
            if generation_manifest_collector:
                existing_manifest = preview.generation_manifest_json or {}
                preview.generation_manifest_json = {
                    **existing_manifest,
                    **{str(k): v for k, v in generation_manifest_collector.items()},
                }

            # Update generated_prompts_cache with final prompts from remaining pages
            if prompt_debug_collector:
                _rem_cache = preview.generated_prompts_cache or {}
                _rem_cached_prompts = list(_rem_cache.get("prompts") or [])
                for _pn_str, _dbg in prompt_debug_collector.items():
                    _pn_int = int(_pn_str)
                    _found = False
                    for _cp in _rem_cached_prompts:
                        if _cp.get("page_number") == _pn_int:
                            _cp["visual_prompt"] = _dbg.get("final_prompt", _cp.get("visual_prompt", ""))
                            if _dbg.get("negative_prompt"):
                                _cp["negative_prompt"] = _dbg["negative_prompt"]
                            _found = True
                            break
                    if not _found:
                        _rem_cached_prompts.append({
                            "page_number": _pn_int,
                            "visual_prompt": _dbg.get("final_prompt", ""),
                            "negative_prompt": _dbg.get("negative_prompt", ""),
                            "v3_composed": True,
                            "pipeline_version": "v3",
                        })
                _rem_cache["prompts"] = _rem_cached_prompts
                preview.generated_prompts_cache = _rem_cache

            # Tum sayfalar tamamlandiginda status'u guncelle
            total_story_pages = len(preview.story_pages) if preview.story_pages else 0
            total_images_now = len(preview.page_images) if preview.page_images else 0
            if total_images_now >= total_story_pages and total_story_pages > 0:
                # Tüm sayfalar hazır — müşteri onayı bekleniyor
                preview.status = "PENDING"
                logger.info(
                    "REMAINING_PAGES_ALL_COMPLETE_PENDING_APPROVAL",
                    preview_id=preview_id,
                    total_images=total_images_now,
                    total_pages=total_story_pages,
                )
            else:
                # Eksik sayfalar var — admin notu bırak
                _missing = total_story_pages - total_images_now
                preview.admin_notes = (
                    (preview.admin_notes or "")
                    + f"\n\nKalan sayfa üretimi tamamlanamadı: {_missing} sayfa eksik. "
                    f"Admin panelden 'Eksik Sayfa Oluştur' ile yeniden deneyin."
                )

            await db.commit()
            logger.info(
                "REMAINING_PAGES_DONE",
                preview_id=preview_id,
                total_images=total_images_now,
            )

            # ── PDF generation + onay e-postası (tüm sayfalar hazırsa) ──
            if preview.status == "PENDING":
                try:
                    from app.models.book_template import BackCoverConfig
                    from app.services.email_service import email_service
                    from app.services.pdf_service import PDFService

                    # Resolve templates for PDF (product-specific or default)
                    _pdf_inner = inner_template
                    _pdf_cover = cover_template
                    _pdf_page_w = _pdf_inner.page_width_mm if _pdf_inner else 297.0
                    _pdf_page_h = _pdf_inner.page_height_mm if _pdf_inner else 210.0
                    _pdf_bleed = _pdf_inner.bleed_mm if _pdf_inner else 3.0

                    # Dedication page
                    _pdf_ded_tpl_r = await db.execute(
                        select(PageTemplate)
                        .where(PageTemplate.page_type == "dedication", PageTemplate.is_active == True)
                    )
                    _pdf_ded_tpl = _pdf_ded_tpl_r.scalar_one_or_none()

                    _pdf_ded_note = getattr(preview, "dedication_note", None)
                    if not _pdf_ded_note:
                        # Try AI-generated dedication text from story_pages
                        for _sp in (preview.story_pages or []):
                            if isinstance(_sp, dict) and _sp.get("page_type") == "front_matter" and (_sp.get("text") or "").strip():
                                _pdf_ded_note = _sp["text"].strip()
                                break
                    if not _pdf_ded_note and _pdf_ded_tpl:
                        _ded_default = getattr(_pdf_ded_tpl, "dedication_default_text", None) or ""
                        if _ded_default:
                            _pdf_ded_note = _ded_default.replace(
                                "{child_name}", preview.child_name or ""
                            )

                    _pdf_ded_b64: str | None = None
                    if _pdf_ded_note:
                        try:
                            _ded_cfg = build_template_config(_pdf_ded_tpl) if _pdf_ded_tpl else {}
                            _pdf_ded_b64 = page_composer.compose_dedication_page(
                                text=_pdf_ded_note, template_config=_ded_cfg, dpi=300,
                            )
                        except Exception as _ded_err:
                            logger.warning("Dedication compose failed for PDF", error=str(_ded_err))

                    # Back cover config
                    _pdf_back_cover = None
                    try:
                        _bc_r = await db.execute(
                            select(BackCoverConfig)
                            .where(BackCoverConfig.is_active == True)
                            .where(BackCoverConfig.is_default == True)
                        )
                        _pdf_back_cover = _bc_r.scalar_one_or_none()
                    except Exception:
                        pass

                    # Audio QR URL
                    _pdf_audio_url = getattr(preview, "audio_file_url", None)

                    # Collect all image URLs for PDF
                    # NOTE: page_images contains ALREADY-COMPOSED URLs (text overlay applied).
                    all_images = preview.page_images or {}

                    _pdf_composed: list[dict] = []
                    for page in (preview.story_pages or []):
                        _pn = page.get("page_number")
                        if _pn is None:
                            continue
                        if page.get("page_type") == "front_matter":
                            continue

                        _img_url = all_images.get(str(_pn))
                        _comp_text = page.get("text", "")
                        if _pn == 0:
                            _comp_text = (preview.story_title or "").strip() or _comp_text

                        _pdf_composed.append({
                            "page_number": _pn,
                            "text": _comp_text,
                            "image_url": _img_url,
                        })

                    # Separate cover from inner pages
                    _cover_url: str | None = None
                    _inner_pages: list[dict] = []
                    for _p in _pdf_composed:
                        if _p.get("page_number") == 0:
                            _cover_url = _p.get("image_url")
                        else:
                            _inner_pages.append(_p)

                    _inner_tpl_cfg = build_template_config(_pdf_inner) if _pdf_inner else {}
                    pdf_data = {
                        "story_title": preview.story_title,
                        "child_name": preview.child_name,
                        "story_pages": _inner_pages,
                        "cover_image_url": _cover_url,
                        "dedication_image_base64": _pdf_ded_b64,
                        "back_cover_config": _pdf_back_cover,
                        "audio_qr_url": _pdf_audio_url,
                        "page_width_mm": _pdf_page_w,
                        "page_height_mm": _pdf_page_h,
                        "bleed_mm": _pdf_bleed,
                        "template_config": _inner_tpl_cfg,
                        "images_precomposed": True,
                    }

                    _pdf_svc = PDFService()
                    _pdf_bytes = _pdf_svc.generate_book_pdf_from_preview(pdf_data)

                    if _pdf_bytes:
                        _pdf_url = storage_service.upload_pdf(
                            pdf_bytes=_pdf_bytes,
                            order_id=str(preview.id),
                        )
                        logger.info(
                            "REMAINING_PAGES_PDF_GENERATED",
                            preview_id=preview_id, pdf_url=_pdf_url,
                        )
                        preview.admin_notes = (
                            (preview.admin_notes or "") + f"\n\nPDF URL: {_pdf_url}"
                        )
                        await db.commit()

                    # Müşteriye tüm sayfalar + onay linki ile e-posta gönder
                    _parent_email = getattr(preview, "parent_email", None)
                    if _parent_email:
                        try:
                            _email_pages = [
                                {
                                    "page_number": _p["page_number"],
                                    "text": _p.get("text", ""),
                                    "image_url": all_images.get(str(_p["page_number"])),
                                }
                                for _p in _pdf_composed
                            ]
                            _confirmation_url = (
                                f"{settings.frontend_url}/confirm/"
                                f"{preview.confirmation_token}"
                            )
                            email_service.send_story_email_with_confirmation(
                                recipient_email=_parent_email,
                                recipient_name=preview.parent_name or _parent_email,
                                child_name=preview.child_name,
                                story_title=preview.story_title,
                                story_pages=_email_pages,
                                confirmation_url=_confirmation_url,
                                product_price=(
                                    float(preview.product_price)
                                    if preview.product_price
                                    else None
                                ),
                            )
                            logger.info(
                                "REMAINING_PAGES_APPROVAL_EMAIL_SENT",
                                preview_id=preview_id,
                            )
                        except Exception as _mail_err:
                            logger.warning(
                                "REMAINING_PAGES_APPROVAL_EMAIL_FAILED (PDF still saved)",
                                preview_id=preview_id,
                                error=str(_mail_err),
                            )
                            preview.admin_notes = (
                                (preview.admin_notes or "")
                                + f"\n\nOnay e-postası gönderilemedi: {str(_mail_err)[:300]}"
                            )
                            await db.commit()

                except Exception as _pdf_mail_err:
                    logger.exception(
                        "REMAINING_PAGES_PDF_EMAIL_FAILED",
                        preview_id=preview_id,
                        error=str(_pdf_mail_err),
                    )
    except Exception as e:
        import traceback

        logger.error(
            "REMAINING_PAGES_ERROR",
            preview_id=preview_id,
            error=str(e),
            traceback=traceback.format_exc(),
        )
        # Mark preview as FAILED so admin can see stuck orders
        try:
            from app.core.database import async_session_factory

            async with async_session_factory() as err_db:
                from app.models.story_preview import StoryPreview as _SP

                _err_r = await err_db.execute(select(_SP).where(_SP.id == preview_id))
                _err_prev = _err_r.scalar_one_or_none()
                if _err_prev and _err_prev.status not in ("COMPLETED", "FAILED", "PENDING", "CONFIRMED"):
                    _err_prev.status = "FAILED"
                    _err_prev.generation_progress = {
                        "stage": "error",
                        "error": str(e)[:500],
                    }
                    await err_db.commit()
                    logger.info("REMAINING_PAGES_MARKED_FAILED", preview_id=preview_id)
        except Exception as status_err:
            logger.warning("Could not mark preview as FAILED", error=str(status_err))


MAX_PAGE_REGENERATIONS = 3


@router.get("/preview-by-token/{token}")
async def get_preview_by_token(
    token: str,
    db: DbSession,
) -> dict:
    """
    Token ile sipariş detayını getir (onay yapmadan).
    Müşteriye kitabı göstermek için kullanılır.
    """
    from sqlalchemy import select

    from app.models.story_preview import StoryPreview

    result = await db.execute(
        select(StoryPreview).where(StoryPreview.confirmation_token == token)
    )
    preview = result.scalar_one_or_none()
    if not preview:
        raise NotFoundError("Sipariş", token)

    page_images = preview.page_images or {}
    story_pages = preview.story_pages or []

    return {
        "id": str(preview.id),
        "status": preview.status,
        "story_title": preview.story_title,
        "child_name": preview.child_name,
        "child_age": preview.child_age,
        "parent_name": preview.parent_name,
        "product_name": preview.product_name,
        "product_price": float(preview.product_price) if preview.product_price else None,
        "page_count": len(story_pages),
        "image_count": len([k for k in page_images if k != "dedication"]),
        "page_images": page_images,
        "story_pages": [
            {
                "page_number": p.get("page_number"),
                "text": p.get("text", ""),
            }
            for p in story_pages
            if isinstance(p, dict)
        ],
        "dedication_note": getattr(preview, "dedication_note", None),
        "created_at": preview.created_at.isoformat() if preview.created_at else None,
        "page_regenerate_count": preview.page_regenerate_count or 0,
        "max_page_regenerations": MAX_PAGE_REGENERATIONS,
    }


class RegeneratePageRequest(BaseModel):
    page_number: int | str


@router.post("/preview-by-token/{token}/regenerate-page")
async def regenerate_page_image(
    token: str,
    body: RegeneratePageRequest,
    db: DbSession,
) -> dict:
    """Regenerate a single page image on the confirmation page.

    The customer gets up to 3 regeneration chances (total, not per-page)
    before confirming the order.
    """
    from sqlalchemy import update as sa_update
    from sqlalchemy.orm import selectinload

    from app.api.v1.trials import _resolve_visual_style_from_db
    from app.models.book_template import PageTemplate
    from app.models.product import Product
    from app.models.story_preview import PreviewStatus, StoryPreview
    from app.prompt_engine.constants import (
        DEFAULT_COVER_TEMPLATE_EN as _DEF_COVER,
    )
    from app.prompt_engine.constants import (
        DEFAULT_INNER_TEMPLATE_EN as _DEF_INNER,
    )
    from app.services.ai.image_provider_dispatch import (
        get_effective_ai_config,
        get_image_provider_for_generation,
    )
    from app.services.page_composer import (
        build_template_config,
        effective_page_dimensions_mm,
        page_composer,
    )
    from app.services.prompt_template_service import get_prompt_service
    from app.services.storage_service import storage_service
    from app.utils.resolution_calc import DEFAULT_GENERATION_A4_LANDSCAPE

    logger = structlog.get_logger()
    page_key = str(body.page_number)

    # ── Phase 1: validate + reserve a regen slot (short lock) ──
    result = await db.execute(
        select(StoryPreview)
        .where(StoryPreview.confirmation_token == token)
        .with_for_update()
    )
    preview = result.scalar_one_or_none()
    if not preview:
        raise NotFoundError("Sipariş", token)

    if preview.status not in (
        PreviewStatus.PENDING.value,
        PreviewStatus.PREVIEW_GENERATED.value,
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Sadece onay bekleyen siparişlerde resim yenilenebilir.",
        )

    current_count = preview.page_regenerate_count or 0
    if current_count >= MAX_PAGE_REGENERATIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Yeniden çizim hakkınız doldu (maksimum {MAX_PAGE_REGENERATIONS}).",
        )

    if page_key == "dedication":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Karşılama sayfası yeniden çizilemez.",
        )

    cache = preview.generated_prompts_cache or {}
    prompts = cache.get("prompts") or []
    page_num_int = int(page_key) if page_key.isdigit() else -1
    prompt_data = next(
        (p for p in prompts if p.get("page_number") == page_num_int),
        None,
    )

    # Fallback: cache boşsa story_pages'den prompt bul (eski siparişler için)
    if not prompt_data:
        _story_pages = preview.story_pages or []
        _sp_match = next(
            (sp for sp in _story_pages
             if isinstance(sp, dict) and sp.get("page_number") == page_num_int),
            None,
        )
        if _sp_match and _sp_match.get("visual_prompt"):
            prompt_data = {
                "page_number": page_num_int,
                "visual_prompt": _sp_match["visual_prompt"],
                "v3_composed": _sp_match.get("v3_composed", False),
                "negative_prompt": _sp_match.get("negative_prompt", ""),
            }
            logger.info(
                "Regen prompt from story_pages fallback",
                page=page_key,
                prompt_len=len(prompt_data["visual_prompt"]),
            )

    if not prompt_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Sayfa {page_key} için prompt bulunamadı.",
        )

    # Snapshot fields we need for AI generation before releasing the lock
    preview_id = preview.id
    child_photo_url = preview.child_photo_url or ""
    clothing_desc = preview.clothing_description or ""
    visual_style_name = preview.visual_style_name
    story_title = preview.story_title or ""
    existing_page_images = dict(preview.page_images or {})
    product_id = preview.product_id
    child_name = preview.child_name or ""
    child_age = preview.child_age or 7
    child_gender = preview.child_gender or ""

    # Find page text for composition
    story_pages_list = preview.story_pages or []
    page_text = ""
    for sp in story_pages_list:
        if sp.get("page_number") == page_num_int:
            page_text = sp.get("text", "")
            break

    # Increment count atomically and release the row lock
    preview.page_regenerate_count = current_count + 1
    await db.commit()

    # ── Phase 2: AI image generation (no DB lock held) ──
    actual_style = ""
    style_negative_en = ""
    leading_prefix_override = None
    style_block_override = None
    regen_id_weight: float | None = None
    regen_true_cfg_override: float | None = None
    regen_start_step_override: int | None = None
    regen_num_inference_steps_override: int | None = None
    regen_guidance_scale_override: float | None = None

    vs = await _resolve_visual_style_from_db(db, visual_style_name)
    if vs:
        actual_style = (vs.prompt_modifier or "").strip()
        style_negative_en = (vs.style_negative_en or "").strip()
        leading_prefix_override = (vs.leading_prefix_override or "").strip() or None
        style_block_override = (vs.style_block_override or "").strip() or None
        if vs.id_weight is not None:
            regen_id_weight = float(vs.id_weight)
        regen_true_cfg_override = float(vs.true_cfg) if getattr(vs, "true_cfg", None) is not None else None
        regen_start_step_override = int(vs.start_step) if getattr(vs, "start_step", None) is not None else None
        regen_num_inference_steps_override = int(vs.num_inference_steps) if getattr(vs, "num_inference_steps", None) is not None else None
        regen_guidance_scale_override = float(vs.guidance_scale) if getattr(vs, "guidance_scale", None) is not None else None

    from app.services.ai.image_provider_dispatch import DEFAULT_PROVIDER_FALLBACK
    ai_config = await get_effective_ai_config(db, product_id=product_id)
    provider_name = (
        (ai_config.image_provider or DEFAULT_PROVIDER_FALLBACK).strip().lower()
        if ai_config
        else DEFAULT_PROVIDER_FALLBACK
    )
    image_provider = get_image_provider_for_generation(provider_name)

    tpl_svc = get_prompt_service()
    cover_tpl = await tpl_svc.get_template_en(db, "COVER_TEMPLATE", _DEF_COVER)
    inner_tpl = await tpl_svc.get_template_en(db, "INNER_TEMPLATE", _DEF_INNER)

    width, height = DEFAULT_GENERATION_A4_LANDSCAPE
    visual_prompt = prompt_data["visual_prompt"]
    is_v3 = prompt_data.get("v3_composed", False)
    is_cover = page_num_int == 0

    from app.services.ai.face_service import resolve_face_reference
    from app.services.storage_service import storage_service as _ss_regen
    _regen_face_url, _regen_face_embedding = await resolve_face_reference(child_photo_url, _ss_regen)

    # AI-Director: generate character description for face likeness
    _regen_char_desc = ""
    if _regen_face_url:
        try:
            from app.services.ai.face_analyzer_service import get_face_analyzer as _get_fa_regen
            _fa_regen = _get_fa_regen()
            _regen_char_desc = await _fa_regen.analyze_for_ai_director(
                image_source=_regen_face_url,
                child_name=child_name,
                child_age=child_age,
                child_gender=child_gender,
            )
            logger.info(
                "Regen: character description ready",
                page=page_key,
                description_length=len(_regen_char_desc),
            )
        except Exception as _fa_err:
            logger.warning(
                "Regen: face analysis failed — no character description",
                page=page_key,
                error=str(_fa_err),
            )

    try:
        gen_result = await image_provider.generate_consistent_image(
            prompt=visual_prompt,
            child_face_url=_regen_face_url,
            clothing_prompt=clothing_desc,
            style_modifier=actual_style,
            width=width,
            height=height,
            is_cover=is_cover,
            template_en=cover_tpl if is_cover else inner_tpl,
            story_title=story_title if is_cover else "",
            child_gender=child_gender,
            child_age=child_age,
            style_negative_en=style_negative_en,
            leading_prefix_override=leading_prefix_override,
            style_block_override=style_block_override,
            id_weight=regen_id_weight,
            true_cfg_override=regen_true_cfg_override,
            start_step_override=regen_start_step_override,
            num_inference_steps_override=regen_num_inference_steps_override,
            guidance_scale_override=regen_guidance_scale_override,
            skip_compose=is_v3,
            precomposed_negative=prompt_data.get("negative_prompt", "") if is_v3 else "",
            reference_embedding=_regen_face_embedding,
            character_description=_regen_char_desc,
        )
        new_image_url = gen_result[0] if isinstance(gen_result, tuple) else gen_result
    except Exception as e:
        logger.exception("Page regeneration failed", token=token[:10], page=page_key, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Resim yeniden oluşturulamadı. Lütfen tekrar deneyin.",
        ) from e

    if not new_image_url:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Resim üretilemedi, lütfen tekrar deneyin.",
        )

    # ── Phase 2b: upscale + text overlay + GCS upload ──
    import base64 as _b64

    import httpx

    # Download raw AI image → base64
    image_base64 = ""
    try:
        async with httpx.AsyncClient(timeout=60) as _http:
            resp = await _http.get(new_image_url)
            resp.raise_for_status()
            image_base64 = _b64.b64encode(resp.content).decode()
    except Exception as dl_err:
        logger.warning("Regen image download failed, skipping compose", error=str(dl_err))

    # Resolve templates for text overlay
    regen_cover_tpl = None
    regen_inner_tpl = None
    if product_id:
        _prod_res = await db.execute(
            select(Product)
            .where(Product.id == product_id)
            .options(selectinload(Product.inner_template), selectinload(Product.cover_template))
        )
        _prod = _prod_res.scalar_one_or_none()
        if _prod:
            regen_cover_tpl = _prod.cover_template
            regen_inner_tpl = _prod.inner_template

    if not regen_inner_tpl:
        _tpl_res = await db.execute(
            select(PageTemplate)
            .where(PageTemplate.is_active == True)
            .order_by(PageTemplate.updated_at.desc().nulls_last())
        )
        for _t in _tpl_res.scalars():
            if _t.page_type == "cover" and not regen_cover_tpl:
                regen_cover_tpl = _t
            elif _t.page_type == "inner" and not regen_inner_tpl:
                regen_inner_tpl = _t

    # Compose text on image
    composed_b64 = image_base64
    _tpl = regen_cover_tpl if is_cover else regen_inner_tpl
    if image_base64 and _tpl:
        try:
            _compose_text = story_title if is_cover else page_text
            _tcfg = build_template_config(_tpl)
            _pw, _ph = effective_page_dimensions_mm(_tpl.page_width_mm, _tpl.page_height_mm)
            composed_b64 = page_composer.compose_page(
                image_base64=image_base64,
                text=_compose_text,
                template_config=_tcfg,
                page_width_mm=_pw,
                page_height_mm=_ph,
                dpi=300,
            )
        except Exception as comp_err:
            logger.warning("Regen page compose failed, using raw image", error=str(comp_err))

    # Upload composed image to GCS
    final_url = new_image_url
    if composed_b64:
        try:
            uploaded = storage_service.upload_multiple_images(
                images={page_num_int: composed_b64},
                story_id=str(preview_id),
            )
            if uploaded.get(page_num_int):
                final_url = uploaded[page_num_int]
        except Exception as up_err:
            logger.warning("Regen GCS upload failed, using raw URL", error=str(up_err))

    # ── Phase 3: persist the composed image URL ──
    existing_page_images[page_key] = final_url
    await db.execute(
        sa_update(StoryPreview)
        .where(StoryPreview.id == preview_id)
        .values(page_images=existing_page_images)
    )
    await db.commit()

    remaining = MAX_PAGE_REGENERATIONS - (current_count + 1)
    logger.info(
        "PAGE_REGENERATED",
        token=token[:10],
        page=page_key,
        remaining=remaining,
        composed=bool(_tpl and image_base64),
        uploaded_to_gcs=final_url != new_image_url,
    )

    return {
        "success": True,
        "new_image_url": final_url,
        "page_number": page_key,
        "remaining_regenerations": remaining,
    }


@router.post("/confirm/{token}")
@router.get("/confirm/{token}")
async def confirm_order(
    token: str,
    db: DbSession,
) -> dict:
    """
    Müşteri kitabı onaylıyor (tüm sayfalar üretildikten sonra gelen e-postadaki link).
    Kalan sayfa üretimi artık ödeme sonrası otomatik tetikleniyor, bu endpoint
    sadece PENDING → CONFIRMED geçişi yapar.
    """
    from datetime import datetime

    import structlog
    from sqlalchemy import select

    from app.models.story_preview import StoryPreview

    logger = structlog.get_logger()
    logger.info("CONFIRM_START", token_prefix=token[:10] if token else "None")

    result = await db.execute(select(StoryPreview).where(StoryPreview.confirmation_token == token))
    preview = result.scalar_one_or_none()

    if not preview:
        logger.warning("CONFIRM_PREVIEW_NOT_FOUND", token_prefix=token[:10])
        raise NotFoundError("Sipariş", token)

    logger.info(
        "CONFIRM_PREVIEW_FOUND",
        preview_id=str(preview.id),
        current_status=preview.status,
    )

    if preview.status == "CONFIRMED":
        logger.info("CONFIRM_ALREADY_DONE", preview_id=str(preview.id))
        return {
            "success": True,
            "message": "Bu sipariş zaten onaylanmış",
            "already_confirmed": True,
        }

    if preview.status == "EXPIRED":
        return {
            "success": False,
            "message": "Bu onay linki süresi dolmuş",
            "expired": True,
        }

    # Kitap henüz hazır değilse (PROCESSING veya QUEUE_FAILED) bilgilendir
    if preview.status in ("PROCESSING", "QUEUE_FAILED"):
        return {
            "success": False,
            "message": "Kitabınız henüz hazırlanıyor. Tamamlandığında size tekrar e-posta göndereceğiz.",
            "still_processing": True,
        }

    # Check expiration
    if preview.expires_at and preview.expires_at < datetime.now(UTC):
        preview.status = "EXPIRED"
        await db.commit()
        return {
            "success": False,
            "message": "Bu onay linki süresi dolmuş",
            "expired": True,
        }

    # Müşteri kitabı onaylıyor
    preview.status = "CONFIRMED"
    preview.confirmed_at = datetime.now(UTC)
    await db.commit()

    logger.info(
        "CONFIRM_CUSTOMER_APPROVED",
        preview_id=str(preview.id),
        child_name=preview.child_name,
    )

    return {
        "success": True,
        "message": "Kitabınızı onayladınız! Baskıya hazırlanıyor.",
        "preview_id": str(preview.id),
        "child_name": preview.child_name,
        "story_title": preview.story_title,
    }


# Request schemas
class OrderInitRequest(BaseModel):
    """Order initialization request."""

    product_id: UUID
    scenario_id: UUID
    visual_style_id: UUID
    child_name: str = Field(..., min_length=2, max_length=100)
    child_age: int = Field(..., ge=5, le=10)
    child_gender: str | None = None
    selected_outcomes: list[UUID] = Field(..., max_length=3)


class ShippingAddressRequest(BaseModel):
    """Shipping address for order."""

    full_name: str
    phone: str
    address_line1: str
    address_line2: str | None = None
    city: str
    district: str
    postal_code: str


class ApproveTextRequest(BaseModel):
    """Approve or edit story text."""

    story_text: str | None = None  # If provided, use edited text


# Response schemas
class OrderResponse(BaseModel):
    """Order response schema."""

    id: str
    status: str
    child_name: str
    child_age: int
    product_name: str
    scenario_name: str
    style_name: str
    cover_regenerate_count: int
    max_cover_regenerate: int
    story_text: str | None
    cover_url: str | None
    created_at: str

    class Config:
        from_attributes = True


class OrderInitResponse(BaseModel):
    """Order initialization response."""

    order_id: str
    status: str


@router.post("/init", response_model=OrderInitResponse, status_code=status.HTTP_201_CREATED)
async def init_order(
    request: OrderInitRequest,
    db: DbSession,
    current_user: CurrentUserOptional,
) -> OrderInitResponse:
    """
    Initialize a new order (DRAFT status).

    Can be called with or without authentication.
    """
    # Validate selected outcomes count
    if len(request.selected_outcomes) > 3:
        raise ValidationError("En fazla 3 kazanım seçebilirsiniz")

    # Create order
    order = Order(
        user_id=current_user.id if current_user else None,
        product_id=request.product_id,
        scenario_id=request.scenario_id,
        visual_style_id=request.visual_style_id,
        child_name=request.child_name,
        child_age=request.child_age,
        child_gender=request.child_gender,
        selected_outcomes=[str(o) for o in request.selected_outcomes],
        status=OrderStatus.DRAFT,
    )

    db.add(order)
    await db.commit()
    await db.refresh(order)

    return OrderInitResponse(
        order_id=str(order.id),
        status=order.status.value,
    )


@router.post("/{order_id}/upload-photo")
async def upload_photo(
    order_id: UUID,
    db: DbSession,
    current_user: CurrentUserOptional,
    photo: UploadFile = File(...),
) -> dict[str, Any]:
    """
    Upload child photo for face detection.

    Requirements:
    - Min 512x512 pixels
    - Max 10MB
    - Format: JPG, PNG
    """
    # Get order
    result = await db.execute(select(Order).where(Order.id == order_id))
    order = result.scalar_one_or_none()

    if not order:
        raise NotFoundError("Sipariş", order_id)

    # IDOR check: verify ownership — if order has an owner, caller must match
    if order.user_id and (not current_user or order.user_id != current_user.id):
        raise ForbiddenError("Bu siparişe fotoğraf yükleme yetkiniz yok")

    if order.status != OrderStatus.DRAFT:
        raise ValidationError("Fotoğraf sadece DRAFT durumunda yüklenebilir")

    # Validate file
    if not photo.content_type or not photo.content_type.startswith("image/"):
        raise ValidationError("Sadece resim dosyası yükleyebilirsiniz")

    if photo.size and photo.size > 10 * 1024 * 1024:  # 10MB
        raise ValidationError("Dosya boyutu 10MB'dan küçük olmalı")

    # TODO: Implement face detection with InsightFace
    # TODO: Upload to GCS
    # This will be implemented in ai-services task

    return {
        "message": "Fotoğraf yüklendi",
        "photo_url": "https://storage.example.com/placeholder",
        "face_score": 0.95,
    }


@router.patch("/{order_id}/approve-text", response_model=OrderResponse)
async def approve_text(
    order_id: UUID,
    request: ApproveTextRequest,
    db: DbSession,
    current_user: CurrentUserOptional,
) -> dict[str, Any]:
    """Approve story text and move to TEXT_APPROVED status."""
    result = await db.execute(select(Order).where(Order.id == order_id))
    order = result.scalar_one_or_none()

    if not order:
        raise NotFoundError("Sipariş", order_id)

    # IDOR check: verify ownership — if order has an owner, caller must match
    if order.user_id and (not current_user or order.user_id != current_user.id):
        raise ForbiddenError("Bu siparişi onaylama yetkiniz yok")

    if order.status != OrderStatus.DRAFT:
        raise ValidationError("Metin onayı sadece DRAFT durumunda yapılabilir")

    # Update text if edited
    if request.story_text:
        # TODO: Store edited text in order_pages
        pass

    # Transition state
    from app.services.order_state_machine import transition_order

    await transition_order(order, OrderStatus.TEXT_APPROVED, db)

    return {
        "id": str(order.id),
        "status": order.status.value,
        "message": "Metin onaylandı",
    }


@router.get("/{order_id}", response_model=dict)
async def get_order(
    order_id: UUID,
    db: DbSession,
    current_user: CurrentUserOptional,
) -> dict[str, Any]:
    """Get order details."""
    result = await db.execute(select(Order).where(Order.id == order_id))
    order = result.scalar_one_or_none()

    if not order:
        raise NotFoundError("Sipariş", order_id)

    # IDOR check: verify ownership — if order has an owner, caller must match
    if order.user_id and (not current_user or order.user_id != current_user.id):
        raise ForbiddenError("Bu siparişi görüntüleme yetkiniz yok")

    return {
        "id": str(order.id),
        "status": order.status.value,
        "child_name": order.child_name,
        "child_age": order.child_age,
        "cover_regenerate_count": order.cover_regenerate_count,
        "max_cover_regenerate": order.max_cover_regenerate,
        "created_at": order.created_at.isoformat(),
    }


@router.get("", response_model=list[dict])
async def list_user_orders(
    db: DbSession,
    current_user: CurrentUser,
) -> list[dict[str, Any]]:
    """List orders for current user."""
    result = await db.execute(
        select(Order).where(Order.user_id == current_user.id).order_by(Order.created_at.desc())
    )
    orders = result.scalars().all()

    return [
        {
            "id": str(o.id),
            "status": o.status.value,
            "child_name": o.child_name,
            "created_at": o.created_at.isoformat(),
        }
        for o in orders
    ]


# ============== Progress Tracking ==============


class ProgressResponse(BaseModel):
    """Order generation progress response."""

    order_id: str
    status: str
    completed_pages: int
    total_pages: int
    progress_percent: int
    estimated_remaining_seconds: int | None = None
    error: str | None = None
    is_stuck: bool = False


@router.get("/{order_id}/progress", response_model=ProgressResponse)
async def get_order_progress(
    order_id: UUID,
    db: DbSession,
    current_user: CurrentUserOptional,
) -> ProgressResponse:
    """
    Get real-time progress for order generation.

    Use this endpoint to poll for progress during long-running
    image generation tasks.
    """
    from datetime import datetime

    result = await db.execute(select(Order).where(Order.id == order_id))
    order = result.scalar_one_or_none()

    if not order:
        raise NotFoundError("Sipariş", order_id)

    if order.user_id and (not current_user or order.user_id != current_user.id):
        raise NotFoundError("Sipariş", order_id)

    # Calculate progress percentage
    total = order.total_pages or 16
    completed = order.completed_pages or 0
    progress_percent = int((completed / total) * 100) if total > 0 else 0

    # Estimate remaining time (assume ~8 seconds per page for image generation)
    remaining_pages = total - completed
    estimated_remaining = remaining_pages * 8 if remaining_pages > 0 else None

    # Check if order is stuck (processing for more than 30 minutes)
    is_stuck = False
    if order.status == OrderStatus.PROCESSING and order.generation_started_at:
        now = datetime.now(UTC)
        elapsed = (now - order.generation_started_at).total_seconds()
        if elapsed > 1800:  # 30 minutes
            is_stuck = True

    return ProgressResponse(
        order_id=str(order.id),
        status=order.status.value if hasattr(order.status, "value") else str(order.status),
        completed_pages=completed,
        total_pages=total,
        progress_percent=progress_percent,
        estimated_remaining_seconds=estimated_remaining,
        error=order.generation_error,
        is_stuck=is_stuck,
    )


# ============== Coloring Book Order ==============

class AddColoringBookRequest(BaseModel):
    """Request to add coloring book to existing order."""
    pass


class AddColoringBookResponse(BaseModel):
    """Response with coloring book order details."""
    coloring_order_id: str
    payment_url: str
    amount: float


@router.post("/{order_id}/add-coloring-book")
async def add_coloring_book_to_order(
    order_id: UUID,
    request: AddColoringBookRequest,
    db: DbSession,
    current_user: CurrentUser,
) -> AddColoringBookResponse:
    """
    Add coloring book to existing story order.
    
    Creates a new order with is_coloring_book=true and links it to the original order.
    Returns payment URL for the coloring book purchase.
    
    Requirements:
    - Original order must be READY_FOR_PRINT (completed story)
    - User must own the original order
    - Coloring book product must be active
    """
    from uuid import uuid4
    from app.models.product import Product
    
    # 1. Verify original order
    result = await db.execute(
        select(Order).where(Order.id == order_id)
    )
    original_order = result.scalar_one_or_none()
    
    if not original_order:
        raise NotFoundError("Sipariş", order_id)
    
    if original_order.user_id != current_user.id:
        raise ForbiddenError("Bu siparişe erişim izniniz yok")
    
    if original_order.status != OrderStatus.READY_FOR_PRINT:
        raise ValidationError(
            "Boyama kitabı sadece tamamlanmış hikaye siparişlerine eklenebilir"
        )
    
    if original_order.is_coloring_book:
        raise ValidationError("Bu zaten bir boyama kitabı siparişidir")
    
    # Check if coloring book already added
    if original_order.coloring_book_order_id:
        raise ValidationError("Bu siparişe zaten boyama kitabı eklenmiş")
    
    # 2. Find active coloring book product
    product_result = await db.execute(
        select(Product).where(
            Product.product_type == "coloring_book",
            Product.is_active == True
        ).limit(1)
    )
    coloring_product = product_result.scalar_one_or_none()
    
    if not coloring_product:
        raise ValidationError("Boyama kitabı ürünü şu anda aktif değil")
    
    # 3. Create coloring book order
    coloring_order_id = uuid4()
    coloring_order = Order(
        id=coloring_order_id,
        user_id=current_user.id,
        product_id=coloring_product.id,
        status=OrderStatus.PAYMENT_PENDING,
        is_coloring_book=True,
        # Copy child info from original order
        child_name=original_order.child_name,
        child_age=original_order.child_age,
        child_gender=original_order.child_gender,
        # Use original order's page count
        total_pages=original_order.total_pages,
        # Pricing
        subtotal=coloring_product.base_price,
        total_amount=coloring_product.base_price,
    )
    
    db.add(coloring_order)
    
    # 4. Link to original order
    original_order.coloring_book_order_id = coloring_order_id
    
    await db.commit()
    await db.refresh(coloring_order)
    
    _logger.info(
        "coloring_book_order_created",
        coloring_order_id=str(coloring_order_id),
        original_order_id=str(order_id),
        user_id=str(current_user.id),
        price=float(coloring_product.base_price),
    )
    
    # 5. Generate payment URL (Iyzico integration)
    from app.api.v1.payments import create_payment_checkout
    
    payment_url = await create_payment_checkout(
        order_id=coloring_order_id,
        db=db,
        current_user=current_user
    )
    
    return AddColoringBookResponse(
        coloring_order_id=str(coloring_order_id),
        payment_url=payment_url,
        amount=float(coloring_product.base_price),
    )

"""Order management endpoints."""

from __future__ import annotations

import asyncio
import re
from datetime import UTC
from typing import TYPE_CHECKING, Any
from uuid import UUID

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from app.models.user import User

import structlog
import sqlalchemy as sa
from fastapi import APIRouter, BackgroundTasks, File, HTTPException, Query, UploadFile, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import select

from app.api.v1.deps import CurrentUser, CurrentUserOptional, DbSession
from app.config import get_settings
from app.core.exceptions import ForbiddenError, NotFoundError, ValidationError
from app.core.image_dimensions import get_page_image_dimensions
from app.models.order import Order, OrderStatus
from app.prompt_engine import VisualPromptValidationError
from app.prompt_engine import personalize_style_prompt
from app.schemas.orders import (
    AddColoringBookRequest,
    AddColoringBookResponse,
    ApproveTextRequest,
    AsyncPreviewRequest,
    BillingUpdateRequest,
    OrderInitRequest,
    OrderInitResponse,
    OrderResponse,
    ProgressResponse,
    RegeneratePageRequest,
    SendPreviewRequest,
    ShippingAddressRequest,
    StoryPageData,
)
from app.services.order_helpers import (
    build_billing_summary as _build_billing_summary,
    build_invoice_summary as _build_invoice_summary,
    force_deterministic_title as _force_deterministic_title,
    load_order_pages as _load_order_pages,
    load_timeline_events as _load_timeline_events,
    snapshot_billing_to_order,
    validate_tax_id as _validate_tax_id,
)
from app.services.preview_generation_service import (
    process_preview_background_inner as _process_preview_background_inner,
    process_remaining_pages_inner as _process_remaining_pages_inner,
    ensure_v3_story_pages as _ensure_v3_story_pages,
    page_to_dict as _page_to_dict,
    page_version_flags as _page_version_flags,
)

_logger = structlog.get_logger()
settings = get_settings()
router = APIRouter()
_V3_BLOCK_MSG = "V2_LABEL_BLOCKED: expected v3"


def _verify_order_ownership(order: Order, current_user: User | None) -> None:
    """Consistent object-level authorization for orders.

    Rules:
    - If order has a user_id, caller must be that user.
    - If order has no user_id (anonymous), only unauthenticated callers
      within the same session flow can access it (token-based endpoints).
      Authenticated users cannot claim unowned orders.
    Raises ForbiddenError on mismatch (never reveals order existence via 404).
    """
    if order.user_id is not None:
        if current_user is None or order.user_id != current_user.id:
            raise ForbiddenError("Bu siparişe erişim yetkiniz yok")
    else:
        if current_user is not None:
            raise ForbiddenError("Bu siparişe erişim yetkiniz yok")

# ---------------------------------------------------------------------------
# Concurrency guard (BackgroundTasks fallback): max 2 parallel generations
# per process when Redis/Arq is unavailable.  Arq worker handles global
# queue ordering; this semaphore only limits the in-process fallback path.
# ---------------------------------------------------------------------------
_IMAGE_GEN_SEMAPHORE = asyncio.Semaphore(settings.order_concurrency_slots)

# List routes: must be registered before GET /{order_id} so /my-trials is not matched as order_id
_ACTIVE_STATUSES = {
    OrderStatus.PAID, OrderStatus.PROCESSING, OrderStatus.READY_FOR_PRINT, OrderStatus.SHIPPED,
}
_DELIVERED_STATUSES = {OrderStatus.DELIVERED}
_CANCELLED_STATUSES = {OrderStatus.CANCELLED, OrderStatus.REFUNDED}
_LIST_COLUMNS = [
    Order.id,
    Order.status,
    Order.child_name,
    Order.created_at,
    Order.payment_amount,
    Order.tracking_number,
    Order.carrier,
    Order.has_audio_book,
    Order.total_pages,
    Order.completed_pages,
]


@router.get("", response_model=dict)
async def list_user_orders(
    db: DbSession,
    current_user: CurrentUser,
    status_filter: str | None = None,
    search: str | None = None,
    page: int = 1,
    per_page: int = 20,
) -> dict[str, Any]:
    """List orders for current user with filtering, search, and pagination."""
    from sqlalchemy import func as sa_func

    base_where = Order.user_id == current_user.id
    filters = [base_where]
    if status_filter == "active":
        filters.append(Order.status.in_([s.value for s in _ACTIVE_STATUSES]))
    elif status_filter == "delivered":
        filters.append(Order.status.in_([s.value for s in _DELIVERED_STATUSES]))
    elif status_filter == "cancelled":
        filters.append(Order.status.in_([s.value for s in _CANCELLED_STATUSES]))
    if search:
        search_clean = search.strip()
        if search_clean:
            search_term = f"%{search_clean}%"
            filters.append(
                Order.child_name.ilike(search_term)
                | sa.cast(Order.id, sa.Text).ilike(search_term)
            )
    where_clause = sa.and_(*filters)
    count_result = await db.execute(
        select(sa_func.count(Order.id)).where(where_clause)
    )
    total = count_result.scalar() or 0
    page = max(1, page)
    per_page = min(max(1, per_page), 50)
    offset = (page - 1) * per_page
    result = await db.execute(
        select(*_LIST_COLUMNS)
        .where(where_clause)
        .order_by(Order.created_at.desc())
        .offset(offset)
        .limit(per_page)
    )
    rows = result.all()
    items = [
        {
            "id": str(r.id),
            "status": r.status.value if hasattr(r.status, "value") else str(r.status),
            "child_name": r.child_name,
            "created_at": r.created_at.isoformat(),
            "payment_amount": float(r.payment_amount) if r.payment_amount else None,
            "tracking_number": r.tracking_number,
            "carrier": r.carrier,
            "has_audio_book": r.has_audio_book,
            "total_pages": r.total_pages or 0,
            "completed_pages": r.completed_pages or 0,
        }
        for r in rows
    ]
    return {
        "items": items,
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": (total + per_page - 1) // per_page if total > 0 else 0,
    }




# ============== Send Preview (Test Mode) ==============










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

    from app.services.trial_generation_service import resolve_visual_style_from_db as _resolve_visual_style_from_db
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






# Response schemas




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

    _verify_order_ownership(order, current_user)

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

    _verify_order_ownership(order, current_user)

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


_STATUS_DESCRIPTIONS: dict[str, tuple[str, str | None]] = {
    "DRAFT": ("Taslak oluşturuldu", "Hikayenizi kişiselleştirmeye başlayabilirsiniz."),
    "TEXT_APPROVED": ("Hikaye metni onaylandı", "Kapak görseli seçimine geçebilirsiniz."),
    "COVER_APPROVED": ("Kapak görseli onaylandı", "Ödeme adımına geçebilirsiniz."),
    "PAYMENT_PENDING": ("Ödeme bekleniyor", "Ödemenizi tamamladığınızda üretim başlayacak."),
    "PAID": ("Ödeme alındı, üretim başlıyor", "Kitabınız kısa süre içinde üretilmeye başlanacak."),
    "PROCESSING": ("Kitabınız yapay zeka ile üretiliyor", "Tahmini süre: 3-5 dakika"),
    "READY_FOR_PRINT": ("Baskıya hazır", "Kısa süre içinde kargoya verilecek"),
    "SHIPPED": ("Kargoya verildi", "Tahmini teslimat: 2-4 iş günü"),
    "DELIVERED": ("Teslim edildi", "Keyifli okumalar!"),
    "CANCELLED": ("İptal edildi", "Sorularınız için destek ekibimize ulaşabilirsiniz."),
    "REFUNDED": ("İade edildi", "Tutar ödeme yönteminize iade edilecektir."),
}

@router.get("/{order_id}", response_model=dict)
async def get_order(
    order_id: UUID,
    db: DbSession,
    current_user: CurrentUserOptional,
    include: str | None = None,
) -> dict[str, Any]:
    """Get order details. Pages and timeline are lazy-loaded via `include` param.

    Query params:
        include: comma-separated list of optional sections.
                 Supported: "pages", "timeline". Default: none (core data only).
                 Example: ?include=pages,timeline
    """
    result = await db.execute(select(Order).where(Order.id == order_id))
    order = result.scalar_one_or_none()

    if not order:
        raise NotFoundError("Sipariş", order_id)

    _verify_order_ownership(order, current_user)

    includes = {s.strip().lower() for s in (include or "").split(",") if s.strip()}

    status_val = order.status.value if hasattr(order.status, "value") else str(order.status)
    desc, hint = _STATUS_DESCRIPTIONS.get(status_val, ("", None))

    data: dict[str, Any] = {
        "id": str(order.id),
        "status": status_val,
        "status_description": desc,
        "status_hint": hint,
        "child_name": order.child_name,
        "child_age": order.child_age,
        "child_gender": order.child_gender,
        "created_at": order.created_at.isoformat(),
        "updated_at": order.updated_at.isoformat() if order.updated_at else None,
        "payment_amount": float(order.payment_amount) if order.payment_amount else None,
        "payment_status": order.payment_status,
        "shipping_address": order.shipping_address,
        "tracking_number": order.tracking_number,
        "carrier": order.carrier,
        "final_pdf_url": order.final_pdf_url,
        "has_audio_book": order.has_audio_book,
        "audio_type": order.audio_type,
        "audio_file_url": order.audio_file_url,
        "qr_code_url": order.qr_code_url,
        "total_pages": order.total_pages or 0,
        "completed_pages": order.completed_pages or 0,
        "cover_regenerate_count": order.cover_regenerate_count,
        "max_cover_regenerate": order.max_cover_regenerate,
        "delivered_at": order.delivered_at.isoformat() if order.delivered_at else None,
        "is_guest_order": order.user_id is None,
        "billing": _build_billing_summary(order),
        "invoice": await _build_invoice_summary(order.id, db),
    }

    if "pages" in includes:
        data["pages"] = await _load_order_pages(order.id, db)

    if "timeline" in includes:
        data["timeline_events"] = await _load_timeline_events(order, db)

    return data






# ============== Progress Tracking ==============




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

    _verify_order_ownership(order, current_user)

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

    _verify_order_ownership(original_order, current_user)
    
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
    
    return AddColoringBookResponse(
        coloring_order_id=str(coloring_order_id),
        payment_url="",  # Client calls POST /payments/checkout with this order_id
        amount=float(coloring_product.base_price),
    )


# ─── Billing / Invoice ──────────────────────────────────────────────

_BILLING_EDITABLE_STATUSES = {
    OrderStatus.DRAFT,
    OrderStatus.TEXT_APPROVED,
    OrderStatus.COVER_APPROVED,
    OrderStatus.PAYMENT_PENDING,
}






@router.patch("/{order_id}/billing")
async def update_billing(
    order_id: UUID,
    body: BillingUpdateRequest,
    db: DbSession,
    current_user: CurrentUser,
) -> dict[str, Any]:
    """Update billing info. Locked after PAID."""
    from app.models.audit_log import AuditLog

    result = await db.execute(select(Order).where(Order.id == order_id))
    order = result.scalar_one_or_none()
    if not order:
        raise NotFoundError("Sipariş", order_id)

    _verify_order_ownership(order, current_user)

    current_status = order.status if isinstance(order.status, OrderStatus) else OrderStatus(order.status)
    if current_status not in _BILLING_EDITABLE_STATUSES:
        raise ForbiddenError(
            "Ödeme tamamlandıktan sonra fatura bilgileri değiştirilemez. "
            "Değişiklik için destek ekibiyle iletişime geçin."
        )

    if body.billing_type == "corporate":
        if not body.billing_company_name or not body.billing_company_name.strip():
            raise ValidationError("Kurumsal fatura için şirket ünvanı zorunludur.")
        if not body.billing_tax_id or not body.billing_tax_id.strip():
            raise ValidationError("Kurumsal fatura için vergi numarası zorunludur.")
        if not _validate_tax_id(body.billing_tax_id):
            raise ValidationError("Vergi numarası 10 (VKN) veya 11 (TCKN) haneli olmalıdır.")
    else:
        if not body.billing_full_name or not body.billing_full_name.strip():
            raise ValidationError("Bireysel fatura için ad soyad zorunludur.")

    old_billing = {
        "billing_type": order.billing_type,
        "billing_full_name": order.billing_full_name,
        "billing_company_name": order.billing_company_name,
        "billing_tax_id": order.billing_tax_id,
        "billing_tax_office": order.billing_tax_office,
    }

    order.billing_type = body.billing_type
    order.billing_full_name = body.billing_full_name
    order.billing_email = body.billing_email
    order.billing_phone = body.billing_phone
    order.billing_company_name = body.billing_company_name if body.billing_type == "corporate" else None
    order.billing_tax_id = body.billing_tax_id if body.billing_type == "corporate" else None
    order.billing_tax_office = body.billing_tax_office if body.billing_type == "corporate" else None

    if body.use_shipping_address:
        order.billing_address = order.shipping_address
    elif body.billing_address:
        order.billing_address = body.billing_address

    db.add(AuditLog(
        action="BILLING_INFO_UPDATED",
        user_id=current_user.id,
        order_id=order.id,
        details={"old": old_billing, "new": {
            "billing_type": order.billing_type,
            "billing_full_name": order.billing_full_name,
            "billing_company_name": order.billing_company_name,
            "billing_tax_id": order.billing_tax_id,
            "billing_tax_office": order.billing_tax_office,
        }},
    ))

    await db.commit()

    return {"ok": True, "billing": _build_billing_summary(order)}








@router.get("/{order_id}/invoice/download")
async def download_invoice(
    order_id: UUID,
    db: DbSession,
    current_user: CurrentUser,
) -> Any:
    """Download invoice PDF for an order. Auth + owner check required."""
    from io import BytesIO

    from fastapi.responses import StreamingResponse

    from app.models.invoice import Invoice, InvoiceStatus
    from app.services.storage_service import storage_service

    result = await db.execute(select(Order).where(Order.id == order_id))
    order = result.scalar_one_or_none()
    if not order:
        raise NotFoundError("Sipariş", order_id)

    _verify_order_ownership(order, current_user)

    inv_result = await db.execute(select(Invoice).where(Invoice.order_id == order_id))
    invoice = inv_result.scalar_one_or_none()
    if not invoice or invoice.invoice_status != InvoiceStatus.PDF_READY.value:
        raise NotFoundError("Fatura PDF", order_id)

    pdf_bytes = storage_service.download_bytes(invoice.pdf_url)
    if not pdf_bytes:
        raise HTTPException(status_code=502, detail="Fatura PDF dosyası indirilemedi")

    filename = f"fatura_{invoice.invoice_number}.pdf"
    return StreamingResponse(
        BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )

"""Admin order management endpoints."""

from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any
from uuid import UUID

import structlog
from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import String, func, select

from app.api.v1.deps import AdminUser, DbSession
from app.core.exceptions import NotFoundError
from app.models.order import Order, OrderStatus

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession
from app.models.story_preview import StoryPreview
from app.services.preview_display_service import (
    build_prompts_by_page as _build_prompts_by_page,
)
from app.services.preview_display_service import (
    detect_pipeline_version as _detect_pipeline_version,
)
from app.services.preview_display_service import (
    enrich_manifest_with_prompts as _enrich_manifest_with_prompts,
)
from app.services.preview_display_service import (
    extract_pdf_url as _extract_pdf_url,
)
from app.services.preview_display_service import (
    page_images_for_preview as _page_images_for_preview,
)
from app.services.preview_display_service import (
    page_images_with_cache_bust as _page_images_with_cache_bust,
)
from app.services.preview_display_service import (
    story_pages_for_display as _story_pages_for_display,
)

router = APIRouter()
logger = structlog.get_logger()


def _compute_actual_total(preview: "StoryPreview") -> float | None:
    """Compute actual total from base product price + addon prices.

    StoryPreview.product_price stores only the base book price.
    Audio addon and coloring book prices are added on top during payment
    but never written back, so we recompute them here for display.
    """
    base = float(preview.product_price) if preview.product_price else None
    if base is None:
        return None
    total = base
    if getattr(preview, "has_audio_book", False):
        audio_type = getattr(preview, "audio_type", "system") or "system"
        total += 300.0 if audio_type == "cloned" else 150.0
    if getattr(preview, "has_coloring_book", False):
        total += 150.0
    return total



# =============================================================================
# Helper functions for billing and invoices
# =============================================================================

async def _check_has_invoice(order_id: UUID, db: "AsyncSession") -> bool:
    """Lightweight check: does this order have an invoice row?"""
    from app.models.invoice import Invoice

    result = await db.execute(
        select(func.count()).where(Invoice.order_id == order_id)
    )
    return (result.scalar() or 0) > 0


async def _build_admin_invoice_summary(
    order_id: UUID, db: "AsyncSession",
) -> dict[str, Any] | None:
    from sqlalchemy import or_

    from app.models.invoice import Invoice

    result = await db.execute(
        select(Invoice).where(
            or_(Invoice.order_id == order_id, Invoice.story_preview_id == order_id)
        )
    )
    inv = result.scalar_one_or_none()
    if not inv:
        return None
    return {
        "invoice_number": inv.invoice_number,
        "invoice_status": inv.invoice_status,
        "pdf_ready": inv.pdf_url is not None,
        "pdf_version": inv.pdf_version,
        "issued_at": inv.issued_at.isoformat() if inv.issued_at else None,
        "last_error": inv.last_error,
        "retry_count": inv.retry_count,
        "needs_credit_note": inv.needs_credit_note,
        "email_sent": inv.email_sent_at is not None,
        "email_status": inv.email_status or "NOT_SENT",
        "email_sent_at": inv.email_sent_at.isoformat() if inv.email_sent_at else None,
        "email_error": inv.email_error,
        "email_retry_count": inv.email_retry_count,
        "email_resent_count": inv.email_resent_count,
        "email_last_resent_at": inv.email_last_resent_at.isoformat() if inv.email_last_resent_at else None,
    }


async def _build_billing_summary(
    order_id: UUID,
    db: "AsyncSession",
    preview: "StoryPreview | None" = None,
) -> dict[str, Any] | None:
    # 1) Try Order table first (legacy checkout flow)
    result = await db.execute(select(Order).where(Order.id == order_id))
    order = result.scalar_one_or_none()
    if order and order.billing_type:
        return {
            "billing_type": order.billing_type,
            "billing_tc_no": getattr(order, "billing_tc_no", None),
            "billing_full_name": order.billing_full_name,
            "billing_email": order.billing_email,
            "billing_phone": order.billing_phone,
            "billing_company_name": order.billing_company_name,
            "billing_tax_id": order.billing_tax_id,
            "billing_tax_office": order.billing_tax_office,
            "billing_address": order.billing_address,
        }

    # 2) Try StoryPreview.billing_data (trial/create-v2 flow)
    bd = getattr(preview, "billing_data", None) if preview else None
    if not bd and not preview:
        from app.models.story_preview import StoryPreview as SP
        sp_result = await db.execute(select(SP).where(SP.id == order_id))
        sp = sp_result.scalar_one_or_none()
        bd = getattr(sp, "billing_data", None) if sp else None

    if bd and isinstance(bd, dict) and bd.get("billing_type"):
        return {
            "billing_type": bd.get("billing_type"),
            "billing_tc_no": bd.get("billing_tc_no"),
            "billing_full_name": bd.get("billing_full_name"),
            "billing_email": bd.get("billing_email"),
            "billing_phone": bd.get("billing_phone"),
            "billing_company_name": bd.get("billing_company_name"),
            "billing_tax_id": bd.get("billing_tax_id"),
            "billing_tax_office": bd.get("billing_tax_office"),
            "billing_address": bd.get("billing_address"),
        }

    # 3) Fallback: auto-fill from preview parent info
    if preview:
        name = getattr(preview, "parent_name", None)
        email = getattr(preview, "parent_email", None)
        if name or email:
            return {
                "billing_type": "individual",
                "billing_full_name": name,
                "billing_email": email,
                "billing_phone": getattr(preview, "parent_phone", None),
                "billing_company_name": None,
                "billing_tax_id": None,
                "billing_tax_office": None,
                "billing_address": None,
            }

    return None

# =============================================================================
# STORY PREVIEWS (Pending/Confirmed Orders from Email)
# =============================================================================

@router.get("/previews")
async def list_story_previews(
    db: DbSession,
    admin: AdminUser,
    status: str | None = Query(None, description="Filter by status"),
    limit: int = Query(30, ge=1, le=100),
    offset: int = Query(0, ge=0),
    search: str | None = Query(None, description="Search by name, email, child name, or order ID prefix"),
    date_from: str | None = Query(None, description="ISO date lower bound (inclusive)"),
    date_to: str | None = Query(None, description="ISO date upper bound (inclusive)"),
) -> dict:
    """List story previews — slim payload (no page_images)."""
    base = select(StoryPreview)

    if status:
        base = base.where(StoryPreview.status == status)

    if search:
        like = f"%{search}%"
        base = base.where(
            StoryPreview.parent_name.ilike(like)
            | StoryPreview.parent_email.ilike(like)
            | StoryPreview.child_name.ilike(like)
            | StoryPreview.parent_phone.ilike(like)
            | func.cast(StoryPreview.id, String).ilike(f"{search}%")
        )

    if date_from:
        try:
            dt_from = datetime.fromisoformat(date_from)
            base = base.where(StoryPreview.created_at >= dt_from)
        except ValueError:
            pass

    if date_to:
        try:
            dt_to = datetime.fromisoformat(date_to)
            dt_to = dt_to.replace(hour=23, minute=59, second=59)
            base = base.where(StoryPreview.created_at <= dt_to)
        except ValueError:
            pass

    count_result = await db.execute(select(func.count()).select_from(base.subquery()))
    total = count_result.scalar() or 0

    query = base.order_by(StoryPreview.created_at.desc()).limit(limit).offset(offset)
    result = await db.execute(query)
    previews = result.scalars().all()

    items = []
    for p in previews:
        raw_images = _page_images_for_preview(p)
        cover_thumb = None
        if raw_images:
            cover_thumb = raw_images.get("0") or raw_images.get("page_0")
        image_count = len(raw_images) if raw_images else 0

        has_pdf = bool(_extract_pdf_url(p))
        has_invoice = await _check_has_invoice(p.id, db)

        items.append({
            "id": str(p.id),
            "status": p.status,
            "parent_name": p.parent_name,
            "parent_email": p.parent_email,
            "parent_phone": p.parent_phone,
            "child_name": p.child_name,
            "child_age": p.child_age,
            "child_gender": p.child_gender,
            "story_title": p.story_title,
            "product_name": p.product_name,
            "product_price": _compute_actual_total(p),
            "scenario_name": p.scenario_name,
            "visual_style_name": p.visual_style_name,
            "page_count": len(p.story_pages) if p.story_pages else 0,
            "cover_thumb": cover_thumb,
            "image_count": image_count,
            "has_pdf": has_pdf,
            "has_invoice": has_invoice,
            "has_audio_book": getattr(p, "has_audio_book", False),
            "has_coloring_book": getattr(p, "has_coloring_book", False),
            "confirmed_at": p.confirmed_at.isoformat() if p.confirmed_at else None,
            "created_at": p.created_at.isoformat() if p.created_at else None,
            "admin_notes": p.admin_notes,
        })

    return {"items": items, "total": total, "limit": limit, "offset": offset}


@router.get("/previews/{preview_id}")
async def get_preview_detail(
    preview_id: UUID,
    db: DbSession,
    admin: AdminUser,
) -> dict:
    """Get full details of a story preview including all pages."""
    result = await db.execute(select(StoryPreview).where(StoryPreview.id == preview_id))
    preview = result.scalar_one_or_none()

    if not preview:
        raise NotFoundError("Önizleme", preview_id)

    _pipeline_version = _detect_pipeline_version(preview)

    return {
        "id": str(preview.id),
        "status": preview.status,
        "confirmation_token": preview.confirmation_token,
        # Parent info
        "parent_name": preview.parent_name,
        "parent_email": preview.parent_email,
        "parent_phone": preview.parent_phone,
        # Child info
        "child_name": preview.child_name,
        "child_age": preview.child_age,
        "child_gender": preview.child_gender,
        # Product
        "product_id": str(preview.product_id) if preview.product_id else None,
        "product_name": preview.product_name,
        "product_price": _compute_actual_total(preview),
        # Story
        "story_title": preview.story_title,
        "story_pages": _story_pages_for_display(preview),
        "page_images": _page_images_with_cache_bust(preview),
        "dedication_note": getattr(preview, "dedication_note", None),
        # Options
        "scenario_name": preview.scenario_name,
        "visual_style_name": preview.visual_style_name,
        # Audio book
        "has_audio_book": preview.has_audio_book if hasattr(preview, "has_audio_book") else False,
        "audio_type": preview.audio_type if hasattr(preview, "audio_type") else None,
        "audio_voice_id": preview.audio_voice_id if hasattr(preview, "audio_voice_id") else None,
        "voice_sample_url": preview.voice_sample_url
        if hasattr(preview, "voice_sample_url")
        else None,
        # Timestamps
        "confirmed_at": preview.confirmed_at.isoformat() if preview.confirmed_at else None,
        "expires_at": preview.expires_at.isoformat() if preview.expires_at else None,
        "created_at": preview.created_at.isoformat() if preview.created_at else None,
        "updated_at": preview.updated_at.isoformat() if preview.updated_at else None,
        # Admin
        "admin_notes": preview.admin_notes,
        "generation_manifest_json": _enrich_manifest_with_prompts(preview),
        "prompt_debug_json": getattr(preview, "prompt_debug_json", None),
        "prompts_by_page": _build_prompts_by_page(preview),
        # Pipeline version detection (V3 = story generated with blueprint pipeline)
        "pipeline_version": _pipeline_version,
        "pipeline_label": _pipeline_version,
        # PDF URL — from manifest or admin_notes fallback
        "pdf_url": _extract_pdf_url(preview),
        # Coloring book
        "has_coloring_book": getattr(preview, "has_coloring_book", False),
        "coloring_pdf_url": getattr(preview, "coloring_pdf_url", None),
        # Cover images
        "back_cover_image_url": getattr(preview, "back_cover_image_url", None),
        # Page count
        "page_count": len(preview.story_pages) if preview.story_pages else 0,
        # Invoice (preview.id == order.id)
        "invoice": await _build_admin_invoice_summary(preview.id, db),
        # Billing (from linked order or trial billing_data)
        "billing": await _build_billing_summary(preview.id, db, preview=preview),
    }


@router.patch("/previews/{preview_id}/notes")
async def update_preview_notes(
    preview_id: UUID,
    notes: str,
    db: DbSession,
    admin: AdminUser,
) -> dict:
    """Update admin notes for a preview."""
    result = await db.execute(select(StoryPreview).where(StoryPreview.id == preview_id))
    preview = result.scalar_one_or_none()

    if not preview:
        raise NotFoundError("Önizleme", preview_id)

    preview.admin_notes = notes
    await db.commit()

    return {"success": True, "message": "Notlar güncellendi"}


@router.patch("/previews/{preview_id}/status")
async def update_preview_status(
    preview_id: UUID,
    status: str,
    db: DbSession,
    admin: AdminUser,
) -> dict:
    """Update status of a preview (admin can manually confirm/cancel)."""

    result = await db.execute(select(StoryPreview).where(StoryPreview.id == preview_id))
    preview = result.scalar_one_or_none()

    if not preview:
        raise NotFoundError("Önizleme", preview_id)

    if status not in ["PENDING", "CONFIRMED", "EXPIRED", "CANCELLED"]:
        from app.core.exceptions import ValidationError

        raise ValidationError("Geçersiz durum")

    preview.status = status
    if status == "CONFIRMED" and not preview.confirmed_at:
        preview.confirmed_at = datetime.now(UTC)

    await db.commit()

    return {"success": True, "message": f"Durum {status} olarak güncellendi"}


@router.post("/previews/{preview_id}/generate-remaining")
async def generate_remaining_pages(
    preview_id: UUID,
    db: DbSession,
    admin: AdminUser,
) -> dict:
    """
    Trigger background generation of missing page images for a preview.

    Accepts previews in CONFIRMED, QUEUE_FAILED, or FAILED status.
    Uses only Arq (reliable Redis queue); does NOT use BackgroundTasks
    which are unreliable on Cloud Run.
    """
    import structlog

    _logger = structlog.get_logger()

    result = await db.execute(select(StoryPreview).where(StoryPreview.id == preview_id))
    preview = result.scalar_one_or_none()
    if not preview:
        raise NotFoundError("Önizleme", preview_id)

    # Allow retry from CONFIRMED, PENDING, QUEUE_FAILED, FAILED, PREVIEW_GENERATED, COMPLETING statuses
    allowed_statuses = {"CONFIRMED", "PENDING", "QUEUE_FAILED", "FAILED", "PREVIEW_GENERATED", "COMPLETING"}
    if preview.status not in allowed_statuses:
        from app.core.exceptions import ValidationError

        raise ValidationError(
            f"Bu durumdaki sipariş için kalan sayfalar üretilemez: {preview.status}. "
            f"İzin verilen durumlar: {', '.join(sorted(allowed_statuses))}"
        )

    num_pages = len(preview.story_pages) if preview.story_pages else 0
    page_images = preview.page_images or {}
    numeric_keys = [k for k in page_images if k.isdigit()]
    num_images = len(numeric_keys)
    _email_sent = "TRIAL_APPROVAL_EMAIL_SENT" in (preview.admin_notes or "")

    if num_images >= num_pages and _email_sent:
        return {"success": True, "message": "Tüm sayfaların görseli zaten mevcut ve email gönderildi", "missing": 0}

    missing = max(0, num_pages - num_images)

    # Reset status to PROCESSING so worker can process it
    if preview.status in ("QUEUE_FAILED", "FAILED", "PREVIEW_GENERATED", "COMPLETING"):
        preview.status = "PROCESSING"

    # If all images exist but email was not sent, keep PENDING status so worker sends email
    if num_images >= num_pages and not _email_sent and preview.status == "PENDING":
        pass  # Keep PENDING; worker will detect _is_full_retry and only send email/PDF

    preview.admin_notes = (
        (preview.admin_notes or "")
        + f"\n\nAdmin tarafindan yeniden tetiklendi ({admin.email})"
    )
    await db.commit()

    try:
        from app.workers.enqueue import enqueue_remaining_pages

        _job = await enqueue_remaining_pages(str(preview.id))
        if not _job:
            raise RuntimeError("Arq enqueue returned None — Redis baglantisi kontrol edilmeli")
    except Exception as _enq_err:
        _logger.critical(
            "ADMIN_REMAINING_ENQUEUE_FAILED",
            preview_id=str(preview_id),
            error=str(_enq_err),
        )
        # Mark as QUEUE_FAILED so it's visible
        preview.status = "QUEUE_FAILED"
        preview.admin_notes = (
            (preview.admin_notes or "")
            + f"\n\nArq kuyrugu basarisiz: {str(_enq_err)[:300]}"
        )
        await db.commit()
        raise HTTPException(
            status_code=503,
            detail=f"Arq kuyruguna eklenemedi: {str(_enq_err)[:200]}. "
            f"Redis baglantisini kontrol edin.",
        )

    return {
        "success": True,
        "message": f"{missing} eksik sayfa görseli Arq kuyruğuna eklendi, arka planda üretilecek.",
        "missing": missing,
    }


@router.post("/previews/{preview_id}/generate-book")
async def generate_book_from_preview(
    preview_id: UUID,
    db: DbSession,
    admin: AdminUser,
) -> dict:
    """
    Generate a complete book from a confirmed StoryPreview.

    This creates the audiobook (if selected), back cover, intro page, 
    and final PDF in a single orchestrated flow.
    """
    from app.services.book_generation_service import BookGenerationService

    # Get preview
    result = await db.execute(select(StoryPreview).where(StoryPreview.id == preview_id))
    preview = result.scalar_one_or_none()

    if not preview:
        raise NotFoundError("Önizleme", preview_id)

    if preview.status != "CONFIRMED":
        from app.core.exceptions import ValidationError

        raise ValidationError("Sadece onaylanmış siparişler için kitap oluşturulabilir")

    logger.info(
        "Generating book from preview via BookGenerationService",
        preview_id=str(preview_id),
        has_audio=getattr(preview, "has_audio_book", False),
    )

    # Orchestrate everything inside the new service
    service = BookGenerationService(db)
    gen_result = await service.generate_full_book(preview)

    # Update preview with generated URLs
    notes_update = ""
    audio_file_url = gen_result.get("audio_file_url")
    pdf_url = gen_result.get("pdf_url")

    if audio_file_url:
        preview.audio_file_url = audio_file_url  # Save audio URL to preview
        notes_update += f"\n\nAudio URL: {audio_file_url}"
    if pdf_url:
        notes_update += f"\n\nPDF URL: {pdf_url}"
        # Save PDF URL to generation_manifest_json so download-pdf endpoint can find it
        manifest = preview.generation_manifest_json or {}
        manifest["final_pdf_url"] = pdf_url
        preview.generation_manifest_json = manifest

    if notes_update or audio_file_url:
        if notes_update:
            preview.admin_notes = (preview.admin_notes or "") + notes_update
        await db.commit()

    return {
        "success": True,
        "preview_id": str(preview.id),
        "has_audio": gen_result.get("has_audio", False),
        "audio_url": audio_file_url,
        "audio_qr_url": gen_result.get("audio_qr_url"),
        "pdf_url": pdf_url,
        "pdf_error": gen_result.get("pdf_error"),
        "message": "Kitap oluşturma tamamlandı" + (" (ses dahil)" if audio_file_url else ""),
    }


@router.post("/previews/{preview_id}/generate-pdf-task")
async def generate_admin_pdf_bg(
    preview_id: UUID,
    db: DbSession,
    admin: AdminUser,
) -> dict:
    """
    Kilitlenmeyi önlemek için PDF üretimini asenkron (Arq) worker'a gönderir.
    Admin paneli bu endpoint'i çağırır ve hemen yanıt alır.
    """
    import structlog

    from app.workers.enqueue import enqueue_job

    logger = structlog.get_logger()
    logger.info("Enqueuing admin PDF generation task", preview_id=str(preview_id))

    try:
        await enqueue_job(
            "generate_admin_pdf_task",
            str(preview_id),
        )
        return {"success": True, "message": "PDF oluşturma işlemi arka planda başlatıldı."}
    except Exception as e:
        logger.error("Failed to enqueue PDF task", error=str(e), preview_id=str(preview_id))
        raise HTTPException(status_code=500, detail=f"İşlem kuyruğa eklenemedi: {e}")


@router.post("/previews/{preview_id}/generate-coloring-book")
async def trigger_coloring_book_generation(
    preview_id: UUID,
    db: DbSession,
    admin: AdminUser,
) -> dict:
    """
    Trigger coloring book PDF generation for a StoryPreview via Arq worker.
    Used to retry failed coloring book generation from admin panel.
    """
    import structlog

    from app.workers.enqueue import enqueue_job

    logger = structlog.get_logger()

    # Verify trial exists and has coloring book flag
    result = await db.execute(select(StoryPreview).where(StoryPreview.id == preview_id))
    preview = result.scalar_one_or_none()

    if not preview:
        raise HTTPException(status_code=404, detail="Önizleme bulunamadı")

    if not getattr(preview, "has_coloring_book", False):
        raise HTTPException(status_code=400, detail="Bu siparişte boyama kitabı yok")

    # Check if already generated
    if getattr(preview, "coloring_pdf_url", None):
        return {
            "success": True,
            "message": "Boyama kitabı zaten oluşturulmuş.",
            "coloring_pdf_url": preview.coloring_pdf_url,
        }

    logger.info("Enqueuing coloring book generation", preview_id=str(preview_id))

    try:
        await enqueue_job(
            "generate_coloring_book_for_trial",
            trial_id=str(preview_id),
        )
        return {"success": True, "message": "Boyama kitabı oluşturma işlemi arka planda başlatıldı."}
    except Exception as e:
        logger.error("Failed to enqueue coloring book task", error=str(e), preview_id=str(preview_id))
        raise HTTPException(status_code=500, detail=f"İşlem kuyruğa eklenemedi: {e}")



@router.get("/previews/{preview_id}/download-pdf")
async def download_preview_pdf(
    preview_id: UUID,
    db: DbSession,
    admin: AdminUser,
) -> dict:
    """
    Mevcut PDF varsa döndürür, yoksa yeni bir görev başlatılmasını ister.
    """
    result = await db.execute(select(StoryPreview).where(StoryPreview.id == preview_id))
    preview = result.scalar_one_or_none()
    
    if preview:
        # 1. generation_manifest_json["final_pdf_url"] (en güvenilir)
        manifest = preview.generation_manifest_json or {}
        if isinstance(manifest, dict) and manifest.get("final_pdf_url"):
            return {"pdf_url": manifest["final_pdf_url"], "size_mb": "?", "status": "ready"}

        # 2. admin_notes içinde "PDF URL: ..." satırı (eski format fallback)
        notes = preview.admin_notes or ""
        for line in notes.splitlines():
            line = line.strip()
            if line.startswith("PDF URL:"):
                url = line[len("PDF URL:"):].strip()
                if url:
                    return {"pdf_url": url, "size_mb": "?", "status": "ready"}

    # 3. Order tablosunda final_pdf_url
    result = await db.execute(select(Order).where(Order.id == preview_id))
    order = result.scalar_one_or_none()
    if order and order.final_pdf_url:
        return {"pdf_url": order.final_pdf_url, "size_mb": "?", "status": "ready"}

    raise HTTPException(status_code=404, detail="PDF henüz oluşturulmamış. Lütfen önce 'Kitap Üret' butonuna basın.")


@router.get("/previews/{preview_id}/composed-images")
async def get_composed_images(
    preview_id: UUID,
    db: DbSession,
    admin: AdminUser,
    force_recompose: bool = False,
) -> dict:
    """
    Get composed images for a preview.
    Composes raw images with text using the SAME template as orders (en son güncellenen şablon).
    force_recompose=true ise cached URL'leri atlar ve güncel template ile yeniden compose eder.
    """
    import structlog

    from app.models.book_template import PageTemplate
    from app.services.page_composer import (
        PageComposer,
        build_template_config,
        effective_page_dimensions_mm,
    )

    logger = structlog.get_logger()

    result = await db.execute(select(StoryPreview).where(StoryPreview.id == preview_id))
    preview = result.scalar_one_or_none()
    if not preview:
        raise NotFoundError("Önizleme", preview_id)

    # Şablon: önizlemenin ürünü atanmışsa ürünün şablonu (font boyutu vb.), yoksa en son güncellenen
    from sqlalchemy.orm import selectinload

    from app.models.product import Product

    inner_template = None
    cover_template = None
    if getattr(preview, "product_id", None):
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

    # Varsayılan boyut (şablon yoksa)
    page_width_mm = 297.0
    page_height_mm = 210.0
    bleed_mm = 3.0
    if inner_template:
        page_width_mm, page_height_mm = effective_page_dimensions_mm(
            inner_template.page_width_mm, inner_template.page_height_mm
        )
        bleed_mm = inner_template.bleed_mm

    page_composer = PageComposer()
    raw_pages = preview.story_pages or []
    page_images = _page_images_for_preview(preview) or {}
    composed_images = {}

    _story_title = getattr(preview, "story_title", "") or ""
    for i, page in enumerate(raw_pages):
        if not isinstance(page, dict):
            continue
        page_num = page.get("page_number", i)
        page_key = str(page_num)
        image_base64 = page.get("image_base64") or page.get("imageBase64")
        text = page.get("text", "")
        # Kapak (page 0): hikaye metni değil, kitap başlığı kullan
        compose_text = _story_title.strip() if (page_num == 0 and _story_title.strip()) else text

        if page_key in page_images and not force_recompose:
            composed_images[page_key] = {
                "type": "url",
                "data": page_images[page_key],
                "text": text,
            }
            continue

        if image_base64:
            template = cover_template if (page_num == 0 and cover_template) else inner_template
            if template:
                template_config = build_template_config(template)
                _pw, _ph = effective_page_dimensions_mm(template.page_width_mm, template.page_height_mm)
                try:
                    composed = page_composer.compose_page(
                        image_base64=image_base64,
                        text=compose_text,
                        template_config=template_config,
                        page_width_mm=_pw,
                        page_height_mm=_ph,
                        dpi=300,
                    )
                    composed_images[page_key] = {"type": "base64", "data": composed, "text": text}
                except Exception as e:
                    logger.warning("Failed to compose page %s: %s", i, e)
                    composed_images[page_key] = {"type": "error", "error": str(e), "text": text}
            else:
                composed_images[page_key] = {"type": "error", "error": "No template", "text": text}
        else:
            composed_images[page_key] = {"type": "text_only", "text": text}

    # Karşılama sayfasını (dedication) ekle
    if "dedication" in page_images:
        dedication_note = getattr(preview, "dedication_note", "") or ""
        composed_images["dedication"] = {
            "type": "url",
            "data": page_images["dedication"],
            "text": dedication_note,
        }

    return {
        "preview_id": str(preview_id),
        "page_count": len(raw_pages),
        "page_size": f"{page_width_mm}x{page_height_mm}mm",
        "bleed": f"{bleed_mm}mm",
        "composed_images": composed_images,
    }


@router.get("/stats/previews")
async def get_preview_stats(
    db: DbSession,
    admin: AdminUser,
) -> dict:
    """Get statistics about story previews."""
    # Total counts by status
    result = await db.execute(
        select(StoryPreview.status, func.count(StoryPreview.id)).group_by(StoryPreview.status)
    )
    status_counts = {row[0]: row[1] for row in result.all()}

    # Total revenue from confirmed orders — compute actual totals (base + addons)
    confirmed_result = await db.execute(
        select(StoryPreview).where(StoryPreview.status == "CONFIRMED")
    )
    confirmed_previews = confirmed_result.scalars().all()
    total_revenue = sum(
        _compute_actual_total(p) or 0.0 for p in confirmed_previews
    )

    return {
        "total": sum(status_counts.values()),
        "pending": status_counts.get("PENDING", 0),
        "confirmed": status_counts.get("CONFIRMED", 0),
        "expired": status_counts.get("EXPIRED", 0),
        "cancelled": status_counts.get("CANCELLED", 0),
        "total_revenue": float(total_revenue),
    }


# Legacy Order endpoints have been removed.


# ── Invoice admin endpoints ──────────────────────────────────────────────


@router.get("/{order_id}/invoice/download")
async def admin_download_invoice(
    order_id: UUID,
    db: DbSession,
    admin: AdminUser,
) -> Any:
    """Admin: download invoice PDF (no owner check)."""
    from io import BytesIO

    from fastapi.responses import StreamingResponse
    from sqlalchemy import or_

    from app.models.invoice import Invoice, InvoiceStatus
    from app.services.storage_service import storage_service

    inv_result = await db.execute(
        select(Invoice).where(
            or_(Invoice.order_id == order_id, Invoice.story_preview_id == order_id)
        )
    )
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


@router.post("/{order_id}/invoice/create")
async def admin_create_invoice(
    order_id: UUID,
    db: DbSession,
    admin: AdminUser,
) -> dict[str, Any]:
    """Admin: sipariş veya önizleme için fatura oluştur (henüz fatura kaydı yoksa).

    order_id; orders.id (eski akış) veya story_previews.id (trial akışı) olabilir.
    Zaten fatura varsa 409 döner; var olan faturayı yenilemek için /regenerate kullan.
    """
    import uuid as _uuid
    from datetime import UTC
    from datetime import datetime as _dt

    from sqlalchemy import or_
    from sqlalchemy.dialects.postgresql import insert as pg_insert

    from app.models.invoice import Invoice
    from app.models.story_preview import PreviewStatus, StoryPreview
    from app.services.invoice_pdf_service import generate_invoice_pdf

    # ── 1. Resolve billing entity (Order or StoryPreview) ────────────────────
    is_preview_flow = False
    order_result = await db.execute(select(Order).where(Order.id == order_id))
    order = order_result.scalar_one_or_none()

    if order is None:
        prev_result = await db.execute(
            select(StoryPreview).where(StoryPreview.id == order_id)
        )
        preview = prev_result.scalar_one_or_none()
        if preview is None:
            raise NotFoundError("Sipariş", order_id)
        is_preview_flow = True

    # ── 2. Status gate ────────────────────────────────────────────────────────
    if not is_preview_flow:
        from app.models.order import OrderStatus
        paid_statuses = {
            OrderStatus.PAID.value,
            OrderStatus.PROCESSING.value,
            OrderStatus.READY_FOR_PRINT.value,
            OrderStatus.SHIPPED.value,
            OrderStatus.DELIVERED.value,
        }
        if order.status not in paid_statuses:
            raise HTTPException(
                status_code=400,
                detail=f"Fatura yalnızca ödenmiş siparişler için oluşturulabilir (mevcut durum: {order.status})",
            )
    else:
        paid_preview_statuses = {
            PreviewStatus.COMPLETING.value,
            PreviewStatus.COMPLETED.value,
            PreviewStatus.CONFIRMED.value,
        }
        if preview.status not in paid_preview_statuses:
            raise HTTPException(
                status_code=400,
                detail=f"Fatura yalnızca ödenmiş siparişler için oluşturulabilir (mevcut durum: {preview.status})",
            )

    # ── 3. Idempotency: reject if invoice already exists ─────────────────────
    existing = await db.execute(
        select(Invoice).where(
            or_(Invoice.order_id == order_id, Invoice.story_preview_id == order_id)
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=409,
            detail="Bu sipariş için zaten bir fatura kaydı mevcut. Yenilemek için /regenerate kullanın.",
        )

    # ── 4. Insert invoice row ─────────────────────────────────────────────────
    now = _dt.now(UTC)
    from app.services.invoice_number_service import next_invoice_number
    invoice_number = await next_invoice_number(db)

    if is_preview_flow:
        conflict_col = "story_preview_id"
        values = {
            "id": _uuid.uuid4(),
            "order_id": None,
            "story_preview_id": order_id,
            "invoice_number": invoice_number,
            "invoice_status": "PENDING",
            "issued_at": now,
        }
    else:
        conflict_col = "order_id"
        values = {
            "id": _uuid.uuid4(),
            "order_id": order_id,
            "story_preview_id": None,
            "invoice_number": invoice_number,
            "invoice_status": "PENDING",
            "issued_at": now,
        }

    stmt = pg_insert(Invoice).values(**values).on_conflict_do_nothing(
        index_elements=[conflict_col]
    )
    await db.execute(stmt)
    await db.commit()

    # ── 5. Generate PDF ───────────────────────────────────────────────────────
    try:
        await generate_invoice_pdf(order_id, db)
    except Exception as exc:
        logger.error(
            "admin_create_invoice: pdf generation failed",
            ref_id=str(order_id),
            error=str(exc),
        )
        return {"status": "failed", "invoice_number": invoice_number, "error": str(exc)[:200]}

    inv_result = await db.execute(
        select(Invoice).where(
            or_(Invoice.order_id == order_id, Invoice.story_preview_id == order_id)
        )
    )
    invoice = inv_result.scalar_one_or_none()
    return {
        "status": "ok",
        "invoice_number": invoice_number,
        "invoice_status": invoice.invoice_status if invoice else "PENDING",
    }


@router.post("/{order_id}/invoice/regenerate")
async def admin_regenerate_invoice(
    order_id: UUID,
    db: DbSession,
    admin: AdminUser,
) -> dict[str, Any]:
    """Admin: regenerate invoice PDF (increments pdf_version)."""
    from sqlalchemy import or_

    from app.models.invoice import Invoice, InvoiceStatus
    from app.services.invoice_pdf_service import generate_invoice_pdf

    inv_result = await db.execute(
        select(Invoice).where(
            or_(Invoice.order_id == order_id, Invoice.story_preview_id == order_id)
        )
    )
    invoice = inv_result.scalar_one_or_none()
    if not invoice:
        raise NotFoundError("Fatura", order_id)

    invoice.pdf_version = (invoice.pdf_version or 1) + 1
    invoice.invoice_status = InvoiceStatus.PENDING.value
    await db.commit()

    try:
        await generate_invoice_pdf(order_id, db)
    except Exception as exc:
        logger.error("admin_regenerate_invoice: failed", ref_id=str(order_id), error=str(exc))
        return {"status": "failed", "error": str(exc)[:200]}

    await db.refresh(invoice)
    return {
        "status": "ok",
        "invoice_number": invoice.invoice_number,
        "pdf_version": invoice.pdf_version,
        "invoice_status": invoice.invoice_status,
    }


@router.post("/{order_id}/invoice/retry")
async def admin_retry_invoice(
    order_id: UUID,
    db: DbSession,
    admin: AdminUser,
) -> dict[str, Any]:
    """Admin: retry a FAILED invoice PDF generation."""
    from sqlalchemy import or_

    from app.models.invoice import Invoice, InvoiceStatus
    from app.services.invoice_pdf_service import generate_invoice_pdf

    inv_result = await db.execute(
        select(Invoice).where(
            or_(Invoice.order_id == order_id, Invoice.story_preview_id == order_id)
        )
    )
    invoice = inv_result.scalar_one_or_none()
    if not invoice:
        raise NotFoundError("Fatura", order_id)

    if invoice.invoice_status != InvoiceStatus.FAILED.value:
        raise HTTPException(
            status_code=400,
            detail=f"Fatura durumu FAILED değil: {invoice.invoice_status}",
        )

    try:
        await generate_invoice_pdf(order_id, db)
    except Exception as exc:
        logger.error("admin_retry_invoice: failed", ref_id=str(order_id), error=str(exc))
        return {"status": "failed", "error": str(exc)[:200]}

    await db.refresh(invoice)
    return {
        "status": "ok",
        "invoice_number": invoice.invoice_number,
        "invoice_status": invoice.invoice_status,
        "retry_count": invoice.retry_count,
    }


@router.get("/invoices/issues")
async def admin_invoice_issues(
    db: DbSession,
    admin: AdminUser,
) -> list[dict[str, Any]]:
    """Admin: list orders with PAID status but invoice not PDF_READY or missing."""
    from app.models.invoice import Invoice, InvoiceStatus

    paid_statuses = [
        OrderStatus.PAID, OrderStatus.PROCESSING,
        OrderStatus.READY_FOR_PRINT, OrderStatus.SHIPPED, OrderStatus.DELIVERED,
    ]
    result = await db.execute(
        select(Order)
        .outerjoin(Invoice, Invoice.order_id == Order.id)
        .where(
            Order.status.in_(paid_statuses),
            (Invoice.id.is_(None)) | (Invoice.invoice_status != InvoiceStatus.PDF_READY.value),
        )
        .order_by(Order.created_at.desc())
    )
    orders = result.scalars().all()

    issues: list[dict[str, Any]] = []
    for o in orders:
        inv_result = await db.execute(select(Invoice).where(Invoice.order_id == o.id))
        inv = inv_result.scalar_one_or_none()
        issues.append({
            "order_id": str(o.id),
            "order_status": o.status.value if hasattr(o.status, "value") else str(o.status),
            "created_at": o.created_at.isoformat(),
            "child_name": o.child_name,
            "invoice_status": inv.invoice_status if inv else "MISSING",
            "invoice_number": inv.invoice_number if inv else None,
            "last_error": inv.last_error if inv else None,
            "retry_count": inv.retry_count if inv else 0,
        })
    return issues


# ────────────────────────────────────────────────────────
# Invoice email management
# ────────────────────────────────────────────────────────

@router.post("/{order_id}/invoice/resend-email")
async def admin_resend_invoice_email(
    order_id: UUID,
    db: DbSession,
    admin: AdminUser,
) -> dict[str, Any]:
    """Admin: resend invoice email (for guest or registered user)."""
    from app.models.audit_log import AuditLog
    from app.services.invoice_email_service import send_invoice_email_for_order

    result = await send_invoice_email_for_order(
        order_id, db, is_resend=True, admin_id=admin.id,
    )

    db.add(AuditLog(
        action="INVOICE_EMAIL_RESEND",
        order_id=order_id,
        admin_id=admin.id,
        details=result,
    ))
    await db.commit()

    return result


@router.get("/invoices/email-issues")
async def admin_invoice_email_issues(
    db: DbSession,
    admin: AdminUser,
) -> list[dict[str, Any]]:
    """Admin: list PDF_READY invoices where email was not sent or failed."""
    from app.models.invoice import Invoice, InvoiceStatus

    result = await db.execute(
        select(Invoice, Order)
        .join(Order, Order.id == Invoice.order_id)
        .where(
            Invoice.invoice_status == InvoiceStatus.PDF_READY.value,
            (Invoice.email_sent_at.is_(None)) | (Invoice.email_status == "FAILED"),
        )
        .order_by(Invoice.created_at.desc())
    )
    rows = result.all()

    issues: list[dict[str, Any]] = []
    for inv, order in rows:
        issues.append({
            "order_id": str(inv.order_id),
            "invoice_number": inv.invoice_number,
            "invoice_status": inv.invoice_status,
            "email_status": inv.email_status or "NOT_SENT",
            "email_error": inv.email_error,
            "email_retry_count": inv.email_retry_count,
            "billing_email": order.billing_email,
            "has_email": bool(order.billing_email),
            "is_guest": order.user_id is None,
            "child_name": order.child_name,
            "created_at": inv.created_at.isoformat() if inv.created_at else None,
        })
    return issues


# ────────────────────────────────────────────────────────
# Invoice download token management
# ────────────────────────────────────────────────────────

@router.post("/{order_id}/invoice/revoke-tokens")
async def admin_revoke_invoice_tokens(
    order_id: UUID,
    db: DbSession,
    admin: AdminUser,
) -> dict[str, Any]:
    """Admin: revoke all active download tokens for an order and optionally issue a new one."""
    from app.models.audit_log import AuditLog
    from app.services.invoice_token_service import (
        create_download_token,
        revoke_tokens_for_order,
    )

    revoked = await revoke_tokens_for_order(order_id, db, admin_id=admin.id)

    from app.models.invoice import Invoice, InvoiceStatus
    inv_result = await db.execute(select(Invoice).where(Invoice.order_id == order_id))
    invoice = inv_result.scalar_one_or_none()

    new_token: str | None = None
    if invoice and invoice.invoice_status == InvoiceStatus.PDF_READY.value:
        new_token = await create_download_token(
            order_id=order_id,
            invoice_id=invoice.id,
            db=db,
            created_by="admin",
        )

    db.add(AuditLog(
        action="INVOICE_TOKENS_REVOKED",
        order_id=order_id,
        admin_id=admin.id,
        details={"revoked_count": revoked, "new_token_issued": new_token is not None},
    ))
    await db.commit()

    return {
        "revoked_count": revoked,
        "new_token_issued": new_token is not None,
    }


# Token attempts and extend token endpoints have been removed as part of dead code cleanup.


# ────────────────────────────────────────────────────────
# Report 3: Token download abuse / high-fail tokens
# ────────────────────────────────────────────────────────

@router.get("/invoices/token-abuse")
async def admin_token_abuse_report(
    db: DbSession,
    admin: AdminUser,
    min_used: int = Query(3, ge=1, description="Minimum used_count to flag"),
) -> list[dict[str, Any]]:
    """Admin: list tokens with suspiciously high usage or multiple failed attempts.

    Returns tokens where used_count >= min_used (default 3) OR tokens that are
    expired/revoked but had usage, grouped by order.
    """
    from app.models.invoice_download_token import InvoiceDownloadToken

    now = datetime.now(UTC)

    result = await db.execute(
        select(InvoiceDownloadToken, Order)
        .join(Order, Order.id == InvoiceDownloadToken.order_id)
        .where(
            (InvoiceDownloadToken.used_count >= min_used)
            | (
                (InvoiceDownloadToken.revoked_at.isnot(None))
                & (InvoiceDownloadToken.used_count > 0)
            )
        )
        .order_by(InvoiceDownloadToken.used_count.desc())
        .limit(100)
    )
    rows = result.all()

    items: list[dict[str, Any]] = []
    for token, order in rows:
        is_expired = token.expires_at < now
        items.append({
            "token_id": str(token.id),
            "token_hash_prefix": token.token_hash[:8] + "...",
            "order_id": str(token.order_id),
            "child_name": order.child_name,
            "used_count": token.used_count,
            "max_uses": token.max_uses,
            "is_expired": is_expired,
            "is_revoked": token.revoked_at is not None,
            "first_used_at": token.first_used_at.isoformat() if token.first_used_at else None,
            "last_used_at": token.last_used_at.isoformat() if token.last_used_at else None,
            "created_at": token.created_at.isoformat() if token.created_at else None,
            "created_by": token.created_by,
        })
    return items


# ────────────────────────────────────────────────────────
# Combined reports dashboard
# ────────────────────────────────────────────────────────

@router.get("/invoices/dashboard")
async def admin_invoice_dashboard(
    db: DbSession,
    admin: AdminUser,
) -> dict[str, Any]:
    """Admin: aggregated invoice health dashboard — counts for each issue category."""
    from app.models.invoice import Invoice, InvoiceStatus
    from app.models.invoice_download_token import InvoiceDownloadToken

    datetime.now(UTC)

    paid_statuses = [
        OrderStatus.PAID, OrderStatus.PROCESSING,
        OrderStatus.READY_FOR_PRINT, OrderStatus.SHIPPED, OrderStatus.DELIVERED,
    ]

    # 1) PAID but no PDF_READY
    pdf_issues_result = await db.execute(
        select(func.count())
        .select_from(Order)
        .outerjoin(Invoice, Invoice.order_id == Order.id)
        .where(
            Order.status.in_(paid_statuses),
            (Invoice.id.is_(None)) | (Invoice.invoice_status != InvoiceStatus.PDF_READY.value),
        )
    )
    pdf_issues_count = pdf_issues_result.scalar() or 0

    # 2) PDF_READY but email not sent / failed
    email_issues_result = await db.execute(
        select(func.count())
        .select_from(Invoice)
        .where(
            Invoice.invoice_status == InvoiceStatus.PDF_READY.value,
            (Invoice.email_sent_at.is_(None)) | (Invoice.email_status == "FAILED"),
        )
    )
    email_issues_count = email_issues_result.scalar() or 0

    # 3) Tokens with high usage (potential abuse)
    token_abuse_result = await db.execute(
        select(func.count())
        .select_from(InvoiceDownloadToken)
        .where(InvoiceDownloadToken.used_count >= 3)
    )
    token_abuse_count = token_abuse_result.scalar() or 0

    # 4) Total invoices by status
    status_result = await db.execute(
        select(Invoice.invoice_status, func.count(Invoice.id))
        .group_by(Invoice.invoice_status)
    )
    status_counts = {row[0]: row[1] for row in status_result.all()}

    return {
        "pdf_issues_count": pdf_issues_count,
        "email_issues_count": email_issues_count,
        "token_abuse_count": token_abuse_count,
        "invoice_status_counts": status_counts,
        "total_invoices": sum(status_counts.values()),
    }

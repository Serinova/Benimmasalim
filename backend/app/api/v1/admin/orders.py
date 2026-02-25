"""Admin order management endpoints."""

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

import structlog
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import func, select

from app.api.v1.deps import AdminUser, DbSession
from app.core.exceptions import NotFoundError
from app.models.order import Order, OrderStatus
from app.models.story_preview import StoryPreview

router = APIRouter()
logger = structlog.get_logger()



def _page_images_for_preview(preview: StoryPreview) -> dict | None:
    """page_images doluysa onu döndür, yoksa preview_images (GCS URL'leri)."""
    if preview.page_images and len(preview.page_images) > 0:
        return preview.page_images
    if preview.preview_images and len(preview.preview_images) > 0:
        return preview.preview_images
    return None


def _append_cache_bust(url: str, version: str) -> str:
    """Append ?v= or &v= to avoid breaking signed URLs (existing query)."""
    if not url or not version:
        return url
    sep = "&v=" if "?" in url else "?v="
    return url + sep + version


def _detect_pipeline_version(preview: StoryPreview) -> str:
    """Detect pipeline version from strongest source to weakest."""
    cache = getattr(preview, "generated_prompts_cache", None) or {}
    if cache.get("pipeline_version") == "v3":
        return "v3"
    if cache.get("blueprint_json"):
        return "v3"
    cache_prompts = cache.get("prompts") if isinstance(cache, dict) else None
    if isinstance(cache_prompts, list):
        for p in cache_prompts:
            if not isinstance(p, dict):
                continue
            if (
                p.get("pipeline_version") == "v3"
                or p.get("composer_version") == "v3"
                or p.get("v3_composed")
            ):
                return "v3"
    raw_pages = preview.story_pages or []
    for p in raw_pages:
        if not isinstance(p, dict):
            continue
        if (
            p.get("pipeline_version") == "v3"
            or p.get("composer_version") == "v3"
            or p.get("v3_composed")
        ):
            return "v3"
    logger.error(
        "V2_LABEL_BLOCKED: expected v3",
        route="/api/v1/admin/orders/previews/{preview_id}",
        preview_id=str(getattr(preview, "id", "")),
        reason="missing_v3_markers",
    )
    return "v3"


def _story_pages_for_display(preview: StoryPreview) -> list[dict]:
    """Story pages with user-visible visual_prompt (Cappadocia + style; never Kapadokya)."""
    from app.prompt_engine import get_display_visual_prompt

    raw = preview.story_pages or []
    style = getattr(preview, "visual_style_name", None) or ""
    debug = getattr(preview, "prompt_debug_json", None) or {}
    out = []
    for p in raw:
        if not isinstance(p, dict):
            out.append({"text": str(p), "visual_prompt": "", "page_number": len(out)})
            continue
        page_num = p.get("page_number", len(out))
        display_prompt = get_display_visual_prompt(
            p.get("visual_prompt", ""),
            page_num,
            style,
            debug,
        )
        out.append({**p, "visual_prompt": display_prompt})
    return out


def _enrich_manifest_with_prompts(preview: StoryPreview) -> dict | None:
    """Manifest'e final_prompt/negative_prompt ekle (prompt_debug veya story_pages'den)."""
    manifest = getattr(preview, "generation_manifest_json", None) or {}
    prompt_debug = getattr(preview, "prompt_debug_json", None) or {}
    raw_pages = preview.story_pages or []
    if not manifest:
        return manifest
    enriched: dict[str, Any] = {}
    for k, m in manifest.items():
        if not isinstance(m, dict):
            enriched[str(k)] = m
            continue
        entry = dict(m)
        key_str = str(k)
        pd = prompt_debug.get(key_str) or prompt_debug.get(k)
        if not entry.get("final_prompt") and pd:
            if isinstance(pd, dict):
                if pd.get("final_prompt"):
                    entry["final_prompt"] = pd["final_prompt"]
                if pd.get("negative_prompt"):
                    entry["negative_prompt"] = pd["negative_prompt"]
        if not entry.get("final_prompt"):
            try:
                idx = int(k)
            except (ValueError, TypeError):
                idx = -1
            if 0 <= idx < len(raw_pages):
                p = raw_pages[idx]
                if isinstance(p, dict) and p.get("visual_prompt"):
                    entry["final_prompt"] = p["visual_prompt"]
        enriched[key_str] = entry
    return enriched


def _page_images_with_cache_bust(preview: StoryPreview) -> dict | None:
    """Return page_images with cache-bust param: ?v=prompt_hash or ?v=updated_at."""
    raw = _page_images_for_preview(preview)
    if not raw:
        return None
    manifest = getattr(preview, "generation_manifest_json", None) or {}
    updated_at = getattr(preview, "updated_at", None)
    updated_ts = updated_at.isoformat() if updated_at else ""
    out: dict[str, Any] = {}
    for k, v in raw.items():
        if not isinstance(v, str):
            out[str(k)] = v
            continue
        if v.startswith("data:"):
            out[str(k)] = v
            continue
        page_manifest = manifest.get(str(k)) if isinstance(manifest, dict) else {}
        ver = (
            page_manifest.get("prompt_hash") if isinstance(page_manifest, dict) else None
        ) or updated_ts
        out[str(k)] = _append_cache_bust(v, ver) if ver else v
    return out


# =============================================================================
# STORY PREVIEWS (Pending/Confirmed Orders from Email)
# =============================================================================


@router.get("/previews")
async def list_story_previews(
    db: DbSession,
    admin: AdminUser,
    status: str | None = Query(None, description="Filter by status: PENDING, CONFIRMED, EXPIRED"),
) -> list[dict]:
    """List all story previews (pending and confirmed orders)."""
    query = select(StoryPreview).order_by(StoryPreview.created_at.desc())

    if status:
        query = query.where(StoryPreview.status == status)

    result = await db.execute(query)
    previews = result.scalars().all()

    return [
        {
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
            "product_price": float(p.product_price) if p.product_price else None,
            "scenario_name": p.scenario_name,
            "visual_style_name": p.visual_style_name,
            "learning_outcomes": p.learning_outcomes,
            "page_count": len(p.story_pages) if p.story_pages else 0,
            "page_images": _page_images_with_cache_bust(p),
            "confirmed_at": p.confirmed_at.isoformat() if p.confirmed_at else None,
            "expires_at": p.expires_at.isoformat() if p.expires_at else None,
            "created_at": p.created_at.isoformat() if p.created_at else None,
            "admin_notes": p.admin_notes,
        }
        for p in previews
    ]


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
        "product_price": float(preview.product_price) if preview.product_price else None,
        # Story
        "story_title": preview.story_title,
        "story_pages": _story_pages_for_display(preview),
        "page_images": _page_images_with_cache_bust(preview),
        "dedication_note": getattr(preview, "dedication_note", None),
        # Options
        "scenario_name": preview.scenario_name,
        "visual_style_name": preview.visual_style_name,
        "learning_outcomes": preview.learning_outcomes,
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
        # Cover images
        "back_cover_image_url": getattr(preview, "back_cover_image_url", None),
        # Page count
        "page_count": len(preview.story_pages) if preview.story_pages else 0,
    }


def _extract_pdf_url(preview: StoryPreview) -> str | None:
    """PDF URL'yi manifest'ten veya admin_notes'tan çıkar."""
    # 1. generation_manifest_json["final_pdf_url"] (en güvenilir)
    manifest = getattr(preview, "generation_manifest_json", None) or {}
    if isinstance(manifest, dict) and manifest.get("final_pdf_url"):
        return manifest["final_pdf_url"]
    # 2. admin_notes'ta "PDF URL: ..." satırı (eski format)
    notes = getattr(preview, "admin_notes", None) or ""
    for line in notes.splitlines():
        line = line.strip()
        if line.startswith("PDF URL:"):
            url = line[len("PDF URL:"):].strip()
            if url:
                return url
    return None


def _build_prompts_by_page(preview: StoryPreview) -> dict[str, dict]:
    """Per-page prompt data with metadata — keyed by page_number (not array index).

    Returns dict[page_number_str, {final_prompt, negative_prompt, page_type,
    page_index, story_page_number, composer_version, pipeline_version}].
    """
    from app.prompt_engine.constants import NEGATIVE_PROMPT, STRICT_NEGATIVE_ADDITIONS

    prompt_debug = getattr(preview, "prompt_debug_json", None) or {}
    cache = getattr(preview, "generated_prompts_cache", None) or {}
    cache_prompts = cache.get("prompts") if isinstance(cache, dict) else None
    cache_by_page: dict[str, dict] = {}
    if isinstance(cache_prompts, list):
        for cp in cache_prompts:
            if not isinstance(cp, dict):
                continue
            cp_key = str(cp.get("page_number", len(cache_by_page)))
            cache_by_page[cp_key] = cp
    raw_pages = preview.story_pages or []
    _fallback_neg = f"{NEGATIVE_PROMPT} {STRICT_NEGATIVE_ADDITIONS}".strip()

    out: dict[str, dict] = {}
    for i, page in enumerate(raw_pages):
        if not isinstance(page, dict):
            continue

        page_num = page.get("page_number", i)
        key = str(page_num)

        # Try prompt_debug first (from image generation debug), then fall back to raw page
        pd = prompt_debug.get(key) or prompt_debug.get(str(page_num)) or prompt_debug.get(page_num)
        final_p = ""
        neg_p = ""
        if isinstance(pd, dict):
            final_p = pd.get("final_prompt") or ""
            neg_p = pd.get("negative_prompt") or ""

        if not final_p:
            final_p = page.get("visual_prompt", "")
        if not neg_p:
            neg_p = page.get("negative_prompt", "") or (_fallback_neg if final_p else "")

        cp = cache_by_page.get(key) or {}
        composer_ver = page.get("composer_version", "") or cp.get("composer_version", "")
        page_v3 = page.get("v3_composed", False) or bool(cp.get("v3_composed"))
        page_pipeline = page.get("pipeline_version", "") or cp.get("pipeline_version", "")

        # Prefer explicit pipeline_version on page, then composer_version, then v3_composed
        if page_pipeline == "v3" or composer_ver == "v3" or page_v3:
            pipeline_ver = "v3"
        else:
            logger.error(
                "V2_LABEL_BLOCKED: expected v3",
                route="/api/v1/admin/orders/previews/{preview_id}",
                preview_id=str(getattr(preview, "id", "")),
                page_number=page_num,
                page_pipeline=page_pipeline or None,
                composer_version=composer_ver or None,
            )
            pipeline_ver = "v3"

        if final_p or neg_p:
            out[key] = {
                "final_prompt": final_p,
                "negative_prompt": neg_p,
                "pipeline_version": pipeline_ver,
                "composer_version": composer_ver or pipeline_ver,
                "page_type": page.get("page_type", "inner"),
                "page_index": page.get("page_index", i),
                "story_page_number": page.get("story_page_number"),
            }
    return out


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

    if num_images >= num_pages:
        return {"success": True, "message": "Tüm sayfaların görseli zaten mevcut", "missing": 0}

    missing = num_pages - num_images

    # Reset status to PROCESSING so worker can process it
    if preview.status in ("QUEUE_FAILED", "FAILED", "PREVIEW_GENERATED", "COMPLETING"):
        preview.status = "PROCESSING"
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

    This creates an Order from the preview and triggers book generation
    including audio if selected.
    """
    import structlog

    from app.models.book_template import BackCoverConfig
    from app.models.product import Product
    from app.services.ai.elevenlabs_service import ElevenLabsService
    from app.services.pdf_service import PDFService
    from app.services.storage_service import StorageService

    logger = structlog.get_logger()

    # Get preview
    result = await db.execute(select(StoryPreview).where(StoryPreview.id == preview_id))
    preview = result.scalar_one_or_none()

    if not preview:
        raise NotFoundError("Önizleme", preview_id)

    if preview.status != "CONFIRMED":
        from app.core.exceptions import ValidationError

        raise ValidationError("Sadece onaylanmış siparişler için kitap oluşturulabilir")

    logger.info(
        "Generating book from preview",
        preview_id=str(preview_id),
        has_audio=getattr(preview, "has_audio_book", False),
        audio_type=getattr(preview, "audio_type", None),
    )

    storage = StorageService()
    pdf_service = PDFService()

    # Generate audio if selected
    audio_qr_url = None
    audio_file_url = None

    has_audio = getattr(preview, "has_audio_book", False)
    audio_type = getattr(preview, "audio_type", None)
    audio_voice_id = getattr(preview, "audio_voice_id", None)

    if has_audio:
        try:
            elevenlabs = ElevenLabsService()

            # Combine all page texts
            full_story_text = ""
            if preview.story_pages:
                for page in preview.story_pages:
                    if isinstance(page, dict) and page.get("text"):
                        full_story_text += page["text"] + "\n\n"

            if full_story_text.strip():
                logger.info(
                    "Generating audio book",
                    preview_id=str(preview_id),
                    audio_type=audio_type,
                    text_length=len(full_story_text),
                )

                # Generate audio using ElevenLabs
                if audio_type == "cloned" and audio_voice_id:
                    audio_bytes = await elevenlabs.text_to_speech(
                        text=full_story_text,
                        voice_id=audio_voice_id,
                    )
                else:
                    # Use system voice (default female)
                    audio_bytes = await elevenlabs.text_to_speech(
                        text=full_story_text,
                        voice_type="female",
                    )

                # Upload audio to GCS
                audio_file_url = storage.upload_audio(
                    audio_bytes=audio_bytes,
                    order_id=str(preview.id),
                    filename="audiobook.mp3",
                )

                # Generate signed URL for QR code (valid for 1 year)
                audio_qr_url = storage.get_signed_url(
                    audio_file_url,
                    expiration_hours=24 * 365,
                )

                logger.info(
                    "Audio book generated",
                    preview_id=str(preview_id),
                    audio_url=audio_file_url,
                )

        except Exception as e:
            logger.error(
                "Audio generation failed",
                preview_id=str(preview_id),
                error=str(e),
            )
            # Don't fail - continue without audio

    # Get back cover config
    back_cover_config = None
    try:
        result = await db.execute(
            select(BackCoverConfig)
            .where(BackCoverConfig.is_active == True)
            .where(BackCoverConfig.is_default == True)
        )
        back_cover_config = result.scalar_one_or_none()
    except Exception as e:
        logger.warning("Failed to get back cover config", error=str(e))

    # Get product with inner_template eagerly loaded
    from sqlalchemy.orm import selectinload

    product = None
    inner_template = None
    page_width_mm = 297.0  # Varsayılan: yatay A4 (kitap formatı)
    page_height_mm = 210.0
    bleed_mm = 3.0

    if preview.product_id:
        result = await db.execute(
            select(Product)
            .where(Product.id == preview.product_id)
            .options(selectinload(Product.inner_template), selectinload(Product.cover_template))
        )
        product = result.scalar_one_or_none()

        if product:
            if product.inner_template:
                inner_template = product.inner_template
                _w = inner_template.page_width_mm
                _h = inner_template.page_height_mm
                if _w < _h:
                    from app.utils.resolution_calc import (
                        A4_LANDSCAPE_HEIGHT_MM,
                        A4_LANDSCAPE_WIDTH_MM,
                    )
                    page_width_mm, page_height_mm = A4_LANDSCAPE_WIDTH_MM, A4_LANDSCAPE_HEIGHT_MM
                else:
                    page_width_mm, page_height_mm = _w, _h
                bleed_mm = inner_template.bleed_mm

    template_config: dict = {
        "page_width_mm": page_width_mm,
        "page_height_mm": page_height_mm,
        "bleed_mm": bleed_mm,
        "image_x_percent": 0.0,
        "image_y_percent": 0.0,
        "image_width_percent": 100.0,
        "image_height_percent": 70.0,
        "text_x_percent": 5.0,
        "text_y_percent": 72.0,
        "text_width_percent": 90.0,
        "text_height_percent": 25.0,
        "text_position": "bottom",
        "text_align": "center",
        "font_family": "Arial",
        "font_size_pt": 16,
        "font_color": "#333333",
        "background_color": "#FFFFFF",
    }
    if inner_template:
        template_config.update({
            "image_x_percent": inner_template.image_x_percent or 0.0,
            "image_y_percent": inner_template.image_y_percent or 0.0,
            "image_width_percent": inner_template.image_width_percent or 100.0,
            "image_height_percent": inner_template.image_height_percent or 70.0,
            "text_x_percent": inner_template.text_x_percent or 5.0,
            "text_y_percent": inner_template.text_y_percent or 72.0,
            "text_width_percent": inner_template.text_width_percent or 90.0,
            "text_height_percent": inner_template.text_height_percent or 25.0,
            "text_position": inner_template.text_position or "bottom",
            "text_align": inner_template.text_align or "center",
            "font_family": inner_template.font_family or "Arial",
            "font_size_pt": inner_template.font_size_pt or 16,
            "font_color": inner_template.font_color or "#333333",
            "background_color": inner_template.background_color or "#FFFFFF",
        })

    # Generate PDF
    pdf_url = None
    pdf_error: str | None = None
    back_cover_image_url: str | None = None
    intro_image_url: str | None = None
    _intro_b64: str | None = None
    try:
        logger.info("Generating PDF for preview", preview_id=str(preview_id))

        # Get cover image from page_images (veya preview_images GCS fallback)
        cover_image_url = None
        page_images = _page_images_for_preview(preview) or {}
        if page_images:
            cover_image_url = page_images.get("0") or page_images.get(0) or page_images.get("cover")

        # Build story pages with images — skip page 0 if used as cover
        # NOTE: page_images are ALREADY composed (text overlay). Clear image_base64
        # to prevent accidental re-composition in PDF service fallback path.
        story_pages_with_images = []
        raw_pages = preview.story_pages or []
        for i, page in enumerate(raw_pages):
            if i == 0 and cover_image_url:
                continue
            if isinstance(page, dict) and page.get("page_type") == "front_matter":
                continue
            page_data = dict(page) if isinstance(page, dict) else {"text": str(page)}
            page_num = page.get("page_number", i) if isinstance(page, dict) else i
            page_key = str(page_num)
            if page_key in page_images:
                page_data["image_url"] = page_images[page_key]
                page_data.pop("image_base64", None)
                page_data.pop("imageBase64", None)
            elif page_num in page_images:
                page_data["image_url"] = page_images[page_num]
                page_data.pop("image_base64", None)
                page_data.pop("imageBase64", None)
            story_pages_with_images.append(page_data)

        # Karşılama sayfası URL'i
        dedication_image_url = page_images.get("dedication")

        # Karşılama 2 + Arka kapak — paralel üret (zaman kazanmak için)
        import asyncio as _asyncio
        from app.models.scenario import Scenario as _Scenario

        # Scenario lookup (shared by both tasks)
        _scenario_obj_shared = None
        _cache_shared = getattr(preview, "generated_prompts_cache", None) or {}
        _sc_id_str = _cache_shared.get("scenario_id") if isinstance(_cache_shared, dict) else None
        if _sc_id_str:
            try:
                import uuid as _uuid
                _scenario_obj_shared = await db.get(_Scenario, _uuid.UUID(_sc_id_str))
            except Exception:
                pass
        if _scenario_obj_shared is None and getattr(preview, "scenario_name", None):
            from sqlalchemy import select as _sel_sc2
            _sc_res2 = await db.execute(
                _sel_sc2(_Scenario).where(_Scenario.name == preview.scenario_name).limit(1)
            )
            _scenario_obj_shared = _sc_res2.scalar_one_or_none()

        # Dedication template (shared)
        from app.models.book_template import PageTemplate as _PageTemplate
        from sqlalchemy import select as _select_tpl
        _ded_tpl_result = await db.execute(
            _select_tpl(_PageTemplate)
            .where(_PageTemplate.page_type == "dedication")
            .where(_PageTemplate.is_active == True)
            .limit(1)
        )
        _ded_tpl_shared = _ded_tpl_result.scalar_one_or_none()

        async def _build_intro_page() -> tuple[str | None, str | None]:
            """Returns (intro_image_url, intro_b64). Uploads to GCS so admin panel can display it."""
            _url = page_images.get("intro")
            if _url:
                return _url, None
            try:
                from app.tasks.generate_book import _generate_scenario_intro_text
                from app.services.page_composer import PageComposer, build_template_config
                from app.services.storage_service import StorageService as _IntroStorage
                import base64 as _b64mod

                _text = await _generate_scenario_intro_text(
                    scenario=_scenario_obj_shared,
                    child_name=preview.child_name or "",
                    story_title=getattr(preview, "story_title", "") or "",
                )
                if _text:
                    _cfg = build_template_config(_ded_tpl_shared) if _ded_tpl_shared else {}
                    _b64 = PageComposer().compose_dedication_page(text=_text, template_config=_cfg, dpi=300)
                    if _b64:
                        # Upload to GCS so admin panel can display it
                        try:
                            _img_bytes = _b64mod.b64decode(_b64)
                            _intro_gcs_url = await _IntroStorage().upload_generated_image(
                                _img_bytes, str(preview.id), page_number=9998
                            )
                            # Save to page_images so it persists
                            _pi = dict(preview.page_images or {})
                            _pi["intro"] = _intro_gcs_url
                            preview.page_images = _pi
                            logger.info("Scenario intro page (karşılama 2) uploaded to GCS", preview_id=str(preview_id), url=_intro_gcs_url[:80])
                            return _intro_gcs_url, None
                        except Exception as _upload_err:
                            logger.warning("Intro page GCS upload failed, using base64 fallback", error=str(_upload_err))
                            return None, _b64
            except Exception as _e:
                logger.warning("Scenario intro page failed", preview_id=str(preview_id), error=str(_e))
            return None, None

        async def _build_back_cover() -> str | None:
            """Returns back_cover_image_url or None."""
            _existing = page_images.get("backcover") or getattr(preview, "back_cover_image_url", None)
            if _existing:
                return _existing
            try:
                from app.prompt.book_context import BookContext
                from app.prompt.cover_builder import build_back_cover_prompt
                from app.services.ai.gemini_consistent_image import GeminiConsistentImageService
                from app.services.storage_service import StorageService as _StorageService
                from app.utils.resolution_calc import (
                    A4_LANDSCAPE_HEIGHT_MM,
                    A4_LANDSCAPE_WIDTH_MM,
                    calculate_generation_params_from_mm,
                )

                _storage_bc = _StorageService()
                _image_svc = GeminiConsistentImageService()
                _style_name = getattr(preview, "visual_style_name", None) or ""
                _scenario_name = getattr(preview, "scenario_name", None) or "magical adventure"
                _child_gender = getattr(preview, "child_gender", None) or "child"
                _child_name_bc = preview.child_name or "child"
                _child_age_bc = getattr(preview, "child_age", None) or 7
                
                # PRIORITY 1: Try to resolve clothing from scenario (most accurate)
                _clothing = ""
                _scenario_id = getattr(preview, "scenario_id", None)
                if _scenario_id:
                    try:
                        from app.models.scenario import Scenario as _Scen
                        from sqlalchemy import select as _sel
                        from uuid import UUID as _U
                        _sc_res = await db.execute(_sel(_Scen).where(_Scen.id == _U(str(_scenario_id))))
                        _sc = _sc_res.scalar_one_or_none()
                        if _sc:
                            _g = (_child_gender or "erkek").lower()
                            if _g in ("kiz", "kız", "girl", "female"):
                                _clothing = (getattr(_sc, "outfit_girl", None) or "").strip() or (getattr(_sc, "outfit_boy", None) or "").strip()
                            else:
                                _clothing = (getattr(_sc, "outfit_boy", None) or "").strip() or (getattr(_sc, "outfit_girl", None) or "").strip()
                            if _clothing:
                                logger.info("back_cover: clothing resolved from scenario (priority)", scenario_id=str(_scenario_id), outfit=_clothing[:60])
                    except Exception as _ce:
                        logger.warning("back_cover: failed to resolve clothing from scenario", error=str(_ce))
                
                # PRIORITY 2: Fallback to preview's clothing_description if scenario didn't have outfit
                if not _clothing:
                    _clothing = (getattr(preview, "clothing_description", None) or "").strip()
                    if _clothing:
                        logger.info("back_cover: using preview clothing_description (fallback)", outfit=_clothing[:60])
                
                _face_ref_url = getattr(preview, "face_crop_url", None) or getattr(preview, "child_photo_url", None)

                _book_ctx = BookContext.build(
                    child_name=_child_name_bc, child_age=_child_age_bc, child_gender=_child_gender,
                    scenario_name=_scenario_name, clothing_description=_clothing,
                    story_title=getattr(preview, "story_title", ""), style_modifier=_style_name,
                )
                _back_scene = (
                    f"Wide panoramic view. The same young {_child_gender} seen from behind or side, "
                    f"gazing into the distance of the {_scenario_name} world. "
                    f"Continuation of the front cover atmosphere — same lighting, same environment, same mood."
                )
                _back_prompt = build_back_cover_prompt(ctx=_book_ctx, scene_description=_back_scene)
                _params = calculate_generation_params_from_mm(A4_LANDSCAPE_WIDTH_MM, A4_LANDSCAPE_HEIGHT_MM)
                
                # CRITICAL: Back cover should have NO text/title, use stronger negative prompt
                _back_negative = (
                    "text, title, letters, words, writing, book title, story title, "
                    "watermark, signature, logo, typography, "
                    "close-up, portrait, headshot, face filling frame, cropped body, cut-off legs"
                )
                
                _result = await _image_svc.generate_consistent_image(
                    prompt=_back_prompt, child_face_url=_face_ref_url, clothing_prompt=_clothing,
                    style_modifier=_style_name, width=_params["generation_width"], height=_params["generation_height"],
                    id_weight=_book_ctx.style.id_weight, is_cover=True, template_en=None, story_title="",
                    child_gender=_child_gender, child_age=_child_age_bc, 
                    style_negative_en=_back_negative, base_negative_en="",
                    skip_compose=True,  # Already composed by build_back_cover_prompt
                    precomposed_negative="",
                    reference_embedding=getattr(preview, "face_embedding", None),
                    character_description=getattr(preview, "child_description", None) or "",
                )
                _img_url = _result[0] if isinstance(_result, tuple) else _result
                import httpx as _httpx
                async with _httpx.AsyncClient(timeout=60.0) as _client:
                    _resp = await _client.get(_img_url)
                    _img_bytes = _resp.content
                
                # Upscale/resize to target dimensions for print quality
                from app.utils.resolution_calc import resize_image_bytes_to_target
                _target_w, _target_h = _params["target_width"], _params["target_height"]
                logger.info("back_cover: resizing to target", gen_size=f"{_params['generation_width']}x{_params['generation_height']}", target_size=f"{_target_w}x{_target_h}")
                _img_bytes = resize_image_bytes_to_target(_img_bytes, _target_w, _target_h, output_format="JPEG", dpi=300)
                
                _bc_url = await _storage_bc.upload_generated_image(_img_bytes, str(preview.id), page_number=9999)
                logger.info("Back cover image generated", preview_id=str(preview_id), url=_bc_url[:80])
                return _bc_url
            except Exception as _bc_err:
                logger.warning("Back cover generation failed — continuing without it", preview_id=str(preview_id), error=str(_bc_err))
                return None

        # Run intro + back cover generation in parallel
        (_intro_url_result, _intro_b64_result), back_cover_image_url = await _asyncio.gather(
            _build_intro_page(),
            _build_back_cover(),
        )
        intro_image_url = _intro_url_result
        _intro_b64 = _intro_b64_result

        _needs_commit = False
        if back_cover_image_url and back_cover_image_url != getattr(preview, "back_cover_image_url", None):
            preview.back_cover_image_url = back_cover_image_url
            _needs_commit = True
        if intro_image_url and intro_image_url != (preview.page_images or {}).get("intro"):
            _needs_commit = True  # page_images already updated inside _build_intro_page
        if _needs_commit:
            await db.commit()

        # Prepare data for PDF
        # page_images are ALREADY composed (text overlay applied by page_composer)
        pdf_data = {
            "child_name": preview.child_name,
            "story_pages": story_pages_with_images,
            "cover_image_url": cover_image_url,
            "dedication_image_url": dedication_image_url,
            "intro_image_base64": _intro_b64,
            "intro_image_url": intro_image_url,
            "back_cover_config": back_cover_config,
            "back_cover_image_url": back_cover_image_url,
            "audio_qr_url": audio_qr_url,
            "page_width_mm": page_width_mm,
            "page_height_mm": page_height_mm,
            "bleed_mm": bleed_mm,
            "template_config": template_config,
            "images_precomposed": True,
        }

        # Generate PDF bytes (run in threadpool — blocking I/O)
        from starlette.concurrency import run_in_threadpool
        pdf_bytes = await run_in_threadpool(pdf_service.generate_book_pdf_from_preview, pdf_data)

        if pdf_bytes:
            # Upload to GCS
            pdf_url = storage.upload_pdf(
                pdf_bytes=pdf_bytes,
                order_id=str(preview.id),
            )
            logger.info("PDF generated and uploaded", preview_id=str(preview_id), pdf_url=pdf_url)
        else:
            pdf_error = "PDF üretimi boş sonuç döndürdü"
            logger.warning("PDF generation returned empty bytes", preview_id=str(preview_id))
    except Exception as e:
        pdf_error = str(e)
        logger.error("PDF generation failed", preview_id=str(preview_id), error=str(e), exc_info=True)

    # Update preview with generated URLs
    notes_update = ""
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
        "has_audio": has_audio,
        "audio_url": audio_file_url,
        "audio_qr_url": audio_qr_url,
        "pdf_url": pdf_url,
        "pdf_error": pdf_error,
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

async def _generate_admin_pdf_inner(preview_id: str) -> str:
    """Arq worker tarafından çağrılır. PDF üretir, GCS'ye yükler ve order.final_pdf_url kaydeder."""

    import structlog
    from sqlalchemy.orm import selectinload
    from starlette.concurrency import run_in_threadpool

    from app.core.database import async_session_factory
    from app.models.book_template import BackCoverConfig
    from app.models.order import Order
    from app.models.product import Product
    from app.models.story_preview import StoryPreview
    from app.services.pdf_service import PDFService
    from app.services.storage_service import StorageService

    logger = structlog.get_logger()

    async with async_session_factory() as db:
        result = await db.execute(select(StoryPreview).where(StoryPreview.id == preview_id))
        preview = result.scalar_one_or_none()

        if not preview:
            logger.error("PDF task: Preview not found", preview_id=preview_id)
            raise ValueError(f"Preview {preview_id} not found")

        # Get product with both cover and inner templates eagerly loaded
        product = None
        page_width_mm = 297.0  # Default: Yatay A4
        page_height_mm = 210.0
        bleed_mm = 3.0
        inner_template = None
        _cover_template = None  # Reserved for cover-specific logic

        if preview.product_id:
            result = await db.execute(
                select(Product)
                .where(Product.id == preview.product_id)
                .options(selectinload(Product.inner_template), selectinload(Product.cover_template))
            )
            product = result.scalar_one_or_none()

            if product:
                if product.inner_template:
                    inner_template = product.inner_template
                    _w, _h = inner_template.page_width_mm, inner_template.page_height_mm
                    if _w < _h:
                        from app.utils.resolution_calc import (
                            A4_LANDSCAPE_HEIGHT_MM,
                            A4_LANDSCAPE_WIDTH_MM,
                        )
                        page_width_mm, page_height_mm = A4_LANDSCAPE_WIDTH_MM, A4_LANDSCAPE_HEIGHT_MM
                    else:
                        page_width_mm, page_height_mm = _w, _h
                    bleed_mm = inner_template.bleed_mm

        template_config = {
            "page_width_mm": page_width_mm,
            "page_height_mm": page_height_mm,
            "bleed_mm": bleed_mm,
            "image_x_percent": 0.0,
            "image_y_percent": 0.0,
            "image_width_percent": 100.0,
            "image_height_percent": 70.0,
            "text_x_percent": 5.0,
            "text_y_percent": 72.0,
            "text_width_percent": 90.0,
            "text_height_percent": 25.0,
            "text_position": "bottom",
            "text_align": "center",
            "font_family": "Arial",
            "font_size_pt": 16,
            "font_color": "#333333",
            "background_color": "#FFFFFF",
        }

        if inner_template:
            template_config.update(
                {
                    "image_x_percent": inner_template.image_x_percent or 0.0,
                    "image_y_percent": inner_template.image_y_percent or 0.0,
                    "image_width_percent": inner_template.image_width_percent or 100.0,
                    "image_height_percent": inner_template.image_height_percent or 70.0,
                    "text_x_percent": inner_template.text_x_percent or 5.0,
                    "text_y_percent": inner_template.text_y_percent or 72.0,
                    "text_width_percent": inner_template.text_width_percent or 90.0,
                    "text_height_percent": inner_template.text_height_percent or 25.0,
                    "text_position": inner_template.text_position or "bottom",
                    "text_align": inner_template.text_align or "center",
                    "font_family": inner_template.font_family or "Arial",
                    "font_size_pt": inner_template.font_size_pt or 16,
                    "font_color": inner_template.font_color or "#333333",
                    "background_color": inner_template.background_color or "#FFFFFF",
                }
            )

        back_cover_config = None
        try:
            result = await db.execute(
                select(BackCoverConfig)
                .where(BackCoverConfig.is_active == True)
                .where(BackCoverConfig.is_default == True)
            )
            back_cover_config = result.scalar_one_or_none()
        except Exception as e:
            logger.warning("Failed to get back cover config", error=str(e))

        page_images = _page_images_for_preview(preview) or {}
        raw_pages = preview.story_pages or []

        cover_image_url = None
        if page_images:
            cover_image_url = page_images.get("0") or page_images.get(0) or page_images.get("cover")

        story_pages = []
        for i, page in enumerate(raw_pages):
            if i == 0 and cover_image_url:
                continue
            if isinstance(page, dict) and page.get("page_type") == "front_matter":
                continue

            page_data = dict(page) if isinstance(page, dict) else {"text": str(page)}
            page_num = page.get("page_number", i) if isinstance(page, dict) else i
            page_key = str(page_num)

            if page_key in page_images:
                page_data["image_url"] = page_images[page_key]
                page_data.pop("image_base64", None)
                page_data.pop("imageBase64", None)
            elif page_num in page_images:
                page_data["image_url"] = page_images[page_num]
                page_data.pop("image_base64", None)
                page_data.pop("imageBase64", None)

            story_pages.append(page_data)

        audio_qr_url = None
        has_audio = getattr(preview, "has_audio_book", False)

        if has_audio:
            stored_audio_url = getattr(preview, "audio_file_url", None)
            if stored_audio_url:
                audio_qr_url = stored_audio_url
            else:
                try:
                    from app.services.ai.elevenlabs_service import ElevenLabsService
                    from app.services.storage_service import StorageService

                    storage = StorageService()
                    elevenlabs = ElevenLabsService()

                    full_story_text = ""
                    if preview.story_pages:
                        for page in preview.story_pages:
                            if isinstance(page, dict) and page.get("text"):
                                full_story_text += page["text"] + "\n\n"

                    if full_story_text.strip():
                        audio_type = getattr(preview, "audio_type", "system")
                        audio_voice_id = getattr(preview, "audio_voice_id", None)

                        if audio_type == "cloned" and audio_voice_id:
                            audio_bytes = await elevenlabs.text_to_speech(
                                text=full_story_text,
                                voice_id=audio_voice_id,
                            )
                        else:
                            audio_bytes = await elevenlabs.text_to_speech(
                                text=full_story_text,
                                voice_type="female",
                            )

                        audio_file_url = storage.upload_audio(
                            audio_bytes=audio_bytes,
                            order_id=str(preview.id),
                            filename="audiobook.mp3",
                        )
                        preview.audio_file_url = audio_file_url
                        await db.commit()
                        audio_qr_url = audio_file_url
                except Exception as e:
                    logger.error("Failed to generate audio for PDF", preview_id=str(preview_id), error=str(e))

        dedication_image_url = page_images.get("dedication")

        # Karşılama 2 (senaryo intro) — page_images'dan al veya üret
        _admin_intro_image_url: str | None = page_images.get("intro")
        _admin_intro_b64: str | None = None
        if not _admin_intro_image_url:
            try:
                from app.tasks.generate_book import _generate_scenario_intro_text
                from app.models.scenario import Scenario as _AdminScenario

                # StoryPreview has no direct scenario_id — look in generated_prompts_cache,
                # then fall back to querying by scenario_name
                _admin_scenario_obj = None
                _admin_cache = getattr(preview, "generated_prompts_cache", None) or {}
                _admin_sc_id_str = _admin_cache.get("scenario_id") if isinstance(_admin_cache, dict) else None
                if _admin_sc_id_str:
                    try:
                        import uuid as _admin_uuid
                        _admin_scenario_obj = await db.get(_AdminScenario, _admin_uuid.UUID(_admin_sc_id_str))
                    except Exception:
                        pass
                if _admin_scenario_obj is None and getattr(preview, "scenario_name", None):
                    from sqlalchemy import select as _admin_sel_sc
                    _admin_sc_res = await db.execute(
                        _admin_sel_sc(_AdminScenario).where(_AdminScenario.name == preview.scenario_name).limit(1)
                    )
                    _admin_scenario_obj = _admin_sc_res.scalar_one_or_none()

                _admin_intro_text = await _generate_scenario_intro_text(
                    scenario=_admin_scenario_obj,
                    child_name=preview.child_name or "",
                    story_title=getattr(preview, "story_title", "") or "",
                )
                if _admin_intro_text:
                    from app.models.book_template import PageTemplate as _AdminPageTemplate
                    from app.services.page_composer import PageComposer, build_template_config
                    from sqlalchemy import select as _admin_select

                    _admin_ded_tpl_result = await db.execute(
                        _admin_select(_AdminPageTemplate)
                        .where(_AdminPageTemplate.page_type == "dedication")
                        .where(_AdminPageTemplate.is_active == True)
                        .limit(1)
                    )
                    _admin_ded_tpl = _admin_ded_tpl_result.scalar_one_or_none()
                    _admin_intro_cfg = build_template_config(_admin_ded_tpl) if _admin_ded_tpl else {}
                    _admin_intro_composer = PageComposer()
                    _admin_intro_b64 = _admin_intro_composer.compose_dedication_page(
                        text=_admin_intro_text,
                        template_config=_admin_intro_cfg,
                        dpi=300,
                    )
                    if _admin_intro_b64:
                        logger.info("Scenario intro page (karşılama 2) composed for admin PDF", preview_id=str(preview_id))
            except Exception as _intro_err:
                logger.warning("Scenario intro page generation failed — continuing without it", preview_id=str(preview_id), error=str(_intro_err))

        back_cover_image_url = (
            page_images.get("backcover")
            or getattr(preview, "back_cover_image_url", None)
        )

        # Generate back cover image if not already available
        if not back_cover_image_url:
            try:
                from app.prompt.book_context import BookContext
                from app.prompt.cover_builder import build_back_cover_prompt
                from app.services.ai.gemini_consistent_image import GeminiConsistentImageService
                from app.services.storage_service import StorageService as _StorageService
                from app.utils.resolution_calc import (
                    A4_LANDSCAPE_HEIGHT_MM,
                    A4_LANDSCAPE_WIDTH_MM,
                    calculate_generation_params_from_mm,
                )

                _storage = _StorageService()
                _image_svc = GeminiConsistentImageService()

                _style_name = getattr(preview, "visual_style_name", None) or ""
                _scenario_name = getattr(preview, "scenario_name", None) or "magical adventure"
                _child_gender = getattr(preview, "child_gender", None) or "child"
                _child_name = preview.child_name or "child"
                _child_age = getattr(preview, "child_age", None) or 7
                
                # PRIORITY 1: Try to resolve clothing from scenario (most accurate)
                _clothing = ""
                _scenario_id = getattr(preview, "scenario_id", None)
                if _scenario_id:
                    try:
                        from app.models.scenario import Scenario as _Scen2
                        from sqlalchemy import select as _sel2
                        from uuid import UUID as _U2
                        _sc_res2 = await db.execute(_sel2(_Scen2).where(_Scen2.id == _U2(str(_scenario_id))))
                        _sc2 = _sc_res2.scalar_one_or_none()
                        if _sc2:
                            _g2 = (_child_gender or "erkek").lower()
                            if _g2 in ("kiz", "kız", "girl", "female"):
                                _clothing = (getattr(_sc2, "outfit_girl", None) or "").strip() or (getattr(_sc2, "outfit_boy", None) or "").strip()
                            else:
                                _clothing = (getattr(_sc2, "outfit_boy", None) or "").strip() or (getattr(_sc2, "outfit_girl", None) or "").strip()
                            if _clothing:
                                logger.info("back_cover_admin: clothing resolved from scenario (priority)", scenario_id=str(_scenario_id), outfit=_clothing[:60])
                    except Exception as _ce2:
                        logger.warning("back_cover_admin: failed to resolve clothing from scenario", error=str(_ce2))
                
                # PRIORITY 2: Fallback to preview's clothing_description if scenario didn't have outfit
                if not _clothing:
                    _clothing = (getattr(preview, "clothing_description", None) or "").strip()
                    if _clothing:
                        logger.info("back_cover_admin: using preview clothing_description (fallback)", outfit=_clothing[:60])
                
                _face_ref_url = getattr(preview, "face_crop_url", None) or getattr(preview, "child_photo_url", None)

                _book_ctx = BookContext.build(
                    child_name=_child_name,
                    child_age=_child_age,
                    child_gender=_child_gender,
                    scenario_name=_scenario_name,
                    clothing_description=_clothing,
                    story_title=getattr(preview, "story_title", ""),
                    style_modifier=_style_name,
                )

                _back_scene = (
                    f"Wide panoramic view. "
                    f"The same young {_child_gender} seen from behind or side, "
                    f"gazing into the distance of the {_scenario_name} world. "
                    f"Continuation of the front cover atmosphere — same lighting, same environment, same mood."
                )
                _back_prompt = build_back_cover_prompt(ctx=_book_ctx, scene_description=_back_scene)

                _params = calculate_generation_params_from_mm(A4_LANDSCAPE_WIDTH_MM, A4_LANDSCAPE_HEIGHT_MM)
                _width, _height = _params["generation_width"], _params["generation_height"]

                # CRITICAL: Back cover should have NO text/title, use stronger negative prompt
                _back_negative = (
                    "text, title, letters, words, writing, book title, story title, "
                    "watermark, signature, logo, typography, "
                    "close-up, portrait, headshot, face filling frame, cropped body, cut-off legs"
                )

                _result = await _image_svc.generate_consistent_image(
                    prompt=_back_prompt,
                    child_face_url=_face_ref_url,
                    clothing_prompt=_clothing,
                    style_modifier=_style_name,
                    width=_width,
                    height=_height,
                    id_weight=_book_ctx.style.id_weight,
                    is_cover=True,
                    template_en=None,
                    story_title="",
                    child_gender=_child_gender,
                    child_age=_child_age,
                    style_negative_en=_back_negative,
                    base_negative_en="",
                    skip_compose=False,
                    precomposed_negative="",
                    reference_embedding=getattr(preview, "face_embedding", None),
                    character_description=getattr(preview, "child_description", None) or "",
                )
                _img_url = _result[0] if isinstance(_result, tuple) else _result

                import httpx as _httpx
                async with _httpx.AsyncClient(timeout=60.0) as _client:
                    _resp = await _client.get(_img_url)
                    _img_bytes = _resp.content

                # Upscale/resize to target dimensions for print quality
                from app.utils.resolution_calc import resize_image_bytes_to_target
                _target_w, _target_h = _params["target_width"], _params["target_height"]
                logger.info("back_cover_admin: resizing to target", gen_size=f"{_params['generation_width']}x{_params['generation_height']}", target_size=f"{_target_w}x{_target_h}")
                _img_bytes = resize_image_bytes_to_target(_img_bytes, _target_w, _target_h, output_format="JPEG", dpi=300)

                back_cover_image_url = await _storage.upload_generated_image(
                    _img_bytes,
                    str(preview.id),
                    page_number=9999,
                )

                preview.back_cover_image_url = back_cover_image_url
                await db.commit()
                logger.info("Back cover image generated for admin PDF", preview_id=str(preview_id), url=back_cover_image_url[:80])
            except Exception as _bc_err:
                logger.warning("Back cover image generation failed — continuing without it", preview_id=str(preview_id), error=str(_bc_err))

        pdf_data = {
            "child_name": preview.child_name,
            "story_pages": story_pages,
            "cover_image_url": cover_image_url,
            "dedication_image_url": dedication_image_url,
            "intro_image_base64": _admin_intro_b64,
            "intro_image_url": _admin_intro_image_url,
            "back_cover_config": back_cover_config,
            "back_cover_image_url": back_cover_image_url,
            "audio_qr_url": audio_qr_url,
            "page_width_mm": page_width_mm,
            "page_height_mm": page_height_mm,
            "bleed_mm": bleed_mm,
            "template_config": template_config,
            "images_precomposed": True,
        }

        pdf_service = PDFService()
        pdf_bytes = await run_in_threadpool(pdf_service.generate_book_pdf_from_preview, pdf_data)

        if not pdf_bytes:
            raise ValueError("PDF oluşturulamadı (boş)")

        storage = StorageService()
        pdf_url = storage.upload_pdf(pdf_bytes=pdf_bytes, order_id=str(preview.id))

        # Update StoryPreview with the generated PDF URL
        manifest = dict(preview.generation_manifest_json) if preview.generation_manifest_json else {}
        manifest["final_pdf_url"] = pdf_url
        preview.generation_manifest_json = manifest
        
        # Also check for matching Order to update final_pdf_url
        result = await db.execute(select(Order).where(Order.id == preview.id))
        order = result.scalar_one_or_none()
        if order:
            order.final_pdf_url = pdf_url
            
        await db.commit()

        return pdf_url


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

    # Total revenue from confirmed orders
    result = await db.execute(
        select(func.sum(StoryPreview.product_price)).where(StoryPreview.status == "CONFIRMED")
    )
    total_revenue = result.scalar() or 0

    return {
        "total": sum(status_counts.values()),
        "pending": status_counts.get("PENDING", 0),
        "confirmed": status_counts.get("CONFIRMED", 0),
        "expired": status_counts.get("EXPIRED", 0),
        "cancelled": status_counts.get("CANCELLED", 0),
        "total_revenue": float(total_revenue),
    }


class OrderListResponse(BaseModel):
    """Paginated order list response."""

    items: list[dict]
    total: int
    page: int
    page_size: int


class UpdateTrackingRequest(BaseModel):
    """Update tracking number request."""

    tracking_number: str
    carrier: str


@router.get("", response_model=OrderListResponse)
async def list_orders(
    db: DbSession,
    admin: AdminUser,
    status: OrderStatus | None = Query(None),
    date_from: datetime | None = Query(None),
    date_to: datetime | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
) -> OrderListResponse:
    """
    List all orders with filters.

    Admin only endpoint.
    """
    query = select(Order)

    if status:
        query = query.where(Order.status == status)
    if date_from:
        query = query.where(Order.created_at >= date_from)
    if date_to:
        query = query.where(Order.created_at <= date_to)

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Paginate
    query = query.order_by(Order.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    orders = result.scalars().all()

    return OrderListResponse(
        items=[
            {
                "id": str(o.id),
                "status": o.status.value,
                "child_name": o.child_name,
                "payment_amount": float(o.payment_amount) if o.payment_amount else None,
                "tracking_number": o.tracking_number,
                "created_at": o.created_at.isoformat(),
            }
            for o in orders
        ],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{order_id}")
async def get_order_detail(
    order_id: UUID,
    db: DbSession,
    admin: AdminUser,
) -> dict[str, Any]:
    """Get detailed order information for admin."""
    result = await db.execute(select(Order).where(Order.id == order_id))
    order = result.scalar_one_or_none()

    if not order:
        raise NotFoundError("Sipariş", order_id)

    return {
        "id": str(order.id),
        "status": order.status.value,
        "child_name": order.child_name,
        "child_age": order.child_age,
        "child_gender": order.child_gender,
        "selected_outcomes": order.selected_outcomes,
        "payment_id": order.payment_id,
        "payment_amount": float(order.payment_amount) if order.payment_amount else None,
        "payment_status": order.payment_status,
        "shipping_address": order.shipping_address,
        "tracking_number": order.tracking_number,
        "carrier": order.carrier,
        "has_audio_book": order.has_audio_book,
        "audio_type": order.audio_type,
        "cover_regenerate_count": order.cover_regenerate_count,
        "final_pdf_url": order.final_pdf_url,
        "delivered_at": order.delivered_at.isoformat() if order.delivered_at else None,
        "photo_deletion_scheduled_at": (
            order.photo_deletion_scheduled_at.isoformat()
            if order.photo_deletion_scheduled_at
            else None
        ),
        "created_at": order.created_at.isoformat(),
        "updated_at": order.updated_at.isoformat(),
    }


@router.get("/{order_id}/download-pdf")
async def download_pdf(
    order_id: UUID,
    db: DbSession,
    admin: AdminUser,
) -> dict:
    """Download order PDF for printing. Returns GCS URL."""
    result = await db.execute(select(Order).where(Order.id == order_id))
    order = result.scalar_one_or_none()

    if not order:
        raise NotFoundError("Sipariş", order_id)

    if not order.final_pdf_url:
        raise HTTPException(status_code=404, detail="PDF henüz oluşturulmamış")

    return {"pdf_url": order.final_pdf_url}


@router.patch("/{order_id}/tracking")
async def update_tracking(
    order_id: UUID,
    request: UpdateTrackingRequest,
    db: DbSession,
    admin: AdminUser,
) -> dict[str, Any]:
    """Update tracking number and mark as shipped."""
    result = await db.execute(select(Order).where(Order.id == order_id))
    order = result.scalar_one_or_none()

    if not order:
        raise NotFoundError("Sipariş", order_id)

    if order.status != OrderStatus.READY_FOR_PRINT:
        from app.core.exceptions import ValidationError

        raise ValidationError("Kargo takip no sadece READY_FOR_PRINT durumunda eklenebilir")

    order.tracking_number = request.tracking_number
    order.carrier = request.carrier

    # Transition to SHIPPED
    from app.services.order_state_machine import transition_order

    await transition_order(order, OrderStatus.SHIPPED, db, actor_id=admin.id)

    return {
        "id": str(order.id),
        "status": order.status.value,
        "tracking_number": order.tracking_number,
        "carrier": order.carrier,
    }


@router.post("/{order_id}/regenerate-page")
async def regenerate_page(
    order_id: UUID,
    page_number: int,
    db: DbSession,
    admin: AdminUser,
) -> dict[str, Any]:
    """Regenerate a specific page (admin only, no limit)."""
    result = await db.execute(select(Order).where(Order.id == order_id))
    order = result.scalar_one_or_none()

    if not order:
        raise NotFoundError("Sipariş", order_id)

    # TODO: Implement page regeneration
    # This will be in the AI services task

    return {
        "order_id": str(order_id),
        "page_number": page_number,
        "status": "regenerating",
    }

"""Try Before You Buy - Trial API Endpoints.

Phase 1: Generate full story + 3 preview images (FREE)
Phase 2: After payment, generate remaining 13 images (PAID)
"""

import asyncio
import uuid

import structlog
from fastapi import APIRouter, BackgroundTasks, Header, HTTPException, Query, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import CurrentUser, DbSession, CurrentUserOptional
from app.config import get_settings
from app.models.story_preview import PreviewStatus, StoryPreview
from app.models.visual_style import VisualStyle
from app.models.product import Product
from app.models.scenario import Scenario
from app.models.order import Order, OrderStatus
from app.services.trial_service import get_trial_service
from app.services.trial_generation_service import (
    generate_trial_story_inner as _generate_trial_story_inner,
    generate_preview_images_inner as _generate_preview_images_inner,
    generate_composed_preview_inner as _generate_composed_preview_inner,
    generate_remaining_images_inner as _generate_remaining_images_inner,
    create_coloring_book_order_from_trial as _create_coloring_book_order_from_trial,
    resolve_visual_style_from_db as _resolve_visual_style_from_db,
    select_preview_prompts as _select_preview_prompts,
)
from app.services.trial_payment_service import (
    create_iyzico_checkout,
    get_iyzico_options,
    verify_iyzico_payment,
)
from app.schemas.trials import (
    BillingData,
    CompleteTrialRequest,
    CreatePaymentRequest,
    CreateTrialRequest,
    GeneratePreviewRequest,
    PreviewResponse,
    StoryPageInput,
    TrialResponse,
    VerifyTrialPaymentRequest,
)

logger = structlog.get_logger()
router = APIRouter()
_V3_BLOCK_MSG = "V2_LABEL_BLOCKED: expected v3"
_TRIAL_CREATE_ROUTE = "/api/v1/trials/create"

_settings = get_settings()

# Trial background tasks get their own semaphore so they are never blocked by
# long-running order jobs.  Default: 3 slots (trials are lightweight: 3 images).
_TRIAL_GEN_SEMAPHORE = asyncio.Semaphore(_settings.trial_concurrency_slots)


def _mask_email(email: str | None) -> str:
    """Mask email for safe logging: us***@domain.com"""
    if not email or "@" not in email:
        return "***"
    local, domain = email.split("@", 1)
    return f"{local[:2]}***@{domain}"


# ============ PHASE 1: Create Trial & Generate Preview ============


@router.post("/create", response_model=TrialResponse)
async def create_trial(
    request: CreateTrialRequest,
    background_tasks: BackgroundTasks,
    db: DbSession,
    current_user: CurrentUserOptional = None,
) -> TrialResponse:
    """Create a new trial - Phase 1 of "Try Before You Buy".

    This endpoint saves lead data and enqueues story generation to a
    background worker.  It returns in < 1 s — no Gemini call is made
    inside the HTTP request.

    Frontend should poll /trials/{trial_id}/status for updates.
    """
    try:
        from uuid import UUID as _UUID

        from app.services.trial_service import get_trial_service as _get_ts

        # ── Resolve page_count: request > linked_product > scenario > explicit_product > fallback 16 ──
        # Öncelik: request > senaryonun bağlı ürünü > senaryo default > explicit ürün > 16
        _page_count: int | None = request.page_count
        _scenario_obj = None

        if not _page_count and request.scenario_id:
            try:
                from sqlalchemy import select as _sel
                from sqlalchemy.orm import selectinload as _sil

                from app.models.scenario import Scenario

                _sr = await db.execute(
                    _sel(Scenario)
                    .where(Scenario.id == _UUID(request.scenario_id))
                    .options(_sil(Scenario.linked_product))
                )
                _scenario_obj = _sr.scalar_one_or_none()
                if _scenario_obj:
                    # Önce linked_product'ın default_page_count'ını dene
                    _lp = getattr(_scenario_obj, "linked_product", None)
                    if _lp and _lp.default_page_count and _lp.default_page_count >= 4:
                        _page_count = int(_lp.default_page_count)
                    # Linked product yoksa veya page_count yoksa senaryo default'unu kullan
                    elif _scenario_obj.default_page_count and _scenario_obj.default_page_count >= 4:
                        _page_count = int(_scenario_obj.default_page_count)
            except Exception:
                pass

        # Explicit product default_page_count (senaryo yoksa veya page_count hala boşsa)
        if not _page_count and request.product_id:
            try:
                from sqlalchemy import select as _sel

                from app.models.product import Product

                _pr = await db.execute(
                    _sel(Product).where(Product.id == _UUID(request.product_id))
                )
                _product = _pr.scalar_one_or_none()
                if _product and _product.default_page_count and _product.default_page_count >= 4:
                    _page_count = int(_product.default_page_count)
            except Exception:
                pass
        if not _page_count:
            _page_count = 16

        # ── Create trial lead (fast DB insert, no AI call) ──
        # lead_user_id: JWT token'dan gelen current_user öncelikli,
        # yoksa request body'deki user_id, yoksa None.
        _effective_lead_user_id: uuid.UUID | None = None
        if current_user:
            _effective_lead_user_id = current_user.id
        elif request.user_id:
            try:
                _effective_lead_user_id = uuid.UUID(request.user_id)
            except (ValueError, AttributeError):
                pass

        trial_service = _get_ts(db)
        trial = await trial_service.create_trial_lead(
            lead_user_id=_effective_lead_user_id,
            parent_name=request.parent_name,
            parent_email=request.parent_email,
            parent_phone=request.parent_phone,
            child_name=request.child_name,
            child_age=request.child_age,
            child_gender=request.child_gender,
            product_id=uuid.UUID(request.product_id) if request.product_id else None,
            product_name=request.product_name,
            product_price=request.product_price,
            scenario_name=request.scenario_name,
            visual_style_name=request.visual_style_name,
            learning_outcomes=request.learning_outcomes,
            child_photo_url=request.child_photo_url,
            visual_style=request.visual_style,
            scenario_id=request.scenario_id,
            page_count=_page_count,
            magic_items=request.magic_items,
        )

        # ── Enqueue story generation to Arq worker ──
        _request_data = {
            "child_name": request.child_name,
            "child_age": request.child_age,
            "child_gender": request.child_gender,
            "child_photo_url": request.child_photo_url,
            "scenario_id": request.scenario_id,
            "scenario_name": request.scenario_name,
            "visual_style": request.visual_style,
            "visual_style_name": request.visual_style_name,
            "learning_outcomes": request.learning_outcomes,
            "page_count": _page_count,
            "magic_items": request.magic_items,
            "product_id": request.product_id,
            "product_name": request.product_name,
        }

        _arq_ok = False
        try:
            from app.workers.enqueue import enqueue_trial_story

            _arq_job_id = await enqueue_trial_story(
                trial_id=str(trial.id),
                request_data=_request_data,
            )
            if _arq_job_id:
                _arq_ok = True
        except Exception as _enq_err:
            logger.warning("Arq enqueue failed for trial story", error=str(_enq_err))

        if not _arq_ok:
            background_tasks.add_task(
                _generate_trial_story_inner,
                trial_id=str(trial.id),
                request_data=_request_data,
            )

        # Provide queue-aware message to user
        _msg = "Hikaye oluşturuluyor, lütfen bekleyin..."
        try:
            from app.workers.enqueue import get_queue_depth

            _depth = await get_queue_depth()
            if _depth > 10:
                _msg = (
                    "Yoğunluk nedeniyle hikaye oluşturma biraz uzayabilir. "
                    "Sayfayı kapatmayın, size bildireceğiz!"
                )
        except Exception:
            pass

        return TrialResponse(
            success=True,
            trial_id=str(trial.id),
            status=trial.status,
            message=_msg,
            preview_url=f"/preview/{trial.confirmation_token}",
            trial_token=trial.confirmation_token,
            used_page_count=_page_count,
        )

    except Exception as e:
        logger.exception("Failed to create trial", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Trial oluşturulamadı: {str(e)}",
        )


async def generate_preview_images_background(
    trial_id: str,
    prompts: list[dict],
    child_photo_url: str | None,
    visual_style: str | None,
    product_name: str | None = None,
    story_title: str = "",
    clothing_description: str = "",
    visual_style_name: str | None = None,
):
    """Background task to generate 3 preview images. Uses effective image provider (Fal/Gemini).

    Guarded by _TRIAL_GEN_SEMAPHORE so trial tasks never compete with order tasks.
    """
    logger.info("Trial preview waiting for semaphore slot", trial_id=trial_id)
    async with _TRIAL_GEN_SEMAPHORE:
        logger.info("Trial preview acquired semaphore slot", trial_id=trial_id)
        await _generate_preview_images_inner(
            trial_id, prompts, child_photo_url, visual_style,
            product_name, story_title, clothing_description, visual_style_name,
        )


# ============ GENERATE PREVIEW FROM EXISTING STORY ============


@router.post("/generate-preview", response_model=TrialResponse)
async def generate_preview_from_story(
    request: GeneratePreviewRequest,
    background_tasks: BackgroundTasks,
    db: DbSession,
    current_user: CurrentUserOptional = None,
) -> TrialResponse:
    """
    Generate 3 preview images from an already-generated story.
    Unlike /create, this does NOT re-generate the story via Gemini.
    It directly creates a trial record and generates 3 composed preview images.
    """
    try:
        trial_service = get_trial_service(db)

        story_pages = [
            {
                "page_number": p.page_number,
                "text": p.text,
                "visual_prompt": p.visual_prompt,
                **({"v3_composed": True, "negative_prompt": getattr(p, "negative_prompt", "") or ""} if getattr(p, "v3_composed", False) else {}),
                **({"page_type": p.page_type} if getattr(p, "page_type", None) else {}),
                **({"composer_version": p.composer_version} if getattr(p, "composer_version", None) else {}),
                **({"pipeline_version": p.pipeline_version} if getattr(p, "pipeline_version", None) else {}),
            }
            for p in request.story_pages
        ]

        # Deterministic title
        from app.services.order_helpers import force_deterministic_title as _force_deterministic_title

        det_title = _force_deterministic_title(
            child_name=request.child_name,
            scenario_name=request.scenario_name,
            original_title=request.story_title,
        )

        # ── COVER TEXT GUARD ──────────────────────────────────────────────
        # Cover page (page_number=0) must carry the story TITLE, not story
        # text.  Frontend may send the wrong text for page 0.
        for sp in story_pages:
            if isinstance(sp, dict) and sp.get("page_number") == 0:
                sp["text"] = det_title
                sp["page_type"] = sp.get("page_type") or "cover"
                break

        # Resolve style_id for cache (Phase 2 remaining images need it)
        _resolved_style_id: str | None = None
        _resolved_vs = await _resolve_visual_style_from_db(db, request.visual_style_name)
        if _resolved_vs:
            _resolved_style_id = str(_resolved_vs.id)

        # Resolve clothing from scenario if not provided by frontend
        _effective_clothing = (request.clothing_description or "").strip()
        if not _effective_clothing and request.scenario_id:
            try:
                from uuid import UUID as _UUID
                from app.models.scenario import Scenario as _Scenario
                from sqlalchemy import select as _select
                _scen_result = await db.execute(
                    _select(_Scenario).where(_Scenario.id == _UUID(request.scenario_id))
                )
                _scen = _scen_result.scalar_one_or_none()
                if _scen:
                    _gender = (request.child_gender or "erkek").lower()
                    if _gender in ("kiz", "kız", "girl", "female"):
                        _effective_clothing = (getattr(_scen, "outfit_girl", None) or "").strip()
                        if not _effective_clothing:
                            _effective_clothing = (getattr(_scen, "outfit_boy", None) or "").strip()
                    else:
                        _effective_clothing = (getattr(_scen, "outfit_boy", None) or "").strip()
                        if not _effective_clothing:
                            _effective_clothing = (getattr(_scen, "outfit_girl", None) or "").strip()
                    if _effective_clothing:
                        logger.info(
                            "generate_preview: clothing resolved from scenario",
                            scenario_id=request.scenario_id,
                            gender=_gender,
                            outfit=_effective_clothing[:60],
                        )
            except Exception as _ce:
                logger.warning("generate_preview: failed to resolve clothing from scenario", error=str(_ce))

        # lead_user_id: JWT token'dan gelen current_user öncelikli,
        # yoksa request body'deki user_id, yoksa None.
        _gp_lead_user_id: uuid.UUID | None = None
        if current_user:
            _gp_lead_user_id = current_user.id
        elif request.user_id:
            try:
                _gp_lead_user_id = uuid.UUID(request.user_id)
            except (ValueError, AttributeError):
                pass

        trial = await trial_service.create_trial(
            lead_user_id=_gp_lead_user_id,
            parent_name=request.parent_name,
            parent_email=request.parent_email,
            parent_phone=request.parent_phone,
            child_name=request.child_name,
            child_age=request.child_age,
            child_gender=request.child_gender,
            product_id=uuid.UUID(request.product_id) if request.product_id else None,
            product_name=request.product_name,
            product_price=request.product_price,
            story_title=det_title,
            scenario_name=request.scenario_name,
            visual_style_name=request.visual_style_name,
            learning_outcomes=request.learning_outcomes,
            story_pages=story_pages,
            generated_prompts=story_pages,
            child_photo_url=request.child_photo_url,
            clothing_description=_effective_clothing,
            style_id=_resolved_style_id,
        )

        # Try Arq (persistent Redis queue) first, fall back to BackgroundTasks
        _arq_ok_comp = False
        try:
            from app.workers.enqueue import enqueue_trial_composed_preview

            _comp_preview_prompts = _select_preview_prompts(story_pages, num_inner=2)
            _arq_comp_id = await enqueue_trial_composed_preview(
                trial_id=str(trial.id),
                prompts=_comp_preview_prompts,
                child_photo_url=request.child_photo_url,
                visual_style=request.visual_style,
                visual_style_name=request.visual_style_name,
                product_id=request.product_id,
                story_title=det_title,
                clothing_description=_effective_clothing,
                child_name=request.child_name,
                child_age=request.child_age,
                child_gender=request.child_gender,
                id_weight=request.id_weight,
                scenario_id=request.scenario_id,
            )
            if _arq_comp_id:
                _arq_ok_comp = True
        except Exception as _enq_err:
            logger.warning("Arq enqueue failed for composed preview", error=str(_enq_err))
        if not _arq_ok_comp:
            background_tasks.add_task(
                generate_composed_preview_images_background,
                trial_id=str(trial.id),
                prompts=_comp_preview_prompts,
                child_photo_url=request.child_photo_url,
                visual_style=request.visual_style,
                visual_style_name=request.visual_style_name,
                product_id=request.product_id,
                story_title=det_title,
                clothing_description=_effective_clothing,
                child_name=request.child_name,
                child_age=request.child_age,
                child_gender=request.child_gender,
                id_weight=request.id_weight,
                scenario_id=request.scenario_id,
            )

        return TrialResponse(
            success=True,
            trial_id=str(trial.id),
            status=trial.status,
            message="Önizleme görselleri hazırlanıyor...",
            preview_url=f"/preview/{trial.confirmation_token}",
            trial_token=trial.confirmation_token,
        )

    except Exception as e:
        logger.exception("Failed to generate preview", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Önizleme oluşturulamadı: {str(e)}",
        )


async def generate_composed_preview_images_background(
    trial_id: str,
    prompts: list[dict],
    child_photo_url: str | None,
    visual_style: str | None,
    visual_style_name: str | None = None,
    product_id: str | None = None,
    story_title: str = "",
    clothing_description: str | None = None,
    child_name: str = "",
    child_age: int = 7,
    child_gender: str | None = None,
    id_weight: float | None = None,
    scenario_id: str | None = None,
):
    """
    Background task to generate 3 preview images WITH text composition.
    Guarded by _TRIAL_GEN_SEMAPHORE so trial tasks never compete with order tasks.
    """
    logger.info("Composed preview waiting for semaphore slot", trial_id=trial_id)
    async with _TRIAL_GEN_SEMAPHORE:
        logger.info("Composed preview acquired semaphore slot", trial_id=trial_id)
        await _generate_composed_preview_inner(
            trial_id, prompts, child_photo_url, visual_style,
            visual_style_name, product_id, story_title, clothing_description,
            child_name, child_age, child_gender, id_weight, scenario_id,
        )


# ============ STATUS & PREVIEW ============


def _verify_trial_access(
    trial: StoryPreview,
    x_trial_token: str | None,
) -> None:
    """Verify caller owns this trial via confirmation_token.

    The token is returned to the client at creation time and must be sent
    back as ``X-Trial-Token`` header on subsequent calls.  This prevents
    enumeration / IDOR attacks — knowing the UUID alone is not enough.
    """
    if not x_trial_token:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Trial erişim tokenı gerekli (X-Trial-Token)",
        )
    if x_trial_token != trial.confirmation_token:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Geçersiz trial erişim tokenı",
        )


@router.get("/me", response_model=list[dict])
async def list_my_trials(
    db: DbSession,
    current_user: CurrentUser,
    include_paid: bool = Query(False, description="Include paid/completed trials"),
) -> list[dict]:
    """List trials for current user. include_paid=true for \"Siparişlerim\" section."""
    if include_paid:
        statuses = ["COMPLETING", "COMPLETED", "PAYMENT_PENDING"]
        query = (
            select(StoryPreview)
            .where(StoryPreview.lead_user_id == current_user.id)
            .where(StoryPreview.status.in_(statuses))
        )
    else:
        excluded = ["COMPLETED", "COMPLETING", "CANCELLED", "EXPIRED", "ABANDONED_TRIAL"]
        query = (
            select(StoryPreview)
            .where(StoryPreview.lead_user_id == current_user.id)
            .where(StoryPreview.status.notin_(excluded))
        )
    query = query.order_by(StoryPreview.created_at.desc())
    result = await db.execute(query)
    trials = result.scalars().all()
    return [
        {
            "id": str(t.id),
            "status": t.status,
            "child_name": t.child_name,
            "story_title": t.story_title,
            "created_at": t.created_at.isoformat(),
            "product_name": t.product_name,
            "product_price": float(t.product_price) if t.product_price else None,
            "has_audio_book": t.has_audio_book,
            "has_coloring_book": t.has_coloring_book,
            "preview_images": t.preview_images,
            "confirmation_token": t.confirmation_token,
            "payment_reference": t.payment_reference if include_paid else None,
        }
        for t in trials
    ]


@router.get("/{trial_id}/status")
async def get_trial_status(
    trial_id: str,
    db: DbSession,
    x_trial_token: str | None = Header(None, alias="X-Trial-Token"),
) -> dict:
    """Get current trial status (for polling)."""
    result = await db.execute(select(StoryPreview).where(StoryPreview.id == uuid.UUID(trial_id)))
    trial = result.scalar_one_or_none()

    if not trial:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trial bulunamadı")

    _verify_trial_access(trial, x_trial_token)

    _progress = trial.generation_progress or {}
    _stage = _progress.get("stage", "")
    _is_story_ready = bool(trial.story_pages) and len(trial.story_pages) > 0

    return {
        "trial_id": str(trial.id),
        "status": trial.status,
        "is_preview_ready": trial.status in (
            PreviewStatus.PREVIEW_GENERATED.value,
            PreviewStatus.PENDING.value,
        ),
        "is_story_ready": _is_story_ready,
        "is_failed": _stage == "failed",
        "preview_images_count": len(trial.preview_images or {}),
        "story_title": trial.story_title,
        "generation_progress": trial.generation_progress,
    }


@router.get("/{trial_id}/preview", response_model=PreviewResponse)
async def get_trial_preview(
    trial_id: str,
    db: DbSession,
    x_trial_token: str | None = Header(None, alias="X-Trial-Token"),
) -> PreviewResponse:
    """Get trial preview data (story + 3 images)."""
    result = await db.execute(select(StoryPreview).where(StoryPreview.id == uuid.UUID(trial_id)))
    trial = result.scalar_one_or_none()

    if not trial:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trial bulunamadı")

    _verify_trial_access(trial, x_trial_token)

    if trial.status not in [
        PreviewStatus.PREVIEW_GENERATED.value,
        PreviewStatus.PAYMENT_PENDING.value,
        PreviewStatus.COMPLETING.value,
        PreviewStatus.COMPLETED.value,
    ]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Preview henüz hazır değil. Status: {trial.status}",
        )

    # Sanitize story_pages: strip visual_prompt from public response
    sanitized_pages = []
    for p in (trial.story_pages or []):
        if isinstance(p, dict):
            sanitized_pages.append({
                "page_number": p.get("page_number"),
                "text": p.get("text", ""),
                "visual_prompt": "",  # Never expose AI prompts to client
            })

    return PreviewResponse(
        success=True,
        trial_id=str(trial.id),
        status=trial.status,
        story_title=trial.story_title,
        story_pages=sanitized_pages,
        preview_images=trial.preview_images or {},
        child_name=trial.child_name,
        product_name=trial.product_name,
        product_price=float(trial.product_price) if trial.product_price else None,
    )


# ============ PHASE 2: Complete Trial ============


@router.post("/complete", response_model=TrialResponse)
async def complete_trial(
    request: CompleteTrialRequest,
    background_tasks: BackgroundTasks,
    db: DbSession,
    current_user: CurrentUserOptional = None,
    x_trial_token: str | None = Header(None, alias="X-Trial-Token"),
) -> TrialResponse:
    """
    Complete a trial after payment - Phase 2.

    Security: Validates ownership via X-Trial-Token AND that payment was
    actually completed (via promo code covering 100%, or verified Iyzico
    payment on the linked Order).
    If the trial has no lead_user_id and the caller is authenticated,
    links the trial to that user so it appears under "Siparişlerim".
    """
    try:
        import secrets

        logger.info(
            "COMPLETE_TRIAL_CALLED",
            trial_id=request.trial_id,
            has_promo=bool(request.promo_code),
            has_email=bool(request.parent_email),
            payment_ref=request.payment_reference,
        )

        try:
            trial_uuid = uuid.UUID(request.trial_id)
        except ValueError:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Geçersiz trial ID formatı")

        trial_service = get_trial_service(db)

        result = await db.execute(
            select(StoryPreview).where(StoryPreview.id == trial_uuid)
        )
        trial = result.scalar_one_or_none()

        if not trial:
            logger.error("COMPLETE_TRIAL_NOT_FOUND", trial_id=request.trial_id)
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trial bulunamadı")

        _verify_trial_access(trial, x_trial_token)

        # Link trial to logged-in user so it appears in "Siparişlerim" (my-trials include_paid)
        if current_user and trial.lead_user_id is None:
            trial.lead_user_id = current_user.id
            logger.info(
                "COMPLETE_TRIAL_LINKED_TO_USER",
                trial_id=request.trial_id,
                user_id=str(current_user.id),
            )

        # ── PAYMENT VERIFICATION ──
        # Only allow completion if:
        # 1. A valid promo code that covers %100 of the cost is provided, OR
        # 2. The linked Order is in PAID status (Iyzico payment verified)
        payment_ref = (request.payment_reference or "").strip()
        is_free_order = False

        if payment_ref.startswith("promo:"):
            # Will be validated below in the promo section — must result in 0 TL
            is_free_order = True
        elif payment_ref.startswith("iyzico_paid:"):
            # Payment was verified via POST /trials/{id}/verify-payment
            # Check that stored payment_reference is also iyzico_paid (not pending)
            stored_ref = (trial.payment_reference or "").strip()
            
            # Extract tokens for comparison (URL encoding may differ)
            provided_token = payment_ref[len("iyzico_paid:"):]
            stored_token = stored_ref[len("iyzico_paid:"):] if stored_ref.startswith("iyzico_paid:") else ""
            
            logger.info(
                "COMPLETE_TRIAL_PAYMENT_REF_CHECK",
                trial_id=request.trial_id,
                stored_starts_with_iyzico=stored_ref.startswith("iyzico_paid:"),
                tokens_match=provided_token == stored_token,
                # NOTE: Token içeriği güvenlik nedeniyle loglanmıyor
            )
            
            if not stored_ref.startswith("iyzico_paid:"):
                # Still pending or not yet verified
                logger.warning(
                    "COMPLETE_TRIAL_PAYMENT_NOT_VERIFIED",
                    trial_id=request.trial_id,
                    stored_ref_prefix=stored_ref[:20],
                )
                raise HTTPException(
                    status_code=status.HTTP_402_PAYMENT_REQUIRED,
                    detail="Ödeme henüz doğrulanmadı. Lütfen ödemenin tamamlandığını kontrol edin.",
                )
            
            # Token comparison — allow if tokens match
            if provided_token and stored_token and provided_token != stored_token:
                logger.warning(
                    "COMPLETE_TRIAL_PAYMENT_REF_MISMATCH",
                    trial_id=request.trial_id,
                    provided=provided_token[:30],
                    stored=stored_token[:30],
                )
                raise HTTPException(
                    status_code=status.HTTP_402_PAYMENT_REQUIRED,
                    detail="Ödeme doğrulanamadı. Lütfen tekrar deneyin.",
                )

        else:
            # Unknown payment reference — reject
            logger.warning(
                "COMPLETE_TRIAL_INVALID_PAYMENT_REF",
                trial_id=request.trial_id,
                payment_ref=payment_ref,
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Geçersiz ödeme referansı.",
            )

        logger.info(
            "COMPLETE_TRIAL_FOUND",
            trial_id=request.trial_id,
            current_status=trial.status,
            page_count=len(trial.page_images or {}),
        )

        # Verify trial is in correct state
        if trial.status not in [
            PreviewStatus.PREVIEW_GENERATED.value,
            PreviewStatus.PAYMENT_PENDING.value,
        ]:
            logger.warning(
                "COMPLETE_TRIAL_BAD_STATUS",
                trial_id=request.trial_id,
                status=trial.status,
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Trial bu durumda tamamlanamaz: {trial.status}",
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
            subtotal = Decimal(str(trial.product_price or 0))

            try:
                promo = await validate_promo_code(promo_code_str, subtotal, db)
                discount_amount = calculate_discount(promo, subtotal)

                # Eğer bu tamamen ücretsiz bir sipariş ise (promo ile ödeniyor),
                # promo'nun tüm tutarı karşıladığını doğrula
                if is_free_order:
                    final_amount = max(subtotal - discount_amount, Decimal("0"))
                    if final_amount > Decimal("0"):
                        raise HTTPException(
                            status_code=status.HTTP_402_PAYMENT_REQUIRED,
                            detail=f"Kupon kodu toplam tutarı ({subtotal} ₺) karşılamıyor. "
                                   f"Kalan tutar ({final_amount} ₺) için ödeme sayfasından devam edin.",
                        )
                else:
                    # Kısmi promo veya Iyzico sonrası tracking — consume et, limit kontrol yap
                    logger.info(
                        "partial_promo_or_post_iyzico_consume",
                        code=promo_code_str,
                        discount=str(discount_amount),
                        subtotal=str(subtotal),
                        is_free_order=is_free_order,
                    )

                consumed = await consume_promo_code(promo.id, db)
                if not consumed:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Kupon kodunun kullanım limiti dolmuş, lütfen başka bir kod deneyin",
                    )

                logger.info(
                    "promo_code_consumed_in_trial_complete",
                    code=promo.code,
                    discount=str(discount_amount),
                    trial_id=request.trial_id,
                    is_free_order=is_free_order,
                )
            except HTTPException:
                raise
            except Exception as promo_err:
                # Kısmi promo hatalarını sadece log'la, iyzico_paid akışında sipariş bloke etme
                if not is_free_order:
                    logger.warning(
                        "partial_promo_consume_failed_continuing",
                        code=promo_code_str,
                        error=str(promo_err),
                        trial_id=request.trial_id,
                    )
                    promo = None
                    discount_amount = None
                else:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Kupon kodu doğrulanamadı: {str(promo_err)}",
                    ) from promo_err


        # ── Save order-specific fields to trial ──
        if request.parent_name:
            trial.parent_name = request.parent_name
        if request.parent_email:
            trial.parent_email = request.parent_email
        if request.parent_phone:
            trial.parent_phone = request.parent_phone
        if request.dedication_note is not None:
            trial.dedication_note = request.dedication_note
        trial.has_audio_book = request.has_audio_book
        trial.audio_type = request.audio_type
        trial.audio_voice_id = request.audio_voice_id
        trial.voice_sample_url = request.voice_sample_url
        trial.has_coloring_book = request.has_coloring_book  # Boyama kitabı flag

        # Save billing data (may already be set from create-payment, but override if provided)
        if request.billing:
            b = request.billing
            trial.billing_data = {
                "billing_type": b.billing_type,
                "billing_full_name": b.billing_full_name or trial.parent_name,
                "billing_email": b.billing_email or trial.parent_email,
                "billing_phone": b.billing_phone or trial.parent_phone,
                "billing_company_name": b.billing_company_name if b.billing_type == "corporate" else None,
                "billing_tax_id": b.billing_tax_id if b.billing_type == "corporate" else None,
                "billing_tax_office": b.billing_tax_office if b.billing_type == "corporate" else None,
                "billing_address": b.billing_address,
                "use_shipping_address": b.use_shipping_address,
            }
        elif not trial.billing_data:
            # Auto-fill minimal billing from parent info if no billing data exists
            trial.billing_data = {
                "billing_type": "individual",
                "billing_full_name": trial.parent_name,
                "billing_email": trial.parent_email,
                "billing_phone": trial.parent_phone,
            }

        # Promo code snapshot
        if promo:
            trial.promo_code_id = promo.id
            trial.promo_code_text = promo.code
            trial.promo_discount_type = promo.discount_type
            trial.promo_discount_value = promo.discount_value
            trial.discount_applied_amount = discount_amount

        # Ensure confirmation_token exists (for approval email later)
        if not trial.confirmation_token:
            trial.confirmation_token = secrets.token_urlsafe(32)

        await db.commit()
        await db.refresh(trial)

        # Mark payment as completed
        trial = await trial_service.complete_payment(
            uuid.UUID(request.trial_id),
            request.payment_reference,
        )

        # Get remaining prompts from cache (NOT calling Gemini again!)
        remaining_prompts = await trial_service.get_remaining_prompts(uuid.UUID(request.trial_id))

        if not remaining_prompts:
            logger.error(
                "COMPLETE_TRIAL_NO_REMAINING_PROMPTS",
                trial_id=request.trial_id,
                cache_keys=list((getattr(trial, "generated_prompts_cache", None) or {}).keys()),
                existing_pages=list((trial.page_images or {}).keys()),
            )

        logger.info(
            "COMPLETE_TRIAL_PROMPTS_READY",
            trial_id=request.trial_id,
            remaining_count=len(remaining_prompts),
            existing_page_count=len(trial.page_images or {}),
        )

        # Stil: önce cache'teki style_id ile (sızıntı yok), yoksa visual_style_name ile tam eşleşme
        visual_style_modifier = ""
        cache = getattr(trial, "generated_prompts_cache", None) or {}
        style_id = cache.get("style_id")
        if style_id:
            try:
                r = await db.execute(
                    select(VisualStyle).where(VisualStyle.id == uuid.UUID(style_id))
                )
                vs = r.scalar_one_or_none()
                if vs and vs.prompt_modifier:
                    visual_style_modifier = (vs.prompt_modifier or "").strip()
            except (ValueError, TypeError):
                pass
        if not visual_style_modifier and getattr(trial, "visual_style_name", None):
            vs = await _resolve_visual_style_from_db(db, trial.visual_style_name)
            if vs and vs.prompt_modifier:
                visual_style_modifier = (vs.prompt_modifier or "").strip()

        logger.info(
            "Starting completion phase",
            trial_id=request.trial_id,
            remaining_prompts=len(remaining_prompts),
            has_promo=bool(promo),
            has_audio=request.has_audio_book,
        )

        # Try Arq (persistent Redis queue) first, fall back to BackgroundTasks
        _arq_ok_rem = False
        try:
            from app.workers.enqueue import enqueue_trial_remaining

            _arq_rem_id = await enqueue_trial_remaining(
                trial_id=request.trial_id,
                prompts=remaining_prompts,
                product_name=trial.product_name,
                visual_style_modifier=visual_style_modifier,
                child_photo_url=getattr(trial, "child_photo_url", None) or "",
                clothing_description=cache.get("clothing_description", ""),
            )
            if _arq_rem_id:
                _arq_ok_rem = True
                logger.info(
                    "COMPLETE_TRIAL_ARQ_ENQUEUED",
                    trial_id=request.trial_id,
                    arq_job_id=str(_arq_rem_id),
                )
        except Exception as _enq_err:
            logger.warning("Arq enqueue failed for trial remaining", error=str(_enq_err))
        if not _arq_ok_rem:
            # Arq failed — set QUEUE_FAILED so admin can retry
            trial.status = "QUEUE_FAILED"
            trial.admin_notes = (trial.admin_notes or "") + "\nArq enqueue basarisiz. Admin retry gerekli."
            await db.commit()
            logger.critical(
                "COMPLETE_TRIAL_QUEUE_FAILED",
                trial_id=request.trial_id,
            )

        # ── Create Coloring Book Order (if requested) ──
        coloring_order_id = None
        if request.has_coloring_book:
            try:
                coloring_order = await _create_coloring_book_order_from_trial(
                    trial=trial,
                    db=db,
                )
                if coloring_order:
                    coloring_order_id = str(coloring_order.id)
                    logger.info(
                        "Coloring book order created",
                        trial_id=request.trial_id,
                        coloring_order_id=coloring_order_id,
                    )
                    
                    # Enqueue coloring book generation (background task)
                    from app.tasks.generate_coloring_book import generate_coloring_book
                    import asyncio
                    
                    # Create task in background (non-blocking)
                    asyncio.create_task(generate_coloring_book(coloring_order.id, db))
            except Exception as coloring_err:
                logger.error(
                    "Failed to create coloring book order",
                    trial_id=request.trial_id,
                    error=str(coloring_err),
                )
                # Don't fail main order if coloring book creation fails

        return TrialResponse(
            success=True,
            trial_id=request.trial_id,
            status=trial.status,
            message="Ödeme alındı! Kitabınız hazırlanıyor...",
            order_id=coloring_order_id,  # Coloring book order ID (if created)
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to complete trial", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Trial tamamlanamadı: {str(e)}",
        )


async def generate_remaining_images_background(
    trial_id: str,
    prompts: list[dict],
    product_name: str | None = None,
    visual_style_modifier: str = "",
    child_photo_url: str = "",
    clothing_description: str = "",
):
    """Background task to generate remaining pages after payment (dynamic count per product).

    Guarded by _TRIAL_GEN_SEMAPHORE to avoid competing with order tasks.
    """
    logger.info("Trial remaining pages waiting for semaphore slot", trial_id=trial_id)
    async with _TRIAL_GEN_SEMAPHORE:
        logger.info("Trial remaining pages acquired semaphore slot", trial_id=trial_id)
        await _generate_remaining_images_inner(
            trial_id, prompts, product_name,
            visual_style_modifier, child_photo_url, clothing_description,
        )


# ============ INITIATE PAYMENT ============


@router.post("/{trial_id}/initiate-payment")
async def initiate_payment(
    trial_id: str,
    db: DbSession,
    x_trial_token: str | None = Header(None, alias="X-Trial-Token"),
) -> dict:
    """Mark trial as payment pending when user clicks 'Buy'."""
    # Ownership check before initiating payment
    result = await db.execute(select(StoryPreview).where(StoryPreview.id == uuid.UUID(trial_id)))
    _trial_check = result.scalar_one_or_none()
    if not _trial_check:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trial bulunamadı")
    _verify_trial_access(_trial_check, x_trial_token)

    trial_service = get_trial_service(db)
    trial = await trial_service.initiate_payment(uuid.UUID(trial_id))

    if not trial:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trial bulunamadı")

    return {
        "success": True,
        "trial_id": str(trial.id),
        "status": trial.status,
        "product_price": float(trial.product_price) if trial.product_price else None,
    }


# ============ RETRY STUCK TRIAL ============


@router.post("/{trial_id}/retry")
async def retry_stuck_trial(
    trial_id: str,
    background_tasks: BackgroundTasks,
    db: DbSession,
    x_trial_token: str | None = Header(None, alias="X-Trial-Token"),
) -> dict:
    """Re-queue a stuck trial that failed to generate images.

    Works for trials stuck in GENERATING or LEAD_CAPTURED status
    for more than 5 minutes (likely lost due to instance restart).
    """
    from datetime import UTC, datetime, timedelta

    result = await db.execute(select(StoryPreview).where(StoryPreview.id == uuid.UUID(trial_id)))
    trial = result.scalar_one_or_none()

    if not trial:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trial bulunamadi")

    _verify_trial_access(trial, x_trial_token)

    # Only retry stuck trials
    stuck_statuses = {
        PreviewStatus.GENERATING.value,
        PreviewStatus.LEAD_CAPTURED.value,
    }
    if trial.status not in stuck_statuses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Trial durumu '{trial.status}' — yalnizca GENERATING veya LEAD_CAPTURED durumdaki trial'lar yeniden kuyruga alinabilir.",
        )

    # Safety: only retry if trial is older than 5 minutes (avoid double-processing)
    if trial.updated_at and (datetime.now(UTC) - trial.updated_at) < timedelta(minutes=5):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Trial henuz isleniyor olabilir. 5 dakika bekleyip tekrar deneyin.",
        )

    # Decide whether to retry story generation or preview images
    cache = getattr(trial, "generated_prompts_cache", None) or {}
    prompts = cache.get("prompts") or []
    _needs_story = cache.get("pending", False) or not prompts

    _arq_ok_retry = False
    _arq_id: str | None = None

    if _needs_story:
        # Story was never generated (or failed) — re-enqueue story generation
        _request_data = {
            "child_name": trial.child_name,
            "child_age": trial.child_age,
            "child_gender": trial.child_gender,
            "child_photo_url": trial.child_photo_url,
            "scenario_id": cache.get("scenario_id"),
            "scenario_name": trial.scenario_name,
            "visual_style": cache.get("visual_style"),
            "visual_style_name": trial.visual_style_name,
            "learning_outcomes": trial.learning_outcomes,
            "page_count": cache.get("page_count") or 16,
            "magic_items": cache.get("magic_items"),
            "product_id": str(trial.product_id) if trial.product_id else None,
            "product_name": trial.product_name,
        }

        # Reset progress
        trial.generation_progress = {
            "stage": "queued",
            "message": "Hikaye yeniden kuyruğa alındı...",
        }
        await db.commit()

        try:
            from app.workers.enqueue import enqueue_trial_story

            _arq_id = await enqueue_trial_story(
                trial_id=trial_id,
                request_data=_request_data,
            )
            if _arq_id:
                _arq_ok_retry = True
        except Exception as _enq_err:
            logger.warning("Arq enqueue failed for trial story retry", error=str(_enq_err))
        if not _arq_ok_retry:
            background_tasks.add_task(
                _generate_trial_story_inner,
                trial_id=trial_id,
                request_data=_request_data,
            )

        _retry_type = "story"
    else:
        # Story exists but preview images missing — re-enqueue image generation
        preview_prompts = prompts[:3]

        try:
            from app.workers.enqueue import enqueue_trial_preview

            _arq_id = await enqueue_trial_preview(
                trial_id=trial_id,
                prompts=preview_prompts,
                child_photo_url=getattr(trial, "child_photo_url", None),
                visual_style=cache.get("visual_style"),
                product_name=getattr(trial, "product_name", None),
                story_title=trial.story_title or "",
                clothing_description=cache.get("clothing_description", ""),
                visual_style_name=getattr(trial, "visual_style_name", None),
            )
            if _arq_id:
                _arq_ok_retry = True
        except Exception as _enq_err:
            logger.warning("Arq enqueue failed for trial retry", error=str(_enq_err))
        if not _arq_ok_retry:
            background_tasks.add_task(
                generate_preview_images_background,
                trial_id=trial_id,
                prompts=preview_prompts,
                child_photo_url=getattr(trial, "child_photo_url", None),
                visual_style=cache.get("visual_style"),
                product_name=getattr(trial, "product_name", None),
                story_title=trial.story_title or "",
                clothing_description=cache.get("clothing_description", ""),
                visual_style_name=getattr(trial, "visual_style_name", None),
            )

        _retry_type = "images"

    logger.info(
        "TRIAL_RETRY_ENQUEUED",
        trial_id=trial_id,
        retry_type=_retry_type,
        via="arq" if _arq_ok_retry else "background_tasks",
    )

    return {
        "success": True,
        "trial_id": trial_id,
        "message": "Trial yeniden kuyruğa alındı.",
        "retry_type": _retry_type,
        "queue": "arq" if _arq_ok_retry else "background_tasks",
    }


# ============ TRIAL PAYMENT: IYZICO CHECKOUT ============


@router.post("/{trial_id}/create-payment")
async def create_trial_payment(
    trial_id: str,
    request: "Request",
    db: DbSession,
    x_trial_token: str | None = Header(None, alias="X-Trial-Token"),
    body: CreatePaymentRequest | None = None,
) -> dict:
    """Create an Iyzico checkout session for a trial (Phase 2 payment).

    Returns payment_url for redirect to Iyzico hosted checkout page.
    Supports optional promo_code in request body for discounted payments.
    """
    try:
        trial_uuid = uuid.UUID(trial_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Gecersiz trial ID")

    result = await db.execute(select(StoryPreview).where(StoryPreview.id == trial_uuid))
    trial = result.scalar_one_or_none()

    if not trial:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trial bulunamadi")

    _verify_trial_access(trial, x_trial_token)

    # Save billing data before payment
    if body and body.billing:
        b = body.billing
        trial.billing_data = {
            "billing_type": b.billing_type,
            "billing_full_name": b.billing_full_name,
            "billing_email": b.billing_email,
            "billing_phone": b.billing_phone,
            "billing_company_name": b.billing_company_name if b.billing_type == "corporate" else None,
            "billing_tax_id": b.billing_tax_id if b.billing_type == "corporate" else None,
            "billing_tax_office": b.billing_tax_office if b.billing_type == "corporate" else None,
            "billing_address": b.billing_address,
            "use_shipping_address": b.use_shipping_address,
        }
        await db.commit()
        await db.refresh(trial)

    client_ip = (
        request.headers.get("x-forwarded-for", "").split(",")[0].strip()
        or (request.client.host if request.client else "127.0.0.1")
    )
    promo_code_str = ((body.promo_code if body else None) or "").strip().upper()

    return await create_iyzico_checkout(trial, db, client_ip, promo_code_str)

@router.post("/{trial_id}/verify-payment")
async def verify_trial_payment(
    trial_id: str,
    request: VerifyTrialPaymentRequest,
    db: DbSession,
    x_trial_token: str | None = Header(None, alias="X-Trial-Token"),
) -> dict:
    """Verify Iyzico payment result for a trial after user returns from Iyzico page.

    Marks trial payment as verified so complete_trial can proceed.
    """
    try:
        trial_uuid = uuid.UUID(trial_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Gecersiz trial ID")

    result = await db.execute(select(StoryPreview).where(StoryPreview.id == trial_uuid))
    trial = result.scalar_one_or_none()

    if not trial:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trial bulunamadi")

    _verify_trial_access(trial, x_trial_token)

    return await verify_iyzico_payment(trial, request.token, db)


# ============ ADD COLORING BOOK (UPSELL) ============

@router.post("/{trial_id}/add-coloring-book")
async def add_coloring_book_to_trial(
    trial_id: str,
    request: "Request",
    db: DbSession,
    x_trial_token: str | None = Header(None, alias="X-Trial-Token"),
) -> dict:
    """
    Upsell endpoint: Add a coloring book to an already purchased (or completing) trial.
    Creates an Iyzico payment intent specifically for the coloring book price.
    """
    from decimal import Decimal
    import iyzipay
    from app.config import settings
    from app.models.coloring_book import ColoringBookProduct

    try:
        trial_uuid = uuid.UUID(trial_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Geçersiz trial ID")

    result = await db.execute(select(StoryPreview).where(StoryPreview.id == trial_uuid))
    trial = result.scalar_one_or_none()

    if not trial:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trial bulunamadı")

    _verify_trial_access(trial, x_trial_token)

    # Allow upsell if it's already generated or confirmed
    allowed_statuses = [
        PreviewStatus.COMPLETING.value,
        PreviewStatus.COMPLETED.value,
        PreviewStatus.CONFIRMATION_PENDING.value,
        PreviewStatus.CONFIRMED.value,
    ]
    if trial.status not in allowed_statuses and not trial.payment_reference:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bu işlem için ana siparişin ödenmiş olması gerekir.",
        )
        
    if trial.has_coloring_book:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bu siparişte zaten boyama kitabı mevcut.",
        )

    try:
        _iyzico_opts = get_iyzico_options()
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc

    # Get active coloring book config for pricing
    config_result = await db.execute(
        select(ColoringBookProduct).where(ColoringBookProduct.active == True).limit(1)
    )
    coloring_config = config_result.scalar_one_or_none()
    
    if not coloring_config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Boyama ürünü şu anda aktif değil.",
        )
        
    coloring_book_price = coloring_config.discounted_price or coloring_config.base_price
    
    if coloring_book_price <= Decimal("0"):
         raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Geçersiz fiyat yapılandırması.",
        )

    options = _iyzico_opts

    buyer_name = (trial.parent_name or "Misafir Kullanıcı").strip()
    buyer_email = (trial.parent_email or "misafir@benimmasalim.com").strip()
    buyer_phone = (trial.parent_phone or "").strip()
    name_parts = buyer_name.split(" ", 1)
    first_name = name_parts[0] if name_parts else "Misafir"
    last_name = name_parts[1] if len(name_parts) > 1 else "."

    client_ip = (
        request.headers.get("x-forwarded-for", "").split(",")[0].strip()
        or (request.client.host if request.client else "127.0.0.1")
    )

    buyer = {
        "id": str(trial.id),
        "name": first_name,
        "surname": last_name,
        "email": buyer_email,
        "identityNumber": "11111111111",
        "registrationAddress": "Adres belirtilmedi",
        "city": "Istanbul",
        "country": "Turkey",
        "ip": client_ip,
    }
    if buyer_phone:
        buyer["gsmNumber"] = buyer_phone

    address = {"contactName": buyer_name, "city": "Istanbul", "country": "Turkey", "address": "Adres belirtilmedi"}

    # We use a distinct callback for upsell to process it separately
    callback_url = f"{settings.frontend_url}/api/payment/callback-upsell?trialId={trial.id}&type=coloring"

    # Distinct group ID for the upsell payment
    basket_id = f"{str(trial.id)[:12]}_up"
    
    iyzico_request = {
        "locale": "tr",
        "conversationId": f"{trial.id}_upsell_cb",
        "price": str(coloring_book_price),
        "paidPrice": str(coloring_book_price),
        "currency": "TRY",
        "basketId": basket_id,
        "paymentGroup": "PRODUCT",
        "callbackUrl": callback_url,
        "enabledInstallments": [1, 2, 3, 6],
        "buyer": buyer,
        "shippingAddress": address,
        "billingAddress": address,
        "basketItems": [
            {
                "id": basket_id,
                "name": "Ekleme: Boyama Kitabı",
                "category1": "Kitap",
                "category2": "Ek Özellik",
                "itemType": "VIRTUAL",
                "price": str(coloring_book_price),
            }
        ],
    }

    try:
        checkout_form = iyzipay.CheckoutFormInitialize().create(iyzico_request, options)
        import json as _json
        result_dict = _json.loads(checkout_form.read().decode("utf-8"))
    except Exception as exc:
        logger.error("TRIAL_UPSELL_CHECKOUT_ERROR", trial_id=trial_id, error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Ek ürün ödeme sayfası oluşturulamadı.",
        ) from exc

    if result_dict.get("status") != "success":
        error_msg = result_dict.get("errorMessage", "Bilinmeyen hata")
        logger.error("TRIAL_UPSELL_CHECKOUT_FAILED", trial_id=trial_id, error=error_msg)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Ödeme sayfası oluşturulamadı: {error_msg}",
        )

    # Note: We do NOT overwrite trial.payment_reference here, as that represents the MAIN payment check.
    # The callback will verify using Iyzico directly and update `has_coloring_book` = True.

    payment_page_url = result_dict.get("paymentPageUrl", "")

    logger.info(
        "TRIAL_UPSELL_CHECKOUT_CREATED",
        trial_id=trial_id,
        upsell_type="coloring_book",
        price=str(coloring_book_price),
    )

    return {
        "success": True,
        "payment_url": payment_page_url,
        "trial_id": trial_id,
    }


@router.post("/add-coloring-book-callback")
async def add_coloring_book_callback(
    request: "Request",
    db: DbSession,
) -> dict:
    """
    Callback for the upsell payment. Validates payment with Iyzico,
    sets has_coloring_book = True on the trial, and queues generation.
    """
    import json as _json
    import iyzipay
    from app.config import settings
    from urllib.parse import parse_qs
    from fastapi.responses import RedirectResponse
    
    # trialId might be in query params from callbackUrl
    query_params = parse_qs(str(request.query_params))
    trial_id_list = query_params.get("trialId")
    trial_id_str = trial_id_list[0] if trial_id_list else None

    # Try JSON first (sometimes webhooks are JSON)
    try:
        body_bytes = await request.body()
        body_str = body_bytes.decode()
        if body_str.startswith("{"):
             data = _json.loads(body_str)
             token = data.get("token")
        else:
            # Iyzico sends data as form URL encoded
            form_data = await request.form()
            token = form_data.get("token")
    except Exception:
        token = None
        
    if not token or not trial_id_str:
        logger.error("UPSELL_CALLBACK_MISSING_DATA", token=token, trial_id=trial_id_str)
        return RedirectResponse(url=f"{settings.frontend_url}/payment-failed?error=Eksik_parametre")
        
    try:
        trial_uuid = uuid.UUID(trial_id_str)
    except ValueError:
        return RedirectResponse(url=f"{settings.frontend_url}/payment-failed?error=Gecersiz_ID")

    try:
        options = get_iyzico_options()
    except ValueError:
        return RedirectResponse(url=f"{settings.frontend_url}/payment-failed?error=Sistem_Hatasi")

    try:
        verify_result = iyzipay.CheckoutForm().retrieve(
            {"locale": "tr", "token": token},
            options,
        )
        result_dict = _json.loads(verify_result.read().decode("utf-8"))
    except Exception as exc:
        logger.error("UPSELL_IYZICO_VERIFY_ERROR", trial_id=trial_id_str, error=str(exc))
        return RedirectResponse(url=f"{settings.frontend_url}/payment-failed?error=Dogrulama_Hatasi")

    iyzico_status = result_dict.get("paymentStatus")

    if iyzico_status != "SUCCESS":
        error_msg = result_dict.get("errorMessage", "Ödeme başarısız")
        logger.warning("UPSELL_IYZICO_VERIFY_FAILED", trial_id=trial_id_str, status=iyzico_status, error=error_msg)
        return RedirectResponse(url=f"{settings.frontend_url}/payment-failed?error=Odeme_Basarisiz")

    # Payment successful. Update trial.
    result = await db.execute(select(StoryPreview).where(StoryPreview.id == trial_uuid))
    trial = result.scalar_one_or_none()
    
    if not trial:
        logger.error("UPSELL_CALLBACK_TRIAL_NOT_FOUND", trial_id=trial_id_str)
        return RedirectResponse(url=f"{settings.frontend_url}/payment-failed?error=Siparis_Bulunamadi")
        
    if trial.has_coloring_book:
        logger.info("UPSELL_ALREADY_PROCESSED", trial_id=trial_id_str)
    else:
        trial.has_coloring_book = True
        trial.admin_notes = (trial.admin_notes or "") + f"\n\nUPSELL_COLORING_BOOK_PAID: {token}"
        await db.commit()
        
        # Enqueue the coloring book generation task
        try:
            from app.workers.enqueue import enqueue_job
            logger.info("Enqueuing trial coloring book generation from upsell", trial_id=trial_id_str)
            await enqueue_job("generate_coloring_book_for_trial", trial_id=str(trial_uuid))
        except Exception as _cb_err:
            logger.error(
                "Failed to enqueue trial coloring book generation from upsell",
                trial_id=trial_id_str,
                error=str(_cb_err)
            )
            trial.admin_notes = (trial.admin_notes or "") + f"\n\nBoyama kitabi olusturma siraya alinamadi (upsell): {str(_cb_err)}"
            await db.commit()
            
    # Redirect to a success page
    return RedirectResponse(url=f"{settings.frontend_url}/payment-success?trialId={trial.id}&upsell=coloring")

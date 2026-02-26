"""Try Before You Buy - Trial API Endpoints.

Phase 1: Generate full story + 3 preview images (FREE)
Phase 2: After payment, generate remaining 13 images (PAID)
"""

import asyncio
import uuid

import structlog
from fastapi import APIRouter, BackgroundTasks, Header, HTTPException, Request, status
from pydantic import BaseModel, EmailStr, Field, field_validator
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import DbSession
from app.config import get_settings
from app.core.url_validator import validate_image_url
from app.models.story_preview import PreviewStatus, StoryPreview
from app.models.visual_style import VisualStyle
from app.models.product import Product
from app.models.scenario import Scenario
from app.models.order import Order, OrderStatus
from app.services.trial_service import get_trial_service

logger = structlog.get_logger()
router = APIRouter()
_V3_BLOCK_MSG = "V2_LABEL_BLOCKED: expected v3"
_TRIAL_CREATE_ROUTE = "/api/v1/trials/create"

_settings = get_settings()

# Trial background tasks get their own semaphore so they are never blocked by
# long-running order jobs.  Default: 3 slots (trials are lightweight: 3 images).
_TRIAL_GEN_SEMAPHORE = asyncio.Semaphore(_settings.trial_concurrency_slots)


async def _resolve_visual_style_from_db(
    db,
    visual_style_name: str | None,
) -> "VisualStyle | None":
    """Resolve VisualStyle by name, falling back to display_name if needed.

    Frontend may send display_name (e.g. 'Pastel Rüya') while DB name column
    stores a different value (e.g. 'Yumuşak Pastel'). This helper tries both.
    """
    if not visual_style_name:
        return None

    vs = (
        await db.execute(select(VisualStyle).where(VisualStyle.name == visual_style_name))
    ).scalar_one_or_none()

    if vs:
        return vs

    # Fallback: frontend may have sent display_name instead of name
    vs = (
        await db.execute(
            select(VisualStyle).where(VisualStyle.display_name == visual_style_name)
        )
    ).scalar_one_or_none()

    if vs:
        logger.info(
            "VisualStyle resolved via display_name fallback",
            searched=visual_style_name,
            resolved_name=vs.name,
        )
    else:
        logger.warning(
            "VisualStyle NOT found by name or display_name",
            searched=visual_style_name,
        )

    return vs


def _mask_email(email: str | None) -> str:
    """Mask email for safe logging: us***@domain.com"""
    if not email or "@" not in email:
        return "***"
    local, domain = email.split("@", 1)
    return f"{local[:2]}***@{domain}"


# ============ SCHEMAS ============


class StoryPageInput(BaseModel):
    """Story page from frontend."""

    page_number: int
    text: str
    visual_prompt: str
    negative_prompt: str | None = None
    v3_composed: bool | None = None
    page_type: str | None = None
    composer_version: str | None = None
    pipeline_version: str | None = None


class CreateTrialRequest(BaseModel):
    """Request to create a trial (Phase 1)."""

    # Lead info
    user_id: str | None = None
    parent_name: str = Field(..., min_length=2)
    parent_email: EmailStr
    parent_phone: str | None = None

    # Child info
    child_name: str
    child_age: int
    child_gender: str | None = None
    child_photo_url: str | None = None

    # Product info
    product_id: str | None = None
    product_name: str | None = None
    product_price: float | None = None

    # Story info
    scenario_name: str | None = None
    scenario_id: str | None = None
    visual_style: str | None = None
    visual_style_name: str | None = None
    learning_outcomes: list[str] | None = None

    # Custom variables
    custom_variables: dict | None = None

    # Explicit page count override (takes priority over product default)
    page_count: int | None = Field(default=None, ge=4, le=64)

    # V3: Magic items (sihirli malzemeler)
    magic_items: list[str] | None = None

    @field_validator("child_photo_url")
    @classmethod
    def validate_photo_url(cls, v: str | None) -> str | None:
        """Validate child photo URL to prevent SSRF."""
        return validate_image_url(v, field_name="child_photo_url")


class TrialResponse(BaseModel):
    """Response after creating/updating trial."""

    success: bool
    trial_id: str
    status: str
    message: str
    preview_url: str | None = None
    trial_token: str | None = None
    used_page_count: int | None = None
    order_id: str | None = None  # Main story order ID (if created)


class PreviewResponse(BaseModel):
    """Response with preview data."""

    success: bool
    trial_id: str
    status: str
    story_title: str
    story_pages: list[dict]
    preview_images: dict  # {page_num: url}
    child_name: str
    product_name: str | None
    product_price: float | None


class CompleteTrialRequest(BaseModel):
    """Request to complete a trial after payment."""

    trial_id: str
    payment_reference: str  # "promo:{CODE}" veya iyzico ref
    # Siparis verileri (odeme sonrasi eklenen)
    parent_name: str | None = None
    parent_email: EmailStr | None = None
    parent_phone: str | None = None
    dedication_note: str | None = None
    promo_code: str | None = None
    has_audio_book: bool = False
    audio_type: str | None = None
    audio_voice_id: str | None = None
    voice_sample_url: str | None = None
    has_coloring_book: bool = False  # Boyama kitabı flag


# ============ PHASE 1: Create Trial & Generate Preview ============


@router.post("/create", response_model=TrialResponse)
async def create_trial(
    request: CreateTrialRequest,
    background_tasks: BackgroundTasks,
    db: DbSession,
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
        trial_service = _get_ts(db)
        trial = await trial_service.create_trial_lead(
            lead_user_id=uuid.UUID(request.user_id) if request.user_id else None,
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


async def _generate_trial_story_inner(
    trial_id: str,
    request_data: dict,
) -> None:
    """Generate story via Gemini and enqueue preview image generation.

    Runs inside an Arq worker (or as a FastAPI BackgroundTask fallback).
    """
    from uuid import UUID as _UUID

    from sqlalchemy import select as _sel

    from app.core.database import async_session_factory
    from app.models.learning_outcome import LearningOutcome
    from app.models.scenario import Scenario
    from app.services.ai.gemini_service import PageManifest, gemini_service
    from app.services.trial_service import get_trial_service

    child_name = request_data["child_name"]
    child_age = request_data["child_age"]
    child_gender = request_data.get("child_gender")
    scenario_id = request_data.get("scenario_id")
    scenario_name = request_data.get("scenario_name")
    visual_style = request_data.get("visual_style")
    visual_style_name = request_data.get("visual_style_name")
    learning_outcomes = request_data.get("learning_outcomes") or []
    page_count = request_data.get("page_count") or 16
    magic_items = request_data.get("magic_items")
    child_photo_url = request_data.get("child_photo_url")
    product_name = request_data.get("product_name")

    async with async_session_factory() as db:
        try:
            trial_svc = get_trial_service(db)
            _trial_uuid = _UUID(trial_id)
            _trial = (
                await db.execute(_sel(StoryPreview).where(StoryPreview.id == _trial_uuid))
            ).scalar_one_or_none()

            # ── Idempotency: skip Gemini if story already generated (Arq retry) ──
            _story_already_done = (
                _trial
                and _trial.story_pages
                and len(_trial.story_pages) > 0
                and not (_trial.generated_prompts_cache or {}).get("pending")
            )
            if _story_already_done:
                logger.info(
                    "Story already generated (Arq retry), skipping Gemini",
                    trial_id=trial_id,
                )
                _cache = _trial.generated_prompts_cache or {}
                _retry_prompts = _select_preview_prompts(_cache.get("prompts") or [], num_inner=2)
                _arq_ok = False
                try:
                    from app.workers.enqueue import enqueue_trial_preview

                    _arq_job_id = await enqueue_trial_preview(
                        trial_id=trial_id,
                        prompts=_retry_prompts,
                        child_photo_url=child_photo_url,
                        visual_style=visual_style,
                        product_name=product_name,
                        story_title=_trial.story_title or "",
                        clothing_description=_cache.get("clothing_description", ""),
                        visual_style_name=visual_style_name,
                    )
                    if _arq_job_id:
                        _arq_ok = True
                except Exception as _enq_err:
                    logger.warning("Arq enqueue failed on retry", error=str(_enq_err))

                if not _arq_ok:
                    await _generate_preview_images_inner(
                        trial_id=trial_id,
                        prompts=_retry_prompts,
                        child_photo_url=child_photo_url,
                        visual_style=visual_style,
                        product_name=product_name,
                        story_title=_trial.story_title or "",
                        clothing_description=_cache.get("clothing_description", ""),
                        visual_style_name=visual_style_name,
                    )
                return

            # Update progress
            if _trial:
                _trial.generation_progress = {
                    "stage": "generating_story",
                    "message": "Hikaye oluşturuluyor...",
                }
                await db.commit()

            # ── Fetch scenario from DB ──
            scenario = None
            if scenario_id:
                try:
                    _r = await db.execute(_sel(Scenario).where(Scenario.id == _UUID(scenario_id)))
                    scenario = _r.scalar_one_or_none()
                except Exception:
                    pass
            if not scenario and scenario_name:
                name_stripped = (scenario_name or "").strip()
                if name_stripped:
                    try:
                        _r = await db.execute(_sel(Scenario).where(Scenario.name == name_stripped))
                        scenario = _r.scalar_one_or_none()
                    except Exception:
                        pass
                    if not scenario:
                        try:
                            _r = await db.execute(
                                _sel(Scenario)
                                .where(Scenario.name.ilike(f"%{name_stripped}%"))
                                .order_by(Scenario.name)
                                .limit(1)
                            )
                            scenario = _r.scalar_one_or_none()
                        except Exception:
                            pass
            if not scenario:
                class _MockScenario:
                    def __init__(self, name, description):
                        self.id = scenario_id
                        self.name = name
                        self.description = description
                        self.story_prompt_tr = None
                        self.ai_prompt_template = None
                        self.cover_prompt_template = None
                        self.page_prompt_template = None
                        self.location_en = None
                        self.flags = None
                        self.outfit_girl = None
                        self.outfit_boy = None

                scenario = _MockScenario(scenario_name or "Macera", "Büyülü bir macera hikayesi")

            # ── Fetch learning outcomes ──
            outcomes: list = []
            if learning_outcomes:
                lo_result = await db.execute(
                    _sel(LearningOutcome).where(
                        LearningOutcome.name.in_(learning_outcomes),
                        LearningOutcome.is_active == True,  # noqa: E712
                    )
                )
                outcomes = list(lo_result.scalars().all())
                found_names = {o.name for o in outcomes}
                missing = [n for n in learning_outcomes if n not in found_names]
                if missing:
                    class _FallbackOutcome:
                        def __init__(self, name: str):
                            self.name = name
                            self.ai_prompt = name
                            self.ai_prompt_instruction = None
                            self.banned_words_tr = None

                        @property
                        def effective_ai_instruction(self) -> str:
                            return self.ai_prompt_instruction or self.ai_prompt or self.name

                    outcomes.extend(_FallbackOutcome(n) for n in missing)

            # Trial preview için yüz analizi gerekmez — görsel üretimde yapılacak
            _visual_char_desc = f"a {child_age}-year-old child named {child_name}"

            # ── Resolve visual style overrides for story pre-compose ──
            _story_leading_prefix_override: str | None = None
            _story_style_block_override: str | None = None
            if visual_style_name:
                try:
                    from app.api.v1.admin.visual_styles import _resolve_visual_style_from_db as _rvs
                    _story_vs = await _rvs(db, visual_style_name)
                    if _story_vs:
                        _story_leading_prefix_override = (_story_vs.leading_prefix_override or "").strip() or None
                        _story_style_block_override = (_story_vs.style_block_override or "").strip() or None
                except Exception:
                    pass

            # ── Resolve scenario outfit (gender-specific, scenario-first) ──
            # getattr ile None-safe okuma; .strip() ile boşluk temizleme
            _scenario_outfit_girl = (getattr(scenario, "outfit_girl", None) or "").strip()
            _scenario_outfit_boy = (getattr(scenario, "outfit_boy", None) or "").strip()
            if child_gender == "kiz":
                _scenario_outfit = _scenario_outfit_girl or _scenario_outfit_boy
            else:
                _scenario_outfit = _scenario_outfit_boy or _scenario_outfit_girl
            logger.info(
                "scenario_outfit_resolved",
                scenario_id=scenario_id,
                child_gender=child_gender,
                outfit=_scenario_outfit[:60] if _scenario_outfit else "(none)",
            )

            # ── Generate story via Gemini ──
            story_response, final_pages, fixed_outfit, blueprint_json = (
                await gemini_service.generate_story_structured(
                    scenario=scenario,
                    requested_version="v3",
                    child_name=child_name,
                    child_age=child_age,
                    child_gender=child_gender,
                    outcomes=outcomes,
                    visual_style=visual_style or "children's book illustration, soft colors",
                    visual_character_description=_visual_char_desc,
                    page_count=page_count,
                    magic_items=magic_items,
                    leading_prefix_override=_story_leading_prefix_override,
                    style_block_override=_story_style_block_override,
                    fixed_outfit=_scenario_outfit,
                    generate_visual_prompts=False,  # Two-phase: story text only first
                )
            )

            # ── Deterministic title ──
            from app.api.v1.orders import _force_deterministic_title

            story_response.title = _force_deterministic_title(
                child_name=child_name,
                scenario_name=scenario_name or getattr(scenario, "name", ""),
                original_title=story_response.title,
            )

            # ── Build serializable pages ──
            story_pages: list[dict] = []
            generated_prompts: list[dict] = []
            for page in final_pages:
                page_text = page.text
                if page.page_number == 0:
                    # Kapak sayfasında her zaman başlık kullan; AI hikaye metni koymuş olsa bile override et.
                    page_text = story_response.title or child_name or ""
                
                # Two-phase: visual_prompt may be empty string if generate_visual_prompts=False
                visual_prompt_value = page.visual_prompt if page.visual_prompt else ""
                
                page_dict: dict = {
                    "page_number": page.page_number,
                    "text": page_text,
                    "visual_prompt": visual_prompt_value,
                    "page_type": getattr(page, "page_type", "inner"),
                    "page_index": getattr(page, "page_index", 0),
                    "story_page_number": getattr(page, "story_page_number", None),
                    "composer_version": getattr(page, "composer_version", "v3"),
                    "pipeline_version": getattr(page, "pipeline_version", "v3"),
                }
                if page.v3_composed:
                    page_dict["negative_prompt"] = page.negative_prompt
                    page_dict["v3_composed"] = True
                if getattr(page, "v3_enhancement_skipped", False):
                    page_dict["v3_enhancement_skipped"] = True
                story_pages.append(page_dict)
                generated_prompts.append(page_dict)

            # ── V3 pipeline validation ──
            from app.core.build_meta import get_commit_hash
            from app.core.pipeline_version import (
                prompt_builder_name_for_version,
                require_v3_pipeline,
            )

            _job_id = str(uuid.uuid4())
            _non_v3 = [
                p for p in final_pages
                if getattr(p, "pipeline_version", "") != "v3"
                or getattr(p, "composer_version", "") != "v3"
            ]
            _pipeline_ver = "v3"
            if _non_v3:
                logger.error(_V3_BLOCK_MSG, route="worker", job_id=_job_id, non_v3_pages=len(_non_v3))
                raise ValueError(_V3_BLOCK_MSG)
            require_v3_pipeline(pipeline_version=_pipeline_ver, job_id=_job_id, route="worker")

            logger.info(
                "PIPELINE_AUDIT",
                job_id=_job_id,
                route="worker/generate_trial_story",
                pipeline_version=_pipeline_ver,
                enhancement_skipped=any(getattr(p, "v3_enhancement_skipped", False) for p in final_pages),
                template_id=str(getattr(scenario, "id", "") or ""),
                prompt_builder_name=prompt_builder_name_for_version(_pipeline_ver),
                commit_hash=get_commit_hash(),
            )

            # ── Page manifest ──
            page_manifest = PageManifest.from_final_pages(
                title=story_response.title,
                child_name=child_name,
                final_pages=final_pages,
                pipeline_version=_pipeline_ver,
                include_dedication=True,
                include_backcover=True,
            )

            # ── QA checks ──
            from app.prompt_engine.qa_checks import run_qa_checks
            from app.prompt_engine.scenario_bible import normalize_location_key_for_anchors

            _loc_key = (
                getattr(scenario, "theme_key", None)
                or getattr(scenario, "location_en", "")
                or getattr(scenario, "name", "")
            )
            # Exclude backcover page from QA — its closing scene may not reference location keyword
            _qa_prompts = [p for p in generated_prompts if p.get("page_type") != "backcover"]
            qa_report = run_qa_checks(
                final_pages=_qa_prompts,
                manifest_pages=[e.model_dump() for e in page_manifest.pages],
                expected_story_pages=page_count,
                child_name=child_name,
                expected_location_key=normalize_location_key_for_anchors(str(_loc_key or "")),
            )
            if not qa_report["passed"]:
                critical = qa_report.get("checks", {})
                block = (
                    critical.get("no_text_instructions", {}).get("failures")
                    or critical.get("no_text_suffix", {}).get("failures")
                    or critical.get("page_count", {}).get("failures")
                    or critical.get("location_contamination", {}).get("failures")
                )
                if block:
                    logger.error("QA_CHECK_FAIL in worker", trial_id=trial_id, failures=qa_report["failures"][:10])
                    raise ValueError("QA check failed — story generation rejected")
                logger.warning("QA checks found issues (non-blocking)", failures=qa_report["failures"][:10])

            # ── Persist story data to trial ──
            await trial_svc.update_trial_story(
                trial_id=_trial_uuid,
                story_title=story_response.title,
                story_pages=story_pages,
                generated_prompts=generated_prompts,
                clothing_description=fixed_outfit,
                blueprint_json=blueprint_json,
                pipeline_version=_pipeline_ver,
                page_manifest=page_manifest.model_dump(),
                scenario_id=str(getattr(scenario, "id", "") or ""),
            )

            # ── TWO-PHASE: Generate visual prompts for preview pages only ──
            _preview_pages_text_only = _select_preview_prompts(story_pages, num_inner=2)
            
            # Ensure pages have text_tr field (enhance_all_pages may expect it)
            for page in _preview_pages_text_only:
                if "text" in page and "text_tr" not in page:
                    page["text_tr"] = page["text"]
            
            logger.info(
                "Generating visual prompts for preview pages",
                trial_id=trial_id,
                preview_page_count=len(_preview_pages_text_only),
            )
            
            # Generate visual prompts for preview pages using same character bible + blueprint
            from app.prompt_engine.character_bible import build_character_bible
            from app.prompt_engine.scenario_bible import normalize_location_key_for_anchors
            
            # Rebuild character bible for prompt generation
            _raw_loc = getattr(scenario, "theme_key", None) or getattr(scenario, "location_en", "") or scenario.name
            location_key = normalize_location_key_for_anchors(str(_raw_loc or ""))
            
            _child_outfit_block = blueprint_json.get("child_outfit") or {}
            _blueprint_outfit = _child_outfit_block.get("description_en", "").strip()
            _blueprint_hair = _child_outfit_block.get("hair_style_en", "").strip()
            _effective_outfit = (fixed_outfit or "").strip() or _blueprint_outfit
            
            character_bible = build_character_bible(
                child_name=child_name,
                child_age=child_age,
                child_gender=child_gender or "erkek",
                child_description=_visual_char_desc,
                fixed_outfit=_effective_outfit,
                hair_style=_blueprint_hair,
                companion_name="",
                companion_species="",
                companion_appearance="",
            )
            
            try:
                _preview_enhanced = await gemini_service.enhance_pages_with_visual_prompts(
                    story_pages=_preview_pages_text_only,
                    blueprint=blueprint_json,
                    character_bible=character_bible,
                    visual_style=visual_style or "children's book illustration",
                    location_key=location_key,
                    value_visual_motif="",
                    likeness_hint="",
                    has_pulid=bool(child_photo_url),
                    leading_prefix_override=_story_leading_prefix_override,
                    style_block_override=_story_style_block_override,
                )
                
                # Update generated_prompts cache with enhanced preview pages
                _preview_enhanced_dict = []
                for i, page in enumerate(_preview_enhanced):
                    # Enhanced pages have image_prompt_en and negative_prompt added
                    # but may not have text_tr (they may have kept original field names)
                    # Get text from original page if not in enhanced
                    original_page = _preview_pages_text_only[i] if i < len(_preview_pages_text_only) else {}
                    page_text = page.get("text_tr") or page.get("text") or original_page.get("text", "")
                    
                    page_dict = {
                        "page_number": page.get("page_number", page.get("page", 0)),
                        "text": page_text,
                        "visual_prompt": page.get("image_prompt_en", ""),
                        "image_prompt_en": page.get("image_prompt_en", ""),  # Keep both fields for compatibility
                        "negative_prompt": page.get("negative_prompt", ""),
                        "v3_composed": True,
                        "page_type": page.get("page_type", "inner"),
                    }
                    _preview_enhanced_dict.append(page_dict)
                
                logger.info(
                    "Preview visual prompts generated",
                    trial_id=trial_id,
                    enhanced_count=len(_preview_enhanced_dict),
                )
            except Exception as _preview_err:
                logger.error(
                    "CRITICAL: Failed to generate preview visual prompts - cannot proceed with preview",
                    trial_id=trial_id,
                    error=str(_preview_err),
                    error_type=type(_preview_err).__name__,
                )
                # CRITICAL: Cannot generate preview without visual prompts
                # Re-raise error instead of using text-only pages
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Görsel promptları oluşturulamadı. Lütfen tekrar deneyin."
                ) from _preview_err

            # ── Enqueue preview image generation ──
            _arq_ok = False
            try:
                from app.workers.enqueue import enqueue_trial_preview

                _arq_job_id = await enqueue_trial_preview(
                    trial_id=trial_id,
                    prompts=_preview_enhanced_dict,
                    child_photo_url=child_photo_url,
                    visual_style=visual_style,
                    product_name=product_name,
                    story_title=story_response.title,
                    clothing_description=fixed_outfit,
                    visual_style_name=visual_style_name,
                )
                if _arq_job_id:
                    _arq_ok = True
            except Exception as _enq_err:
                logger.warning("Arq enqueue failed for trial preview", error=str(_enq_err))

            if not _arq_ok:
                await _generate_preview_images_inner(
                    trial_id=trial_id,
                    prompts=_preview_enhanced_dict,
                    child_photo_url=child_photo_url,
                    visual_style=visual_style,
                    product_name=product_name,
                    story_title=story_response.title,
                    clothing_description=fixed_outfit,
                    visual_style_name=visual_style_name,
                )

            logger.info("Trial story generation completed", trial_id=trial_id)

        except Exception as e:
            logger.exception("Trial story generation failed", trial_id=trial_id, error=str(e))
            # Mark the trial as failed so frontend can show an error
            try:
                _trial_fail = (
                    await db.execute(_sel(StoryPreview).where(StoryPreview.id == _UUID(trial_id)))
                ).scalar_one_or_none()
                if _trial_fail:
                    _trial_fail.generation_progress = {
                        "stage": "failed",
                        "message": "Hikaye oluşturulamadı. Lütfen tekrar deneyin.",
                        "error": str(e)[:200],
                    }
                    await db.commit()
            except Exception:
                pass
            raise


def _select_preview_prompts(all_prompts: list[dict], num_inner: int = 2) -> list[dict]:
    """Select pages for preview in order: Cover, Greeting1-2, Story1-2.

    Returns: [cover, front_matter_1, front_matter_2, story_1, story_2]
    This gives a proper preview showing: Cover → Karşılama pages → First story pages.
    
    Args:
        all_prompts: All generated prompts (cover, front_matter, inner pages, backcover)
        num_inner: Number of actual story (inner) pages to include (default 2)
    
    Returns:
        List of prompts ordered as: cover, all front_matter, first num_inner story pages
    """
    result: list[dict] = []
    
    # 1. Add cover first (page_type="cover")
    cover_pages = [p for p in all_prompts if p.get("page_type") == "cover"]
    result.extend(cover_pages)
    
    # 2. Add ALL front_matter pages (karşılama/dedication) in order
    front_matter_pages = [p for p in all_prompts if p.get("page_type") == "front_matter"]
    # Sort by page_number to ensure correct order
    front_matter_pages.sort(key=lambda x: x.get("page_number", 999))
    result.extend(front_matter_pages)
    
    # 3. Add first N story pages (page_type="inner")
    story_pages = [p for p in all_prompts if p.get("page_type") not in ("cover", "front_matter", "backcover")]
    # Sort by page_number to get first pages
    story_pages.sort(key=lambda x: x.get("page_number", 999))
    result.extend(story_pages[:num_inner])
    
    return result


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


async def _generate_preview_images_inner(
    trial_id: str,
    prompts: list[dict],
    child_photo_url: str | None,
    visual_style: str | None,
    product_name: str | None = None,
    story_title: str = "",
    clothing_description: str = "",
    visual_style_name: str | None = None,
):
    """Actual preview image generation logic, runs inside trial semaphore."""
    from app.core.database import async_session_factory
    from app.services.ai.image_provider_dispatch import (
        get_effective_ai_config,
        get_image_provider_for_generation,
    )
    from app.services.trial_service import get_trial_service

    # Kitap yatay A4: tüm ürün tipleri için yatay A4 oranı (1024×724) kullan
    from app.utils.resolution_calc import DEFAULT_GENERATION_A4_LANDSCAPE
    width, height = DEFAULT_GENERATION_A4_LANDSCAPE

    from app.services.ai.face_service import resolve_face_reference
    from app.services.storage_service import storage_service as _ss
    _face_ref_url, _face_embedding = await resolve_face_reference(child_photo_url, _ss)

    logger.info(
        "Starting preview image generation (yatay A4)",
        trial_id=trial_id,
        prompts_count=len(prompts),
        image_size=f"{width}x{height}",
        product_name=product_name,
        clothing=clothing_description[:60] if clothing_description else "NONE",
        face_cropped=_face_ref_url != child_photo_url,
    )

    async with async_session_factory() as db:
        try:
            trial_service = get_trial_service(db)

            # Update status to GENERATING
            await trial_service.update_to_generating(uuid.UUID(trial_id))

            # Resolve visual style from DB for correct style matching
            actual_style = ""
            style_negative_en = ""
            leading_prefix_override = None
            style_block_override = None
            _preview_id_weight: float | None = None
            _preview_true_cfg_override: float | None = None
            _preview_start_step_override: int | None = None
            _preview_num_inference_steps_override: int | None = None
            _preview_guidance_scale_override: float | None = None
            vs = await _resolve_visual_style_from_db(db, visual_style_name)
            if vs:
                if vs.prompt_modifier:
                    actual_style = vs.prompt_modifier.strip()
                style_negative_en = (vs.style_negative_en or "").strip()
                leading_prefix_override = (vs.leading_prefix_override or "").strip() or None
                style_block_override = (vs.style_block_override or "").strip() or None
                if vs.id_weight is not None:
                    _preview_id_weight = float(vs.id_weight)
                _preview_true_cfg_override = float(vs.true_cfg) if getattr(vs, "true_cfg", None) is not None else None
                _preview_start_step_override = int(vs.start_step) if getattr(vs, "start_step", None) is not None else None
                _preview_num_inference_steps_override = int(vs.num_inference_steps) if getattr(vs, "num_inference_steps", None) is not None else None
                _preview_guidance_scale_override = float(vs.guidance_scale) if getattr(vs, "guidance_scale", None) is not None else None
                logger.info(
                    "Resolved VisualStyle from DB (preview)",
                    style_name=vs.name,
                    has_override=bool(leading_prefix_override or style_block_override),
                    id_weight=_preview_id_weight,
                    id_weight_source="db" if _preview_id_weight is not None else "code_fallback",
                )
            elif visual_style:
                # DB lookup failed — use frontend-provided value BUT strip dangerous fallback
                actual_style = visual_style if "pixar" not in (visual_style or "").lower() else ""

            preview_images = {}
            ai_config = await get_effective_ai_config(db, product_id=None)
            provider_name = (
                (ai_config.image_provider or "gemini").strip().lower() if ai_config else "gemini"
            )
            image_provider = get_image_provider_for_generation(provider_name)

            logger.info(
                "IMAGE_ENGINE_USED",
                provider=provider_name,
                model=getattr(ai_config, "image_model", "") if ai_config else "",
                trial_id=trial_id,
                source="generate_preview_images",
            )

            # Load prompt templates from DB (same as composed preview)
            from app.prompt_engine.constants import (
                DEFAULT_COVER_TEMPLATE_EN as _DEF_COVER,
            )
            from app.prompt_engine.constants import (
                DEFAULT_INNER_TEMPLATE_EN as _DEF_INNER,
            )
            from app.services.prompt_template_service import get_prompt_service

            _tpl_svc_prev = get_prompt_service()
            _cover_tpl = await _tpl_svc_prev.get_template_en(db, "COVER_TEMPLATE", _DEF_COVER)
            _inner_tpl = await _tpl_svc_prev.get_template_en(db, "INNER_TEMPLATE", _DEF_INNER)

            # Parallel image generation with concurrency limit
            from app.config import settings as _cfg
            _gen_sem = asyncio.Semaphore(_cfg.image_concurrency)

            async def _gen_preview_single(prompt_data: dict, custom_clothing: str | None = None) -> tuple[int, str] | None:
                page_num = prompt_data["page_number"]
                visual_prompt = prompt_data["visual_prompt"]
                _is_v3 = prompt_data.get("v3_composed", False)
                _clothing = custom_clothing if custom_clothing is not None else clothing_description
                async with _gen_sem:
                    try:
                        result = await image_provider.generate_consistent_image(
                            prompt=visual_prompt,
                            child_face_url=_face_ref_url or "",
                            clothing_prompt=_clothing or "",
                            style_modifier=actual_style,
                            width=width,
                            height=height,
                            is_cover=(page_num == 0),
                            template_en=_cover_tpl if page_num == 0 else _inner_tpl,
                            story_title=story_title if page_num == 0 else "",
                            style_negative_en=style_negative_en,
                            leading_prefix_override=leading_prefix_override,
                            style_block_override=style_block_override,
                            id_weight=_preview_id_weight,
                            true_cfg_override=_preview_true_cfg_override,
                            start_step_override=_preview_start_step_override,
                            num_inference_steps_override=_preview_num_inference_steps_override,
                            guidance_scale_override=_preview_guidance_scale_override,
                            skip_compose=_is_v3,
                            precomposed_negative=prompt_data.get("negative_prompt", "") if _is_v3 else "",
                            reference_embedding=_face_embedding,
                        )
                        image_url = result[0] if isinstance(result, tuple) else result
                        if image_url:
                            logger.info(f"Generated preview image for page {page_num}")
                            return (page_num, image_url)
                    except Exception as e:
                        logger.error(
                            f"Failed to generate image for page {page_num}",
                            error=str(e),
                        )
                return None

            # Filter out front_matter pages (text-only, no image).
            # backcover pages ARE included — they get AI-generated images too.
            image_prompts = [
                p for p in prompts
                if p.get("page_type", "inner") != "front_matter"
            ]

            # Separate back cover (page_number=999) from story/cover prompts
            _backcover_prompt_data = next(
                (p for p in image_prompts if p.get("page_type") == "backcover"), None
            )
            story_image_prompts = [p for p in image_prompts if p.get("page_type") != "backcover"]

            # Guard: cover page must be present
            _has_cover = any(p.get("page_number") == 0 and p.get("page_type", "inner") == "cover" for p in story_image_prompts)
            if not _has_cover and story_image_prompts:
                logger.warning(
                    "COVER_MISSING_IN_PREVIEW: no page_number=0 with page_type=cover found",
                    trial_id=trial_id,
                    pages=[p.get("page_number") for p in story_image_prompts],
                )

            gen_results = await asyncio.gather(
                *[_gen_preview_single(p) for p in story_image_prompts],
                return_exceptions=True,
            )
            for r in gen_results:
                if isinstance(r, tuple) and len(r) == 2:
                    preview_images[r[0]] = r[1]

            # Generate back cover image (same quality as front cover)
            if _backcover_prompt_data and _backcover_prompt_data.get("visual_prompt"):
                try:
                    # Resolve clothing for back cover — use scenario-specific outfit if available
                    _bc_clothing = clothing_description
                    if not _bc_clothing:
                        # Try to get trial record to extract scenario_id
                        try:
                            _trial_rec = await trial_service.get_trial_by_id(uuid.UUID(trial_id))
                            _scenario_id = getattr(_trial_rec, "scenario_id", None)
                            if _scenario_id:
                                from app.models.scenario import Scenario as _ScenBC
                                from sqlalchemy import select as _selBC
                                _sc_res = await db.execute(_selBC(_ScenBC).where(_ScenBC.id == _scenario_id))
                                _sc = _sc_res.scalar_one_or_none()
                                if _sc:
                                    # Get child gender from trial
                                    _child_gender_bc = getattr(_trial_rec, "child_gender", "erkek") or "erkek"
                                    _g_bc = _child_gender_bc.lower()
                                    if _g_bc in ("kiz", "kız", "girl", "female"):
                                        _bc_clothing = (getattr(_sc, "outfit_girl", None) or "").strip() or (getattr(_sc, "outfit_boy", None) or "").strip()
                                    else:
                                        _bc_clothing = (getattr(_sc, "outfit_boy", None) or "").strip() or (getattr(_sc, "outfit_girl", None) or "").strip()
                                    if _bc_clothing:
                                        logger.info("BACK_COVER_CLOTHING_RESOLVED", trial_id=trial_id, scenario_id=str(_scenario_id), outfit=_bc_clothing[:60])
                        except Exception as _outfit_err:
                            logger.warning("BACK_COVER_OUTFIT_RESOLVE_FAILED", trial_id=trial_id, error=str(_outfit_err))
                    
                    # Generate back cover with resolved clothing
                    _bc_result = await _gen_preview_single(_backcover_prompt_data, custom_clothing=_bc_clothing)
                    if isinstance(_bc_result, tuple) and len(_bc_result) == 2:
                        # Store under key "backcover" (not a page number)
                        preview_images["backcover"] = _bc_result[1]
                        logger.info("BACK_COVER_IMAGE_GENERATED", trial_id=trial_id, clothing_used=_bc_clothing[:60] if _bc_clothing else "none")
                except Exception as _bc_img_err:
                    logger.warning("BACK_COVER_IMAGE_FAILED", trial_id=trial_id, error=str(_bc_img_err))

            # Save preview images
            if preview_images:
                await trial_service.save_preview_images(
                    uuid.UUID(trial_id),
                    preview_images,
                )
                logger.info(
                    "Preview images saved",
                    trial_id=trial_id,
                    count=len(preview_images),
                    keys=list(preview_images.keys()),
                )

        except Exception as e:
            logger.exception("Background preview generation failed", error=str(e))


# ============ GENERATE PREVIEW FROM EXISTING STORY ============


class GeneratePreviewRequest(BaseModel):
    """Request to generate 3 preview images for an already-generated story."""

    # Lead info
    user_id: str | None = None
    parent_name: str = Field(..., min_length=2)
    parent_email: EmailStr
    parent_phone: str | None = None

    # Child info
    child_name: str
    child_age: int
    child_gender: str | None = None
    child_photo_url: str | None = None

    # Product info
    product_id: str | None = None
    product_name: str | None = None
    product_price: float | None = None

    # Story info (already generated)
    story_title: str
    story_pages: list[StoryPageInput]
    scenario_id: str | None = None
    scenario_name: str | None = None
    visual_style: str | None = None
    visual_style_name: str | None = None
    learning_outcomes: list[str] | None = None
    clothing_description: str | None = None
    id_weight: float | None = None

    @field_validator("child_photo_url")
    @classmethod
    def validate_photo_url(cls, v: str | None) -> str | None:
        """Validate child photo URL to prevent SSRF."""
        return validate_image_url(v, field_name="child_photo_url")


@router.post("/generate-preview", response_model=TrialResponse)
async def generate_preview_from_story(
    request: GeneratePreviewRequest,
    background_tasks: BackgroundTasks,
    db: DbSession,
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
        from app.api.v1.orders import _force_deterministic_title

        det_title = _force_deterministic_title(
            child_name=request.child_name,
            scenario_name=request.scenario_name,
            original_title=request.story_title,
        )

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

        trial = await trial_service.create_trial(
            lead_user_id=uuid.UUID(request.user_id) if request.user_id else None,
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


async def _generate_composed_preview_inner(
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
    """Actual composed preview logic, runs inside trial semaphore."""
    import base64

    import httpx

    from app.core.database import async_session_factory
    from app.models.book_template import PageTemplate
    from app.services.ai.image_provider_dispatch import (
        get_effective_ai_config,
        get_image_provider_for_generation,
    )
    from app.services.page_composer import build_template_config, page_composer
    from app.services.storage_service import storage_service
    from app.services.trial_service import get_trial_service
    from app.utils.resolution_calc import DEFAULT_GENERATION_A4_LANDSCAPE
    width, height = DEFAULT_GENERATION_A4_LANDSCAPE

    from app.services.ai.face_service import resolve_face_reference
    from app.services.storage_service import storage_service as _ss_comp
    _face_ref_url, _face_embedding = await resolve_face_reference(child_photo_url, _ss_comp)

    # Full forensic description for Gemini — richer than ai_director (30-50 words)
    _char_desc_for_images = ""
    if _face_ref_url:
        try:
            from app.services.ai.face_analyzer_service import get_face_analyzer as _get_fa2
            _fa2 = _get_fa2()
            _char_desc_for_images = await _fa2.get_enhanced_child_description(
                image_source=_face_ref_url,
                child_name=child_name,
                child_age=child_age,
                child_gender=child_gender or "",
            )
        except Exception as _fa2_err:
            logger.warning(
                "Preview image face analysis failed — no CHARACTER ANCHOR",
                trial_id=trial_id,
                error=str(_fa2_err),
            )

    logger.info(
        "Starting composed preview image generation",
        trial_id=trial_id,
        prompts_count=len(prompts),
        image_size=f"{width}x{height}",
        face_cropped=_face_ref_url != child_photo_url,
    )

    async with async_session_factory() as db:
        try:
            trial_service = get_trial_service(db)
            await trial_service.update_to_generating(uuid.UUID(trial_id))

            # Get AI config and image provider
            product_uuid = None
            if product_id:
                try:
                    product_uuid = uuid.UUID(product_id)
                except ValueError:
                    pass

            ai_config = await get_effective_ai_config(db, product_id=product_uuid)
            provider_name = (
                (ai_config.image_provider or "gemini").strip().lower() if ai_config else "gemini"
            )
            image_provider = get_image_provider_for_generation(provider_name)

            logger.info(
                "IMAGE_ENGINE_USED",
                provider=provider_name,
                model=getattr(ai_config, "image_model", "") if ai_config else "",
                trial_id=trial_id,
                product_id=product_id or "",
                source="generate_composed_preview",
            )

            # Resolve visual style from DB (name + display_name fallback)
            actual_style = ""
            _comp_vs_leading_prefix: str | None = None
            _comp_vs_style_block: str | None = None
            _comp_vs_style_negative = ""
            _comp_true_cfg_override: float | None = None
            _comp_start_step_override: int | None = None
            _comp_num_inference_steps_override: int | None = None
            _comp_guidance_scale_override: float | None = None
            vs = await _resolve_visual_style_from_db(db, visual_style_name)
            if vs:
                if vs.prompt_modifier:
                    actual_style = vs.prompt_modifier.strip()
                if id_weight is None and vs.id_weight is not None:
                    id_weight = float(vs.id_weight)
                _comp_vs_leading_prefix = (vs.leading_prefix_override or "").strip() or None
                _comp_vs_style_block = (vs.style_block_override or "").strip() or None
                _comp_vs_style_negative = (vs.style_negative_en or "").strip()
                _comp_true_cfg_override = float(vs.true_cfg) if getattr(vs, "true_cfg", None) is not None else None
                _comp_start_step_override = int(vs.start_step) if getattr(vs, "start_step", None) is not None else None
                _comp_num_inference_steps_override = int(vs.num_inference_steps) if getattr(vs, "num_inference_steps", None) is not None else None
                _comp_guidance_scale_override = float(vs.guidance_scale) if getattr(vs, "guidance_scale", None) is not None else None
                logger.info(
                    "Resolved VisualStyle from DB (composed preview)",
                    style_name=vs.name,
                    has_override=bool(_comp_vs_leading_prefix or _comp_vs_style_block),
                    id_weight=id_weight,
                    id_weight_source="db" if id_weight is not None else "code_fallback",
                )
            elif visual_style:
                # DB lookup failed — use frontend value BUT strip dangerous fallback
                actual_style = visual_style if "pixar" not in (visual_style or "").lower() else ""

            from app.prompt_engine import personalize_style_prompt

            actual_style = personalize_style_prompt(
                actual_style,
                child_name=child_name,
                child_age=child_age,
                child_gender=child_gender or "",
            )

            # ── PERSIST resolved style params to trial cache ──────────────
            # Remaining pages will read these exact values → guarantees
            # identical style between preview (pages 1-3) and remaining (4+).
            try:
                _trial_for_cache = (
                    await db.execute(
                        select(StoryPreview).where(
                            StoryPreview.id == uuid.UUID(trial_id)
                        )
                    )
                ).scalar_one_or_none()
                if _trial_for_cache and _trial_for_cache.generated_prompts_cache is not None:
                    _cache = dict(_trial_for_cache.generated_prompts_cache)
                    _cache["_resolved_style"] = {
                        "style_modifier": actual_style,
                        "style_negative_en": _comp_vs_style_negative,
                        "leading_prefix_override": _comp_vs_leading_prefix or "",
                        "style_block_override": _comp_vs_style_block or "",
                        "id_weight": id_weight,
                        "true_cfg_override": _comp_true_cfg_override,
                        "start_step_override": _comp_start_step_override,
                        "num_inference_steps_override": _comp_num_inference_steps_override,
                        "guidance_scale_override": _comp_guidance_scale_override,
                        "provider_name": provider_name,
                        "product_id": product_id or "",
                    }
                    _trial_for_cache.generated_prompts_cache = _cache
                    await db.commit()
                    logger.info(
                        "PREVIEW_STYLE_CACHED — remaining pages will reuse these exact params",
                        trial_id=trial_id,
                        provider=provider_name,
                        style_modifier_len=len(actual_style),
                        has_leading_prefix=bool(_comp_vs_leading_prefix),
                        has_style_block=bool(_comp_vs_style_block),
                    )
            except Exception as _cache_err:
                logger.warning("Failed to cache resolved style", error=str(_cache_err))

            # Get prompt templates
            from app.prompt_engine.constants import (
                DEFAULT_COVER_TEMPLATE_EN,
                DEFAULT_INNER_TEMPLATE_EN,
            )
            from app.services.prompt_template_service import get_prompt_service

            _tpl_svc = get_prompt_service()
            cover_tpl = await _tpl_svc.get_template_en(
                db, "COVER_TEMPLATE", DEFAULT_COVER_TEMPLATE_EN
            )
            inner_tpl = await _tpl_svc.get_template_en(
                db, "INNER_TEMPLATE", DEFAULT_INNER_TEMPLATE_EN
            )

            # Get page templates for text composition
            cover_template = None
            inner_template = None
            if product_uuid:
                from sqlalchemy.orm import selectinload

                from app.models.product import Product

                rp = await db.execute(
                    select(Product)
                    .where(Product.id == product_uuid)
                    .options(
                        selectinload(Product.inner_template),
                        selectinload(Product.cover_template),
                    )
                )
                product_obj = rp.scalar_one_or_none()
                if product_obj:
                    cover_template = product_obj.cover_template
                    inner_template = product_obj.inner_template

            if not cover_template or not inner_template:
                from sqlalchemy import desc

                ct_result = await db.execute(
                    select(PageTemplate)
                    .where(PageTemplate.page_type == "cover")
                    .order_by(desc(PageTemplate.updated_at))
                    .limit(1)
                )
                cover_template = ct_result.scalar_one_or_none()

                it_result = await db.execute(
                    select(PageTemplate)
                    .where(PageTemplate.page_type == "inner")
                    .order_by(desc(PageTemplate.updated_at))
                    .limit(1)
                )
                inner_template = it_result.scalar_one_or_none()

            preview_images: dict[int, str] = {}

            # Parallel image generation with concurrency limit
            from app.config import settings as _cfg_comp
            _comp_sem = asyncio.Semaphore(_cfg_comp.image_concurrency)

            async def _gen_composed_single(prompt_data: dict) -> tuple[int, str] | None:
                page_num = prompt_data["page_number"]
                visual_prompt = prompt_data["visual_prompt"]
                _is_v3 = prompt_data.get("v3_composed", False)
                async with _comp_sem:
                    try:
                        _is_cover = page_num == 0
                        result = await image_provider.generate_consistent_image(
                            prompt=visual_prompt,
                            child_face_url=_face_ref_url or "",
                            clothing_prompt=(clothing_description or "").strip(),
                            style_modifier=actual_style,
                            width=width,
                            height=height,
                            is_cover=_is_cover,
                            template_en=cover_tpl if _is_cover else inner_tpl,
                            story_title=story_title if _is_cover else "",
                            child_gender=child_gender or "",
                            style_negative_en=_comp_vs_style_negative,
                            leading_prefix_override=_comp_vs_leading_prefix,
                            style_block_override=_comp_vs_style_block,
                            id_weight=id_weight,
                            true_cfg_override=_comp_true_cfg_override,
                            start_step_override=_comp_start_step_override,
                            num_inference_steps_override=_comp_num_inference_steps_override,
                            guidance_scale_override=_comp_guidance_scale_override,
                            skip_compose=_is_v3,
                            precomposed_negative=prompt_data.get("negative_prompt", "") if _is_v3 else "",
                            reference_embedding=_face_embedding,
                            character_description=_char_desc_for_images,
                        )
                        image_url = result[0] if isinstance(result, tuple) else result
                        if image_url:
                            logger.info(f"Generated composed preview image for page {page_num}")
                            return (page_num, image_url)
                    except Exception as e:
                        logger.error(
                            f"Failed to generate image for page {page_num}",
                            error=str(e),
                        )
                return None

            # Filter out front_matter pages (text-only, no image)
            comp_image_prompts = [
                p for p in prompts
                if p.get("page_type", "inner") != "front_matter"
            ]
            comp_results = await asyncio.gather(
                *[_gen_composed_single(p) for p in comp_image_prompts],
                return_exceptions=True,
            )
            for r in comp_results:
                if isinstance(r, tuple) and len(r) == 2:
                    preview_images[r[0]] = r[1]

            # Compose text on images (preview quality - 150 DPI)
            composed_urls: dict[int, str] = {}
            PREVIEW_DPI = 150
            story_id = trial_id[:8]

            for page_num, image_url in preview_images.items():
                try:
                    _is_cover = page_num == 0
                    template = cover_template if _is_cover else inner_template
                    if not template:
                        # No template, use raw image
                        composed_urls[page_num] = image_url
                        continue

                    # Download the AI image as base64
                    async with httpx.AsyncClient(timeout=30) as client:
                        resp = await client.get(image_url)
                        resp.raise_for_status()
                        image_b64 = base64.b64encode(resp.content).decode("utf-8")

                    # Get text for this page
                    page_text = ""
                    for p in prompts:
                        if p["page_number"] == page_num:
                            page_text = p.get("text", "")
                            break

                    # Kapak sayfası: sadece story_title kullan; prompts'tan gelen metin
                    # hikaye paragrafı olabilir (AI hatası) — asla kapağa hikaye metni yazma.
                    if _is_cover:
                        page_text = story_title or ""

                    template_config = build_template_config(template)

                    # Compose with text overlay at preview DPI (sync/CPU-bound -> thread)
                    composed_b64 = await asyncio.to_thread(
                        page_composer.compose_page,
                        image_base64=image_b64,
                        text=page_text,
                        template_config=template_config,
                        page_width_mm=297,
                        page_height_mm=210,
                        dpi=PREVIEW_DPI,
                    )

                    # Upload composed image to GCS (sync I/O -> thread)
                    uploaded = await asyncio.to_thread(
                        storage_service.upload_multiple_images,
                        images={page_num: composed_b64},
                        story_id=f"preview-{story_id}",
                    )
                    if page_num in uploaded:
                        composed_urls[page_num] = uploaded[page_num]
                    else:
                        composed_urls[page_num] = image_url

                except Exception as e:
                    logger.warning(
                        f"Failed to compose page {page_num}, using raw image",
                        error=str(e),
                    )
                    composed_urls[page_num] = image_url

            # --- Compose dedication page / karşılama 1 (AI text, fallback to template) ---
            try:
                # Extract AI-generated dedication text from front_matter page
                _ai_ded_text = ""
                for p in prompts:
                    if p.get("page_type") == "front_matter":
                        _ai_ded_text = (p.get("text") or "").strip()
                        break

                from sqlalchemy import desc as _desc_

                ded_result = await db.execute(
                    select(PageTemplate)
                    .where(PageTemplate.page_type == "dedication", PageTemplate.is_active == True)
                    .order_by(_desc_(PageTemplate.updated_at))
                    .limit(1)
                )
                ded_tpl = ded_result.scalar_one_or_none()

                # Use AI text if available, otherwise fall back to template default
                if _ai_ded_text:
                    ded_text = _ai_ded_text
                    logger.info("Using AI-generated dedication text", trial_id=trial_id, text_preview=ded_text[:80])
                elif ded_tpl:
                    ded_text = (getattr(ded_tpl, "dedication_default_text", None) or "Bu kitap {child_name} için özel hazırlanmıştır")
                    ded_text = ded_text.replace("{child_name}", child_name)
                else:
                    ded_text = f"Bu kitap {child_name} için özel hazırlanmıştır"

                ded_cfg = build_template_config(ded_tpl) if ded_tpl else {}
                ded_b64 = await asyncio.to_thread(
                    page_composer.compose_dedication_page,
                    text=ded_text,
                    template_config=ded_cfg,
                    dpi=PREVIEW_DPI,
                )
                ded_uploaded = await asyncio.to_thread(
                    storage_service.upload_multiple_images,
                    images={"dedication": ded_b64},
                    story_id=f"preview-{story_id}",
                )
                if "dedication" in ded_uploaded:
                    composed_urls["dedication"] = ded_uploaded["dedication"]
                    logger.info("Dedication preview page composed", trial_id=trial_id)
            except Exception as ded_err:
                logger.warning("Failed to compose dedication preview: %s", ded_err)

            # --- Compose scenario intro page / karşılama 2 ---
            try:
                _intro_text: str | None = None

                # 1. Try scenario.description
                if scenario_id:
                    from app.models.scenario import Scenario as _Scenario
                    _sc_result = await db.execute(
                        select(_Scenario).where(_Scenario.id == uuid.UUID(scenario_id))
                    )
                    _sc = _sc_result.scalar_one_or_none()
                    if _sc and getattr(_sc, "description", None) and len(_sc.description) > 20:
                        _intro_text = _sc.description[:500]
                    elif _sc:
                        # Fallback: generate via Gemini
                        location = getattr(_sc, "location_en", None) or getattr(_sc, "name", None)
                        if location:
                            import httpx as _httpx
                            _intro_prompt = (
                                f"'{story_title}' adlı çocuk kitabı için '{location}' hakkında "
                                f"2-3 cümlelik, çocuk dostu, eğitici ve büyülü bir giriş paragrafı yaz. "
                                f"Türkçe yaz. Sadece paragrafı yaz, başlık veya açıklama ekleme."
                            )
                            _api_key = _settings.gemini_api_key
                            if _api_key:
                                _url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={_api_key}"
                                _payload = {
                                    "contents": [{"parts": [{"text": _intro_prompt}]}],
                                    "generationConfig": {"temperature": 0.7, "maxOutputTokens": 200},
                                }
                                try:
                                    async with _httpx.AsyncClient(timeout=30.0) as _hc:
                                        _resp = await _hc.post(_url, json=_payload)
                                        _resp.raise_for_status()
                                        _intro_text = _resp.json()["candidates"][0]["content"]["parts"][0]["text"].strip()[:500]
                                except Exception as _gem_err:
                                    logger.warning("Gemini intro text failed for preview", error=str(_gem_err))

                if _intro_text:
                    from sqlalchemy import desc as _desc2_
                    _intro_tpl_result = await db.execute(
                        select(PageTemplate)
                        .where(PageTemplate.page_type == "dedication", PageTemplate.is_active == True)
                        .order_by(_desc2_(PageTemplate.updated_at))
                        .limit(1)
                    )
                    _intro_tpl = _intro_tpl_result.scalar_one_or_none()
                    _intro_cfg = build_template_config(_intro_tpl) if _intro_tpl else {}
                    _intro_b64 = await asyncio.to_thread(
                        page_composer.compose_dedication_page,
                        text=_intro_text,
                        template_config=_intro_cfg,
                        dpi=PREVIEW_DPI,
                    )
                    _intro_uploaded = await asyncio.to_thread(
                        storage_service.upload_multiple_images,
                        images={"intro": _intro_b64},
                        story_id=f"preview-{story_id}",
                    )
                    if "intro" in _intro_uploaded:
                        composed_urls["intro"] = _intro_uploaded["intro"]
                        logger.info("Scenario intro page (karşılama 2) composed for preview", trial_id=trial_id)
            except Exception as _intro_err:
                logger.warning("Failed to compose scenario intro preview: %s", _intro_err)

            # Save composed preview images
            final_images = composed_urls if composed_urls else preview_images
            if final_images:
                await trial_service.save_preview_images(
                    uuid.UUID(trial_id),
                    final_images,
                )
                logger.info(
                    "Composed preview images saved",
                    trial_id=trial_id,
                    count=len(final_images),
                    keys=list(final_images.keys()),
                )

        except Exception as e:
            logger.exception("Background composed preview generation failed", error=str(e))


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
    x_trial_token: str | None = Header(None, alias="X-Trial-Token"),
) -> TrialResponse:
    """
    Complete a trial after payment - Phase 2.

    Security: Validates ownership via X-Trial-Token AND that payment was
    actually completed (via promo code covering 100%, or verified Iyzico
    payment on the linked Order).
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
            # Check that the stored payment_reference matches to prevent spoofing
            stored_ref = (trial.payment_reference or "").strip()
            if stored_ref != payment_ref:
                logger.warning(
                    "COMPLETE_TRIAL_PAYMENT_REF_MISMATCH",
                    trial_id=request.trial_id,
                    provided=payment_ref[:30],
                    stored=stored_ref[:30],
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

                # If this is a promo-only payment, verify discount covers full price
                if is_free_order:
                    final_amount = max(subtotal - discount_amount, Decimal("0"))
                    if final_amount > Decimal("0"):
                        raise HTTPException(
                            status_code=status.HTTP_402_PAYMENT_REQUIRED,
                            detail="Kupon kodu toplam tutarı karşılamıyor. Ödeme gerekli.",
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
                )
            except HTTPException:
                raise
            except Exception as promo_err:
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
    """Background task to generate remaining 13 images after payment.

    Guarded by _TRIAL_GEN_SEMAPHORE to avoid competing with order tasks.
    """
    logger.info("Trial remaining pages waiting for semaphore slot", trial_id=trial_id)
    async with _TRIAL_GEN_SEMAPHORE:
        logger.info("Trial remaining pages acquired semaphore slot", trial_id=trial_id)
        await _generate_remaining_images_inner(
            trial_id, prompts, product_name,
            visual_style_modifier, child_photo_url, clothing_description,
        )


async def _generate_remaining_images_inner(
    trial_id: str,
    prompts: list[dict],
    product_name: str | None = None,
    visual_style_modifier: str = "",
    child_photo_url: str = "",
    clothing_description: str = "",
):
    """Actual remaining images logic, runs inside trial semaphore.
    
    TWO-PHASE: First generate visual prompts for remaining pages, then generate images.
    """
    from app.core.database import async_session_factory
    from app.services.ai.image_provider_dispatch import (
        get_effective_ai_config,
        get_image_provider_for_generation,
    )
    from app.services.trial_service import get_trial_service

    # Kitap yatay A4: tüm ürün tipleri için yatay A4 oranı (1024×724)
    from app.utils.resolution_calc import DEFAULT_GENERATION_A4_LANDSCAPE
    width, height = DEFAULT_GENERATION_A4_LANDSCAPE

    from app.services.ai.face_service import resolve_face_reference
    from app.services.storage_service import storage_service as _ss_rem
    _face_ref_url, _face_embedding = await resolve_face_reference(child_photo_url, _ss_rem)

    # AI-Director character description — resolved after trial obj is loaded below
    _rem_char_desc_for_images = ""

    logger.info(
        "Starting remaining pages generation (TWO-PHASE: prompts + images)",
        trial_id=trial_id,
        prompts_count=len(prompts),
        image_size=f"{width}x{height}",
        has_style=bool(visual_style_modifier),
        has_child_photo=bool(child_photo_url),
        has_clothing=bool(clothing_description),
        face_cropped=_face_ref_url != child_photo_url,
    )
    if not child_photo_url:
        logger.warning(
            "REMAINING_PAGES_NO_CHILD_PHOTO — images will lack face consistency",
            trial_id=trial_id,
        )

    async with async_session_factory() as db:
        try:
            trial_service = get_trial_service(db)

            # ── Idempotency: retry durumunda zaten uretilmis sayfalari atla ──
            _idem_result = await db.execute(
                select(StoryPreview).where(StoryPreview.id == uuid.UUID(trial_id))
            )
            _idem_trial = _idem_result.scalar_one_or_none()
            existing_pages = set((_idem_trial.page_images or {}).keys()) if _idem_trial else set()

            prompts_to_generate = [
                p for p in prompts
                if str(p["page_number"]) not in existing_pages
            ]
            logger.info(
                "REMAINING_PAGES_IDEMPOTENCY",
                trial_id=trial_id,
                total_prompts=len(prompts),
                already_generated=len(prompts) - len(prompts_to_generate),
                to_generate=len(prompts_to_generate),
            )

            # Retry flag: tum sayfalar onceki calistirmada uretildi mi?
            _is_full_retry = (
                not prompts_to_generate
                and _idem_trial is not None
                and _idem_trial.status == "PENDING"
            )
            if _is_full_retry:
                logger.info(
                    "REMAINING_PAGES_ALREADY_COMPLETE_SKIPPING_GEN",
                    trial_id=trial_id,
                    msg="Gorseller zaten uretildi, sadece PDF/email kontrol ediliyor",
                )

            generated_images = {}

            # Get trial record for cache + child info
            _trial_result_rem = await db.execute(
                select(StoryPreview).where(StoryPreview.id == uuid.UUID(trial_id))
            )
            _trial_obj_rem = _trial_result_rem.scalar_one_or_none()
            _rem_child_name = getattr(_trial_obj_rem, "child_name", "") or ""
            _rem_child_age = getattr(_trial_obj_rem, "child_age", 7) or 7
            _rem_child_gender = getattr(_trial_obj_rem, "child_gender", "") or ""

            # ── TWO-PHASE STEP 1: Generate visual prompts for remaining pages ──
            logger.info(
                "PHASE 1: Generating visual prompts for remaining pages",
                trial_id=trial_id,
                pages_without_prompts=len(prompts_to_generate),
            )
            
            # Check if pages need visual prompts (text_only pages have no visual_prompt)
            _pages_need_prompts = [
                p for p in prompts_to_generate
                if not p.get("visual_prompt") or not p.get("image_prompt_en")
            ]
            
            if _pages_need_prompts and _trial_obj_rem:
                try:
                    from app.prompt_engine.character_bible import build_character_bible
                    from app.prompt_engine.scenario_bible import normalize_location_key_for_anchors
                    from app.services.ai.gemini_service import gemini_service
                    
                    # Get cached data from trial
                    _cache = _trial_obj_rem.generated_prompts_cache or {}
                    _blueprint = _cache.get("blueprint_json", {})
                    
                    # Rebuild character bible from cache
                    _child_outfit_block = _blueprint.get("child_outfit") or {}
                    _blueprint_outfit = _child_outfit_block.get("description_en", "").strip()
                    _blueprint_hair = _child_outfit_block.get("hair_style_en", "").strip()
                    _effective_outfit = (clothing_description or "").strip() or _blueprint_outfit
                    
                    # Get scenario for location key
                    from app.models.scenario import Scenario
                    _scenario = None
                    _scenario_id = _cache.get("scenario_id")
                    if _scenario_id:
                        try:
                            _sc_res = await db.execute(
                                select(Scenario).where(Scenario.id == uuid.UUID(_scenario_id))
                            )
                            _scenario = _sc_res.scalar_one_or_none()
                        except Exception:
                            pass
                    
                    _location_key = ""
                    if _scenario:
                        _raw_loc = (
                            getattr(_scenario, "theme_key", None) or 
                            getattr(_scenario, "location_en", "") or 
                            _scenario.name
                        )
                        _location_key = normalize_location_key_for_anchors(str(_raw_loc or ""))
                    
                    character_bible = build_character_bible(
                        child_name=_rem_child_name,
                        child_age=_rem_child_age,
                        child_gender=_rem_child_gender or "erkek",
                        child_description="",
                        fixed_outfit=_effective_outfit,
                        hair_style=_blueprint_hair,
                        companion_name="",
                        companion_species="",
                        companion_appearance="",
                    )
                    
                    # Generate visual prompts for remaining pages
                    _remaining_enhanced = await gemini_service.enhance_pages_with_visual_prompts(
                        story_pages=_pages_need_prompts,
                        blueprint=_blueprint,
                        character_bible=character_bible,
                        visual_style=visual_style_modifier or "children's book illustration",
                        location_key=_location_key,
                        value_visual_motif="",
                        likeness_hint="",
                        has_pulid=bool(child_photo_url),
                        leading_prefix_override=None,
                        style_block_override=None,
                    )
                    
                    # Update prompts with enhanced visual prompts
                    _enhanced_map = {
                        p.get("page_number", p.get("page", 0)): p
                        for p in _remaining_enhanced
                    }
                    
                    for prompt in prompts_to_generate:
                        page_num = prompt.get("page_number", prompt.get("page", 0))
                        if page_num in _enhanced_map:
                            enhanced = _enhanced_map[page_num]
                            enhanced_prompt = enhanced.get("image_prompt_en", "")
                            prompt["visual_prompt"] = enhanced_prompt  # For image generation
                            prompt["image_prompt_en"] = enhanced_prompt  # For cache consistency
                            prompt["negative_prompt"] = enhanced.get("negative_prompt", "")
                            prompt["v3_composed"] = True
                    
                    logger.info(
                        "PHASE 1 COMPLETE: Visual prompts generated for remaining pages",
                        trial_id=trial_id,
                        enhanced_count=len(_remaining_enhanced),
                    )
                    
                    # Update trial cache with enhanced prompts
                    if _trial_obj_rem.generated_prompts_cache:
                        _all_prompts = _trial_obj_rem.generated_prompts_cache.get("prompts", [])
                        for enhanced in _remaining_enhanced:
                            page_num = enhanced.get("page_number", enhanced.get("page", 0))
                            enhanced_prompt = enhanced.get("image_prompt_en", "")
                            # Find and update existing prompt in cache
                            for i, cached_p in enumerate(_all_prompts):
                                if cached_p.get("page_number") == page_num:
                                    _all_prompts[i]["visual_prompt"] = enhanced_prompt
                                    _all_prompts[i]["image_prompt_en"] = enhanced_prompt  # Keep both for compatibility
                                    _all_prompts[i]["negative_prompt"] = enhanced.get("negative_prompt", "")
                                    _all_prompts[i]["v3_composed"] = True
                                    break
                        await db.commit()
                        
                except Exception as _prompt_gen_err:
                    logger.error(
                        "Failed to generate visual prompts for remaining pages",
                        trial_id=trial_id,
                        error=str(_prompt_gen_err),
                    )
                    # Continue with existing prompts (may have visual_prompt already)
            
            # ── TWO-PHASE STEP 2: Generate images using prompts ──
            logger.info(
                "PHASE 2: Generating images for remaining pages",
                trial_id=trial_id,
                prompts_count=len(prompts_to_generate),
            )

            # Full forensic description for Gemini — richer than ai_director (30-50 words)
            if _face_ref_url and not _rem_char_desc_for_images:
                try:
                    from app.services.ai.face_analyzer_service import (
                        get_face_analyzer as _get_fa_rem,
                    )
                    _fa_rem = _get_fa_rem()
                    _rem_char_desc_for_images = await _fa_rem.get_enhanced_child_description(
                        image_source=_face_ref_url,
                        child_name=_rem_child_name,
                        child_age=_rem_child_age,
                        child_gender=_rem_child_gender,
                    )
                    logger.info(
                        "Remaining pages: character description ready",
                        trial_id=trial_id,
                        description_length=len(_rem_char_desc_for_images),
                    )
                except Exception as _fa_rem_err:
                    logger.warning(
                        "Remaining pages: face analysis failed — no CHARACTER ANCHOR",
                        trial_id=trial_id,
                        error=str(_fa_rem_err),
                    )

            # ── CACHE-FIRST: Read style params cached by preview generation ──
            # This guarantees remaining pages use EXACTLY the same style
            # as preview pages (provider, style_modifier, negatives, overrides).
            _cached_style = (
                (_trial_obj_rem.generated_prompts_cache or {}).get("_resolved_style")
                if _trial_obj_rem
                else None
            )

            if _cached_style:
                visual_style = _cached_style.get("style_modifier", "")
                _rem_style_negative_en = _cached_style.get("style_negative_en", "")
                _rem_leading_prefix_override = _cached_style.get("leading_prefix_override", "") or None
                _rem_style_block_override = _cached_style.get("style_block_override", "") or None
                _rem_id_weight = _cached_style.get("id_weight")
                _rem_true_cfg_override = _cached_style.get("true_cfg_override")
                _rem_start_step_override = _cached_style.get("start_step_override")
                _rem_num_inference_steps_override = _cached_style.get("num_inference_steps_override")
                _rem_guidance_scale_override = _cached_style.get("guidance_scale_override")
                _cached_provider = _cached_style.get("provider_name", "")
                _cached_product_id = _cached_style.get("product_id", "")

                # Resolve product_uuid for AI config lookup
                _rem_product_uuid = None
                if _cached_product_id:
                    try:
                        _rem_product_uuid = uuid.UUID(_cached_product_id)
                    except (ValueError, TypeError):
                        pass

                # Use same AI provider as preview
                ai_config_rem = None
                if _cached_provider:
                    provider_name_rem = _cached_provider
                else:
                    ai_config_rem = await get_effective_ai_config(db, product_id=_rem_product_uuid)
                    provider_name_rem = (
                        (ai_config_rem.image_provider or "fal").strip().lower()
                        if ai_config_rem else "fal"
                    )

                image_provider_rem = get_image_provider_for_generation(provider_name_rem)

                logger.info(
                    "IMAGE_ENGINE_USED",
                    provider=provider_name_rem,
                    trial_id=trial_id,
                    source="generate_remaining_images_cached",
                )
                logger.info(
                    "REMAINING_STYLE_FROM_CACHE — using exact preview params",
                    trial_id=trial_id,
                    provider=provider_name_rem,
                    style_modifier_len=len(visual_style),
                    has_leading_prefix=bool(_rem_leading_prefix_override),
                    has_style_block=bool(_rem_style_block_override),
                    has_id_weight=_rem_id_weight is not None,
                )
            else:
                # Fallback: resolve from DB (legacy trials without cache)
                logger.warning(
                    "REMAINING_STYLE_NO_CACHE — falling back to DB resolution",
                    trial_id=trial_id,
                )
                _rem_style_negative_en = ""
                _rem_leading_prefix_override: str | None = None
                _rem_style_block_override: str | None = None
                _rem_id_weight: float | None = None
                _rem_true_cfg_override: float | None = None
                _rem_start_step_override: int | None = None
                _rem_num_inference_steps_override: int | None = None
                _rem_guidance_scale_override: float | None = None

                # Use product_id from trial for consistent AI config
                _rem_product_uuid = getattr(_trial_obj_rem, "product_id", None)
                ai_config_rem = await get_effective_ai_config(db, product_id=_rem_product_uuid)
                provider_name_rem = (
                    (ai_config_rem.image_provider or "fal").strip().lower()
                    if ai_config_rem else "fal"
                )
                image_provider_rem = get_image_provider_for_generation(provider_name_rem)

                logger.info(
                    "IMAGE_ENGINE_USED",
                    provider=provider_name_rem,
                    model=getattr(ai_config_rem, "image_model", "") if ai_config_rem else "",
                    trial_id=trial_id,
                    source="generate_remaining_images_fallback",
                )

                visual_style = (visual_style_modifier or "").strip() or (
                    (prompts[0].get("visual_style") or "").strip() if prompts else ""
                )

                _rem_vs_name = getattr(_trial_obj_rem, "visual_style_name", None) if _trial_obj_rem else None
                _vs_rem = await _resolve_visual_style_from_db(db, _rem_vs_name)
                if _vs_rem:
                    if _vs_rem.prompt_modifier:
                        visual_style = _vs_rem.prompt_modifier.strip()
                    _rem_style_negative_en = (_vs_rem.style_negative_en or "").strip()
                    _rem_leading_prefix_override = (_vs_rem.leading_prefix_override or "").strip() or None
                    _rem_style_block_override = (_vs_rem.style_block_override or "").strip() or None
                    if _vs_rem.id_weight is not None:
                        _rem_id_weight = float(_vs_rem.id_weight)
                    _rem_true_cfg_override = float(_vs_rem.true_cfg) if getattr(_vs_rem, "true_cfg", None) is not None else None
                    _rem_start_step_override = int(_vs_rem.start_step) if getattr(_vs_rem, "start_step", None) is not None else None
                    _rem_num_inference_steps_override = int(_vs_rem.num_inference_steps) if getattr(_vs_rem, "num_inference_steps", None) is not None else None
                    _rem_guidance_scale_override = float(_vs_rem.guidance_scale) if getattr(_vs_rem, "guidance_scale", None) is not None else None
                    logger.info(
                        "Resolved VisualStyle from DB for remaining pages",
                        style_name=_vs_rem.name,
                        has_override=bool(_rem_leading_prefix_override or _rem_style_block_override),
                        id_weight=_rem_id_weight,
                        id_weight_source="db" if _rem_id_weight is not None else "code_fallback",
                    )

                if not _vs_rem and visual_style and "pixar" in visual_style.lower():
                    visual_style = ""

                if visual_style:
                    from app.prompt_engine import personalize_style_prompt

                    visual_style = personalize_style_prompt(
                        visual_style,
                        child_name=_rem_child_name,
                        child_age=_rem_child_age,
                        child_gender=_rem_child_gender,
                    )

            # Load prompt templates from DB (same pattern as composed preview)
            from app.prompt_engine.constants import (
                DEFAULT_COVER_TEMPLATE_EN as _DEF_COVER_REM,
            )
            from app.prompt_engine.constants import (
                DEFAULT_INNER_TEMPLATE_EN as _DEF_INNER_REM,
            )
            from app.services.prompt_template_service import get_prompt_service as _get_tpl_rem

            _tpl_svc_rem = _get_tpl_rem()
            _cover_tpl_rem = await _tpl_svc_rem.get_template_en(db, "COVER_TEMPLATE", _DEF_COVER_REM)
            _inner_tpl_rem = await _tpl_svc_rem.get_template_en(db, "INNER_TEMPLATE", _DEF_INNER_REM)

            # Parallel image generation with concurrency limit
            from app.config import settings as _cfg_rem
            _gen_sem_rem = asyncio.Semaphore(_cfg_rem.image_concurrency)

            async def _gen_remaining_single(prompt_data: dict) -> tuple[int, str] | None:
                page_num = prompt_data["page_number"]
                visual_prompt = prompt_data["visual_prompt"]
                _is_v3 = prompt_data.get("v3_composed", False)
                async with _gen_sem_rem:
                    try:
                        result = await image_provider_rem.generate_consistent_image(
                            prompt=visual_prompt,
                            child_face_url=_face_ref_url,
                            clothing_prompt=clothing_description,
                            style_modifier=visual_style or prompt_data.get("visual_style") or "",
                            width=width,
                            height=height,
                            is_cover=(page_num == 0),
                            template_en=_cover_tpl_rem if page_num == 0 else _inner_tpl_rem,
                            style_negative_en=_rem_style_negative_en,
                            leading_prefix_override=_rem_leading_prefix_override,
                            style_block_override=_rem_style_block_override,
                            id_weight=_rem_id_weight,
                            true_cfg_override=_rem_true_cfg_override,
                            start_step_override=_rem_start_step_override,
                            num_inference_steps_override=_rem_num_inference_steps_override,
                            guidance_scale_override=_rem_guidance_scale_override,
                            child_gender=_rem_child_gender,
                            skip_compose=_is_v3,
                            precomposed_negative=prompt_data.get("negative_prompt", "") if _is_v3 else "",
                            reference_embedding=_face_embedding,
                            character_description=_rem_char_desc_for_images,
                        )
                        image_url = result[0] if isinstance(result, tuple) else result
                        if image_url:
                            logger.info(f"Generated image for page {page_num}")
                            return (page_num, image_url)
                    except Exception as e:
                        logger.error(
                            f"Failed to generate image for page {page_num}",
                            error=str(e),
                        )
                return None

            # Filter out front_matter pages (text-only, no image)
            rem_image_prompts = [
                p for p in prompts_to_generate
                if p.get("page_type", "inner") != "front_matter"
            ]
            gen_results_rem = await asyncio.gather(
                *[_gen_remaining_single(p) for p in rem_image_prompts],
                return_exceptions=True,
            )
            for r in gen_results_rem:
                if isinstance(r, tuple) and len(r) == 2:
                    generated_images[r[0]] = r[1]

            # ── Compose remaining images: text overlay + template frame ──
            if generated_images:
                import base64 as _b64_rem

                import httpx as _httpx_rem

                from app.models.book_template import PageTemplate as _PT_rem
                from app.services.page_composer import build_template_config as _build_tpl_cfg
                from app.services.page_composer import page_composer as _pc_rem
                from app.services.storage_service import storage_service as _ss_rem

                # Load page templates (product-specific, fallback to latest)
                _cover_tmpl: _PT_rem | None = None
                _inner_tmpl: _PT_rem | None = None
                _prod_id_rem = getattr(_trial_obj_rem, "product_id", None) if _trial_obj_rem else None
                if _prod_id_rem:
                    from sqlalchemy.orm import selectinload as _sel_rem

                    from app.models.product import Product as _Prod_rem
                    _rp_rem = await db.execute(
                        select(_Prod_rem)
                        .where(_Prod_rem.id == _prod_id_rem)
                        .options(
                            _sel_rem(_Prod_rem.inner_template),
                            _sel_rem(_Prod_rem.cover_template),
                        )
                    )
                    _prod_obj_rem = _rp_rem.scalar_one_or_none()
                    if _prod_obj_rem:
                        _cover_tmpl = _prod_obj_rem.cover_template
                        _inner_tmpl = _prod_obj_rem.inner_template

                if not _cover_tmpl or not _inner_tmpl:
                    from sqlalchemy import desc as _desc_rem
                    if not _cover_tmpl:
                        _ct_r = await db.execute(
                            select(_PT_rem)
                            .where(_PT_rem.page_type == "cover")
                            .order_by(_desc_rem(_PT_rem.updated_at))
                            .limit(1)
                        )
                        _cover_tmpl = _ct_r.scalar_one_or_none()
                    if not _inner_tmpl:
                        _it_r = await db.execute(
                            select(_PT_rem)
                            .where(_PT_rem.page_type == "inner")
                            .order_by(_desc_rem(_PT_rem.updated_at))
                            .limit(1)
                        )
                        _inner_tmpl = _it_r.scalar_one_or_none()

                _COMPOSE_DPI = 150
                _story_id_short = trial_id[:8]
                _text_map = {p["page_number"]: p.get("text", "") for p in prompts}
                _story_title_rem = getattr(_trial_obj_rem, "story_title", "") or ""

                composed_count = 0
                compose_fail_count = 0
                composed_images: dict[int, str] = {}

                for _pg_num, _raw_url in generated_images.items():
                    try:
                        _is_cov = (_pg_num == 0)
                        _tmpl = _cover_tmpl if _is_cov else _inner_tmpl
                        if not _tmpl:
                            composed_images[_pg_num] = _raw_url
                            continue

                        # Download raw AI image
                        async with _httpx_rem.AsyncClient(timeout=30) as _hc:
                            _resp = await _hc.get(_raw_url)
                            _resp.raise_for_status()
                            _img_b64 = _b64_rem.b64encode(_resp.content).decode()

                        _pg_text = _text_map.get(_pg_num, "")
                        if _is_cov:
                            _pg_text = _story_title_rem or _pg_text

                        _tpl_cfg = _build_tpl_cfg(_tmpl)
                        _composed_b64 = await asyncio.to_thread(
                            _pc_rem.compose_page,
                            image_base64=_img_b64,
                            text=_pg_text,
                            template_config=_tpl_cfg,
                            page_width_mm=297,
                            page_height_mm=210,
                            dpi=_COMPOSE_DPI,
                        )

                        # Upload composed image to GCS
                        _uploaded = await asyncio.to_thread(
                            _ss_rem.upload_multiple_images,
                            images={_pg_num: _composed_b64},
                            story_id=f"preview-{_story_id_short}",
                        )
                        composed_images[_pg_num] = _uploaded.get(_pg_num, _raw_url)
                        composed_count += 1
                    except Exception as _comp_err:
                        logger.warning(
                            f"Compose failed for page {_pg_num}, using raw image",
                            trial_id=trial_id,
                            error=str(_comp_err),
                        )
                        composed_images[_pg_num] = _raw_url
                        compose_fail_count += 1

                # Overwrite generated_images with composed versions
                if composed_images:
                    generated_images.update(composed_images)

                logger.info(
                    "REMAINING_PAGES_COMPOSED",
                    trial_id=trial_id,
                    composed=composed_count,
                    failed=compose_fail_count,
                    total=len(generated_images),
                )

            # Save all images (composed versions)
            if generated_images:
                await trial_service.save_remaining_images(
                    uuid.UUID(trial_id),
                    generated_images,
                )

            # Override status: PENDING (musteri onayini bekle) instead of COMPLETED
            _trial_for_status = await db.execute(
                select(StoryPreview).where(StoryPreview.id == uuid.UUID(trial_id))
            )
            _trial_obj_status = _trial_for_status.scalar_one_or_none()
            if _trial_obj_status:
                _trial_obj_status.status = "PENDING"
                await db.commit()
                logger.info("TRIAL_REMAINING_STATUS_PENDING", trial_id=trial_id)

            # ── Generate PDF and send email ──────────────────────────
            try:
                from sqlalchemy.orm import selectinload

                from app.models.book_template import BackCoverConfig, PageTemplate
                from app.models.product import Product
                from app.services.email_service import email_service
                from app.services.page_composer import (
                    build_template_config,
                    page_composer,
                )
                from app.services.pdf_service import PDFService
                from app.services.storage_service import storage_service

                # Reload trial from DB
                trial_result = await db.execute(
                    select(StoryPreview).where(StoryPreview.id == uuid.UUID(trial_id))
                )
                trial = trial_result.scalar_one_or_none()
                if not trial:
                    raise ValueError(f"Trial {trial_id} not found for PDF/email")

                # Fetch templates
                tpl_result = await db.execute(
                    select(PageTemplate).where(PageTemplate.is_active == True)
                )
                templates_map: dict[str, PageTemplate] = {}
                for t in tpl_result.scalars().all():
                    if t.page_type not in templates_map:
                        templates_map[t.page_type] = t

                inner_template = templates_map.get("inner")
                _cover_template = templates_map.get("cover")
                _back_template = templates_map.get("back")
                ded_template = templates_map.get("dedication")

                page_width_mm = inner_template.page_width_mm if inner_template else 297.0
                page_height_mm = inner_template.page_height_mm if inner_template else 210.0
                bleed_mm = inner_template.bleed_mm if inner_template else 3.0

                # Override from product if linked
                product = None
                if getattr(trial, "product_id", None):
                    prod_r = await db.execute(
                        select(Product)
                        .where(Product.id == trial.product_id)
                        .options(
                            selectinload(Product.inner_template),
                            selectinload(Product.cover_template),
                        )
                    )
                    product = prod_r.scalar_one_or_none()
                    if product:
                        if product.inner_template:
                            inner_template = product.inner_template
                        if product.cover_template:
                            _cover_template = product.cover_template
                        page_width_mm = inner_template.page_width_mm if inner_template else page_width_mm
                        page_height_mm = inner_template.page_height_mm if inner_template else page_height_mm
                        bleed_mm = inner_template.bleed_mm if inner_template else bleed_mm

                # Collect all page image URLs (preview_images + page_images merged)
                # NOTE: These images are ALREADY composed (text overlay applied).
                # Do NOT re-compose — otherwise text appears twice.
                all_images = {**(trial.preview_images or {}), **(trial.page_images or {})}

                composed_pages: list[dict] = []
                story_pages = trial.story_pages or []
                for page in story_pages:
                    page_num = page.get("page_number")
                    if page_num is None:
                        continue
                    if page.get("page_type") == "front_matter":
                        continue

                    compose_text = page.get("text", "")
                    if page_num == 0:
                        compose_text = trial.story_title or compose_text

                    # Use already-composed image URL directly (no re-composition)
                    image_url = all_images.get(str(page_num)) or generated_images.get(page_num)

                    composed_pages.append({
                        "page_number": page_num,
                        "text": compose_text,
                        "image_url": image_url,
                    })

                # Compose dedication page
                dedication_b64: str | None = None
                ded_note = getattr(trial, "dedication_note", None)
                if not ded_note and ded_template:
                    ded_text = getattr(ded_template, "dedication_default_text", None) or ""
                    if ded_text:
                        ded_note = ded_text.replace("{child_name}", trial.child_name or "")
                if ded_note:
                    try:
                        ded_cfg = build_template_config(ded_template) if ded_template else {}
                        dedication_b64 = page_composer.compose_dedication_page(
                            text=ded_note, template_config=ded_cfg, dpi=300,
                        )
                    except Exception as ded_err:
                        logger.warning("Dedication compose failed for PDF", error=str(ded_err))

                # Back cover config — pass ORM object directly (render_back_cover uses attribute access)
                back_cover_config = None
                audio_url = getattr(trial, "audio_file_url", None)
                try:
                    bc_result = await db.execute(
                        select(BackCoverConfig)
                        .where(BackCoverConfig.is_active == True)
                        .where(BackCoverConfig.is_default == True)
                    )
                    back_cover_config = bc_result.scalar_one_or_none()
                except Exception:
                    pass

                # Extract cover image URL and filter it from story pages (avoid duplicate)
                cover_image_url: str | None = None
                story_pages_no_cover: list[dict] = []
                for p in composed_pages:
                    if p.get("page_number") == 0:
                        cover_image_url = p.get("image_url")
                    else:
                        story_pages_no_cover.append(p)

                _n_story = len(story_pages_no_cover)
                _has_ded = 1 if dedication_b64 else 0
                _has_back = 1 if back_cover_config else 0
                _inner_tpl_cfg = build_template_config(inner_template) if inner_template else {}
                pdf_data = {
                    "story_title": trial.story_title,
                    "child_name": trial.child_name,
                    "story_pages": story_pages_no_cover,
                    "cover_image_url": cover_image_url,
                    "dedication_image_base64": dedication_b64,
                    "back_cover_config": back_cover_config,
                    "audio_qr_url": audio_url,
                    "page_width_mm": page_width_mm,
                    "page_height_mm": page_height_mm,
                    "bleed_mm": bleed_mm,
                    "template_config": _inner_tpl_cfg,
                    "images_precomposed": True,
                    "expected_story_pages": _n_story,
                    "expected_total_pages": 1 + _has_ded + _n_story + _has_back,
                }

                pdf_service = PDFService()
                pdf_bytes = pdf_service.generate_book_pdf_from_preview(pdf_data)
                pdf_url: str | None = None

                if pdf_bytes:
                    pdf_url = storage_service.upload_pdf(
                        pdf_bytes=pdf_bytes,
                        order_id=str(trial.id),
                    )
                    logger.info("PDF generated and uploaded", trial_id=trial_id, pdf_url=pdf_url)

                    # Save PDF URL to trial
                    trial.admin_notes = (trial.admin_notes or "") + f"\n\nPDF URL: {pdf_url}"
                    await db.commit()
                    
                # [NEW] Trigger coloring book generation if requested
                if trial.has_coloring_book:
                    try:
                        from app.workers.enqueue import enqueue_job
                        logger.info("Enqueuing trial coloring book generation", trial_id=trial_id)
                        await enqueue_job("generate_coloring_book_for_trial", trial_id=str(trial_id))
                    except Exception as _cb_err:
                        logger.error(
                            "Failed to enqueue trial coloring book generation",
                            trial_id=trial_id,
                            error=str(_cb_err)
                        )
                        trial.admin_notes = (trial.admin_notes or "") + f"\n\nBoyama kitabi olusturma siraya alinamadi: {str(_cb_err)}"
                        await db.commit()

                # Send approval email with confirmation link (mukerrer email onleme)
                _email_already_sent = (
                    _is_full_retry
                    and trial.admin_notes
                    and "TRIAL_APPROVAL_EMAIL_SENT" in (trial.admin_notes or "")
                )
                if _email_already_sent:
                    logger.info(
                        "TRIAL_APPROVAL_EMAIL_SKIP_DUPLICATE",
                        trial_id=trial_id,
                        msg="Email onceki retry'da zaten gonderildi",
                    )
                elif trial.parent_email:
                    try:
                        from app.config import get_settings as _get_settings_email
                        _email_settings = _get_settings_email()

                        pages_for_email = [
                            {
                                "page_number": p["page_number"],
                                "text": p.get("text", ""),
                                "image_url": (
                                    all_images.get(str(p["page_number"]))
                                    or generated_images.get(p["page_number"])
                                ),
                            }
                            for p in composed_pages
                        ]
                        _confirmation_url = (
                            f"{_email_settings.frontend_url}/confirm/"
                            f"{trial.confirmation_token}"
                        )
                        email_service.send_story_email_with_confirmation(
                            recipient_email=trial.parent_email,
                            recipient_name=trial.parent_name or trial.parent_email,
                            child_name=trial.child_name,
                            story_title=trial.story_title,
                            story_pages=pages_for_email,
                            confirmation_url=_confirmation_url,
                            product_price=(
                                float(trial.product_price)
                                if trial.product_price
                                else None
                            ),
                        )
                        # Email gonderildi flag'i — mukerrer email onleme
                        trial.admin_notes = (trial.admin_notes or "") + "\nTRIAL_APPROVAL_EMAIL_SENT"
                        await db.commit()
                        logger.info(
                            "TRIAL_APPROVAL_EMAIL_SENT",
                            trial_id=trial_id,
                            email=_mask_email(trial.parent_email),
                        )
                    except Exception as mail_err:
                        logger.warning(
                            "Approval email sending failed (PDF still saved)",
                            trial_id=trial_id,
                            error=str(mail_err),
                        )
                        trial.admin_notes = (trial.admin_notes or "") + f"\n\nOnay e-postası gönderilemedi: {str(mail_err)[:300]}"
                        await db.commit()

            except Exception as pdf_mail_err:
                logger.exception(
                    "PDF/Email generation failed",
                    trial_id=trial_id,
                    error=str(pdf_mail_err),
                )

            logger.info(
                "Trial completion finished",
                trial_id=trial_id,
                images_generated=len(generated_images),
            )

        except Exception as e:
            logger.exception("Background completion failed", error=str(e))
            # Mark trial as FAILED so it doesn't stay stuck
            try:
                from app.core.database import async_session_factory

                async with async_session_factory() as err_db:

                    _err_r = await err_db.execute(
                        select(StoryPreview).where(StoryPreview.id == uuid.UUID(trial_id))
                    )
                    _err_trial = _err_r.scalar_one_or_none()
                    if _err_trial and _err_trial.status not in ("COMPLETED", "FAILED", "PENDING", "CONFIRMED"):
                        _err_trial.status = "FAILED"
                        await err_db.commit()
                        logger.info("TRIAL_REMAINING_MARKED_FAILED", trial_id=trial_id)
            except Exception as status_err:
                logger.warning("Could not mark trial as FAILED", error=str(status_err))


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
) -> dict:
    """Create an Iyzico checkout session for a trial (Phase 2 payment).

    Returns payment_url for redirect to Iyzico hosted checkout page.
    """
    from decimal import Decimal

    import iyzipay

    from app.config import settings

    # ── Validate trial ──
    try:
        trial_uuid = uuid.UUID(trial_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Geçersiz trial ID")

    result = await db.execute(select(StoryPreview).where(StoryPreview.id == trial_uuid))
    trial = result.scalar_one_or_none()

    if not trial:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trial bulunamadı")

    _verify_trial_access(trial, x_trial_token)

    if trial.status not in [
        PreviewStatus.PREVIEW_GENERATED.value,
        PreviewStatus.PAYMENT_PENDING.value,
    ]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Trial bu durumda ödeme başlatılamaz: {trial.status}",
        )

    if not settings.iyzico_api_key or not settings.iyzico_secret_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Ödeme sistemi henüz yapılandırılmamış.",
        )

    final_amount = Decimal(str(trial.product_price or 0))
    
    # Add coloring book price if requested
    coloring_book_price = Decimal("0")
    if getattr(trial, "has_coloring_book", False):
        from app.models.coloring_book import ColoringBookProduct
        
        # Get active coloring book config
        coloring_config_result = await db.execute(
            select(ColoringBookProduct).where(ColoringBookProduct.active == True).limit(1)
        )
        coloring_config = coloring_config_result.scalar_one_or_none()
        
        if coloring_config:
            coloring_book_price = coloring_config.discounted_price or coloring_config.base_price
            final_amount += coloring_book_price
            logger.info(
                "Coloring book added to payment",
                trial_id=trial_id,
                coloring_book_price=str(coloring_book_price),
            )
    
    if final_amount <= Decimal("0"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bu ürün ücretsiz — promo kodu ile tamamlayın.",
        )

    options = {
        "api_key": settings.iyzico_api_key,
        "secret_key": settings.iyzico_secret_key,
        "base_url": settings.iyzico_base_url,
    }

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

    callback_url = f"{settings.frontend_url}/api/payment/callback?trialId={trial.id}"

    iyzico_request = {
        "locale": "tr",
        "conversationId": str(trial.id),
        "price": str(final_amount),
        "paidPrice": str(final_amount),
        "currency": "TRY",
        "basketId": str(trial.id)[:16],
        "paymentGroup": "PRODUCT",
        "callbackUrl": callback_url,
        "enabledInstallments": [1, 2, 3, 6],
        "buyer": buyer,
        "shippingAddress": address,
        "billingAddress": address,
        "basketItems": [
            {
                "id": str(trial.id)[:16],
                "name": "Kişiselleştirilmiş Hikaye Kitabı",
                "category1": "Kitap",
                "category2": "Çocuk Kitabı",
                "itemType": "VIRTUAL",
                "price": str(Decimal(str(trial.product_price or 0))),
            }
        ],
    }
    
    # Add coloring book as separate basket item if requested
    if coloring_book_price > Decimal("0"):
        iyzico_request["basketItems"].append({
            "id": f"{str(trial.id)[:12]}_clr",
            "name": "Boyama Kitabı",
            "category1": "Kitap",
            "category2": "Çocuk Kitabı",
            "itemType": "VIRTUAL",
            "price": str(coloring_book_price),
        })

    try:
        checkout_form = iyzipay.CheckoutFormInitialize().create(iyzico_request, options)
        import json as _json
        result_dict = _json.loads(checkout_form.read().decode("utf-8"))
    except Exception as exc:
        logger.error("TRIAL_IYZICO_CHECKOUT_ERROR", trial_id=trial_id, error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Ödeme sayfası oluşturulamadı. Lütfen tekrar deneyin.",
        ) from exc

    if result_dict.get("status") != "success":
        error_msg = result_dict.get("errorMessage", "Bilinmeyen hata")
        logger.error("TRIAL_IYZICO_CHECKOUT_FAILED", trial_id=trial_id, error=error_msg)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Ödeme sayfası oluşturulamadı: {error_msg}",
        )

    iyzico_token = result_dict.get("token", "")
    payment_page_url = result_dict.get("paymentPageUrl", "")

    # Store pending token so verify-payment can confirm it
    trial.payment_reference = f"iyzico_pending:{iyzico_token}"
    trial.status = PreviewStatus.PAYMENT_PENDING.value
    await db.commit()

    logger.info(
        "TRIAL_IYZICO_CHECKOUT_CREATED",
        trial_id=trial_id,
        token_prefix=iyzico_token[:10] if iyzico_token else "N/A",
    )

    return {
        "success": True,
        "payment_url": payment_page_url,
        "trial_id": trial_id,
    }


class VerifyTrialPaymentRequest(BaseModel):
    token: str = Field(..., min_length=1, max_length=500)


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
    import json as _json

    import iyzipay

    from app.config import settings

    try:
        trial_uuid = uuid.UUID(trial_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Geçersiz trial ID")

    result = await db.execute(select(StoryPreview).where(StoryPreview.id == trial_uuid))
    trial = result.scalar_one_or_none()

    if not trial:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trial bulunamadı")

    _verify_trial_access(trial, x_trial_token)

    if not settings.iyzico_api_key or not settings.iyzico_secret_key:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Ödeme sistemi yapılandırılmamış")

    options = {
        "api_key": settings.iyzico_api_key,
        "secret_key": settings.iyzico_secret_key,
        "base_url": settings.iyzico_base_url,
    }

    try:
        verify_result = iyzipay.CheckoutForm().retrieve(
            {"locale": "tr", "conversationId": trial_id, "token": request.token},
            options,
        )
        result_dict = _json.loads(verify_result.read().decode("utf-8"))
    except Exception as exc:
        logger.error("TRIAL_IYZICO_VERIFY_ERROR", trial_id=trial_id, error=str(exc))
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Ödeme doğrulanamadı") from exc

    iyzico_status = result_dict.get("paymentStatus")

    if iyzico_status != "SUCCESS":
        error_msg = result_dict.get("errorMessage", "Ödeme başarısız")
        logger.warning("TRIAL_IYZICO_VERIFY_FAILED", trial_id=trial_id, status=iyzico_status, error=error_msg)
        return {"success": False, "error": error_msg}

    # Mark trial payment as verified
    trial.payment_reference = f"iyzico_paid:{request.token}"
    await db.commit()

    logger.info("TRIAL_IYZICO_VERIFY_OK", trial_id=trial_id)

    return {"success": True, "trial_id": trial_id, "payment_reference": f"iyzico_paid:{request.token}"}


async def _create_coloring_book_order_from_trial(
    trial: StoryPreview,
    db: AsyncSession,
) -> Order | None:
    """
    Create separate coloring book order from trial.

    Args:
        trial: Story preview/trial
        db: Database session

    Returns:
        Coloring book Order or None if failed
    """
    from app.models.coloring_book import ColoringBookProduct

    try:
        # Get active coloring book config
        config_result = await db.execute(
            select(ColoringBookProduct).where(ColoringBookProduct.active == True).limit(1)
        )
        coloring_config = config_result.scalar_one_or_none()

        if not coloring_config:
            logger.error("No active coloring book product configuration")
            return None

        # Get product, scenario, visual_style from trial
        # NOTE: trial.product_id is already a UUID object from asyncpg — do NOT wrap with uuid.UUID()
        product_result = await db.execute(
            select(Product).where(Product.id == trial.product_id)
        )
        product = product_result.scalar_one_or_none()

        if not product:
            logger.error("Product not found for trial", trial_id=str(trial.id))
            return None

        scenario_result = await db.execute(
            select(Scenario).where(Scenario.name == trial.scenario_name)
        )
        scenario = scenario_result.scalar_one_or_none()

        if not scenario:
            logger.error("Scenario not found", scenario_name=trial.scenario_name)
            return None

        visual_style_result = await db.execute(
            select(VisualStyle).where(VisualStyle.name == trial.visual_style_name)
        )
        visual_style = visual_style_result.scalar_one_or_none()

        if not visual_style:
            logger.error("Visual style not found", visual_style_name=trial.visual_style_name)
            return None

        # Find main order for this trial (if exists) to link coloring book to it
        # Main order might not exist yet (created later by generate_remaining_images_background)
        # So we'll link it later when main order is created
        main_order_result = await db.execute(
            select(Order)
            .where(Order.user_id == trial.lead_user_id)
            .where(Order.child_name == trial.child_name)
            .where(Order.status.in_([OrderStatus.PAID, OrderStatus.PROCESSING, OrderStatus.READY_FOR_PRINT]))
            .where(Order.is_coloring_book == False)
            .where(Order.payment_reference == trial.payment_reference)
            .order_by(Order.created_at.desc())
            .limit(1)
        )
        main_order = main_order_result.scalar_one_or_none()

        # Create coloring book order
        coloring_order = Order(
            user_id=trial.lead_user_id,
            product_id=product.id,
            scenario_id=scenario.id,
            visual_style_id=visual_style.id,
            child_name=trial.child_name,
            child_age=trial.child_age,
            child_gender=trial.child_gender,
            selected_outcomes=trial.learning_outcomes or [],
            status=OrderStatus.PAID,  # Payment already done via main order
            payment_amount=coloring_config.discounted_price or coloring_config.base_price,
            payment_provider="iyzico",
            payment_reference=trial.payment_reference,  # Same payment as main order
            is_coloring_book=True,  # CRITICAL FLAG
            shipping_address={
                "fullName": trial.parent_name,
                "email": trial.parent_email,
                "phone": trial.parent_phone or "",
            },
            child_photo_url=trial.child_photo_url,
            face_embedding=trial.face_embedding,
        )

        db.add(coloring_order)
        await db.commit()
        await db.refresh(coloring_order)

        # Link main order to coloring book (if main order exists)
        if main_order:
            main_order.coloring_book_order_id = coloring_order.id
            await db.commit()
            logger.info(
                "Linked main order to coloring book",
                main_order_id=str(main_order.id),
                coloring_order_id=str(coloring_order.id),
            )

        logger.info(
            "Coloring book order created",
            coloring_order_id=str(coloring_order.id),
            trial_id=str(trial.id),
            price=str(coloring_order.payment_amount),
            linked_to_main=main_order is not None,
        )

        return coloring_order

    except Exception as e:
        logger.error("Failed to create coloring book order", error=str(e), trial_id=str(trial.id))
        return None

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

    if not settings.iyzico_api_key or not settings.iyzico_secret_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Ödeme sistemi yapılandırılmamış.",
        )

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

    options = {
        "api_key": settings.iyzico_api_key,
        "secret_key": settings.iyzico_secret_key,
        "base_url": settings.iyzico_base_url,
    }

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

    if not settings.iyzico_api_key or not settings.iyzico_secret_key:
        return RedirectResponse(url=f"{settings.frontend_url}/payment-failed?error=Sistem_Hatasi")

    options = {
        "api_key": settings.iyzico_api_key,
        "secret_key": settings.iyzico_secret_key,
        "base_url": settings.iyzico_base_url,
    }

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

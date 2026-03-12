"""Trial generation pipeline: story generation, preview images, and remaining images.

These functions are the heavy AI generation workers extracted from the API router.
They run as Arq background tasks (or FastAPI BackgroundTask fallbacks).
"""

import asyncio
import uuid

import structlog
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.order import Order, OrderStatus
from app.models.product import Product
from app.models.scenario import Scenario
from app.models.story_preview import PreviewStatus, StoryPreview
from app.models.visual_style import VisualStyle

logger = structlog.get_logger()

_V3_BLOCK_MSG = "V2_LABEL_BLOCKED: expected v3"


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------


async def resolve_visual_style_from_db(
    db: AsyncSession,
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


def select_preview_prompts(all_prompts: list[dict], num_inner: int = 2) -> list[dict]:
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

    cover_pages = [p for p in all_prompts if p.get("page_type") == "cover"]
    result.extend(cover_pages)

    front_matter_pages = [p for p in all_prompts if p.get("page_type") == "front_matter"]
    front_matter_pages.sort(key=lambda x: x.get("page_number", 999))
    result.extend(front_matter_pages)

    story_pages = [p for p in all_prompts if p.get("page_type") not in ("cover", "front_matter", "backcover")]
    story_pages.sort(key=lambda x: x.get("page_number", 999))
    result.extend(story_pages[:num_inner])

    return result


# ---------------------------------------------------------------------------
# Phase 1: Story generation
# ---------------------------------------------------------------------------


async def generate_trial_story_inner(
    trial_id: str,
    request_data: dict,
) -> None:
    """Generate story via Gemini and enqueue preview image generation.

    Runs inside an Arq worker (or as a FastAPI BackgroundTask fallback).
    """
    from uuid import UUID as _UUID

    from sqlalchemy import select as _sel

    from app.core.database import async_session_factory
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

            # %% Idempotency: skip Gemini if story already generated (Arq retry) %%
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
                _retry_prompts = select_preview_prompts(_cache.get("prompts") or [], num_inner=2)
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
                    await generate_preview_images_inner(
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

            # %% Fetch scenario from DB %%
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


            # Trial preview için yüz analizi gerekmez — görsel üretimde yapılacak
            _visual_char_desc = f"a {child_age}-year-old child named {child_name}"

            # %% Resolve visual style overrides for story pre-compose %%
            _story_leading_prefix_override: str | None = None
            _story_style_block_override: str | None = None
            if visual_style_name:
                try:
                    _story_vs = await resolve_visual_style_from_db(db, visual_style_name)
                    if _story_vs:
                        _story_leading_prefix_override = (_story_vs.leading_prefix_override or "").strip() or None
                        _story_style_block_override = (_story_vs.style_block_override or "").strip() or None
                except Exception:
                    pass

            # %% Resolve scenario outfit (gender-specific, scenario-first) %%
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

            # %% Generate story via Gemini %%
            story_response, final_pages, fixed_outfit, blueprint_json = (
                await gemini_service.generate_story_structured(
                    scenario=scenario,
                    requested_version="v3",
                    child_name=child_name,
                    child_age=child_age,
                    child_gender=child_gender,
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

            # %% Deterministic title %%
            from app.services.order_helpers import (
                force_deterministic_title as _force_deterministic_title,
            )

            story_response.title = _force_deterministic_title(
                child_name=child_name,
                scenario_name=scenario_name or getattr(scenario, "name", ""),
                original_title=story_response.title,
            )

            # %% Build serializable pages %%
            story_pages: list[dict] = []
            generated_prompts: list[dict] = []
            for page in final_pages:
                page_text = page.text
                if page.page_number == 0:
                    page_text = story_response.title or child_name or ""

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

            # %% V3 pipeline validation %%
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

            # %% Page manifest %%
            page_manifest = PageManifest.from_final_pages(
                title=story_response.title,
                child_name=child_name,
                final_pages=final_pages,
                pipeline_version=_pipeline_ver,
                include_dedication=True,
                include_backcover=True,
            )

            # %% QA checks %%
            from app.prompt_engine import run_qa_checks
            from app.prompt_engine.scenario_bible import normalize_location_key_for_anchors

            _loc_key = (
                getattr(scenario, "theme_key", None)
                or getattr(scenario, "location_en", "")
                or getattr(scenario, "name", "")
            )
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
                    raise ValueError("QA check failed   story generation rejected")
                logger.warning("QA checks found issues (non-blocking)", failures=qa_report["failures"][:10])

            # %% Persist story data to trial %%
            _cover_count = sum(1 for p in story_pages if p.get("page_number") == 0)
            _inner_count = sum(1 for p in story_pages if (p.get("page_number") or 0) > 0 and p.get("page_type") != "backcover")
            _bc_count = sum(1 for p in story_pages if p.get("page_type") == "backcover")
            logger.info(
                "STORY_PAGES_PERSIST_AUDIT",
                trial_id=trial_id,
                total=len(story_pages),
                cover=_cover_count,
                inner=_inner_count,
                backcover=_bc_count,
                expected_inner=page_count,
                page_numbers=[p.get("page_number") for p in story_pages],
            )
            if _inner_count < page_count:
                logger.error(
                    "STORY_PAGES_INNER_COUNT_SHORT",
                    trial_id=trial_id,
                    expected=page_count,
                    actual=_inner_count,
                )
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

            # %% TWO-PHASE: Generate visual prompts for preview pages only %%
            _preview_pages_text_only = select_preview_prompts(story_pages, num_inner=2)

            for page in _preview_pages_text_only:
                if "text" in page and "text_tr" not in page:
                    page["text_tr"] = page["text"]

            logger.info(
                "Generating visual prompts for preview pages",
                trial_id=trial_id,
                preview_page_count=len(_preview_pages_text_only),
            )

            from app.prompt_engine import build_character_bible
            from app.prompt_engine.scenario_bible import normalize_location_key_for_anchors

            _raw_loc = getattr(scenario, "theme_key", None) or getattr(scenario, "location_en", "") or scenario.name
            location_key = normalize_location_key_for_anchors(str(_raw_loc or ""))

            _child_outfit_block = blueprint_json.get("child_outfit") or {}
            _blueprint_outfit = _child_outfit_block.get("description_en", "").strip()
            _blueprint_hair = _child_outfit_block.get("hair_style_en", "").strip()
            _effective_outfit = (fixed_outfit or "").strip() or _blueprint_outfit
            # Extract companion from blueprint for CharacterBible
            _side_char_trial = blueprint_json.get("side_character") or {}
            _trial_comp_name = _side_char_trial.get("name", "")
            _trial_comp_species = _side_char_trial.get("type", "")
            _trial_comp_appearance = _side_char_trial.get("appearance", "")

            character_bible = build_character_bible(
                child_name=child_name,
                child_age=child_age,
                child_gender=child_gender or "erkek",
                child_description=_visual_char_desc,
                fixed_outfit=_effective_outfit,
                hair_style=_blueprint_hair,
                companion_name=_trial_comp_name,
                companion_species=_trial_comp_species,
                companion_appearance=_trial_comp_appearance,
            )

            try:
                _preview_enhanced = await gemini_service.enhance_pages_with_visual_prompts(
                    story_pages=_preview_pages_text_only,
                    blueprint=blueprint_json,
                    character_bible=character_bible,
                    visual_style=visual_style or "children's book illustration",
                    location_key=location_key,
                    likeness_hint="",
                    has_pulid=bool(child_photo_url),
                    leading_prefix_override=_story_leading_prefix_override,
                    style_block_override=_story_style_block_override,
                )

                _preview_enhanced_dict = []
                for i, page in enumerate(_preview_enhanced):
                    original_page = _preview_pages_text_only[i] if i < len(_preview_pages_text_only) else {}
                    page_text = page.get("text_tr") or page.get("text") or original_page.get("text", "")

                    page_dict = {
                        "page_number": page.get("page_number", page.get("page", 0)),
                        "text": page_text,
                        "visual_prompt": page.get("image_prompt_en", ""),
                        "image_prompt_en": page.get("image_prompt_en", ""),
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
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Görsel promptları oluşturulamadı. Lütfen tekrar deneyin."
                ) from _preview_err

            # %% Enqueue preview image generation %%
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
                await generate_preview_images_inner(
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


# ---------------------------------------------------------------------------
# Phase 1: Preview image generation
# ---------------------------------------------------------------------------


async def generate_preview_images_inner(
    trial_id: str,
    prompts: list[dict],
    child_photo_url: str | None,
    visual_style: str | None,
    product_name: str | None = None,
    story_title: str = "",
    clothing_description: str = "",
    visual_style_name: str | None = None,
) -> None:
    """Actual preview image generation logic, runs inside trial semaphore."""
    from app.core.database import async_session_factory
    from app.services.ai.image_provider_dispatch import (
        get_effective_ai_config,
        get_image_provider_for_generation,
    )
    from app.services.trial_service import get_trial_service
    from app.utils.resolution_calc import DEFAULT_GENERATION_A4_LANDSCAPE
    width, height = DEFAULT_GENERATION_A4_LANDSCAPE

    from app.services.ai.face_service import resolve_face_reference
    from app.services.storage_service import storage_service as _ss
    _face_ref_url, _original_photo_url, _face_embedding = await resolve_face_reference(child_photo_url, _ss)

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

            await trial_service.update_to_generating(uuid.UUID(trial_id))

            actual_style = ""
            style_negative_en = ""
            leading_prefix_override = None
            style_block_override = None
            _preview_id_weight: float | None = None
            _preview_true_cfg_override: float | None = None
            _preview_start_step_override: int | None = None
            _preview_num_inference_steps_override: int | None = None
            _preview_guidance_scale_override: float | None = None
            vs = await resolve_visual_style_from_db(db, visual_style_name)
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
                        original_photo_url=_original_photo_url,
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

            image_prompts = [
                p for p in prompts
                if p.get("page_type", "inner") != "front_matter"
            ]

            _backcover_prompt_data = next(
                (p for p in image_prompts if p.get("page_type") == "backcover"), None
            )
            story_image_prompts = [p for p in image_prompts if p.get("page_type") != "backcover"]

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

            if _backcover_prompt_data and _backcover_prompt_data.get("visual_prompt"):
                try:
                    _bc_clothing = clothing_description
                    if not _bc_clothing:
                        try:
                            _trial_rec = await trial_service.get_trial_by_id(uuid.UUID(trial_id))
                            _scenario_id = getattr(_trial_rec, "scenario_id", None)
                            if _scenario_id:
                                from sqlalchemy import select as _selBC

                                from app.models.scenario import Scenario as _ScenBC
                                _sc_res = await db.execute(_selBC(_ScenBC).where(_ScenBC.id == _scenario_id))
                                _sc = _sc_res.scalar_one_or_none()
                                if _sc:
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

                    _bc_result = await _gen_preview_single(_backcover_prompt_data, custom_clothing=_bc_clothing)
                    if isinstance(_bc_result, tuple) and len(_bc_result) == 2:
                        preview_images["backcover"] = _bc_result[1]
                        logger.info("BACK_COVER_IMAGE_GENERATED", trial_id=trial_id, clothing_used=_bc_clothing[:60] if _bc_clothing else "none")
                except Exception as _bc_img_err:
                    logger.warning("BACK_COVER_IMAGE_FAILED", trial_id=trial_id, error=str(_bc_img_err))

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


# ---------------------------------------------------------------------------
# Phase 1: Composed preview generation (with text overlay)
# ---------------------------------------------------------------------------


async def generate_composed_preview_inner(
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
) -> None:
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
    _face_ref_url, _original_photo_url, _face_embedding = await resolve_face_reference(child_photo_url, _ss_comp)

    _char_desc_for_images = ""
    if _face_ref_url:
        try:
            from app.services.ai.face_analyzer_service import get_face_analyzer as _get_fa2
            _fa2 = _get_fa2()
            # Use "AI Director" mode for concise description (30-50 words) to avoid prompt dilution
            _char_desc_for_images = await _fa2.analyze_for_ai_director(
                image_source=_face_ref_url,
                child_name=child_name,
                child_age=child_age,
                child_gender=child_gender or "",
            )
        except Exception as _fa2_err:
            logger.warning(
                "Preview image face analysis failed   no CHARACTER ANCHOR",
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

            actual_style = ""
            _comp_vs_leading_prefix: str | None = None
            _comp_vs_style_block: str | None = None
            _comp_vs_style_negative = ""
            _comp_true_cfg_override: float | None = None
            _comp_start_step_override: int | None = None
            _comp_num_inference_steps_override: int | None = None
            _comp_guidance_scale_override: float | None = None
            vs = await resolve_visual_style_from_db(db, visual_style_name)
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
                actual_style = visual_style if "pixar" not in (visual_style or "").lower() else ""

            from app.prompt_engine import personalize_style_prompt

            actual_style = personalize_style_prompt(
                actual_style,
                child_name=child_name,
                child_age=child_age,
                child_gender=child_gender or "",
            )

            # %% PERSIST resolved style params to trial cache %%
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
                        "PREVIEW_STYLE_CACHED   remaining pages will reuse these exact params",
                        trial_id=trial_id,
                        provider=provider_name,
                        style_modifier_len=len(actual_style),
                        has_leading_prefix=bool(_comp_vs_leading_prefix),
                        has_style_block=bool(_comp_vs_style_block),
                    )
            except Exception as _cache_err:
                logger.warning("Failed to cache resolved style", error=str(_cache_err))

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
                        original_photo_url=_original_photo_url,
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

            composed_urls: dict[int, str] = {}
            PREVIEW_DPI = 300  # Print-quality DPI (was 150 → low-res PDFs)
            story_id = trial_id[:8]

            for page_num, image_url in preview_images.items():
                try:
                    _is_cover = page_num == 0

                    # COVER: Gemini already renders the title natively via is_cover=True +
                    # story_title parameter. PIL compose on top would double-render (or worse,
                    # write wrong text if story_title arrives empty). Use the raw Gemini image.
                    if _is_cover:
                        composed_urls[page_num] = image_url
                        logger.info(
                            "COVER_COMPOSE_SKIPPED: using raw Gemini image (title rendered natively)",
                            page_num=page_num,
                        )
                        continue

                    template = inner_template
                    if not template:
                        composed_urls[page_num] = image_url
                        continue

                    async with httpx.AsyncClient(timeout=30) as client:
                        resp = await client.get(image_url)
                        resp.raise_for_status()
                        image_b64 = base64.b64encode(resp.content).decode("utf-8")

                    page_text = ""
                    for p in prompts:
                        if p["page_number"] == page_num:
                            page_text = p.get("text", "")
                            break

                    if False:  # was: if _is_cover — now cover is handled above
                        page_text = story_title or ""

                    template_config = build_template_config(template)

                    composed_b64 = await asyncio.to_thread(
                        page_composer.compose_page,
                        image_base64=image_b64,
                        text=page_text,
                        template_config=template_config,
                        page_width_mm=297,
                        page_height_mm=210,
                        dpi=PREVIEW_DPI,
                    )

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

            # --- Compose dedication page ---
            try:
                from sqlalchemy import desc as _desc_

                ded_result = await db.execute(
                    select(PageTemplate)
                    .where(PageTemplate.page_type == "dedication", PageTemplate.is_active == True)
                    .order_by(_desc_(PageTemplate.updated_at))
                    .limit(1)
                )
                ded_tpl = ded_result.scalar_one_or_none()

                # Never use AI story content as dedication text.
                # The front_matter prompt contains the opening story scene, not an ithaf message.
                if ded_tpl and getattr(ded_tpl, 'dedication_default_text', None):
                    ded_text = ded_tpl.dedication_default_text.replace('{child_name}', child_name)
                else:
                    ded_text = f'Bu ozel masal, sevgili {child_name} icin hazirlandi.\n\nUnutma, her macera seni bekliyor!'

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

            # --- Compose scenario intro page (karsılama 2) ---
            try:
                _intro_text: str | None = None

                if scenario_id:
                    from app.models.scenario import Scenario as _Scenario
                    from app.services.scenario_content_service import (
                        generate_scenario_intro_text as _gen_intro,
                    )

                    _sc_result = await db.execute(
                        select(_Scenario).where(_Scenario.id == uuid.UUID(scenario_id))
                    )
                    _sc = _sc_result.scalar_one_or_none()
                    if _sc:
                        # Edebi, kitap tanıtan metin; [Çocuk adı] gibi placeholder kullanılmaz (story_title zaten çözülmüş başlık)
                        _intro_text = await _gen_intro(
                            scenario=_sc,
                            child_name=child_name,
                            story_title=story_title or "",
                        )
                    if not _intro_text and _sc:
                        _sc_name = getattr(_sc, "name", None) or getattr(_sc, "location_en", None)
                        if _sc_name:
                            _intro_text = (
                                f"{_sc_name} macerasına hoş geldin, {child_name}!\n\n"
                                f"Bu kitapta seni çok özel bir yolculuk bekliyor. Hazır mısın?"
                            )

                # Garantili intro metni: AppSetting veya genel fallback (placeholder yok)
                if not _intro_text:
                    try:
                        from app.models.app_setting import AppSetting as _AppSetting
                        _setting_row = (await db.execute(
                            select(_AppSetting).where(_AppSetting.key == "default_intro_text")
                        )).scalar_one_or_none()
                        _tpl_text = _setting_row.value if _setting_row and _setting_row.value else None
                    except Exception:
                        _tpl_text = None
                    if _tpl_text:
                        _intro_text = (
                            _tpl_text
                            .replace("{child_name}", child_name)
                            .replace("{story_title}", story_title or "Masalım")
                        )
                    else:
                        _intro_text = (
                            f"{story_title or 'Bu macera'} yolculuğuna hoş geldin, {child_name}!\n\n"
                            f"Bu kitapta neler göreceğini, neler keşfedeceğini merak ediyor musun? "
                            f"Sayfaları çevir, seni bekleyen hikâyeye dal!"
                        )

                # Son güvenlik: placeholder/senaryo description sızıntısı varsa güvenli metne geç
                _intro_lower = (_intro_text or "").lower()
                if "[çocuk adı]" in _intro_lower or "[cocuk adi]" in _intro_lower or "kitap adı:" in _intro_lower or "kitap adi:" in _intro_lower:
                    _intro_text = (
                        f"{story_title or 'Bu macera'} yolculuğuna hoş geldin, {child_name}!\n\n"
                        f"Bu kitapta neler göreceğini, neler keşfedeceğini merak ediyor musun? "
                        f"Sayfaları çevir, seni bekleyen hikâyeye dal!"
                    )
                    logger.warning("Intro text contained placeholder leak — replaced with safe fallback", trial_id=trial_id)

                from sqlalchemy import desc as _desc2_
                _intro_tpl_result = await db.execute(
                    select(PageTemplate)
                    .where(PageTemplate.page_type == 'dedication', PageTemplate.is_active == True)
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
                    images={'intro': _intro_b64},
                    story_id=f'preview-{story_id}',
                )
                if 'intro' in _intro_uploaded:
                    composed_urls['intro'] = _intro_uploaded['intro']
                    logger.info('Scenario intro page (karsılama 2) composed', trial_id=trial_id)
            except Exception as _intro_err:
                logger.warning('Failed to compose scenario intro preview: %s', _intro_err)

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
            # Mark trial as failed so the frontend polling loop can stop
            try:
                async with async_session_factory() as _fail_db:
                    from sqlalchemy import select as _sel_fail
                    _fail_trial = (
                        await _fail_db.execute(
                            _sel_fail(StoryPreview).where(StoryPreview.id == uuid.UUID(trial_id))
                        )
                    ).scalar_one_or_none()
                    if _fail_trial and _fail_trial.status == PreviewStatus.GENERATING.value:
                        _fail_trial.generation_progress = {
                            "stage": "failed",
                            "message": "Resimler olu\u015fturulamad\u0131. L\u00fctfen tekrar deneyin.",
                            "error": str(e)[:200],
                        }
                        await _fail_db.commit()
            except Exception as _mark_err:
                logger.warning("Failed to mark trial as failed", trial_id=trial_id, error=str(_mark_err))


# ---------------------------------------------------------------------------
# Phase 2: Remaining image generation (after payment)
# ---------------------------------------------------------------------------


async def generate_remaining_images_inner(
    trial_id: str,
    prompts: list[dict],
    product_name: str | None = None,
    visual_style_modifier: str = "",
    child_photo_url: str = "",
    clothing_description: str = "",
) -> None:
    """Actual remaining images logic, runs inside trial semaphore.

    TWO-PHASE: First generate visual prompts for remaining pages, then generate images.
    """
    from app.core.database import async_session_factory
    from app.services.ai.image_provider_dispatch import (
        get_effective_ai_config,
        get_image_provider_for_generation,
    )
    from app.services.trial_service import get_trial_service
    from app.utils.resolution_calc import DEFAULT_GENERATION_A4_LANDSCAPE
    width, height = DEFAULT_GENERATION_A4_LANDSCAPE

    from app.services.ai.face_service import resolve_face_reference
    from app.services.storage_service import storage_service as _ss_rem
    _face_ref_url, _original_photo_url, _face_embedding = await resolve_face_reference(child_photo_url, _ss_rem)

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
            "REMAINING_PAGES_NO_CHILD_PHOTO   images will lack face consistency",
            trial_id=trial_id,
        )

    async with async_session_factory() as db:
        try:
            trial_service = get_trial_service(db)

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

            _trial_result_rem = await db.execute(
                select(StoryPreview).where(StoryPreview.id == uuid.UUID(trial_id))
            )
            _trial_obj_rem = _trial_result_rem.scalar_one_or_none()
            _rem_child_name = getattr(_trial_obj_rem, "child_name", "") or ""
            _rem_child_age = getattr(_trial_obj_rem, "child_age", 7) or 7
            _rem_child_gender = getattr(_trial_obj_rem, "child_gender", "") or ""

            # %% TWO-PHASE STEP 1: Generate visual prompts for remaining pages %%
            logger.info(
                "PHASE 1: Generating visual prompts for remaining pages",
                trial_id=trial_id,
                pages_without_prompts=len(prompts_to_generate),
            )

            _pages_need_prompts = [
                p for p in prompts_to_generate
                if not p.get("visual_prompt") or not p.get("image_prompt_en")
            ]

            if _pages_need_prompts and _trial_obj_rem:
                try:
                    from app.prompt_engine import build_character_bible
                    from app.prompt_engine.scenario_bible import normalize_location_key_for_anchors
                    from app.services.ai.gemini_service import gemini_service

                    _cache = _trial_obj_rem.generated_prompts_cache or {}
                    _blueprint = _cache.get("blueprint_json", {})

                    _child_outfit_block = _blueprint.get("child_outfit") or {}
                    _blueprint_outfit = _child_outfit_block.get("description_en", "").strip()
                    _blueprint_hair = _child_outfit_block.get("hair_style_en", "").strip()
                    _effective_outfit = (clothing_description or "").strip() or _blueprint_outfit

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

                    # Extract companion from blueprint
                    _rem_side_char = _blueprint.get("side_character") or {} if _blueprint else {}
                    _rem_comp_name = _rem_side_char.get("name", "")
                    _rem_comp_species = _rem_side_char.get("type", "")
                    _rem_comp_appearance = _rem_side_char.get("appearance", "")

                    character_bible = build_character_bible(
                        child_name=_rem_child_name,
                        child_age=_rem_child_age,
                        child_gender=_rem_child_gender or "erkek",
                        child_description="",
                        fixed_outfit=_effective_outfit,
                        hair_style=_blueprint_hair,
                        companion_name=_rem_comp_name,
                        companion_species=_rem_comp_species,
                        companion_appearance=_rem_comp_appearance,
                    )

                    _remaining_enhanced = await gemini_service.enhance_pages_with_visual_prompts(
                        story_pages=_pages_need_prompts,
                        blueprint=_blueprint,
                        character_bible=character_bible,
                        visual_style=visual_style_modifier or "children's book illustration",
                        location_key=_location_key,
                        likeness_hint="",
                        has_pulid=bool(child_photo_url),
                        leading_prefix_override=None,
                        style_block_override=None,
                    )

                    _enhanced_map = {
                        p.get("page_number", p.get("page", 0)): p
                        for p in _remaining_enhanced
                    }

                    for prompt in prompts_to_generate:
                        page_num = prompt.get("page_number", prompt.get("page", 0))
                        if page_num in _enhanced_map:
                            enhanced = _enhanced_map[page_num]
                            enhanced_prompt = enhanced.get("image_prompt_en", "")
                            prompt["visual_prompt"] = enhanced_prompt
                            prompt["image_prompt_en"] = enhanced_prompt
                            prompt["negative_prompt"] = enhanced.get("negative_prompt", "")
                            prompt["v3_composed"] = True

                    logger.info(
                        "PHASE 1 COMPLETE: Visual prompts generated for remaining pages",
                        trial_id=trial_id,
                        enhanced_count=len(_remaining_enhanced),
                    )

                    if _trial_obj_rem.generated_prompts_cache:
                        _all_prompts = _trial_obj_rem.generated_prompts_cache.get("prompts", [])
                        for enhanced in _remaining_enhanced:
                            page_num = enhanced.get("page_number", enhanced.get("page", 0))
                            enhanced_prompt = enhanced.get("image_prompt_en", "")
                            for i, cached_p in enumerate(_all_prompts):
                                if cached_p.get("page_number") == page_num:
                                    _all_prompts[i]["visual_prompt"] = enhanced_prompt
                                    _all_prompts[i]["image_prompt_en"] = enhanced_prompt
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

            # %% TWO-PHASE STEP 2: Generate images using prompts %%
            logger.info(
                "PHASE 2: Generating images for remaining pages",
                trial_id=trial_id,
                prompts_count=len(prompts_to_generate),
            )

            if _face_ref_url and not _rem_char_desc_for_images:
                try:
                    from app.services.ai.face_analyzer_service import (
                        get_face_analyzer as _get_fa_rem,
                    )
                    _fa_rem = _get_fa_rem()
                    # Use "AI Director" mode for concise description (30-50 words) to avoid prompt dilution
                    _rem_char_desc_for_images = await _fa_rem.analyze_for_ai_director(
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
                        "Remaining pages: face analysis failed   no CHARACTER ANCHOR",
                        trial_id=trial_id,
                        error=str(_fa_rem_err),
                    )

            # %% CACHE-FIRST: Read style params cached by preview generation %%
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

                _rem_product_uuid = None
                if _cached_product_id:
                    try:
                        _rem_product_uuid = uuid.UUID(_cached_product_id)
                    except (ValueError, TypeError):
                        pass

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
                    "REMAINING_STYLE_FROM_CACHE   using exact preview params",
                    trial_id=trial_id,
                    provider=provider_name_rem,
                    style_modifier_len=len(visual_style),
                    has_leading_prefix=bool(_rem_leading_prefix_override),
                    has_style_block=bool(_rem_style_block_override),
                    has_id_weight=_rem_id_weight is not None,
                )
            else:
                logger.warning(
                    "REMAINING_STYLE_NO_CACHE   falling back to DB resolution",
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
                _vs_rem = await resolve_visual_style_from_db(db, _rem_vs_name)
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

            # %% Compose remaining images: text overlay + template frame %%
            if generated_images:
                import base64 as _b64_rem

                import httpx as _httpx_rem

                from app.models.book_template import PageTemplate as _PT_rem
                from app.services.page_composer import build_template_config as _build_tpl_cfg
                from app.services.page_composer import page_composer as _pc_rem
                from app.services.storage_service import storage_service as _ss_rem

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

                _COMPOSE_DPI = 300  # Print-quality DPI (was 150 → low-res PDFs)
                _story_id_short = trial_id[:8]
                _text_map = {p["page_number"]: p.get("text", "") for p in prompts}
                _story_title_rem = getattr(_trial_obj_rem, "story_title", "") or ""

                composed_count = 0
                compose_fail_count = 0
                composed_images: dict[int, str] = {}

                for _pg_num, _raw_url in generated_images.items():
                    try:
                        _is_cov = (_pg_num == 0)

                        # COVER: Gemini renders title natively — skip PIL compose to avoid
                        # double-rendering or wrong text on cover.
                        if _is_cov:
                            composed_images[_pg_num] = _raw_url
                            logger.info(
                                "REMAINING_COVER_COMPOSE_SKIPPED: using raw Gemini image",
                                page_num=_pg_num,
                            )
                            continue

                        _tmpl = _inner_tmpl
                        if not _tmpl:
                            composed_images[_pg_num] = _raw_url
                            continue

                        async with _httpx_rem.AsyncClient(timeout=30) as _hc:
                            _resp = await _hc.get(_raw_url)
                            _resp.raise_for_status()
                            _img_b64 = _b64_rem.b64encode(_resp.content).decode()

                        _pg_text = _text_map.get(_pg_num, "")
                        if False:  # was: if _is_cov — cover handled above
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

                if composed_images:
                    generated_images.update(composed_images)

                logger.info(
                    "REMAINING_PAGES_COMPOSED",
                    trial_id=trial_id,
                    composed=composed_count,
                    failed=compose_fail_count,
                    total=len(generated_images),
                )

            if generated_images:
                await trial_service.save_remaining_images(
                    uuid.UUID(trial_id),
                    generated_images,
                )

            _trial_for_status = await db.execute(
                select(StoryPreview).where(StoryPreview.id == uuid.UUID(trial_id))
            )
            _trial_obj_status = _trial_for_status.scalar_one_or_none()
            if _trial_obj_status:
                _trial_obj_status.status = "PENDING"
                await db.commit()
                logger.info("TRIAL_REMAINING_STATUS_PENDING", trial_id=trial_id)

            # %% Generate PDF and send email %%
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

                trial_result = await db.execute(
                    select(StoryPreview).where(StoryPreview.id == uuid.UUID(trial_id))
                )
                trial = trial_result.scalar_one_or_none()
                if not trial:
                    raise ValueError(f"Trial {trial_id} not found for PDF/email")

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

                all_images = {**(trial.preview_images or {}), **(trial.page_images or {})}

                composed_pages: list[dict] = []
                story_pages_db = trial.story_pages or []
                for page in story_pages_db:
                    page_num = page.get("page_number")
                    if page_num is None:
                        continue
                    if page.get("page_type") == "front_matter":
                        continue

                    compose_text = page.get("text", "")
                    if page_num == 0:
                        compose_text = trial.story_title or compose_text

                    image_url = all_images.get(str(page_num)) or generated_images.get(page_num)

                    composed_pages.append({
                        "page_number": page_num,
                        "text": compose_text,
                        "image_url": image_url,
                    })

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

                back_cover_config = None
                audio_url = getattr(trial, "audio_file_url", None)

                # QR kodu düzeltmesi: audio_file_url yoksa ama has_audio_book true ise
                # sesli kitabı oluşturup audio_url'yi set et
                if not audio_url and getattr(trial, "has_audio_book", False):
                    try:
                        from app.services.ai.elevenlabs_service import ElevenLabsService
                        from app.services.storage_service import StorageService as _StorageSvc

                        _tts_storage = _StorageSvc()
                        _tts_svc = ElevenLabsService()

                        _full_story_text = ""
                        for _sp in (trial.story_pages or []):
                            if isinstance(_sp, dict) and _sp.get("text"):
                                _full_story_text += _sp["text"] + "\n\n"

                        if _full_story_text.strip():
                            _audio_type = getattr(trial, "audio_type", "system")
                            _audio_voice_id = getattr(trial, "audio_voice_id", None)

                            if _audio_type == "cloned" and _audio_voice_id:
                                _audio_bytes = await _tts_svc.text_to_speech(
                                    text=_full_story_text,
                                    voice_id=_audio_voice_id,
                                )
                            else:
                                _audio_bytes = await _tts_svc.text_to_speech(
                                    text=_full_story_text,
                                    voice_type="female",
                                )

                            _audio_gcs_url = _tts_storage.upload_audio(
                                audio_bytes=_audio_bytes,
                                order_id=str(trial.id),
                                filename="audiobook.mp3",
                            )
                            trial.audio_file_url = _audio_gcs_url
                            await db.commit()
                            audio_url = _audio_gcs_url
                            logger.info(
                                "TRIAL_AUDIO_GENERATED_FOR_QR",
                                trial_id=trial_id,
                                audio_url=_audio_gcs_url[:80] if _audio_gcs_url else "",
                            )
                    except Exception as _tts_err:
                        logger.warning(
                            "TRIAL_AUDIO_GENERATION_FAILED (QR will be missing)",
                            trial_id=trial_id,
                            error=str(_tts_err),
                        )

                try:
                    bc_result = await db.execute(
                        select(BackCoverConfig)
                        .where(BackCoverConfig.is_active == True)
                        .where(BackCoverConfig.is_default == True)
                    )
                    back_cover_config = bc_result.scalar_one_or_none()
                except Exception:
                    pass

                # CRITICAL: Sort pages by page_number before PDF assembly.
                # story_pages from DB may not be ordered — if page 1 lands
                # after page 2 in the list, the PDF will read out-of-order.
                composed_pages.sort(key=lambda p: int(p.get("page_number", 9999)))

                cover_image_url: str | None = None
                story_pages_no_cover: list[dict] = []
                for p in composed_pages:
                    if p.get("page_number") == 0:
                        cover_image_url = p.get("image_url")
                    else:
                        story_pages_no_cover.append(p)

                # Also ensure final list is ordered (redundant but defensive)
                story_pages_no_cover.sort(key=lambda p: int(p.get("page_number", 9999)))


                _n_story = len(story_pages_no_cover)
                _has_ded = 1 if dedication_b64 else 0
                _has_back = 1 if back_cover_config else 0
                _back_cover_img_url = getattr(trial, "back_cover_image_url", None)
                _has_visual_back = 1 if _back_cover_img_url else 0
                _inner_tpl_cfg = build_template_config(inner_template) if inner_template else {}
                pdf_data = {
                    "story_title": trial.story_title,
                    "child_name": trial.child_name,
                    "story_pages": story_pages_no_cover,
                    "cover_image_url": cover_image_url,
                    "dedication_image_base64": dedication_b64,
                    "back_cover_config": back_cover_config,
                    "back_cover_image_url": _back_cover_img_url,
                    "audio_qr_url": audio_url,
                    "page_width_mm": page_width_mm,
                    "page_height_mm": page_height_mm,
                    "bleed_mm": bleed_mm,
                    "template_config": _inner_tpl_cfg,
                    "images_precomposed": True,
                    "expected_story_pages": _n_story,
                    "expected_total_pages": 1 + _has_ded + _n_story + _has_back + _has_visual_back,
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

                    trial.admin_notes = (trial.admin_notes or "") + f"\n\nPDF URL: {pdf_url}"
                    await db.commit()

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
                        # Calculate total price including add-ons
                        _total_price: float | None = None
                        if trial.product_price:
                            _total_price = float(trial.product_price)
                            if getattr(trial, "has_audio_book", False):
                                _audio_type = getattr(trial, "audio_type", "system") or "system"
                                _total_price += 300.0 if _audio_type == "cloned" else 150.0
                            if getattr(trial, "has_coloring_book", False):
                                try:
                                    from app.models.product import Product as _CBProd, ProductType as _CBType
                                    _cb_r = await db.execute(
                                        select(_CBProd).where(
                                            _CBProd.product_type == _CBType.COLORING_BOOK.value,
                                            _CBProd.is_active == True,
                                        ).limit(1)
                                    )
                                    _cb = _cb_r.scalar_one_or_none()
                                    if _cb:
                                        _total_price += float(_cb.discounted_price or _cb.base_price)
                                except Exception:
                                    pass

                        email_service.send_story_email_with_confirmation(
                            recipient_email=trial.parent_email,
                            recipient_name=trial.parent_name or trial.parent_email,
                            child_name=trial.child_name,
                            story_title=trial.story_title,
                            story_pages=pages_for_email,
                            confirmation_url=_confirmation_url,
                            product_price=_total_price,
                        )
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


# ---------------------------------------------------------------------------
# Coloring book order creation
# ---------------------------------------------------------------------------


async def create_coloring_book_order_from_trial(
    trial: StoryPreview,
    db: AsyncSession,
) -> "Order | None":
    """Create separate coloring book order from trial.

    Args:
        trial: Story preview/trial
        db: Database session

    Returns:
        Coloring book Order or None if failed
    """
    from app.models.product import Product as _CBProduct
    from app.models.product import ProductType as _CBProductType

    try:
        config_result = await db.execute(
            select(_CBProduct).where(
                _CBProduct.product_type == _CBProductType.COLORING_BOOK.value,
                _CBProduct.is_active == True,
            ).limit(1)
        )
        coloring_config = config_result.scalar_one_or_none()

        if not coloring_config:
            logger.error("No active coloring book product configuration")
            return None

        # NOTE: trial.product_id is already a UUID object from asyncpg   do NOT wrap with uuid.UUID()
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
        visual_style_obj = visual_style_result.scalar_one_or_none()

        if not visual_style_obj:
            logger.error("Visual style not found", visual_style_name=trial.visual_style_name)
            return None

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

        coloring_order = Order(
            user_id=trial.lead_user_id,
            product_id=product.id,
            scenario_id=scenario.id,
            visual_style_id=visual_style_obj.id,
            child_name=trial.child_name,
            child_age=trial.child_age,
            child_gender=trial.child_gender,
            status=OrderStatus.PAID,
            payment_amount=coloring_config.discounted_price or coloring_config.base_price,
            payment_provider="iyzico",
            payment_reference=trial.payment_reference,
            is_coloring_book=True,
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

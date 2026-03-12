"""Admin story generation service.

Extracted from api/v1/ai.py to keep the router thin.
Contains the full TWO-PASS story generation pipeline, the legacy fallback,
and the outfit-picking helpers used by the test/admin endpoints.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from app.schemas.ai import TestStructuredStoryRequest

# ---------------------------------------------------------------------------
# Pipeline constants (mirrors api/v1/ai.py)
# ---------------------------------------------------------------------------

_V3_BLOCK_MSG = "V2_LABEL_BLOCKED: expected v3"
_GENERATE_STORY_ROUTE = "/api/v1/ai/generate-story"

# ---------------------------------------------------------------------------
# Pre-defined fallback outfits per gender (English)
# ---------------------------------------------------------------------------

FALLBACK_OUTFITS_BOY = [
    "blue jacket, gray pants, white sneakers",
    "red hooded sweatshirt, dark blue jeans, black sneakers",
    "green windbreaker, khaki cargo pants, brown boots",
    "yellow raincoat, navy blue pants, red rain boots",
    "orange fleece jacket, black sweatpants, gray sneakers",
    "white t-shirt, blue shorts, colorful sneakers",
]

FALLBACK_OUTFITS_GIRL = [
    "pink jacket, navy blue leggings, white sneakers",
    "purple hooded sweatshirt, jeans, pink sneakers",
    "red windbreaker, black leggings, white boots",
    "turquoise raincoat, gray pants, yellow rain boots",
    "lilac fleece jacket, purple sweatpants, white sneakers",
    "white t-shirt, floral skirt, colorful sneakers",
]

FALLBACK_OUTFITS_NEUTRAL = [
    "green jacket, black pants, white sneakers",
    "orange hooded sweatshirt, gray pants, black sneakers",
    "blue windbreaker, dark pants, brown boots",
    "yellow raincoat, navy blue pants, red rain boots",
    "red fleece jacket, black sweatpants, gray sneakers",
    "white t-shirt, blue shorts, colorful sneakers",
]


# ---------------------------------------------------------------------------
# Outfit helper
# ---------------------------------------------------------------------------


async def auto_outfit_for_story(
    scenario_name: str,
    child_age: int,
    child_gender: str,
) -> str:
    """Pick ONE outfit for the child based on scenario, age, gender.

    Uses Gemini; falls back to a hard-coded default on any error.
    """
    import httpx

    from app.config import settings
    from app.prompt_engine import normalize_clothing_description

    gender_en = (
        "boy" if (child_gender or "").strip().lower() in ("erkek", "boy", "male") else "girl"
    )
    prompt = (
        f"You are a children's book illustrator. Pick ONE outfit for a {child_age}-year-old {gender_en} "
        f"in a '{scenario_name}' themed storybook.\n\n"
        f"RULES:\n- Return exactly ONE outfit as a short English string.\n"
        f"- Include: top, bottom, footwear (e.g. 'red jacket, blue pants, white sneakers').\n"
        f"- Match the story theme (Kapadokya = adventure/sturdy, space = playful, etc.).\n"
        f"- Child-appropriate ONLY.\n- Return ONLY the outfit string, no quotes, no JSON."
    )
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"
                f"?key={settings.gemini_api_key}",
                json={
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {"temperature": 0.8, "maxOutputTokens": 128},
                },
            )
            resp.raise_for_status()
            data = resp.json()
            candidates = data.get("candidates") or [{}]
            first_candidate = candidates[0] if candidates else {}
            content = first_candidate.get("content", {})
            parts = content.get("parts") or [{}]
            first_part = parts[0] if parts else {}
            text = (first_part.get("text") or "").strip()
            if text and len(text) < 120:
                return normalize_clothing_description(text)
    except Exception as e:
        import structlog

        structlog.get_logger().warning("auto_outfit_failed", error=str(e))
    if gender_en == "girl":
        return "a colorful adventure dress and comfortable sneakers"
    return "an adventure jacket with comfortable pants and sneakers"


# ---------------------------------------------------------------------------
# Legacy single-pass fallback
# ---------------------------------------------------------------------------


async def legacy_single_pass_generation(
    request: TestStructuredStoryRequest,
    db: AsyncSession,
    scenario,
    scenario_name: str,
    scenario_description: str,
    child_visual_desc: str,
    face_analysis_used: bool,
    face_analysis_error: str | None,
    clothing_desc: str = "",
) -> dict:
    """Legacy single-pass generation — fallback if TWO-PASS fails.

    Includes retry logic with exponential backoff for rate limit errors.
    Extracted from api/v1/ai.py (_legacy_single_pass_generation).
    """
    import asyncio
    import json

    import httpx
    import structlog

    from app.config import settings

    logger = structlog.get_logger()

    inner_pages = request.page_count
    gender_word = (
        "boy"
        if request.child_gender == "erkek"
        else "girl"
        if request.child_gender == "kiz"
        else "child"
    )

    _outfit_line = f"KIYAFETİ (SABIT, DEĞİŞMEZ): {clothing_desc}" if clothing_desc else ""
    system_prompt = f"""Sen bir ÇOCUK KİTABI YAZARISIN.
{inner_pages} sayfalık büyülü bir hikaye yaz.

ÇOCUK: {request.child_name}, {request.child_age} yaşında {gender_word}
SENARYO: {scenario_name}
GÖRSEL STİL: {request.visual_style}
{_outfit_line}

🚫🚫 KESİN KURAL: Hikayede anne, baba, kardeş, abla, abi, dede, nine, babaanne,
anneanne, aile, ebeveyn kelimeleri ASLA GEÇMEYECEK!
Çocuk macerayı TEK BAŞINA veya hayvan/hayali arkadaşlarla yaşayacak!
Bu kural İHLAL EDİLEMEZ!

Her sayfa için:
- text: Türkçe hikaye metni (2-4 cümle, duygusal, büyülü)
- visual_prompt: İngilizce sahne açıklaması (SADECE sahne ve aksiyonu yaz — kıyafet bilgisi YAZMA, sistem otomatik ekler)

JSON döndür."""

    user_prompt = f"Hikaye başlat: {scenario_description}"

    max_retries = 4
    base_wait = 8  # seconds

    for attempt in range(max_retries):
        try:
            async with httpx.AsyncClient(timeout=90.0) as client:
                response = await client.post(
                    f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={settings.gemini_api_key}",
                    json={
                        "contents": [{"parts": [{"text": system_prompt + "\n\n" + user_prompt}]}],
                        "generationConfig": {
                            "temperature": 0.9,
                            "maxOutputTokens": 12000,
                            "responseMimeType": "application/json",
                        },
                    },
                )
                response.raise_for_status()
                data = response.json()

                raw_text = data["candidates"][0]["content"]["parts"][0]["text"]

                try:
                    story_data = json.loads(raw_text)
                except json.JSONDecodeError as e:
                    return {
                        "success": False,
                        "error": "JSON parse error (legacy)",
                        "details": str(e),
                    }

                if isinstance(story_data, list):
                    pages_list = story_data
                    title = "Hikaye"
                else:
                    pages_list = story_data.get("pages", [])
                    title = story_data.get("title", "Hikaye")

                from app.prompt_engine import compose_visual_prompt as _compose
                from app.prompt_engine.constants import (
                    DEFAULT_COVER_TEMPLATE_EN,
                    DEFAULT_INNER_TEMPLATE_EN,
                )
                from app.services.prompt_template_service import get_prompt_service

                _tpl_svc = get_prompt_service()
                _cover_tpl = await _tpl_svc.get_template_en(
                    db, "COVER_TEMPLATE", DEFAULT_COVER_TEMPLATE_EN
                )
                _inner_tpl = await _tpl_svc.get_template_en(
                    db, "INNER_TEMPLATE", DEFAULT_INNER_TEMPLATE_EN
                )

                _style = (request.visual_style or "").strip()
                _clothing = clothing_desc or (getattr(request, "clothing_description", None) or "").strip()

                pages_with_prompts = []
                for idx, page in enumerate(pages_list):
                    if isinstance(page, dict):
                        _pn = page.get("page_number", idx)
                        _raw_vp = page.get("visual_prompt", "")
                    else:
                        _pn = idx
                        _raw_vp = ""

                    _is_cover = _pn == 0
                    _tpl_key = "COVER_TEMPLATE" if _is_cover else "INNER_TEMPLATE"
                    _tpl_en = _cover_tpl if _is_cover else _inner_tpl

                    if _raw_vp:
                        _composed, _neg = _compose(
                            _raw_vp,
                            is_cover=_is_cover,
                            template_en=_tpl_en,
                            clothing_description=_clothing,
                            style_prompt_en=_style,
                        )
                    else:
                        _composed, _neg = "", ""

                    _lower = _composed.lower()
                    pages_with_prompts.append(
                        {
                            "page_number": _pn,
                            "text": page.get("text", "") if isinstance(page, dict) else str(page),
                            "visual_prompt": _composed,
                            "negative_prompt": _neg,
                            "pipeline_version": "v2_fallback",
                            "composer_version": "v2_fallback",
                            "v3_composed": False,
                            "v2_debug": {
                                "template_key": _tpl_key,
                                "template_from_db": bool(_tpl_en),
                                "style_key": _style[:60] if _style else None,
                                "has_style_block": "\nSTYLE:\n" in _composed,
                                "has_negative": bool(_neg),
                                "has_safe_area": (
                                    "space for title at top" in _lower
                                    if _is_cover
                                    else "text space at bottom" in _lower
                                ),
                                "has_composition": "child not looking at camera" in _lower,
                                "is_cover": _is_cover,
                                "legacy_fallback": True,
                            },
                        }
                    )

                return {
                    "success": True,
                    "pipeline_version": "v2_fallback",
                    "pipeline_label": "v2_fallback",
                    "generation_method": "LEGACY FALLBACK (V2 composed)",
                    "model": "gemini-2.5-flash",
                    "face_analysis_used": face_analysis_used,
                    "story": {
                        "title": title,
                        "pages": pages_with_prompts,
                    },
                    "page_count": len(pages_with_prompts),
                    "used_page_count": request.page_count,
                }

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                wait_time = base_wait * (2**attempt)
                retry_after = e.response.headers.get("Retry-After")
                if retry_after:
                    try:
                        wait_time = max(wait_time, int(retry_after))
                    except ValueError:
                        pass

                logger.warning(
                    "Rate limit hit in legacy fallback - retrying",
                    attempt=attempt + 1,
                    max_retries=max_retries,
                    wait_seconds=wait_time,
                )

                if attempt < max_retries - 1:
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    return {
                        "success": False,
                        "error": "AI servisi şu an yoğun. Lütfen 1-2 dakika bekleyip tekrar deneyin.",
                        "error_code": "RATE_LIMIT",
                        "retry_after": 60,
                    }
            else:
                return {
                    "success": False,
                    "error": f"API hatası: {e.response.status_code}",
                }

        except httpx.TimeoutException:
            logger.warning("Timeout in legacy fallback", attempt=attempt + 1)
            if attempt < max_retries - 1:
                await asyncio.sleep(5)
                continue
            return {
                "success": False,
                "error": "İstek zaman aşımına uğradı. Lütfen tekrar deneyin.",
                "error_code": "TIMEOUT",
            }

        except Exception as e:
            logger.exception("Unexpected error in legacy fallback", error=str(e))
            return {
                "success": False,
                "error": f"Beklenmeyen hata: {str(e)}",
            }

    return {
        "success": False,
        "error": "Hikaye oluşturulamadı. Lütfen tekrar deneyin.",
    }


# ---------------------------------------------------------------------------
# Main structured story pipeline
# ---------------------------------------------------------------------------


async def run_structured_story_generation(
    request: TestStructuredStoryRequest,
    db: AsyncSession,
) -> dict:
    """Execute the full TWO-PASS story generation pipeline.

    Extracted from the test_structured_story_generation endpoint handler.
    Falls back to legacy_single_pass_generation on non-rate-limit errors.
    """
    import uuid

    import structlog
    from fastapi import HTTPException
    from sqlalchemy import select

    from app.core.exceptions import AIServiceError, ContentPolicyError
    from app.models.scenario import Scenario
    from app.services.ai.face_analyzer_service import get_face_analyzer
    from app.services.ai.gemini_service import get_gemini_service

    logger = structlog.get_logger()
    logger.info("test-story-structured endpoint called", child_name=request.child_name)

    # Build child description — enhanced with face analysis if photo provided
    face_analysis_used = False
    face_analysis_error = None
    child_visual_desc = ""

    if request.child_photo_url:
        try:
            from app.core.pipeline_events import mask_photo_url
            logger.info(
                "Starting face analysis for DOUBLE LOCKING",
                child_photo_hash=mask_photo_url(request.child_photo_url),
            )
            face_analyzer = get_face_analyzer()
            child_visual_desc = await face_analyzer.analyze_for_ai_director(
                image_source=request.child_photo_url,
                child_name=request.child_name,
                child_age=request.child_age,
                child_gender=request.child_gender,
            )
            face_analysis_used = True
            logger.info("Face analysis complete", description=child_visual_desc[:100])
        except Exception as e:
            from app.core.pipeline_events import mask_photo_url
            logger.warning(
                "FACE_ANALYSIS_FAIL",
                error=str(e),
                child_photo_hash=mask_photo_url(request.child_photo_url),
            )
            face_analysis_error = str(e)

    # Fetch scenario from database
    scenario = None

    if request.scenario_id:
        try:
            from uuid import UUID
            result = await db.execute(
                select(Scenario).where(Scenario.id == UUID(request.scenario_id))
            )
            scenario = result.scalar_one_or_none()
        except Exception as e:
            logger.warning("Failed to fetch scenario by ID", error=str(e))

    if not scenario and request.scenario_name:
        name_stripped = (request.scenario_name or "").strip()
        if name_stripped:
            try:
                result = await db.execute(
                    select(Scenario).where(Scenario.name == name_stripped)
                )
                scenario = result.scalar_one_or_none()
                if scenario:
                    logger.info("Scenario matched by exact name", name=name_stripped)
            except Exception as e:
                logger.warning("Failed to fetch scenario by exact name", error=str(e))
            if not scenario:
                try:
                    result = await db.execute(
                        select(Scenario)
                        .where(Scenario.name.ilike(f"%{name_stripped}%"))
                        .order_by(Scenario.name)
                        .limit(1)
                    )
                    scenario = result.scalar_one_or_none()
                    if scenario:
                        logger.warning(
                            "Scenario matched by ilike (exact match preferred); possible cross-scenario leak",
                            requested=name_stripped,
                            matched=scenario.name,
                        )
                except Exception as e:
                    logger.warning("Failed to fetch scenario by ilike", error=str(e))

    # V2: Look up VisualStyle from DB by ID
    style_prompt_resolved = (request.visual_style or "").strip()
    style_negative_resolved = ""
    style_id_resolved: str | None = request.visual_style_id

    if request.visual_style_id:
        try:
            from uuid import UUID

            from app.models.visual_style import VisualStyle

            vs_result = await db.execute(
                select(VisualStyle).where(VisualStyle.id == UUID(request.visual_style_id))
            )
            vs_row = vs_result.scalar_one_or_none()
            if vs_row:
                style_prompt_resolved = (
                    vs_row.prompt_modifier or ""
                ).strip() or style_prompt_resolved
                style_negative_resolved = (vs_row.style_negative_en or "").strip()
                logger.info(
                    "[V2] VisualStyle loaded from DB",
                    visual_style_id=request.visual_style_id,
                    style_name=vs_row.name,
                    has_negative=bool(style_negative_resolved),
                )
            else:
                logger.warning(
                    "[V2] visual_style_id not found in DB, using text fallback",
                    visual_style_id=request.visual_style_id,
                )
        except Exception as e:
            logger.warning("[V2] Failed to fetch visual_style by ID", error=str(e))

    # V2: Resolve clothing_description — priority: request > scenario outfit > auto
    clothing_desc = (request.clothing_description or "").strip()
    if not clothing_desc and scenario:
        _gender = (request.child_gender or "erkek").lower()
        if _gender in ("kiz", "kız", "girl", "female"):
            clothing_desc = (getattr(scenario, "outfit_girl", None) or "").strip()
            if not clothing_desc:
                clothing_desc = (getattr(scenario, "outfit_boy", None) or "").strip()
        else:
            clothing_desc = (getattr(scenario, "outfit_boy", None) or "").strip()
            if not clothing_desc:
                clothing_desc = (getattr(scenario, "outfit_girl", None) or "").strip()
        if clothing_desc:
            logger.info(
                "clothing_from_scenario",
                scenario=scenario.name,
                gender=_gender,
                outfit=clothing_desc[:60],
            )
    if not clothing_desc:
        clothing_desc = await auto_outfit_for_story(
            scenario_name=scenario.name if scenario else request.scenario_name or "macera",
            child_age=request.child_age or 7,
            child_gender=request.child_gender or "erkek",
        )

    # V2: Personalize style block
    from app.prompt_engine import personalize_style_prompt

    style_prompt_resolved = personalize_style_prompt(
        style_prompt_resolved,
        child_name=request.child_name or "",
        child_age=request.child_age or 7,
        child_gender=request.child_gender or "",
    )

    scenario_name = scenario.name if scenario else request.scenario_name
    scenario_description = scenario.description if scenario else request.scenario_prompt

    # =========================================================================
    # TWO-PASS GENERATION via GeminiService
    # =========================================================================
    try:
        gemini_service = get_gemini_service()

        logger.info(
            "Starting TWO-PASS story generation",
            pass1_model=gemini_service.story_model,
            pass2_model=gemini_service.technical_model,
            scenario=scenario_name,
            child_name=request.child_name,
        )

        class MockScenario:
            def __init__(self, name, description):
                self.name = name
                self.description = description
                self.cover_prompt_template = None
                self.page_prompt_template = None
                self.ai_prompt_template = None
                self.location_constraints = None
                self.cultural_elements = None

            def get_cover_prompt(self, **kwargs) -> str | None:
                return None

            def get_page_prompt(self, **kwargs) -> str | None:
                return None

            def get_story_prompt(self, **kwargs) -> str | None:
                return None

        scenario_obj = scenario if scenario else MockScenario(scenario_name, scenario_description)

        location_constraints = getattr(scenario_obj, "location_constraints", None)

        logger.info(
            "[STORY-GEN] SINGLE SOURCE OF TRUTH - Story Generation Start",
            scenario_id=request.scenario_id,
            scenario_name=scenario_name,
            scenario_from_db=bool(scenario),
            has_location_constraints=bool(location_constraints),
            location_constraints_preview=location_constraints[:100]
            if location_constraints
            else "none",
            visual_style_input=style_prompt_resolved[:80] if style_prompt_resolved else "default",
            visual_style_id=request.visual_style_id,
            clothing_description=clothing_desc[:50] if clothing_desc else "none",
            page_count=request.page_count,
        )

        logger.info(f"Calling TWO-PASS generation with page_count={request.page_count}")

        story_response, final_pages, _outfit, _blueprint = await gemini_service.generate_story_structured(
            scenario=scenario_obj,
            child_name=request.child_name,
            child_age=request.child_age,
            child_gender=request.child_gender,
            visual_style=style_prompt_resolved,
            visual_character_description=child_visual_desc,
            page_count=request.page_count,
            fixed_outfit=clothing_desc,
            requested_version="v3",
        )

        # Title safety net
        from app.services.ai.gemini_service import (
            _get_possessive_suffix,
            _normalize_title_turkish,
        )

        _GENERIC_TITLES = {
            "hikaye", "masal", "hikâye", "öykü", "macera", "story",
            "bir hikaye", "bir masal", "yeni hikaye", "güzel hikaye",
        }
        _title = (story_response.title or "").strip()
        if _title.lower() in _GENERIC_TITLES or len(_title) < 4:
            _sn = scenario_name or "Büyülü Macera"
            _sfx = _get_possessive_suffix(request.child_name or "")
            story_response.title = f"{request.child_name}'{_sfx} {_sn}"
            logger.warning("Generic title replaced", original=_title, new=story_response.title)

        story_response.title = _normalize_title_turkish(story_response.title)

        # V3 pipeline guard
        from app.core.build_meta import get_commit_hash
        from app.core.pipeline_version import (
            prompt_builder_name_for_version,
            require_v3_pipeline,
        )

        _job_id = str(uuid.uuid4())
        _non_v3_pages = [
            p
            for p in final_pages
            if getattr(p, "pipeline_version", "") != "v3"
            or getattr(p, "composer_version", "") != "v3"
            or not getattr(p, "v3_composed", False)
        ]
        if _non_v3_pages:
            logger.error(
                _V3_BLOCK_MSG,
                route="/api/v1/ai/test-story-structured",
                job_id=_job_id,
                non_v3_pages=len(_non_v3_pages),
            )
            raise HTTPException(status_code=400, detail=_V3_BLOCK_MSG)

        _pipeline_version = "v3"
        try:
            require_v3_pipeline(
                pipeline_version=_pipeline_version,
                job_id=_job_id,
                route=_GENERATE_STORY_ROUTE,
            )
        except ValueError as _v3_err:
            logger.error(
                _V3_BLOCK_MSG,
                route=_GENERATE_STORY_ROUTE,
                job_id=_job_id,
                error=str(_v3_err),
            )
            raise HTTPException(status_code=400, detail=_V3_BLOCK_MSG) from _v3_err

        logger.info(
            "PIPELINE_AUDIT",
            job_id=_job_id,
            route=_GENERATE_STORY_ROUTE,
            pipeline_version=_pipeline_version,
            template_id=str(getattr(scenario_obj, "id", "") or ""),
            prompt_builder_name=prompt_builder_name_for_version(_pipeline_version),
            commit_hash=get_commit_hash(),
        )

        _any_enhancement_skipped = any(
            getattr(p, "v3_enhancement_skipped", False) for p in final_pages
        )
        if _any_enhancement_skipped:
            logger.warning(
                "V3 enhancement was skipped — raw prompts used (graceful degradation)",
                skipped_pages=sum(1 for p in final_pages if getattr(p, "v3_enhancement_skipped", False)),
            )

        if _pipeline_version == "v3":
            pages_with_prompts = []
            for page in final_pages:
                pages_with_prompts.append(
                    {
                        "page_number": page.page_number,
                        "text": page.text,
                        "visual_prompt": page.visual_prompt,
                        "negative_prompt": page.negative_prompt or "",
                        "v3_composed": True,
                        "v3_enhancement_skipped": getattr(page, "v3_enhancement_skipped", False),
                        "page_type": getattr(page, "page_type", "inner"),
                        "page_index": getattr(page, "page_index", 0),
                        "story_page_number": getattr(page, "story_page_number", None),
                        "composer_version": getattr(page, "composer_version", "v3"),
                        "pipeline_version": getattr(page, "pipeline_version", "v3"),
                    }
                )
            logger.info(
                "V3 pages passed through (no V2 recomposition)",
                page_count=len(pages_with_prompts),
                enhancement_skipped=_any_enhancement_skipped,
            )
            for _i, page in enumerate(pages_with_prompts[:3]):
                logger.info(
                    f"[PROMPT-CHECK] V3 FINAL Page {page['page_number']}",
                    prompt_length=len(page["visual_prompt"]),
                    prompt_preview=page["visual_prompt"][:200] + "...",
                    has_style_block="\nSTYLE:\n" in page["visual_prompt"],
                    v3_composed=True,
                )

        return {
            "success": True,
            "pipeline_version": _pipeline_version,
            "pipeline_label": _pipeline_version,
            "v3_enhancement_skipped": _any_enhancement_skipped,
            "generation_method": "TWO-PASS (Pure Author + Technical Director)",
            "pass1_model": gemini_service.story_model,
            "pass2_model": gemini_service.technical_model,
            "face_analysis_used": face_analysis_used,
            "face_analysis_error": face_analysis_error,
            "story": {
                "title": story_response.title,
                "pages": pages_with_prompts,
            },
            "page_count": len(pages_with_prompts),
            "used_page_count": request.page_count,
            "metadata": {
                "scenario_name": scenario_name,
                "visual_style": style_prompt_resolved[:50] if style_prompt_resolved else "default",
                "visual_style_id": style_id_resolved,
                "clothing_description": clothing_desc or None,
                "child_visual_description": child_visual_desc[:100]
                if child_visual_desc
                else "basic",
                "cover_template_source": "v3_composed" if _pipeline_version == "v3" else "default",
                "inner_template_source": "v3_composed" if _pipeline_version == "v3" else "default",
            },
        }

    except ContentPolicyError:
        # Aile kelimesi ihlali — legacy fallback'e düşme, doğrudan hata dön
        raise

    except AIServiceError as ai_exc:
        from app.core.pipeline_events import PipelineErrorCode, build_error_response

        _err_str = str(ai_exc)
        _is_rate_limit = "429" in _err_str or "rate limit" in _err_str.lower()
        _error_code = PipelineErrorCode.RATE_LIMIT if _is_rate_limit else "AI_GENERATION_FAIL"

        logger.error(
            "PIPELINE_FAIL",
            error_code=_error_code,
            reason_code=ai_exc.reason_code,
            trace_id=ai_exc.trace_id,
            request_id=structlog.contextvars.get_contextvars().get("request_id", ""),
            user_id="",
            product_id="",
            requested_page_count=request.page_count,
            used_page_count=0,
            pipeline_version="v3",
            error=_err_str[:300],
        )

        return build_error_response(
            error_code=_error_code,
            trace_id=ai_exc.trace_id,
            retry_after=60 if _is_rate_limit else None,
        )

    except Exception as e:
        import uuid as _uuid_err

        from app.core.pipeline_events import PipelineErrorCode, build_error_response

        error_str = str(e)
        _trace = _uuid_err.uuid4().hex[:12]
        _is_rate_limit = "429" in error_str or "rate limit" in error_str.lower()
        _error_code = PipelineErrorCode.RATE_LIMIT if _is_rate_limit else "PIPELINE_UNHANDLED"

        logger.exception(
            "PIPELINE_FAIL",
            error_code=_error_code,
            trace_id=_trace,
            request_id=structlog.contextvars.get_contextvars().get("request_id", ""),
            user_id="",
            product_id="",
            requested_page_count=request.page_count,
            used_page_count=0,
            pipeline_version="v3",
            error=error_str[:300],
        )

        if _is_rate_limit:
            return build_error_response(
                error_code=PipelineErrorCode.RATE_LIMIT,
                trace_id=_trace,
                retry_after=60,
            )

        logger.warning(
            "LEGACY_FALLBACK_USED",
            trace_id=_trace,
            error_code=PipelineErrorCode.LEGACY_FALLBACK_USED,
            reason=error_str[:200],
        )
        return await legacy_single_pass_generation(
            request,
            db,
            scenario,
            scenario_name,
            scenario_description,
            child_visual_desc,
            face_analysis_used,
            face_analysis_error,
            clothing_desc=clothing_desc,
        )

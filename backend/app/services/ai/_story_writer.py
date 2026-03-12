"""Story writer mixin for GeminiService — orchestration layer.

Responsibilities (this file):
- V3 pipeline orchestration: generate_story_v3, generate_story_structured
- PASS-1 page generation: _pass1_generate_pages
- Legacy wrappers: generate_story, generate_story_with_prompts, parse_story_pages
- JSON helpers: _extract_and_repair_json, _dedupe_style

Sub-mixins (inherited automatically):
- _story_blueprint._BlueprintMixin                 — PASS-0 blueprint
- _story_legacy_passes._LegacyPassesMixin          — legacy PASS-1/PASS-2
"""

from __future__ import annotations

import json
import time
from typing import TYPE_CHECKING

import httpx
import structlog

from app.config import settings
from app.core.exceptions import AIServiceError, ContentPolicyError
from app.core.rate_limit import rate_limit_retry
from app.models.scenario import Scenario
from app.services.ai._helpers import (
    AI_DIRECTOR_SYSTEM,
    _extract_text_from_parts,
    _get_possessive_suffix,
    _normalize_title_turkish,
    get_gemini_api_url,
    get_gemini_story_url,
)
from app.services.ai._models import (
    FinalPageContent,
    PageContent,
    StoryResponse,
)
from app.services.ai._story_blueprint import _BlueprintMixin
from app.services.ai._story_legacy_passes import _LegacyPassesMixin
from app.services.ai.llm_output_repair import (
    extract_and_repair_json as _enhanced_extract_json,
)
from app.services.ai.llm_output_repair import (
    repair_pages as _repair_pages,
)

if TYPE_CHECKING:
    pass

logger = structlog.get_logger()


class _StoryWriterMixin(_BlueprintMixin, _LegacyPassesMixin):
    """Story generation mixin for GeminiService.

    Orchestration only — PASS-0 blueprint in _story_blueprint,
    legacy PASS-1/PASS-2 in _story_legacy_passes."""

    def _extract_and_repair_json(self, raw_text: str) -> dict | list:
        """Extract and repair JSON from Gemini response.

        Uses the enhanced extractor from llm_output_repair, with the
        original implementation as fallback for backward-compat.
        """
        return _enhanced_extract_json(raw_text)

    @staticmethod
    def _dedupe_style(visual_style: str) -> str:
        """Remove duplicate style phrases (e.g. Pixar, DreamWorks) so style is applied once only."""
        if not visual_style or len(visual_style.strip()) < 3:
            return visual_style.strip() if visual_style else "children's book illustration"
        seen_lower: set[str] = set()
        # Split by comma and paren, normalize
        parts: list[str] = []
        for raw in visual_style.replace("(", ",").replace(")", ",").split(","):
            token = raw.strip()
            if not token:
                continue
            key = token.lower()
            if key in seen_lower:
                continue
            seen_lower.add(key)
            parts.append(token)
        return ", ".join(parts) if parts else visual_style.strip()




    async def _pass1_generate_pages(
        self,
        *,
        blueprint: dict,
        child_name: str,
        child_age: int,
        child_description: str,
        visual_style: str,
        location_display_name: str,
        magic_items: list[str],
        page_count: int,
        location_constraints: str = "",
        skip_visual_prompts: bool = False,
    ) -> list[dict]:
        """PASS-1: Generate story pages with text_tr + image_prompt_en + negative_prompt_en.

        Takes the blueprint from PASS-0 and produces the final page content.
        """
        import asyncio as _asyncio_pg

        from app.prompt_engine import (
            PAGE_GENERATION_SYSTEM_PROMPT,
            build_page_task_prompt,
        )
        from app.prompt_engine.style_adapter import get_style_instructions_for_prompt

        style_instructions = get_style_instructions_for_prompt(visual_style)

        system_prompt = await self._get_prompt(
            "PAGE_GENERATION_SYSTEM_PROMPT", PAGE_GENERATION_SYSTEM_PROMPT
        )

        task_prompt = build_page_task_prompt(
            blueprint_json=blueprint,
            child_name=child_name,
            child_age=child_age,
            child_description=child_description,
            visual_style=visual_style,
            style_instructions=style_instructions,
            location_display_name=location_display_name,
            location_constraints=location_constraints,
            magic_items=magic_items,
            page_count=page_count,
            skip_visual_prompts=skip_visual_prompts,
        )

        full_prompt = system_prompt + "\n\n" + task_prompt

        pages_url = get_gemini_story_url()
        max_retries = 3
        base_wait = 10

        for attempt in range(max_retries):
            try:
                logger.info(
                    "PASS-1: Generating story pages",
                    model=self.story_model,
                    page_count=page_count,
                    attempt=attempt + 1,
                )

                client = self._get_gemini_client()
                response = await client.post(
                    f"{pages_url}?key={self.api_key}",
                    json={
                        "contents": [{"parts": [{"text": full_prompt}]}],
                        "generationConfig": {
                            "temperature": self.story_temperature,
                            "topK": 64,
                            "topP": 0.95,
                            "maxOutputTokens": 32000,
                            "responseMimeType": "application/json",
                        },
                        "safetySettings": [
                            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                        ],
                    },
                )
                response.raise_for_status()

                data = response.json()
                parts = data["candidates"][0]["content"]["parts"]
                raw_text = _extract_text_from_parts(parts)

                # Parse — may be a JSON array or object with "pages" key
                parsed = self._extract_and_repair_json(raw_text)
                if isinstance(parsed, list):
                    pages = parsed
                elif isinstance(parsed, dict) and "pages" in parsed:
                    pages = parsed["pages"]
                elif isinstance(parsed, dict):
                    pages = [parsed]
                else:
                    pages = []

                # Count only inner pages (exclude page 0 which is a cover placeholder)
                _inner_pages = [
                    p for p in pages
                    if int(p.get("page", -1) if str(p.get("page", -1)).lstrip("-").isdigit() else -1) != 0
                ]
                if len(_inner_pages) < page_count and attempt < max_retries - 1:
                    logger.warning(
                        "PASS-1: Page count mismatch, retrying",
                        expected=page_count,
                        got_total=len(pages),
                        got_inner=len(_inner_pages),
                        attempt=attempt + 1,
                    )
                    await _asyncio_pg.sleep(base_wait * (attempt + 1))
                    continue

                # Full schema repair (pad missing, fill empty fields from blueprint)
                pages, pg_repairs = _repair_pages(pages, blueprint, page_count, skip_visual_prompts)
                if pg_repairs:
                    logger.info(
                        "PASS-1: Pages repaired",
                        repairs=pg_repairs,
                    )

                # Post-validation: check story quality
                _short_pages = [
                    p["page"] for p in pages
                    if len((p.get("text_tr") or "").strip()) < 30
                ]
                if _short_pages:
                    logger.warning(
                        "PASS-1: Short text pages detected",
                        short_pages=_short_pages,
                        total=len(pages),
                    )

                _last_text = (pages[-1].get("text_tr") or "").strip() if pages else ""
                _has_closure = any(
                    kw in _last_text.lower()
                    for kw in ["gülümsedi", "mutlu", "döndü", "veda", "ayrıl",
                               "hatırla", "öğren", "gurur", "teşekkür", "sarıl",
                               "eve", "geri", "sonunda", "artık"]
                ) if _last_text else False

                logger.info(
                    "PASS-1: Story pages generated",
                    pages=len(pages),
                    repairs_count=len(pg_repairs),
                    short_page_count=len(_short_pages),
                    has_closure_keywords=_has_closure,
                )
                return pages

            except httpx.HTTPStatusError as exc:
                if exc.response.status_code == 429 and attempt < max_retries - 1:
                    wait = base_wait * (attempt + 1)
                    logger.warning("PASS-1: Rate limited, waiting", wait=wait)
                    await _asyncio_pg.sleep(wait)
                    continue
                raise AIServiceError(
                    "Gemini",
                    f"Sayfa üretimi başarısız (HTTP {exc.response.status_code})",
                    reason_code="PAGE_HTTP_FAIL",
                ) from exc
            except (KeyError, IndexError, json.JSONDecodeError) as exc:
                if attempt < max_retries - 1:
                    await _asyncio_pg.sleep(base_wait)
                    continue
                raise AIServiceError(
                    "Gemini",
                    f"Sayfa JSON ayrıştırma hatası: {type(exc).__name__}",
                    reason_code="PAGE_PARSE_FAIL",
                ) from exc

        raise AIServiceError(
            "Gemini",
            "Sayfa üretimi tüm denemelerde başarısız.",
            reason_code="PAGE_ALL_RETRIES_EXHAUSTED",
        )

    @rate_limit_retry(service="gemini", max_attempts=2, timeout_attempts=1)
    async def generate_story_v3(
        self,
        scenario: Scenario,
        child_name: str,
        child_age: int,
        child_gender: str | None,
        visual_style: str = "children's book illustration, soft colors",
        visual_character_description: str = "",
        page_count: int = 16,
        fixed_outfit: str = "",
        magic_items: list[str] | None = None,
        leading_prefix_override: str | None = None,
        style_block_override: str | None = None,
        generate_visual_prompts: bool = True,
    ) -> tuple[StoryResponse, list[FinalPageContent], str, dict]:
        """Generate a personalized story using V3 BLUEPRINT PIPELINE.

        V3 APPROACH:
        ============
        PASS-0 - "Blueprint Architect":
          - Generates structured plan (page roles, cultural hooks, magic items)
          - Output: Blueprint JSON

        PASS-1 - "Story Writer + Art Director":
          - Follows blueprint, generates text_tr + image_prompt_en + negative_prompt_en
          - Output: Pages JSON

        Validation:
          - Magic item count, cultural fact uniqueness, safety, family ban

        Returns:
            Tuple of (StoryResponse, list[FinalPageContent], fixed_outfit, blueprint_json)
        """
        import asyncio as _asyncio_v3

        from app.core.pipeline_events import PipelineTracer, mask_photo_url

        tracer = PipelineTracer.for_order(
            pipeline_version="v3",
            requested_page_count=page_count,
        )
        tracer.pipeline_start(
            scenario_id=str(getattr(scenario, "id", "") or ""),
            style_id="",
            child_photo_hash=mask_photo_url(visual_character_description[:8] if visual_character_description else None),
        )

        logger.info(
            "Starting V3 BLUEPRINT story generation",
            trace_id=tracer.trace_id,
            scenario=scenario.name,
            child_name=child_name,
            page_count=page_count,
            magic_items=magic_items,
        )

        # Resolve location info — SINGLE SOURCE: scenario only; normalize for anchors
        from app.prompt_engine.scenario_bible import normalize_location_key_for_anchors
        _raw_loc = getattr(scenario, "theme_key", None) or getattr(scenario, "location_en", "") or scenario.name
        location_key = normalize_location_key_for_anchors(str(_raw_loc or ""))
        location_display_name = getattr(scenario, "location_en", None) or scenario.name
        logger.info(
            "V3_LOCATION_RESOLVED",
            trace_id=tracer.trace_id,
            scenario_id=str(getattr(scenario, "id", "")),
            scenario_name=getattr(scenario, "name", ""),
            location_key=location_key,
            location_display_name=location_display_name,
        )
        child_description = visual_character_description or ""

        # =================================================================
        # FACE ANALYSIS: convert photo URL → text description
        # =================================================================
        # trials.py passes child_photo_url as visual_character_description.
        # The URL is needed for PuLID (image reference), but CharacterBible
        # and blueprint need a *text* description to parse hair/skin/eye
        # tokens.  Run face analyzer once and reuse the result.
        _child_photo_url: str = ""
        if child_description and child_description.strip().startswith(("http://", "https://")):
            _child_photo_url = child_description.strip()
            try:
                from app.services.ai.face_analyzer_service import get_face_analyzer
                _face_analyzer = get_face_analyzer()
                child_description = await _face_analyzer.analyze_for_ai_director(
                    image_source=_child_photo_url,
                    child_name=child_name,
                    child_age=child_age,
                    child_gender=(child_gender or "erkek"),
                )
                logger.info(
                    "FACE_ANALYSIS_COMPLETE",
                    trace_id=tracer.trace_id,
                    description_preview=child_description[:120],
                )
            except Exception as _fa_err:
                logger.warning(
                    "Face analysis failed — pipeline continues without appearance tokens",
                    trace_id=tracer.trace_id,
                    error=str(_fa_err),
                )
                child_description = ""

        # =====================================================================
        # PASS-0: BLUEPRINT
        # =====================================================================
        _p0_start = time.monotonic()
        try:
            blueprint = await self._pass0_generate_blueprint(
                child_name=child_name,
                child_age=child_age,
                child_description=child_description,
                location_key=location_key,
                location_display_name=location_display_name,
                visual_style=visual_style,
                magic_items=magic_items or [],
                page_count=page_count,
                scenario=scenario,
            )
            tracer.story_pass0_ok(
                page_count=len(blueprint.get("pages", [])),
                latency_ms=(time.monotonic() - _p0_start) * 1000,
            )
        except Exception as _p0_err:
            tracer.story_pass0_fail(error=str(_p0_err))
            tracer.pipeline_fail(
                error_code="PASS0_GEMINI_ERROR",
                error=str(_p0_err),
            )
            raise

        # Minimal buffer — token bucket handles rate limiting
        await _asyncio_v3.sleep(1)

        # =====================================================================
        # PASS-1: STORY PAGES
        # =====================================================================
        _p1_start = time.monotonic()
        try:
            pages = await self._pass1_generate_pages(
                blueprint=blueprint,
                child_name=child_name,
                child_age=child_age,
                child_description=child_description,
                visual_style=visual_style,
                location_display_name=location_display_name,
                magic_items=magic_items or [],
                page_count=page_count,
                location_constraints=getattr(scenario, "location_constraints", "") or "",
                skip_visual_prompts=not generate_visual_prompts,
            )
            tracer.story_pass1_ok(
                page_count=len(pages),
                latency_ms=(time.monotonic() - _p1_start) * 1000,
            )
        except Exception as _p1_err:
            tracer.story_pass1_fail(error=str(_p1_err))
            tracer.pipeline_fail(
                error_code="PASS1_GEMINI_ERROR",
                error=str(_p1_err),
            )
            raise

        # =====================================================================
        # VALIDATION → FIX → RE-VALIDATE (text + basic structure)
        # =====================================================================
        from app.prompt_engine.story_validators import (
            apply_all_fixes,
            validate_story_output,
        )

        report = validate_story_output(
            pages=pages,
            blueprint=blueprint,
            magic_items=magic_items or [],
            expected_page_count=page_count,
        )

        if not report.all_passed:
            pages, fix_summary = apply_all_fixes(pages)

            if fix_summary:
                logger.info(
                    "V3 auto-fixer applied corrections",
                    fixes=fix_summary,
                )
                report = validate_story_output(
                    pages=pages,
                    blueprint=blueprint,
                    magic_items=magic_items or [],
                    expected_page_count=page_count,
                )

            if not report.all_passed:
                logger.warning(
                    "V3 story validation still has failures after auto-fix",
                    failures=[f.code for f in report.failures],
                )

        # =====================================================================
        # VISUAL PROMPT ENHANCEMENT (CharacterBible + SceneDirector + Safety)
        # =====================================================================
        from app.prompt_engine.character_bible import build_character_bible
        from app.prompt_engine.style_adapter import adapt_style
        from app.prompt_engine.visual_prompt_builder import enhance_all_pages
        from app.prompt_engine.visual_prompt_validator import autofix as autofix_visual_prompts
        from app.prompt_engine.visual_prompt_validator import (
            validate_all as validate_visual_prompts,
        )

        child_gender_str = child_gender or "erkek"

        # Extract companion (side_character) from blueprint for consistency
        _side_char = blueprint.get("side_character") or {}
        _companion_name = _side_char.get("name", "")
        _companion_type = _side_char.get("type", "")  # e.g. "sincap" / "squirrel"
        _companion_appearance = _side_char.get("appearance", "")

        # Extract child outfit + hair from blueprint (V3 outfit lock)
        _child_outfit_block = blueprint.get("child_outfit") or {}
        _blueprint_outfit = _child_outfit_block.get("description_en", "").strip()
        _blueprint_hair = _child_outfit_block.get("hair_style_en", "").strip()
        # Öncelik: senaryo kıyafeti (fixed_outfit) > blueprint kıyafeti > cinsiyet default'u
        # NOT: fixed_outfit boş string ("") olabilir — .strip() ile kontrol et
        _fixed_outfit_clean = (fixed_outfit or "").strip()
        _effective_outfit = _fixed_outfit_clean or _blueprint_outfit
        if not _effective_outfit:
            # Senaryo veya blueprint kıyafeti yoksa cinsiyet bazlı fallback
            if child_gender_str in ("girl", "kiz", "female"):
                _effective_outfit = "a colorful adventure dress and comfortable sneakers"
            else:
                _effective_outfit = "an adventure jacket with comfortable pants and sneakers"
        logger.info(
            "OUTFIT_LOCKED",
            source="scenario" if _fixed_outfit_clean else ("blueprint" if _blueprint_outfit else "default"),
            outfit=_effective_outfit[:80],
            fixed_outfit_raw=bool(_fixed_outfit_clean),
        )

        character_bible = build_character_bible(
            child_name=child_name,
            child_age=child_age,
            child_gender=child_gender_str,
            child_description=child_description,
            fixed_outfit=_effective_outfit,
            hair_style=_blueprint_hair,
            companion_name=_companion_name,
            companion_species=_companion_type,
            companion_appearance=_companion_appearance,
        )

        logger.info(
            "CHARACTER_BIBLE_BUILT",
            trace_id=tracer.trace_id,
            appearance_tokens=character_bible.appearance_tokens,
            identity_anchor=character_bible.identity_anchor,
            hair_style=character_bible.hair_style,
            negative_preview=character_bible.negative_tokens[:100],
        )

        if _companion_name:
            _final_appearance = ""
            if character_bible.companion:
                _final_appearance = character_bible.companion.appearance
            logger.info(
                "Companion locked in CharacterBible",
                companion_name=_companion_name,
                companion_species=_companion_type,
                companion_appearance=_final_appearance,
            )

        from app.prompt_engine.constants import LIKENESS_HINT_WHEN_REFERENCE
        _has_child_photo = bool(_child_photo_url)
        _likeness = LIKENESS_HINT_WHEN_REFERENCE if _has_child_photo else ""

        _enhancement_skipped = False
        enhanced_report = None
        _pages_before_enhance = [dict(p) for p in pages]

        _enhance_start = time.monotonic()
        try:
            enhancement_result = enhance_all_pages(
                pages=pages,
                blueprint=blueprint,
                character_bible=character_bible,
                visual_style=visual_style,
                location_key=location_display_name,
                likeness_hint=_likeness,
                has_pulid=_has_child_photo,
                leading_prefix_override=leading_prefix_override,
                style_block_override=style_block_override,
            )
            pages = enhancement_result["pages"]
            tracer.prompt_enhance_ok(
                page_count=len(pages),
                latency_ms=(time.monotonic() - _enhance_start) * 1000,
            )

            # Visual prompt validation + auto-fix (V3: shot conflict + value motif checks)
            style_mapping = adapt_style(visual_style)
            visual_validation = validate_visual_prompts(
                pages, character_bible, style_mapping
            )
            if not visual_validation.passed:
                auto_fixes = autofix_visual_prompts(pages, character_bible, style_mapping, visual_validation)
                visual_validation.auto_fixed = auto_fixes
                logger.info("Visual prompt auto-fix applied", fixes=len(auto_fixes))

            # Post-enhancement story-level validation
            enhanced_report = validate_story_output(
                pages=pages,
                blueprint=blueprint,
                magic_items=magic_items or [],
                expected_page_count=page_count,
                character_prompt_block=character_bible.prompt_block,
            )

            if not enhanced_report.all_passed:
                logger.warning(
                    "V3 post-enhancement validation has warnings",
                    failures=[f.code for f in enhanced_report.failures],
                )
        except Exception as _enhance_err:
            _enhancement_skipped = True
            pages = _pages_before_enhance
            tracer.prompt_enhance_fail(error=str(_enhance_err))
            logger.error(
                "V3 enhance_all_pages FAILED — using raw pages (graceful degradation)",
                trace_id=tracer.trace_id,
                error=str(_enhance_err),
                error_type=type(_enhance_err).__name__,
                page_count=len(pages),
            )
            # Minimal fallback: inject identity anchor + outfit lock + hair lock
            # into raw pages so PuLID mode still has basic character grounding.
            _fb_id = character_bible.identity_anchor_minimal if _has_child_photo else character_bible.identity_anchor
            _fb_outfit = f"OUTFIT LOCK: {character_bible.outfit_en}" if character_bible.outfit_en else ""
            _fb_hair = f"HAIR: {character_bible.hair_style}" if character_bible.hair_style else ""
            _fb_neg = (
                "low quality, blurry, extra limbs, deformed hands, "
                "scary, horror, text, watermark, logo, "
                "different outfit, different hairstyle, outfit change"
            )
            for _p in pages:
                _raw_prompt = (_p.get("image_prompt_en") or "").strip()
                if _raw_prompt and _fb_id and _fb_id not in _raw_prompt:
                    _fb_tokens = ", ".join(t for t in [_fb_id, _fb_hair, _fb_outfit] if t)
                    _p["image_prompt_en"] = f"{_fb_tokens}, {_raw_prompt}"
                if not _p.get("negative_prompt"):
                    _p["negative_prompt"] = _fb_neg
            logger.info(
                "Enhancement fallback: injected minimal identity + outfit lock",
                page_count=len(pages),
            )

        # =====================================================================
        # CONVERT TO StoryResponse + FinalPageContent
        # =====================================================================
        title = blueprint.get("title", "")
        if not title:
            _suffix = _get_possessive_suffix(child_name)
            title = f"{child_name}'{_suffix} Büyülü Macerası"

        title = _normalize_title_turkish(title)

        # Determine outfit (CharacterBible is the source of truth now)
        # CharacterBible'da _effective_outfit var; fixed_outfit boş string olabilir
        if not (fixed_outfit or "").strip():
            fixed_outfit = character_bible.outfit_en

        from app.prompt.book_context import BookContext as _BCtx
        from app.prompt.negative_builder import build_negative
        from app.prompt_engine import resolve_style as _resolve_style
        from app.prompt_engine.visual_prompt_builder import build_cover_prompt

        # Pre-build the full inner-page negative once for all pages in this book.
        # LLM (Pass-1) only outputs "bad quality, blurry, text, watermark".
        # We merge that with the proper style + character-consistency negative.
        _style_config = _resolve_style(visual_style or "")
        _neg_ctx = _BCtx.build(
            child_name=child_name,
            child_age=child_age,
            child_gender=child_gender or "",
            style_modifier=visual_style or "",
            face_reference_url="ref" if _has_child_photo else "",
        )
        _base_inner_negative = build_negative(_neg_ctx)

        story_pages: list[PageContent] = []
        final_pages: list[FinalPageContent] = []

        # =====================================================================
        # STEP 1: Synthesize COVER page
        #   page_index=0, page_number=0, story_page_number=None
        #   Cover is image-only — text = title (no story paragraph)
        # =====================================================================
        # build_cover_prompt returns (gemini_scene, flux_prompt, negative_prompt).
        # We use flux_prompt as visual_prompt to preserve clothing consistency.
        cover_scene, _cover_flux_prompt, cover_negative = build_cover_prompt(
            character_bible=character_bible,
            visual_style=visual_style,
            location_key=location_display_name,
            location_constraints=getattr(scenario, "location_constraints", "") or "",
            story_title=title,
            blueprint=blueprint,
            likeness_hint=_likeness,
            has_pulid=_has_child_photo,
        )

        logger.info(
            "V3_COVER_GENERATED",
            page_index=0,
            page_type="cover",
            composer_version="v3",
            COVER_GENERATED=True,
            COVER_SCENE_LENGTH=len(cover_scene),
        )

        story_pages.append(PageContent(
            page_number=0,
            text=title,
            scene_description=cover_scene[:200],
        ))
        final_pages.append(FinalPageContent(
            page_number=0,
            text=title,
            scene_description=cover_scene[:200],
            visual_prompt=_cover_flux_prompt or cover_scene,
            negative_prompt=cover_negative,
            v3_composed=True,
            v3_enhancement_skipped=_enhancement_skipped,
            page_type="cover",
            page_index=0,
            story_page_number=None,
            composer_version="v3",
            pipeline_version="v3",
        ))

        # =====================================================================
        # STEP 2: Process inner pages
        #   LLM pages are 1-indexed (page 1..page_count).
        #   page_index = 1..N (position in book after cover)
        #   story_page_number = same as LLM page number (1..N)
        #
        #   Dedication (page 1, role="dedication"):
        #     - page_type="front_matter", NO image generation
        #     - Carries only text, no visual_prompt needed
        # =====================================================================
        # ⚠️ Hiçbir blueprint sayfa rolü front_matter olarak işaretlenmiyor!
        # "dedication" rolü blueprint'te sayfa 1'e verilse bile, AI o sayfaya
        # hikayenin 1. paragrafını yazar. Bu metni front_matter yaparsak kaybolur.
        # Karşılama 1 (dedication) ve Karşılama 2 sayfaları PDF'de template üzerinden
        # ayrıca render ediliyor — AI'ın üretmesine gerek yok.
        _FRONT_MATTER_ROLES: set[str] = set()  # boş: hiçbir sayfa front_matter olmaz
        bp_pages_list = blueprint.get("pages", [])
        bp_role_by_page: dict[int, str] = {}
        for bp in bp_pages_list:
            bp_role_by_page[bp.get("page", 0)] = bp.get("role", "")

        inner_count = 0
        _page_nums_seen: set[int] = set()
        for _page_idx, page_data in enumerate(pages):
            llm_page_num = page_data.get("page")
            if llm_page_num is None:
                llm_page_num = _page_idx + 1
                logger.warning(
                    "V3_PAGE_MISSING_PAGE_FIELD: assigning sequential page number",
                    page_index=_page_idx,
                    assigned_page_num=llm_page_num,
                )
            llm_page_num = int(llm_page_num)
            if llm_page_num == 0:
                if page_data.get("text_tr", "").strip():
                    llm_page_num = max(_page_nums_seen, default=0) + 1
                    logger.warning(
                        "V3_PAGE0_HAS_STORY_TEXT: reassigning to inner page",
                        new_page_num=llm_page_num,
                        text_preview=page_data.get("text_tr", "")[:60],
                    )
                else:
                    continue
            _page_nums_seen.add(llm_page_num)
            text_tr = page_data.get("text_tr", "")
            image_prompt_en = page_data.get("image_prompt_en", "")
            _llm_neg = (page_data.get("negative_prompt_en") or "").strip()
            _base_tokens = {t.strip().lower() for t in _base_inner_negative.split(",") if t.strip()}
            _new_tokens = [
                t.strip() for t in _llm_neg.split(",")
                if t.strip() and t.strip().lower() not in _base_tokens
            ] if _llm_neg else []
            if _new_tokens:
                negative_prompt_en = f"{_base_inner_negative}, {', '.join(_new_tokens)}"
            else:
                negative_prompt_en = _base_inner_negative

            scene_desc = image_prompt_en[:200] if image_prompt_en else ""

            # Determine page_type from blueprint role
            bp_role = bp_role_by_page.get(llm_page_num, "")
            if bp_role in _FRONT_MATTER_ROLES:
                page_type = "front_matter"
            else:
                page_type = "inner"
                inner_count += 1

            # page_index = position in book (cover=0, so inner starts at 1)
            current_page_index = len(final_pages)  # cover is already at index 0

            story_pages.append(PageContent(
                page_number=llm_page_num,
                text=text_tr,
                scene_description=scene_desc,
            ))

            # Use the fully composed FLUX-style prompt (image_prompt_en) because it contains 
            # the clothing description integrated into the sentence (e.g., "A young boy... wearing...").
            # Using the bare gemini_scene causes clothing consistency loss because the image generator
            # when skip_compose=True relies on the prompt being fully composed.
            gemini_scene = page_data.get("gemini_scene", "")
            final_prompt = image_prompt_en or gemini_scene

            logger.info(
                "V3_PAGE_PIPELINE_STATS",
                page_index=current_page_index,
                story_page_number=llm_page_num,
                page_type=page_type,
                composer_version="v3",
                v3_composed=True,
                skip_compose=True,
                scene_length=len(final_prompt),
                used_gemini_scene=bool(gemini_scene),
                negative_length=len(negative_prompt_en),
            )

            final_pages.append(FinalPageContent(
                page_number=llm_page_num,
                text=text_tr,
                scene_description=scene_desc,
                visual_prompt=final_prompt,
                negative_prompt=negative_prompt_en,
                v3_composed=True,
                v3_enhancement_skipped=_enhancement_skipped,
                page_type=page_type,
                page_index=current_page_index,
                story_page_number=llm_page_num,
                composer_version="v3",
                pipeline_version="v3",
            ))

        # =====================================================================
        # STEP 3: Synthesize BACK COVER page
        #   page_type="backcover", page_index=last+1
        #   Back cover gets an AI-generated image (like front cover) with closing scene.
        #   Bottom 35% is clear for text/QR overlay in render_back_cover().
        # =====================================================================
        try:
            from app.prompt_engine.visual_prompt_builder import build_back_cover_prompt
            _bc_scene, _bc_flux_prompt, _bc_negative = build_back_cover_prompt(
                character_bible=character_bible,
                visual_style=visual_style,
                location_key=location_display_name,
                story_title=title,
                blueprint=blueprint,
                likeness_hint=_likeness,
                has_pulid=_has_child_photo,
            )
            _bc_page_index = len(final_pages)
            final_pages.append(FinalPageContent(
                page_number=999,  # sentinel — not a story page
                text="",
                scene_description=_bc_scene[:200],
                visual_prompt=_bc_flux_prompt or _bc_scene,
                negative_prompt=_bc_negative,
                v3_composed=True,
                v3_enhancement_skipped=_enhancement_skipped,
                page_type="backcover",
                page_index=_bc_page_index,
                story_page_number=None,
                composer_version="v3",
                pipeline_version="v3",
            ))
            logger.info("V3_BACK_COVER_GENERATED", page_index=_bc_page_index)
        except Exception as _bc_err:
            logger.warning("V3_BACK_COVER_PROMPT_FAILED", error=str(_bc_err))

        # =====================================================================
        # GUARDS
        # =====================================================================
        # 1) Cover must be present at position 0
        if not final_pages or final_pages[0].page_type != "cover":
            raise AIServiceError("V3 pipeline FAILED: cover page (page_index=0) is missing — aborting")

        # 2) All pages must have pipeline_version=v3 AND composer_version=v3
        non_v3 = [p for p in final_pages if p.pipeline_version != "v3" or p.composer_version != "v3"]
        if non_v3:
            raise AIServiceError(
                f"V3 pipeline FAILED: {len(non_v3)} pages have pipeline/composer version != 'v3' — aborting"
            )

        # 3) Inner page count: LLM is called with page_count and produces page_count inner pages
        # (cover is page 0 and added separately in STEP 1, not counted in LLM page_count).
        front_matter_count = sum(1 for p in final_pages if p.page_type == "front_matter")
        expected_inner = page_count  # LLM writes exactly page_count inner pages (1..N)
        if inner_count < expected_inner:
            _missing = expected_inner - inner_count
            logger.warning(
                "V3 inner page count SHORT — padding missing pages",
                expected=expected_inner,
                actual=inner_count,
                missing=_missing,
                front_matter=front_matter_count,
            )
            _existing_inner_nums = sorted(
                p.page_number for p in final_pages if p.page_type == "inner"
            )
            _next_num = (_existing_inner_nums[-1] + 1) if _existing_inner_nums else 1
            bp_pages_list = blueprint.get("pages", [])
            for _mi in range(_missing):
                _pad_num = _next_num + _mi
                _bp_idx = _pad_num - 1
                _bp = bp_pages_list[_bp_idx] if _bp_idx < len(bp_pages_list) else {}
                _pad_text = _bp.get("scene_goal", "Macera devam ediyor.")
                _pad_idx = len(final_pages)
                story_pages.append(PageContent(
                    page_number=_pad_num,
                    text=_pad_text,
                    scene_description="",
                ))
                final_pages.append(FinalPageContent(
                    page_number=_pad_num,
                    text=_pad_text,
                    scene_description="",
                    visual_prompt="",
                    negative_prompt=_base_inner_negative,
                    v3_composed=True,
                    v3_enhancement_skipped=True,
                    page_type="inner",
                    page_index=_pad_idx,
                    story_page_number=_pad_num,
                    composer_version="v3",
                    pipeline_version="v3",
                ))
                inner_count += 1
            logger.info(
                "V3 inner pages padded to target",
                final_inner_count=inner_count,
                expected=expected_inner,
            )
        elif inner_count > expected_inner:
            logger.warning(
                "V3 inner page count EXCESS (not trimming)",
                expected=expected_inner,
                actual=inner_count,
                front_matter=front_matter_count,
            )

        story_response = StoryResponse(title=title, pages=story_pages)

        # Location contamination check: fail if any prompt contains wrong-city keywords (e.g. Istanbul in Kapadokya story)
        # Exclude backcover page — its closing scene may not reference the location keyword.
        from app.prompt_engine.qa_checks import run_qa_checks
        _qa_pages = [p.model_dump() for p in final_pages if p.page_type != "backcover"]
        _qa_report = run_qa_checks(
            final_pages=_qa_pages,
            expected_location_key=location_key,
        )
        _loc_failures = (_qa_report.get("checks") or {}).get("location_contamination", {}).get("failures") or []
        if _loc_failures:
            raise AIServiceError(
                "V3 pipeline",
                f"Location contamination: prompts must not contain wrong-city keywords. Failures: {_loc_failures[:3]}",
            )

        tracer.pipeline_complete(
            page_count=len(final_pages),
            enhancement_skipped=_enhancement_skipped,
        )

        logger.info(
            "V3 BLUEPRINT story generation complete",
            trace_id=tracer.trace_id,
            title=title,
            total_pages=len(final_pages),
            cover_present=True,
            front_matter_count=front_matter_count,
            inner_count=inner_count,
            child_name=child_name,
            validation_passed=report.all_passed,
            visual_enhancement_passed=enhanced_report.all_passed if enhanced_report else False,
        )

        return story_response, final_pages, fixed_outfit, blueprint

    @rate_limit_retry(service="gemini", max_attempts=2, timeout_attempts=1)
    async def generate_story_structured(
        self,
        scenario: Scenario,
        child_name: str,
        child_age: int,
        child_gender: str | None,
        visual_style: str = "children's book illustration, soft colors",
        visual_character_description: str = "",  # DOUBLE LOCKING!
        page_count: int = 16,  # Number of story pages (from product settings)
        fixed_outfit: str = "",  # Consistent clothing for all pages
        magic_items: list[str] | None = None,  # V3: magic items
        requested_version: str | None = None,  # "v3" to force V3, None = auto (feature flag)
        leading_prefix_override: str | None = None,
        style_block_override: str | None = None,
        generate_visual_prompts: bool = True,  # False = story text only (for two-phase generation)
    ) -> tuple[StoryResponse, list[FinalPageContent], str, dict | None]:
        """Generate a personalized story.

        Supports TWO modes:
        - V3 Blueprint Pipeline (USE_BLUEPRINT_PIPELINE=true or requested_version="v3")
        - V2 Legacy (default): 2-pass Pure Author + Technical Director

        Returns:
            4-tuple: (StoryResponse, list[FinalPageContent], fixed_outfit, blueprint_json | None)
            blueprint_json is the PASS-0 blueprint dict when V3 is used, None for V2.

        Raises:
            AIServiceError: If generation fails, or if requested_version="v3" but V3 didn't run.
            Non-V3 requests are blocked by policy.
        """
        pipeline_cfg = getattr(settings, "book_pipeline_version", "3")
        # V3 is the only supported pipeline.
        use_v3 = True
        if requested_version == "v2":
            raise AIServiceError(
                "V2_LABEL_BLOCKED: expected v3"
            )
        if pipeline_cfg != "3":
            raise AIServiceError(
                "BOOK_PIPELINE_VERSION must be '3'. Current value is invalid."
            )

        if use_v3:
            from app.core.pipeline_version import prompt_builder_name_for_version

            _builder_name = prompt_builder_name_for_version("v3")
            logger.info(
                "Dispatching to V3 Blueprint Pipeline",
                requested_version=requested_version,
                book_pipeline_version=pipeline_cfg,
                prompt_builder_name=_builder_name,
            )
            logger.info(
                "PROMPT_BUILDER_SELECTED",
                pipeline_version="v3",
                builder_name=_builder_name,
                requested_version=requested_version,
            )
            story_response, final_pages, outfit, blueprint = await self.generate_story_v3(
                scenario=scenario,
                child_name=child_name,
                child_age=child_age,
                child_gender=child_gender,
                visual_style=visual_style,
                visual_character_description=visual_character_description,
                page_count=page_count,
                fixed_outfit=fixed_outfit,
                magic_items=magic_items,
                leading_prefix_override=leading_prefix_override,
                style_block_override=style_block_override,
                generate_visual_prompts=generate_visual_prompts,
            )

            # Hard fail: if caller explicitly requested v3, verify every page
            if requested_version == "v3":
                bad = [p for p in final_pages if p.pipeline_version != "v3"]
                if bad:
                    raise AIServiceError(
                        f"requested_version='v3' but {len(bad)} pages have "
                        f"pipeline_version != 'v3' — aborting"
                    )

            return story_response, final_pages, outfit, blueprint

        # Legacy branch intentionally disabled (V3 single source of truth)
        gender_term = child_gender or "erkek"

        logger.info(
            "Starting TWO-PASS story generation (V2 legacy)",
            scenario=scenario.name,
            child_name=child_name,
            pass1_model=self.story_model,
            pass2_model=self.technical_model,
        )

        # =====================================================================
        # PASS 1: PURE AUTHOR - Write beautiful story
        # ⚠ï¸ SCENARIO TEMPLATES NOW INTEGRATED!
        # =====================================================================

        # Extract scenario template fields — V2 prefers story_prompt_tr, falls back to ai_prompt_template
        ai_prompt_template = (
            getattr(scenario, "story_prompt_tr", None)
            or getattr(scenario, "ai_prompt_template", None)
            or ""
        )
        location_constraints = getattr(scenario, "location_constraints", None) or ""
        cultural_elements = getattr(scenario, "cultural_elements", None)

        # V2: Merge location_en into location_constraints (don't discard either)
        v2_location_en = getattr(scenario, "location_en", None) or ""
        if v2_location_en:
            location_prefix = f"Tüm sahneler {v2_location_en} bölgesinde geçmeli."
            if location_constraints:
                # Merge: prepend location_en if not already present
                if v2_location_en.lower() not in location_constraints.lower():
                    location_constraints = f"{location_prefix} {location_constraints}"
            else:
                location_constraints = location_prefix

        logger.info(
            "[TEMPLATE] SCENARIO TEMPLATES CHECK (V2)",
            scenario_name=scenario.name,
            has_story_prompt_tr=bool(getattr(scenario, "story_prompt_tr", None)),
            has_ai_prompt_template=bool(getattr(scenario, "ai_prompt_template", None)),
            has_location_en=bool(v2_location_en),
            has_location_constraints=bool(location_constraints),
            has_cultural_elements=bool(cultural_elements),
            ai_prompt_preview=ai_prompt_template[:80] if ai_prompt_template else "NONE",
        )

        # V2: Extract no_family flag (compose_story_prompt already adds no_family constraint)
        v2_flags = getattr(scenario, "flags", None) or {}
        v2_no_family = v2_flags.get("no_family", False)

        # V2: no_family banned words list — use word-boundary regex to avoid
        # false positives (e.g. "abi" matching inside "sabırsız", "kabiliye")
        import re as _re

        from app.prompt_engine.constants import NO_FAMILY_BANNED_WORDS_TR

        _no_family_words = [
            w.strip().lower() for w in NO_FAMILY_BANNED_WORDS_TR.split(",") if w.strip()
        ]
        # Pre-compile word-boundary patterns for each banned word
        _no_family_patterns = {
            w: _re.compile(r"(?<![a-zA-ZçğıöşüÇÄİÖÅÜ])" + _re.escape(w) + r"(?![a-zA-ZçğıöşüÇÄİÖÅÜ])", _re.IGNORECASE)
            for w in _no_family_words
        }

        max_pass1_attempts = 2  # Reduced from 4: free tier 15 RPM → her retry 3 Gemini çağrısı
        story_text = ""
        extra_no_family = ""
        for pass1_attempt in range(max_pass1_attempts):
            # Rate limit koruması: ardışık PASS 1 çağrıları arası bekleme
            if pass1_attempt > 0:
                import asyncio as _asyncio_retry
                _retry_delay = 15  # 15s — free tier 15 RPM; önceki çağrı RPM'i tüketmiş olabilir
                logger.info(
                    "[STORY-GEN] Waiting before Pass1 retry to avoid rate limit",
                    delay_seconds=_retry_delay,
                    attempt=pass1_attempt + 1,
                )
                await _asyncio_retry.sleep(_retry_delay)

            story_text = await self._pass1_write_story(
                scenario=scenario,
                child_name=child_name,
                child_age=child_age,
                child_gender=gender_term,
                page_count=page_count,
                cultural_elements=cultural_elements,
                extra_instructions=extra_no_family,
            )

            # --- Aile kelimeleri kontrolü: Sadece senaryo no_family=true ise uygula
            family_ok = True
            if v2_no_family:
                violations = [w for w, pat in _no_family_patterns.items() if pat.search(story_text)]
                if violations:
                    family_ok = False
                    logger.warning(
                        "[STORY-GEN] aile kelimesi ihlali — yasaklı kelimeler bulundu (no_family aktif)",
                        attempt=pass1_attempt + 1,
                        violations=violations,
                        story_preview=story_text[:200],
                    )
                    if not extra_no_family:
                        extra_no_family = (
                            "\n\nğŸš«ğŸš« KESİNLİKLE AİLE KELİMELERİ YASAKLI: "
                            f"{', '.join(_no_family_words)}. "
                            "Bu kelimeleri HİÇBİR ÅEKİLDE kullanma!"
                        )

            if family_ok:
                break

        # Post-loop validation
        # Aile kuralı sadece no_family senaryolarda uygulanır
        if v2_no_family:
            final_violations = [w for w, pat in _no_family_patterns.items() if pat.search(story_text)]
            if final_violations:
                logger.error(
                    "[STORY-GEN] aile kelimesi HARD FAIL — no_family senaryo",
                    violations=final_violations,
                    story_preview=story_text[:300],
                )
                raise ContentPolicyError(
                    f"Hikaye aile kelimeleri içeriyor ({', '.join(final_violations)}). "
                    f"{max_pass1_attempts} deneme sonrasında temiz bir hikaye oluşturulamadı. "
                    "Lütfen farklı bir senaryo veya stil deneyin.",
                )

        # =====================================================================
        # PASS 2: TECHNICAL DIRECTOR - Format and generate SCENE DESCRIPTIONS
        # ⚠ï¸ NOTE: Style is NOT passed here! It's added in _compose_visual_prompts
        # =====================================================================

        # Rate limit koruması: PASS 1 hemen ardından PASS 2 çağrılırsa free tier'da
        # 429 tetiklenir. 15 RPM = 4s/request ama retry'lar RPM'i tüketmiş olabilir.
        import asyncio as _asyncio
        await _asyncio.sleep(10)  # Free tier: 15 RPM; PASS 1 retry'ları sonrası güvenli aralık

        # Get location constraints from scenario (if available)
        location_constraints = ""
        if hasattr(scenario, "location_constraints") and scenario.location_constraints:
            location_constraints = scenario.location_constraints

        logger.info(
            "PASS 2: Generating scene descriptions (NO STYLE)",
            scenario_name=scenario.name,
            has_location_constraints=bool(location_constraints),
        )

        # Determine outfit BEFORE Pass 2 so Gemini + compose use same clothing
        if not fixed_outfit:
            if child_gender == "kiz":
                fixed_outfit = "a colorful adventure dress and comfortable sneakers"
            else:
                fixed_outfit = "an adventure jacket with comfortable pants and sneakers"

        story_response = await self._pass2_format_story(
            story_text=story_text,
            child_name=child_name,
            child_age=child_age,
            child_gender=gender_term,
            visual_character_description=visual_character_description,
            scenario_name=scenario.name,
            location_constraints=location_constraints,
            fixed_outfit=fixed_outfit,
            expected_page_count=page_count + 1,  # +1 for cover (page 0) + page_count inner pages
        )

        logger.info(
            "ğŸ‘• OUTFIT CONSISTENCY",
            fixed_outfit=fixed_outfit,
            source="provided" if fixed_outfit else "default",
        )

        # Load prompt templates from DB for visual prompt composition
        from app.prompt_engine.constants import (
            DEFAULT_COVER_TEMPLATE_EN as _COVER_CONST,
        )
        from app.prompt_engine.constants import (
            DEFAULT_INNER_TEMPLATE_EN as _INNER_CONST,
        )

        _db_cover_tpl = ""
        _db_inner_tpl = ""
        if self._db is not None:
            try:
                if self._prompt_service is None:
                    from app.services.prompt_template_service import get_prompt_service
                    self._prompt_service = get_prompt_service()
                _db_cover_tpl = await self._prompt_service.get_template_en(
                    self._db, "COVER_TEMPLATE", _COVER_CONST
                )
                _db_inner_tpl = await self._prompt_service.get_template_en(
                    self._db, "INNER_TEMPLATE", _INNER_CONST
                )
            except Exception as _tpl_err:
                logger.warning("Failed to load DB templates for compose", error=str(_tpl_err))

        # Compose final pages
        final_pages = self._compose_visual_prompts(
            story_response=story_response,
            scenario=scenario,
            child_name=child_name,
            child_description=visual_character_description
            or self._build_child_description(child_name, child_age, child_gender),
            visual_style=visual_style,
            fixed_outfit=fixed_outfit,
            cover_template_en=_db_cover_tpl,
            inner_template_en=_db_inner_tpl,
        )

        # ==================== TITLE FALLBACK ====================
        # Gemini bazen generic title üretiyor ("Hikaye", "Masal" vb.)
        # Bu durumda çocuğun adı + senaryo adıyla kişiselleştirilmiş title oluştur
        _GENERIC_TITLES = {
            "hikaye", "masal", "hikâye", "öykü", "macera", "story",
            "bir hikaye", "bir masal", "yeni hikaye", "güzel hikaye",
        }
        _raw_title = (story_response.title or "").strip()
        if _raw_title.lower() in _GENERIC_TITLES or len(_raw_title) < 4:
            scenario_name = getattr(scenario, "name", "") or ""
            # "Kapadokya Macerası" -> "Kapadokya Macerası"
            # "Enes" + "Kapadokya Macerası" -> "Enes'in Kapadokya Macerası"
            if scenario_name:
                _suffix = _get_possessive_suffix(child_name)
                new_title = f"{child_name}'{_suffix} {scenario_name}"
            else:
                _suffix = _get_possessive_suffix(child_name)
                new_title = f"{child_name}'{_suffix} Büyülü Macerası"
            story_response.title = new_title
            logger.warning(
                "Generic title replaced with personalized title",
                original_title=_raw_title,
                new_title=new_title,
            )

        # ==================== SCENARIO-SPECIFIC FIXED BOOK TITLES ====================
        _theme = (getattr(scenario, "theme_key", None) or "").strip().lower()
        _sc_name = (getattr(scenario, "name", "") or "").strip().lower()
        _suffix = _get_possessive_suffix(child_name)
        if _theme == "umre_pilgrimage" or "kutsal topraklara" in _sc_name:
            story_response.title = f"{child_name}'{_suffix} Kutsal Topraklara Ziyareti"
            logger.info("Umre title enforced", title=story_response.title)
        elif _theme == "gobeklitepe" or "göbeklitepe" in _sc_name:
            story_response.title = f"{child_name}'{_suffix} Göbeklitepe Macerası"
            logger.info("Göbeklitepe title enforced", title=story_response.title)

        # ==================== TITLE TURKISH NORMALIZATION ====================
        # AI bazen İngilizce yer adları kullanıyor — Türkçe'ye çevir
        story_response.title = _normalize_title_turkish(story_response.title)

        logger.info(
            "TWO-PASS story generation complete",
            title=story_response.title,
            page_count=len(final_pages),
            child_name=child_name,
            fixed_outfit=fixed_outfit,
        )

        if requested_version == "v3":
            raise AIServiceError(
                "requested_version='v3' but pipeline ran V2 (feature flag is off) — aborting"
            )
        if pipeline_cfg == "3":
            raise AIServiceError(
                "BOOK_PIPELINE_VERSION=3 but V2 pipeline ran — aborting (single source: V3)"
            )

        return story_response, final_pages, fixed_outfit, None

    # =========================================================================
    # LEGACY: Single-pass generation (kept for backward compatibility)
    # =========================================================================

    async def _legacy_generate_story_structured(
        self,
        scenario: Scenario,
        child_name: str,
        child_age: int,
        child_gender: str | None,
        visual_style: str = "children's book illustration, soft colors",
        visual_character_description: str = "",
    ) -> tuple[StoryResponse, list[FinalPageContent]]:
        """Legacy single-pass generation - kept for reference."""
        clothing_default = (
            "adventure clothes with a colorful jacket"
            if child_gender == "erkek"
            else "a pretty adventure outfit"
        )

        if visual_character_description:
            character_instruction = f'''â­ DOUBLE LOCKING - KARAKTER AÇIKLAMASI:
"{visual_character_description}"
Bu açıklamayı HER visual_prompt'ta TAM OLARAK KULLAN!'''
        else:
            character_instruction = f"""KARAKTER: A {child_age}-year-old child named {child_name}"""

        system_prompt = f"""Sen bir UZMAN SANAT YÖNETMENİSİN.

{AI_DIRECTOR_SYSTEM}

{character_instruction}

ğŸ“‹ ÇIKTI: JSON formatında 17 sayfalık hikaye ve görsel promptlar.
GÖRSEL STİL: {visual_style}
EÄİTSEL HEDEFLER:
{outcome_text}"""

        user_prompt = f"""SENARYO: {scenario.name}
KARAKTER: {child_name}, {child_age} yaş
Åimdi 17 sayfalık hikaye üret."""

        try:
            api_url = get_gemini_api_url()

            logger.info(
                "Legacy: Generating story with single pass",
                model=self.model,
                scenario=scenario.name,
            )

            client = self._get_gemini_client()
            response = await client.post(
                f"{api_url}?key={self.api_key}",
                json={
                    "contents": [{"parts": [{"text": system_prompt + "\n\n" + user_prompt}]}],
                    "generationConfig": {
                        "temperature": self.story_temperature,
                        "topK": 64,
                        "topP": 0.95,
                        "maxOutputTokens": 16384,
                        "responseMimeType": "application/json",
                    },
                    "safetySettings": [
                        {
                            "category": "HARM_CATEGORY_HARASSMENT",
                            "threshold": "BLOCK_MEDIUM_AND_ABOVE",
                        },
                        {
                            "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                            "threshold": "BLOCK_MEDIUM_AND_ABOVE",
                        },
                        {
                            "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                            "threshold": "BLOCK_MEDIUM_AND_ABOVE",
                        },
                        {
                            "category": "HARM_CATEGORY_HATE_SPEECH",
                            "threshold": "BLOCK_MEDIUM_AND_ABOVE",
                        },
                    ],
                },
            )
            response.raise_for_status()

            data = response.json()
            parts = data["candidates"][0]["content"]["parts"]
            raw_text = _extract_text_from_parts(parts)

            # Parse JSON response
            try:
                story_data = json.loads(raw_text)
                story_response = StoryResponse(**story_data)
            except json.JSONDecodeError as e:
                logger.error(
                    "Failed to parse Gemini JSON response", error=str(e), raw=raw_text[:500]
                )
                raise AIServiceError("Gemini", "Hikaye formatı hatalı. Lütfen tekrar deneyin.")
            except Exception as e:
                logger.error("Failed to validate story structure", error=str(e))
                raise AIServiceError(
                    "Gemini", "Hikaye yapısı doğrulanamadı. Lütfen tekrar deneyin."
                )

            # Compose final visual prompts using scenario templates
            child_description = visual_character_description or self._build_child_description(
                child_name, child_age, child_gender
            )
            final_pages = self._compose_visual_prompts(
                story_response=story_response,
                scenario=scenario,
                child_name=child_name,
                child_description=child_description,
                visual_style=visual_style,
                fixed_outfit=clothing_default,
            )

            logger.info(
                "Structured story generated successfully",
                child_name=child_name,
                scenario=scenario.name,
                page_count=len(story_response.pages),
                title=story_response.title,
                cover_prompt_len=len(final_pages[0].visual_prompt) if final_pages else 0,
            )

            return story_response, final_pages

        except httpx.TimeoutException:
            logger.error("Gemini API timeout", scenario=scenario.name)
            raise AIServiceError(
                "Gemini",
                "AI yoğunluktan dolayı hikayeyi oluşturamadı. Lütfen tekrar deneyin.",
            )
        except httpx.HTTPStatusError as e:
            logger.error(
                "Gemini API error", status=e.response.status_code, body=e.response.text[:500]
            )
            raise AIServiceError("Gemini", "Hikaye oluşturulurken bir hata oluştu.")
        except AIServiceError:
            raise  # Re-raise our custom errors
        except Exception as e:
            logger.exception("Unexpected Gemini error", error=str(e))
            raise AIServiceError("Gemini", "Beklenmeyen bir hata oluştu.")

    # Legacy method for backward compatibility
    @rate_limit_retry(service="gemini", max_attempts=2, timeout_attempts=1)
    async def generate_story(
        self,
        scenario: Scenario,
        child_name: str,
        child_age: int,
        child_gender: str | None,
        outcomes: list[LearningOutcome],
    ) -> str:
        """
        Legacy method: Generate story as plain text.
        Use generate_story_structured() for new implementations.
        """
        story_response, _final_pages, _outfit, _bp = await self.generate_story_structured(
            scenario=scenario,
            child_name=child_name,
            child_age=child_age,
            child_gender=child_gender,
            outcomes=outcomes,
        )

        # Convert structured response to plain text
        full_text = f"# {story_response.title}\n\n"
        for page in story_response.pages:
            if page.page_number == 0:
                continue  # Skip cover for text version
            full_text += f"[SAYFA {page.page_number}]\n{page.text}\n\n"

        return full_text

    async def generate_story_with_prompts(
        self,
        scenario: Scenario,
        child_name: str,
        child_age: int,
        child_gender: str | None,
        outcomes: list[LearningOutcome],
        visual_style: str = "children's book illustration, soft colors",
    ) -> tuple[str, list[FinalPageContent]]:
        """
        Generate story and return both title and pages with composed visual prompts.

        This is the recommended method for new code.

        Returns:
            Tuple of (title, list[FinalPageContent])
        """
        story_response, final_pages, _outfit, _bp = await self.generate_story_structured(
            scenario=scenario,
            child_name=child_name,
            child_age=child_age,
            child_gender=child_gender,
            outcomes=outcomes,
            visual_style=visual_style,
        )
        return story_response.title, final_pages

    def parse_story_pages(self, story_text: str) -> list[str]:
        """
        Parse generated story into individual pages (legacy support).

        Args:
            story_text: Full story text with [SAYFA X] markers

        Returns:
            List of page texts
        """
        import re

        # Split by page markers
        pages = re.split(r"\[SAYFA \d+\]", story_text)

        # Clean up and filter empty pages
        pages = [p.strip() for p in pages if p.strip()]

        # Ensure we have at least 16 pages, pad if necessary
        while len(pages) < 16:
            pages.append("")

        return pages[:16]  # Return exactly 16 pages

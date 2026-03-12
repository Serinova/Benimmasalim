"""PASS-0: Blueprint generation mixin for GeminiService.

Extracted from _story_writer.py.  Provides _BlueprintMixin which is
inherited by _StoryWriterMixin → GeminiService.
"""

from __future__ import annotations

import json

import httpx
import structlog

from app.core.exceptions import AIServiceError
from app.models.scenario import Scenario
from app.services.ai._helpers import (
    _extract_text_from_parts,
    get_gemini_story_url,
)
from app.services.ai.llm_output_repair import (
    repair_blueprint as _repair_blueprint,
)

logger = structlog.get_logger()


class _BlueprintMixin:
    """Mixin providing PASS-0 blueprint generation."""

    async def _pass0_generate_blueprint(
        self,
        *,
        child_name: str,
        child_age: int,
        child_description: str,
        location_key: str,
        location_display_name: str,
        visual_style: str,
        magic_items: list[str],
        page_count: int,
        scenario: Scenario,
        book_title: str = "",
    ) -> dict:
        """PASS-0: Generate story blueprint JSON.

        Returns the parsed blueprint dict with page roles, cultural hooks,
        magic item distribution, and visual briefs.
        """
        import asyncio as _asyncio_bp

        from app.prompt_engine.blueprint_prompt import (
            BLUEPRINT_SYSTEM_PROMPT,
            build_blueprint_task_prompt,
        )
        from app.prompt_engine.scenario_bible import get_scenario_bible

        # Resolve scenario bible
        db_bible = getattr(scenario, "scenario_bible", None)
        bible = get_scenario_bible(location_key, db_bible=db_bible)

        system_prompt = await self._get_prompt(
            "BLUEPRINT_SYSTEM_PROMPT", BLUEPRINT_SYSTEM_PROMPT
        )

        # Extract story structure from scenario (hikaye yapısı, zone progression, epic moments)
        story_structure = getattr(scenario, "story_prompt_tr", "") or ""
        
        task_prompt = build_blueprint_task_prompt(
            child_name=child_name,
            child_age=child_age,
            child_description=child_description,
            location_key=location_key,
            location_display_name=location_display_name,
            visual_style=visual_style,
            magic_items=magic_items,
            page_count=page_count,
            bible=bible,
            book_title=book_title,
            story_structure=story_structure,  # YENİ: Senaryo yapısını blueprint'e dahil et
        )

        full_prompt = system_prompt + "\n\n" + task_prompt

        blueprint_url = get_gemini_story_url()
        max_retries = 3
        base_wait = 10

        for attempt in range(max_retries):
            try:
                logger.info(
                    "PASS-0: Generating blueprint",
                    model=self.story_model,
                    page_count=page_count,
                    location=location_key,
                    attempt=attempt + 1,
                )

                client = self._get_gemini_client()
                response = await client.post(
                    f"{blueprint_url}?key={self.api_key}",
                    json={
                        "contents": [{"parts": [{"text": full_prompt}]}],
                        "generationConfig": {
                            "temperature": 0.7,
                            "topK": 40,
                            "topP": 0.90,
                            "maxOutputTokens": 16000,
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
                blueprint = self._extract_and_repair_json(raw_text)

                # Gemini bazen array döndürebilir — dict'e wrap et
                if isinstance(blueprint, list):
                    logger.warning(
                        "PASS-0: Blueprint as list, wrapping to dict",
                        list_len=len(blueprint),
                    )
                    blueprint = {"pages": blueprint}

                # Page count pre-check: retry if mismatch and retries remain
                bp_pages = blueprint.get("pages", [])
                if len(bp_pages) != page_count and attempt < max_retries - 1:
                    logger.warning(
                        "PASS-0: Blueprint page count mismatch, retrying",
                        expected=page_count,
                        got=len(bp_pages),
                        attempt=attempt + 1,
                    )
                    await _asyncio_bp.sleep(base_wait * (attempt + 1))
                    continue

                # Full schema repair (page count, story_arc, act, emotional_state…)
                blueprint, bp_repairs = _repair_blueprint(blueprint, page_count)
                if bp_repairs:
                    logger.info(
                        "PASS-0: Blueprint repaired",
                        repairs=bp_repairs,
                    )

                logger.info(
                    "PASS-0: Blueprint generated",
                    title=blueprint.get("title", ""),
                    pages=len(blueprint.get("pages", [])),
                    repairs_count=len(bp_repairs),
                )
                return blueprint

            except httpx.HTTPStatusError as exc:
                if exc.response.status_code == 429 and attempt < max_retries - 1:
                    wait = base_wait * (attempt + 1)
                    logger.warning("PASS-0: Rate limited, waiting", wait=wait)
                    await _asyncio_bp.sleep(wait)
                    continue
                raise AIServiceError(
                    "Gemini",
                    f"Blueprint oluşturulamadı (HTTP {exc.response.status_code})",
                    reason_code="BLUEPRINT_HTTP_FAIL",
                ) from exc
            except (KeyError, IndexError, json.JSONDecodeError) as exc:
                if attempt < max_retries - 1:
                    await _asyncio_bp.sleep(base_wait)
                    continue
                raise AIServiceError(
                    "Gemini",
                    f"Blueprint JSON ayrıştırma hatası: {type(exc).__name__}",
                    reason_code="BLUEPRINT_PARSE_FAIL",
                ) from exc

        raise AIServiceError(
            "Gemini",
            "Blueprint tüm denemelerde oluşturulamadı.",
            reason_code="BLUEPRINT_ALL_RETRIES_EXHAUSTED",
        )

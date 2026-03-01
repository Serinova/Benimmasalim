"""Gemini AI service for story generation with TWO-PASS GENERATION strategy.

TWO-PASS GENERATION STRATEGY:
=============================
PASS 1 - "Pure Author" (gemini-2.5-flash):
  - Focus: 100% on creative writing
  - Output: Beautiful, emotional, immersive story TEXT ONLY

PASS 2 - "Technical Director" (gemini-2.5-flash):
  - Input: The beautiful story from Pass 1
  - Focus: Split into pages, generate visual prompts
  - Output: Structured JSON with visual prompts

Architecture notes (sub-modules):
  _models.py        — Pydantic output models
  _helpers.py       — constants, URL helpers, Turkish text utils
  _visual_composer.py — _VisualComposerMixin (scene/visual methods)
  _story_writer.py  — _StoryWriterMixin (story generation methods)
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

import httpx
import structlog

from app.config import settings
from app.core.exceptions import AIServiceError
from app.core.rate_limit import rate_limit_retry
from app.services.ai._helpers import (
    AI_DIRECTOR_SYSTEM,
    GEMINI_API_BASE,
    _DEFAULT_FLASH_MODEL,
    _extract_text_from_parts,
    get_gemini_api_url,
    get_gemini_story_url,
    get_gemini_technical_url,
)
from app.services.ai._models import (
    FinalPageContent,
    PageContent,
    PageManifest,
    PageManifestEntry,
    StoryResponse,
)
from app.services.ai._story_writer import _StoryWriterMixin
from app.services.ai._visual_composer import _VisualComposerMixin

# Re-export helpers that external code imports directly from gemini_service
from app.services.ai._helpers import (  # noqa: F401
    _get_possessive_suffix,
    _normalize_title_turkish,
    build_educational_prompt,
    get_value_message_tr_for_outcomes,
    get_value_visual_motif_for_outcomes,
)

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()


# ============== Gemini Service ==============


class GeminiService(_StoryWriterMixin, _VisualComposerMixin):
    """Service for generating stories using Google Gemini with TWO-PASS GENERATION.

    TWO-PASS STRATEGY:
    =================
    PASS 1 - "Pure Author" (gemini-2.5-flash):
      - 100% creative focus
      - Beautiful, emotional stories
      - No JSON, no technical constraints

    PASS 2 - "Technical Director" (gemini-2.5-flash):
      - Takes the beautiful story
      - Splits into pages
      - Generates visual prompts
      - Outputs structured JSON

    DYNAMIC PROMPT SUPPORT:
    ======================
    When a database session is provided, prompts can be loaded dynamically from
    the PromptTemplate table, allowing admins to modify prompts without code changes.
    Falls back to hardcoded constants if DB lookup fails.
    """

    def __init__(self, db_session: "AsyncSession | None" = None):
        """
        Initialize GeminiService.

        Args:
            db_session: Optional database session for dynamic prompt loading.
                        If not provided, uses hardcoded prompt constants.
        """
        self.api_key = settings.gemini_api_key
        self.timeout = 180.0  # seconds (32-page stories need more time)
        self._db = db_session

        # TWO-PASS MODEL CONFIGURATION
        self.story_model = getattr(settings, "gemini_story_model", None) or _DEFAULT_FLASH_MODEL
        self.technical_model = (
            getattr(settings, "gemini_technical_model", None) or _DEFAULT_FLASH_MODEL
        )
        self.model = settings.gemini_model or _DEFAULT_FLASH_MODEL

        self.story_temperature = settings.gemini_story_temperature or 0.92
        self.scene_temperature = settings.gemini_scene_temperature or 0.7

        # Shared httpx client — reuses TCP connections across Gemini calls
        self._http_client: httpx.AsyncClient | None = None

        # Initialize PromptTemplateService for dynamic prompts
        self._prompt_service = None

        logger.info(
            "GeminiService initialized with TWO-PASS strategy",
            story_model=self.story_model,
            technical_model=self.technical_model,
            story_temperature=self.story_temperature,
            dynamic_prompts_enabled=db_session is not None,
        )

    def _get_gemini_client(self) -> httpx.AsyncClient:
        """Lazy-init shared httpx client for Gemini API calls."""
        if self._http_client is None or self._http_client.is_closed:
            self._http_client = httpx.AsyncClient(
                timeout=self.timeout,
                limits=httpx.Limits(
                    max_connections=100,
                    max_keepalive_connections=20,
                    keepalive_expiry=60,
                ),
            )
        return self._http_client

    async def _get_prompt(self, key: str, fallback: str) -> str:
        """Get prompt content from database or fallback to hardcoded constant.

        Enables dynamic prompt management via admin panel while maintaining
        safety through hardcoded fallbacks.
        """
        if self._db is None:
            return fallback

        try:
            if self._prompt_service is None:
                from app.services.prompt_template_service import get_prompt_service

                self._prompt_service = get_prompt_service()

            return await self._prompt_service.get_prompt(
                db=self._db,
                key=key,
                fallback=fallback,
            )
        except Exception as e:
            logger.warning(
                "Failed to fetch dynamic prompt, using fallback",
                key=key,
                error=str(e),
            )
            return fallback

    @rate_limit_retry(service="gemini", max_attempts=2, timeout_attempts=1)
    async def generate_json(self, prompt: str) -> dict:
        """Generate JSON response from a prompt using Gemini with Visual Director instructions.

        Used by StoryGenerationService for generating story text with clear,
        2D-friendly scene descriptions.
        """
        api_url = get_gemini_api_url()

        enhanced_prompt = prompt
        if "AI-DIRECTOR" not in prompt and "SANAT YÖNETMENİ" not in prompt:
            enhanced_prompt = f"{AI_DIRECTOR_SYSTEM}\n\n{prompt}"

        logger.info(
            "Generating JSON with Visual Director",
            model=self.model,
            temperature=self.story_temperature,
            prompt_length=len(enhanced_prompt),
        )

        try:
            client = self._get_gemini_client()
            response = await client.post(
                f"{api_url}?key={self.api_key}",
                json={
                    "contents": [{"parts": [{"text": enhanced_prompt}]}],
                    "generationConfig": {
                        "temperature": self.story_temperature,
                        "topK": 64,
                        "topP": 0.95,
                        "maxOutputTokens": 16384,
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

            try:
                result = json.loads(raw_text)
                logger.info("JSON generation successful", keys=list(result.keys()) if isinstance(result, dict) else "list")
                return result
            except json.JSONDecodeError as e:
                logger.error("Failed to parse Gemini JSON", error=str(e), raw=raw_text[:500])
                raise AIServiceError("Gemini", "AI yanıtı işlenemedi. Lütfen tekrar deneyin.")

        except httpx.TimeoutException:
            logger.error("Gemini API timeout in generate_json")
            raise AIServiceError("Gemini", "AI yoğunluktan dolayı yanıt veremedi.")
        except httpx.HTTPStatusError as e:
            logger.error("Gemini API error", status=e.response.status_code)
            raise AIServiceError("Gemini", "AI servisinde hata oluştu.")
        except AIServiceError:
            raise
        except Exception as e:
            logger.exception("Unexpected error in generate_json", error=str(e))
            raise AIServiceError("Gemini", "Beklenmeyen bir hata oluştu.")

    async def enhance_pages_with_visual_prompts(
        self,
        story_pages: list[dict],
        blueprint: dict,
        character_bible,
        visual_style: str,
        location_key: str,
        value_visual_motif: str = "",
        likeness_hint: str = "",
        has_pulid: bool = False,
        leading_prefix_override: str | None = None,
        style_block_override: str | None = None,
    ) -> list[dict]:
        """Generate visual prompts for story pages that only have text.

        Used in two-phase generation: after story text is approved, generate visual prompts.
        """
        from app.prompt_engine.visual_prompt_builder import enhance_all_pages

        logger.info(
            "Enhancing pages with visual prompts",
            page_count=len(story_pages),
            has_character_bible=bool(character_bible),
        )

        try:
            enhancement_result = enhance_all_pages(
                pages=story_pages,
                blueprint=blueprint,
                character_bible=character_bible,
                visual_style=visual_style,
                location_key=location_key,
                value_visual_motif=value_visual_motif,
                likeness_hint=likeness_hint,
                has_pulid=has_pulid,
                leading_prefix_override=leading_prefix_override,
                style_block_override=style_block_override,
            )
            enhanced_pages = enhancement_result["pages"]

            logger.info(
                "Visual prompts enhanced successfully",
                original_count=len(story_pages),
                enhanced_count=len(enhanced_pages),
            )
            return enhanced_pages
        except Exception as e:
            logger.error("Failed to enhance visual prompts", error=str(e), page_count=len(story_pages))
            raise


_gemini_service: GeminiService | None = None


def get_gemini_service() -> GeminiService:
    """Get or create GeminiService singleton (single source for story/clothing)."""
    global _gemini_service
    if _gemini_service is None:
        _gemini_service = GeminiService()
    return _gemini_service


# Convenience alias used in some endpoints
gemini_service = get_gemini_service


__all__ = [
    "GeminiService",
    "PageContent",
    "StoryResponse",
    "FinalPageContent",
    "PageManifest",
    "PageManifestEntry",
    "get_gemini_service",
    "gemini_service",
    "get_gemini_story_url",
    "get_gemini_technical_url",
    "get_gemini_api_url",
    "_get_possessive_suffix",
    "_normalize_title_turkish",
    "build_educational_prompt",
    "get_value_visual_motif_for_outcomes",
    "get_value_message_tr_for_outcomes",
]

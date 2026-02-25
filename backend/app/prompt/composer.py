"""PromptComposer — tek giriş noktası.

Tüm prompt oluşturma bu class üzerinden, tek yoldan geçer.
V2/V3 ayrımı yok. BookContext kitap başında bir kez oluşturulur.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import structlog

from app.prompt.book_context import BookContext
from app.prompt.cover_builder import build_cover_prompt
from app.prompt.negative_builder import build_negative
from app.prompt.page_builder import build_page_prompt
from app.prompt.sanitizer import MAX_PROMPT_CHARS, truncate_safe

logger = structlog.get_logger()


@dataclass
class PromptResult:
    """Prompt oluşturma sonucu."""

    prompt: str
    negative_prompt: str
    metadata: dict = field(default_factory=dict)


class PromptComposer:
    """Kitap için prompt oluşturma — tek pipeline, tek yol."""

    def __init__(
        self,
        ctx: BookContext,
        *,
        cover_template: str | None = None,
        inner_template: str | None = None,
    ) -> None:
        self._ctx = ctx
        self._cover_template = cover_template
        self._inner_template = inner_template
        self._negative = build_negative(ctx)

    @property
    def negative_prompt(self) -> str:
        return self._negative

    @property
    def context(self) -> BookContext:
        return self._ctx

    def compose_cover(self, scene_description: str) -> PromptResult:
        """Kapak prompt'u oluşturur."""
        prompt = build_cover_prompt(
            self._ctx,
            scene_description,
            template=self._cover_template,
        )

        if len(prompt) > MAX_PROMPT_CHARS:
            prompt = truncate_safe(prompt, MAX_PROMPT_CHARS)

        logger.info(
            "cover_prompt_composed",
            style=self._ctx.style.key,
            prompt_length=len(prompt),
            negative_length=len(self._negative),
        )

        return PromptResult(
            prompt=prompt,
            negative_prompt=self._negative,
            metadata={
                "style_key": self._ctx.style.key,
                "is_cover": True,
                "has_face_ref": bool(self._ctx.face_reference_url),
            },
        )

    def compose_page(self, scene_description: str, page_number: int) -> PromptResult:
        """İç sayfa prompt'u oluşturur."""
        prompt = build_page_prompt(
            self._ctx,
            scene_description,
            page_number,
            template=self._inner_template,
        )

        if len(prompt) > MAX_PROMPT_CHARS:
            prompt = truncate_safe(prompt, MAX_PROMPT_CHARS)

        logger.info(
            "page_prompt_composed",
            style=self._ctx.style.key,
            page_number=page_number,
            prompt_length=len(prompt),
        )

        return PromptResult(
            prompt=prompt,
            negative_prompt=self._negative,
            metadata={
                "style_key": self._ctx.style.key,
                "page_number": page_number,
                "is_cover": False,
                "has_face_ref": bool(self._ctx.face_reference_url),
            },
        )

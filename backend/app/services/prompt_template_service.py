"""Backward-compatibility shim for prompt_template_service.

Eski API imzalarını korur: get_prompt(db, key, fallback) ve get_template_en(db, key, fallback).
Yeni sistemde app.prompt.service.PromptService kullanılacak.
"""

from __future__ import annotations

from typing import Any

import structlog

logger = structlog.get_logger()


class PromptTemplateService:
    """Eski prompt template service — yeni sisteme yönlendirir."""

    async def get_prompt(
        self,
        db: Any = None,
        key: str = "",
        fallback: str = "",
        **kwargs: Any,
    ) -> str:
        """DB'den prompt yükler, yoksa fallback döner.

        Eski imza: get_prompt(db, key, fallback)
        Keyword-arg imzası: get_prompt(db=..., key=..., fallback=...)
        """
        if db is None:
            return fallback or ""
        try:
            from app.prompt.service import PromptService
            svc = PromptService(db)
            return await svc.get(key, fallback=fallback)
        except Exception:
            logger.warning("prompt_template_service_shim_error", key=key)
            return fallback or ""

    async def get_template_en(
        self,
        db: Any = None,
        key: str = "",
        fallback: str = "",
        **kwargs: Any,
    ) -> str:
        """EN template yükler, yoksa fallback döner.

        Eski imza: get_template_en(db, key, fallback)
        """
        if db is None:
            return fallback or ""
        try:
            from app.prompt.service import PromptService
            svc = PromptService(db)
            return await svc.get_en(key, fallback=fallback)
        except Exception:
            logger.warning("prompt_template_service_shim_error", key=key)
            return fallback or ""

    async def render_template(
        self,
        db: Any = None,
        key: str = "",
        fallback: str = "",
        **kwargs: Any,
    ) -> str:
        content = await self.get_prompt(db, key, fallback)
        if content and kwargs:
            try:
                return content.format(**kwargs)
            except (KeyError, IndexError):
                pass
        return content or fallback or ""

    def get_cache_stats(self) -> dict:
        from app.prompt.service import PromptService
        return PromptService.cache_stats()

    def clear_cache(self, key: str | None = None) -> None:
        from app.prompt.service import PromptService
        PromptService.clear_cache(key)


_instance: PromptTemplateService | None = None


def get_prompt_service() -> PromptTemplateService:
    global _instance
    if _instance is None:
        _instance = PromptTemplateService()
    return _instance

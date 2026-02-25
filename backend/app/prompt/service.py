"""Prompt template service — DB cache + fallback.

Admin panelinden düzenlenen prompt'ları yükler.
5 dakika TTL ile in-memory cache kullanır.
DB'de yoksa hardcoded fallback döner.
"""

from __future__ import annotations

import time
from typing import Any

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.prompt_template import PromptTemplate

logger = structlog.get_logger()

_CACHE_TTL = 300  # 5 dakika
_cache: dict[str, tuple[float, Any]] = {}


class PromptService:
    """Prompt template yükleme servisi."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def get(self, key: str, *, fallback: str = "") -> str:
        """Prompt'u DB'den yükler, cache'ler. Yoksa fallback döner."""
        cached = _cache.get(key)
        if cached and (time.time() - cached[0]) < _CACHE_TTL:
            return cached[1]

        try:
            result = await self._db.execute(
                select(PromptTemplate.content).where(
                    PromptTemplate.key == key,
                    PromptTemplate.is_active == True,
                )
            )
            content = result.scalar_one_or_none()
            value = content if content is not None else fallback
        except Exception:
            logger.warning("prompt_service_db_error", key=key)
            value = fallback

        _cache[key] = (time.time(), value)
        return value

    async def get_en(self, key: str, *, fallback: str = "") -> str:
        """İngilizce template'i yükler."""
        cached_key = f"{key}__en"
        cached = _cache.get(cached_key)
        if cached and (time.time() - cached[0]) < _CACHE_TTL:
            return cached[1]

        try:
            result = await self._db.execute(
                select(PromptTemplate.content_en).where(
                    PromptTemplate.key == key,
                    PromptTemplate.is_active == True,
                )
            )
            content = result.scalar_one_or_none()
            value = content if content is not None else fallback
        except Exception:
            logger.warning("prompt_service_db_error", key=key)
            value = fallback

        _cache[cached_key] = (time.time(), value)
        return value

    async def get_all(self, category: str | None = None) -> list[PromptTemplate]:
        """Tüm aktif prompt'ları listeler."""
        query = select(PromptTemplate).where(PromptTemplate.is_active == True)
        if category:
            query = query.where(PromptTemplate.category == category)
        query = query.order_by(PromptTemplate.category, PromptTemplate.key)

        result = await self._db.execute(query)
        return list(result.scalars().all())

    @staticmethod
    def clear_cache(key: str | None = None) -> None:
        """Cache temizler."""
        if key:
            _cache.pop(key, None)
            _cache.pop(f"{key}__en", None)
        else:
            _cache.clear()

    @staticmethod
    def cache_stats() -> dict:
        """Cache istatistikleri."""
        now = time.time()
        active = sum(1 for _, (ts, _) in _cache.items() if (now - ts) < _CACHE_TTL)
        return {"total": len(_cache), "active": active, "ttl_seconds": _CACHE_TTL}

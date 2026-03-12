"""
Görsel üretim sağlayıcı seçimi ve effective config.

- get_image_provider_for_generation(provider_name) -> Gemini servisi
- get_effective_ai_config(db, product_id?) -> AIGenerationConfig (varsayılan veya ürün)
"""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.book_template import AIGenerationConfig
from app.models.product import Product

# Provider name normalization
GEMINI_PROVIDER_VALUES = ("gemini", "gemini_flash")
DEFAULT_PROVIDER_FALLBACK = "gemini"


_gemini_service = None  # Singleton — connection pool paylasilsin


def get_image_provider_for_generation(provider_name: str):
    """
    Sadece Gemini servisini döndürür.
    """
    global _gemini_service
    if _gemini_service is None:
        from app.services.ai.gemini_consistent_image import GeminiConsistentImageService

        _gemini_service = GeminiConsistentImageService()
    return _gemini_service


async def get_effective_ai_config(
    db: AsyncSession,
    product_id: UUID | None = None,
) -> AIGenerationConfig | None:
    """
    Stil testi / trials / ai.py: product_id vermeden çağrılırsa varsayılan config.
    generate_book / orders: product_id ile ürünün ai_config'i; yoksa varsayılan.
    """
    if product_id:
        product = await db.get(Product, product_id)
        if product and product.ai_config_id:
            config = await db.get(AIGenerationConfig, product.ai_config_id)
            if config and config.is_active:
                return config
    result = await db.execute(
        select(AIGenerationConfig).where(
            AIGenerationConfig.is_active == True,
            AIGenerationConfig.is_default == True,
        )
    )
    default = result.scalar_one_or_none()
    return default


async def get_effective_image_provider_name(
    db: AsyncSession,
    product_id: UUID | None = None,
) -> str:
    """
    Effective AIGenerationConfig'ten image_provider döndürür.
    Config yoksa DEFAULT_PROVIDER_FALLBACK ("gemini").
    """
    config = await get_effective_ai_config(db, product_id=product_id)
    if not config:
        return DEFAULT_PROVIDER_FALLBACK
    return (config.image_provider or DEFAULT_PROVIDER_FALLBACK).strip().lower()

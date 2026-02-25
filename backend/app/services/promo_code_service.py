"""Promo code business logic: validation, discount calculation, atomic consumption."""

import secrets
import string
from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

import structlog
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ValidationError
from app.models.promo_code import DiscountType, PromoCode

logger = structlog.get_logger()

# Characters for code generation (exclude O/0/I/1 to avoid confusion)
_CODE_CHARS = string.ascii_uppercase.replace("O", "").replace("I", "") + "23456789"


async def generate_promo_code(
    db: AsyncSession,
    length: int = 8,
    prefix: str = "",
    max_attempts: int = 10,
) -> str:
    """
    Generate a unique promo code.

    Uses A-Z (excluding O, I) + 2-9 to avoid visual ambiguity.
    Checks DB uniqueness; retries on collision.
    """
    for _ in range(max_attempts):
        random_part = "".join(secrets.choice(_CODE_CHARS) for _ in range(length))
        code = f"{prefix}{random_part}" if prefix else random_part

        result = await db.execute(
            select(PromoCode.id).where(PromoCode.code == code)
        )
        if result.scalar_one_or_none() is None:
            return code

    raise ValidationError(
        f"Benzersiz kupon kodu üretilemedi ({max_attempts} deneme sonrası)"
    )


async def validate_promo_code(
    code: str,
    subtotal: Decimal,
    db: AsyncSession,
) -> PromoCode:
    """
    Validate a promo code for use. Checks:
    1. Code exists
    2. is_active = True
    3. Within valid_from / valid_until range
    4. used_count < usage_limit
    5. subtotal >= min_order_amount (if set)

    Returns the PromoCode object if valid, raises ValidationError otherwise.
    """
    result = await db.execute(
        select(PromoCode).where(PromoCode.code == code.strip().upper())
    )
    promo = result.scalar_one_or_none()

    # Generic error message for all failure cases to prevent promo code enumeration
    _GENERIC_ERR = "Kupon kodu geçersiz veya kullanılamıyor"

    if not promo:
        raise ValidationError(_GENERIC_ERR)

    if not promo.is_active:
        raise ValidationError(_GENERIC_ERR)

    now = datetime.now(UTC)

    if promo.valid_from and now < promo.valid_from:
        raise ValidationError(_GENERIC_ERR)

    if promo.valid_until and now > promo.valid_until:
        raise ValidationError(_GENERIC_ERR)

    if promo.used_count >= promo.usage_limit:
        raise ValidationError(_GENERIC_ERR)

    if promo.min_order_amount and subtotal < promo.min_order_amount:
        raise ValidationError(_GENERIC_ERR)

    return promo


def calculate_discount(promo: PromoCode, subtotal: Decimal) -> Decimal:
    """
    Calculate the discount amount based on promo type.

    PERCENT: discount = subtotal * value / 100, capped by max_discount_amount
    AMOUNT: discount = value (fixed)

    Final discount never exceeds subtotal (no negative orders).
    """
    if promo.discount_type == DiscountType.PERCENT:
        discount = subtotal * promo.discount_value / Decimal("100")
        if promo.max_discount_amount:
            discount = min(discount, promo.max_discount_amount)
    else:
        # AMOUNT
        discount = promo.discount_value

    # Discount can't exceed subtotal
    discount = min(discount, subtotal)

    # Round to 2 decimal places
    return discount.quantize(Decimal("0.01"))


async def consume_promo_code(promo_id: UUID, db: AsyncSession) -> bool:
    """
    Atomically increment used_count if the promo code is still valid.

    Uses a single UPDATE with WHERE conditions for concurrency safety:
    - is_active = true
    - used_count < usage_limit

    Returns True if consumption succeeded, False if limit was already reached
    (race condition protection).
    """
    result = await db.execute(
        update(PromoCode)
        .where(
            PromoCode.id == promo_id,
            PromoCode.is_active.is_(True),
            PromoCode.used_count < PromoCode.usage_limit,
        )
        .values(used_count=PromoCode.used_count + 1)
    )

    consumed = result.rowcount > 0

    if consumed:
        logger.info("promo_code_consumed", promo_id=str(promo_id))
    else:
        logger.warning("promo_code_consume_failed", promo_id=str(promo_id))

    return consumed

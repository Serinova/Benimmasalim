"""Unit tests for promo code service: discount calculation, code generation, validation."""

import uuid
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.models.promo_code import DiscountType, PromoCode
from app.services.promo_code_service import (
    _CODE_CHARS,
    calculate_discount,
    validate_promo_code,
)

# ─── Helpers ─────────────────────────────────────────────────────


def _make_promo(**overrides) -> PromoCode:
    """Create a PromoCode instance with sensible defaults for testing."""
    defaults = {
        "id": uuid.uuid4(),
        "code": "TEST100",
        "discount_type": DiscountType.PERCENT,
        "discount_value": Decimal("10"),
        "usage_limit": 100,
        "used_count": 0,
        "is_active": True,
        "valid_from": None,
        "valid_until": None,
        "min_order_amount": None,
        "max_discount_amount": None,
        "notes": None,
        "created_by": None,
    }
    defaults.update(overrides)
    promo = PromoCode.__new__(PromoCode)
    for k, v in defaults.items():
        object.__setattr__(promo, k, v)
    return promo


# ─── calculate_discount ─────────────────────────────────────────


class TestCalculateDiscount:
    """Tests for calculate_discount function."""

    def test_percent_discount(self):
        """25% discount on 400 TL -> 100 TL."""
        promo = _make_promo(
            discount_type=DiscountType.PERCENT,
            discount_value=Decimal("25"),
        )
        result = calculate_discount(promo, Decimal("400.00"))
        assert result == Decimal("100.00")

    def test_amount_discount(self):
        """50 TL fixed discount."""
        promo = _make_promo(
            discount_type=DiscountType.AMOUNT,
            discount_value=Decimal("50"),
        )
        result = calculate_discount(promo, Decimal("400.00"))
        assert result == Decimal("50.00")

    def test_percent_with_max_cap(self):
        """50% of 400 = 200, but max_discount_amount=100 -> capped at 100."""
        promo = _make_promo(
            discount_type=DiscountType.PERCENT,
            discount_value=Decimal("50"),
            max_discount_amount=Decimal("100"),
        )
        result = calculate_discount(promo, Decimal("400.00"))
        assert result == Decimal("100.00")

    def test_percent_without_cap(self):
        """50% of 400 = 200, no cap -> 200."""
        promo = _make_promo(
            discount_type=DiscountType.PERCENT,
            discount_value=Decimal("50"),
        )
        result = calculate_discount(promo, Decimal("400.00"))
        assert result == Decimal("200.00")

    def test_amount_exceeds_subtotal(self):
        """Fixed 500 TL discount on 400 TL order -> capped at 400."""
        promo = _make_promo(
            discount_type=DiscountType.AMOUNT,
            discount_value=Decimal("500"),
        )
        result = calculate_discount(promo, Decimal("400.00"))
        assert result == Decimal("400.00")

    def test_percent_100(self):
        """100% discount -> full subtotal."""
        promo = _make_promo(
            discount_type=DiscountType.PERCENT,
            discount_value=Decimal("100"),
        )
        result = calculate_discount(promo, Decimal("450.00"))
        assert result == Decimal("450.00")

    def test_small_percent(self):
        """1% of 450 -> 4.50."""
        promo = _make_promo(
            discount_type=DiscountType.PERCENT,
            discount_value=Decimal("1"),
        )
        result = calculate_discount(promo, Decimal("450.00"))
        assert result == Decimal("4.50")

    def test_rounding(self):
        """33% of 100 -> 33.00 (rounded to 2 decimals)."""
        promo = _make_promo(
            discount_type=DiscountType.PERCENT,
            discount_value=Decimal("33"),
        )
        result = calculate_discount(promo, Decimal("100.00"))
        assert result == Decimal("33.00")

    def test_percent_cap_below_calculated(self):
        """10% of 1000 = 100, cap=50 -> 50."""
        promo = _make_promo(
            discount_type=DiscountType.PERCENT,
            discount_value=Decimal("10"),
            max_discount_amount=Decimal("50"),
        )
        result = calculate_discount(promo, Decimal("1000.00"))
        assert result == Decimal("50.00")

    def test_percent_cap_above_calculated(self):
        """10% of 100 = 10, cap=50 -> 10 (cap not triggered)."""
        promo = _make_promo(
            discount_type=DiscountType.PERCENT,
            discount_value=Decimal("10"),
            max_discount_amount=Decimal("50"),
        )
        result = calculate_discount(promo, Decimal("100.00"))
        assert result == Decimal("10.00")


# ─── Code generation character set ──────────────────────────────


class TestCodeCharacters:
    """Test the character set used for promo code generation."""

    def test_no_ambiguous_characters(self):
        """O, 0, I, 1 should not be in the character set."""
        assert "O" not in _CODE_CHARS
        assert "0" not in _CODE_CHARS
        assert "I" not in _CODE_CHARS
        assert "1" not in _CODE_CHARS

    def test_has_letters_and_digits(self):
        """Should contain letters A-Z (minus O,I) and digits 2-9."""
        for c in "ABCDEFGHJKLMNPQRSTUVWXYZ":
            assert c in _CODE_CHARS
        for c in "23456789":
            assert c in _CODE_CHARS

    def test_length(self):
        """24 letters + 8 digits = 32 characters."""
        assert len(_CODE_CHARS) == 32


# ─── validate_promo_code ────────────────────────────────────────


class TestValidatePromoCode:
    """Tests for validate_promo_code function (async, requires mock db)."""

    @pytest.mark.asyncio
    async def test_invalid_code_raises(self):
        """Non-existent code should raise ValidationError."""
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        from app.core.exceptions import ValidationError

        with pytest.raises(ValidationError, match="Geçersiz kupon kodu"):
            await validate_promo_code("NONEXIST", Decimal("400"), mock_db)

    @pytest.mark.asyncio
    async def test_inactive_code_raises(self):
        """Inactive code should raise ValidationError."""
        promo = _make_promo(is_active=False)
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = promo
        mock_db.execute.return_value = mock_result

        from app.core.exceptions import ValidationError

        with pytest.raises(ValidationError, match="aktif değil"):
            await validate_promo_code("TEST100", Decimal("400"), mock_db)

    @pytest.mark.asyncio
    async def test_expired_code_raises(self):
        """Expired code should raise ValidationError."""
        promo = _make_promo(
            valid_until=datetime.now(UTC) - timedelta(days=1),
        )
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = promo
        mock_db.execute.return_value = mock_result

        from app.core.exceptions import ValidationError

        with pytest.raises(ValidationError, match="süresi dolmuş"):
            await validate_promo_code("TEST100", Decimal("400"), mock_db)

    @pytest.mark.asyncio
    async def test_not_yet_valid_raises(self):
        """Code not yet valid should raise ValidationError."""
        promo = _make_promo(
            valid_from=datetime.now(UTC) + timedelta(days=1),
        )
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = promo
        mock_db.execute.return_value = mock_result

        from app.core.exceptions import ValidationError

        with pytest.raises(ValidationError, match="henüz geçerli değil"):
            await validate_promo_code("TEST100", Decimal("400"), mock_db)

    @pytest.mark.asyncio
    async def test_usage_limit_reached_raises(self):
        """Code at usage limit should raise ValidationError."""
        promo = _make_promo(usage_limit=5, used_count=5)
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = promo
        mock_db.execute.return_value = mock_result

        from app.core.exceptions import ValidationError

        with pytest.raises(ValidationError, match="kullanım limiti dolmuş"):
            await validate_promo_code("TEST100", Decimal("400"), mock_db)

    @pytest.mark.asyncio
    async def test_min_order_amount_not_met_raises(self):
        """Subtotal below min_order_amount should raise."""
        promo = _make_promo(min_order_amount=Decimal("500"))
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = promo
        mock_db.execute.return_value = mock_result

        from app.core.exceptions import ValidationError

        with pytest.raises(ValidationError, match="Minimum sipariş tutarı"):
            await validate_promo_code("TEST100", Decimal("400"), mock_db)

    @pytest.mark.asyncio
    async def test_valid_code_returns_promo(self):
        """A fully valid code should return the PromoCode object."""
        promo = _make_promo(
            valid_from=datetime.now(UTC) - timedelta(days=1),
            valid_until=datetime.now(UTC) + timedelta(days=1),
            usage_limit=10,
            used_count=3,
        )
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = promo
        mock_db.execute.return_value = mock_result

        result = await validate_promo_code("TEST100", Decimal("400"), mock_db)
        assert result is promo

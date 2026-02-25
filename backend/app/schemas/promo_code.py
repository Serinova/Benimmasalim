"""Pydantic schemas for PromoCode CRUD and checkout integration."""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.promo_code import DiscountType

# ─── Admin CRUD ────────────────────────────────────────────────


class PromoCodeCreate(BaseModel):
    """Create a new promo code. If code is omitted, auto-generated."""

    code: str | None = Field(None, max_length=50, description="Omit to auto-generate")
    discount_type: DiscountType
    discount_value: Decimal = Field(gt=0)
    usage_limit: int = Field(ge=1, default=1)
    valid_from: datetime | None = None
    valid_until: datetime | None = None
    min_order_amount: Decimal | None = Field(None, ge=0)
    max_discount_amount: Decimal | None = Field(None, gt=0)
    notes: str | None = None

    @field_validator("code", mode="before")
    @classmethod
    def normalize_code(cls, v: str | None) -> str | None:
        if v is not None:
            return v.strip().upper()
        return v

    @field_validator("discount_value")
    @classmethod
    def validate_discount_value(cls, v: Decimal, info) -> Decimal:
        dt = info.data.get("discount_type")
        if dt == DiscountType.PERCENT and (v < 1 or v > 100):
            raise ValueError("Yüzde indirim 1-100 arasında olmalıdır")
        return v


class PromoCodeUpdate(BaseModel):
    """Partial update for promo code."""

    discount_type: DiscountType | None = None
    discount_value: Decimal | None = Field(None, gt=0)
    usage_limit: int | None = Field(None, ge=1)
    is_active: bool | None = None
    valid_from: datetime | None = None
    valid_until: datetime | None = None
    min_order_amount: Decimal | None = Field(None, ge=0)
    max_discount_amount: Decimal | None = Field(None, gt=0)
    notes: str | None = None


class PromoCodeResponse(BaseModel):
    """Full promo code response for admin endpoints."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    code: str
    discount_type: str
    discount_value: Decimal
    usage_limit: int
    used_count: int
    is_active: bool
    valid_from: datetime | None
    valid_until: datetime | None
    min_order_amount: Decimal | None
    max_discount_amount: Decimal | None
    notes: str | None
    created_by: UUID | None
    created_at: datetime
    updated_at: datetime


class PromoCodeListResponse(BaseModel):
    """Paginated list of promo codes."""

    items: list[PromoCodeResponse]
    total: int
    page: int
    page_size: int


class BulkGenerateRequest(BaseModel):
    """Bulk generate N promo codes with shared settings."""

    count: int = Field(ge=1, le=100)
    discount_type: DiscountType
    discount_value: Decimal = Field(gt=0)
    usage_limit: int = Field(ge=1, default=1)
    valid_from: datetime | None = None
    valid_until: datetime | None = None
    min_order_amount: Decimal | None = Field(None, ge=0)
    max_discount_amount: Decimal | None = Field(None, gt=0)
    prefix: str | None = Field(None, max_length=10, description="Optional code prefix")
    notes: str | None = None

    @field_validator("prefix", mode="before")
    @classmethod
    def normalize_prefix(cls, v: str | None) -> str | None:
        if v is not None:
            return v.strip().upper()
        return v

    @field_validator("discount_value")
    @classmethod
    def validate_discount_value(cls, v: Decimal, info) -> Decimal:
        dt = info.data.get("discount_type")
        if dt == DiscountType.PERCENT and (v < 1 or v > 100):
            raise ValueError("Yüzde indirim 1-100 arasında olmalıdır")
        return v


class BulkGenerateResponse(BaseModel):
    """Response for bulk code generation."""

    codes: list[PromoCodeResponse]
    count: int


# ─── Checkout / Apply ──────────────────────────────────────────


class ApplyPromoRequest(BaseModel):
    """Apply a promo code to an order (preview only, no consumption)."""

    code: str = Field(min_length=1, max_length=50)
    order_id: UUID

    @field_validator("code", mode="before")
    @classmethod
    def normalize_code(cls, v: str) -> str:
        return v.strip().upper()


class PromoSummary(BaseModel):
    """Summary of applied promo code for frontend display."""

    code: str
    discount_type: str
    discount_value: Decimal
    max_discount_amount: Decimal | None


class ApplyPromoResponse(BaseModel):
    """Response for promo code apply preview."""

    valid: bool
    reason: str | None = None
    discount_amount: Decimal | None = None
    subtotal_amount: Decimal | None = None
    final_amount: Decimal | None = None
    promo_summary: PromoSummary | None = None

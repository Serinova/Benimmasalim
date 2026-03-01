"""Pydantic schemas for payment endpoints."""

from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class BillingInfo(BaseModel):
    billing_type: str = "individual"  # "individual" | "corporate"
    billing_tc_no: str | None = None  # TCKN — bireysel fatura için
    billing_full_name: str | None = None
    billing_email: str | None = None
    billing_phone: str | None = None
    billing_company_name: str | None = None
    billing_tax_id: str | None = None
    billing_tax_office: str | None = None
    billing_address: dict | None = None
    use_shipping_address: bool = True

    @field_validator("billing_tc_no", mode="before")
    @classmethod
    def validate_tc_no(cls, v: str | None) -> str | None:
        if v is None or v == "":
            return None
        v_str = str(v).strip()
        if not v_str.isdigit() or len(v_str) != 11:
            raise ValueError("TC kimlik numarası 11 haneli rakamdan oluşmalıdır")
        return v_str


class CheckoutRequest(BaseModel):
    """Checkout request with shipping address and billing info."""

    order_id: UUID
    shipping_address: dict
    has_audio_book: bool = False
    audio_type: str | None = None  # "system" or "cloned"
    voice_sample_url: str | None = None  # For cloned voice
    promo_code: str | None = None  # Optional promo code
    billing: BillingInfo | None = None


class CheckoutResponse(BaseModel):
    """Checkout response with payment URL."""

    payment_url: str | None  # None when free order (no payment needed)
    payment_id: str | None
    total_amount: float
    breakdown: dict
    is_free_order: bool = False  # True when 100% discount, no payment needed
    order_status: str | None = None  # Current order status after checkout


class PaymentStatusResponse(BaseModel):
    """Payment status response."""

    order_id: str
    status: str
    payment_status: str | None


class PublicApplyPromoRequest(BaseModel):
    """Public promo code validation — no auth required, uses subtotal directly."""

    code: str = Field(min_length=1, max_length=50)
    subtotal: Decimal = Field(gt=0)

    @field_validator("code", mode="before")
    @classmethod
    def normalize_code(cls, v: str) -> str:
        return v.strip().upper()


class VerifyIyzicoRequest(BaseModel):
    """Request to verify Iyzico checkout result."""

    token: str = Field(..., min_length=1, max_length=500)
    order_id: str = Field(..., min_length=36, max_length=36)

    @field_validator("order_id")
    @classmethod
    def validate_uuid(cls, v: str) -> str:
        try:
            UUID(v)
        except ValueError as exc:
            raise ValueError("Geçersiz sipariş ID formatı") from exc
        return v

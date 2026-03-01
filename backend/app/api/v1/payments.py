"""Payment endpoints - Iyzico integration + promo code support."""

from decimal import Decimal
from uuid import UUID

import structlog
from fastapi import APIRouter, Request
from sqlalchemy import select

from app.api.v1.deps import CurrentUser, DbSession
from app.core.exceptions import ForbiddenError, NotFoundError, ValidationError
from app.models.order import Order, OrderStatus
from app.schemas.payments import (
    BillingInfo,
    CheckoutRequest,
    CheckoutResponse,
    PaymentStatusResponse,
    PublicApplyPromoRequest,
    VerifyIyzicoRequest,
)
from app.schemas.promo_code import ApplyPromoRequest, ApplyPromoResponse, PromoSummary
from app.services.checkout_service import (
    calculate_subtotal,
    process_checkout,
    process_verify_payment,
)
from app.services.promo_code_service import (
    calculate_discount,
    rollback_promo_code,
    validate_promo_code,
)

logger = structlog.get_logger()
router = APIRouter()

_ORDER_RESOURCE = "Sipariş"

# Re-exported for backward compatibility — callers should import from promo_code_service
# directly going forward.
__all__ = ["router", "rollback_promo_code"]


def _verify_order_ownership_payment(order: "Order", current_user: "object") -> None:
    """Object-level auth for payment endpoints (always require auth)."""
    if order.user_id is None or order.user_id != current_user.id:
        raise ForbiddenError("Bu siparişe erişim yetkiniz yok")


@router.get("/config-status")
async def payment_config_status() -> dict:
    """
    Ödeme ortamını kontrol et (FRONTEND_URL, Iyzico anahtarları).
    Anahtar değerleri döndürülmez; sadece yapılandırılmış mı bilgisi.
    """
    from app.config import get_settings

    s = get_settings()
    frontend_ok = bool(
        s.frontend_url
        and "localhost" not in s.frontend_url
        and "127.0.0.1" not in s.frontend_url
    )
    iyzico_ok = bool(s.iyzico_api_key and s.iyzico_secret_key)
    return {
        "frontend_url_configured": frontend_ok,
        "frontend_url_preview": (
            s.frontend_url[:50] + "..."
            if len(s.frontend_url or "") > 50
            else (s.frontend_url or "")
        ),
        "iyzico_configured": iyzico_ok,
        "iyzico_base_url": s.iyzico_base_url or "",
    }


@router.post("/validate-promo", response_model=ApplyPromoResponse)
async def validate_promo_public(
    request: PublicApplyPromoRequest,
    db: DbSession,
) -> ApplyPromoResponse:
    """
    Public promo code validation — no auth or order required.
    Just validates the code against the given subtotal.
    """
    try:
        promo = await validate_promo_code(request.code, request.subtotal, db)
    except ValidationError as e:
        return ApplyPromoResponse(
            valid=False,
            reason=str(e.detail),
        )

    discount_amount = calculate_discount(promo, request.subtotal)
    final_amount = max(request.subtotal - discount_amount, Decimal("0.00"))

    return ApplyPromoResponse(
        valid=True,
        discount_amount=discount_amount,
        subtotal_amount=request.subtotal,
        final_amount=final_amount,
        promo_summary=PromoSummary(
            code=promo.code,
            discount_type=promo.discount_type,
            discount_value=promo.discount_value,
            max_discount_amount=promo.max_discount_amount,
        ),
    )


@router.post("/apply-promo", response_model=ApplyPromoResponse)
async def apply_promo(
    request: ApplyPromoRequest,
    db: DbSession,
    current_user: CurrentUser,
) -> ApplyPromoResponse:
    """
    Preview promo code discount without consuming it (requires auth + order).
    """
    result = await db.execute(select(Order).where(Order.id == request.order_id))
    order = result.scalar_one_or_none()
    if not order:
        raise NotFoundError(_ORDER_RESOURCE, request.order_id)

    _verify_order_ownership_payment(order, current_user)

    subtotal, _ = await calculate_subtotal(order, db, order.has_audio_book, order.audio_type)

    try:
        promo = await validate_promo_code(request.code, subtotal, db)
    except ValidationError as e:
        return ApplyPromoResponse(
            valid=False,
            reason=str(e.detail),
        )

    discount_amount = calculate_discount(promo, subtotal)
    final_amount = max(subtotal - discount_amount, Decimal("0.00"))

    return ApplyPromoResponse(
        valid=True,
        discount_amount=discount_amount,
        subtotal_amount=subtotal,
        final_amount=final_amount,
        promo_summary=PromoSummary(
            code=promo.code,
            discount_type=promo.discount_type,
            discount_value=promo.discount_value,
            max_discount_amount=promo.max_discount_amount,
        ),
    )


@router.post("/checkout", response_model=CheckoutResponse)
async def create_checkout(
    request: CheckoutRequest,
    db: DbSession,
    current_user: CurrentUser,
    raw_request: Request,
) -> CheckoutResponse:
    """
    Create payment session with Iyzico.

    If promo code results in 0 TL total, skips payment entirely
    and transitions directly to PAID.
    """
    return await process_checkout(request, current_user, db, raw_request)


@router.post("/verify-iyzico")
async def verify_iyzico_payment(
    request: VerifyIyzicoRequest,
    db: DbSession,
) -> dict:
    """Verify Iyzico checkout form result after user returns from payment page.

    Called by frontend callback route. Uses SELECT FOR UPDATE to
    prevent race conditions with the parallel webhook handler.
    """
    return await process_verify_payment(request, db)


@router.get("/status/{order_id}", response_model=PaymentStatusResponse)
async def get_payment_status(
    order_id: UUID,
    db: DbSession,
    current_user: CurrentUser,
) -> PaymentStatusResponse:
    """Get payment status for an order. Requires authentication + ownership check."""
    result = await db.execute(select(Order).where(Order.id == order_id))
    order = result.scalar_one_or_none()

    if not order:
        raise NotFoundError(_ORDER_RESOURCE, order_id)

    _verify_order_ownership_payment(order, current_user)

    return PaymentStatusResponse(
        order_id=str(order.id),
        status=order.status.value,
        payment_status=order.payment_status,
    )

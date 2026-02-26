"""Payment endpoints - Iyzico integration + promo code support."""

from decimal import Decimal
from uuid import UUID

import structlog
from fastapi import APIRouter, Request
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import select, update

from app.api.v1.deps import CurrentUser, DbSession
from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.models.audit_log import AuditLog
from app.models.order import Order, OrderStatus
from app.models.product import Product
from app.models.promo_code import PromoCode
from app.schemas.promo_code import ApplyPromoRequest, ApplyPromoResponse, PromoSummary
from app.services.promo_code_service import (
    calculate_discount,
    consume_promo_code,
    validate_promo_code,
)

logger = structlog.get_logger()
router = APIRouter()

_ORDER_RESOURCE = "Sipariş"


class CheckoutRequest(BaseModel):
    """Checkout request with shipping address."""

    order_id: UUID
    shipping_address: dict
    has_audio_book: bool = False
    audio_type: str | None = None  # "system" or "cloned"
    voice_sample_url: str | None = None  # For cloned voice
    promo_code: str | None = None  # Optional promo code


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


async def _calculate_subtotal(
    order: Order, db, has_audio_book: bool, audio_type: str | None
) -> tuple[Decimal, dict]:
    """Calculate subtotal from product price + audio addon.
    
    Audio addon pricing is now fetched from products table (product_type='audio_addon')
    instead of being hardcoded.
    """
    result = await db.execute(select(Product).where(Product.id == order.product_id))
    product = result.scalar_one_or_none()

    base_price = product.calculate_price(order.total_pages) if product else Decimal("450.00")

    audio_price = Decimal("0.00")
    if has_audio_book and audio_type:
        # Fetch audio addon product from database
        audio_slug = "audio-addon-cloned-voice" if audio_type == "cloned" else "audio-addon-system-voice"
        audio_result = await db.execute(
            select(Product).where(
                Product.product_type == "audio_addon",
                Product.slug == audio_slug,
                Product.is_active == True
            )
        )
        audio_product = audio_result.scalar_one_or_none()
        
        if audio_product:
            audio_price = audio_product.base_price
        else:
            # Fallback to hardcoded prices if product not found (backward compatibility)
            logger.warning(
                "audio_addon_product_not_found",
                audio_type=audio_type,
                slug=audio_slug,
                using_fallback=True
            )
            audio_price = Decimal("300.00") if audio_type == "cloned" else Decimal("150.00")

    subtotal = base_price + audio_price
    breakdown = {
        "base_price": float(base_price),
        "audio_book": float(audio_price),
    }
    return subtotal, breakdown


async def rollback_promo_code(order: Order, db) -> None:
    """
    Rollback a consumed promo code: decrement used_count by 1.

    Called when payment fails or order is cancelled from PAYMENT_PENDING.
    Only rolls back if the order has a promo_code_id attached.
    """
    if not order.promo_code_id:
        return

    result = await db.execute(
        update(PromoCode)
        .where(
            PromoCode.id == order.promo_code_id,
            PromoCode.used_count > 0,
        )
        .values(used_count=PromoCode.used_count - 1)
    )

    if result.rowcount > 0:
        logger.info(
            "promo_code_rolled_back",
            promo_code_id=str(order.promo_code_id),
            order_id=str(order.id),
        )
        db.add(AuditLog(
            action="PROMO_CODE_ROLLED_BACK",
            order_id=order.id,
            details={
                "promo_code_id": str(order.promo_code_id),
                "promo_code_text": order.promo_code_text,
                "reason": "payment_failed_or_cancelled",
            },
        ))


async def _rollback_promo_after_failure(promo, order: Order, user_id, db) -> None:
    """Rollback promo code when Iyzico checkout creation fails."""
    try:
        await rollback_promo_code(order, db)
        logger.info(
            "PROMO_ROLLBACK_ON_IYZICO_FAILURE",
            order_id=str(order.id),
            promo_code=promo.code,
            user_id=str(user_id),
        )
    except Exception as rb_exc:
        logger.critical(
            "PROMO_ROLLBACK_FAILED",
            order_id=str(order.id),
            promo_code=promo.code,
            error=str(rb_exc),
        )


class PublicApplyPromoRequest(BaseModel):
    """Public promo code validation — no auth required, uses subtotal directly."""

    code: str = Field(min_length=1, max_length=50)
    subtotal: Decimal = Field(gt=0)

    @field_validator("code", mode="before")
    @classmethod
    def normalize_code(cls, v: str) -> str:
        return v.strip().upper()


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

    if order.user_id and order.user_id != current_user.id:
        raise ValidationError("Bu sipariş size ait değil")

    subtotal, _ = await _calculate_subtotal(
        order, db, order.has_audio_book, order.audio_type
    )

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


async def _create_iyzico_checkout(
    order: Order,
    final_amount: Decimal,
    shipping: dict,
    buyer_email: str,
    buyer_name: str,
    buyer_phone: str,
    raw_request: Request,
) -> tuple[str, str]:
    """
    Create Iyzico checkout form and return (payment_page_url, token).

    Uses iyzipay SDK for PCI-compliant payment page (hosted by iyzico).
    Card details are NEVER sent to our servers.
    """
    import iyzipay

    from app.config import settings

    if not settings.iyzico_api_key or not settings.iyzico_secret_key:
        raise ValidationError(
            "Ödeme sistemi henüz yapılandırılmamış. Lütfen daha sonra tekrar deneyin."
        )

    options = {
        "api_key": settings.iyzico_api_key,
        "secret_key": settings.iyzico_secret_key,
        "base_url": settings.iyzico_base_url,
    }

    # Split buyer name
    name_parts = buyer_name.strip().split(" ", 1)
    first_name = name_parts[0] if name_parts else "Misafir"
    last_name = name_parts[1] if len(name_parts) > 1 else "."

    buyer = {
        "id": str(order.user_id or order.id),
        "name": first_name,
        "surname": last_name,
        "email": buyer_email or "misafir@benimmasalim.com",
        "identityNumber": "11111111111",  # TC kimlik — iyzico sandbox accepts dummy
        "registrationAddress": shipping.get("address", "Adres belirtilmedi"),
        "city": shipping.get("city", "Istanbul"),
        "country": "Turkey",
        "ip": (
            raw_request.headers.get("x-forwarded-for", "").split(",")[0].strip()
            or (raw_request.client.host if raw_request.client else "127.0.0.1")
        ),
    }

    if buyer_phone:
        buyer["gsmNumber"] = buyer_phone

    shipping_address = {
        "contactName": buyer_name,
        "city": shipping.get("city", "Istanbul"),
        "country": "Turkey",
        "address": shipping.get("address", "Adres belirtilmedi"),
    }

    billing_address = shipping_address.copy()

    basket_items = [
        {
            "id": str(order.id)[:16],
            "name": "Kişiselleştirilmiş Hikaye Kitabı",
            "category1": "Kitap",
            "category2": "Çocuk Kitabı",
            "itemType": "PHYSICAL",
            "price": str(final_amount),
        }
    ]

    callback_url = f"{settings.frontend_url}/api/payment/callback?orderId={order.id}"

    iyzico_request = {
        "locale": "tr",
        "conversationId": str(order.id),
        "price": str(final_amount),
        "paidPrice": str(final_amount),
        "currency": "TRY",
        "basketId": str(order.id)[:16],
        "paymentGroup": "PRODUCT",
        "callbackUrl": callback_url,
        "enabledInstallments": [1, 2, 3, 6],
        "buyer": buyer,
        "shippingAddress": shipping_address,
        "billingAddress": billing_address,
        "basketItems": basket_items,
    }

    try:
        checkout_form = iyzipay.CheckoutFormInitialize().create(iyzico_request, options)
        result = checkout_form.read().decode("utf-8")

        import json
        result_dict = json.loads(result)

        if result_dict.get("status") != "success":
            error_msg = result_dict.get("errorMessage", "Bilinmeyen hata")
            logger.error(
                "IYZICO_CHECKOUT_FORM_FAILED",
                order_id=str(order.id),
                error=error_msg,
                error_code=result_dict.get("errorCode"),
            )
            raise ValidationError(f"Ödeme sayfası oluşturulamadı: {error_msg}")

        payment_page_url = result_dict.get("paymentPageUrl", "")
        token = result_dict.get("token", "")

        logger.info(
            "IYZICO_CHECKOUT_CREATED",
            order_id=str(order.id),
            token=token[:20] if token else "N/A",
        )

        return payment_page_url, token

    except ValidationError:
        raise
    except Exception as exc:
        logger.error("IYZICO_SDK_ERROR", order_id=str(order.id), error=str(exc))
        raise ValidationError("Ödeme sistemi geçici olarak kullanılamıyor.") from exc


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
    from app.services.order_state_machine import get_order_for_update

    order = await get_order_for_update(request.order_id, db)
    if not order:
        raise NotFoundError(_ORDER_RESOURCE, request.order_id)

    # Idempotency: if already PAYMENT_PENDING with a payment URL, return it
    if order.status == OrderStatus.PAYMENT_PENDING and order.payment_id:
        return CheckoutResponse(
            payment_url=None,
            payment_id=order.payment_id,
            total_amount=float(order.payment_amount or 0),
            breakdown={"note": "Mevcut ödeme oturumu devam ediyor"},
            is_free_order=False,
            order_status=OrderStatus.PAYMENT_PENDING.value,
        )

    if order.status != OrderStatus.COVER_APPROVED:
        raise ValidationError("Ödeme sadece COVER_APPROVED durumunda yapılabilir")

    if order.user_id and order.user_id != current_user.id:
        raise ValidationError("Bu sipariş size ait değil")

    # Calculate subtotal
    subtotal, breakdown = await _calculate_subtotal(
        order, db, request.has_audio_book, request.audio_type
    )

    # Handle promo code
    discount_amount = Decimal("0.00")
    promo = None

    if request.promo_code:
        promo_code_str = request.promo_code.strip().upper()
        promo = await validate_promo_code(promo_code_str, subtotal, db)
        discount_amount = calculate_discount(promo, subtotal)

        # Atomic consume -- concurrency-safe
        consumed = await consume_promo_code(promo.id, db)
        if not consumed:
            raise ConflictError(
                "Kupon kodunun kullanım limiti dolmuş, lütfen başka bir kod deneyin"
            )

        # Write promo snapshot to order
        order.promo_code_id = promo.id
        order.promo_code_text = promo.code
        order.promo_discount_type = promo.discount_type
        order.promo_discount_value = promo.discount_value
        order.discount_applied_amount = discount_amount

        # Audit log for consumption
        db.add(AuditLog(
            action="PROMO_CODE_CONSUMED",
            user_id=current_user.id,
            order_id=order.id,
            details={
                "code": promo.code,
                "discount_type": promo.discount_type,
                "discount_value": str(promo.discount_value),
                "discount_applied": str(discount_amount),
            },
        ))

    final_amount = max(subtotal - discount_amount, Decimal("0.00"))

    # Write price fields to order
    order.subtotal_amount = subtotal
    order.final_amount = final_amount
    order.shipping_address = request.shipping_address
    order.has_audio_book = request.has_audio_book
    order.audio_type = request.audio_type
    order.payment_amount = final_amount

    # Build breakdown
    breakdown["discount"] = float(discount_amount)
    breakdown["subtotal"] = float(subtotal)
    breakdown["total"] = float(final_amount)
    if promo:
        breakdown["promo_code"] = promo.code

    from app.services.order_state_machine import transition_order

    # --- FREE ORDER: %100 indirim, odeme gereksiz ---
    if final_amount == Decimal("0.00"):
        order.payment_status = "FREE_ORDER"
        order.payment_id = f"free-{order.id}"
        order.payment_provider = "promo_code"

        # Skip PAYMENT_PENDING, go directly: COVER_APPROVED -> PAYMENT_PENDING -> PAID
        await transition_order(order, OrderStatus.PAYMENT_PENDING, db, auto_commit=False)
        await transition_order(order, OrderStatus.PAID, db, auto_commit=False)
        await db.commit()

        logger.info(
            "free_order_completed",
            order_id=str(order.id),
            promo_code=promo.code if promo else None,
        )

        # Trigger generation task for free orders
        try:
            if order.is_coloring_book:
                from app.tasks.generate_coloring_book import generate_coloring_book
                import asyncio
                asyncio.create_task(generate_coloring_book(order.id, db))
            else:
                from app.workers.enqueue import enqueue_full_book_generation
                await enqueue_full_book_generation(str(order.id))
        except Exception as exc:
            logger.critical("FREE_ORDER_ENQUEUE_FAILED", order_id=str(order.id), error=str(exc))

        return CheckoutResponse(
            payment_url=None,
            payment_id=None,
            total_amount=0.0,
            breakdown=breakdown,
            is_free_order=True,
            order_status=OrderStatus.PAID.value,
        )

    # --- PAID ORDER: normal Iyzico flow ---
    await transition_order(order, OrderStatus.PAYMENT_PENDING, db, auto_commit=False)
    await db.commit()

    try:
        payment_page_url, iyzico_token = await _create_iyzico_checkout(
            order=order,
            final_amount=final_amount,
            shipping=request.shipping_address,
            buyer_email=request.shipping_address.get("email", ""),
            buyer_name=request.shipping_address.get("fullName", ""),
            buyer_phone=request.shipping_address.get("phone", ""),
            raw_request=raw_request,
        )
    except Exception as iyzico_exc:
        if promo:
            await _rollback_promo_after_failure(promo, order, current_user.id, db)
        await transition_order(order, OrderStatus.COVER_APPROVED, db, auto_commit=False)
        await db.commit()
        logger.error(
            "CHECKOUT_IYZICO_FAILED_ROLLBACK",
            order_id=str(order.id),
            error=str(iyzico_exc),
        )
        raise ValidationError("Ödeme sistemi geçici olarak kullanılamıyor. Lütfen tekrar deneyin.") from iyzico_exc

    order.payment_id = iyzico_token
    order.payment_provider = "iyzico"
    await db.commit()

    return CheckoutResponse(
        payment_url=payment_page_url,
        payment_id=iyzico_token,
        total_amount=float(final_amount),
        breakdown=breakdown,
        is_free_order=False,
        order_status=OrderStatus.PAYMENT_PENDING.value,
    )


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


@router.post("/verify-iyzico")
async def verify_iyzico_payment(
    request: VerifyIyzicoRequest,
    db: DbSession,
) -> dict:
    """Verify Iyzico checkout form result after user returns from payment page.

    Called by frontend callback route.  Uses ``SELECT … FOR UPDATE`` to
    prevent race conditions with the parallel webhook handler.
    """
    import json

    import iyzipay

    from app.config import settings
    from app.services.order_state_machine import get_order_for_update, transition_order

    if not settings.iyzico_api_key or not settings.iyzico_secret_key:
        raise ValidationError("Ödeme sistemi yapılandırılmamış")

    options = {
        "api_key": settings.iyzico_api_key,
        "secret_key": settings.iyzico_secret_key,
        "base_url": settings.iyzico_base_url,
    }

    # 1) Verify with Iyzico server-side (before locking the row)
    try:
        result = iyzipay.CheckoutForm().retrieve(
            {"locale": "tr", "conversationId": request.order_id, "token": request.token},
            options,
        )
        result_dict = json.loads(result.read().decode("utf-8"))
    except Exception as exc:
        logger.error("IYZICO_VERIFY_ERROR", error=str(exc))
        raise ValidationError("Ödeme doğrulanamadı") from exc

    iyzico_status = result_dict.get("paymentStatus")
    payment_id = result_dict.get("paymentId")
    paid_price = result_dict.get("paidPrice")

    # 2) Lock the order row — prevents webhook from processing in parallel
    order = await get_order_for_update(UUID(request.order_id), db)
    if not order:
        raise NotFoundError(_ORDER_RESOURCE, request.order_id)

    # Idempotency: already processed (webhook may have beaten us)
    if order.status != OrderStatus.PAYMENT_PENDING:
        return {"status": "already_processed", "order_status": order.status.value}

    if iyzico_status == "SUCCESS":
        if paid_price is not None and order.payment_amount:
            received = Decimal(str(paid_price))
            expected = order.payment_amount
            if abs(received - expected) > Decimal("0.01"):
                logger.critical(
                    "IYZICO_VERIFY_AMOUNT_MISMATCH",
                    order_id=str(order.id),
                    expected=str(expected),
                    received=str(received),
                )
                order.payment_status = "AMOUNT_MISMATCH"
                await rollback_promo_code(order, db)
                await transition_order(order, OrderStatus.COVER_APPROVED, db, auto_commit=False)
                await db.commit()
                return {"status": "amount_mismatch", "error": "Ödeme tutarı uyuşmuyor"}

        order.payment_id = payment_id
        order.payment_status = "SUCCESS"

        await transition_order(order, OrderStatus.PAID, db, auto_commit=False)
        await db.commit()

        # Enqueue AFTER commit so that the worker sees PAID status
        try:
            # Check if this is a coloring book order
            if order.is_coloring_book:
                # Trigger coloring book generation task
                from app.tasks.generate_coloring_book import generate_coloring_book
                import asyncio
                asyncio.create_task(generate_coloring_book(order.id, db))
                logger.info(
                    "coloring_book_generation_triggered",
                    order_id=str(order.id),
                    payment_id=payment_id,
                )
            else:
                # Regular story book generation
                from app.workers.enqueue import enqueue_full_book_generation
                await enqueue_full_book_generation(str(order.id))
        except Exception as exc:
            logger.critical("IYZICO_VERIFY_ENQUEUE_FAILED", order_id=str(order.id), error=str(exc))

        return {"status": "success", "order_status": OrderStatus.PAID.value}

    # Payment failed or cancelled
    order.payment_status = "FAILED"
    await rollback_promo_code(order, db)
    order.promo_code_id = None
    order.promo_code_text = None
    order.promo_discount_type = None
    order.promo_discount_value = None
    order.discount_applied_amount = None
    await db.commit()

    return {
        "status": "failed",
        "error": result_dict.get("errorMessage", "Ödeme başarısız"),
    }


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

    # IDOR check: verify ownership
    if order.user_id and order.user_id != current_user.id:
        raise NotFoundError(_ORDER_RESOURCE, order_id)

    return PaymentStatusResponse(
        order_id=str(order.id),
        status=order.status.value,
        payment_status=order.payment_status,
    )

"""Checkout business logic: subtotal calculation, Iyzico integration, payment processing."""

from decimal import Decimal
from uuid import UUID

import structlog
from fastapi import Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.models.audit_log import AuditLog
from app.models.order import Order, OrderStatus
from app.models.product import Product
from app.schemas.payments import CheckoutRequest, CheckoutResponse, VerifyIyzicoRequest
from app.services.promo_code_service import (
    _rollback_promo_after_failure,
    calculate_discount,
    consume_promo_code,
    rollback_promo_code,
    validate_promo_code,
)
from app.services.trial_payment_service import get_iyzico_options

logger = structlog.get_logger()

_ORDER_RESOURCE = "Sipariş"


async def calculate_subtotal(
    order: Order,
    db: AsyncSession,
    has_audio_book: bool,
    audio_type: str | None,
) -> tuple[Decimal, dict]:
    """Calculate subtotal from product price + audio addon.

    Audio addon pricing is fetched from products table (product_type='audio_addon').
    Falls back to hardcoded prices if product not found.
    """
    result = await db.execute(select(Product).where(Product.id == order.product_id))
    product = result.scalar_one_or_none()

    base_price = product.calculate_price(order.total_pages) if product else Decimal("450.00")

    audio_price = Decimal("0.00")
    if has_audio_book and audio_type:
        audio_slug = "audio-addon-cloned-voice" if audio_type == "cloned" else "audio-addon-system-voice"
        audio_result = await db.execute(
            select(Product).where(
                Product.product_type == "audio_addon",
                Product.slug == audio_slug,
                Product.is_active == True,
            )
        )
        audio_product = audio_result.scalar_one_or_none()

        if audio_product:
            audio_price = audio_product.base_price
        else:
            logger.warning(
                "audio_addon_product_not_found",
                audio_type=audio_type,
                slug=audio_slug,
                using_fallback=True,
            )
            audio_price = Decimal("300.00") if audio_type == "cloned" else Decimal("150.00")

    subtotal = base_price + audio_price
    breakdown = {
        "base_price": float(base_price),
        "audio_book": float(audio_price),
    }
    return subtotal, breakdown


async def create_iyzico_checkout(
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

    try:
        options = get_iyzico_options()
    except ValueError as exc:
        raise ValidationError(str(exc)) from exc

    name_parts = buyer_name.strip().split(" ", 1)
    first_name = name_parts[0] if name_parts else "Misafir"
    last_name = name_parts[1] if len(name_parts) > 1 else "."

    buyer = {
        "id": str(order.user_id or order.id),
        "name": first_name,
        "surname": last_name,
        "email": buyer_email or "misafir@benimmasalim.com",
        "identityNumber": order.billing_tc_no or "11111111111",
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

    if order.billing_address:
        billing_address = {
            "contactName": order.billing_full_name or buyer_name,
            "city": order.billing_address.get("city", shipping.get("city", "Istanbul")),
            "country": "Turkey",
            "address": order.billing_address.get(
                "address", shipping.get("address", "Adres belirtilmedi")
            ),
        }
    else:
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


async def process_checkout(
    request: CheckoutRequest,
    current_user: "object",
    db: AsyncSession,
    raw_request: Request,
) -> CheckoutResponse:
    """
    Full checkout pipeline: validate → price → promo → Iyzico or free-order fast path.

    Raises NotFoundError, ValidationError, ConflictError on failure.
    """
    from app.services.order_state_machine import get_order_for_update, transition_order

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

    if order.user_id is None or order.user_id != current_user.id:
        from app.core.exceptions import ForbiddenError
        raise ForbiddenError("Bu siparişe erişim yetkiniz yok")

    subtotal, breakdown = await calculate_subtotal(
        order, db, request.has_audio_book, request.audio_type
    )

    discount_amount = Decimal("0.00")
    promo = None

    if request.promo_code:
        promo_code_str = request.promo_code.strip().upper()
        promo = await validate_promo_code(promo_code_str, subtotal, db)
        discount_amount = calculate_discount(promo, subtotal)

        consumed = await consume_promo_code(promo.id, db)
        if not consumed:
            raise ConflictError(
                "Kupon kodunun kullanım limiti dolmuş, lütfen başka bir kod deneyin"
            )

        order.promo_code_id = promo.id
        order.promo_code_text = promo.code
        order.promo_discount_type = promo.discount_type
        order.promo_discount_value = promo.discount_value
        order.discount_applied_amount = discount_amount

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

    order.subtotal_amount = subtotal
    order.final_amount = final_amount
    order.shipping_address = request.shipping_address
    order.has_audio_book = request.has_audio_book
    order.audio_type = request.audio_type
    order.payment_amount = final_amount

    if request.billing:
        b = request.billing
        order.billing_type = b.billing_type
        order.billing_tc_no = b.billing_tc_no if b.billing_type == "individual" else None
        order.billing_full_name = b.billing_full_name
        order.billing_email = b.billing_email
        order.billing_phone = b.billing_phone
        order.billing_company_name = b.billing_company_name if b.billing_type == "corporate" else None
        order.billing_tax_id = b.billing_tax_id if b.billing_type == "corporate" else None
        order.billing_tax_office = b.billing_tax_office if b.billing_type == "corporate" else None
        if b.use_shipping_address:
            order.billing_address = request.shipping_address
        elif b.billing_address:
            order.billing_address = b.billing_address

    breakdown["discount"] = float(discount_amount)
    breakdown["subtotal"] = float(subtotal)
    breakdown["total"] = float(final_amount)
    if promo:
        breakdown["promo_code"] = promo.code

    # --- FREE ORDER: 100% discount, skip payment ---
    if final_amount == Decimal("0.00"):
        order.payment_status = "FREE_ORDER"
        order.payment_id = f"free-{order.id}"
        order.payment_provider = "promo_code"

        await transition_order(order, OrderStatus.PAYMENT_PENDING, db, auto_commit=False)
        await transition_order(order, OrderStatus.PAID, db, auto_commit=False)
        await db.commit()

        logger.info(
            "free_order_completed",
            order_id=str(order.id),
            promo_code=promo.code if promo else None,
        )

        try:
            import asyncio as _aio

            from app.services.invoice_pdf_service import generate_invoice_pdf

            _aio.create_task(generate_invoice_pdf(order.id, db))
        except Exception as _inv_err:
            logger.error(
                "FREE_ORDER_INVOICE_PDF_FAILED",
                order_id=str(order.id),
                error=str(_inv_err),
            )

        try:
            if order.is_coloring_book:
                import asyncio

                from app.tasks.generate_coloring_book import generate_coloring_book

                asyncio.create_task(generate_coloring_book(order.id, db))
            else:
                from app.workers.enqueue import enqueue_full_book_generation

                await enqueue_full_book_generation(str(order.id))
        except Exception as exc:
            logger.critical(
                "FREE_ORDER_ENQUEUE_FAILED", order_id=str(order.id), error=str(exc)
            )

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
        payment_page_url, iyzico_token = await create_iyzico_checkout(
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
        raise ValidationError(
            "Ödeme sistemi geçici olarak kullanılamıyor. Lütfen tekrar deneyin."
        ) from iyzico_exc

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


async def process_verify_payment(
    request: VerifyIyzicoRequest,
    db: AsyncSession,
) -> dict:
    """
    Verify Iyzico checkout form result after user returns from payment page.

    Uses SELECT FOR UPDATE to prevent race conditions with the parallel webhook handler.
    """
    import json

    import iyzipay

    from app.services.order_state_machine import get_order_for_update, transition_order

    try:
        options = get_iyzico_options()
    except ValueError as exc:
        raise ValidationError(str(exc)) from exc

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

    order = await get_order_for_update(UUID(request.order_id), db)
    if not order:
        raise NotFoundError(_ORDER_RESOURCE, request.order_id)

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

        try:
            if order.is_coloring_book:
                import asyncio

                from app.tasks.generate_coloring_book import generate_coloring_book

                asyncio.create_task(generate_coloring_book(order.id, db))
                logger.info(
                    "coloring_book_generation_triggered",
                    order_id=str(order.id),
                    payment_id=payment_id,
                )
            else:
                from app.workers.enqueue import enqueue_full_book_generation

                await enqueue_full_book_generation(str(order.id))
        except Exception as exc:
            logger.critical(
                "IYZICO_VERIFY_ENQUEUE_FAILED", order_id=str(order.id), error=str(exc)
            )

        return {"status": "success", "order_status": OrderStatus.PAID.value}

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

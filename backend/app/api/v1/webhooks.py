"""Webhook endpoints for external services."""

import hashlib
import hmac
from decimal import Decimal
from typing import Any

import structlog
from fastapi import APIRouter, Header, Request, status
from pydantic import BaseModel

from app.api.v1.deps import DbSession
from app.config import settings
from app.core.audit import record_audit
from app.core.exceptions import ForbiddenError, ValidationError
from app.models.order import OrderStatus

logger = structlog.get_logger()

router = APIRouter()


class IyzicoWebhookPayload(BaseModel):
    """Iyzico payment webhook payload."""

    status: str
    payment_id: str
    order_id: str  # conversation_id we sent
    amount: float
    transaction_id: str
    merchant_order_id: str | None = None


def _verify_webhook_signature(
    x_signature: str | None,
    raw_body: bytes,
    context: str,
) -> None:
    """Verify webhook signature using HMAC-SHA256(secret, body).

    Fail closed if secret is not configured or signature doesn't match.
    """
    _webhook_secret = getattr(settings, "webhook_secret", "")
    if not _webhook_secret:
        logger.error("WEBHOOK_SECRET_NOT_CONFIGURED", context=context)
        raise ForbiddenError("Webhook doğrulama yapılandırılmamış")
    if not x_signature:
        logger.warning("Webhook signature missing", context=context)
        raise ForbiddenError("Geçersiz webhook imzası")

    # Compute HMAC-SHA256 over the raw request body
    expected = hmac.new(
        _webhook_secret.encode("utf-8"),
        raw_body,
        hashlib.sha256,
    ).hexdigest()

    if not hmac.compare_digest(x_signature, expected):
        logger.warning("Webhook signature mismatch", context=context)
        raise ForbiddenError("Geçersiz webhook imzası")


@router.post("/payment", status_code=status.HTTP_200_OK)
async def payment_webhook(
    request: Request,
    db: DbSession,
    x_signature: str | None = Header(None, alias="X-Signature"),
) -> dict[str, Any]:
    """
    Handle Iyzico payment webhook.

    Security: HMAC-SHA256 signature mandatory, amount verified, order status checked.
    Idempotency: Duplicate payment_id calls are ignored.
    """
    import json as _json

    raw_body = await request.body()
    _verify_webhook_signature(x_signature, raw_body, context="payment")

    body = _json.loads(raw_body)

    payment_id = body.get("paymentId")
    conversation_id = body.get("conversationId")  # Our order_id
    payment_status = body.get("status")
    webhook_amount = body.get("price") or body.get("paidPrice")

    if not conversation_id:
        raise ValidationError("Missing conversationId")

    # Lock the order row to prevent race with verify-iyzico
    from app.services.order_state_machine import get_order_for_update

    order = await get_order_for_update(conversation_id, db)
    if not order:
        logger.warning("WEBHOOK_ORDER_NOT_FOUND", conversation_id=conversation_id)
        raise ValidationError("Sipariş bulunamadı")

    # Idempotency: already processed (verify-iyzico may have beaten us)
    if order.payment_id == payment_id:
        return {"received": True, "message": "Duplicate webhook ignored"}
    if order.status != OrderStatus.PAYMENT_PENDING:
        logger.warning(
            "WEBHOOK_INVALID_ORDER_STATUS",
            order_id=str(order.id),
            current_status=order.status.value,
        )
        return {"received": True, "message": "Order not awaiting payment"}

    if payment_status == "SUCCESS" and webhook_amount is not None:
        try:
            received = Decimal(str(webhook_amount))
            expected = order.payment_amount or Decimal("0")
            if abs(received - expected) > Decimal("0.01"):
                logger.critical(
                    "WEBHOOK_AMOUNT_MISMATCH",
                    order_id=str(order.id),
                    expected=str(expected),
                    received=str(received),
                )
                raise ValidationError(
                    f"Ödeme tutarı uyuşmuyor: beklenen {expected}, gelen {received}"
                )
        except (ValueError, TypeError) as exc:
            logger.error("WEBHOOK_AMOUNT_PARSE_ERROR", error=str(exc))
            raise ValidationError("Ödeme tutarı ayrıştırılamadı") from exc

    # Update payment info
    order.payment_id = payment_id
    order.payment_status = payment_status

    await record_audit(
        db,
        action="PAYMENT_CALLBACK_RECEIVED",
        order_id=order.id,
        user_id=order.user_id,
        request=request,
        details={
            "payment_id": payment_id,
            "payment_status": payment_status,
            "amount": str(webhook_amount) if webhook_amount else None,
        },
    )

    if payment_status == "SUCCESS":
        from app.services.order_state_machine import transition_order

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
                    "WEBHOOK_COLORING_BOOK_GENERATION_TRIGGERED",
                    order_id=str(order.id),
                    payment_id=payment_id,
                )
            else:
                # Regular story book generation
                from app.workers.enqueue import enqueue_full_book_generation
                _book_job = await enqueue_full_book_generation(str(order.id))
                if _book_job:
                    logger.info(
                        "WEBHOOK_BOOK_GENERATION_ENQUEUED",
                        order_id=str(order.id),
                        arq_job_id=_book_job,
                    )
                else:
                    logger.critical(
                        "WEBHOOK_BOOK_GENERATION_ENQUEUE_RETURNED_NONE — "
                        "Arq kuyrugu is olusturamadi, admin panelden tetiklenmeli!",
                        order_id=str(order.id),
                    )
        except Exception as _enq_err:
            logger.critical(
                "WEBHOOK_GENERATION_ENQUEUE_FAILED — "
                "Admin panelden tetiklenmeli.",
                order_id=str(order.id),
                error=str(_enq_err),
                is_coloring=order.is_coloring_book,
            )

    elif payment_status == "FAILURE":
        order.payment_status = "FAILED"

        from app.api.v1.payments import rollback_promo_code

        await rollback_promo_code(order, db)

        order.promo_code_id = None
        order.promo_code_text = None
        order.promo_discount_type = None
        order.promo_discount_value = None
        order.discount_applied_amount = None

        await db.commit()

    return {"received": True}


@router.post("/elevenlabs", status_code=status.HTTP_200_OK)
async def elevenlabs_webhook(
    request: Request,
    db: DbSession,
    x_signature: str | None = Header(None, alias="X-Webhook-Secret"),
) -> dict[str, Any]:
    """
    Handle ElevenLabs voice cloning webhook.

    Called when voice cloning is complete.
    """
    import json as _json

    raw_body = await request.body()
    _verify_webhook_signature(x_signature, raw_body, context="elevenlabs")

    _body = _json.loads(raw_body)

    # TODO: Implement voice cloning completion handling
    # Update order with voice_id

    return {"received": True}

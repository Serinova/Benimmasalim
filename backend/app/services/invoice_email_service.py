"""Invoice email service — sends invoice PDF to order owner (guest or registered).

Trigger: called when invoice_status transitions to PDF_READY.
Idempotency: email_sent_at on Invoice row prevents duplicate sends.
Guest handling: uses billing_email from order; skips if missing.
KVKK: respects cancelled invoices and deleted accounts.
"""

from datetime import UTC, datetime
from uuid import UUID

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.invoice import Invoice, InvoiceStatus
from app.models.order import Order
from app.models.user import User

logger = structlog.get_logger()


async def send_invoice_email_for_order(
    order_id: UUID,
    db: AsyncSession,
    *,
    is_resend: bool = False,
    admin_id: UUID | None = None,
) -> dict[str, str]:
    """Send invoice PDF email for an order.

    Returns dict with "status" key: "sent", "skipped", "failed", or "already_sent".
    """
    result = await db.execute(
        select(Invoice).where(Invoice.order_id == order_id)
    )
    invoice = result.scalar_one_or_none()
    if not invoice:
        return {"status": "skipped", "reason": "no_invoice"}

    if invoice.invoice_status == InvoiceStatus.CANCELLED.value:
        return {"status": "skipped", "reason": "invoice_cancelled"}

    if invoice.invoice_status != InvoiceStatus.PDF_READY.value:
        return {"status": "skipped", "reason": f"invoice_not_ready ({invoice.invoice_status})"}

    if not is_resend and invoice.email_sent_at is not None:
        return {"status": "already_sent", "sent_at": invoice.email_sent_at.isoformat()}

    # Try Order table first (legacy flow), then StoryPreview (trial flow)
    result = await db.execute(select(Order).where(Order.id == order_id))
    order = result.scalar_one_or_none()

    billing_entity = order
    if billing_entity is None:
        from app.models.story_preview import StoryPreview
        prev_res = await db.execute(
            select(StoryPreview).where(StoryPreview.id == order_id)
        )
        preview = prev_res.scalar_one_or_none()
        if preview:
            from app.services.invoice_pdf_service import _PreviewBillingAdapter
            billing_entity = _PreviewBillingAdapter.from_preview(preview)

    if billing_entity is None:
        return {"status": "skipped", "reason": "order_not_found"}

    recipient_email = await resolve_recipient_email_with_user(billing_entity, db)
    if not recipient_email:
        invoice.email_status = "SKIPPED"
        invoice.email_error = "no_email_available"
        await db.commit()
        logger.warning(
            "invoice_email_skipped_no_email",
            order_id=str(order_id),
            invoice_number=invoice.invoice_number,
        )
        return {"status": "skipped", "reason": "no_email"}

    recipient_name = _resolve_recipient_name(billing_entity)

    if not invoice.pdf_url:
        invoice.email_status = "FAILED"
        invoice.email_error = "pdf_url_missing"
        await db.commit()
        return {"status": "failed", "reason": "pdf_url_missing"}

    try:
        from app.services.storage_service import storage_service
        pdf_bytes = storage_service.download_bytes(invoice.pdf_url)
    except Exception as exc:
        invoice.email_status = "FAILED"
        invoice.email_error = f"pdf_download_failed: {str(exc)[:200]}"
        invoice.email_retry_count = (invoice.email_retry_count or 0) + 1
        await db.commit()
        logger.error(
            "invoice_email_pdf_download_failed",
            order_id=str(order_id),
            error=str(exc),
        )
        return {"status": "failed", "reason": "pdf_download_failed"}

    try:
        from app.services.email_service import email_service
        from app.services.invoice_token_service import create_download_token

        issued_date = (
            invoice.issued_at.strftime("%d.%m.%Y")
            if invoice.issued_at
            else datetime.now(UTC).strftime("%d.%m.%Y")
        )
        total_amount = f"{billing_entity.final_amount:.2f} TL" if billing_entity.final_amount else "0.00 TL"
        order_ref = str(billing_entity.id)[:8].upper()

        # Pass the actual order FK (None for trial/preview invoices — token table supports nullable)
        raw_token = await create_download_token(
            order_id=invoice.order_id,
            invoice_id=invoice.id,
            db=db,
            created_by="admin" if is_resend else "system",
        )
        from app.config import settings as _cfg
        frontend_base = getattr(_cfg, "frontend_url", "https://benimmasalim.com")
        download_url = f"{frontend_base}/api/v1/invoice/{raw_token}/download"

        await email_service.send_invoice_email_async(
            recipient_email=recipient_email,
            recipient_name=recipient_name,
            invoice_number=invoice.invoice_number,
            order_ref=order_ref,
            issued_date=issued_date,
            total_amount=total_amount,
            pdf_bytes=pdf_bytes,
            download_url=download_url,
        )

        now = datetime.now(UTC)
        invoice.email_status = "SENT"
        invoice.email_error = None

        if is_resend:
            invoice.email_resent_count = (invoice.email_resent_count or 0) + 1
            invoice.email_last_resent_at = now
            if admin_id:
                invoice.email_resent_by_admin_id = admin_id
        else:
            invoice.email_sent_at = now

        await db.commit()

        logger.info(
            "invoice_email_sent",
            order_id=str(order_id),
            invoice_number=invoice.invoice_number,
            is_resend=is_resend,
            recipient_domain=recipient_email.rsplit("@", 1)[-1],
        )
        return {"status": "sent", "recipient": recipient_email}

    except Exception as exc:
        invoice.email_status = "FAILED"
        invoice.email_error = str(exc)[:500]
        invoice.email_retry_count = (invoice.email_retry_count or 0) + 1
        await db.commit()

        logger.error(
            "invoice_email_send_failed",
            order_id=str(order_id),
            error=str(exc),
        )
        return {"status": "failed", "reason": str(exc)[:200]}


def _resolve_recipient_email(order: Order, db: AsyncSession) -> str | None:
    """Resolve the best email for invoice delivery.

    Priority: billing_email > user.email (if registered).
    Empty strings are treated as missing.
    """
    if order.billing_email and order.billing_email.strip():
        return order.billing_email.strip()
    return None


async def resolve_recipient_email_with_user(
    order: Order, db: AsyncSession,
) -> str | None:
    """Resolve email with user lookup fallback (for async contexts).

    Works with both Order instances and _PreviewBillingAdapter duck-types.
    """
    if order.billing_email:
        return order.billing_email
    user_id = getattr(order, "user_id", None)
    if user_id:
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if user and user.email:
            return user.email
    return None


def _resolve_recipient_name(order: Order) -> str:
    if order.billing_full_name:
        return order.billing_full_name
    return "Değerli Müşterimiz"


async def retry_failed_invoice_emails(db: AsyncSession) -> int:
    """Retry FAILED invoice emails with retry_count < 3. Returns count retried."""
    result = await db.execute(
        select(Invoice).where(
            Invoice.email_status == "FAILED",
            Invoice.email_retry_count < 3,
            Invoice.invoice_status == InvoiceStatus.PDF_READY.value,
        )
    )
    invoices = result.scalars().all()
    count = 0
    for inv in invoices:
        ref_id = inv.order_id or inv.story_preview_id
        if not ref_id:
            continue
        try:
            resp = await send_invoice_email_for_order(ref_id, db)
            if resp["status"] == "sent":
                count += 1
        except Exception:
            logger.exception(
                "retry_failed_invoice_emails: retry failed",
                ref_id=str(ref_id),
            )
    return count

"""Public invoice PDF download via secure token.

No authentication required — the token IS the credential.
Security: hashed token lookup, atomic consumption, TTL, single-use, rate-limited.
"""

from io import BytesIO
from typing import Any

import structlog
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from sqlalchemy import select

from app.models.invoice import Invoice, InvoiceStatus

logger = structlog.get_logger()

router = APIRouter()

_SECURITY_HEADERS = {
    "Cache-Control": "private, no-store, no-cache, must-revalidate",
    "Pragma": "no-cache",
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "no-referrer",
    "X-Frame-Options": "DENY",
    "Content-Security-Policy": "default-src 'none'",
    "X-Robots-Tag": "noindex, nofollow, noarchive",
}


@router.get("/{token}/download")
async def public_invoice_download(
    token: str,
    request: Request,
) -> Any:
    """Download invoice PDF using a secure single-use token.

    No auth required. Token validity is checked atomically.
    Returns 404 for any invalid/expired/used/revoked token (no info leak).
    """
    from app.core.database import async_session_factory

    client_ip = _get_client_ip(request)
    user_agent = request.headers.get("user-agent", "")[:200]

    if not token or len(token) < 20:
        logger.warning(
            "invoice_download_attempt_invalid_format",
            ip=client_ip,
        )
        raise HTTPException(status_code=404, detail="Geçersiz veya süresi dolmuş link")

    async with async_session_factory() as session:
        from app.services.invoice_token_service import verify_and_consume_token

        token_record = await verify_and_consume_token(token, session)

        if not token_record:
            logger.warning(
                "invoice_download_attempt_rejected",
                ip=client_ip,
                user_agent=user_agent[:50],
            )
            await session.commit()
            raise HTTPException(status_code=404, detail="Geçersiz veya süresi dolmuş link")

        inv_result = await session.execute(
            select(Invoice).where(Invoice.id == token_record.invoice_id)
        )
        invoice = inv_result.scalar_one_or_none()

        if not invoice or invoice.invoice_status != InvoiceStatus.PDF_READY.value:
            logger.error(
                "invoice_download_token_valid_but_invoice_not_ready",
                order_id=str(token_record.order_id),
                invoice_status=invoice.invoice_status if invoice else "MISSING",
            )
            await session.commit()
            raise HTTPException(status_code=404, detail="Fatura henüz hazır değil")

        if not invoice.pdf_url:
            await session.commit()
            raise HTTPException(status_code=502, detail="Fatura dosyası bulunamadı")

        try:
            from app.services.storage_service import storage_service
            pdf_bytes = storage_service.download_bytes(invoice.pdf_url)
        except Exception as exc:
            logger.error(
                "invoice_download_storage_error",
                order_id=str(token_record.order_id),
                error=str(exc)[:200],
            )
            await session.commit()
            raise HTTPException(status_code=502, detail="Fatura dosyası indirilemedi")

        await session.commit()

        filename = f"fatura_{invoice.invoice_number}.pdf"

        logger.info(
            "invoice_download_success",
            token_hash_prefix=token_record.token_hash[:8],
            order_id=str(token_record.order_id),
            ip=client_ip,
        )

        return StreamingResponse(
            BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
                **_SECURITY_HEADERS,
            },
        )


def _get_client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    real_ip = request.headers.get("x-real-ip")
    if real_ip:
        return real_ip
    return request.client.host if request.client else "unknown"

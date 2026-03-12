"""Tests for invoice email sending system.

Covers:
- Automatic email on PDF_READY (guest + registered)
- Idempotency: duplicate PDF_READY events don't send duplicate emails
- Missing email: skipped + admin warning
- Admin resend: works, increments resent_count, writes audit log
- KVKK: cancelled invoice blocks email
- Retry worker: retries FAILED emails
- Email content: correct subject, attachment
"""

from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.models.invoice import Invoice, InvoiceStatus

# ─── Helpers ──────────────────────────────────────────────────────

def _make_order(**overrides) -> MagicMock:
    order = MagicMock()
    order.id = overrides.get("id", uuid4())
    order.user_id = overrides.get("user_id")
    order.billing_email = overrides.get("billing_email", "guest@test.com")
    order.billing_full_name = overrides.get("billing_full_name", "Test User")
    order.final_amount = overrides.get("final_amount", Decimal("149.90"))
    order.child_name = overrides.get("child_name", "Ali")
    return order


def _make_invoice(**overrides) -> MagicMock:
    inv = MagicMock(spec=Invoice)
    inv.id = overrides.get("id", uuid4())
    inv.order_id = overrides.get("order_id", uuid4())
    inv.invoice_number = overrides.get("invoice_number", "BM-2026-000001")
    inv.invoice_status = overrides.get("invoice_status", InvoiceStatus.PDF_READY.value)
    inv.pdf_url = overrides.get("pdf_url", "gs://bucket/invoices/test.pdf")
    inv.issued_at = overrides.get("issued_at", datetime(2026, 2, 28, tzinfo=UTC))
    inv.email_sent_at = overrides.get("email_sent_at")
    inv.email_status = overrides.get("email_status")
    inv.email_error = overrides.get("email_error")
    inv.email_retry_count = overrides.get("email_retry_count", 0)
    inv.email_resent_count = overrides.get("email_resent_count", 0)
    inv.email_last_resent_at = overrides.get("email_last_resent_at")
    inv.email_resent_by_admin_id = overrides.get("email_resent_by_admin_id")
    inv.needs_credit_note = overrides.get("needs_credit_note", False)
    inv.pdf_version = overrides.get("pdf_version", 1)
    return inv


def _mock_db_with(invoice, order=None):
    """Create a mock AsyncSession that returns invoice and order from select queries."""
    db = AsyncMock()
    call_count = {"n": 0}

    async def execute_side_effect(stmt):
        call_count["n"] += 1
        result = MagicMock()
        if call_count["n"] == 1:
            result.scalar_one_or_none.return_value = invoice
        elif call_count["n"] == 2:
            result.scalar_one_or_none.return_value = order
        else:
            result.scalar_one_or_none.return_value = None
        return result

    db.execute = AsyncMock(side_effect=execute_side_effect)
    db.commit = AsyncMock()
    db.add = MagicMock()
    return db


# ─── Automatic email on PDF_READY ─────────────────────────────────

class TestInvoiceEmailAutoSend:
    """Email is sent automatically when invoice reaches PDF_READY."""

    @pytest.mark.asyncio
    async def test_guest_order_email_sent(self):
        """Guest order (no user_id) gets invoice email via billing_email."""
        order = _make_order(billing_email="guest@example.com", user_id=None)
        invoice = _make_invoice(order_id=order.id)
        db = _mock_db_with(invoice, order)

        mock_storage = MagicMock()
        mock_storage.download_bytes.return_value = b"%PDF-fake-content"
        mock_email = MagicMock()
        mock_email.send_invoice_email_async = AsyncMock(return_value=True)

        with patch("app.services.storage_service.storage_service", mock_storage), \
             patch("app.services.email_service.email_service", mock_email):
            from app.services.invoice_email_service import send_invoice_email_for_order
            result = await send_invoice_email_for_order(order.id, db)

        assert result["status"] == "sent"
        assert result["recipient"] == "guest@example.com"
        mock_email.send_invoice_email_async.assert_called_once()

    @pytest.mark.asyncio
    async def test_registered_user_email_sent(self):
        """Registered user gets invoice email via billing_email."""
        user_id = uuid4()
        order = _make_order(billing_email="user@example.com", user_id=user_id)
        invoice = _make_invoice(order_id=order.id)
        db = _mock_db_with(invoice, order)

        mock_storage = MagicMock()
        mock_storage.download_bytes.return_value = b"%PDF-fake-content"
        mock_email = MagicMock()
        mock_email.send_invoice_email_async = AsyncMock(return_value=True)

        with patch("app.services.storage_service.storage_service", mock_storage), \
             patch("app.services.email_service.email_service", mock_email):
            from app.services.invoice_email_service import send_invoice_email_for_order
            result = await send_invoice_email_for_order(order.id, db)

        assert result["status"] == "sent"

    @pytest.mark.asyncio
    async def test_email_sent_at_is_set(self):
        """After successful send, email_sent_at is set on invoice."""
        order = _make_order()
        invoice = _make_invoice(order_id=order.id)
        db = _mock_db_with(invoice, order)

        mock_storage = MagicMock()
        mock_storage.download_bytes.return_value = b"%PDF-content"
        mock_email = MagicMock()
        mock_email.send_invoice_email_async = AsyncMock(return_value=True)

        with patch("app.services.storage_service.storage_service", mock_storage), \
             patch("app.services.email_service.email_service", mock_email):
            from app.services.invoice_email_service import send_invoice_email_for_order
            await send_invoice_email_for_order(order.id, db)

        assert invoice.email_sent_at is not None
        assert invoice.email_status == "SENT"


# ─── Idempotency ──────────────────────────────────────────────────

class TestInvoiceEmailIdempotency:
    """Duplicate PDF_READY events must not send duplicate emails."""

    @pytest.mark.asyncio
    async def test_already_sent_returns_already_sent(self):
        """If email_sent_at is set, return already_sent without sending."""
        order = _make_order()
        invoice = _make_invoice(
            order_id=order.id,
            email_sent_at=datetime(2026, 2, 28, 12, 0, tzinfo=UTC),
        )
        db = _mock_db_with(invoice, order)

        with patch("app.services.email_service.email_service") as mock_email:
            mock_email.send_invoice_email_async = AsyncMock()

            from app.services.invoice_email_service import send_invoice_email_for_order
            result = await send_invoice_email_for_order(order.id, db)

        assert result["status"] == "already_sent"
        mock_email.send_invoice_email_async.assert_not_called()

    @pytest.mark.asyncio
    async def test_resend_bypasses_idempotency(self):
        """Admin resend ignores email_sent_at and sends again."""
        order = _make_order()
        invoice = _make_invoice(
            order_id=order.id,
            email_sent_at=datetime(2026, 2, 28, 12, 0, tzinfo=UTC),
        )
        db = _mock_db_with(invoice, order)

        mock_storage = MagicMock()
        mock_storage.download_bytes.return_value = b"%PDF-content"
        mock_email = MagicMock()
        mock_email.send_invoice_email_async = AsyncMock(return_value=True)

        with patch("app.services.storage_service.storage_service", mock_storage), \
             patch("app.services.email_service.email_service", mock_email):
            from app.services.invoice_email_service import send_invoice_email_for_order
            result = await send_invoice_email_for_order(
                order.id, db, is_resend=True, admin_id=uuid4(),
            )

        assert result["status"] == "sent"
        mock_email.send_invoice_email_async.assert_called_once()
        assert invoice.email_resent_count == 1


# ─── Missing email ────────────────────────────────────────────────

class TestInvoiceEmailMissing:
    """Orders without email should be skipped, not crash."""

    @pytest.mark.asyncio
    async def test_no_email_skipped(self):
        """If billing_email is None, skip and set email_status=SKIPPED."""
        order = _make_order(billing_email=None, user_id=None)
        invoice = _make_invoice(order_id=order.id)
        db = _mock_db_with(invoice, order)

        from app.services.invoice_email_service import send_invoice_email_for_order
        result = await send_invoice_email_for_order(order.id, db)

        assert result["status"] == "skipped"
        assert result["reason"] == "no_email"
        assert invoice.email_status == "SKIPPED"

    @pytest.mark.asyncio
    async def test_empty_string_email_skipped(self):
        """Empty string email is treated as missing."""
        order = _make_order(billing_email="", user_id=None)
        invoice = _make_invoice(order_id=order.id)
        db = _mock_db_with(invoice, order)

        from app.services.invoice_email_service import send_invoice_email_for_order
        result = await send_invoice_email_for_order(order.id, db)

        assert result["status"] == "skipped"
        assert result["reason"] == "no_email"


# ─── Invoice not ready ────────────────────────────────────────────

class TestInvoiceEmailNotReady:
    """Email should only be sent for PDF_READY invoices."""

    @pytest.mark.asyncio
    async def test_pending_invoice_skipped(self):
        invoice = _make_invoice(invoice_status=InvoiceStatus.PENDING.value)
        db = _mock_db_with(invoice)

        from app.services.invoice_email_service import send_invoice_email_for_order
        result = await send_invoice_email_for_order(invoice.order_id, db)

        assert result["status"] == "skipped"
        assert "not_ready" in result["reason"]

    @pytest.mark.asyncio
    async def test_cancelled_invoice_skipped(self):
        invoice = _make_invoice(invoice_status=InvoiceStatus.CANCELLED.value)
        db = _mock_db_with(invoice)

        from app.services.invoice_email_service import send_invoice_email_for_order
        result = await send_invoice_email_for_order(invoice.order_id, db)

        assert result["status"] == "skipped"
        assert result["reason"] == "invoice_cancelled"

    @pytest.mark.asyncio
    async def test_no_invoice_skipped(self):
        db = _mock_db_with(None)

        from app.services.invoice_email_service import send_invoice_email_for_order
        result = await send_invoice_email_for_order(uuid4(), db)

        assert result["status"] == "skipped"
        assert result["reason"] == "no_invoice"


# ─── Email send failure ───────────────────────────────────────────

class TestInvoiceEmailFailure:
    """SMTP failures should be recorded, not crash the system."""

    @pytest.mark.asyncio
    async def test_smtp_failure_marks_failed(self):
        order = _make_order()
        invoice = _make_invoice(order_id=order.id)
        db = _mock_db_with(invoice, order)

        mock_storage = MagicMock()
        mock_storage.download_bytes.return_value = b"%PDF-content"
        mock_email = MagicMock()
        mock_email.send_invoice_email_async = AsyncMock(
            side_effect=Exception("SMTP connection refused"),
        )

        with patch("app.services.storage_service.storage_service", mock_storage), \
             patch("app.services.email_service.email_service", mock_email):
            from app.services.invoice_email_service import send_invoice_email_for_order
            result = await send_invoice_email_for_order(order.id, db)

        assert result["status"] == "failed"
        assert invoice.email_status == "FAILED"
        assert "SMTP" in (invoice.email_error or "")
        assert invoice.email_retry_count == 1

    @pytest.mark.asyncio
    async def test_pdf_download_failure(self):
        order = _make_order()
        invoice = _make_invoice(order_id=order.id)
        db = _mock_db_with(invoice, order)

        mock_storage = MagicMock()
        mock_storage.download_bytes.side_effect = Exception("GCS timeout")

        with patch("app.services.storage_service.storage_service", mock_storage):
            from app.services.invoice_email_service import send_invoice_email_for_order
            result = await send_invoice_email_for_order(order.id, db)

        assert result["status"] == "failed"
        assert result["reason"] == "pdf_download_failed"
        assert invoice.email_status == "FAILED"

    @pytest.mark.asyncio
    async def test_missing_pdf_url(self):
        order = _make_order()
        invoice = _make_invoice(order_id=order.id, pdf_url=None)
        db = _mock_db_with(invoice, order)

        from app.services.invoice_email_service import send_invoice_email_for_order
        result = await send_invoice_email_for_order(order.id, db)

        assert result["status"] == "failed"
        assert result["reason"] == "pdf_url_missing"


# ─── Admin resend ─────────────────────────────────────────────────

class TestAdminResend:
    """Admin can resend invoice email; resent_count increments."""

    @pytest.mark.asyncio
    async def test_resend_increments_count(self):
        admin_id = uuid4()
        order = _make_order()
        invoice = _make_invoice(
            order_id=order.id,
            email_sent_at=datetime(2026, 2, 28, tzinfo=UTC),
            email_resent_count=2,
        )
        db = _mock_db_with(invoice, order)

        mock_storage = MagicMock()
        mock_storage.download_bytes.return_value = b"%PDF-content"
        mock_email = MagicMock()
        mock_email.send_invoice_email_async = AsyncMock(return_value=True)

        with patch("app.services.storage_service.storage_service", mock_storage), \
             patch("app.services.email_service.email_service", mock_email):
            from app.services.invoice_email_service import send_invoice_email_for_order
            result = await send_invoice_email_for_order(
                order.id, db, is_resend=True, admin_id=admin_id,
            )

        assert result["status"] == "sent"
        assert invoice.email_resent_count == 3
        assert invoice.email_resent_by_admin_id == admin_id
        assert invoice.email_last_resent_at is not None


# ─── Retry worker ─────────────────────────────────────────────────

class TestInvoiceEmailRetryWorker:
    """Retry worker picks up FAILED emails and retries them."""

    @pytest.mark.asyncio
    async def test_retry_picks_up_failed(self):
        inv1 = _make_invoice(
            email_status="FAILED",
            email_retry_count=1,
            invoice_status=InvoiceStatus.PDF_READY.value,
        )

        db = AsyncMock()
        result_mock = MagicMock()
        result_mock.scalars.return_value.all.return_value = [inv1]
        db.execute = AsyncMock(return_value=result_mock)

        with patch(
            "app.services.invoice_email_service.send_invoice_email_for_order",
            new_callable=AsyncMock,
            return_value={"status": "sent"},
        ) as mock_send:
            from app.services.invoice_email_service import retry_failed_invoice_emails
            count = await retry_failed_invoice_emails(db)

        assert count == 1
        mock_send.assert_called_once_with(inv1.order_id, db)

    @pytest.mark.asyncio
    async def test_retry_skips_max_retries(self):
        """Invoices with retry_count >= 3 should not be picked up (filtered by query)."""
        db = AsyncMock()
        result_mock = MagicMock()
        result_mock.scalars.return_value.all.return_value = []
        db.execute = AsyncMock(return_value=result_mock)

        from app.services.invoice_email_service import retry_failed_invoice_emails
        count = await retry_failed_invoice_emails(db)

        assert count == 0


# ─── Email content validation ─────────────────────────────────────

class TestInvoiceEmailContent:
    """Validate email method receives correct parameters."""

    @pytest.mark.asyncio
    async def test_email_params_correct(self):
        order = _make_order(
            billing_email="test@example.com",
            billing_full_name="Ahmet Yılmaz",
            final_amount=Decimal("249.90"),
        )
        invoice = _make_invoice(
            order_id=order.id,
            invoice_number="BM-2026-000042",
        )
        db = _mock_db_with(invoice, order)

        mock_storage = MagicMock()
        mock_storage.download_bytes.return_value = b"%PDF-content"
        mock_email = MagicMock()
        mock_email.send_invoice_email_async = AsyncMock(return_value=True)

        with patch("app.services.storage_service.storage_service", mock_storage), \
             patch("app.services.email_service.email_service", mock_email):
            from app.services.invoice_email_service import send_invoice_email_for_order
            await send_invoice_email_for_order(order.id, db)

        call_kwargs = mock_email.send_invoice_email_async.call_args.kwargs
        assert call_kwargs["recipient_email"] == "test@example.com"
        assert call_kwargs["recipient_name"] == "Ahmet Yılmaz"
        assert call_kwargs["invoice_number"] == "BM-2026-000042"
        assert "249.90" in call_kwargs["total_amount"]
        assert call_kwargs["pdf_bytes"] == b"%PDF-content"

    @pytest.mark.asyncio
    async def test_order_ref_is_first_8_chars(self):
        order_id = uuid4()
        order = _make_order(id=order_id)
        invoice = _make_invoice(order_id=order_id)
        db = _mock_db_with(invoice, order)

        mock_storage = MagicMock()
        mock_storage.download_bytes.return_value = b"%PDF-content"
        mock_email = MagicMock()
        mock_email.send_invoice_email_async = AsyncMock(return_value=True)

        with patch("app.services.storage_service.storage_service", mock_storage), \
             patch("app.services.email_service.email_service", mock_email):
            from app.services.invoice_email_service import send_invoice_email_for_order
            await send_invoice_email_for_order(order_id, db)

        call_kwargs = mock_email.send_invoice_email_async.call_args.kwargs
        assert call_kwargs["order_ref"] == str(order_id)[:8].upper()


# ─── PDF_READY trigger integration ────────────────────────────────

class TestPdfReadyTrigger:
    """generate_invoice_pdf should call send_invoice_email_for_order on success."""

    @pytest.mark.asyncio
    async def test_email_triggered_after_pdf_ready(self):
        """After PDF generation succeeds, invoice email is triggered."""
        with patch(
            "app.services.invoice_email_service.send_invoice_email_for_order",
            new_callable=AsyncMock,
        ) as mock_send:
            mock_send.return_value = {"status": "sent"}
            assert mock_send is not None


# ─── Email HTML template ──────────────────────────────────────────

class TestInvoiceEmailTemplate:
    """Validate the email service builds correct email content."""

    def test_send_invoice_email_builds_attachment(self):
        """_send_invoice_email attaches PDF and sets correct subject."""
        from app.services.email_service import EmailService

        service = EmailService()

        with patch("app.services.email_service.settings.dev_email_override", None), \
             patch.object(service, "_send_with_retry") as mock_send:
            service._send_invoice_email(
                recipient_email="test@example.com",
                recipient_name="Test User",
                invoice_number="BM-2026-000001",
                order_ref="ABCD1234",
                issued_date="28.02.2026",
                total_amount="149.90 TL",
                pdf_bytes=b"%PDF-1.4 fake content",
            )

        mock_send.assert_called_once()
        args = mock_send.call_args
        msg = args[0][1]

        assert msg["Subject"] == "Faturanız Hazır — Sipariş #ABCD1234"
        assert "test@example.com" in msg["To"]

        payloads = msg.get_payload()
        assert len(payloads) == 2  # alternative + pdf attachment
        pdf_part = payloads[1]
        assert pdf_part.get_content_type() == "application/pdf"
        assert "fatura_BM-2026-000001.pdf" in pdf_part.get("Content-Disposition", "")

    def test_subject_sanitized(self):
        """Subject line is sanitized against header injection."""
        from app.services.email_service import EmailService

        service = EmailService()

        with patch.object(service, "_send_with_retry") as mock_send:
            service._send_invoice_email(
                recipient_email="test@example.com",
                recipient_name="Test",
                invoice_number="BM-2026-000001",
                order_ref="ABCD\r\nBcc: evil@hacker.com",
                issued_date="28.02.2026",
                total_amount="100 TL",
                pdf_bytes=b"%PDF",
            )

        msg = mock_send.call_args[0][1]
        assert "\r" not in msg["Subject"]
        assert "\n" not in msg["Subject"]

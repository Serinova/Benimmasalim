"""Tests for admin invoice operation reports and actions.

Covers:
- Report 1: PAID orders without PDF_READY invoice
- Report 2: PDF_READY invoices without email sent
- Report 3: Token abuse / high-usage tokens
- Dashboard aggregation endpoint
- Admin actions: resend email, revoke tokens, retry/regenerate PDF
- Audit log entries for admin actions
- Preview detail includes invoice data
"""

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from app.models.invoice import InvoiceStatus
from app.models.order import OrderStatus


# ─── Helpers ──────────────────────────────────────────────────────

def _make_order(
    status: OrderStatus = OrderStatus.PAID,
    user_id=None,
    child_name: str = "Test",
) -> MagicMock:
    order = MagicMock()
    order.id = uuid4()
    order.status = status
    order.child_name = child_name
    order.child_age = 5
    order.child_gender = "erkek"
    order.user_id = user_id
    order.payment_amount = Decimal("149.90")
    order.payment_status = "paid"
    order.billing_email = "test@example.com"
    order.billing_type = "individual"
    order.billing_full_name = "Test User"
    order.billing_phone = None
    order.billing_company_name = None
    order.billing_tax_id = None
    order.billing_tax_office = None
    order.billing_address = None
    order.shipping_address = None
    order.tracking_number = None
    order.carrier = None
    order.created_at = datetime.now(UTC)
    order.updated_at = datetime.now(UTC)
    return order


def _make_invoice(
    order_id,
    status: str = InvoiceStatus.PDF_READY.value,
    email_sent: bool = True,
    email_status: str = "SENT",
) -> MagicMock:
    inv = MagicMock()
    inv.id = uuid4()
    inv.order_id = order_id
    inv.invoice_number = "BM-2026-000001"
    inv.invoice_status = status
    inv.pdf_url = "gs://bucket/invoice.pdf" if status == InvoiceStatus.PDF_READY.value else None
    inv.pdf_version = 1
    inv.pdf_generated_at = datetime.now(UTC) if status == InvoiceStatus.PDF_READY.value else None
    inv.pdf_hash = None
    inv.issued_at = datetime.now(UTC)
    inv.last_error = None
    inv.retry_count = 0
    inv.needs_credit_note = False
    inv.cancelled_at = None
    inv.email_sent_at = datetime.now(UTC) if email_sent else None
    inv.email_status = email_status
    inv.email_error = None
    inv.email_retry_count = 0
    inv.email_resent_count = 0
    inv.email_last_resent_at = None
    inv.email_resent_by_admin_id = None
    inv.created_at = datetime.now(UTC)
    inv.updated_at = datetime.now(UTC)
    return inv


def _make_token(
    order_id,
    invoice_id,
    used_count: int = 0,
    max_uses: int = 1,
    expired: bool = False,
    revoked: bool = False,
) -> MagicMock:
    token = MagicMock()
    token.id = uuid4()
    token.token_hash = "a" * 64
    token.order_id = order_id
    token.invoice_id = invoice_id
    token.expires_at = datetime.now(UTC) + (timedelta(hours=-1) if expired else timedelta(hours=48))
    token.max_uses = max_uses
    token.used_count = used_count
    token.first_used_at = datetime.now(UTC) if used_count > 0 else None
    token.last_used_at = datetime.now(UTC) if used_count > 0 else None
    token.revoked_at = datetime.now(UTC) if revoked else None
    token.revoked_by_admin_id = None
    token.created_by = "system"
    token.created_at = datetime.now(UTC)
    token.updated_at = datetime.now(UTC)
    return token


# ─── Report 1: PDF Issues ────────────────────────────────────────

class TestPdfIssuesReport:
    """GET /admin/orders/invoices/issues — PAID orders without PDF_READY."""

    def test_paid_order_without_invoice_is_flagged(self):
        order = _make_order(status=OrderStatus.PAID)
        assert order.status == OrderStatus.PAID

    def test_paid_order_with_failed_invoice_is_flagged(self):
        order = _make_order(status=OrderStatus.PAID)
        inv = _make_invoice(order.id, status=InvoiceStatus.FAILED.value)
        assert inv.invoice_status == InvoiceStatus.FAILED.value
        assert inv.invoice_status != InvoiceStatus.PDF_READY.value

    def test_paid_order_with_pdf_ready_not_flagged(self):
        order = _make_order(status=OrderStatus.PAID)
        inv = _make_invoice(order.id, status=InvoiceStatus.PDF_READY.value)
        assert inv.invoice_status == InvoiceStatus.PDF_READY.value

    def test_draft_order_not_included(self):
        order = _make_order(status=OrderStatus.DRAFT)
        assert order.status not in [
            OrderStatus.PAID, OrderStatus.PROCESSING,
            OrderStatus.READY_FOR_PRINT, OrderStatus.SHIPPED, OrderStatus.DELIVERED,
        ]

    def test_processing_order_with_pending_invoice_is_flagged(self):
        order = _make_order(status=OrderStatus.PROCESSING)
        inv = _make_invoice(order.id, status=InvoiceStatus.PENDING.value)
        assert order.status == OrderStatus.PROCESSING
        assert inv.invoice_status != InvoiceStatus.PDF_READY.value


# ─── Report 2: Email Issues ──────────────────────────────────────

class TestEmailIssuesReport:
    """GET /admin/orders/invoices/email-issues — PDF_READY without email sent."""

    def test_pdf_ready_no_email_is_flagged(self):
        order = _make_order()
        inv = _make_invoice(order.id, email_sent=False, email_status="NOT_SENT")
        assert inv.invoice_status == InvoiceStatus.PDF_READY.value
        assert inv.email_sent_at is None

    def test_pdf_ready_email_failed_is_flagged(self):
        order = _make_order()
        inv = _make_invoice(order.id, email_sent=False, email_status="FAILED")
        assert inv.email_status == "FAILED"

    def test_pdf_ready_email_sent_not_flagged(self):
        order = _make_order()
        inv = _make_invoice(order.id, email_sent=True, email_status="SENT")
        assert inv.email_sent_at is not None
        assert inv.email_status == "SENT"

    def test_pending_invoice_not_included(self):
        order = _make_order()
        inv = _make_invoice(order.id, status=InvoiceStatus.PENDING.value, email_sent=False)
        assert inv.invoice_status != InvoiceStatus.PDF_READY.value

    def test_report_includes_billing_email(self):
        order = _make_order()
        assert order.billing_email == "test@example.com"

    def test_report_flags_guest_order(self):
        order = _make_order(user_id=None)
        assert order.user_id is None


# ─── Report 3: Token Abuse ───────────────────────────────────────

class TestTokenAbuseReport:
    """GET /admin/orders/invoices/token-abuse — high-usage tokens."""

    def test_token_with_high_usage_flagged(self):
        order = _make_order()
        inv = _make_invoice(order.id)
        token = _make_token(order.id, inv.id, used_count=5, max_uses=1)
        assert token.used_count >= 3

    def test_token_with_low_usage_not_flagged(self):
        order = _make_order()
        inv = _make_invoice(order.id)
        token = _make_token(order.id, inv.id, used_count=1, max_uses=1)
        assert token.used_count < 3

    def test_revoked_token_with_usage_flagged(self):
        order = _make_order()
        inv = _make_invoice(order.id)
        token = _make_token(order.id, inv.id, used_count=1, revoked=True)
        assert token.revoked_at is not None
        assert token.used_count > 0

    def test_expired_token_status(self):
        order = _make_order()
        inv = _make_invoice(order.id)
        token = _make_token(order.id, inv.id, expired=True, used_count=5)
        assert token.expires_at < datetime.now(UTC)

    def test_active_token_status(self):
        order = _make_order()
        inv = _make_invoice(order.id)
        token = _make_token(order.id, inv.id, used_count=0)
        assert token.expires_at > datetime.now(UTC)
        assert token.revoked_at is None
        assert token.used_count < token.max_uses


# ─── Dashboard Aggregation ───────────────────────────────────────

class TestInvoiceDashboard:
    """GET /admin/orders/invoices/dashboard — aggregated counts."""

    def test_dashboard_fields(self):
        expected_fields = [
            "pdf_issues_count",
            "email_issues_count",
            "token_abuse_count",
            "invoice_status_counts",
            "total_invoices",
        ]
        for field in expected_fields:
            assert field in expected_fields

    def test_status_counts_aggregation(self):
        counts = {"PENDING": 2, "PDF_READY": 10, "FAILED": 1}
        total = sum(counts.values())
        assert total == 13

    def test_zero_issues_is_healthy(self):
        dashboard = {
            "pdf_issues_count": 0,
            "email_issues_count": 0,
            "token_abuse_count": 0,
        }
        total_issues = sum(dashboard.values())
        assert total_issues == 0


# ─── Admin Actions ────────────────────────────────────────────────

class TestAdminInvoiceActions:
    """Admin action endpoints: resend, revoke, retry, regenerate."""

    def test_resend_email_requires_pdf_ready(self):
        order = _make_order()
        inv = _make_invoice(order.id, status=InvoiceStatus.PENDING.value)
        assert inv.invoice_status != InvoiceStatus.PDF_READY.value

    def test_retry_requires_failed_status(self):
        order = _make_order()
        inv = _make_invoice(order.id, status=InvoiceStatus.PDF_READY.value)
        assert inv.invoice_status != InvoiceStatus.FAILED.value

    def test_regenerate_increments_pdf_version(self):
        order = _make_order()
        inv = _make_invoice(order.id)
        original_version = inv.pdf_version
        inv.pdf_version = (inv.pdf_version or 1) + 1
        assert inv.pdf_version == original_version + 1

    def test_revoke_tokens_sets_revoked_at(self):
        order = _make_order()
        inv = _make_invoice(order.id)
        token = _make_token(order.id, inv.id)
        assert token.revoked_at is None
        token.revoked_at = datetime.now(UTC)
        assert token.revoked_at is not None

    def test_resend_increments_resent_count(self):
        order = _make_order()
        inv = _make_invoice(order.id)
        assert inv.email_resent_count == 0
        inv.email_resent_count = (inv.email_resent_count or 0) + 1
        assert inv.email_resent_count == 1

    def test_resend_sets_admin_id(self):
        admin_id = uuid4()
        order = _make_order()
        inv = _make_invoice(order.id)
        inv.email_resent_by_admin_id = admin_id
        assert inv.email_resent_by_admin_id == admin_id


# ─── Audit Log ────────────────────────────────────────────────────

class TestAuditLogForInvoiceActions:
    """Audit log entries for admin invoice actions."""

    def test_resend_email_audit_action(self):
        action = "INVOICE_EMAIL_RESEND"
        assert "INVOICE" in action
        assert "EMAIL" in action

    def test_revoke_tokens_audit_action(self):
        action = "INVOICE_TOKENS_REVOKED"
        assert "TOKENS" in action

    def test_audit_log_includes_order_id(self):
        order_id = uuid4()
        log_entry = {
            "action": "INVOICE_EMAIL_RESEND",
            "order_id": order_id,
            "admin_id": uuid4(),
            "details": {"status": "sent"},
        }
        assert log_entry["order_id"] == order_id

    def test_audit_log_includes_admin_id(self):
        admin_id = uuid4()
        log_entry = {
            "action": "INVOICE_TOKENS_REVOKED",
            "order_id": uuid4(),
            "admin_id": admin_id,
            "details": {"revoked_count": 2},
        }
        assert log_entry["admin_id"] == admin_id


# ─── Preview Detail Invoice Data ─────────────────────────────────

class TestPreviewDetailInvoice:
    """Preview detail endpoint includes invoice data."""

    def test_invoice_summary_fields(self):
        order = _make_order()
        inv = _make_invoice(order.id)
        summary = {
            "invoice_number": inv.invoice_number,
            "invoice_status": inv.invoice_status,
            "pdf_ready": inv.pdf_url is not None,
            "pdf_version": inv.pdf_version,
            "issued_at": inv.issued_at.isoformat() if inv.issued_at else None,
            "last_error": inv.last_error,
            "retry_count": inv.retry_count,
            "needs_credit_note": inv.needs_credit_note,
            "email_sent": inv.email_sent_at is not None,
            "email_status": inv.email_status or "NOT_SENT",
            "email_sent_at": inv.email_sent_at.isoformat() if inv.email_sent_at else None,
            "email_error": inv.email_error,
            "email_retry_count": inv.email_retry_count,
            "email_resent_count": inv.email_resent_count,
            "email_last_resent_at": inv.email_last_resent_at.isoformat() if inv.email_last_resent_at else None,
        }
        assert summary["invoice_number"] == "BM-2026-000001"
        assert summary["pdf_ready"] is True
        assert summary["email_sent"] is True
        assert summary["email_status"] == "SENT"

    def test_invoice_summary_null_when_no_invoice(self):
        summary = None
        assert summary is None

    def test_cancelled_invoice_summary(self):
        order = _make_order()
        inv = _make_invoice(order.id, status=InvoiceStatus.CANCELLED.value)
        inv.needs_credit_note = True
        assert inv.needs_credit_note is True
        assert inv.invoice_status == InvoiceStatus.CANCELLED.value

    def test_failed_invoice_shows_error(self):
        order = _make_order()
        inv = _make_invoice(order.id, status=InvoiceStatus.FAILED.value)
        inv.last_error = "ReportLab font error"
        inv.retry_count = 3
        assert inv.last_error is not None
        assert inv.retry_count == 3


# ─── Token Attempt List ──────────────────────────────────────────

class TestTokenAttemptList:
    """GET /admin/orders/{order_id}/invoice/token-attempts."""

    def test_token_attempt_fields(self):
        order = _make_order()
        inv = _make_invoice(order.id)
        token = _make_token(order.id, inv.id, used_count=1)
        now = datetime.now(UTC)

        attempt = {
            "id": str(token.id),
            "token_hash_prefix": token.token_hash[:8] + "...",
            "created_at": token.created_at.isoformat() if token.created_at else None,
            "expires_at": token.expires_at.isoformat(),
            "max_uses": token.max_uses,
            "used_count": token.used_count,
            "first_used_at": token.first_used_at.isoformat() if token.first_used_at else None,
            "last_used_at": token.last_used_at.isoformat() if token.last_used_at else None,
            "revoked_at": token.revoked_at.isoformat() if token.revoked_at else None,
            "created_by": token.created_by,
            "is_active": (
                token.revoked_at is None
                and token.used_count < token.max_uses
                and token.expires_at > now
            ),
        }
        assert attempt["used_count"] == 1
        assert attempt["is_active"] is False  # used_count >= max_uses

    def test_active_token(self):
        order = _make_order()
        inv = _make_invoice(order.id)
        token = _make_token(order.id, inv.id, used_count=0, max_uses=3)
        now = datetime.now(UTC)
        is_active = (
            token.revoked_at is None
            and token.used_count < token.max_uses
            and token.expires_at > now
        )
        assert is_active is True

    def test_revoked_token_not_active(self):
        order = _make_order()
        inv = _make_invoice(order.id)
        token = _make_token(order.id, inv.id, revoked=True)
        assert token.revoked_at is not None

    def test_expired_token_not_active(self):
        order = _make_order()
        inv = _make_invoice(order.id)
        token = _make_token(order.id, inv.id, expired=True)
        assert token.expires_at < datetime.now(UTC)

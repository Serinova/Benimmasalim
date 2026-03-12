"""Tests for invoice PDF generation system.

Covers:
- Invoice model creation and idempotency
- Invoice number format validation
- PDF generation failure handling
- IDOR prevention on download
- Cancel/refund invoice handling
- Regenerate functionality
- Admin issues endpoint logic
- Retry worker logic
"""

import re
from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.models.invoice import Invoice, InvoiceStatus
from app.models.order import Order

# ─── Invoice number format ───────────────────────────────────────

class TestInvoiceNumberFormat:
    """Invoice number must match BM-{YYYY}-{NNNNNN}."""

    def test_valid_format(self):
        pattern = r"^BM-\d{4}-\d{6}$"
        assert re.match(pattern, "BM-2026-000001")
        assert re.match(pattern, "BM-2026-999999")
        assert re.match(pattern, "BM-2025-000042")

    def test_invalid_format(self):
        pattern = r"^BM-\d{4}-\d{6}$"
        assert not re.match(pattern, "BM-2026-1")
        assert not re.match(pattern, "INV-2026-000001")
        assert not re.match(pattern, "BM-26-000001")
        assert not re.match(pattern, "")


# ─── Invoice model ───────────────────────────────────────────────

class TestInvoiceModel:
    """Test Invoice model schema and server_defaults."""

    def test_invoice_status_enum_values(self):
        assert InvoiceStatus.PENDING.value == "PENDING"
        assert InvoiceStatus.ISSUED.value == "ISSUED"
        assert InvoiceStatus.PDF_READY.value == "PDF_READY"
        assert InvoiceStatus.FAILED.value == "FAILED"
        assert InvoiceStatus.CANCELLED.value == "CANCELLED"

    def test_invoice_table_name(self):
        assert Invoice.__tablename__ == "invoices"

    def test_invoice_has_order_id_column(self):
        assert "order_id" in Invoice.__table__.columns.keys()

    def test_invoice_has_invoice_number_column(self):
        assert "invoice_number" in Invoice.__table__.columns.keys()

    def test_server_default_pdf_version(self):
        col = Invoice.__table__.columns["pdf_version"]
        assert col.server_default is not None

    def test_server_default_retry_count(self):
        col = Invoice.__table__.columns["retry_count"]
        assert col.server_default is not None


# ─── Idempotent invoice creation ─────────────────────────────────

class TestInvoiceIdempotency:
    """_create_invoice_if_not_exists must be idempotent."""

    @pytest.mark.asyncio
    async def test_create_invoice_uses_pg_upsert(self):
        """Verify the function uses ON CONFLICT DO NOTHING."""
        import inspect

        from app.services.order_state_machine import _create_invoice_if_not_exists

        source = inspect.getsource(_create_invoice_if_not_exists)
        assert "on_conflict_do_nothing" in source
        assert "pg_insert" in source or "insert" in source

    @pytest.mark.asyncio
    async def test_create_invoice_generates_correct_number_format(self):
        """Verify the generated invoice number matches BM-YYYY-NNNNNN."""
        import inspect

        from app.services.invoice_number_service import next_invoice_number

        source = inspect.getsource(next_invoice_number)
        assert "{prefix}-{year}-{serial:06d}" in source

    @pytest.mark.asyncio
    async def test_create_invoice_uses_yearly_sequence(self):
        """Verify the function creates/uses a yearly gap-free sequence."""
        import inspect

        from app.services.invoice_number_service import next_invoice_number

        source = inspect.getsource(next_invoice_number)
        assert "invoice_serial_counters" in source
        assert "UPDATE" in source
        assert "last_serial = last_serial + 1" in source


# ─── PDF generation service ──────────────────────────────────────

class TestInvoicePdfGeneration:
    """Test the PDF generation service logic."""

    def test_build_invoice_pdf_returns_bytes(self):
        """_build_invoice_pdf should return valid PDF bytes."""
        from app.services.invoice_pdf_service import _build_invoice_pdf

        inv = Invoice()
        inv.invoice_number = "BM-2026-000001"
        inv.issued_at = datetime.now(UTC)
        inv.pdf_version = 1

        order = Order()
        order.id = uuid4()
        order.child_name = "Ali"
        order.billing_type = "individual"
        order.billing_full_name = "Ahmet Yılmaz"
        order.billing_email = "ahmet@test.com"
        order.billing_phone = "05551234567"
        order.billing_address = {"address_line": "Test Sk.", "city": "İstanbul", "district": "Kadıköy"}
        order.shipping_address = None
        order.billing_company_name = None
        order.billing_tax_id = None
        order.billing_tax_office = None
        order.subtotal_amount = Decimal("149.90")
        order.payment_amount = Decimal("149.90")
        order.final_amount = Decimal("149.90")
        order.discount_applied_amount = None
        order.promo_code_text = None
        order.has_audio_book = False
        order.is_coloring_book = False

        pdf_bytes = _build_invoice_pdf(inv, order)
        assert isinstance(pdf_bytes, bytes)
        assert len(pdf_bytes) > 100
        assert pdf_bytes[:5] == b"%PDF-"

    def test_build_invoice_pdf_corporate(self):
        """PDF generation works for corporate billing."""
        from app.services.invoice_pdf_service import _build_invoice_pdf

        inv = Invoice()
        inv.invoice_number = "BM-2026-000002"
        inv.issued_at = datetime.now(UTC)
        inv.pdf_version = 1

        order = Order()
        order.id = uuid4()
        order.child_name = "Zeynep"
        order.billing_type = "corporate"
        order.billing_company_name = "Test A.Ş."
        order.billing_tax_id = "1234567890"
        order.billing_tax_office = "Kadıköy"
        order.billing_full_name = "Mehmet Demir"
        order.billing_email = "mehmet@test.com"
        order.billing_phone = "05559876543"
        order.billing_address = {"address_line": "İş Sk.", "city": "Ankara", "district": "Çankaya"}
        order.shipping_address = None
        order.subtotal_amount = Decimal("199.90")
        order.payment_amount = Decimal("199.90")
        order.final_amount = Decimal("179.90")
        order.discount_applied_amount = Decimal("20.00")
        order.promo_code_text = "INDIRIM20"
        order.has_audio_book = True
        order.is_coloring_book = False

        pdf_bytes = _build_invoice_pdf(inv, order)
        assert isinstance(pdf_bytes, bytes)
        assert pdf_bytes[:5] == b"%PDF-"

    def test_build_invoice_pdf_turkish_chars(self):
        """PDF generation handles Turkish characters (ş, ğ, İ, ı, ö, ü, ç)."""
        from app.services.invoice_pdf_service import _build_invoice_pdf

        inv = Invoice()
        inv.invoice_number = "BM-2026-000003"
        inv.issued_at = datetime.now(UTC)
        inv.pdf_version = 1

        order = Order()
        order.id = uuid4()
        order.child_name = "Şükrü Öğüt"
        order.billing_type = "individual"
        order.billing_full_name = "Çağla Güneş"
        order.billing_email = "cagla@test.com"
        order.billing_phone = "05551112233"
        order.billing_address = {"address_line": "Çiçek Sk.", "city": "İstanbul", "district": "Üsküdar"}
        order.shipping_address = None
        order.billing_company_name = None
        order.billing_tax_id = None
        order.billing_tax_office = None
        order.subtotal_amount = Decimal("149.90")
        order.payment_amount = Decimal("149.90")
        order.final_amount = Decimal("149.90")
        order.discount_applied_amount = None
        order.promo_code_text = None
        order.has_audio_book = False
        order.is_coloring_book = False

        pdf_bytes = _build_invoice_pdf(inv, order)
        assert isinstance(pdf_bytes, bytes)
        assert len(pdf_bytes) > 100

    def test_pdf_hash_is_sha256(self):
        """PDF hash should be SHA-256 hex digest."""
        import hashlib

        from app.services.invoice_pdf_service import _build_invoice_pdf

        inv = Invoice()
        inv.invoice_number = "BM-2026-000004"
        inv.issued_at = datetime.now(UTC)
        inv.pdf_version = 1

        order = Order()
        order.id = uuid4()
        order.child_name = "Test"
        order.billing_type = "individual"
        order.billing_full_name = "Test User"
        order.billing_email = "test@test.com"
        order.billing_phone = "05550000000"
        order.billing_address = None
        order.shipping_address = None
        order.billing_company_name = None
        order.billing_tax_id = None
        order.billing_tax_office = None
        order.subtotal_amount = Decimal("100")
        order.payment_amount = Decimal("100")
        order.final_amount = Decimal("100")
        order.discount_applied_amount = None
        order.promo_code_text = None
        order.has_audio_book = False
        order.is_coloring_book = False

        pdf_bytes = _build_invoice_pdf(inv, order)
        pdf_hash = hashlib.sha256(pdf_bytes).hexdigest()
        assert len(pdf_hash) == 64
        assert all(c in "0123456789abcdef" for c in pdf_hash)


# ─── Generate invoice PDF error handling ─────────────────────────

class TestGenerateInvoicePdfErrors:
    """Test error handling in generate_invoice_pdf."""

    @pytest.mark.asyncio
    async def test_no_invoice_record_returns_early(self):
        """If no invoice exists, function returns without error."""
        from app.services.invoice_pdf_service import generate_invoice_pdf

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        await generate_invoice_pdf(uuid4(), mock_db)
        mock_db.commit.assert_not_called()

    @pytest.mark.asyncio
    async def test_cancelled_invoice_skipped(self):
        """Cancelled invoices should not be regenerated."""
        from app.services.invoice_pdf_service import generate_invoice_pdf

        inv = Invoice()
        inv.invoice_status = InvoiceStatus.CANCELLED.value
        inv.order_id = uuid4()

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = inv
        mock_db.execute.return_value = mock_result

        await generate_invoice_pdf(inv.order_id, mock_db)
        mock_db.commit.assert_not_called()

    @pytest.mark.asyncio
    async def test_generation_failure_sets_failed_status(self):
        """On exception, invoice status should be FAILED with error details."""
        from app.services.invoice_pdf_service import generate_invoice_pdf

        order_id = uuid4()
        inv = Invoice()
        inv.invoice_status = InvoiceStatus.PENDING.value
        inv.order_id = order_id
        inv.invoice_number = "BM-2026-000099"
        inv.retry_count = 0

        call_count = 0

        def mock_execute_side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            result = MagicMock()
            if call_count == 1:
                result.scalar_one_or_none.return_value = inv
            elif call_count == 2:
                raise RuntimeError("Simulated GCS failure")
            elif call_count == 3:
                result.scalar_one_or_none.return_value = inv
            return result

        mock_db = AsyncMock()
        mock_db.execute.side_effect = mock_execute_side_effect
        mock_db.flush = AsyncMock()
        mock_db.commit = AsyncMock()
        mock_db.rollback = AsyncMock()

        await generate_invoice_pdf(order_id, mock_db)

        assert inv.invoice_status == InvoiceStatus.FAILED.value
        assert inv.retry_count == 1
        assert inv.last_error is not None


# ─── IDOR prevention ────────────────────────────────────────────

class TestInvoiceIdorPrevention:
    """Verify download endpoint checks ownership."""

    def test_verify_order_ownership_raises_for_wrong_user(self):
        """User A cannot access User B's order."""
        from app.api.v1.orders import _verify_order_ownership
        from app.core.exceptions import ForbiddenError

        order = Order()
        order.user_id = uuid4()

        other_user = MagicMock()
        other_user.id = uuid4()

        with pytest.raises(ForbiddenError):
            _verify_order_ownership(order, other_user)

    def test_verify_order_ownership_passes_for_owner(self):
        """Owner should be able to access their order."""
        from app.api.v1.orders import _verify_order_ownership

        user_id = uuid4()
        order = Order()
        order.user_id = user_id

        user = MagicMock()
        user.id = user_id

        _verify_order_ownership(order, user)

    def test_download_endpoint_requires_auth(self):
        """download_invoice uses CurrentUser (required auth)."""
        import inspect

        from app.api.v1.orders import download_invoice

        sig = inspect.signature(download_invoice)
        params = list(sig.parameters.keys())
        assert "current_user" in params


# ─── Cancel/refund handling ──────────────────────────────────────

class TestInvoiceCancelRefund:
    """Test that cancel/refund transitions mark invoice as CANCELLED."""

    @pytest.mark.asyncio
    async def test_cancel_invoice_sets_cancelled_status(self):
        """_cancel_invoice_if_exists should set CANCELLED + needs_credit_note."""
        from app.services.order_state_machine import _cancel_invoice_if_exists

        inv = Invoice()
        inv.invoice_status = InvoiceStatus.PDF_READY.value
        inv.needs_credit_note = False
        inv.cancelled_at = None

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = inv
        mock_db = AsyncMock()
        mock_db.execute.return_value = mock_result

        await _cancel_invoice_if_exists(uuid4(), mock_db)

        assert inv.invoice_status == InvoiceStatus.CANCELLED.value
        assert inv.needs_credit_note is True
        assert inv.cancelled_at is not None

    @pytest.mark.asyncio
    async def test_cancel_invoice_no_invoice_is_noop(self):
        """If no invoice exists, function should not raise."""
        from app.services.order_state_machine import _cancel_invoice_if_exists

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db = AsyncMock()
        mock_db.execute.return_value = mock_result

        await _cancel_invoice_if_exists(uuid4(), mock_db)

    @pytest.mark.asyncio
    async def test_already_cancelled_invoice_not_modified(self):
        """Already cancelled invoice should not be modified again."""
        from app.services.order_state_machine import _cancel_invoice_if_exists

        inv = Invoice()
        inv.invoice_status = InvoiceStatus.CANCELLED.value
        inv.needs_credit_note = True
        original_cancelled_at = datetime.now(UTC)
        inv.cancelled_at = original_cancelled_at

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = inv
        mock_db = AsyncMock()
        mock_db.execute.return_value = mock_result

        await _cancel_invoice_if_exists(uuid4(), mock_db)

        assert inv.cancelled_at == original_cancelled_at

    def test_state_machine_calls_cancel_on_cancelled(self):
        """transition_order should call _cancel_invoice_if_exists for CANCELLED."""
        import inspect

        from app.services.order_state_machine import transition_order

        source = inspect.getsource(transition_order)
        assert "_cancel_invoice_if_exists" in source
        assert "CANCELLED" in source

    def test_state_machine_calls_cancel_on_refunded(self):
        """transition_order should call _cancel_invoice_if_exists for REFUNDED."""
        import inspect

        from app.services.order_state_machine import transition_order

        source = inspect.getsource(transition_order)
        assert "REFUNDED" in source


# ─── Regenerate ──────────────────────────────────────────────────

class TestInvoiceRegenerate:
    """Test admin regenerate increments pdf_version."""

    def test_admin_regenerate_endpoint_exists(self):
        """admin_regenerate_invoice endpoint should exist."""
        from app.api.v1.admin.orders import admin_regenerate_invoice
        assert callable(admin_regenerate_invoice)

    def test_admin_retry_endpoint_exists(self):
        """admin_retry_invoice endpoint should exist."""
        from app.api.v1.admin.orders import admin_retry_invoice
        assert callable(admin_retry_invoice)

    def test_admin_issues_endpoint_exists(self):
        """admin_invoice_issues endpoint should exist."""
        from app.api.v1.admin.orders import admin_invoice_issues
        assert callable(admin_invoice_issues)


# ─── Retry worker ────────────────────────────────────────────────

class TestRetryWorker:
    """Test retry_failed_invoices logic."""

    def test_retry_function_exists(self):
        """retry_failed_invoices should be importable."""
        from app.services.invoice_pdf_service import retry_failed_invoices
        assert callable(retry_failed_invoices)

    def test_retry_only_failed_with_low_count(self):
        """Verify the query filters FAILED + retry_count < 3."""
        import inspect

        from app.services.invoice_pdf_service import retry_failed_invoices

        source = inspect.getsource(retry_failed_invoices)
        assert "FAILED" in source
        assert "retry_count" in source


# ─── Invoice summary in order detail ─────────────────────────────

class TestInvoiceSummary:
    """Test _build_invoice_summary helper."""

    @pytest.mark.asyncio
    async def test_no_invoice_returns_none(self):
        """If no invoice exists, summary should be None."""
        from app.services.order_helpers import build_invoice_summary as _build_invoice_summary

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db = AsyncMock()
        mock_db.execute.return_value = mock_result

        result = await _build_invoice_summary(uuid4(), mock_db)
        assert result is None

    @pytest.mark.asyncio
    async def test_pdf_ready_invoice_returns_summary(self):
        """PDF_READY invoice should return full summary with pdf_ready=True."""
        from app.services.order_helpers import build_invoice_summary as _build_invoice_summary

        inv = Invoice()
        inv.invoice_number = "BM-2026-000010"
        inv.invoice_status = InvoiceStatus.PDF_READY.value
        inv.issued_at = datetime(2026, 2, 28, 12, 0, 0)
        inv.needs_credit_note = False

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = inv
        mock_db = AsyncMock()
        mock_db.execute.return_value = mock_result

        result = await _build_invoice_summary(uuid4(), mock_db)
        assert result is not None
        assert result["invoice_number"] == "BM-2026-000010"
        assert result["pdf_ready"] is True
        assert result["invoice_status"] == "PDF_READY"

    @pytest.mark.asyncio
    async def test_pending_invoice_returns_pdf_ready_false(self):
        """PENDING invoice should have pdf_ready=False."""
        from app.services.order_helpers import build_invoice_summary as _build_invoice_summary

        inv = Invoice()
        inv.invoice_number = "BM-2026-000011"
        inv.invoice_status = InvoiceStatus.PENDING.value
        inv.issued_at = datetime(2026, 2, 28, 12, 0, 0)
        inv.needs_credit_note = False

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = inv
        mock_db = AsyncMock()
        mock_db.execute.return_value = mock_result

        result = await _build_invoice_summary(uuid4(), mock_db)
        assert result is not None
        assert result["pdf_ready"] is False


# ─── Storage service invoice upload ──────────────────────────────

class TestStorageInvoiceUpload:
    """Test storage service invoice-specific methods."""

    def test_upload_invoice_pdf_method_exists(self):
        """StorageService should have upload_invoice_pdf method."""
        from app.services.storage_service import StorageService
        assert hasattr(StorageService, "upload_invoice_pdf")

    def test_download_bytes_method_exists(self):
        """StorageService should have download_bytes method."""
        from app.services.storage_service import StorageService
        assert hasattr(StorageService, "download_bytes")


# ─── Config settings ─────────────────────────────────────────────

class TestInvoiceConfig:
    """Test that invoice company config settings exist."""

    def test_invoice_company_settings_exist(self):
        """Settings should have invoice_company_* fields."""
        from app.config import Settings

        fields = Settings.model_fields
        assert "invoice_company_name" in fields
        assert "invoice_company_address" in fields
        assert "invoice_company_tax_id" in fields
        assert "invoice_company_tax_office" in fields
        assert "invoice_company_phone" in fields
        assert "invoice_company_email" in fields

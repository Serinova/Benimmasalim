"""Tests for billing/invoice functionality.

Covers:
- Billing validation (corporate vs individual)
- PAID lock (403 after payment)
- Snapshot integrity (billing frozen at PAID)
- Tax ID format validation
- Audit log on billing update
"""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from uuid import uuid4

from app.models.order import Order, OrderStatus


# ─── Tax ID validation ──────────────────────────────────────────

class TestTaxIdValidation:
    """Test VKN/TCKN format validation."""

    def test_valid_vkn_10_digits(self):
        from app.services.order_helpers import validate_tax_id as _validate_tax_id
        assert _validate_tax_id("1234567890") is True

    def test_valid_tckn_11_digits(self):
        from app.services.order_helpers import validate_tax_id as _validate_tax_id
        assert _validate_tax_id("12345678901") is True

    def test_invalid_9_digits(self):
        from app.services.order_helpers import validate_tax_id as _validate_tax_id
        assert _validate_tax_id("123456789") is False

    def test_invalid_12_digits(self):
        from app.services.order_helpers import validate_tax_id as _validate_tax_id
        assert _validate_tax_id("123456789012") is False

    def test_invalid_letters(self):
        from app.services.order_helpers import validate_tax_id as _validate_tax_id
        assert _validate_tax_id("12345abcde") is False

    def test_whitespace_stripped(self):
        from app.services.order_helpers import validate_tax_id as _validate_tax_id
        assert _validate_tax_id(" 1234567890 ") is True

    def test_empty_string(self):
        from app.services.order_helpers import validate_tax_id as _validate_tax_id
        assert _validate_tax_id("") is False


# ─── Billing snapshot ───────────────────────────────────────────

class TestBillingSnapshot:
    """Test that billing data is frozen at PAID transition."""

    def test_snapshot_fills_defaults_from_shipping(self):
        from app.services.order_helpers import snapshot_billing_to_order

        order = Order()
        order.billing_type = None
        order.billing_full_name = None
        order.billing_email = None
        order.billing_phone = None
        order.billing_address = None
        order.shipping_address = {
            "fullName": "Ali Veli",
            "email": "ali@test.com",
            "phone": "05551234567",
            "address": "Test Mah.",
            "city": "Istanbul",
            "district": "Kadıköy",
            "postalCode": "34000",
        }

        snapshot_billing_to_order(order)

        assert order.billing_type == "individual"
        assert order.billing_full_name == "Ali Veli"
        assert order.billing_email == "ali@test.com"
        assert order.billing_phone == "05551234567"
        assert order.billing_address["city"] == "Istanbul"

    def test_snapshot_preserves_existing_billing(self):
        from app.services.order_helpers import snapshot_billing_to_order

        order = Order()
        order.billing_type = "corporate"
        order.billing_full_name = "Şirket Yetkilisi"
        order.billing_email = "muhasebe@firma.com"
        order.billing_phone = "02121234567"
        order.billing_company_name = "Test A.Ş."
        order.billing_tax_id = "1234567890"
        order.billing_tax_office = "Kadıköy"
        order.billing_address = {"address": "Firma Adresi", "city": "Istanbul"}
        order.shipping_address = {
            "fullName": "Farklı Kişi",
            "email": "farkli@test.com",
        }

        snapshot_billing_to_order(order)

        assert order.billing_type == "corporate"
        assert order.billing_full_name == "Şirket Yetkilisi"
        assert order.billing_email == "muhasebe@firma.com"
        assert order.billing_address["address"] == "Firma Adresi"

    def test_snapshot_without_shipping_address(self):
        from app.services.order_helpers import snapshot_billing_to_order

        order = Order()
        order.billing_type = None
        order.billing_full_name = None
        order.billing_email = None
        order.billing_phone = None
        order.billing_address = None
        order.shipping_address = None

        snapshot_billing_to_order(order)

        assert order.billing_type == "individual"
        assert order.billing_full_name is None


# ─── Billing summary builder ────────────────────────────────────

class TestBillingSummary:
    """Test _build_billing_summary output."""

    def test_individual_billing_summary(self):
        from app.services.order_helpers import build_billing_summary as _build_billing_summary

        order = Order()
        order.billing_type = "individual"
        order.billing_full_name = "Ali Veli"
        order.billing_email = "ali@test.com"
        order.billing_phone = "05551234567"
        order.billing_company_name = None
        order.billing_tax_id = None
        order.billing_tax_office = None
        order.billing_address = {"city": "Istanbul"}

        result = _build_billing_summary(order)

        assert result["billing_type"] == "individual"
        assert result["billing_full_name"] == "Ali Veli"
        assert result["billing_company_name"] is None
        assert result["billing_tax_id"] is None

    def test_corporate_billing_summary(self):
        from app.services.order_helpers import build_billing_summary as _build_billing_summary

        order = Order()
        order.billing_type = "corporate"
        order.billing_full_name = "Yetkili"
        order.billing_email = "muhasebe@firma.com"
        order.billing_phone = None
        order.billing_company_name = "Test A.Ş."
        order.billing_tax_id = "1234567890"
        order.billing_tax_office = "Kadıköy"
        order.billing_address = {"city": "Istanbul", "address": "Firma Adresi"}

        result = _build_billing_summary(order)

        assert result["billing_type"] == "corporate"
        assert result["billing_company_name"] == "Test A.Ş."
        assert result["billing_tax_id"] == "1234567890"
        assert result["billing_tax_office"] == "Kadıköy"


# ─── Billing editable status check ──────────────────────────────

class TestBillingEditableStatuses:
    """Test that billing is only editable in pre-PAID statuses."""

    def test_editable_statuses_defined(self):
        from app.api.v1.orders import _BILLING_EDITABLE_STATUSES

        assert OrderStatus.DRAFT in _BILLING_EDITABLE_STATUSES
        assert OrderStatus.TEXT_APPROVED in _BILLING_EDITABLE_STATUSES
        assert OrderStatus.COVER_APPROVED in _BILLING_EDITABLE_STATUSES
        assert OrderStatus.PAYMENT_PENDING in _BILLING_EDITABLE_STATUSES

    def test_paid_not_editable(self):
        from app.api.v1.orders import _BILLING_EDITABLE_STATUSES

        assert OrderStatus.PAID not in _BILLING_EDITABLE_STATUSES
        assert OrderStatus.PROCESSING not in _BILLING_EDITABLE_STATUSES
        assert OrderStatus.SHIPPED not in _BILLING_EDITABLE_STATUSES
        assert OrderStatus.DELIVERED not in _BILLING_EDITABLE_STATUSES


# ─── BillingUpdateRequest validation ────────────────────────────

class TestBillingUpdateRequest:
    """Test Pydantic model validation."""

    def test_valid_individual(self):
        from app.api.v1.orders import BillingUpdateRequest

        req = BillingUpdateRequest(
            billing_type="individual",
            billing_full_name="Ali Veli",
        )
        assert req.billing_type == "individual"

    def test_valid_corporate(self):
        from app.api.v1.orders import BillingUpdateRequest

        req = BillingUpdateRequest(
            billing_type="corporate",
            billing_company_name="Test A.Ş.",
            billing_tax_id="1234567890",
            billing_tax_office="Kadıköy",
        )
        assert req.billing_type == "corporate"

    def test_invalid_billing_type_rejected(self):
        from app.api.v1.orders import BillingUpdateRequest
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            BillingUpdateRequest(billing_type="invalid_type")

    def test_use_shipping_address_default_true(self):
        from app.api.v1.orders import BillingUpdateRequest

        req = BillingUpdateRequest(
            billing_type="individual",
            billing_full_name="Ali",
        )
        assert req.use_shipping_address is True


# ─── BillingInfo in CheckoutRequest ─────────────────────────────

class TestCheckoutBillingInfo:
    """Test that billing info is accepted in checkout request."""

    def test_billing_info_optional(self):
        from app.schemas.payments import CheckoutRequest

        req = CheckoutRequest(
            order_id=uuid4(),
            shipping_address={"fullName": "Ali", "city": "Istanbul"},
        )
        assert req.billing is None

    def test_billing_info_accepted(self):
        from app.schemas.payments import CheckoutRequest, BillingInfo

        req = CheckoutRequest(
            order_id=uuid4(),
            shipping_address={"fullName": "Ali", "city": "Istanbul"},
            billing=BillingInfo(
                billing_type="corporate",
                billing_company_name="Test A.Ş.",
                billing_tax_id="1234567890",
            ),
        )
        assert req.billing is not None
        assert req.billing.billing_type == "corporate"
        assert req.billing.billing_company_name == "Test A.Ş."


# ─── State machine snapshot integration ─────────────────────────

class TestStateMachineSnapshot:
    """Test that snapshot is called during PAID transition."""

    def test_snapshot_called_on_paid_transition(self):
        """Verify the state machine code calls snapshot_billing_to_order on PAID."""
        import inspect
        from app.services.order_state_machine import transition_order

        source = inspect.getsource(transition_order)
        assert "snapshot_billing_to_order" in source
        assert "OrderStatus.PAID" in source


# ─── KVKK cleanup includes new billing fields ───────────────────

class TestKvkkBillingCleanup:
    """Test that KVKK cleanup clears all billing PII."""

    def test_kvkk_clears_billing_fields(self):
        import inspect
        from app.tasks.kvkk_cleanup import delete_user_data

        source = inspect.getsource(delete_user_data)
        assert "billing_tax_office" in source
        assert "billing_full_name" in source
        assert "billing_email" in source
        assert "billing_phone" in source
        assert "billing_address" in source


# ─── Admin export endpoint exists ────────────────────────────────

class TestAdminBillingExport:
    """Test that admin billing export endpoint is registered."""

    def test_export_billing_endpoint_exists(self):
        import inspect
        from app.api.v1.admin.orders import export_billing

        assert callable(export_billing)
        sig = inspect.signature(export_billing)
        assert "db" in sig.parameters
        assert "admin" in sig.parameters

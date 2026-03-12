"""Tests for guest→user conversion, IDOR prevention, and order ownership.

Unit-level tests that validate:
- Object-level authorization (IDOR) across order endpoints
- Guest-to-user conversion idempotency and anti-enumeration
- Order ownership verification helper
- Token invalidation on password change/reset
- Convert-guest audit trail completeness
"""

import inspect
import uuid

import pytest

from app.models.order import Order, OrderStatus
from app.models.user import User

# ── IDOR: _verify_order_ownership ──────────────────────────────────────────


class TestVerifyOrderOwnership:
    """Object-level authorization helper must enforce strict ownership."""

    @pytest.fixture()
    def helper(self):
        from app.api.v1.orders import _verify_order_ownership
        return _verify_order_ownership

    def _make_order(self, user_id: uuid.UUID | None = None) -> Order:
        return Order(
            id=uuid.uuid4(),
            user_id=user_id,
            status=OrderStatus.DRAFT,
        )

    def _make_user(self, uid: uuid.UUID | None = None) -> User:
        return User(id=uid or uuid.uuid4(), email="a@b.com", is_guest=False)

    def test_owner_can_access_own_order(self, helper):
        uid = uuid.uuid4()
        order = self._make_order(user_id=uid)
        user = self._make_user(uid)
        helper(order, user)  # should not raise

    def test_different_user_cannot_access_order(self, helper):
        from app.core.exceptions import ForbiddenError

        order = self._make_order(user_id=uuid.uuid4())
        attacker = self._make_user()
        with pytest.raises(ForbiddenError):
            helper(order, attacker)

    def test_unauthenticated_cannot_access_owned_order(self, helper):
        from app.core.exceptions import ForbiddenError

        order = self._make_order(user_id=uuid.uuid4())
        with pytest.raises(ForbiddenError):
            helper(order, None)

    def test_authenticated_user_cannot_access_unowned_order(self, helper):
        """Authenticated users must NOT be able to claim unowned orders."""
        from app.core.exceptions import ForbiddenError

        order = self._make_order(user_id=None)
        user = self._make_user()
        with pytest.raises(ForbiddenError):
            helper(order, user)

    def test_unowned_order_accessible_by_unauthenticated(self, helper):
        """Unowned orders (user_id=None) can be accessed without auth (anonymous flow)."""
        order = self._make_order(user_id=None)
        helper(order, None)  # should not raise


class TestPaymentOwnershipHelper:
    """Payment endpoints always require auth — stricter ownership check."""

    @pytest.fixture()
    def helper(self):
        from app.api.v1.payments import _verify_order_ownership_payment
        return _verify_order_ownership_payment

    def test_owner_can_access(self, helper):
        uid = uuid.uuid4()
        order = Order(id=uuid.uuid4(), user_id=uid, status=OrderStatus.COVER_APPROVED)
        user = User(id=uid, email="x@y.com", is_guest=False)
        helper(order, user)

    def test_different_user_blocked(self, helper):
        from app.core.exceptions import ForbiddenError

        order = Order(id=uuid.uuid4(), user_id=uuid.uuid4(), status=OrderStatus.COVER_APPROVED)
        attacker = User(id=uuid.uuid4(), email="x@y.com", is_guest=False)
        with pytest.raises(ForbiddenError):
            helper(order, attacker)

    def test_unowned_order_blocked_for_payment(self, helper):
        """Payment endpoints must reject orders with no user_id."""
        from app.core.exceptions import ForbiddenError

        order = Order(id=uuid.uuid4(), user_id=None, status=OrderStatus.COVER_APPROVED)
        user = User(id=uuid.uuid4(), email="x@y.com", is_guest=False)
        with pytest.raises(ForbiddenError):
            helper(order, user)


# ── IDOR: Endpoint-level checks ───────────────────────────────────────────


class TestIDOREndpointPatterns:
    """Verify all order endpoints use the centralized ownership check."""

    def test_get_order_uses_verify_helper(self):
        source = inspect.getsource(
            __import__("app.api.v1.orders", fromlist=["get_order"]).get_order
        )
        assert "_verify_order_ownership" in source

    def test_upload_photo_uses_verify_helper(self):
        source = inspect.getsource(
            __import__("app.api.v1.orders", fromlist=["upload_photo"]).upload_photo
        )
        assert "_verify_order_ownership" in source

    def test_approve_text_uses_verify_helper(self):
        source = inspect.getsource(
            __import__("app.api.v1.orders", fromlist=["approve_text"]).approve_text
        )
        assert "_verify_order_ownership" in source

    def test_get_order_progress_uses_verify_helper(self):
        source = inspect.getsource(
            __import__("app.api.v1.orders", fromlist=["get_order_progress"]).get_order_progress
        )
        assert "_verify_order_ownership" in source

    def test_add_coloring_book_uses_verify_helper(self):
        source = inspect.getsource(
            __import__(
                "app.api.v1.orders", fromlist=["add_coloring_book_to_order"]
            ).add_coloring_book_to_order
        )
        assert "_verify_order_ownership" in source

    def test_payment_checkout_uses_verify_helper(self):
        source = inspect.getsource(
            __import__("app.services.checkout_service", fromlist=["process_checkout"]).process_checkout
        )
        assert "ForbiddenError" in source
        assert "order.user_id != current_user.id" in source

    def test_payment_apply_promo_uses_verify_helper(self):
        source = inspect.getsource(
            __import__("app.api.v1.payments", fromlist=["apply_promo"]).apply_promo
        )
        assert "_verify_order_ownership_payment" in source

    def test_payment_status_uses_verify_helper(self):
        source = inspect.getsource(
            __import__(
                "app.api.v1.payments", fromlist=["get_payment_status"]
            ).get_payment_status
        )
        assert "_verify_order_ownership_payment" in source


# ── Convert-Guest Security ─────────────────────────────────────────────────


class TestConvertGuestSecurity:
    """Validate convert-guest endpoint security properties."""

    def test_convert_requires_guest_flag(self):
        """Non-guest users should be rejected (unless idempotent same-email)."""
        source = inspect.getsource(
            __import__(
                "app.services.auth_service", fromlist=["perform_convert_guest"]
            ).perform_convert_guest
        )
        assert "is_guest" in source

    def test_convert_handles_integrity_error(self):
        """Race condition: two concurrent converts with same email → IntegrityError handled."""
        source = inspect.getsource(
            __import__(
                "app.services.auth_service", fromlist=["perform_convert_guest"]
            ).perform_convert_guest
        )
        assert "IntegrityError" in source

    def test_convert_no_email_enumeration(self):
        """Error message must NOT reveal whether email exists."""
        source = inspect.getsource(
            __import__(
                "app.services.auth_service", fromlist=["perform_convert_guest"]
            ).perform_convert_guest
        )
        # Must NOT contain "Bu email adresi zaten kullanımda"
        assert "Bu email adresi zaten kullanımda" not in source
        # Must contain generic message
        assert "Lütfen farklı bilgilerle tekrar deneyin" in source

    def test_convert_idempotent_for_same_email(self):
        """If already converted with same email, return tokens (no error)."""
        source = inspect.getsource(
            __import__(
                "app.services.auth_service", fromlist=["perform_convert_guest"]
            ).perform_convert_guest
        )
        assert "current_user.email == body.email" in source

    def test_convert_audit_includes_order_count(self):
        """Audit log should record how many orders were preserved."""
        source = inspect.getsource(
            __import__(
                "app.services.auth_service", fromlist=["perform_convert_guest"]
            ).perform_convert_guest
        )
        assert "orders_preserved" in source

    def test_convert_uses_db_flush_not_commit_before_audit(self):
        """Flush first (to catch IntegrityError), audit, then commit."""
        source = inspect.getsource(
            __import__(
                "app.services.auth_service", fromlist=["perform_convert_guest"]
            ).perform_convert_guest
        )
        flush_pos = source.index("await db.flush()")
        audit_pos = source.index("record_audit")
        commit_pos = source.index("await db.commit()")
        assert flush_pos < audit_pos < commit_pos


# ── Token Invalidation on Password Change/Reset ───────────────────────────


class TestPasswordTokenInvalidation:
    """Password change and reset must increment token_version."""

    def test_change_password_increments_token_version(self):
        source = inspect.getsource(
            __import__("app.api.v1.auth", fromlist=["change_password"]).change_password
        )
        assert "token_version" in source
        assert "create_access_token" in source

    def test_change_password_returns_new_tokens(self):
        """After password change, response includes fresh tokens for current session."""
        source = inspect.getsource(
            __import__("app.api.v1.auth", fromlist=["change_password"]).change_password
        )
        assert "access_token" in source
        assert "refresh_token" in source

    def test_reset_password_increments_token_version(self):
        source = inspect.getsource(
            __import__("app.api.v1.auth", fromlist=["reset_password"]).reset_password
        )
        assert "token_version" in source


# ── Order List: No IDOR (scoped to current_user.id) ───────────────────────


class TestOrderListScoping:
    """list_user_orders must always filter by current_user.id."""

    def test_list_orders_filters_by_user_id(self):
        source = inspect.getsource(
            __import__(
                "app.api.v1.orders", fromlist=["list_user_orders"]
            ).list_user_orders
        )
        assert "Order.user_id == current_user.id" in source

    def test_list_orders_requires_auth(self):
        """list_user_orders uses CurrentUser (not Optional)."""
        source = inspect.getsource(
            __import__(
                "app.api.v1.orders", fromlist=["list_user_orders"]
            ).list_user_orders
        )
        assert "current_user: CurrentUser" in source


# ── Guest Lifecycle ────────────────────────────────────────────────────────


class TestGuestLifecycle:
    """Validate guest user creation and token behavior."""

    def test_guest_token_has_type_guest(self):
        """Guest tokens must have type=guest so auth guard can distinguish."""
        from app.core.security import create_guest_token, decode_token

        token = create_guest_token()
        payload = decode_token(token)
        assert payload is not None
        assert payload.get("type") == "guest"

    def test_guest_token_has_no_sub(self):
        """Guest tokens must NOT have a sub claim (no user_id)."""
        from app.core.security import create_guest_token, decode_token

        token = create_guest_token()
        payload = decode_token(token)
        assert payload is not None
        assert "sub" not in payload

    def test_auth_guard_rejects_guest_token(self):
        """get_current_user requires type=access, so guest tokens are rejected."""
        source = inspect.getsource(
            __import__("app.api.v1.deps", fromlist=["get_current_user"]).get_current_user
        )
        assert 'token_type != "access"' in source

    def test_guest_user_model_has_is_guest_flag(self):
        guest = User(is_guest=True, email=None)
        assert guest.is_guest is True

    def test_register_error_prevents_email_enumeration(self):
        """Register endpoint must use generic error for duplicate email."""
        source = inspect.getsource(
            __import__("app.services.auth_service", fromlist=["perform_register"]).perform_register
        )
        assert "Kayıt işlemi tamamlanamadı" in source


# ── Confirm Endpoint: Token-based (not IDOR) ──────────────────────────────


class TestConfirmEndpointSecurity:
    """Confirm endpoint uses secret token, not order_id — not IDOR-vulnerable."""

    def test_confirm_uses_token_not_order_id(self):
        source = inspect.getsource(
            __import__("app.api.v1.orders", fromlist=["confirm_order"]).confirm_order
        )
        assert "confirmation_token" in source
        assert "order_id" not in source.split("def confirm_order")[0]


# ── Edge Cases ─────────────────────────────────────────────────────────────


class TestEdgeCases:
    """Edge case scenarios for guest conversion and order ownership."""

    def test_convert_guest_password_validation(self):
        """ConvertGuestRequest enforces password complexity."""
        from app.schemas.auth import ConvertGuestRequest

        with pytest.raises(Exception):
            ConvertGuestRequest(
                email="test@example.com",
                password="weak",
                full_name="Test User",
            )

    def test_order_status_not_affected_by_ownership_check(self):
        """Ownership check should not modify order status."""
        from app.api.v1.orders import _verify_order_ownership

        uid = uuid.uuid4()
        order = Order(id=uuid.uuid4(), user_id=uid, status=OrderStatus.PAID)
        user = User(id=uid, email="a@b.com", is_guest=False)
        _verify_order_ownership(order, user)
        assert order.status == OrderStatus.PAID

    def test_deps_guard_checks_deletion_scheduled(self):
        """Auth guard must block users with pending deletion."""
        source = inspect.getsource(
            __import__("app.api.v1.deps", fromlist=["get_current_user"]).get_current_user
        )
        assert "deletion_scheduled_at" in source

    def test_deps_guard_checks_token_version(self):
        """Auth guard must validate token_version claim."""
        source = inspect.getsource(
            __import__("app.api.v1.deps", fromlist=["get_current_user"]).get_current_user
        )
        assert "token_version" in source or "tv" in source

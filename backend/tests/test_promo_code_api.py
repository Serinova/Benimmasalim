"""Integration tests for promo code API endpoints.

Requires a running test PostgreSQL database (see conftest.py).
Tests admin CRUD, concurrent consumption, and validation edge cases.
"""

import asyncio
import uuid
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token
from app.models.promo_code import PromoCode
from app.models.user import User, UserRole
from app.services.promo_code_service import consume_promo_code, generate_promo_code

# ─── Fixtures ────────────────────────────────────────────────────


@pytest_asyncio.fixture
async def admin_user(db_session: AsyncSession) -> User:
    """Create an admin user for testing."""
    user = User(
        id=uuid.uuid4(),
        email=f"admin_{uuid.uuid4().hex[:6]}@test.com",
        full_name="Test Admin",
        hashed_password="fakehash",
        role=UserRole.ADMIN,
        is_active=True,
    )
    db_session.add(user)
    await db_session.flush()
    return user


@pytest.fixture
def admin_token(admin_user: User) -> str:
    """Create JWT token for admin user."""
    return create_access_token(str(admin_user.id))


@pytest_asyncio.fixture
async def sample_promo(db_session: AsyncSession) -> PromoCode:
    """Create a sample active promo code."""
    promo = PromoCode(
        code=f"TEST{uuid.uuid4().hex[:6].upper()}",
        discount_type="PERCENT",
        discount_value=Decimal("20"),
        usage_limit=10,
        used_count=0,
        is_active=True,
        valid_from=datetime.now(UTC) - timedelta(days=1),
        valid_until=datetime.now(UTC) + timedelta(days=30),
    )
    db_session.add(promo)
    await db_session.flush()
    return promo


@pytest_asyncio.fixture
async def expired_promo(db_session: AsyncSession) -> PromoCode:
    """Create an expired promo code."""
    promo = PromoCode(
        code=f"EXP{uuid.uuid4().hex[:6].upper()}",
        discount_type="AMOUNT",
        discount_value=Decimal("50"),
        usage_limit=100,
        used_count=0,
        is_active=True,
        valid_until=datetime.now(UTC) - timedelta(days=1),
    )
    db_session.add(promo)
    await db_session.flush()
    return promo


@pytest_asyncio.fixture
async def single_use_promo(db_session: AsyncSession) -> PromoCode:
    """Create a promo code with usage_limit=1 for concurrency testing."""
    promo = PromoCode(
        code=f"ONCE{uuid.uuid4().hex[:6].upper()}",
        discount_type="PERCENT",
        discount_value=Decimal("10"),
        usage_limit=1,
        used_count=0,
        is_active=True,
    )
    db_session.add(promo)
    await db_session.flush()
    return promo


# ─── Code Generation ────────────────────────────────────────────


class TestGeneratePromoCode:
    """Tests for generate_promo_code."""

    @pytest.mark.asyncio
    async def test_generates_unique_code(self, db_session: AsyncSession):
        """Generated code should be unique in the database."""
        code = await generate_promo_code(db_session)
        assert len(code) == 8
        assert code.isalnum()
        assert code == code.upper()

    @pytest.mark.asyncio
    async def test_generates_with_prefix(self, db_session: AsyncSession):
        """Generated code with prefix should start with prefix."""
        code = await generate_promo_code(db_session, prefix="VIP")
        assert code.startswith("VIP")
        assert len(code) == 3 + 8  # prefix + random part


# ─── Concurrent Consumption ──────────────────────────────────────


class TestConcurrentConsume:
    """Tests for atomic promo code consumption under concurrency."""

    @pytest.mark.asyncio
    async def test_single_use_concurrent_consume(
        self, single_use_promo: PromoCode, db_session: AsyncSession
    ):
        """
        usage_limit=1: Two concurrent consume calls should result in
        exactly one success and one failure.
        """
        results = await asyncio.gather(
            consume_promo_code(single_use_promo.id, db_session),
            consume_promo_code(single_use_promo.id, db_session),
        )

        success_count = sum(1 for r in results if r is True)

        # At least one should succeed; total successes must not exceed usage_limit
        assert success_count >= 1
        assert success_count <= single_use_promo.usage_limit

    @pytest.mark.asyncio
    async def test_consume_active_promo(
        self, sample_promo: PromoCode, db_session: AsyncSession
    ):
        """Active promo with remaining uses should consume successfully."""
        result = await consume_promo_code(sample_promo.id, db_session)
        assert result is True

    @pytest.mark.asyncio
    async def test_consume_inactive_promo_fails(
        self, db_session: AsyncSession
    ):
        """Inactive promo should fail to consume."""
        promo = PromoCode(
            code=f"INACT{uuid.uuid4().hex[:6].upper()}",
            discount_type="PERCENT",
            discount_value=Decimal("10"),
            usage_limit=10,
            used_count=0,
            is_active=False,
        )
        db_session.add(promo)
        await db_session.flush()

        result = await consume_promo_code(promo.id, db_session)
        assert result is False


# ─── Admin CRUD (HTTP) ───────────────────────────────────────────


class TestAdminPromoCRUD:
    """Tests for admin promo code HTTP endpoints."""

    @pytest.mark.asyncio
    async def test_create_promo(self, client, admin_token: str):
        """POST /admin/promo-codes should create a promo code."""
        response = await client.post(
            "/api/v1/admin/promo-codes",
            json={
                "code": "NEWCODE25",
                "discount_type": "PERCENT",
                "discount_value": 25,
                "usage_limit": 50,
            },
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == "NEWCODE25"
        assert data["discount_type"] == "PERCENT"
        assert data["discount_value"] == "25.00" or data["discount_value"] == 25

    @pytest.mark.asyncio
    async def test_create_auto_code(self, client, admin_token: str):
        """POST without code should auto-generate one."""
        response = await client.post(
            "/api/v1/admin/promo-codes",
            json={
                "discount_type": "AMOUNT",
                "discount_value": 50,
                "usage_limit": 10,
            },
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["code"]) == 8

    @pytest.mark.asyncio
    async def test_list_promos(self, client, admin_token: str):
        """GET /admin/promo-codes should return paginated list."""
        response = await client.get(
            "/api/v1/admin/promo-codes",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data

    @pytest.mark.asyncio
    async def test_duplicate_code_conflict(self, client, admin_token: str):
        """Creating a promo with duplicate code should return 409."""
        code = f"DUP{uuid.uuid4().hex[:6].upper()}"
        await client.post(
            "/api/v1/admin/promo-codes",
            json={
                "code": code,
                "discount_type": "PERCENT",
                "discount_value": 10,
                "usage_limit": 1,
            },
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        response = await client.post(
            "/api/v1/admin/promo-codes",
            json={
                "code": code,
                "discount_type": "PERCENT",
                "discount_value": 10,
                "usage_limit": 1,
            },
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 409

    @pytest.mark.asyncio
    async def test_soft_delete(self, client, admin_token: str):
        """DELETE should soft-delete (set is_active=False)."""
        # Create
        resp = await client.post(
            "/api/v1/admin/promo-codes",
            json={
                "discount_type": "PERCENT",
                "discount_value": 5,
                "usage_limit": 1,
            },
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        promo_id = resp.json()["id"]

        # Delete
        del_resp = await client.delete(
            f"/api/v1/admin/promo-codes/{promo_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert del_resp.status_code == 200
        assert del_resp.json()["is_active"] is False

    @pytest.mark.asyncio
    async def test_unauthorized_access(self, client):
        """Endpoints without token should return 401."""
        response = await client.get("/api/v1/admin/promo-codes")
        assert response.status_code in (401, 403)

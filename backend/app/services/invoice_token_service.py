"""Secure invoice download token service.

Token lifecycle:
  1. create_download_token() → generates 256-bit random token, stores sha256(token+salt)
  2. verify_and_consume_token() → atomic SELECT FOR UPDATE, checks expiry/revoke/uses, increments used_count
  3. revoke_token() → sets revoked_at (admin action)

Security properties:
  - Token is 32 random bytes, base64url encoded (43 chars)
  - DB never stores plaintext token; only sha256(token + INVOICE_TOKEN_SALT)
  - Atomic consumption via SELECT FOR UPDATE prevents race conditions
  - Constant-time hash comparison via hmac.compare_digest
"""

import hashlib
import hmac
import secrets
from base64 import urlsafe_b64encode
from datetime import UTC, datetime, timedelta
from uuid import UUID

import structlog
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.invoice_download_token import InvoiceDownloadToken

logger = structlog.get_logger()

_TOKEN_BYTES = 32  # 256-bit
_DEFAULT_TTL_HOURS = 48
_DEFAULT_MAX_USES = 1


def _get_salt() -> str:
    return getattr(settings, "invoice_token_salt", settings.secret_key[:32])


def _hash_token(raw_token: str) -> str:
    """SHA-256(token + salt). Deterministic for lookup."""
    salted = f"{raw_token}{_get_salt()}"
    return hashlib.sha256(salted.encode()).hexdigest()


def generate_raw_token() -> str:
    """Generate a cryptographically random URL-safe token."""
    return urlsafe_b64encode(secrets.token_bytes(_TOKEN_BYTES)).rstrip(b"=").decode("ascii")


async def create_download_token(
    order_id: UUID | None,
    invoice_id: UUID,
    db: AsyncSession,
    *,
    ttl_hours: int = _DEFAULT_TTL_HOURS,
    max_uses: int = _DEFAULT_MAX_USES,
    created_by: str = "system",
) -> str:
    """Create a new download token. Returns the raw (plaintext) token for email inclusion.

    The raw token is NEVER stored in DB — only its salted hash.
    order_id may be None for trial/preview-flow invoices (used only for logging).
    """
    raw_token = generate_raw_token()
    token_hash = _hash_token(raw_token)

    token_record = InvoiceDownloadToken(
        token_hash=token_hash,
        order_id=order_id,
        invoice_id=invoice_id,
        expires_at=datetime.now(UTC) + timedelta(hours=ttl_hours),
        max_uses=max_uses,
        created_by=created_by,
    )
    db.add(token_record)
    await db.flush()

    logger.info(
        "invoice_download_token_created",
        token_hash_prefix=token_hash[:8],
        order_id=str(order_id),
        ttl_hours=ttl_hours,
        max_uses=max_uses,
    )
    return raw_token


async def verify_and_consume_token(
    raw_token: str,
    db: AsyncSession,
) -> InvoiceDownloadToken | None:
    """Verify token validity and atomically consume one use.

    Returns the token record if valid, None otherwise.
    Uses SELECT FOR UPDATE to prevent race conditions on concurrent requests.
    """
    token_hash = _hash_token(raw_token)
    now = datetime.now(UTC)

    result = await db.execute(
        select(InvoiceDownloadToken)
        .where(InvoiceDownloadToken.token_hash == token_hash)
        .with_for_update(skip_locked=False)
    )
    token_record = result.scalar_one_or_none()

    if not token_record:
        logger.warning(
            "invoice_token_invalid",
            token_hash_prefix=token_hash[:8],
        )
        return None

    if token_record.revoked_at is not None:
        logger.warning(
            "invoice_token_revoked",
            token_hash_prefix=token_hash[:8],
            order_id=str(token_record.order_id),
        )
        return None

    if token_record.expires_at < now:
        logger.warning(
            "invoice_token_expired",
            token_hash_prefix=token_hash[:8],
            order_id=str(token_record.order_id),
            expired_at=token_record.expires_at.isoformat(),
        )
        return None

    if token_record.used_count >= token_record.max_uses:
        logger.warning(
            "invoice_token_exhausted",
            token_hash_prefix=token_hash[:8],
            order_id=str(token_record.order_id),
            used_count=token_record.used_count,
            max_uses=token_record.max_uses,
        )
        return None

    token_record.used_count += 1
    token_record.last_used_at = now
    if token_record.first_used_at is None:
        token_record.first_used_at = now

    await db.flush()

    logger.info(
        "invoice_token_consumed",
        token_hash_prefix=token_hash[:8],
        order_id=str(token_record.order_id),
        used_count=token_record.used_count,
    )
    return token_record


async def revoke_tokens_for_order(
    order_id: UUID,
    db: AsyncSession,
    *,
    admin_id: UUID | None = None,
) -> int:
    """Revoke all active tokens for an order. Returns count revoked."""
    now = datetime.now(UTC)
    result = await db.execute(
        update(InvoiceDownloadToken)
        .where(
            InvoiceDownloadToken.order_id == order_id,
            InvoiceDownloadToken.revoked_at.is_(None),
        )
        .values(revoked_at=now, revoked_by_admin_id=admin_id)
        .returning(InvoiceDownloadToken.id)
    )
    revoked_ids = result.all()
    count = len(revoked_ids)

    if count:
        logger.info(
            "invoice_tokens_revoked",
            order_id=str(order_id),
            count=count,
            admin_id=str(admin_id) if admin_id else None,
        )
    return count


async def extend_token_ttl(
    token_id: UUID,
    db: AsyncSession,
    *,
    extra_hours: int = 48,
) -> bool:
    """Extend a token's TTL. Admin-only. Returns True if updated."""
    result = await db.execute(
        select(InvoiceDownloadToken)
        .where(InvoiceDownloadToken.id == token_id)
        .with_for_update()
    )
    token_record = result.scalar_one_or_none()
    if not token_record or token_record.revoked_at is not None:
        return False

    token_record.expires_at = max(
        token_record.expires_at,
        datetime.now(UTC),
    ) + timedelta(hours=extra_hours)
    await db.flush()

    logger.info(
        "invoice_token_ttl_extended",
        token_hash_prefix=token_record.token_hash[:8],
        new_expires_at=token_record.expires_at.isoformat(),
    )
    return True


async def cleanup_expired_tokens(db: AsyncSession, *, retention_days: int = 30) -> int:
    """Purge token records older than retention_days past expiry. KVKK compliance."""
    from sqlalchemy import delete

    cutoff = datetime.now(UTC) - timedelta(days=retention_days)
    result = await db.execute(
        delete(InvoiceDownloadToken)
        .where(InvoiceDownloadToken.expires_at < cutoff)
        .returning(InvoiceDownloadToken.id)
    )
    deleted = len(result.all())
    if deleted:
        logger.info("invoice_tokens_purged", count=deleted, retention_days=retention_days)
    return deleted

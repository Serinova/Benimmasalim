"""Security utilities: JWT (PyJWT), password hashing (bcrypt), token blacklist."""

import hashlib
import re
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

import bcrypt
import jwt

from app.config import settings

# ---------------------------------------------------------------------------
# Password validation
# ---------------------------------------------------------------------------

_COMMON_PASSWORDS: frozenset[str] = frozenset({
    "12345678", "password", "password1", "qwerty12", "abc12345",
    "11111111", "123456789", "1234567890", "iloveyou", "sunshine",
    "princess", "football", "charlie1", "shadow12", "master12",
})

_SPECIAL_CHARS_RE = re.compile(r'[!@#$%^&*(),.?":{}|<>_\-+=\[\]~`]')


def validate_password_strength(v: str, *, check_common: bool = False) -> str:
    """Enforce password complexity: upper + lower + digit + special char.

    Args:
        v: Password string (must already pass min_length=8 Pydantic constraint).
        check_common: If True, reject passwords in the common-passwords blocklist.
    """
    if not re.search(r"[A-Z]", v):
        raise ValueError("Şifre en az bir büyük harf içermelidir")
    if not re.search(r"[a-z]", v):
        raise ValueError("Şifre en az bir küçük harf içermelidir")
    if not re.search(r"\d", v):
        raise ValueError("Şifre en az bir rakam içermelidir")
    if not _SPECIAL_CHARS_RE.search(v):
        raise ValueError("Şifre en az bir özel karakter içermelidir (!@#$%^&*...)")
    if check_common and v.lower() in _COMMON_PASSWORDS:
        raise ValueError("Bu şifre çok yaygın, lütfen daha güçlü bir şifre seçin")
    return v


# ---------------------------------------------------------------------------
# Password hashing (bcrypt)
# ---------------------------------------------------------------------------


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return bcrypt.checkpw(
        plain_password.encode("utf-8"),
        hashed_password.encode("utf-8"),
    )


def get_password_hash(password: str) -> str:
    """Generate bcrypt hash for a password."""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


# ---------------------------------------------------------------------------
# JWT Token creation / decoding (PyJWT)
# ---------------------------------------------------------------------------

_ISSUER = "benimmasalim"
_AUDIENCE = "benimmasalim-api"


def create_access_token(
    subject: UUID | str,
    expires_delta: timedelta | None = None,
    additional_claims: dict[str, Any] | None = None,
    token_version: int = 0,
) -> str:
    """Create a JWT access token with iss/aud/iat claims + token_version."""
    now = datetime.now(UTC)
    expire = now + (expires_delta or timedelta(minutes=settings.jwt_access_token_expire_minutes))

    to_encode: dict[str, Any] = {
        "sub": str(subject),
        "exp": expire,
        "iat": now,
        "iss": _ISSUER,
        "aud": _AUDIENCE,
        "type": "access",
        "tv": token_version,
    }

    if additional_claims:
        to_encode.update(additional_claims)

    return jwt.encode(
        to_encode,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )


def create_refresh_token(subject: UUID | str, token_version: int = 0) -> str:
    """Create a JWT refresh token with token_version."""
    now = datetime.now(UTC)
    expire = now + timedelta(days=settings.jwt_refresh_token_expire_days)

    to_encode = {
        "sub": str(subject),
        "exp": expire,
        "iat": now,
        "iss": _ISSUER,
        "aud": _AUDIENCE,
        "type": "refresh",
        "tv": token_version,
    }

    return jwt.encode(
        to_encode,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )


def decode_token(token: str) -> dict[str, Any] | None:
    """Decode and validate a JWT token (checks exp, iss, aud)."""
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
            issuer=_ISSUER,
            audience=_AUDIENCE,
        )
        return payload
    except jwt.PyJWTError:
        return None


def create_guest_token() -> str:
    """Create a temporary guest token for checkout without registration (24h)."""
    now = datetime.now(UTC)
    expire = now + timedelta(hours=24)

    to_encode = {
        "type": "guest",
        "exp": expire,
        "iat": now,
        "iss": _ISSUER,
        "aud": _AUDIENCE,
    }

    return jwt.encode(
        to_encode,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )


# ---------------------------------------------------------------------------
# Token blacklist (Redis-backed, async) — used by /auth/logout
# ---------------------------------------------------------------------------

_TOKEN_BLACKLIST_PREFIX = "token_blacklist:"

# Shared async Redis connection — lazy-initialized, reused across calls.
_async_redis: "redis.asyncio.Redis | None" = None


async def _get_async_redis():
    """Get or create a shared async Redis connection for token ops."""
    global _async_redis
    if _async_redis is not None:
        return _async_redis
    try:
        import redis.asyncio as aioredis

        _async_redis = aioredis.from_url(
            str(settings.redis_url),
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=5,
        )
        await _async_redis.ping()
        return _async_redis
    except Exception:
        _async_redis = None
        return None


async def blacklist_token(token: str, expires_in_seconds: int = 7200) -> bool:
    """Add a token's hash to the blacklist. Returns True on success."""
    r = await _get_async_redis()
    if not r:
        return False
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    try:
        await r.setex(f"{_TOKEN_BLACKLIST_PREFIX}{token_hash}", expires_in_seconds, "1")
        return True
    except Exception:
        return False


async def is_token_blacklisted(token: str) -> bool:
    """Check if a token is blacklisted."""
    r = await _get_async_redis()
    if not r:
        return False
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    try:
        return await r.exists(f"{_TOKEN_BLACKLIST_PREFIX}{token_hash}") > 0
    except Exception:
        return False

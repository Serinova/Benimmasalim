"""Security utilities: JWT (PyJWT), password hashing (bcrypt), token blacklist."""

import hashlib
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

import bcrypt
import jwt

from app.config import settings

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
) -> str:
    """Create a JWT access token with iss/aud/iat claims."""
    now = datetime.now(UTC)
    expire = now + (expires_delta or timedelta(minutes=settings.jwt_access_token_expire_minutes))

    to_encode: dict[str, Any] = {
        "sub": str(subject),
        "exp": expire,
        "iat": now,
        "iss": _ISSUER,
        "aud": _AUDIENCE,
        "type": "access",
    }

    if additional_claims:
        to_encode.update(additional_claims)

    return jwt.encode(
        to_encode,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )


def create_refresh_token(subject: UUID | str) -> str:
    """Create a JWT refresh token."""
    now = datetime.now(UTC)
    expire = now + timedelta(days=settings.jwt_refresh_token_expire_days)

    to_encode = {
        "sub": str(subject),
        "exp": expire,
        "iat": now,
        "iss": _ISSUER,
        "aud": _AUDIENCE,
        "type": "refresh",
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
# Token blacklist (Redis-backed) — used by /auth/logout
# ---------------------------------------------------------------------------

_TOKEN_BLACKLIST_PREFIX = "token_blacklist:"


def _get_redis():
    """Lazy Redis connection for token blacklist."""
    import redis as _redis

    try:
        return _redis.Redis.from_url(str(settings.redis_url), decode_responses=True)
    except Exception:
        return None


def blacklist_token(token: str, expires_in_seconds: int = 7200) -> bool:
    """Add a token's hash to the blacklist. Returns True on success."""
    r = _get_redis()
    if not r:
        return False
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    try:
        r.setex(f"{_TOKEN_BLACKLIST_PREFIX}{token_hash}", expires_in_seconds, "1")
        return True
    except Exception:
        return False


def is_token_blacklisted(token: str) -> bool:
    """Check if a token is blacklisted."""
    r = _get_redis()
    if not r:
        return False
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    try:
        return r.exists(f"{_TOKEN_BLACKLIST_PREFIX}{token_hash}") > 0
    except Exception:
        return False

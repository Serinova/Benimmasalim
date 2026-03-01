"""
Global Rate Limiting Middleware for FastAPI.

Provides IP-based and endpoint-specific rate limiting
to protect the application from abuse.

Uses async Redis when available (production) and falls back to
in-memory storage (development / single-worker).
"""

import asyncio
import time
from collections import defaultdict

import structlog
from starlette.responses import JSONResponse

from app.config import settings

logger = structlog.get_logger()


# =============================================================================
# STORAGE BACKENDS
# =============================================================================


class InMemoryRateLimitStorage:
    """In-memory rate limit storage. Only works within a single process."""

    is_async = False

    def __init__(self) -> None:
        self.requests: dict[str, list[float]] = defaultdict(list)
        self.endpoint_requests: dict[str, list[float]] = defaultdict(list)

    def _cleanup(self, key: str, window_seconds: int) -> None:
        cutoff = time.time() - window_seconds
        if key in self.requests:
            self.requests[key] = [ts for ts in self.requests[key] if ts > cutoff]
        if key in self.endpoint_requests:
            self.endpoint_requests[key] = [ts for ts in self.endpoint_requests[key] if ts > cutoff]

    async def get_request_count(self, key: str, window_seconds: int) -> int:
        self._cleanup(key, window_seconds)
        return len(self.requests.get(key, []))

    async def get_endpoint_count(self, key: str, window_seconds: int) -> int:
        self._cleanup(key, window_seconds)
        return len(self.endpoint_requests.get(key, []))

    async def record_request(self, ip: str, endpoint: str, *, skip_endpoint_record: bool = False) -> None:
        now = time.time()
        self.requests[ip].append(now)
        if not skip_endpoint_record:
            self.endpoint_requests[f"{ip}:{endpoint}"].append(now)

    async def scan_and_delete(self, pattern: str) -> int:
        """Delete keys matching pattern (in-memory variant)."""
        deleted = 0
        if ":" in pattern:
            # Endpoint-specific pattern
            keys_to_remove = [k for k in self.endpoint_requests if pattern.replace("*", "") in k]
            for key in keys_to_remove:
                del self.endpoint_requests[key]
                deleted += 1
        # Also check global requests
        keys_to_remove = [k for k in self.requests if pattern.replace("*", "") in k]
        for key in keys_to_remove:
            del self.requests[key]
            deleted += 1
        return deleted

    async def clear_all(self) -> int:
        self.requests.clear()
        self.endpoint_requests.clear()
        return 0


class AsyncRedisRateLimitStorage:
    """Async Redis-backed rate limit storage. Works across multiple workers/containers."""

    is_async = True

    def __init__(self) -> None:
        import redis.asyncio as aioredis

        redis_url = str(settings.redis_url)
        self._redis = aioredis.from_url(
            redis_url,
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=5,
        )
        self._verified = False

    async def _ensure_connected(self) -> None:
        if not self._verified:
            await self._redis.ping()
            self._verified = True
            logger.info("RateLimiter connected to async Redis")

    def _key(self, prefix: str, identifier: str) -> str:
        return f"rl:{prefix}:{identifier}"

    async def get_request_count(self, key: str, window_seconds: int) -> int:
        rk = self._key("global", key)
        now = time.time()
        cutoff = now - window_seconds
        await self._redis.zremrangebyscore(rk, "-inf", cutoff)
        return int(await self._redis.zcard(rk))

    async def get_endpoint_count(self, key: str, window_seconds: int) -> int:
        rk = self._key("ep", key)
        now = time.time()
        cutoff = now - window_seconds
        await self._redis.zremrangebyscore(rk, "-inf", cutoff)
        return int(await self._redis.zcard(rk))

    async def record_request(self, ip: str, endpoint: str, *, skip_endpoint_record: bool = False) -> None:
        now = time.time()
        async with self._redis.pipeline(transaction=False) as pipe:
            global_key = self._key("global", ip)
            pipe.zadd(global_key, {str(now): now})
            pipe.expire(global_key, 7200)

            if not skip_endpoint_record:
                ep_key = self._key("ep", f"{ip}:{endpoint}")
                pipe.zadd(ep_key, {str(now): now})
                pipe.expire(ep_key, 7200)

            await pipe.execute()

    async def scan_and_delete(self, pattern: str) -> int:
        """Delete keys matching a pattern using async SCAN."""
        deleted = 0
        async for key in self._redis.scan_iter(pattern):
            await self._redis.delete(key)
            deleted += 1
        return deleted

    async def clear_all(self) -> int:
        """Delete all rate-limit keys."""
        deleted = 0
        async for key in self._redis.scan_iter("rl:*"):
            await self._redis.delete(key)
            deleted += 1
        return deleted


# Lazy-init storage: created on first use inside the async event loop
_storage: InMemoryRateLimitStorage | AsyncRedisRateLimitStorage | None = None
_storage_init_failed: bool = False
_storage_last_retry: float = 0.0  # timestamp of last retry attempt
_STORAGE_RETRY_INTERVAL = 30.0  # retry Redis connection every 30 seconds
_storage_lock = asyncio.Lock()


async def _get_storage() -> InMemoryRateLimitStorage | AsyncRedisRateLimitStorage | None:
    """Get or create the rate limit storage (thread-safe lazy init).

    Returns None when Redis is unavailable in production — middleware will
    skip rate limiting entirely (fail-open) rather than using per-worker
    in-memory counters that multi-instance deployments can bypass.

    Retries Redis connection every 30s so a temporary blip doesn't permanently
    disable rate limiting until restart.
    """
    import time

    global _storage, _storage_init_failed, _storage_last_retry
    if _storage is not None:
        return _storage
    if _storage_init_failed:
        # Retry periodically instead of permanently giving up
        if time.monotonic() - _storage_last_retry < _STORAGE_RETRY_INTERVAL:
            return None

    async with _storage_lock:
        # Double-check after acquiring lock
        if _storage is not None:
            return _storage
        if _storage_init_failed:
            if time.monotonic() - _storage_last_retry < _STORAGE_RETRY_INTERVAL:
                return None

        if settings.app_env == "development":
            _storage = InMemoryRateLimitStorage()
            return _storage
        try:
            s = AsyncRedisRateLimitStorage()
            await s._ensure_connected()
            _storage = s
            if _storage_init_failed:
                logger.info("Redis reconnected — rate limiting RE-ENABLED")
                _storage_init_failed = False
        except Exception:
            logger.error(
                "CRITICAL: Redis unavailable in production — rate limiting DISABLED. "
                "In-memory fallback skipped to prevent multi-worker bypass. "
                "Will retry in %ds.",
                _STORAGE_RETRY_INTERVAL,
            )
            _storage_init_failed = True
            _storage_last_retry = time.monotonic()
        return _storage


# =============================================================================
# RATE LIMIT CONFIGURATION
# =============================================================================

# Endpoint-specific rate limits (requests, window_seconds)
STORY_ENDPOINT_KEY = "/api/v1/ai/test-story-structured"

ENDPOINT_LIMITS = {
    # AI Story Generation - expensive operation (admin/editor exempt)
    STORY_ENDPOINT_KEY: (
        getattr(settings, "rate_limit_draft", 25),  # 25/hour anonim; admin/editor sınırsız
        3600,  # 1 hour window
    ),
    # AI Image Generation - expensive operation
    "/api/v1/ai/test-image-fal": (
        30,  # 30 per hour
        3600,
    ),
    "/api/v1/ai/test-image-flash": (
        30,
        3600,
    ),
    # Voice cloning - very expensive
    "/api/v1/ai/clone-voice-direct": (
        5,  # 5 per hour
        3600,
    ),
    "/api/v1/ai/clone-voice": (
        5,
        3600,
    ),
    # Order submission
    "/api/v1/orders/send-preview": (
        getattr(settings, "rate_limit_order", 10),  # 10 per hour
        3600,
    ),
    "/api/v1/orders/submit-preview-async": (
        getattr(settings, "rate_limit_order", 10),
        3600,
    ),
    # Login - prevent brute force
    "/api/v1/auth/login": (
        getattr(settings, "rate_limit_login", 5),  # 5 per 15 min
        900,  # 15 min window
    ),
    # Registration
    "/api/v1/auth/register": (5, 3600),  # 5 per hour
    # Password reset — prevent brute force / email enumeration
    "/api/v1/auth/forgot-password": (5, 3600),  # 5 per hour per IP
    "/api/v1/auth/reset-password": (10, 900),   # 10 per 15 min per IP
    # Trial creation - expensive AI generation
    "/api/v1/trials/create": (getattr(settings, "rate_limit_trial_create", 15), 3600),
    "/api/v1/trials/generate-preview": (getattr(settings, "rate_limit_trial_preview", 20), 3600),
    # Payment checkout — prevent replay attacks
    "/api/v1/payments/checkout": (5, 3600),  # 5 per hour per IP
    # Payment verification
    "/api/v1/payments/verify-iyzico": (10, 3600),  # 10 per hour per IP
    # Promo code validation
    "/api/v1/payments/validate-promo": (20, 3600),  # 20 per hour
    # Lead capture
    "/api/v1/leads/capture": (10, 3600),  # 10 per hour
    # Temp image upload — unauthenticated, limit abuse
    "/api/v1/ai/upload/temp-image": (10, 3600),  # 10 per hour per IP
    # Trial status polling — lightweight DB read, needs high limit for preview flow
    "/api/v1/trials/status": (600, 3600),  # 600 per hour (generous for polling)
    # Trial payment endpoints — specific limits to avoid falling into generic /api/v1/trials bucket
    "/api/v1/trials/create-payment": (60, 3600),  # 60 per hour (covers /{id}/create-payment)
    "/api/v1/trials/complete": (60, 3600),        # 60 per hour (covers /{id}/complete)
    "/api/v1/trials/verify-payment": (60, 3600),   # 60 per hour (covers /{id}/verify-payment)
    "/api/v1/trials/preview": (50, 3600),           # 50 per hour (covers /{id}/preview GET polling)
    # Trial retry — re-queues expensive image generation (generic catch-all)
    "/api/v1/trials": (30, 3600),  # 30 per hour per IP
    # Webhook endpoints — signature-verified but still rate-limit against replay floods
    "/api/v1/webhooks/payment": (30, 3600),  # 30 per hour
    "/api/v1/webhooks/elevenlabs": (20, 3600),  # 20 per hour
    # Voice preview — calls ElevenLabs API
    "/api/v1/ai/preview-voice": (20, 3600),  # 20 per hour per IP
    # Voice sample upload
    "/api/v1/ai/upload-voice-sample": (10, 3600),  # 10 per hour per IP
    # Invoice token download — public, rate-limit against brute-force
    "/api/v1/invoice": (10, 300),  # 10 per 5 min per IP
}

# Endpoints where authenticated admin/editor skip the endpoint limit (still count global)
ADMIN_EXEMPT_ENDPOINTS = frozenset({
    STORY_ENDPOINT_KEY,
})


def _is_story_endpoint(path: str) -> bool:
    """True if path is the story generation endpoint."""
    return path == STORY_ENDPOINT_KEY or path.rstrip("/").endswith("ai/test-story-structured")


def _endpoint_limit_key(path: str) -> str:
    """Canonical key for ENDPOINT_LIMITS lookup.

    Handles dynamic path parameters by falling back to prefix matching
    (e.g. ``/api/v1/trials/abc-123/retry`` → ``/api/v1/trials``).

    Special case: trial status polling gets a dedicated high-limit bucket
    (``/api/v1/trials/{id}/status`` → ``/api/v1/trials/status``).
    """
    if _is_story_endpoint(path):
        return STORY_ENDPOINT_KEY
    # Exact match first
    if path in ENDPOINT_LIMITS:
        return path
    # Trial status polling — lightweight GET, needs separate high-limit bucket
    if path.startswith("/api/v1/trials/") and path.endswith("/status"):
        return "/api/v1/trials/status"
    # Trial payment endpoints — must be checked before generic /api/v1/trials catch-all
    if path.startswith("/api/v1/trials/") and path.endswith("/create-payment"):
        return "/api/v1/trials/create-payment"
    if path.startswith("/api/v1/trials/") and path.endswith("/complete"):
        return "/api/v1/trials/complete"
    if path.startswith("/api/v1/trials/") and path.endswith("/verify-payment"):
        return "/api/v1/trials/verify-payment"
    if path.startswith("/api/v1/trials/") and path.endswith("/preview"):
        return "/api/v1/trials/preview"
    # Prefix match for dynamic paths (e.g. /api/v1/ai/orders/{id}/regenerate-cover)
    for key in ENDPOINT_LIMITS:
        if path.startswith(key + "/"):
            return key
    return path

# Global rate limit (all endpoints combined)
GLOBAL_LIMIT = (
    1000,  # 1000 requests
    3600,  # per hour
)


# =============================================================================
# MIDDLEWARE
# =============================================================================


class RateLimitMiddleware:
    """Pure ASGI rate limiting middleware (no BaseHTTPMiddleware — avoids streaming deadlocks).

    All Redis calls are fully async — no event loop blocking.
    """

    def __init__(self, app) -> None:
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)

        if settings.app_env == "development" and not getattr(settings, "is_production", False):
            return await self.app(scope, receive, send)

        try:
            path: str = scope.get("path", "")
            if self._should_skip(path):
                return await self.app(scope, receive, send)

            storage = await _get_storage()
            if storage is None:
                # Redis unavailable — skip rate limiting (fail-open)
                logger.warning("rate_limit_skipped: Redis unavailable, passing request through")
                return await self.app(scope, receive, send)

            client_ip = self._get_client_ip(scope)
            endpoint = _endpoint_limit_key(path)

            global_count = await storage.get_request_count(client_ip, GLOBAL_LIMIT[1])
            if global_count >= GLOBAL_LIMIT[0]:
                logger.warning("Global rate limit exceeded", ip=client_ip, count=global_count, limit=GLOBAL_LIMIT[0])
                return await self._send_429(scope, receive, send, GLOBAL_LIMIT[1])

            is_admin_exempt = (endpoint in ADMIN_EXEMPT_ENDPOINTS) and self._is_admin_request(scope)

            if endpoint in ENDPOINT_LIMITS and not is_admin_exempt:
                limit, window = ENDPOINT_LIMITS[endpoint]
                endpoint_key = f"{client_ip}:{endpoint}"
                endpoint_count = await storage.get_endpoint_count(endpoint_key, window)
                if endpoint_count >= limit:
                    logger.warning("Endpoint rate limit exceeded", ip=client_ip, endpoint=endpoint, count=endpoint_count, limit=limit)
                    return await self._send_429(scope, receive, send, window)

            await storage.record_request(client_ip, endpoint, skip_endpoint_record=is_admin_exempt)

            need_headers = endpoint in ENDPOINT_LIMITS and not is_admin_exempt

            if need_headers:
                limit, window = ENDPOINT_LIMITS[endpoint]
                endpoint_key = f"{client_ip}:{endpoint}"

                # Capture storage ref for closure
                _st = storage

                async def send_with_headers(message):
                    if message["type"] == "http.response.start":
                        remaining = limit - await _st.get_endpoint_count(endpoint_key, window)
                        extra = [
                            (b"x-ratelimit-limit", str(limit).encode()),
                            (b"x-ratelimit-remaining", str(max(0, remaining)).encode()),
                            (b"x-ratelimit-reset", str(int(time.time() + window)).encode()),
                        ]
                        headers = list(message.get("headers", []))
                        headers.extend(extra)
                        message = {**message, "headers": headers}
                    await send(message)

                return await self.app(scope, receive, send_with_headers)

            return await self.app(scope, receive, send)
        except Exception:
            logger.exception("Rate limiter error, passing request through")
            return await self.app(scope, receive, send)

    # -- helpers (scope-based, no Request object needed) --

    def _is_admin_request(self, scope) -> bool:
        auth_value = None
        for name, val in scope.get("headers", []):
            if name == b"authorization":
                auth_value = val.decode("latin-1")
                break
        if not auth_value or not auth_value.startswith("Bearer "):
            return False
        token = auth_value[7:].strip()
        if not token:
            return False
        try:
            from app.core.security import decode_token
            payload = decode_token(token)
            if payload is None:
                return False
            role = payload.get("role")
            return str(role).lower() in ("admin", "editor") if role else False
        except Exception:
            return False

    def _get_client_ip(self, scope) -> str:
        if getattr(settings, "behind_proxy", False):
            for name, val in scope.get("headers", []):
                if name == b"x-forwarded-for":
                    return val.decode("latin-1").split(",")[0].strip()
                if name == b"x-real-ip":
                    return val.decode("latin-1")
        client = scope.get("client")
        return client[0] if client else "unknown"

    def _should_skip(self, endpoint: str) -> bool:
        return any(endpoint.startswith(p) for p in ("/docs", "/redoc", "/openapi.json", "/health"))

    async def _send_429(self, scope, receive, send, retry_after: int) -> None:
        response = JSONResponse(
            status_code=429,
            content={"detail": "Çok fazla istek. Lütfen bekleyin.", "retry_after": retry_after},
            headers={"Retry-After": str(retry_after)},
        )
        await response(scope, receive, send)


# =============================================================================
# UTILITY FUNCTIONS (all async)
# =============================================================================


async def get_rate_limit_status(client_ip: str) -> dict:
    """Get current rate limit status for an IP."""
    storage = await _get_storage()
    if storage is None:
        return {"error": "Redis unavailable — rate limiting disabled"}
    status = {
        "global": {
            "count": await storage.get_request_count(client_ip, GLOBAL_LIMIT[1]),
            "limit": GLOBAL_LIMIT[0],
            "window_seconds": GLOBAL_LIMIT[1],
        },
        "endpoints": {},
    }

    for endpoint, (limit, window) in ENDPOINT_LIMITS.items():
        endpoint_key = f"{client_ip}:{endpoint}"
        status["endpoints"][endpoint] = {
            "count": await storage.get_endpoint_count(endpoint_key, window),
            "limit": limit,
            "window_seconds": window,
        }

    return status


async def reset_rate_limit(client_ip: str) -> None:
    """Reset rate limits for an IP (admin function)."""
    storage = await _get_storage()
    if storage is None:
        return
    if isinstance(storage, InMemoryRateLimitStorage):
        if client_ip in storage.requests:
            del storage.requests[client_ip]
        keys_to_remove = [k for k in storage.endpoint_requests if k.startswith(f"{client_ip}:")]
        for key in keys_to_remove:
            del storage.endpoint_requests[key]
    elif isinstance(storage, AsyncRedisRateLimitStorage):
        try:
            await storage.scan_and_delete(f"rl:*:{client_ip}*")
        except Exception as exc:
            logger.error("Redis reset_rate_limit failed", error=str(exc))
    logger.info("Rate limit reset", ip=client_ip)


async def reset_all_rate_limits() -> int:
    """Reset all rate limits (tüm IP'ler). Returns number of keys deleted. Admin only."""
    storage = await _get_storage()
    if storage is None:
        return 0
    if isinstance(storage, InMemoryRateLimitStorage):
        storage.requests.clear()
        storage.endpoint_requests.clear()
        logger.info("Rate limit reset all (in-memory)")
        return 0
    if isinstance(storage, AsyncRedisRateLimitStorage):
        try:
            deleted = await storage.clear_all()
            logger.info("Rate limit reset all (Redis)", deleted=deleted)
            return deleted
        except Exception as exc:
            logger.error("Redis reset_all_rate_limits failed", error=str(exc))
            raise
    return 0

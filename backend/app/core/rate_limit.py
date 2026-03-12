"""
Rate Limit Management for External API Services.

Provides:
1. Smart retry decorator with 429 handling
2. Retry-After header parsing
3. Circuit breaker pattern
4. Per-service quota tracking
5. Token-bucket rate limiting
6. API key rotation for horizontal scaling
"""

import asyncio
import itertools
import random
import time
from collections import defaultdict
from collections.abc import Callable
from functools import wraps
from typing import Any

import httpx
import structlog

from app.config import settings
from app.core.exceptions import RateLimitError

logger = structlog.get_logger()


# =============================================================================
# CONFIGURATION
# =============================================================================

# Default rate limits per service (requests per minute)
DEFAULT_RATE_LIMITS = {
    "gemini": 60,
    "elevenlabs": 50,
    "gcs": 1000,  # GCS has high limits
}

# Backoff configuration
DEFAULT_BACKOFF_MIN = 1  # seconds
DEFAULT_BACKOFF_MAX = 30  # seconds
RATE_LIMIT_BACKOFF_MIN = 5  # seconds for 429 errors (Gemini "wait a minute" scenarios)
RATE_LIMIT_BACKOFF_MAX = 45  # seconds for 429 errors

# Circuit breaker configuration (fewer false trips, longer cooldown when tripped)
CIRCUIT_BREAKER_THRESHOLD = 5  # consecutive 429s to trip
CIRCUIT_BREAKER_RESET_TIME = 120  # seconds before retrying


# =============================================================================
# TOKEN BUCKET RATE LIMITER
# =============================================================================


class TokenBucket:
    """Token-bucket algorithm — smoother than sliding-window counters.

    Tokens are replenished continuously at ``rate`` tokens/second.
    ``acquire()`` waits (non-blocking ``asyncio.sleep``) until a token
    is available instead of rejecting immediately.
    """

    def __init__(self, rate_per_minute: int, burst: int | None = None):
        self.rate = rate_per_minute / 60.0  # tokens per second
        self.burst = burst or max(rate_per_minute // 6, 5)  # default: 10s worth
        self.tokens = float(self.burst)
        self._last = time.monotonic()
        self._lock = asyncio.Lock()

    async def acquire(self, timeout: float = 30.0) -> bool:
        """Wait until a token is available.  Returns False on timeout."""
        deadline = time.monotonic() + timeout
        while True:
            async with self._lock:
                self._refill()
                if self.tokens >= 1.0:
                    self.tokens -= 1.0
                    return True
                # Calculate wait time but release the lock BEFORE sleeping
                # so other callers can proceed concurrently.
                wait = (1.0 - self.tokens) / self.rate
                if time.monotonic() + wait > deadline:
                    return False
            # Sleep WITHOUT holding the lock
            await asyncio.sleep(min(wait, deadline - time.monotonic()))
            if time.monotonic() >= deadline:
                return False

    def _refill(self) -> None:
        now = time.monotonic()
        elapsed = now - self._last
        self._last = now
        self.tokens = min(self.burst, self.tokens + elapsed * self.rate)


# =============================================================================
# API KEY ROTATOR
# =============================================================================


class APIKeyRotator:
    """Round-robin API key rotation for a service.

    Falls back to a single key when no extras are configured.
    """

    def __init__(self, primary: str, extras_csv: str = ""):
        keys = [primary] if primary else []
        if extras_csv:
            keys.extend(k.strip() for k in extras_csv.split(",") if k.strip())
        if not keys:
            raise ValueError("At least one API key is required")
        self._keys = keys
        self._cycle = itertools.cycle(keys)
        self._lock = asyncio.Lock()

    @property
    def count(self) -> int:
        return len(self._keys)

    async def next_key(self) -> str:
        async with self._lock:
            return next(self._cycle)


def _build_rotators() -> dict[str, APIKeyRotator]:
    """Build per-service key rotators from settings (called once)."""
    rotators: dict[str, APIKeyRotator] = {}
    if settings.gemini_api_key:
        rotators["gemini"] = APIKeyRotator(
            settings.gemini_api_key,
            getattr(settings, "gemini_api_keys_extra", ""),
        )
    return rotators


_key_rotators: dict[str, APIKeyRotator] | None = None


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================


def get_retry_after(response: httpx.Response) -> int | None:
    """
    Parse Retry-After header from response.

    Returns seconds to wait, or None if not present.
    """
    retry_after = response.headers.get("Retry-After")
    if retry_after is None:
        return None

    try:
        # Try parsing as integer (seconds)
        return int(retry_after)
    except ValueError:
        pass

    try:
        # Try parsing as HTTP date
        from email.utils import parsedate_to_datetime

        retry_date = parsedate_to_datetime(retry_after)
        now = time.time()
        wait_seconds = int(retry_date.timestamp() - now)
        return max(1, wait_seconds)
    except Exception:
        pass

    return None


def calculate_backoff(attempt: int, is_rate_limit: bool = False) -> float:
    """
    Calculate exponential backoff time.

    Args:
        attempt: Current attempt number (0-indexed)
        is_rate_limit: If True, use longer backoff for rate limits

    Returns:
        Seconds to wait before next attempt
    """
    if is_rate_limit:
        base = RATE_LIMIT_BACKOFF_MIN
        max_backoff = RATE_LIMIT_BACKOFF_MAX
    else:
        base = DEFAULT_BACKOFF_MIN
        max_backoff = DEFAULT_BACKOFF_MAX

    # Exponential backoff: base * 2^attempt
    wait_time = base * (2**attempt)

    # Add jitter (±20%)

    jitter = wait_time * 0.2 * (random.random() * 2 - 1)
    wait_time += jitter

    return min(wait_time, max_backoff)


# =============================================================================
# RATE LIMIT TRACKER (Singleton)
# =============================================================================


class RateLimitTracker:
    """Tracks API usage and implements circuit breaker + token-bucket.

    Features:
    - Per-service request tracking via token buckets
    - Circuit breaker for repeated 429s
    - Pre-emptive rate limiting
    - API key rotation awareness
    """

    _instance = None
    _lock = None

    def __init__(self):
        self.requests: dict[str, list[float]] = defaultdict(list)
        self.rate_limit_hits: dict[str, int] = defaultdict(int)
        self.circuit_open_until: dict[str, float] = {}

        self.rate_limits: dict[str, int] = {
            "gemini": getattr(settings, "gemini_rpm_limit", DEFAULT_RATE_LIMITS["gemini"]),
            "fal": getattr(settings, "fal_rpm_limit", DEFAULT_RATE_LIMITS["fal"]),
            "elevenlabs": getattr(
                settings, "elevenlabs_rpm_limit", DEFAULT_RATE_LIMITS["elevenlabs"]
            ),
            "gcs": DEFAULT_RATE_LIMITS["gcs"],
        }

        # Multiply effective RPM by key count (each key has its own quota)
        global _key_rotators
        if _key_rotators is None:
            _key_rotators = _build_rotators()
        for svc, rotator in (_key_rotators or {}).items():
            if svc in self.rate_limits:
                self.rate_limits[svc] *= rotator.count

        # Token buckets per service
        self.buckets: dict[str, TokenBucket] = {
            svc: TokenBucket(rpm) for svc, rpm in self.rate_limits.items()
        }

    @classmethod
    async def get_instance(cls) -> "RateLimitTracker":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _cleanup_old_requests(self, service: str):
        now = time.time()
        cutoff = now - 60
        self.requests[service] = [ts for ts in self.requests[service] if ts > cutoff]

    def get_current_rpm(self, service: str) -> int:
        self._cleanup_old_requests(service)
        return len(self.requests[service])

    def is_circuit_open(self, service: str) -> bool:
        if service not in self.circuit_open_until:
            return False
        if time.time() > self.circuit_open_until[service]:
            del self.circuit_open_until[service]
            self.rate_limit_hits[service] = 0
            logger.info(f"Circuit breaker reset for {service}")
            return False
        return True

    async def wait_if_needed(self, service: str):
        """Acquire a token from the bucket (waits if necessary)."""
        bucket = self.buckets.get(service)
        if bucket:
            ok = await bucket.acquire(timeout=30.0)
            if not ok:
                logger.warning("Token bucket timeout", service=service)
        else:
            # Fallback: simple sliding-window throttle
            self._cleanup_old_requests(service)
            current_rpm = len(self.requests[service])
            limit = self.rate_limits.get(service, 60)
            if current_rpm >= limit * 0.9:
                await asyncio.sleep(60 / limit)

    def record_request(self, service: str):
        self.requests[service].append(time.time())
        self.rate_limit_hits[service] = 0

    def record_rate_limit(self, service: str):
        self.rate_limit_hits[service] += 1
        threshold = getattr(settings, "rate_limit_circuit_threshold", CIRCUIT_BREAKER_THRESHOLD)
        if self.rate_limit_hits[service] >= threshold:
            reset_time = getattr(settings, "rate_limit_circuit_reset", CIRCUIT_BREAKER_RESET_TIME)
            self.circuit_open_until[service] = time.time() + reset_time
            logger.warning(
                f"Circuit breaker OPENED for {service}",
                consecutive_429s=self.rate_limit_hits[service],
                reset_in_seconds=reset_time,
            )

    def get_status(self) -> dict[str, Any]:
        status = {}
        for service in self.rate_limits:
            self._cleanup_old_requests(service)
            bucket = self.buckets.get(service)
            status[service] = {
                "current_rpm": len(self.requests[service]),
                "limit_rpm": self.rate_limits[service],
                "consecutive_429s": self.rate_limit_hits[service],
                "circuit_open": self.is_circuit_open(service),
                "bucket_tokens": round(bucket.tokens, 1) if bucket else None,
            }
        return status


# =============================================================================
# RATE LIMIT RETRY DECORATOR
# =============================================================================


def rate_limit_retry(
    service: str,
    max_attempts: int = 4,  # More retries on 429 before showing "AI meşgul"
    timeout_attempts: int = 1,
):
    """
    Decorator for API calls with smart rate limit handling.

    Features:
    - Automatic retry on 429 with exponential backoff
    - Respects Retry-After header
    - Circuit breaker integration
    - Pre-emptive rate limiting

    Args:
        service: Service name (gemini, fal, elevenlabs)
        max_attempts: Max retries for rate limit errors
        timeout_attempts: Max retries for timeout errors

    Usage:
        @rate_limit_retry(service="gemini")
        async def call_gemini_api(...):
            ...
    """

    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            tracker = await RateLimitTracker.get_instance()

            # Check circuit breaker
            if tracker.is_circuit_open(service):
                logger.error(f"Circuit breaker OPEN for {service}")
                raise RateLimitError(
                    f"{service.capitalize()} servisi geçici olarak devre dışı. "
                    "Lütfen birkaç dakika sonra tekrar deneyin."
                )

            rate_limit_attempts = 0
            timeout_attempt_count = 0

            while True:
                try:
                    # Pre-emptive rate limiting
                    await tracker.wait_if_needed(service)

                    # Execute the function
                    result = await func(*args, **kwargs)

                    # Record successful request
                    tracker.record_request(service)

                    return result

                except httpx.HTTPStatusError as e:
                    status_code = e.response.status_code

                    if status_code == 429:
                        # Rate limit error
                        rate_limit_attempts += 1
                        tracker.record_rate_limit(service)

                        if rate_limit_attempts >= max_attempts:
                            logger.error(
                                "Rate limit retry exhausted",
                                service=service,
                                attempts=rate_limit_attempts,
                            )
                            raise RateLimitError(
                                f"{service.capitalize()} API limit aşıldı. "
                                "Lütfen birkaç dakika bekleyin."
                            )

                        # Get wait time from Retry-After or calculate
                        retry_after = get_retry_after(e.response)
                        wait_time = retry_after or calculate_backoff(
                            rate_limit_attempts - 1, is_rate_limit=True
                        )

                        logger.warning(
                            "429 Rate limit hit - waiting",
                            service=service,
                            attempt=rate_limit_attempts,
                            wait_seconds=wait_time,
                            retry_after_header=retry_after,
                        )

                        await asyncio.sleep(wait_time)
                        continue

                    elif 500 <= status_code < 600:
                        # Server error - retry with backoff
                        rate_limit_attempts += 1

                        if rate_limit_attempts >= max_attempts:
                            logger.error(
                                "Server error retry exhausted",
                                service=service,
                                status=status_code,
                            )
                            raise

                        wait_time = calculate_backoff(rate_limit_attempts - 1)
                        logger.warning(
                            "Server error - retrying",
                            service=service,
                            status=status_code,
                            wait_seconds=wait_time,
                        )

                        await asyncio.sleep(wait_time)
                        continue

                    else:
                        # Other HTTP errors - don't retry
                        raise

                except httpx.TimeoutException:
                    timeout_attempt_count += 1

                    if timeout_attempt_count >= timeout_attempts:
                        logger.error(
                            "Timeout retry exhausted",
                            service=service,
                            attempts=timeout_attempt_count,
                        )
                        raise

                    wait_time = calculate_backoff(timeout_attempt_count - 1)
                    logger.warning(
                        "Timeout - retrying",
                        service=service,
                        attempt=timeout_attempt_count,
                        wait_seconds=wait_time,
                    )

                    await asyncio.sleep(wait_time)
                    continue

        return wrapper

    return decorator


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================


async def get_rate_limit_status() -> dict[str, Any]:
    """Get current rate limit status for monitoring."""
    tracker = await RateLimitTracker.get_instance()
    return tracker.get_status()

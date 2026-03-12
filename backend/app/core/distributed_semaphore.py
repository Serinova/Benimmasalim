"""Redis-based distributed semaphore for cross-instance concurrency control.

Provides a global limit on concurrent heavy operations (image generation,
PDF creation) across ALL Cloud Run instances — unlike asyncio.Semaphore which
is per-process only.

Usage::

    from app.core.distributed_semaphore import distributed_semaphore

    async with distributed_semaphore("image_gen", max_concurrent=6, timeout=600):
        await generate_images(...)

When Redis is unavailable, falls back to pass-through (fail-open) so that
the system doesn't block work entirely when Redis is down.
"""

from __future__ import annotations

import asyncio
import time
import uuid
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import redis.asyncio as aioredis
import structlog

from app.config import settings

logger = structlog.get_logger()

# Module-level Redis client (lazy-init)
_redis: aioredis.Redis | None = None
_redis_lock = asyncio.Lock()
_redis_unavailable = False
_redis_last_retry: float = 0.0
_RETRY_INTERVAL = 30.0  # seconds between reconnect attempts


async def _get_redis() -> aioredis.Redis | None:
    """Get or create a Redis client for the distributed semaphore."""
    global _redis, _redis_unavailable, _redis_last_retry

    if _redis is not None:
        return _redis
    if _redis_unavailable:
        if time.monotonic() - _redis_last_retry < _RETRY_INTERVAL:
            return None

    async with _redis_lock:
        if _redis is not None:
            return _redis
        if _redis_unavailable:
            if time.monotonic() - _redis_last_retry < _RETRY_INTERVAL:
                return None

        try:
            client = aioredis.from_url(
                str(settings.redis_url),
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
            )
            await client.ping()
            _redis = client
            if _redis_unavailable:
                logger.info("Distributed semaphore: Redis reconnected")
                _redis_unavailable = False
            return _redis
        except Exception:
            logger.warning("Distributed semaphore: Redis unavailable — fail-open mode")
            _redis_unavailable = True
            _redis_last_retry = time.monotonic()
            return None


# Lua script for atomic acquire: returns 1 if slot acquired, 0 otherwise.
# Uses a sorted set with member=unique_id, score=expiry_timestamp.
# First cleans expired entries, then checks count < max and adds new member.
_ACQUIRE_SCRIPT = """
local key = KEYS[1]
local max_concurrent = tonumber(ARGV[1])
local now = tonumber(ARGV[2])
local acquire_id = ARGV[3]
local ttl = tonumber(ARGV[4])

-- Remove expired entries
redis.call('ZREMRANGEBYSCORE', key, '-inf', now)

-- Check current count
local current = redis.call('ZCARD', key)
if current < max_concurrent then
    -- Add with expiry timestamp as score
    redis.call('ZADD', key, now + ttl, acquire_id)
    -- Set key TTL to prevent orphan keys
    redis.call('EXPIRE', key, ttl + 60)
    return 1
end
return 0
"""

# Lua script for atomic release
_RELEASE_SCRIPT = """
local key = KEYS[1]
local acquire_id = ARGV[1]
redis.call('ZREM', key, acquire_id)
return 1
"""


@asynccontextmanager
async def distributed_semaphore(
    name: str,
    max_concurrent: int = 6,
    timeout: int = 600,
    poll_interval: float = 2.0,
) -> AsyncGenerator[None, None]:
    """Distributed semaphore using Redis sorted sets.

    Args:
        name: Semaphore name (e.g. "image_gen", "pdf_gen").
        max_concurrent: Maximum concurrent holders across all instances.
        timeout: Max seconds to wait for a slot before raising TimeoutError.
        poll_interval: Seconds between retry polls when queue is full.

    Raises:
        TimeoutError: If a slot is not acquired within ``timeout`` seconds.
    """
    redis_client = await _get_redis()
    if redis_client is None:
        # Redis unavailable → fail-open (no global limit)
        logger.debug("dsem:pass-through", name=name)
        yield
        return

    key = f"dsem:{name}"
    acquire_id = str(uuid.uuid4())
    ttl = timeout + 120  # slot auto-expires after timeout + buffer

    acquired = False
    start = time.monotonic()

    try:
        while True:
            elapsed = time.monotonic() - start
            if elapsed > timeout:
                # Log queue state for debugging
                try:
                    now = time.time()
                    await redis_client.zremrangebyscore(key, "-inf", now)
                    current = await redis_client.zcard(key)
                    logger.error(
                        "dsem:timeout",
                        name=name,
                        waited_seconds=int(elapsed),
                        current_holders=current,
                        max=max_concurrent,
                    )
                except Exception:
                    pass
                raise TimeoutError(
                    f"Distributed semaphore '{name}' timeout after {timeout}s "
                    f"(max_concurrent={max_concurrent})"
                )

            try:
                result = await redis_client.eval(
                    _ACQUIRE_SCRIPT,
                    1,  # number of keys
                    key,
                    str(max_concurrent),
                    str(time.time()),
                    acquire_id,
                    str(ttl),
                )
                if int(result) == 1:
                    acquired = True
                    logger.info(
                        "dsem:acquired",
                        name=name,
                        acquire_id=acquire_id[:8],
                        waited_seconds=round(time.monotonic() - start, 1),
                    )
                    break
            except Exception as e:
                logger.warning("dsem:acquire_error", name=name, error=str(e))
                # Redis error → fail-open
                yield
                return

            await asyncio.sleep(poll_interval)

        yield

    finally:
        if acquired:
            try:
                await redis_client.eval(
                    _RELEASE_SCRIPT,
                    1,
                    key,
                    acquire_id,
                )
                logger.info(
                    "dsem:released",
                    name=name,
                    acquire_id=acquire_id[:8],
                    held_seconds=round(time.monotonic() - start, 1),
                )
            except Exception as e:
                logger.warning(
                    "dsem:release_error",
                    name=name,
                    acquire_id=acquire_id[:8],
                    error=str(e),
                )


async def get_semaphore_status(name: str) -> dict:
    """Get current semaphore usage (for admin monitoring)."""
    redis_client = await _get_redis()
    if redis_client is None:
        return {"name": name, "error": "Redis unavailable"}

    key = f"dsem:{name}"
    now = time.time()
    try:
        await redis_client.zremrangebyscore(key, "-inf", now)
        current = await redis_client.zcard(key)
        members = await redis_client.zrangewithscores(key, 0, -1)
        holders = [{"id": m[:8], "expires_in_s": round(s - now, 1)} for m, s in members]
        return {
            "name": name,
            "current_holders": current,
            "holders": holders,
        }
    except Exception as e:
        return {"name": name, "error": str(e)}

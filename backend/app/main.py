"""FastAPI application entry point."""

import asyncio
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from datetime import UTC

import sentry_sdk
import structlog
from fastapi import Depends, FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, ORJSONResponse
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.types import ASGIApp

from app.api.v1.router import api_router
from app.config import settings
from app.core.database import engine, get_db
from app.core.logging import setup_logging
from app.middleware.admin_audit import AdminAuditMiddleware
from app.middleware.rate_limiter import RateLimitMiddleware
from app.middleware.request_logging import RequestLoggingMiddleware

# Setup structured logging (stdout -> Docker logs)
setup_logging()
logger = structlog.get_logger()
logger.info("Logging configured", log_level=settings.log_level, env=settings.app_env)

# ── Production readiness check ──────────────────────────────────────────────
if settings.is_production:
    _fatal, _warnings = settings.validate_prod_readiness()
    for _w in _warnings:
        logger.warning("PROD_CONFIG_WARNING", issue=_w)
    if _fatal:
        for _err in _fatal:
            logger.critical("PROD_CONFIG_FATAL", error=_err)
        raise SystemExit(
            f"FATAL PRODUCTION CONFIG ({len(_fatal)}):\n"
            + "\n".join(f"  ✗ {e}" for e in _fatal)
        )

# Initialize Sentry for error tracking
if settings.sentry_dsn and settings.is_production:
    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        environment=settings.app_env,
        traces_sample_rate=0.1,
    )


async def _cleanup_stuck_payments() -> None:
    """Background task: rollback PAYMENT_PENDING orders older than 2 hours."""
    from datetime import datetime, timedelta

    from sqlalchemy import select

    from app.core.database import async_session_factory
    from app.models.order import Order, OrderStatus

    while True:
        await asyncio.sleep(1800)  # run every 30 minutes
        try:
            threshold = datetime.now(UTC) - timedelta(hours=2)
            async with async_session_factory() as db:
                result = await db.execute(
                    select(Order).where(
                        Order.status == OrderStatus.PAYMENT_PENDING,
                        Order.updated_at < threshold,
                    )
                )
                stuck_orders = result.scalars().all()

                for order in stuck_orders:
                    from app.api.v1.payments import rollback_promo_code
                    from app.services.order_state_machine import transition_order

                    await rollback_promo_code(order, db)
                    await transition_order(order, OrderStatus.COVER_APPROVED, db)
                    order.payment_status = "EXPIRED"
                    logger.warning(
                        "STUCK_PAYMENT_CLEANED",
                        order_id=str(order.id),
                        stuck_since=str(order.updated_at),
                    )
                if stuck_orders:
                    await db.commit()
                    logger.info("payment_cleanup_done", cleaned=len(stuck_orders))
        except Exception:
            logger.exception("payment_cleanup_error")


async def _cleanup_temp_images() -> None:
    """Background task: delete temp GCS images older than 24 hours (KVKK compliance)."""
    while True:
        await asyncio.sleep(3600)  # run every hour
        try:
            from app.services.storage_service import storage_service

            provider = storage_service.provider
            if not hasattr(provider, "_get_bucket"):
                continue

            from datetime import datetime, timedelta

            threshold = datetime.now(UTC) - timedelta(hours=24)
            bucket = provider._get_bucket()
            deleted = 0
            for prefix in ("temp/pulid-faces/", "temp/voice-samples/"):
                blobs = bucket.list_blobs(prefix=prefix)
                for blob in blobs:
                    if blob.time_created and blob.time_created < threshold:
                        blob.delete()
                        deleted += 1
            if deleted:
                logger.info("temp_image_cleanup_done", deleted=deleted)
        except Exception:
            logger.exception("temp_image_cleanup_error")


async def _kvkk_daily_cleanup() -> None:
    """Background task: run KVKK photo cleanup daily at ~02:00 UTC.

    Also runs abandoned preview cleanup for KVKK compliance.
    """
    from datetime import datetime

    await asyncio.sleep(60)  # wait 1 min after startup for DB readiness

    while True:
        try:
            now = datetime.now(UTC)
            # Calculate seconds until next 02:00 UTC
            target_hour = 2
            if now.hour < target_hour:
                seconds_until = (target_hour - now.hour) * 3600 - now.minute * 60 - now.second
            else:
                seconds_until = (24 - now.hour + target_hour) * 3600 - now.minute * 60 - now.second

            # Min 1 hour wait — prevent tight loops if time drifts
            seconds_until = max(seconds_until, 3600)

            logger.info("kvkk_daily_cleanup: next run", wait_seconds=seconds_until)
            await asyncio.sleep(seconds_until)

            from app.tasks.kvkk_cleanup import (
                kvkk_abandoned_preview_cleanup,
                kvkk_photo_cleanup,
            )

            result1 = await kvkk_photo_cleanup()
            logger.info("kvkk_daily_cleanup: photo cleanup done", **result1)

            result2 = await kvkk_abandoned_preview_cleanup()
            logger.info("kvkk_daily_cleanup: abandoned preview cleanup done", **result2)

        except Exception:
            logger.exception("kvkk_daily_cleanup_error")
            await asyncio.sleep(3600)  # retry in 1 hour on error


async def _apply_data_fixes() -> None:
    """One-time data fixes applied on startup. Safe to run multiple times."""
    from sqlalchemy import text

    from app.core.database import async_session_factory

    fixes = [
        (
            "UPDATE scenarios SET description = "
            "'İstanbul''un gizemli yeraltı sarayında, yüzlerce antik mermer sütun ve efsanevi "
            "Medusa başları arasında büyülü bir macera! Bizans döneminden kalma bu muhteşem "
            "sarnıçta, kehribar ışıklarla aydınlanan sütunların su yüzeyindeki yansımalarını "
            "keşfet ve tarihin derinliklerine dal!' "
            "WHERE name ILIKE '%Yerebatan%' AND (description IS NULL OR description = '')"
        ),
    ]
    try:
        async with async_session_factory() as db:
            for sql in fixes:
                await db.execute(text(sql))
            await db.commit()
        logger.info("startup_data_fixes_applied", count=len(fixes))
    except Exception as exc:
        logger.warning("startup_data_fixes_failed", error=str(exc))


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan handler."""
    logger.info("Starting application", env=settings.app_env)
    await _apply_data_fixes()
    cleanup_task = asyncio.create_task(_cleanup_stuck_payments())
    temp_cleanup_task = asyncio.create_task(_cleanup_temp_images())
    kvkk_cleanup_task = asyncio.create_task(_kvkk_daily_cleanup())
    yield
    for _task in (cleanup_task, temp_cleanup_task, kvkk_cleanup_task):
        _task.cancel()
        try:
            await _task
        except asyncio.CancelledError:
            pass

    # Gracefully close shared HTTP clients to avoid connection leaks
    try:
        from app.services.ai.gemini_consistent_image import close_download_client
        await close_download_client()
    except Exception:
        pass

    logger.info("Shutting down application")
    await engine.dispose()


# Docs only in dev — never in production regardless of DEBUG flag
_show_docs = settings.debug and not settings.is_production

app = FastAPI(
    title="Benim Masalım API",
    description="AI-powered personalized children's book platform",
    version="1.0.0",
    docs_url="/docs" if _show_docs else None,
    redoc_url="/redoc" if _show_docs else None,
    openapi_url="/openapi.json" if _show_docs else None,
    default_response_class=ORJSONResponse,
    lifespan=lifespan,
)

# ---------------------------------------------------------------------------
# CORS: environment-based origin whitelist
# ---------------------------------------------------------------------------
# Tüm ortamlarda .com.tr ve Cloud Run origin izinli (Cloud Run'da APP_ENV bazen set edilmeyebilir)
_SAFE_ORIGINS = [
    "https://benimmasalim.com.tr",
    "https://www.benimmasalim.com.tr",
    "https://benimmasalim.com",
    "https://www.benimmasalim.com",
    "https://benimmasalim-frontend-554846094227.europe-west1.run.app",
]
if settings.is_production:
    CORS_ORIGINS = list(dict.fromkeys(_SAFE_ORIGINS + [settings.frontend_url]))
elif settings.app_env == "staging":
    CORS_ORIGINS = _SAFE_ORIGINS + ["https://staging.benimmasalim.com"]
else:
    CORS_ORIGINS = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001",
        "http://localhost:3002",
        "http://127.0.0.1:3002",
        *_SAFE_ORIGINS,
    ]


# ---------------------------------------------------------------------------
# Pure ASGI Security Headers Middleware (BaseHTTPMiddleware yerine)
# ---------------------------------------------------------------------------
# Backend API CSP — sandbox iyzipay ref'lerini sadece development'ta ekle
_CSP_IYZIPAY_ORIGINS = (
    b"https://api.iyzipay.com https://sandbox-api.iyzipay.com"
    if not settings.is_production
    else b"https://api.iyzipay.com"
)
_CSP_VALUE = (
    b"default-src 'self'; "
    b"script-src 'self' 'unsafe-inline' " + _CSP_IYZIPAY_ORIGINS + b"; "
    b"style-src 'self' 'unsafe-inline'; "
    b"img-src 'self' data: blob: https://storage.googleapis.com https://*.storage.googleapis.com; "
    b"font-src 'self' data:; "
    b"connect-src 'self' " + _CSP_IYZIPAY_ORIGINS + b"; "
    b"frame-src " + _CSP_IYZIPAY_ORIGINS + b"; "
    b"frame-ancestors 'none'; "
    b"object-src 'none'; "
    b"base-uri 'self'; "
    b"upgrade-insecure-requests"
)

_SECURITY_HEADERS: list[tuple[bytes, bytes]] = [
    (b"x-frame-options", b"DENY"),
    (b"x-content-type-options", b"nosniff"),
    (b"referrer-policy", b"strict-origin-when-cross-origin"),
    (b"x-xss-protection", b"1; mode=block"),
    (b"permissions-policy", b"camera=(), microphone=(self), geolocation=(), payment=(self)"),
    (b"content-security-policy", _CSP_VALUE),
    (b"x-dns-prefetch-control", b"on"),
]
_HSTS_HEADER = (b"strict-transport-security", b"max-age=63072000; includeSubDomains; preload")


class SecurityHeadersMiddleware:
    """Pure ASGI middleware — no BaseHTTPMiddleware (avoids response body deadlock)."""

    def __init__(self, app: "ASGIApp") -> None:
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)

        is_https = scope.get("scheme") == "https"
        if not is_https:
            for header_name, header_val in scope.get("headers", []):
                if header_name == b"x-forwarded-proto" and header_val == b"https":
                    is_https = True
                    break

        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))
                headers.extend(_SECURITY_HEADERS)
                if is_https:
                    headers.append(_HSTS_HEADER)
                message = {**message, "headers": headers}
            await send(message)

        await self.app(scope, receive, send_wrapper)


# ── Request body size limiter (50MB max — prevents memory DoS) ──
_MAX_BODY_SIZE = 50 * 1024 * 1024  # 50 MB


class BodySizeLimitMiddleware:
    """Pure ASGI middleware for body size checking."""

    def __init__(self, app: "ASGIApp") -> None:
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)

        for header_name, header_val in scope.get("headers", []):
            if header_name == b"content-length":
                try:
                    if int(header_val) > _MAX_BODY_SIZE:
                        response = JSONResponse(
                            status_code=413,
                            content={"detail": "İstek boyutu çok büyük (max 50 MB)"},
                        )
                        return await response(scope, receive, send)
                except ValueError:
                    pass
                break

        await self.app(scope, receive, send)


# Middleware order (last added = first executed):
# 1) Request logging  2) Rate limiter  3) Admin audit  4) Body size limit  5) Security headers  6) CORS
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(AdminAuditMiddleware)
app.add_middleware(BodySizeLimitMiddleware)
app.add_middleware(SecurityHeadersMiddleware)

# CORS middleware (admin + create sayfası tarayıcıdan doğrudan backend'e istek atıyor)
# Cookie kullanılmıyor (pure Bearer token), credentials gereksiz.
# allow_headers/expose_headers explicit — yüzey alanını küçült.
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=[
        "Authorization",
        "Content-Type",
        "Accept",
        "X-User-Id",
        "X-Trial-Token",
        "X-Request-ID",
    ],
    expose_headers=["X-Request-ID", "X-RateLimit-Remaining", "Retry-After"],
    max_age=86400,  # Preflight cache: 24h — preflight trafiğini azalt
)


def _cors_headers(request: Request) -> dict[str, str]:
    """Return CORS headers matching the request origin (if allowed)."""
    origin = request.headers.get("origin", "")
    if origin in CORS_ORIGINS:
        return {
            "access-control-allow-origin": origin,
            "vary": "Origin",
        }
    return {}


# Validation error handler with detailed logging
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    # Pydantic v2 errors() may contain non-serializable objects (ValueError ctx).
    # Convert to safe dicts before JSON serialization.
    raw_errors = exc.errors()
    safe_errors = []
    for err in raw_errors:
        safe = {
            "loc": err.get("loc"),
            "msg": err.get("msg", str(err)),
            "type": err.get("type", "value_error"),
        }
        safe_errors.append(safe)
    logger.error("Validation error", path=request.url.path, errors=safe_errors)
    return JSONResponse(status_code=422, content={"detail": safe_errors}, headers=_cors_headers(request))


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    from starlette.exceptions import HTTPException as StHTTP

    if isinstance(exc, StHTTP):
        detail = exc.detail if isinstance(exc.detail, (str, list, dict)) else str(exc.detail)
        return JSONResponse(status_code=exc.status_code, content={"detail": detail}, headers=_cors_headers(request))
    logger.exception("Unhandled", path=request.url.path, error=str(exc))
    detail = str(exc) if settings.app_env == "development" else "Sunucu hatası"
    return JSONResponse(status_code=500, content={"detail": detail}, headers=_cors_headers(request))


# Include API routes
app.include_router(api_router, prefix="/api/v1")

# Mount local media directory when using local storage driver (development)
if settings.storage_driver == "local":
    import os

    from fastapi.staticfiles import StaticFiles

    _media_dir = settings.local_storage_path
    os.makedirs(_media_dir, exist_ok=True)
    app.mount("/api/v1/media", StaticFiles(directory=_media_dir), name="media")


@app.get("/health")
async def health_check(db: AsyncSession = Depends(get_db)) -> dict:
    """Health check endpoint with DB, Redis, and rate-limit diagnostics."""
    # DB check
    try:
        await db.execute(text("SELECT 1"))
        db_status = "ok"
    except Exception:
        db_status = "error"

    # Redis check (uses cached pool from enqueue module)
    redis_status = "unknown"
    queue_depth: int | None = None
    try:
        from app.workers.enqueue import _get_pool, get_queue_depth

        pool = await _get_pool()
        await pool.ping()
        queue_depth = await get_queue_depth()
        redis_status = "ok"
    except Exception:
        redis_status = "error"

    # Rate-limit status
    rate_limits = {}
    try:
        from app.core.rate_limit import get_rate_limit_status
        rate_limits = await get_rate_limit_status()
    except Exception:
        pass

    status_val = "healthy"
    if db_status != "ok":
        status_val = "degraded"
    if redis_status == "error":
        status_val = "degraded"

    return {
        "status": status_val,
        "db": db_status,
        "redis": redis_status,
        "queue_depth": queue_depth,
        "rate_limits": rate_limits,
        "version": "1.1.0",
    }


@app.get("/")
async def root() -> dict[str, str]:
    """Root endpoint."""
    return {"name": "Benim Masalım API", "version": "1.0.0"}

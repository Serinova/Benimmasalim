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


_SEED_VERSION = "3"  # Increment when creators/updaters list changes


async def _seed_missing_scenarios() -> None:
    """Seed scenarios that exist in scripts but not in production DB.

    Version-gated: skips all work if app_settings.seeded_version == _SEED_VERSION.
    Increment _SEED_VERSION whenever the creators/updaters lists change.
    """
    from sqlalchemy import select

    from app.core.database import async_session_factory

    creators: list[tuple[str, str, str]] = [
        ("gobeklitepe", "scripts.create_gobeklitepe_scenario", "create_gobeklitepe_scenario"),
        ("ephesus", "scripts.create_efes_scenario", "create_efes_scenario"),
        ("sumela", "scripts.create_sumela_scenario", "create_sumela_scenario"),
        ("sultanahmet", "scripts.create_sultanahmet_scenario", "create_sultanahmet_scenario"),
        ("galata", "scripts.create_galata_scenario", "create_galata_scenario"),
        ("toy_world", "scripts.create_toy_world_scenario", "create_toy_world_scenario"),
        ("fairy_tale_world", "scripts.create_fairy_tale_scenario", "create_fairy_tale_scenario"),
    ]

    updaters: list[tuple[str, str, str]] = [
        ("cappadocia", "scripts.update_cappadocia_scenario", "update_cappadocia_scenario"),
        ("solar_system", "scripts.update_space_scenario", "update_space_scenario"),
        ("catalhoyuk", "scripts.update_catalhoyuk_scenario", "update_catalhoyuk_scenario"),
        ("kudus", "scripts.update_jerusalem_scenario", "update_jerusalem_scenario"),
        ("ocean_depths", "scripts.update_ocean_adventure_scenario", "update_ocean_adventure_scenario"),
        ("umre_pilgrimage", "scripts.update_umre_scenario", "update_umre_scenario"),
        ("amazon_rainforest", "scripts.update_amazon_scenario", "update_amazon_scenario"),
        ("dinosaur_time_travel", "scripts.update_dinosaur_scenario", "update_dinosaur_scenario"),
    ]

    try:
        import importlib
        import uuid as _uuid

        from app.models.app_setting import AppSetting
        from app.models.scenario import Scenario

        # Version gate — skip expensive seeding if already done for this version
        async with async_session_factory() as db:
            result = await db.execute(
                select(AppSetting).where(AppSetting.key == "seeded_version")
            )
            setting = result.scalar_one_or_none()
            if setting and setting.value == _SEED_VERSION:
                logger.info("seed_scenarios_skipped", reason="already_seeded", version=_SEED_VERSION)
                return

        for theme_key, module_path, func_name in creators:
            try:
                async with async_session_factory() as db:
                    exists = await db.execute(
                        select(Scenario).where(Scenario.theme_key == theme_key)
                    )
                    if exists.scalar_one_or_none():
                        continue
                mod = importlib.import_module(module_path)
                fn = getattr(mod, func_name)
                await fn()
                logger.info("seed_scenario_created", theme_key=theme_key)
            except Exception as exc:
                logger.warning("seed_scenario_failed", theme_key=theme_key, error=str(exc))

        stub_seeds: list[tuple[str, str, str, int]] = [
            ("cappadocia", "Kapadokya Macerası",
             "Kapadokya'nın büyülü dünyasına yolculuk! Peri bacaları (60 milyon yıllık!), "
             "sıcak hava balonu turu, yeraltı şehri keşfi (8 kat derinlik!) ve kaya "
             "kiliselerdeki 1000 yıllık freskler. UNESCO Dünya Mirası'nda doğa mucizesi ve macera!", 0),
            ("solar_system", "Güneş Sistemi Macerası: Gezegen Kaşifleri",
             "8 gezegen macerası! Modüler uzay istasyonundan başlayarak Merkür'den Neptün'e "
             "kadar tüm gezegenleri keşfet. AI robot arkadaşınla birlikte Jüpiter'in ihtişamını, "
             "Satürn'ün halkalarını ve Mars'taki yaşam izlerini öğren!", 15),
        ]
        for theme_key, name, desc, order in stub_seeds:
            try:
                async with async_session_factory() as db:
                    exists = await db.execute(
                        select(Scenario).where(Scenario.theme_key == theme_key)
                    )
                    if exists.scalar_one_or_none():
                        continue
                    s = Scenario(
                        id=_uuid.uuid4(), name=name, description=desc,
                        thumbnail_url="", theme_key=theme_key,
                        display_order=order, is_active=True,
                    )
                    db.add(s)
                    await db.commit()
                    logger.info("seed_scenario_stub_created", theme_key=theme_key)
            except Exception as exc:
                logger.warning("seed_scenario_stub_failed", theme_key=theme_key, error=str(exc))

        # Link all scenarios to A4 YATAY product if not linked
        try:
            from app.models.product import Product
            async with async_session_factory() as db:
                prod_result = await db.execute(
                    select(Product).where(Product.slug == "a4-yatay")
                )
                a4_product = prod_result.scalar_one_or_none()
                if a4_product:
                    unlinked = await db.execute(
                        select(Scenario).where(Scenario.linked_product_id.is_(None))
                    )
                    for s in unlinked.scalars().all():
                        s.linked_product_id = a4_product.id
                    await db.commit()
                    logger.info("seed_scenarios_linked_product")
        except Exception as exc:
            logger.warning("seed_scenarios_link_failed", error=str(exc))

        for theme_key, module_path, func_name in updaters:
            try:
                mod = importlib.import_module(module_path)
                fn = getattr(mod, func_name)
                await fn()
                logger.info("seed_scenario_updated", theme_key=theme_key)
            except Exception as exc:
                logger.warning("seed_scenario_update_failed", theme_key=theme_key, error=str(exc))

        # Mark seeding complete for this version
        try:
            async with async_session_factory() as db:
                result = await db.execute(
                    select(AppSetting).where(AppSetting.key == "seeded_version")
                )
                setting = result.scalar_one_or_none()
                if setting:
                    setting.value = _SEED_VERSION
                else:
                    db.add(AppSetting(key="seeded_version", value=_SEED_VERSION))
                await db.commit()
            logger.info("seed_version_saved", version=_SEED_VERSION)
        except Exception as exc:
            logger.warning("seed_version_save_failed", error=str(exc))

    except Exception as exc:
        logger.warning("seed_missing_scenarios_failed", error=str(exc))


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

    await _seed_missing_scenarios()


# ---------------------------------------------------------------------------
# Distributed leader lock — ensures periodic tasks run on ONE worker only
# ---------------------------------------------------------------------------
_leader_redis = None


async def _get_leader_redis():
    """Get shared async Redis connection for leader election."""
    global _leader_redis
    if _leader_redis is not None:
        return _leader_redis
    try:
        import redis.asyncio as aioredis
        _leader_redis = aioredis.from_url(
            str(settings.redis_url), decode_responses=True,
            socket_connect_timeout=5, socket_timeout=5,
        )
        await _leader_redis.ping()
        return _leader_redis
    except Exception:
        _leader_redis = None
        return None


async def _acquire_leader_lock(lock_name: str, ttl_seconds: int = 60) -> bool:
    """Try to acquire a distributed lock via Redis SET NX EX.

    Returns True if this worker is the leader for *lock_name*.
    The lock auto-expires after *ttl_seconds* so a crashed leader
    doesn't block others permanently.
    """
    r = await _get_leader_redis()
    if r is None:
        # Redis unavailable — fall back to "everyone runs" (better than nobody)
        return True
    import os
    worker_id = f"{os.getpid()}"
    try:
        acquired = await r.set(
            f"leader:{lock_name}", worker_id, nx=True, ex=ttl_seconds,
        )
        return bool(acquired)
    except Exception:
        return True  # fail-open: run the task if Redis is flaky


async def _renew_leader_lock(lock_name: str, ttl_seconds: int = 60) -> bool:
    """Renew leader lock TTL. Returns False if lock was lost."""
    r = await _get_leader_redis()
    if r is None:
        return True
    import os
    worker_id = f"{os.getpid()}"
    try:
        current = await r.get(f"leader:{lock_name}")
        if current == worker_id:
            await r.expire(f"leader:{lock_name}", ttl_seconds)
            return True
        return False
    except Exception:
        return True


async def _leader_task_wrapper(task_coro, lock_name: str, ttl: int = 120):
    """Only run *task_coro* if this worker holds the leader lock.

    Attempts to acquire the lock on startup. If another worker already
    holds it, this worker sleeps and retries periodically (in case the
    leader crashes). The lock is renewed each cycle.
    """
    import asyncio

    # Initial attempt
    while True:
        if await _acquire_leader_lock(lock_name, ttl):
            logger.info("leader_lock_acquired", lock=lock_name, pid=__import__("os").getpid())
            break
        # Not leader — wait and retry in case leader dies
        await asyncio.sleep(ttl // 2)

    # Run the actual task
    try:
        await task_coro()
    finally:
        # Release lock on cancellation
        r = await _get_leader_redis()
        if r:
            try:
                await r.delete(f"leader:{lock_name}")
            except Exception:
                pass


# Wrappers that renew the lock inside each loop iteration
async def _cleanup_stuck_payments_leader():
    """Stuck payment cleanup — single leader only."""
    from datetime import datetime, timedelta

    from sqlalchemy import select

    from app.core.database import async_session_factory
    from app.models.order import Order, OrderStatus

    while True:
        if not await _renew_leader_lock("bg:stuck_payments", 3600):
            logger.info("leader_lock_lost", task="stuck_payments")
            return
        await asyncio.sleep(1800)
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
                    from app.services.order_state_machine import transition_order
                    from app.services.promo_code_service import rollback_promo_code
                    await rollback_promo_code(order, db)
                    await transition_order(order, OrderStatus.COVER_APPROVED, db)
                    order.payment_status = "EXPIRED"
                    logger.warning("STUCK_PAYMENT_CLEANED", order_id=str(order.id))
                if stuck_orders:
                    await db.commit()
                    logger.info("payment_cleanup_done", cleaned=len(stuck_orders))
        except Exception:
            logger.exception("payment_cleanup_error")


async def _cleanup_temp_images_leader():
    """Temp GCS image cleanup — single leader only."""
    while True:
        if not await _renew_leader_lock("bg:temp_images", 7200):
            logger.info("leader_lock_lost", task="temp_images")
            return
        await asyncio.sleep(3600)
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


async def _kvkk_daily_cleanup_leader():
    """KVKK daily cleanup — single leader only."""
    from datetime import datetime
    await asyncio.sleep(60)
    while True:
        if not await _renew_leader_lock("bg:kvkk_cleanup", 86400):
            logger.info("leader_lock_lost", task="kvkk_cleanup")
            return
        try:
            now = datetime.now(UTC)
            target_hour = 2
            if now.hour < target_hour:
                seconds_until = (target_hour - now.hour) * 3600 - now.minute * 60 - now.second
            else:
                seconds_until = (24 - now.hour + target_hour) * 3600 - now.minute * 60 - now.second
            seconds_until = max(seconds_until, 3600)
            logger.info("kvkk_daily_cleanup: next run", wait_seconds=seconds_until)
            await asyncio.sleep(seconds_until)

            from app.tasks.kvkk_cleanup import (
                kvkk_abandoned_preview_cleanup,
                kvkk_photo_cleanup,
                purge_deleted_accounts,
            )
            result1 = await kvkk_photo_cleanup()
            logger.info("kvkk_daily_cleanup: photo cleanup done", **result1)
            result2 = await kvkk_abandoned_preview_cleanup()
            logger.info("kvkk_daily_cleanup: abandoned preview done", **result2)
            result3 = await purge_deleted_accounts()
            logger.info("kvkk_daily_cleanup: purge done", **result3)

            from app.core.database import async_session_factory as _sf
            from app.services.invoice_token_service import cleanup_expired_tokens
            async with _sf() as _db:
                purged = await cleanup_expired_tokens(_db)
                await _db.commit()
                if purged:
                    logger.info("kvkk_daily_cleanup: tokens purged", count=purged)
        except Exception:
            logger.exception("kvkk_daily_cleanup_error")
            await asyncio.sleep(3600)


async def _outbox_worker_leader():
    """Outbox worker — single leader only. Renews lock on every poll cycle.

    Deliberately does not delegate to run_outbox_worker() because that function
    has no lock-renewal logic and the 120s TTL would expire mid-run.
    """
    from app.core.database import async_session_factory
    from app.tasks.outbox_worker import (
        _POLL_INTERVAL_BUSY_SECONDS,
        _POLL_INTERVAL_IDLE_SECONDS,
        process_outbox_batch,
    )

    await asyncio.sleep(10)
    logger.info("outbox_worker_started")

    while True:
        if not await _renew_leader_lock("bg:outbox", 120):
            logger.info("leader_lock_lost", task="outbox")
            return
        count = 0
        try:
            async with async_session_factory() as db:
                count = await process_outbox_batch(db)
                if count > 0:
                    logger.info("outbox_batch_processed", count=count)
        except Exception:
            logger.exception("outbox_worker_error")
        await asyncio.sleep(_POLL_INTERVAL_BUSY_SECONDS if count > 0 else _POLL_INTERVAL_IDLE_SECONDS)


async def _invoice_retry_leader():
    """Invoice PDF retry — single leader only."""
    await asyncio.sleep(120)
    while True:
        if not await _renew_leader_lock("bg:invoice_retry", 600):
            logger.info("leader_lock_lost", task="invoice_retry")
            return
        try:
            from app.core.database import async_session_factory
            from app.services.invoice_pdf_service import retry_failed_invoices
            async with async_session_factory() as db:
                count = await retry_failed_invoices(db)
                if count:
                    logger.info("invoice_retry_worker: retried", count=count)
        except Exception:
            logger.exception("invoice_retry_worker_error")
        await asyncio.sleep(300)


async def _invoice_email_retry_leader():
    """Invoice email retry — single leader only."""
    await asyncio.sleep(150)
    while True:
        if not await _renew_leader_lock("bg:invoice_email_retry", 600):
            logger.info("leader_lock_lost", task="invoice_email_retry")
            return
        try:
            from app.core.database import async_session_factory
            from app.services.invoice_email_service import retry_failed_invoice_emails
            async with async_session_factory() as db:
                count = await retry_failed_invoice_emails(db)
                if count:
                    logger.info("invoice_email_retry_worker: retried", count=count)
        except Exception:
            logger.exception("invoice_email_retry_worker_error")
        await asyncio.sleep(300)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan handler.

    Background tasks use Redis-based leader election so only ONE
    Gunicorn worker runs periodic jobs (cleanup, outbox, retries).
    If the leader crashes, another worker acquires the lock automatically.
    """
    logger.info("Starting application", env=settings.app_env)
    await _apply_data_fixes()

    # Each background task is wrapped with leader election
    bg_tasks = [
        asyncio.create_task(_leader_task_wrapper(_cleanup_stuck_payments_leader, "bg:stuck_payments", 3600)),
        asyncio.create_task(_leader_task_wrapper(_cleanup_temp_images_leader, "bg:temp_images", 7200)),
        asyncio.create_task(_leader_task_wrapper(_kvkk_daily_cleanup_leader, "bg:kvkk_cleanup", 86400)),
        asyncio.create_task(_leader_task_wrapper(_outbox_worker_leader, "bg:outbox", 120)),
        asyncio.create_task(_leader_task_wrapper(_invoice_retry_leader, "bg:invoice_retry", 600)),
        asyncio.create_task(_leader_task_wrapper(_invoice_email_retry_leader, "bg:invoice_email_retry", 600)),
    ]

    yield

    for _task in bg_tasks:
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
    "https://benimmasalim-frontend-pl5vhpeiya-ew.a.run.app",
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

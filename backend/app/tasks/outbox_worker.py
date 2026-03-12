"""Notification outbox worker — polls PENDING/FAILED rows and sends emails.

Runs as a background asyncio task inside the FastAPI lifespan.
Guarantees at-least-once delivery with idempotent sends
(unique constraint prevents duplicate outbox rows; sent_at prevents re-sends).

Cycle: poll → send → mark SENT/FAILED → sleep → repeat.
"""

from datetime import UTC, datetime, timedelta

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification_outbox import NotificationOutbox, OutboxStatus
from app.models.notification_preference import NotificationPreference
from app.models.user import User

logger = structlog.get_logger()

_BATCH_SIZE = 20
_POLL_INTERVAL_BUSY_SECONDS = 5   # batch had items → poll again quickly
_POLL_INTERVAL_IDLE_SECONDS = 30  # batch was empty → back off
_RETRY_BACKOFF_MINUTES = [1, 5, 30]


async def process_outbox_batch(db: AsyncSession) -> int:
    """Process one batch of pending outbox entries. Returns count processed."""
    now = datetime.now(UTC)

    result = await db.execute(
        select(NotificationOutbox)
        .where(
            NotificationOutbox.status.in_([OutboxStatus.PENDING.value, OutboxStatus.FAILED.value]),
            (NotificationOutbox.next_retry_at.is_(None)) | (NotificationOutbox.next_retry_at <= now),
        )
        .order_by(NotificationOutbox.created_at.asc())
        .limit(_BATCH_SIZE)
        .with_for_update(skip_locked=True)
    )
    entries = list(result.scalars().all())

    if not entries:
        return 0

    processed = 0
    for entry in entries:
        try:
            sent = await _send_single(entry, db)
            if sent:
                entry.status = OutboxStatus.SENT.value
                entry.sent_at = datetime.now(UTC)
                entry.last_error = None
            else:
                entry.status = OutboxStatus.SKIPPED.value
                entry.last_error = "skipped: user pref disabled or user not found"
            processed += 1
        except Exception as exc:
            entry.retry_count += 1
            entry.last_error = str(exc)[:500]

            if entry.retry_count >= entry.max_retries:
                entry.status = OutboxStatus.FAILED.value
                logger.error(
                    "outbox_entry_permanently_failed",
                    outbox_id=entry.id,
                    order_id=str(entry.order_id),
                    status=entry.order_status,
                    error=entry.last_error,
                )
            else:
                backoff_idx = min(entry.retry_count - 1, len(_RETRY_BACKOFF_MINUTES) - 1)
                entry.next_retry_at = datetime.now(UTC) + timedelta(
                    minutes=_RETRY_BACKOFF_MINUTES[backoff_idx],
                )
                logger.warning(
                    "outbox_entry_retry_scheduled",
                    outbox_id=entry.id,
                    retry_count=entry.retry_count,
                    next_retry_at=str(entry.next_retry_at),
                )
            processed += 1

    await db.commit()
    return processed


async def _send_single(entry: NotificationOutbox, db: AsyncSession) -> bool:
    """Send a single outbox entry. Returns True if sent, False if skipped."""
    if not entry.user_id:
        return False

    user_result = await db.execute(select(User).where(User.id == entry.user_id))
    user = user_result.scalar_one_or_none()
    if not user or not user.email:
        return False

    pref_result = await db.execute(
        select(NotificationPreference).where(NotificationPreference.user_id == user.id)
    )
    pref = pref_result.scalar_one_or_none()
    if pref and not pref.email_order_updates:
        return False

    payload = entry.payload or {}
    extra: dict = {}
    if payload.get("tracking_number"):
        extra["tracking_number"] = payload["tracking_number"]

    from app.services.email_service import email_service

    await email_service.send_order_status_email_async(
        recipient_email=user.email,
        recipient_name=user.full_name or "",
        child_name=payload.get("child_name", ""),
        order_id=str(entry.order_id),
        status_key=entry.order_status,
        extra=extra,
    )
    return True


async def run_outbox_worker() -> None:
    """Long-running worker loop. Call as asyncio.create_task in lifespan."""
    import asyncio

    from app.core.database import async_session_factory

    await asyncio.sleep(10)
    logger.info("outbox_worker_started")

    while True:
        count = 0
        try:
            async with async_session_factory() as db:
                count = await process_outbox_batch(db)
                if count > 0:
                    logger.info("outbox_batch_processed", count=count)
        except Exception:
            logger.exception("outbox_worker_error")

        await asyncio.sleep(_POLL_INTERVAL_BUSY_SECONDS if count > 0 else _POLL_INTERVAL_IDLE_SECONDS)

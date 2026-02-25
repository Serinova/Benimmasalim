"""KVKK compliance tasks — automatic data deletion and anonymization.

Provides:
  - kvkk_photo_cleanup(): Daily cleanup of photos 30 days after delivery
  - delete_user_data(): Right to be Forgotten (full user data deletion)
  - kvkk_abandoned_preview_cleanup(): Cleanup of abandoned StoryPreview records
"""

from datetime import UTC, datetime, timedelta

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session_factory
from app.models.audit_log import AuditLog
from app.models.order import Order, OrderStatus
from app.services.storage_service import StorageService

logger = structlog.get_logger()

_ANONYMIZED = "[silindi]"


async def kvkk_photo_cleanup() -> dict:
    """Delete photos from orders delivered more than 30 days ago.

    Also deletes book images, PDFs and cloned audio for those orders.
    Should run daily (Cloud Scheduler / background task at 02:00).
    """
    storage = StorageService()
    processed = 0
    deleted_files = 0
    errors = 0

    async with async_session_factory() as db:
        now = datetime.utcnow()

        result = await db.execute(
            select(Order).where(
                Order.status == OrderStatus.DELIVERED,
                Order.photo_deletion_scheduled_at <= now,
                Order.child_photo_url.isnot(None),
            )
        )
        orders = result.scalars().all()

        logger.info("KVKK cleanup started", orders_to_process=len(orders))

        for order in orders:
            processed += 1
            try:
                # Delete child photo from GCS
                if order.child_photo_url:
                    storage.delete_file(order.child_photo_url)
                    deleted_files += 1

                # Delete cloned voice recordings
                if order.audio_file_url and order.audio_type == "cloned":
                    storage.delete_file(order.audio_file_url)
                    deleted_files += 1

                # Delete voice sample
                if getattr(order, "voice_sample_url", None):
                    storage.delete_file(order.voice_sample_url)
                    deleted_files += 1

                # Delete generated book images + PDF for this order
                order_id_str = str(order.id)
                storage.delete_order_files(order_id_str)

                # Clear personal data fields in DB
                order.child_photo_url = None
                order.face_embedding = None
                order.face_description = None

                if order.audio_type == "cloned":
                    order.audio_file_url = None

                # Create audit log
                audit = AuditLog(
                    action="KVKK_PHOTO_DELETED",
                    order_id=order.id,
                    details={
                        "deletion_date": now.isoformat(),
                        "delivered_at": order.delivered_at.isoformat()
                        if order.delivered_at
                        else None,
                        "days_since_delivery": (now - order.delivered_at).days
                        if order.delivered_at
                        else None,
                    },
                )
                db.add(audit)

                logger.info(
                    "KVKK: Order data deleted",
                    order_id=order_id_str,
                    delivered_at=order.delivered_at,
                )

            except Exception as e:
                errors += 1
                logger.error("KVKK cleanup error", order_id=str(order.id), error=str(e))

        await db.commit()

    summary = {
        "processed": processed,
        "deleted": deleted_files,
        "errors": errors,
        "timestamp": datetime.utcnow().isoformat(),
    }
    logger.info("KVKK cleanup completed", **summary)
    return summary


async def delete_user_data(user_id: str, db: AsyncSession) -> dict:
    """Delete ALL data for a user (Right to be Forgotten / KVKK Art. 7).

    Deletes:
      - Child photos, voice samples, cloned audio from GCS
      - Generated book images and PDFs from GCS
      - StoryPreview records and their GCS files
      - Anonymizes order records (personal fields cleared, kept for accounting)
      - Deletes user account
    """
    from uuid import UUID

    from app.models.story_preview import StoryPreview
    from app.models.user import User

    storage = StorageService()
    uid = UUID(user_id)
    deleted_photos = 0
    deleted_audio = 0
    deleted_previews = 0
    deleted_book_files = 0

    # ── Orders: delete files + anonymize ──────────────────────────────
    result = await db.execute(select(Order).where(Order.user_id == uid))
    orders = result.scalars().all()

    for order in orders:
        # Delete photo from GCS
        if order.child_photo_url:
            storage.delete_file(order.child_photo_url)
            deleted_photos += 1

        # Delete cloned audio
        if order.audio_file_url and order.audio_type == "cloned":
            storage.delete_file(order.audio_file_url)
            deleted_audio += 1

        # Delete voice sample
        if getattr(order, "voice_sample_url", None):
            storage.delete_file(order.voice_sample_url)

        # Delete QR code
        if order.qr_code_url:
            storage.delete_file(order.qr_code_url)

        # Delete generated book images + PDF
        storage.delete_order_files(str(order.id))
        deleted_book_files += 1

        # Anonymize order: clear personal data but keep financial record
        order.user_id = None
        order.child_name = _ANONYMIZED
        order.child_photo_url = None
        order.face_embedding = None
        order.face_description = None
        order.shipping_address = None
        order.dedication_note = None
        order.qr_code_url = None
        if order.audio_type == "cloned":
            order.audio_file_url = None

    # ── StoryPreviews: delete files + records ─────────────────────────
    preview_result = await db.execute(
        select(StoryPreview).where(StoryPreview.lead_user_id == uid)
    )
    previews = preview_result.scalars().all()

    for preview in previews:
        # Delete child photo
        if preview.child_photo_url:
            storage.delete_file(preview.child_photo_url)

        # Delete voice sample / audio
        if preview.voice_sample_url:
            storage.delete_file(preview.voice_sample_url)
        if preview.audio_file_url:
            storage.delete_file(preview.audio_file_url)

        # Delete preview images from GCS
        _delete_jsonb_urls(storage, preview.preview_images)
        _delete_jsonb_urls(storage, preview.page_images)

        await db.delete(preview)
        deleted_previews += 1

    # ── User account: hard delete ─────────────────────────────────────
    user_result = await db.execute(select(User).where(User.id == uid))
    user = user_result.scalar_one_or_none()
    if user:
        await db.delete(user)

    # ── Audit log ─────────────────────────────────────────────────────
    audit = AuditLog(
        action="USER_DATA_DELETED",
        user_id=uid,
        details={
            "orders_anonymized": len(orders),
            "photos_deleted": deleted_photos,
            "audio_deleted": deleted_audio,
            "previews_deleted": deleted_previews,
            "book_files_deleted": deleted_book_files,
        },
    )
    db.add(audit)
    await db.commit()

    return {
        "user_deleted": bool(user),
        "orders_anonymized": len(orders),
        "photos_deleted": deleted_photos,
        "audio_deleted": deleted_audio,
        "previews_deleted": deleted_previews,
        "book_files_deleted": deleted_book_files,
    }


async def kvkk_abandoned_preview_cleanup() -> dict:
    """Delete abandoned StoryPreview records older than 7 days.

    Abandoned trials contain personal data (name, email, phone, photo)
    that must not be kept indefinitely per KVKK.
    """
    from app.models.story_preview import PreviewStatus, StoryPreview

    storage = StorageService()
    deleted = 0
    errors = 0

    async with async_session_factory() as db:
        cutoff = datetime.utcnow() - timedelta(days=7)

        result = await db.execute(
            select(StoryPreview).where(
                StoryPreview.status.in_([
                    PreviewStatus.ABANDONED_TRIAL.value,
                    PreviewStatus.EXPIRED.value,
                    PreviewStatus.CANCELLED.value,
                ]),
                StoryPreview.created_at <= cutoff,
            )
        )
        previews = result.scalars().all()

        logger.info("KVKK abandoned preview cleanup started", count=len(previews))

        for preview in previews:
            try:
                if preview.child_photo_url:
                    storage.delete_file(preview.child_photo_url)
                if preview.voice_sample_url:
                    storage.delete_file(preview.voice_sample_url)
                if preview.audio_file_url:
                    storage.delete_file(preview.audio_file_url)
                _delete_jsonb_urls(storage, preview.preview_images)
                _delete_jsonb_urls(storage, preview.page_images)

                await db.delete(preview)
                deleted += 1
            except Exception as e:
                errors += 1
                logger.error(
                    "KVKK abandoned preview cleanup error",
                    preview_id=str(preview.id),
                    error=str(e),
                )

        if deleted:
            audit = AuditLog(
                action="KVKK_ABANDONED_PREVIEWS_DELETED",
                details={"deleted": deleted, "errors": errors},
            )
            db.add(audit)

        await db.commit()

    summary = {"deleted": deleted, "errors": errors, "timestamp": datetime.utcnow().isoformat()}
    logger.info("KVKK abandoned preview cleanup completed", **summary)
    return summary


async def audit_log_retention_cleanup(retention_days: int = 365) -> dict:
    """Delete audit log entries older than *retention_days*.

    KVKK requires that personal data (including audit trails containing PII
    references like user_id) is not kept longer than necessary.

    Recommended: run monthly via scheduler.
    Default retention: 365 days for general logs, 2 years for financial/KVKK.

    Returns summary dict with counts.
    """
    from app.models.audit_log import AuditLog

    now = datetime.now(UTC)
    threshold = now - timedelta(days=retention_days)

    # Financial & KVKK logs have longer retention (2 × general)
    _long_retention_actions = frozenset({
        "PAYMENT_CALLBACK_RECEIVED",
        "PROMO_CODE_CONSUMED",
        "PROMO_CODE_ROLLED_BACK",
        "KVKK_PHOTO_DELETED",
        "USER_DATA_DELETED",
        "USER_DATA_EXPORTED",
        "DATA_REQUEST_SUBMITTED",
        "KVKK_USER_DATA_DELETED",
        "KVKK_ABANDONED_PREVIEWS_DELETED",
    })
    long_threshold = now - timedelta(days=retention_days * 2)

    deleted_general = 0
    deleted_long = 0

    async with async_session_factory() as db:
        from sqlalchemy import delete

        # General logs
        stmt_general = (
            delete(AuditLog)
            .where(AuditLog.created_at < threshold)
            .where(AuditLog.action.notin_(_long_retention_actions))
        )
        result_general = await db.execute(stmt_general)
        deleted_general = result_general.rowcount

        # Long-retention logs
        stmt_long = (
            delete(AuditLog)
            .where(AuditLog.created_at < long_threshold)
            .where(AuditLog.action.in_(_long_retention_actions))
        )
        result_long = await db.execute(stmt_long)
        deleted_long = result_long.rowcount

        if deleted_general or deleted_long:
            audit = AuditLog(
                action="AUDIT_LOG_RETENTION_CLEANUP",
                details={
                    "deleted_general": deleted_general,
                    "deleted_financial_kvkk": deleted_long,
                    "general_threshold_days": retention_days,
                    "financial_threshold_days": retention_days * 2,
                },
            )
            db.add(audit)

        await db.commit()

    summary = {
        "deleted_general": deleted_general,
        "deleted_financial_kvkk": deleted_long,
        "timestamp": datetime.now(UTC).isoformat(),
    }
    logger.info("Audit log retention cleanup completed", **summary)
    return summary


def _delete_jsonb_urls(storage: StorageService, data: dict | list | None) -> None:
    """Delete GCS files referenced in a JSONB field (e.g. preview_images, page_images)."""
    if not data:
        return
    urls: list[str] = []
    if isinstance(data, dict):
        urls = [v for v in data.values() if isinstance(v, str) and v.startswith("http")]
    elif isinstance(data, list):
        urls = [v for v in data if isinstance(v, str) and v.startswith("http")]
    for url in urls:
        try:
            storage.delete_file(url)
        except Exception as e:
            logger.warning("Failed to delete JSONB URL", url=url[:80], error=str(e))

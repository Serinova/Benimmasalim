"""Stuck order recovery task - detect and handle orders stuck in PROCESSING."""

from datetime import UTC, datetime, timedelta

import structlog
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session_factory
from app.models.audit_log import AuditLog
from app.models.order import Order, OrderStatus

logger = structlog.get_logger()

# Configuration
STUCK_THRESHOLD_MINUTES = 30  # Orders processing for longer than this are considered stuck
MAX_RETRY_ATTEMPTS = 3  # Maximum retry attempts before marking as failed


async def recover_stuck_orders() -> dict:
    """
    Detect and recover orders that are stuck in PROCESSING state.

    This task should run periodically (e.g., every 15 minutes via Cloud Scheduler).

    Recovery strategy:
    1. Find orders in PROCESSING state for more than STUCK_THRESHOLD_MINUTES
    2. For orders with partial progress, mark them for retry
    3. For orders with no progress after multiple attempts, mark as FAILED
    4. Send notifications to admins for manual review

    Returns:
        Summary of recovery operations
    """
    recovered = 0
    marked_failed = 0
    errors = 0

    async with async_session_factory() as db:
        now = datetime.now(UTC)
        threshold = now - timedelta(minutes=STUCK_THRESHOLD_MINUTES)

        # Find stuck orders
        result = await db.execute(
            select(Order).where(
                and_(
                    Order.status == OrderStatus.PROCESSING,
                    Order.generation_started_at.isnot(None),
                    Order.generation_started_at < threshold,
                )
            )
        )
        stuck_orders = result.scalars().all()

        logger.info(
            "Stuck order recovery started",
            orders_to_process=len(stuck_orders),
            threshold_minutes=STUCK_THRESHOLD_MINUTES,
        )

        for order in stuck_orders:
            try:
                elapsed_minutes = (now - order.generation_started_at).total_seconds() / 60

                # Check if order has made any progress
                has_progress = order.completed_pages > 0

                # Determine recovery action
                if has_progress and order.completed_pages < order.total_pages:
                    # Partial progress - can potentially retry remaining pages
                    order.generation_error = (
                        f"İşlem {elapsed_minutes:.0f} dakika sonra takıldı. "
                        f"Tamamlanan: {order.completed_pages}/{order.total_pages} sayfa."
                    )

                    # Reset for retry (keep completed_pages, just mark for retry)
                    order.generation_started_at = None

                    # Create audit log
                    audit = AuditLog(
                        action="ORDER_STUCK_PARTIAL_RECOVERY",
                        order_id=order.id,
                        details={
                            "elapsed_minutes": elapsed_minutes,
                            "completed_pages": order.completed_pages,
                            "total_pages": order.total_pages,
                            "recovery_action": "marked_for_retry",
                        },
                    )
                    db.add(audit)

                    recovered += 1
                    logger.warning(
                        "Stuck order marked for retry (partial progress)",
                        order_id=str(order.id),
                        completed_pages=order.completed_pages,
                        elapsed_minutes=elapsed_minutes,
                    )

                else:
                    # No progress or repeated failures - mark as failed
                    # Note: We don't change OrderStatus to FAILED here because
                    # FAILED is not in the state machine. Instead, we set
                    # generation_error and keep it in PROCESSING for admin review.
                    order.generation_error = (
                        f"İşlem başarısız oldu. {elapsed_minutes:.0f} dakika sonra ilerleme yok. "
                        "Manuel müdahale gerekiyor."
                    )
                    order.generation_started_at = None

                    # Create audit log
                    audit = AuditLog(
                        action="ORDER_STUCK_NO_PROGRESS",
                        order_id=order.id,
                        details={
                            "elapsed_minutes": elapsed_minutes,
                            "completed_pages": order.completed_pages,
                            "total_pages": order.total_pages,
                            "recovery_action": "marked_for_admin_review",
                        },
                    )
                    db.add(audit)

                    marked_failed += 1
                    logger.error(
                        "Stuck order marked for admin review (no progress)",
                        order_id=str(order.id),
                        elapsed_minutes=elapsed_minutes,
                    )

            except Exception as e:
                errors += 1
                logger.error(
                    "Stuck order recovery error",
                    order_id=str(order.id),
                    error=str(e),
                )

        await db.commit()

    summary = {
        "stuck_orders_found": len(stuck_orders),
        "recovered": recovered,
        "marked_for_review": marked_failed,
        "errors": errors,
        "timestamp": datetime.now(UTC).isoformat(),
    }

    logger.info("Stuck order recovery completed", **summary)

    return summary


async def get_stuck_orders_report(db: AsyncSession) -> list[dict]:
    """
    Get a report of all orders currently stuck in PROCESSING.

    Args:
        db: Database session

    Returns:
        List of stuck order details for admin dashboard
    """
    now = datetime.now(UTC)
    threshold = now - timedelta(minutes=STUCK_THRESHOLD_MINUTES)

    result = await db.execute(
        select(Order)
        .where(
            and_(
                Order.status == OrderStatus.PROCESSING,
                Order.generation_started_at.isnot(None),
                Order.generation_started_at < threshold,
            )
        )
        .order_by(Order.generation_started_at.asc())
    )
    stuck_orders = result.scalars().all()

    return [
        {
            "order_id": str(order.id),
            "child_name": order.child_name,
            "status": order.status.value,
            "completed_pages": order.completed_pages,
            "total_pages": order.total_pages,
            "progress_percent": int((order.completed_pages / order.total_pages) * 100)
            if order.total_pages
            else 0,
            "generation_started_at": order.generation_started_at.isoformat()
            if order.generation_started_at
            else None,
            "elapsed_minutes": (now - order.generation_started_at).total_seconds() / 60
            if order.generation_started_at
            else 0,
            "generation_error": order.generation_error,
            "created_at": order.created_at.isoformat(),
        }
        for order in stuck_orders
    ]


async def retry_stuck_order(order_id: str, db: AsyncSession) -> dict:
    """
    Manually retry a stuck order.

    Args:
        order_id: Order UUID to retry
        db: Database session

    Returns:
        Result of retry operation
    """
    from uuid import UUID

    result = await db.execute(select(Order).where(Order.id == UUID(order_id)))
    order = result.scalar_one_or_none()

    if not order:
        return {"success": False, "error": "Sipariş bulunamadı"}

    if order.status != OrderStatus.PROCESSING:
        return {"success": False, "error": f"Sipariş PROCESSING durumunda değil: {order.status}"}

    # Reset for retry
    order.generation_started_at = None
    order.generation_error = None

    # Create audit log
    audit = AuditLog(
        action="ORDER_MANUAL_RETRY",
        order_id=order.id,
        details={
            "previous_completed_pages": order.completed_pages,
            "total_pages": order.total_pages,
        },
    )
    db.add(audit)

    await db.commit()

    logger.info(
        "Order manually reset for retry",
        order_id=order_id,
        completed_pages=order.completed_pages,
    )

    return {
        "success": True,
        "order_id": order_id,
        "message": "Sipariş yeniden işlenmeye hazır",
        "completed_pages": order.completed_pages,
        "total_pages": order.total_pages,
    }

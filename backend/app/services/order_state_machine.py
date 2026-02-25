"""Order state machine - handles status transitions with validation.

IMPORTANT — ``transition_order`` does NOT commit.  The caller owns the
transaction boundary so that multiple DB mutations (payment fields, promo
rollback, audit log, etc.) are committed atomically.
"""

from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.exceptions import InvalidStateTransition
from app.models.audit_log import AuditLog
from app.models.order import Order, OrderStatus

# Valid state transitions
VALID_TRANSITIONS: dict[OrderStatus, list[OrderStatus]] = {
    OrderStatus.DRAFT: [OrderStatus.TEXT_APPROVED, OrderStatus.CANCELLED],
    OrderStatus.TEXT_APPROVED: [OrderStatus.COVER_APPROVED, OrderStatus.DRAFT],
    OrderStatus.COVER_APPROVED: [OrderStatus.PAYMENT_PENDING, OrderStatus.TEXT_APPROVED],
    OrderStatus.PAYMENT_PENDING: [OrderStatus.PAID, OrderStatus.COVER_APPROVED],
    OrderStatus.PAID: [OrderStatus.PROCESSING],
    OrderStatus.PROCESSING: [OrderStatus.READY_FOR_PRINT],
    OrderStatus.READY_FOR_PRINT: [OrderStatus.SHIPPED],
    OrderStatus.SHIPPED: [OrderStatus.DELIVERED],
    OrderStatus.DELIVERED: [],  # Terminal state
    OrderStatus.CANCELLED: [],  # Terminal state
    OrderStatus.REFUNDED: [],  # Terminal state
}


async def get_order_for_update(
    order_id: UUID,
    db: AsyncSession,
) -> Order | None:
    """Read an order with ``SELECT … FOR UPDATE`` row-level lock.

    Use this before any critical state mutation to prevent TOCTOU races
    (e.g. double-payment, concurrent checkout).
    """
    result = await db.execute(
        select(Order).where(Order.id == order_id).with_for_update()
    )
    return result.scalar_one_or_none()


async def transition_order(
    order: Order,
    new_status: OrderStatus,
    db: AsyncSession,
    actor_id: UUID | None = None,
    ip_address: str | None = None,
    details: dict | None = None,
    *,
    auto_commit: bool = True,
) -> Order:
    """Transition order to a new status with validation and audit logging.

    CRITICAL: Never directly set ``order.status``! Always use this function.

    Parameters
    ----------
    auto_commit : bool
        When *True* (default — backward compat) the function commits the
        transaction.  Set to *False* in payment paths where the caller
        needs to perform additional atomic writes before committing.
    """
    old_status = order.status

    if new_status not in VALID_TRANSITIONS.get(old_status, []):
        raise InvalidStateTransition(old_status.value, new_status.value)

    order.status = new_status

    if new_status == OrderStatus.DELIVERED:
        order.delivered_at = datetime.now(UTC)
        order.photo_deletion_scheduled_at = order.delivered_at + timedelta(
            days=settings.kvkk_retention_days
        )

    audit_details = {
        "from_status": old_status.value,
        "to_status": new_status.value,
    }
    if details:
        audit_details.update(details)

    db.add(AuditLog(
        action=f"ORDER_STATUS_{new_status.value}",
        order_id=order.id,
        user_id=actor_id,
        details=audit_details,
        ip_address=ip_address,
    ))

    if auto_commit:
        await db.commit()
        await db.refresh(order)

    return order


def can_transition(current_status: OrderStatus, target_status: OrderStatus) -> bool:
    """Check if a status transition is valid."""
    return target_status in VALID_TRANSITIONS.get(current_status, [])


def get_next_statuses(current_status: OrderStatus) -> list[OrderStatus]:
    """Get list of valid next statuses for current status."""
    return VALID_TRANSITIONS.get(current_status, [])

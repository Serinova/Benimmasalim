"""StoryPreview state machine — validates status transitions.

Usage:
    from app.services.preview_state_machine import transition_preview

    preview = await transition_preview(preview, "GENERATING", db)
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.story_preview import PreviewStatus, StoryPreview

logger = structlog.get_logger()

# ── Valid transitions ────────────────────────────────────────────────
VALID_PREVIEW_TRANSITIONS: dict[str, list[str]] = {
    # New staged flow
    PreviewStatus.LEAD_CAPTURED: [
        PreviewStatus.GENERATING,
        PreviewStatus.ABANDONED_TRIAL,
    ],
    PreviewStatus.GENERATING: [
        PreviewStatus.PREVIEW_GENERATED,
        PreviewStatus.LEAD_CAPTURED,  # retry
        "FAILED",
    ],
    PreviewStatus.PREVIEW_GENERATED: [
        PreviewStatus.PAYMENT_PENDING,
        PreviewStatus.ABANDONED_TRIAL,
    ],
    PreviewStatus.PAYMENT_PENDING: [
        PreviewStatus.COMPLETING,
        PreviewStatus.ABANDONED_TRIAL,
    ],
    PreviewStatus.COMPLETING: [
        PreviewStatus.COMPLETED,
        "FAILED",
    ],
    PreviewStatus.COMPLETED: [],  # terminal
    PreviewStatus.ABANDONED_TRIAL: [],  # terminal

    # Legacy statuses
    PreviewStatus.PENDING: [
        PreviewStatus.CONFIRMED,
        PreviewStatus.EXPIRED,
        PreviewStatus.CANCELLED,
        "FAILED",
    ],
    PreviewStatus.CONFIRMED: [
        PreviewStatus.PROCESSING,
        PreviewStatus.CANCELLED,
        PreviewStatus.COMPLETED,
        "FAILED",
    ],
    PreviewStatus.PROCESSING: [
        PreviewStatus.COMPLETED,
        "FAILED",
    ],
    PreviewStatus.EXPIRED: [],
    PreviewStatus.CANCELLED: [],
    "FAILED": [
        PreviewStatus.GENERATING,   # admin retry
        PreviewStatus.LEAD_CAPTURED, # admin retry
    ],
}


def can_transition_preview(current_status: str, target_status: str) -> bool:
    """Check whether a preview status transition is valid."""
    allowed = VALID_PREVIEW_TRANSITIONS.get(current_status, [])
    return target_status in allowed


async def transition_preview(
    preview: StoryPreview,
    new_status: str,
    db: AsyncSession,
    *,
    force: bool = False,
) -> StoryPreview:
    """Transition a StoryPreview to *new_status* with validation.

    Args:
        preview: The preview to transition.
        new_status: Target status string (e.g. "GENERATING").
        db: Active async DB session.
        force: Skip validation (admin override).

    Returns:
        The updated preview (already committed).

    Raises:
        ValueError: If transition is not valid (and force=False).
    """
    old_status = preview.status

    if not force and not can_transition_preview(old_status, new_status):
        msg = f"Gecersiz preview gecisi: {old_status} → {new_status}"
        logger.warning(msg, preview_id=str(preview.id))
        raise ValueError(msg)

    preview.status = new_status
    await db.commit()

    logger.info(
        "PREVIEW_STATUS_TRANSITION",
        preview_id=str(preview.id),
        from_status=old_status,
        to_status=new_status,
    )
    return preview

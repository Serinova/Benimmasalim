"""Admin API for Abandoned Trials - Lead Recovery System.

Provides endpoints for admin to:
- View abandoned trials (users who saw preview but didn't buy)
- Mark trials as followed up
- View trial statistics
"""

from datetime import UTC, datetime
from uuid import UUID

import structlog
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import func, select

from app.api.v1.deps import AdminUser, DbSession
from app.models.story_preview import PreviewStatus, StoryPreview
from app.services.trial_service import get_trial_service

logger = structlog.get_logger()
router = APIRouter()


# ============ SCHEMAS ============


class AbandonedTrialResponse(BaseModel):
    """Abandoned trial data for admin view."""

    id: str
    # Contact info
    parent_name: str
    parent_email: str
    parent_phone: str | None
    # Child info
    child_name: str
    child_age: int
    # Story info
    story_title: str
    story_pages: list[dict]
    preview_images: dict
    # Product info
    product_name: str | None
    product_price: float | None
    # Timing
    created_at: str
    preview_shown_at: str | None
    abandoned_at: str | None
    # Follow-up status
    followed_up_at: str | None
    followed_up_by: str | None
    follow_up_notes: str | None


class FollowUpRequest(BaseModel):
    """Request to mark trial as followed up."""

    notes: str | None = None


class TrialStatsResponse(BaseModel):
    """Trial statistics for dashboard."""

    total_leads: int
    preview_generated: int
    converted: int
    abandoned: int
    pending_followup: int
    conversion_rate: float


# ============ ENDPOINTS ============


@router.get("/abandoned", response_model=list[AbandonedTrialResponse])
async def get_abandoned_trials(
    db: DbSession,
    admin: AdminUser,
    limit: int = 50,
    offset: int = 0,
    include_followed_up: bool = False,
) -> list[AbandonedTrialResponse]:
    """
    Get abandoned trials for admin follow-up.

    These are high-quality leads - users who:
    - Entered contact info
    - Generated a story
    - Saw preview images
    - But didn't complete payment

    Admin can call them to convert!
    """
    trial_service = get_trial_service(db)

    trials = await trial_service.get_abandoned_trials(
        limit=limit,
        offset=offset,
        include_followed_up=include_followed_up,
    )

    results = []
    for t in trials:
        # Resimler: Önce preview_images, yoksa page_images kullan (eski akış uyumluluğu)
        images = t.preview_images or t.page_images or {}

        # Hikaye sayfaları: story_pages zaten dolu olmalı
        pages = t.story_pages or []

        results.append(
            AbandonedTrialResponse(
                id=str(t.id),
                parent_name=t.parent_name,
                parent_email=t.parent_email,
                parent_phone=t.parent_phone,
                child_name=t.child_name,
                child_age=t.child_age,
                story_title=t.story_title,
                story_pages=pages,
                preview_images=images,
                product_name=t.product_name,
                product_price=float(t.product_price) if t.product_price else None,
                created_at=t.created_at.isoformat() if t.created_at else None,
                preview_shown_at=t.preview_shown_at.isoformat() if t.preview_shown_at else None,
                abandoned_at=t.abandoned_at.isoformat() if t.abandoned_at else None,
                followed_up_at=t.followed_up_at.isoformat() if t.followed_up_at else None,
                followed_up_by=t.followed_up_by,
                follow_up_notes=t.follow_up_notes,
            )
        )

    return results


@router.get("/abandoned/{trial_id}", response_model=AbandonedTrialResponse)
async def get_abandoned_trial_detail(
    trial_id: str,
    db: DbSession,
    admin: AdminUser,
) -> AbandonedTrialResponse:
    """Get detailed view of a single abandoned trial."""
    result = await db.execute(select(StoryPreview).where(StoryPreview.id == UUID(trial_id)))
    trial = result.scalar_one_or_none()

    if not trial:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trial bulunamadı")

    # Resimler: Önce preview_images, yoksa page_images kullan (eski akış uyumluluğu)
    images = trial.preview_images or trial.page_images or {}

    return AbandonedTrialResponse(
        id=str(trial.id),
        parent_name=trial.parent_name,
        parent_email=trial.parent_email,
        parent_phone=trial.parent_phone,
        child_name=trial.child_name,
        child_age=trial.child_age,
        story_title=trial.story_title,
        story_pages=trial.story_pages or [],
        preview_images=images,
        product_name=trial.product_name,
        product_price=float(trial.product_price) if trial.product_price else None,
        created_at=trial.created_at.isoformat() if trial.created_at else None,
        preview_shown_at=trial.preview_shown_at.isoformat() if trial.preview_shown_at else None,
        abandoned_at=trial.abandoned_at.isoformat() if trial.abandoned_at else None,
        followed_up_at=trial.followed_up_at.isoformat() if trial.followed_up_at else None,
        followed_up_by=trial.followed_up_by,
        follow_up_notes=trial.follow_up_notes,
    )


@router.post("/abandoned/{trial_id}/follow-up")
async def mark_trial_followed_up(
    trial_id: str,
    request: FollowUpRequest,
    db: DbSession,
    admin: AdminUser,
) -> dict:
    """
    Mark an abandoned trial as followed up.

    This logs that admin called the user.
    """
    trial_service = get_trial_service(db)

    trial = await trial_service.mark_followed_up(
        UUID(trial_id),
        admin.email,
        request.notes,
    )

    if not trial:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trial bulunamadı")

    logger.info(
        "Trial marked as followed up",
        trial_id=trial_id,
        admin=admin.email,
    )

    return {
        "success": True,
        "message": "Takip kaydedildi",
        "followed_up_at": trial.followed_up_at.isoformat(),
        "followed_up_by": trial.followed_up_by,
    }


@router.get("/stats", response_model=TrialStatsResponse)
async def get_trial_stats(
    db: DbSession,
    admin: AdminUser,
) -> TrialStatsResponse:
    """Get trial statistics for admin dashboard."""
    from datetime import timedelta

    from sqlalchemy import or_

    # Count by status
    status_query = await db.execute(
        select(StoryPreview.status, func.count(StoryPreview.id)).group_by(StoryPreview.status)
    )
    status_counts = dict(status_query.all())

    # Count old PENDING records (older than 1 hour) as potential abandoned
    cutoff = datetime.now(UTC) - timedelta(hours=1)
    old_pending_query = await db.execute(
        select(func.count(StoryPreview.id)).where(
            StoryPreview.status == PreviewStatus.PENDING.value,
            StoryPreview.created_at < cutoff,
        )
    )
    old_pending = old_pending_query.scalar() or 0

    # Count pending follow-ups (ABANDONED_TRIAL + old PENDING)
    pending_query = await db.execute(
        select(func.count(StoryPreview.id)).where(
            or_(
                StoryPreview.status == PreviewStatus.ABANDONED_TRIAL.value,
                (StoryPreview.status == PreviewStatus.PENDING.value)
                & (StoryPreview.created_at < cutoff),
            ),
            StoryPreview.followed_up_at.is_(None),
        )
    )
    pending_followup = pending_query.scalar() or 0

    total_leads = sum(status_counts.values())
    preview_generated = status_counts.get(PreviewStatus.PREVIEW_GENERATED.value, 0)
    converted = status_counts.get(PreviewStatus.COMPLETED.value, 0) + status_counts.get(
        PreviewStatus.CONFIRMED.value, 0
    )  # Include old CONFIRMED

    # Abandoned = explicit ABANDONED_TRIAL + old PENDING records
    abandoned = status_counts.get(PreviewStatus.ABANDONED_TRIAL.value, 0) + old_pending

    # Calculate conversion rate (from total leads to converted)
    conversion_rate = (converted / total_leads * 100) if total_leads > 0 else 0.0

    return TrialStatsResponse(
        total_leads=total_leads,
        preview_generated=preview_generated,
        converted=converted,
        abandoned=abandoned,
        pending_followup=pending_followup,
        conversion_rate=round(conversion_rate, 2),
    )


@router.post("/mark-abandoned")
async def trigger_mark_abandoned(
    db: DbSession,
    admin: AdminUser,
    hours: int = 1,
) -> dict:
    """
    Manually trigger marking trials AND previews as abandoned.

    Marks as abandoned:
    - Trials: PREVIEW_GENERATED status, no payment after `hours` hours
    - Previews: PENDING status (3 preview images sent, no confirmation after 24 hours)

    Normally this runs on a schedule, but admin can trigger it.
    """
    trial_service = get_trial_service(db)

    trial_count = await trial_service.mark_abandoned_trials(hours=hours)
    preview_count = await trial_service.mark_abandoned_previews(hours=24)

    total = trial_count + preview_count

    return {
        "success": True,
        "message": f"{total} kayıt terk edilmiş olarak işaretlendi "
        f"(trial: {trial_count}, preview: {preview_count})",
        "count": total,
        "trial_count": trial_count,
        "preview_count": preview_count,
    }

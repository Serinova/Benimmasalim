"""Privacy / KVKK endpoints: photo deletion, account deletion, data export."""

import uuid
from datetime import UTC, datetime, timedelta

import structlog
from fastapi import APIRouter, Request
from pydantic import BaseModel
from sqlalchemy import select

from app.api.v1.deps import CurrentUser, DbSession
from app.core.audit import record_audit
from app.core.exceptions import NotFoundError, ValidationError
from app.models.consent import ConsentRecord
from app.models.notification_outbox import NotificationOutbox
from app.models.order import Order

logger = structlog.get_logger()
router = APIRouter()


# ── Photo Deletion (User-Requested) ─────────────────────────────────────────


class DeletePhotoRequest(BaseModel):
    order_id: uuid.UUID | None = None
    child_profile_id: uuid.UUID | None = None


@router.post("/delete-photo-now")
async def delete_photo_now(
    body: DeletePhotoRequest,
    http_request: Request,
    db: DbSession,
    current_user: CurrentUser,
) -> dict:
    """Immediately delete child photo and face data (KVKK).

    Accepts either order_id or child_profile_id (or both).
    Idempotent: returns success even if already deleted.
    """
    from app.models.child_profile import ChildProfile
    from app.services.storage_service import StorageService

    if not body.order_id and not body.child_profile_id:
        raise ValidationError("order_id veya child_profile_id gerekli")

    storage = StorageService()
    deleted_urls: list[str] = []

    # --- Order photo deletion ---
    if body.order_id:
        result = await db.execute(
            select(Order).where(Order.id == body.order_id, Order.user_id == current_user.id)
        )
        order = result.scalar_one_or_none()
        if not order:
            raise NotFoundError("Sipariş")

        if order.child_photo_url:
            deleted_urls.append(order.child_photo_url)

        order.child_photo_url = None
        order.face_embedding = None
        order.face_description = None
        order.photo_deletion_scheduled_at = None

    # --- Child profile photo deletion ---
    if body.child_profile_id:
        cp_result = await db.execute(
            select(ChildProfile).where(
                ChildProfile.id == body.child_profile_id,
                ChildProfile.user_id == current_user.id,
            )
        )
        child_profile = cp_result.scalar_one_or_none()
        if not child_profile:
            raise NotFoundError("Çocuk profili")

        if child_profile.photo_url:
            deleted_urls.append(child_profile.photo_url)

        child_profile.photo_url = None
        child_profile.photo_uploaded_at = None

    # Physical deletion from GCS (best-effort, log failures)
    for url in deleted_urls:
        try:
            storage.delete_file(url)
        except Exception:
            logger.warning("Failed to delete photo from storage", url=url[:120])

    await record_audit(
        db, action="USER_REQUESTED_PHOTO_DELETE",
        user_id=current_user.id,
        order_id=body.order_id,
        request=http_request,
        details={"child_profile_id": str(body.child_profile_id) if body.child_profile_id else None},
    )
    await db.commit()

    return {"message": "Fotoğraf ve yüz verileri başarıyla silindi.", "deleted_files": len(deleted_urls)}


# ── Account Deletion ────────────────────────────────────────────────────────


class DeleteAccountRequest(BaseModel):
    password: str | None = None
    reason: str | None = None


@router.delete("/account")
async def delete_account(
    body: DeleteAccountRequest,
    http_request: Request,
    db: DbSession,
    current_user: CurrentUser,
) -> dict:
    """Request account deletion (soft delete, hard purge after 7 days).

    - Regular users must provide their password.
    - Guest users (no password) can delete without password.
    - Increments token_version to immediately revoke ALL existing JWTs.
    - Login within 7 days restores the account (grace period).
    """
    from app.core.security import verify_password

    if current_user.hashed_password:
        if not body.password:
            raise ValidationError("Şifrenizi girmeniz gerekiyor")
        if not verify_password(body.password, current_user.hashed_password):
            raise ValidationError("Şifre hatalı")

    current_user.is_active = False
    current_user.deletion_scheduled_at = datetime.now(UTC) + timedelta(days=7)
    current_user.token_version = (current_user.token_version or 0) + 1

    await record_audit(
        db, action="ACCOUNT_DELETION_REQUESTED",
        user_id=current_user.id, request=http_request,
        details={"reason": body.reason, "scheduled_at": str(current_user.deletion_scheduled_at)},
    )
    await db.commit()

    return {"message": "Hesabınız 7 gün içinde kalıcı olarak silinecektir. İptal etmek için giriş yapın."}


# ── Data Export ──────────────────────────────────────────────────────────────


@router.get("/export-data")
async def export_data(
    http_request: Request,
    db: DbSession,
    current_user: CurrentUser,
) -> dict:
    """Export all user data as JSON (KVKK right of access)."""
    # Orders
    orders_result = await db.execute(
        select(Order).where(Order.user_id == current_user.id).order_by(Order.created_at.desc())
    )
    orders = orders_result.scalars().all()

    orders_data = [
        {
            "id": str(o.id),
            "status": o.status if isinstance(o.status, str) else o.status.value,
            "child_name": o.child_name,
            "child_age": o.child_age,
            "payment_amount": str(o.payment_amount) if o.payment_amount else None,
            "payment_status": o.payment_status,
            "created_at": str(o.created_at),
            "tracking_number": o.tracking_number,
            "carrier": o.carrier,
        }
        for o in orders
    ]

    # Consent records
    consents_result = await db.execute(
        select(ConsentRecord).where(ConsentRecord.user_id == current_user.id)
    )
    consents_data = [
        {
            "consent_type": c.consent_type,
            "action": c.action,
            "consent_version": c.consent_version,
            "created_at": str(c.created_at),
        }
        for c in consents_result.scalars().all()
    ]

    # Notification history
    notif_result = await db.execute(
        select(NotificationOutbox).where(NotificationOutbox.user_id == current_user.id)
        .order_by(NotificationOutbox.created_at.desc())
    )
    notifications_data = [
        {
            "order_id": str(n.order_id),
            "channel": n.channel,
            "event_type": n.event_type,
            "order_status": n.order_status,
            "status": n.status,
            "created_at": str(n.created_at),
            "sent_at": str(n.sent_at) if n.sent_at else None,
        }
        for n in notif_result.scalars().all()
    ]

    await record_audit(
        db, action="USER_DATA_EXPORTED",
        user_id=current_user.id, request=http_request,
    )
    await db.commit()

    return {
        "user": {
            "id": str(current_user.id),
            "email": current_user.email,
            "full_name": current_user.full_name,
            "phone": current_user.phone,
            "is_guest": current_user.is_guest,
            "created_at": str(current_user.created_at),
        },
        "orders": orders_data,
        "consents": consents_data,
        "notifications": notifications_data,
        "exported_at": str(datetime.now(UTC)),
    }

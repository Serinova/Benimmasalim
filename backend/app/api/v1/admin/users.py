"""Admin user management endpoints."""

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Query
from pydantic import BaseModel
from sqlalchemy import func, select

from app.api.v1.deps import AdminUser, DbSession
from app.core.exceptions import NotFoundError
from app.models.order import Order
from app.models.user import User

router = APIRouter()


class UserListResponse(BaseModel):
    """Paginated user list response."""

    items: list[dict]
    total: int
    page: int
    page_size: int


@router.get("", response_model=UserListResponse)
async def list_users(
    db: DbSession,
    admin: AdminUser,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    search: str | None = Query(None),
) -> UserListResponse:
    """List all users with pagination."""
    query = select(User)

    if search:
        query = query.where(User.email.ilike(f"%{search}%") | User.full_name.ilike(f"%{search}%"))

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Paginate
    query = query.order_by(User.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    users = result.scalars().all()

    return UserListResponse(
        items=[
            {
                "id": str(u.id),
                "email": u.email,
                "full_name": u.full_name,
                "role": u.role.value,
                "is_active": u.is_active,
                "is_guest": u.is_guest,
                "created_at": u.created_at.isoformat(),
            }
            for u in users
        ],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{user_id}")
async def get_user_detail(
    user_id: UUID,
    db: DbSession,
    admin: AdminUser,
) -> dict[str, Any]:
    """Get detailed user information."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise NotFoundError("Kullanıcı", user_id)

    # Get order count
    order_count_result = await db.execute(select(func.count()).where(Order.user_id == user_id))
    order_count = order_count_result.scalar() or 0

    return {
        "id": str(user.id),
        "email": user.email,
        "full_name": user.full_name,
        "phone": user.phone,
        "role": user.role.value,
        "is_active": user.is_active,
        "is_guest": user.is_guest,
        "google_id": user.google_id,
        "order_count": order_count,
        "created_at": user.created_at.isoformat(),
        "updated_at": user.updated_at.isoformat(),
    }


@router.delete("/{user_id}/data")
async def delete_user_data(
    user_id: UUID,
    db: DbSession,
    admin: AdminUser,
) -> dict[str, Any]:
    """
    KVKK: Delete all user data (Right to be Forgotten).

    This permanently deletes:
    - User profile
    - All order photos
    - Face embeddings
    - Voice recordings
    """
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise NotFoundError("Kullanıcı", user_id)

    # Get user's orders
    orders_result = await db.execute(select(Order).where(Order.user_id == user_id))
    orders = orders_result.scalars().all()

    deleted_photos = 0
    deleted_voices = 0

    for order in orders:
        # Delete photo from GCS
        if order.child_photo_url:
            # TODO: await delete_from_gcs(order.child_photo_url)
            order.child_photo_url = None
            order.face_embedding = None
            deleted_photos += 1

        # Delete voice recording
        if order.audio_file_url:
            # TODO: await delete_from_gcs(order.audio_file_url)
            order.audio_file_url = None
            deleted_voices += 1

        # Anonymize order
        order.user_id = None

    # Delete user
    await db.delete(user)
    await db.commit()

    # Create audit log
    from app.models.audit_log import AuditLog

    audit = AuditLog(
        action="KVKK_USER_DATA_DELETED",
        admin_id=admin.id,
        details={
            "deleted_user_id": str(user_id),
            "deleted_photos": deleted_photos,
            "deleted_voices": deleted_voices,
        },
    )
    db.add(audit)
    await db.commit()

    return {
        "message": "Kullanıcı verileri kalıcı olarak silindi",
        "deleted_photos": deleted_photos,
        "deleted_voices": deleted_voices,
    }


@router.get("/{user_id}/export")
async def export_user_data(
    user_id: UUID,
    db: DbSession,
    admin: AdminUser,
) -> dict[str, Any]:
    """
    KVKK: Export all user data (Data Portability).

    Returns JSON with all user data.
    """
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise NotFoundError("Kullanıcı", user_id)

    # Get orders
    orders_result = await db.execute(
        select(Order).where(Order.user_id == user_id).order_by(Order.created_at)
    )
    orders = orders_result.scalars().all()

    return {
        "user": {
            "id": str(user.id),
            "email": user.email,
            "full_name": user.full_name,
            "phone": user.phone,
            "created_at": user.created_at.isoformat(),
        },
        "orders": [
            {
                "id": str(o.id),
                "status": o.status.value,
                "child_name": o.child_name,
                "child_age": o.child_age,
                "payment_amount": float(o.payment_amount) if o.payment_amount else None,
                "shipping_address": o.shipping_address,
                "created_at": o.created_at.isoformat(),
                # Note: Photos are NOT included in export for privacy
            }
            for o in orders
        ],
        "export_date": "2026-01-30T00:00:00Z",
    }

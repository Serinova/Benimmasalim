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
                "role": u.role.value if hasattr(u.role, "value") else str(u.role),
                "is_active": u.is_active,
                "is_guest": getattr(u, "is_guest", False),
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
        "role": user.role.value if hasattr(user.role, "value") else str(user.role),
        "is_active": user.is_active,
        "is_guest": getattr(user, "is_guest", False),
        "google_id": user.google_id,
        "order_count": order_count,
        "created_at": user.created_at.isoformat(),
        "updated_at": user.updated_at.isoformat(),
    }



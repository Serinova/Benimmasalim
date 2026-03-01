"""KVKK Management API endpoints for admin panel."""

from datetime import UTC, datetime, timedelta
from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import AdminUser, get_db
from app.models.audit_log import AuditLog
from app.models.order import Order, OrderStatus
from app.models.user import User
from app.tasks.kvkk_cleanup import (
    delete_user_data,
    kvkk_abandoned_preview_cleanup,
    kvkk_photo_cleanup,
)

logger = structlog.get_logger()

router = APIRouter()


# ============================================================================
# Response Models
# ============================================================================


class KVKKStats(BaseModel):
    """KVKK istatistikleri."""

    total_users: int
    total_orders_with_photos: int
    pending_deletions: int  # Silinme sırasında bekleyenler
    deleted_last_30_days: int
    next_scheduled_deletion: str | None
    kvkk_retention_days: int = 30


class DeletionQueueItem(BaseModel):
    """Silinme sırasındaki sipariş."""

    order_id: str
    child_name: str
    delivered_at: str
    scheduled_deletion: str
    days_remaining: int
    has_photo: bool
    has_cloned_voice: bool


class AuditLogItem(BaseModel):
    """Audit log kaydı."""

    id: int
    action: str
    order_id: str | None
    user_id: str | None
    details: dict | None
    created_at: str


class UserDataExport(BaseModel):
    """Kullanıcı veri export formatı."""

    user_id: str
    email: str | None
    full_name: str | None
    created_at: str
    orders: list[dict]
    exported_at: str
    valid_until: str  # 7 gün geçerli


class DeleteUserResponse(BaseModel):
    """Kullanıcı silme sonucu."""

    success: bool
    user_deleted: bool
    orders_anonymized: int
    photos_deleted: int
    audio_deleted: int
    message: str


class ManualCleanupResponse(BaseModel):
    """Manuel temizlik sonucu."""

    processed: int
    deleted: int
    errors: int
    timestamp: str


# ============================================================================
# Stats & Overview
# ============================================================================


@router.get("/stats", response_model=KVKKStats)
async def get_kvkk_stats(admin: AdminUser, db: AsyncSession = Depends(get_db)) -> KVKKStats:
    """KVKK istatistiklerini getir."""
    now = datetime.now(UTC)

    # Toplam kullanıcı sayısı
    total_users = await db.scalar(select(func.count(User.id)))

    # Fotoğrafı olan sipariş sayısı
    total_with_photos = await db.scalar(
        select(func.count(Order.id)).where(Order.child_photo_url.isnot(None))
    )

    # Silinme bekleyen (DELIVERED ve henüz silinmemiş)
    pending_deletions = await db.scalar(
        select(func.count(Order.id)).where(
            Order.status == OrderStatus.DELIVERED,
            Order.photo_deletion_scheduled_at.isnot(None),
            Order.photo_deletion_scheduled_at > now,
            Order.child_photo_url.isnot(None),
        )
    )

    # Son 30 günde silinen
    thirty_days_ago = now - timedelta(days=30)
    deleted_count = await db.scalar(
        select(func.count(AuditLog.id)).where(
            AuditLog.action == "KVKK_PHOTO_DELETED", AuditLog.created_at >= thirty_days_ago
        )
    )

    # Bir sonraki silinme tarihi
    next_deletion = await db.scalar(
        select(func.min(Order.photo_deletion_scheduled_at)).where(
            Order.status == OrderStatus.DELIVERED,
            Order.photo_deletion_scheduled_at > now,
            Order.child_photo_url.isnot(None),
        )
    )

    return KVKKStats(
        total_users=total_users or 0,
        total_orders_with_photos=total_with_photos or 0,
        pending_deletions=pending_deletions or 0,
        deleted_last_30_days=deleted_count or 0,
        next_scheduled_deletion=next_deletion.isoformat() if next_deletion else None,
    )


# ============================================================================
# Deletion Queue
# ============================================================================


@router.get("/deletion-queue", response_model=list[DeletionQueueItem])
async def get_deletion_queue(
    admin: AdminUser, db: AsyncSession = Depends(get_db), limit: int = 50
) -> list[DeletionQueueItem]:
    """Silinme sırasındaki siparişleri listele."""
    now = datetime.now(UTC)

    result = await db.execute(
        select(Order)
        .where(
            Order.status == OrderStatus.DELIVERED,
            Order.photo_deletion_scheduled_at.isnot(None),
            Order.child_photo_url.isnot(None),
        )
        .order_by(Order.photo_deletion_scheduled_at.asc())
        .limit(limit)
    )
    orders = result.scalars().all()

    items = []
    for order in orders:
        days_remaining = (order.photo_deletion_scheduled_at - now).days
        items.append(
            DeletionQueueItem(
                order_id=str(order.id),
                child_name=order.child_name,
                delivered_at=order.delivered_at.isoformat() if order.delivered_at else "",
                scheduled_deletion=order.photo_deletion_scheduled_at.isoformat(),
                days_remaining=max(0, days_remaining),
                has_photo=order.child_photo_url is not None,
                has_cloned_voice=order.audio_type == "cloned" and order.audio_file_url is not None,
            )
        )

    return items


# ============================================================================
# Audit Logs
# ============================================================================


@router.get("/audit-logs", response_model=list[AuditLogItem])
async def get_kvkk_audit_logs(
    admin: AdminUser, db: AsyncSession = Depends(get_db), action_filter: str | None = None, limit: int = 100
) -> list[AuditLogItem]:
    """KVKK ile ilgili audit loglarını getir."""
    query = select(AuditLog).where(
        AuditLog.action.in_(
            [
                "KVKK_PHOTO_DELETED",
                "USER_DATA_DELETED",
                "USER_DATA_EXPORTED",
                "MANUAL_KVKK_CLEANUP",
                "KVKK_ABANDONED_PREVIEWS_DELETED",
                "CONSENT_RECORDED",
                "CONSENT_WITHDRAWN",
                "DATA_REQUEST_SUBMITTED",
            ]
        )
    )

    if action_filter:
        query = query.where(AuditLog.action == action_filter)

    query = query.order_by(AuditLog.created_at.desc()).limit(limit)

    result = await db.execute(query)
    logs = result.scalars().all()

    return [
        AuditLogItem(
            id=log.id,
            action=log.action,
            order_id=str(log.order_id) if log.order_id else None,
            user_id=str(log.user_id) if log.user_id else None,
            details=log.details,
            created_at=log.created_at.isoformat(),
        )
        for log in logs
    ]


# ============================================================================
# User Data Export (Veri Taşınabilirliği)
# ============================================================================


@router.get("/export-user-data/{user_id}", response_model=UserDataExport)
async def export_user_data(user_id: str, admin: AdminUser, db: AsyncSession = Depends(get_db)) -> UserDataExport:
    """
    Kullanıcının tüm verilerini JSON formatında export et.
    KVKK Veri Taşınabilirliği hakkı.
    """
    try:
        uid = UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Geçersiz kullanıcı ID")

    # Kullanıcıyı bul
    user_result = await db.execute(select(User).where(User.id == uid))
    user = user_result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı")

    # Kullanıcının siparişlerini al
    orders_result = await db.execute(select(Order).where(Order.user_id == uid))
    orders = orders_result.scalars().all()

    now = datetime.now(UTC)
    valid_until = now + timedelta(days=7)

    # Sipariş verilerini hazırla (fotoğraf URL'leri hariç - güvenlik)
    orders_data = []
    for order in orders:
        orders_data.append(
            {
                "order_id": str(order.id),
                "child_name": order.child_name,
                "child_age": order.child_age,
                "child_gender": order.child_gender,
                "status": order.status.value
                if hasattr(order.status, "value")
                else str(order.status),
                "has_audio_book": order.has_audio_book,
                "audio_type": order.audio_type,
                "payment_amount": float(order.payment_amount) if order.payment_amount else None,
                "shipping_address": order.shipping_address,
                "created_at": order.created_at.isoformat() if order.created_at else None,
                "delivered_at": order.delivered_at.isoformat() if order.delivered_at else None,
                # Fotoğraf URL'leri dahil değil - güvenlik nedeniyle
                "note": "Fotoğraf ve ses dosyaları güvenlik nedeniyle dahil edilmemiştir.",
            }
        )

    # Audit log kaydet
    audit = AuditLog(
        action="USER_DATA_EXPORTED",
        user_id=uid,
        details={
            "exported_at": now.isoformat(),
            "orders_count": len(orders_data),
            "valid_until": valid_until.isoformat(),
        },
    )
    db.add(audit)
    await db.commit()

    logger.info("User data exported", user_id=user_id, orders_count=len(orders_data))

    return UserDataExport(
        user_id=str(user.id),
        email=user.email,
        full_name=user.full_name,
        created_at=user.created_at.isoformat() if user.created_at else "",
        orders=orders_data,
        exported_at=now.isoformat(),
        valid_until=valid_until.isoformat(),
    )


# ============================================================================
# Delete User (Unutulma Hakkı)
# ============================================================================


@router.post("/delete-user/{user_id}", response_model=DeleteUserResponse)
async def delete_user_request(
    user_id: str, admin: AdminUser, db: AsyncSession = Depends(get_db)
) -> DeleteUserResponse:
    """
    Kullanıcının tüm verilerini sil (Unutulma Hakkı).

    Silinecekler:
    - Çocuk fotoğrafları (GCS'den)
    - Klonlanmış ses kayıtları (GCS'den)
    - Face embedding vektörleri
    - Kullanıcı hesabı

    Siparişler anonimleştirilir (iş kayıtları için tutulur).
    """
    try:
        result = await delete_user_data(user_id, db)

        logger.info("User data deleted (Right to be Forgotten)", user_id=user_id, **result)

        return DeleteUserResponse(
            success=True,
            user_deleted=result["user_deleted"],
            orders_anonymized=result["orders_anonymized"],
            photos_deleted=result["photos_deleted"],
            audio_deleted=result["audio_deleted"],
            message="Kullanıcı verileri başarıyla silindi. Siparişler anonimleştirildi.",
        )

    except Exception as e:
        logger.error("Failed to delete user data", user_id=user_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"Veri silme işlemi başarısız: {str(e)}")


# ============================================================================
# Manual Cleanup
# ============================================================================


@router.post("/manual-cleanup", response_model=ManualCleanupResponse)
async def run_manual_cleanup(admin: AdminUser) -> ManualCleanupResponse:
    """
    KVKK otomatik silme işlemini manuel olarak çalıştır.

    Normalde her gece 02:00'da otomatik çalışır.
    Acil durumlarda admin tarafından manuel tetiklenebilir.
    """
    try:
        result = await kvkk_photo_cleanup()
        preview_result = await kvkk_abandoned_preview_cleanup()

        logger.info("Manual KVKK cleanup executed", photo_result=result, preview_result=preview_result)

        return ManualCleanupResponse(
            processed=result["processed"] + preview_result["deleted"],
            deleted=result["deleted"] + preview_result["deleted"],
            errors=result["errors"] + preview_result["errors"],
            timestamp=result["timestamp"],
        )

    except Exception as e:
        logger.error("Manual KVKK cleanup failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Temizlik işlemi başarısız: {str(e)}")


# ============================================================================
# Users List (for admin to see who can be deleted)
# ============================================================================


class UserListItem(BaseModel):
    """Kullanıcı listesi item."""

    id: str
    email: str | None
    full_name: str | None
    orders_count: int
    photos_count: int
    created_at: str
    is_active: bool


@router.get("/users", response_model=list[UserListItem])
async def list_users_for_kvkk(
    admin: AdminUser, db: AsyncSession = Depends(get_db), search: str | None = None, limit: int = 50
) -> list[UserListItem]:
    """KVKK yönetimi için kullanıcı listesi."""
    query = select(User)

    if search:
        query = query.where(
            (User.email.ilike(f"%{search}%")) | (User.full_name.ilike(f"%{search}%"))
        )

    query = query.order_by(User.created_at.desc()).limit(limit)

    result = await db.execute(query)
    users = result.scalars().all()

    user_items = []
    for user in users:
        # Her kullanıcı için sipariş ve fotoğraf sayısını al
        orders_count = await db.scalar(select(func.count(Order.id)).where(Order.user_id == user.id))
        photos_count = await db.scalar(
            select(func.count(Order.id)).where(
                Order.user_id == user.id, Order.child_photo_url.isnot(None)
            )
        )

        user_items.append(
            UserListItem(
                id=str(user.id),
                email=user.email,
                full_name=user.full_name,
                orders_count=orders_count or 0,
                photos_count=photos_count or 0,
                created_at=user.created_at.isoformat() if user.created_at else "",
                is_active=user.is_active,
            )
        )

    return user_items

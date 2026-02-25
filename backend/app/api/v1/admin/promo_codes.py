"""Admin promo code management endpoints."""

from uuid import UUID

import structlog
from fastapi import APIRouter, Query
from sqlalchemy import func, select

from app.api.v1.deps import AdminUser, DbSession
from app.core.exceptions import ConflictError, NotFoundError
from app.models.audit_log import AuditLog
from app.models.promo_code import PromoCode
from app.schemas.promo_code import (
    BulkGenerateRequest,
    BulkGenerateResponse,
    PromoCodeCreate,
    PromoCodeListResponse,
    PromoCodeResponse,
    PromoCodeUpdate,
)
from app.services.promo_code_service import generate_promo_code

logger = structlog.get_logger()
router = APIRouter()

_RESOURCE_NAME = "Kupon kodu"


def _log_audit(
    db, action: str, admin_id: UUID, details: dict | None = None
) -> None:
    """Write an audit log entry for promo code actions."""
    log = AuditLog(action=action, admin_id=admin_id, details=details or {})
    db.add(log)


@router.post("", response_model=PromoCodeResponse)
async def create_promo_code(
    request: PromoCodeCreate,
    db: DbSession,
    admin: AdminUser,
) -> PromoCodeResponse:
    """Create a new promo code."""
    # Auto-generate code if not provided
    code = request.code
    if not code:
        code = await generate_promo_code(db)
    else:
        # Check uniqueness
        result = await db.execute(
            select(PromoCode).where(PromoCode.code == code)
        )
        if result.scalar_one_or_none():
            raise ConflictError(f"'{code}' kupon kodu zaten mevcut")

    promo = PromoCode(
        code=code,
        discount_type=request.discount_type.value,
        discount_value=request.discount_value,
        usage_limit=request.usage_limit,
        used_count=0,
        is_active=True,
        valid_from=request.valid_from,
        valid_until=request.valid_until,
        min_order_amount=request.min_order_amount,
        max_discount_amount=request.max_discount_amount,
        notes=request.notes,
        created_by=admin.id,
    )
    db.add(promo)

    _log_audit(db, "PROMO_CODE_CREATED", admin.id, {
        "code": code,
        "discount_type": request.discount_type.value,
        "discount_value": str(request.discount_value),
        "usage_limit": request.usage_limit,
    })

    await db.commit()
    await db.refresh(promo)

    logger.info("promo_code_created", code=code, admin_id=str(admin.id))
    return PromoCodeResponse.model_validate(promo)


@router.get("", response_model=PromoCodeListResponse)
async def list_promo_codes(
    db: DbSession,
    admin: AdminUser,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    is_active: bool | None = Query(None, description="Filter by active status"),
    search: str | None = Query(None, description="Search by code"),
) -> PromoCodeListResponse:
    """List promo codes with filtering and pagination."""
    query = select(PromoCode)

    if is_active is not None:
        query = query.where(PromoCode.is_active == is_active)

    if search:
        query = query.where(PromoCode.code.ilike(f"%{search.strip().upper()}%"))

    # Total count
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    # Paginate
    query = query.order_by(PromoCode.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    promos = result.scalars().all()

    return PromoCodeListResponse(
        items=[PromoCodeResponse.model_validate(p) for p in promos],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{promo_id}", response_model=PromoCodeResponse)
async def get_promo_code(
    promo_id: UUID,
    db: DbSession,
    admin: AdminUser,
) -> PromoCodeResponse:
    """Get promo code detail."""
    result = await db.execute(
        select(PromoCode).where(PromoCode.id == promo_id)
    )
    promo = result.scalar_one_or_none()
    if not promo:
        raise NotFoundError(_RESOURCE_NAME, promo_id)

    return PromoCodeResponse.model_validate(promo)


@router.patch("/{promo_id}", response_model=PromoCodeResponse)
async def update_promo_code(
    promo_id: UUID,
    request: PromoCodeUpdate,
    db: DbSession,
    admin: AdminUser,
) -> PromoCodeResponse:
    """Update an existing promo code."""
    result = await db.execute(
        select(PromoCode).where(PromoCode.id == promo_id)
    )
    promo = result.scalar_one_or_none()
    if not promo:
        raise NotFoundError(_RESOURCE_NAME, promo_id)

    changed_fields: dict[str, str] = {}
    update_data = request.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        if field == "discount_type" and value is not None:
            value = value.value  # Enum -> str
        old_val = getattr(promo, field)
        if old_val != value:
            changed_fields[field] = f"{old_val} -> {value}"
            setattr(promo, field, value)

    if changed_fields:
        _log_audit(db, "PROMO_CODE_UPDATED", admin.id, {
            "promo_id": str(promo_id),
            "code": promo.code,
            "changed_fields": changed_fields,
        })
        await db.commit()
        await db.refresh(promo)
        logger.info("promo_code_updated", code=promo.code, changes=changed_fields)

    return PromoCodeResponse.model_validate(promo)


@router.delete("/{promo_id}", response_model=PromoCodeResponse)
async def delete_promo_code(
    promo_id: UUID,
    db: DbSession,
    admin: AdminUser,
) -> PromoCodeResponse:
    """Soft-delete a promo code (set is_active=False)."""
    result = await db.execute(
        select(PromoCode).where(PromoCode.id == promo_id)
    )
    promo = result.scalar_one_or_none()
    if not promo:
        raise NotFoundError(_RESOURCE_NAME, promo_id)

    promo.is_active = False

    _log_audit(db, "PROMO_CODE_DEACTIVATED", admin.id, {
        "promo_id": str(promo_id),
        "code": promo.code,
    })

    await db.commit()
    await db.refresh(promo)

    logger.info("promo_code_deactivated", code=promo.code)
    return PromoCodeResponse.model_validate(promo)


@router.post("/bulk-generate", response_model=BulkGenerateResponse)
async def bulk_generate_promo_codes(
    request: BulkGenerateRequest,
    db: DbSession,
    admin: AdminUser,
) -> BulkGenerateResponse:
    """Bulk generate N promo codes with shared settings."""
    codes: list[PromoCode] = []

    for _ in range(request.count):
        code_str = await generate_promo_code(
            db, prefix=request.prefix or ""
        )
        promo = PromoCode(
            code=code_str,
            discount_type=request.discount_type.value,
            discount_value=request.discount_value,
            usage_limit=request.usage_limit,
            used_count=0,
            is_active=True,
            valid_from=request.valid_from,
            valid_until=request.valid_until,
            min_order_amount=request.min_order_amount,
            max_discount_amount=request.max_discount_amount,
            notes=request.notes,
            created_by=admin.id,
        )
        db.add(promo)
        codes.append(promo)

    _log_audit(db, "PROMO_CODE_BULK_GENERATED", admin.id, {
        "count": request.count,
        "discount_type": request.discount_type.value,
        "discount_value": str(request.discount_value),
        "prefix": request.prefix,
    })

    await db.commit()

    # Refresh all to get generated IDs and timestamps
    for promo in codes:
        await db.refresh(promo)

    logger.info(
        "promo_codes_bulk_generated",
        count=request.count,
        admin_id=str(admin.id),
    )

    return BulkGenerateResponse(
        codes=[PromoCodeResponse.model_validate(p) for p in codes],
        count=len(codes),
    )

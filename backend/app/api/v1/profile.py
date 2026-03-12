"""Profile management endpoints: addresses, notification preferences, child profiles."""

import uuid

import structlog
from fastapi import APIRouter, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import CurrentUser, DbSession
from app.core.exceptions import NotFoundError, ValidationError
from app.models.child_profile import ChildProfile
from app.models.notification_preference import NotificationPreference
from app.models.order import Order
from app.models.user_address import UserAddress

logger = structlog.get_logger()
router = APIRouter()

# ── Address Schemas ──────────────────────────────────────────────────────────


class AddressCreate(BaseModel):
    label: str = Field(default="Ev", max_length=50)
    full_name: str = Field(..., min_length=2, max_length=100)
    phone: str | None = Field(default=None, max_length=20)
    address_line: str = Field(..., min_length=5)
    city: str = Field(..., min_length=2, max_length=50)
    district: str | None = Field(default=None, max_length=50)
    postal_code: str | None = Field(default=None, max_length=10)
    is_default: bool = False


class AddressUpdate(BaseModel):
    label: str | None = Field(default=None, max_length=50)
    full_name: str | None = Field(default=None, max_length=100)
    phone: str | None = Field(default=None, max_length=20)
    address_line: str | None = None
    city: str | None = Field(default=None, max_length=50)
    district: str | None = Field(default=None, max_length=50)
    postal_code: str | None = Field(default=None, max_length=10)
    is_default: bool | None = None


class AddressResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    label: str
    full_name: str
    phone: str | None
    address_line: str
    city: str
    district: str | None
    postal_code: str | None
    is_default: bool


def _addr_to_response(addr: UserAddress) -> AddressResponse:
    return AddressResponse(
        id=str(addr.id),
        label=addr.label,
        full_name=addr.full_name,
        phone=addr.phone,
        address_line=addr.address_line,
        city=addr.city,
        district=addr.district,
        postal_code=addr.postal_code,
        is_default=addr.is_default,
    )


# ── Address CRUD ─────────────────────────────────────────────────────────────

_MAX_ADDRESSES = 5


@router.get("/addresses", response_model=list[AddressResponse])
async def list_addresses(db: DbSession, current_user: CurrentUser) -> list[AddressResponse]:
    result = await db.execute(
        select(UserAddress)
        .where(UserAddress.user_id == current_user.id)
        .order_by(UserAddress.is_default.desc(), UserAddress.created_at.desc())
    )
    return [_addr_to_response(a) for a in result.scalars().all()]


@router.post("/addresses", response_model=AddressResponse, status_code=status.HTTP_201_CREATED)
async def create_address(
    body: AddressCreate, db: DbSession, current_user: CurrentUser,
) -> AddressResponse:
    count_result = await db.execute(
        select(func.count()).select_from(UserAddress).where(UserAddress.user_id == current_user.id)
    )
    if (count_result.scalar() or 0) >= _MAX_ADDRESSES:
        raise ValidationError(f"En fazla {_MAX_ADDRESSES} adres ekleyebilirsiniz")

    if body.is_default:
        await _clear_default(db, current_user.id)

    addr = UserAddress(
        user_id=current_user.id,
        label=body.label,
        full_name=body.full_name,
        phone=body.phone,
        address_line=body.address_line,
        city=body.city,
        district=body.district,
        postal_code=body.postal_code,
        is_default=body.is_default,
    )
    db.add(addr)
    await db.commit()
    await db.refresh(addr)
    return _addr_to_response(addr)


@router.patch("/addresses/{address_id}", response_model=AddressResponse)
async def update_address(
    address_id: uuid.UUID, body: AddressUpdate, db: DbSession, current_user: CurrentUser,
) -> AddressResponse:
    addr = await _get_user_address(db, address_id, current_user.id)

    for field, value in body.model_dump(exclude_unset=True).items():
        if field == "is_default" and value is True:
            await _clear_default(db, current_user.id)
        setattr(addr, field, value)

    await db.commit()
    await db.refresh(addr)
    return _addr_to_response(addr)


@router.delete("/addresses/{address_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_address(
    address_id: uuid.UUID, db: DbSession, current_user: CurrentUser,
) -> None:
    addr = await _get_user_address(db, address_id, current_user.id)
    await db.delete(addr)
    await db.commit()


@router.patch("/addresses/{address_id}/set-default", response_model=AddressResponse)
async def set_default_address(
    address_id: uuid.UUID, db: DbSession, current_user: CurrentUser,
) -> AddressResponse:
    addr = await _get_user_address(db, address_id, current_user.id)
    await _clear_default(db, current_user.id)
    addr.is_default = True
    await db.commit()
    await db.refresh(addr)
    return _addr_to_response(addr)


async def _get_user_address(db: AsyncSession, address_id: uuid.UUID, user_id: uuid.UUID) -> UserAddress:
    result = await db.execute(
        select(UserAddress).where(UserAddress.id == address_id, UserAddress.user_id == user_id)
    )
    addr = result.scalar_one_or_none()
    if not addr:
        raise NotFoundError("Adres")
    return addr


async def _clear_default(db: AsyncSession, user_id: uuid.UUID) -> None:
    result = await db.execute(
        select(UserAddress).where(UserAddress.user_id == user_id, UserAddress.is_default.is_(True))
    )
    for a in result.scalars().all():
        a.is_default = False


# ── Notification Preferences ─────────────────────────────────────────────────


class NotificationPrefsResponse(BaseModel):
    email_order_updates: bool
    email_marketing: bool
    sms_order_updates: bool


class NotificationPrefsUpdate(BaseModel):
    email_order_updates: bool | None = None
    email_marketing: bool | None = None
    sms_order_updates: bool | None = None


@router.get("/notification-preferences", response_model=NotificationPrefsResponse)
async def get_notification_prefs(db: DbSession, current_user: CurrentUser) -> NotificationPrefsResponse:
    result = await db.execute(
        select(NotificationPreference).where(NotificationPreference.user_id == current_user.id)
    )
    pref = result.scalar_one_or_none()
    if not pref:
        return NotificationPrefsResponse(
            email_order_updates=True, email_marketing=False, sms_order_updates=False,
        )
    return NotificationPrefsResponse(
        email_order_updates=pref.email_order_updates,
        email_marketing=pref.email_marketing,
        sms_order_updates=pref.sms_order_updates,
    )


@router.patch("/notification-preferences", response_model=NotificationPrefsResponse)
async def update_notification_prefs(
    body: NotificationPrefsUpdate, db: DbSession, current_user: CurrentUser,
) -> NotificationPrefsResponse:
    result = await db.execute(
        select(NotificationPreference).where(NotificationPreference.user_id == current_user.id)
    )
    pref = result.scalar_one_or_none()

    if not pref:
        pref = NotificationPreference(user_id=current_user.id)
        db.add(pref)

    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(pref, field, value)

    await db.commit()
    await db.refresh(pref)
    return NotificationPrefsResponse(
        email_order_updates=pref.email_order_updates,
        email_marketing=pref.email_marketing,
        sms_order_updates=pref.sms_order_updates,
    )


# ── Child Profiles ───────────────────────────────────────────────────────────

_MAX_CHILDREN = 10


class ChildCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    age: int = Field(..., ge=1, le=18)
    gender: str | None = Field(default=None, max_length=10)


class ChildResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    age: int
    gender: str | None
    photo_url: str | None
    order_count: int = 0


@router.get("/children", response_model=list[ChildResponse])
async def list_children(db: DbSession, current_user: CurrentUser) -> list[ChildResponse]:
    result = await db.execute(
        select(ChildProfile)
        .where(ChildProfile.user_id == current_user.id)
        .order_by(ChildProfile.created_at.desc())
    )
    children = result.scalars().all()

    responses: list[ChildResponse] = []
    for child in children:
        count_result = await db.execute(
            select(func.count()).select_from(Order).where(Order.child_profile_id == child.id)
        )
        responses.append(ChildResponse(
            id=str(child.id),
            name=child.name,
            age=child.age,
            gender=child.gender,
            photo_url=child.photo_url,
            order_count=count_result.scalar() or 0,
        ))
    return responses


@router.post("/children", response_model=ChildResponse, status_code=status.HTTP_201_CREATED)
async def create_child(
    body: ChildCreate, db: DbSession, current_user: CurrentUser,
) -> ChildResponse:
    count_result = await db.execute(
        select(func.count()).select_from(ChildProfile).where(ChildProfile.user_id == current_user.id)
    )
    if (count_result.scalar() or 0) >= _MAX_CHILDREN:
        raise ValidationError(f"En fazla {_MAX_CHILDREN} çocuk profili ekleyebilirsiniz")

    child = ChildProfile(
        user_id=current_user.id,
        name=body.name,
        age=body.age,
        gender=body.gender,
    )
    db.add(child)
    await db.commit()
    await db.refresh(child)
    return ChildResponse(
        id=str(child.id), name=child.name, age=child.age,
        gender=child.gender, photo_url=child.photo_url, order_count=0,
    )


@router.delete("/children/{child_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_child(
    child_id: uuid.UUID, db: DbSession, current_user: CurrentUser,
) -> None:
    result = await db.execute(
        select(ChildProfile).where(ChildProfile.id == child_id, ChildProfile.user_id == current_user.id)
    )
    child = result.scalar_one_or_none()
    if not child:
        raise NotFoundError("Çocuk profili")
    await db.delete(child)
    await db.commit()

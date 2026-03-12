"""Authentication business logic: registration, login, guest conversion."""

from datetime import UTC, datetime

import sqlalchemy as sa
import structlog
from fastapi import HTTPException, Request
from sqlalchemy import func as sa_func
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import record_audit
from app.core.exceptions import ConflictError, UnauthorizedError, ValidationError
from app.core.security import (
    create_access_token,
    create_refresh_token,
    get_password_hash,
    verify_password,
)
from app.models.user import User
from app.schemas.auth import (
    ConvertGuestRequest,
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    UserInfo,
)

logger = structlog.get_logger()

_RESET_TOKEN_TTL = 900  # 15 minutes
_RESET_TOKEN_PREFIX = "pwd_reset:"
_ERR_BAD_CREDENTIALS = "Email veya şifre hatalı"


async def _get_async_redis():
    import redis.asyncio as aioredis

    from app.config import settings

    return aioredis.from_url(str(settings.redis_url), decode_responses=True)


async def link_guest_orders_by_email(db: AsyncSession, user: User) -> None:
    """Link orphan orders and trials to a newly registered/logged-in user by email.

    Called during registration (both new user and guest upgrade) and on login
    to ensure any orders/trials placed with the same email are visible on the
    user's account page.
    """
    from app.models.order import Order
    from app.models.story_preview import StoryPreview

    if not user.email:
        return

    await db.execute(
        sa.update(StoryPreview)
        .where(StoryPreview.parent_email == user.email)
        .where(
            sa.or_(
                StoryPreview.lead_user_id.is_(None),
                StoryPreview.lead_user_id != user.id,
            )
        )
        .values(lead_user_id=user.id)
    )

    await db.execute(
        sa.update(Order)
        .where(Order.billing_email == user.email)
        .where(
            sa.or_(
                Order.user_id.is_(None),
                Order.user_id != user.id,
            )
        )
        .values(user_id=user.id)
    )

    logger.info(
        "guest_orders_linked",
        user_id=str(user.id),
        email_domain=user.email.rsplit("@", 1)[-1],
    )


async def perform_register(
    body: RegisterRequest,
    http_request: Request,
    db: AsyncSession,
) -> TokenResponse:
    """Register a new user account.

    If the email belongs to a guest user (no password), the guest account is
    upgraded in-place so that existing orders and trials stay linked.
    """
    email_lower = body.email.lower().strip()
    result = await db.execute(select(User).where(sa_func.lower(User.email) == email_lower))
    existing_user = result.scalar_one_or_none()

    if existing_user:
        # Guest user → upgrade to full account (keep same user_id, orders stay linked)
        if existing_user.is_guest and not existing_user.hashed_password:
            existing_user.hashed_password = get_password_hash(body.password)
            existing_user.full_name = body.full_name
            existing_user.phone = body.phone or existing_user.phone
            existing_user.is_guest = False

            await link_guest_orders_by_email(db, existing_user)

            await db.flush()
            await record_audit(
                db,
                action="GUEST_UPGRADED_TO_USER",
                user_id=existing_user.id,
                request=http_request,
                details={"email_domain": body.email.rsplit("@", 1)[-1]},
            )
            await db.commit()
            await db.refresh(existing_user)

            tv = existing_user.token_version or 0
            return TokenResponse(
                access_token=create_access_token(existing_user.id, token_version=tv),
                refresh_token=create_refresh_token(existing_user.id, token_version=tv),
                user=UserInfo(
                    id=str(existing_user.id),
                    email=existing_user.email,
                    full_name=existing_user.full_name,
                    role="user",
                    is_guest=False,
                ),
            )
        raise ConflictError("Kayıt işlemi tamamlanamadı. Lütfen farklı bilgilerle tekrar deneyin.")

    user = User(
        email=body.email,
        hashed_password=get_password_hash(body.password),
        full_name=body.full_name,
        phone=body.phone,
    )
    db.add(user)
    await db.flush()

    await link_guest_orders_by_email(db, user)

    await record_audit(
        db,
        action="USER_REGISTERED",
        user_id=user.id,
        request=http_request,
    )
    await db.commit()
    await db.refresh(user)

    tv = user.token_version or 0
    return TokenResponse(
        access_token=create_access_token(user.id, token_version=tv),
        refresh_token=create_refresh_token(user.id, token_version=tv),
        user=UserInfo(
            id=str(user.id),
            email=user.email,
            full_name=user.full_name,
            role="user",
            is_guest=False,
        ),
    )


async def perform_login(
    body: LoginRequest,
    http_request: Request,
    db: AsyncSession,
) -> TokenResponse:
    """Login with email and password.

    If the account has a pending deletion (grace period), login restores it.
    """
    try:
        email_lower = body.email.lower().strip()
        result = await db.execute(
            select(User).where(sa_func.lower(User.email) == email_lower)
        )
        user = result.scalar_one_or_none()

        if not user or not user.hashed_password:
            await record_audit(
                db,
                action="LOGIN_FAILED",
                request=http_request,
                details={"reason": "invalid_credentials"},
            )
            await db.commit()
            raise UnauthorizedError(_ERR_BAD_CREDENTIALS)

        pw_hash = user.hashed_password
        if not pw_hash or not isinstance(pw_hash, str):
            await record_audit(
                db,
                action="LOGIN_FAILED",
                user_id=user.id,
                request=http_request,
                details={"reason": "invalid_hash"},
            )
            await db.commit()
            raise UnauthorizedError(_ERR_BAD_CREDENTIALS)

        try:
            if not verify_password(body.password, pw_hash):
                await record_audit(
                    db,
                    action="LOGIN_FAILED",
                    user_id=user.id,
                    request=http_request,
                    details={"reason": "wrong_password"},
                )
                await db.commit()
                raise UnauthorizedError(_ERR_BAD_CREDENTIALS)
        except UnauthorizedError:
            raise
        except Exception:
            raise UnauthorizedError(_ERR_BAD_CREDENTIALS)

        # Grace period restore: if user deleted account but logs in within 7 days
        if not user.is_active and user.deletion_scheduled_at is not None:
            if user.deletion_scheduled_at > datetime.now(UTC):
                user.is_active = True
                user.deletion_scheduled_at = None
                await record_audit(
                    db, action="ACCOUNT_RESTORED", user_id=user.id, request=http_request,
                )
            else:
                await record_audit(
                    db,
                    action="LOGIN_FAILED",
                    user_id=user.id,
                    request=http_request,
                    details={"reason": "account_purged"},
                )
                await db.commit()
                raise UnauthorizedError("Hesabınız kalıcı olarak silinmiş")

        if not user.is_active:
            await record_audit(
                db,
                action="LOGIN_FAILED",
                user_id=user.id,
                request=http_request,
                details={"reason": "account_disabled"},
            )
            await db.commit()
            raise UnauthorizedError("Hesabınız devre dışı")

        try:
            user_role = (
                user.role.value
                if hasattr(user.role, "value")
                else (user.role if isinstance(user.role, str) else "user")
            )
        except Exception:
            user_role = "user"

        tv = user.token_version or 0
        access_token = create_access_token(
            user.id, additional_claims={"role": user_role}, token_version=tv
        )
        refresh_token = create_refresh_token(user.id, token_version=tv)

        user.last_login_at = datetime.now(UTC)

        await link_guest_orders_by_email(db, user)

        await record_audit(
            db, action="LOGIN_SUCCESS", user_id=user.id, request=http_request,
        )
        await db.commit()

        return TokenResponse(
            access_token=str(access_token) if access_token else "",
            refresh_token=str(refresh_token) if refresh_token else "",
            user=UserInfo(
                id=str(user.id),
                email=user.email,
                full_name=user.full_name,
                role=user_role,
                is_guest=bool(getattr(user, "is_guest", False)),
            ),
        )
    except UnauthorizedError:
        raise
    except Exception as e:
        logger.exception("Login failed", error_type=type(e).__name__)
        raise HTTPException(status_code=500, detail="Giriş işlemi sırasında hata oluştu")


async def perform_convert_guest(
    body: ConvertGuestRequest,
    http_request: Request,
    db: AsyncSession,
    current_user: User,
) -> TokenResponse:
    """Convert a guest account to a full user account.

    Idempotent: if already converted, returns fresh tokens.
    Orders remain on the same user_id (no transfer needed).
    Anti-enumeration: generic error message for email conflicts.
    """
    from sqlalchemy import func as sa_func
    from sqlalchemy.exc import IntegrityError

    from app.models.order import Order

    # Idempotent: already converted → return fresh tokens
    if not current_user.is_guest:
        if current_user.email == body.email:
            role = (
                current_user.role
                if isinstance(current_user.role, str)
                else current_user.role.value
            )
            tv = current_user.token_version or 0
            return TokenResponse(
                access_token=create_access_token(
                    current_user.id, additional_claims={"role": role}, token_version=tv
                ),
                refresh_token=create_refresh_token(current_user.id, token_version=tv),
                user=UserInfo(
                    id=str(current_user.id),
                    email=current_user.email,
                    full_name=current_user.full_name,
                    role=role,
                ),
            )
        raise ValidationError("Bu hesap zaten kayıtlı bir kullanıcı")

    current_user.email = body.email
    current_user.hashed_password = get_password_hash(body.password)
    current_user.full_name = body.full_name
    current_user.is_guest = False

    order_count_result = await db.execute(
        select(sa_func.count()).select_from(
            select(Order.id).where(Order.user_id == current_user.id).subquery()
        )
    )
    orders_count = order_count_result.scalar() or 0

    try:
        await db.flush()
    except IntegrityError:
        await db.rollback()
        raise ConflictError("Hesap oluşturulamadı. Lütfen farklı bilgilerle tekrar deneyin.")

    await record_audit(
        db,
        action="GUEST_CONVERTED",
        user_id=current_user.id,
        request=http_request,
        details={
            "email_domain": body.email.rsplit("@", 1)[-1],
            "orders_preserved": orders_count,
        },
    )
    await db.commit()
    await db.refresh(current_user)

    role = (
        current_user.role
        if isinstance(current_user.role, str)
        else current_user.role.value
    )
    tv = current_user.token_version or 0
    return TokenResponse(
        access_token=create_access_token(
            current_user.id, additional_claims={"role": role}, token_version=tv
        ),
        refresh_token=create_refresh_token(current_user.id, token_version=tv),
        user=UserInfo(
            id=str(current_user.id),
            email=current_user.email,
            full_name=current_user.full_name,
            role=role,
        ),
    )

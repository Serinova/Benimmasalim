"""Authentication endpoints."""

from datetime import UTC, datetime
from uuid import UUID

import structlog
from fastapi import APIRouter, HTTPException, Request, status
from sqlalchemy import select

from app.api.v1.deps import CurrentUser, DbSession
from app.config import settings
from app.core.audit import record_audit
from app.core.exceptions import UnauthorizedError, ValidationError
from app.core.security import (
    blacklist_token,
    create_access_token,
    create_guest_token,
    create_refresh_token,
    get_password_hash,
    verify_password,
)
from app.models.user import User
from app.schemas.auth import (
    ChangePasswordRequest,
    ConvertGuestRequest,
    ForgotPasswordRequest,
    LoginRequest,
    LogoutRequest,
    RefreshRequest,
    RegisterRequest,
    ResetPasswordRequest,
    TokenResponse,
    UpdateProfileRequest,
    UserInfo,
    UserResponse,
)
from app.services.auth_service import (
    perform_convert_guest,
    perform_login,
    perform_register,
)

router = APIRouter()
logger = structlog.get_logger()

_RESET_TOKEN_TTL = 900  # 15 minutes
_RESET_TOKEN_PREFIX = "pwd_reset:"

_ERR_INVALID_REFRESH = "Geçersiz refresh token"


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(body: RegisterRequest, http_request: Request, db: DbSession) -> TokenResponse:
    """Register a new user account.

    If the email belongs to a guest user (no password), the guest account is
    upgraded in-place so that existing orders and trials stay linked.
    """
    return await perform_register(body, http_request, db)


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, http_request: Request, db: DbSession) -> TokenResponse:
    """Login with email and password.

    If the account has a pending deletion (grace period), login restores it.
    """
    return await perform_login(body, http_request, db)


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(request: RefreshRequest, db: DbSession) -> TokenResponse:
    """Refresh access token using refresh token. Old refresh token is blacklisted."""
    from app.core.security import decode_token, is_token_blacklisted

    if await is_token_blacklisted(request.refresh_token):
        raise UnauthorizedError("Refresh token iptal edilmiş — lütfen tekrar giriş yapın")

    payload = decode_token(request.refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise UnauthorizedError(_ERR_INVALID_REFRESH)

    user_id = payload.get("sub")
    if not user_id:
        raise UnauthorizedError(_ERR_INVALID_REFRESH)
    try:
        user_uuid = UUID(user_id) if isinstance(user_id, str) else user_id
    except (ValueError, TypeError):
        raise UnauthorizedError(_ERR_INVALID_REFRESH)

    result = await db.execute(select(User).where(User.id == user_uuid))
    user = result.scalar_one_or_none()

    if not user or not user.is_active:
        raise UnauthorizedError("Kullanıcı bulunamadı")

    if user.deletion_scheduled_at is not None:
        raise UnauthorizedError("Hesabınız silinmek üzere — yeni token verilemez")

    token_tv = payload.get("tv", 0)
    if token_tv != (user.token_version or 0):
        raise UnauthorizedError("Oturumunuz sonlandırılmış — lütfen tekrar giriş yapın")

    role = "user"
    if user.role is not None:
        role = user.role if isinstance(user.role, str) else user.role.value

    tv = user.token_version or 0

    await blacklist_token(request.refresh_token, expires_in_seconds=604800)

    return TokenResponse(
        access_token=create_access_token(user.id, additional_claims={"role": role}, token_version=tv),
        refresh_token=create_refresh_token(user.id, token_version=tv),
    )


@router.post("/guest", response_model=dict)
async def create_guest_session() -> dict:
    """Create a guest session for checkout without registration."""
    return {
        "guest_token": create_guest_token(),
        "token_type": "bearer",
        "expires_in": 86400,
    }


@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout(
    body: LogoutRequest, http_request: Request, current_user: CurrentUser, db: DbSession,
) -> dict:
    """Invalidate access and refresh tokens by adding them to the Redis blacklist."""
    await blacklist_token(body.access_token, expires_in_seconds=7200)
    if body.refresh_token:
        await blacklist_token(body.refresh_token, expires_in_seconds=604800)

    await record_audit(db, action="LOGOUT", user_id=current_user.id, request=http_request)
    await db.commit()
    return {"message": "Çıkış yapıldı"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(current_user: CurrentUser) -> UserResponse:
    """Get current user profile."""
    return UserResponse(
        id=str(current_user.id),
        email=current_user.email,
        full_name=current_user.full_name,
        phone=current_user.phone,
        role=current_user.role if isinstance(current_user.role, str) else current_user.role.value,
        is_guest=current_user.is_guest,
    )


@router.patch("/me", response_model=UserResponse)
async def update_profile(
    request: UpdateProfileRequest,
    db: DbSession,
    current_user: CurrentUser,
) -> UserResponse:
    """Update current user's profile (name, phone)."""
    if request.full_name is not None:
        current_user.full_name = request.full_name.strip()
    if request.phone is not None:
        current_user.phone = request.phone.strip() or None

    await db.commit()
    await db.refresh(current_user)

    return UserResponse(
        id=str(current_user.id),
        email=current_user.email,
        full_name=current_user.full_name,
        phone=current_user.phone,
        role=current_user.role if isinstance(current_user.role, str) else current_user.role.value,
        is_guest=current_user.is_guest,
    )


# ── Password Reset ──────────────────────────────────────────────────────────


async def _get_async_redis():
    import redis.asyncio as aioredis
    return aioredis.from_url(str(settings.redis_url), decode_responses=True)


@router.post("/forgot-password")
async def forgot_password(
    body: ForgotPasswordRequest, http_request: Request, db: DbSession,
) -> dict:
    """Send password reset link. Always returns 200 to prevent email enumeration."""
    from sqlalchemy import func as sa_func

    email_lower = body.email.lower().strip()
    result = await db.execute(select(User).where(sa_func.lower(User.email) == email_lower))
    user = result.scalar_one_or_none()

    if user and user.is_active:
        token = __import__("secrets").token_urlsafe(32)
        try:
            r = await _get_async_redis()
            await r.setex(f"{_RESET_TOKEN_PREFIX}{token}", _RESET_TOKEN_TTL, str(user.id))
        except Exception:
            logger.exception("Redis unavailable for password reset")
            raise HTTPException(status_code=503, detail="Servis geçici olarak kullanılamıyor")

        reset_url = f"{settings.frontend_url}/auth/reset-password?token={token}&email={body.email}"
        try:
            from app.services.email_service import email_service
            await email_service.send_password_reset_email_async(
                recipient_email=body.email,
                recipient_name=user.full_name or "",
                reset_url=reset_url,
            )
        except Exception:
            logger.exception("Failed to send password reset email")

        await record_audit(
            db, action="PASSWORD_RESET_REQUESTED", user_id=user.id, request=http_request,
        )
        await db.commit()

    return {"message": "Eğer bu email adresi kayıtlıysa, şifre sıfırlama linki gönderildi."}


@router.post("/reset-password")
async def reset_password(
    body: ResetPasswordRequest, http_request: Request, db: DbSession,
) -> dict:
    """Reset password using token from email."""
    from sqlalchemy import func as sa_func

    try:
        r = await _get_async_redis()
        user_id = await r.get(f"{_RESET_TOKEN_PREFIX}{body.token}")
    except Exception:
        raise HTTPException(status_code=503, detail="Servis geçici olarak kullanılamıyor")

    if not user_id:
        raise ValidationError("Sıfırlama linki geçersiz veya süresi dolmuş")

    email_lower = body.email.lower().strip()
    result = await db.execute(select(User).where(sa_func.lower(User.email) == email_lower))
    user = result.scalar_one_or_none()

    if not user or str(user.id) != user_id:
        raise ValidationError("Sıfırlama linki geçersiz veya süresi dolmuş")

    user.hashed_password = get_password_hash(body.new_password)
    user.token_version = (user.token_version or 0) + 1

    try:
        await r.delete(f"{_RESET_TOKEN_PREFIX}{body.token}")
    except Exception:
        pass

    await record_audit(db, action="PASSWORD_RESET", user_id=user.id, request=http_request)
    await db.commit()

    return {"message": "Şifreniz başarıyla değiştirildi. Giriş yapabilirsiniz."}


# ── Change Password ─────────────────────────────────────────────────────────


@router.post("/change-password")
async def change_password(
    body: ChangePasswordRequest,
    http_request: Request,
    db: DbSession,
    current_user: CurrentUser,
) -> dict:
    """Change password for authenticated user."""
    if not current_user.hashed_password:
        raise ValidationError("Bu hesap için şifre değiştirme desteklenmiyor")

    if not verify_password(body.current_password, current_user.hashed_password):
        raise UnauthorizedError("Mevcut şifre hatalı")

    if body.current_password == body.new_password:
        raise ValidationError("Yeni şifre mevcut şifreden farklı olmalıdır")

    current_user.hashed_password = get_password_hash(body.new_password)
    current_user.token_version = (current_user.token_version or 0) + 1

    await record_audit(
        db, action="PASSWORD_CHANGED", user_id=current_user.id, request=http_request,
    )
    await db.commit()

    tv = current_user.token_version
    return {
        "message": "Şifreniz başarıyla değiştirildi.",
        "access_token": create_access_token(current_user.id, token_version=tv),
        "refresh_token": create_refresh_token(current_user.id, token_version=tv),
    }


# ── Guest → User Conversion ─────────────────────────────────────────────────


@router.post("/convert-guest", response_model=TokenResponse)
async def convert_guest_to_user(
    body: ConvertGuestRequest,
    http_request: Request,
    db: DbSession,
    current_user: CurrentUser,
) -> TokenResponse:
    """Convert a guest account to a full user account."""
    return await perform_convert_guest(body, http_request, db, current_user)

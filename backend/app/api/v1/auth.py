"""Authentication endpoints."""

import re

import structlog
from fastapi import APIRouter, Request, status
from pydantic import BaseModel, EmailStr, Field, field_validator
from sqlalchemy import select

from app.api.v1.deps import CurrentUser, DbSession
from app.core.audit import record_audit
from app.core.exceptions import ConflictError, UnauthorizedError
from app.core.security import (
    blacklist_token,
    create_access_token,
    create_guest_token,
    create_refresh_token,
    get_password_hash,
    verify_password,
)
from app.models.user import User

router = APIRouter()

# Shared error messages
_ERR_BAD_CREDENTIALS = "Email veya şifre hatalı"
_ERR_INVALID_REFRESH = "Geçersiz refresh token"


# Request/Response schemas
_COMMON_PASSWORDS = frozenset({
    "12345678", "password", "password1", "qwerty12", "abc12345",
    "11111111", "123456789", "1234567890", "iloveyou", "sunshine",
    "princess", "football", "charlie1", "shadow12", "master12",
})


class RegisterRequest(BaseModel):
    """User registration request."""

    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    full_name: str = Field(..., min_length=2, max_length=100)
    phone: str | None = None

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """Enforce password complexity: upper + lower + digit + special char."""
        if not re.search(r"[A-Z]", v):
            raise ValueError("Şifre en az bir büyük harf içermelidir")
        if not re.search(r"[a-z]", v):
            raise ValueError("Şifre en az bir küçük harf içermelidir")
        if not re.search(r"\d", v):
            raise ValueError("Şifre en az bir rakam içermelidir")
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>_\-+=\[\]~`]", v):
            raise ValueError("Şifre en az bir özel karakter içermelidir (!@#$%^&*...)")
        if v.lower() in _COMMON_PASSWORDS:
            raise ValueError("Bu şifre çok yaygın, lütfen daha güçlü bir şifre seçin")
        return v


class LoginRequest(BaseModel):
    """User login request."""

    email: EmailStr
    password: str


class UserInfo(BaseModel):
    """User info in token response."""

    id: str
    email: str | None
    full_name: str | None
    role: str


class TokenResponse(BaseModel):
    """Token response."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserInfo | None = None


class RefreshRequest(BaseModel):
    """Token refresh request."""

    refresh_token: str


class UserResponse(BaseModel):
    """User profile response."""

    id: str
    email: str | None
    full_name: str | None
    phone: str | None
    role: str
    is_guest: bool

    class Config:
        from_attributes = True


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(body: RegisterRequest, http_request: Request, db: DbSession) -> TokenResponse:
    """Register a new user account."""
    result = await db.execute(select(User).where(User.email == body.email))
    if result.scalar_one_or_none():
        raise ConflictError("Kayıt işlemi tamamlanamadı. Lütfen farklı bilgilerle tekrar deneyin.")

    user = User(
        email=body.email,
        hashed_password=get_password_hash(body.password),
        full_name=body.full_name,
        phone=body.phone,
    )
    db.add(user)
    await db.flush()

    await record_audit(
        db,
        action="USER_REGISTERED",
        user_id=user.id,
        request=http_request,
    )
    await db.commit()
    await db.refresh(user)

    return TokenResponse(
        access_token=create_access_token(user.id),
        refresh_token=create_refresh_token(user.id),
    )


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, http_request: Request, db: DbSession) -> TokenResponse:
    """Login with email and password."""
    logger = structlog.get_logger()
    try:
        result = await db.execute(select(User).where(User.email == body.email))
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
                db, action="LOGIN_FAILED", user_id=user.id,
                request=http_request, details={"reason": "invalid_hash"},
            )
            await db.commit()
            raise UnauthorizedError(_ERR_BAD_CREDENTIALS)
        try:
            if not verify_password(body.password, pw_hash):
                await record_audit(
                    db, action="LOGIN_FAILED", user_id=user.id,
                    request=http_request, details={"reason": "wrong_password"},
                )
                await db.commit()
                raise UnauthorizedError(_ERR_BAD_CREDENTIALS)
        except UnauthorizedError:
            raise
        except Exception:
            raise UnauthorizedError(_ERR_BAD_CREDENTIALS)

        if not user.is_active:
            await record_audit(
                db, action="LOGIN_FAILED", user_id=user.id,
                request=http_request, details={"reason": "account_disabled"},
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

        access_token = create_access_token(user.id, additional_claims={"role": user_role})
        refresh_token = create_refresh_token(user.id)

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
            ),
        )
    except UnauthorizedError:
        raise
    except Exception as e:
        logger.exception("Login failed", error_type=type(e).__name__)
        from fastapi import HTTPException

        raise HTTPException(status_code=500, detail="Giriş işlemi sırasında hata oluştu")


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(request: RefreshRequest, db: DbSession) -> TokenResponse:
    """Refresh access token using refresh token. Old refresh token is blacklisted."""
    from uuid import UUID

    from app.core.security import decode_token, is_token_blacklisted

    # Check if refresh token has been revoked (replay detection)
    if is_token_blacklisted(request.refresh_token):
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

    role = "user"
    if user.role is not None:
        role = user.role if isinstance(user.role, str) else user.role.value

    # Blacklist the old refresh token (7 day TTL — prevents replay)
    blacklist_token(request.refresh_token, expires_in_seconds=604800)

    return TokenResponse(
        access_token=create_access_token(user.id, additional_claims={"role": role}),
        refresh_token=create_refresh_token(user.id),
    )


@router.post("/guest", response_model=dict)
async def create_guest_session() -> dict:
    """Create a guest session for checkout without registration."""
    return {
        "guest_token": create_guest_token(),
        "token_type": "bearer",
        "expires_in": 86400,  # 24 hours
    }


class LogoutRequest(BaseModel):
    """Logout request — invalidates tokens."""

    access_token: str
    refresh_token: str | None = None


@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout(
    body: LogoutRequest, http_request: Request, current_user: CurrentUser, db: DbSession,
) -> dict:
    """Invalidate access and refresh tokens by adding them to the Redis blacklist.

    Requires authentication — only the token owner can invalidate their tokens.
    """
    blacklist_token(body.access_token, expires_in_seconds=7200)
    if body.refresh_token:
        blacklist_token(body.refresh_token, expires_in_seconds=604800)

    await record_audit(
        db, action="LOGOUT", user_id=current_user.id, request=http_request,
    )
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

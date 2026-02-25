"""API dependencies for dependency injection."""

from typing import Annotated
from uuid import UUID

import structlog
from fastapi import Depends, Header
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.exceptions import ForbiddenError, NotFoundError, UnauthorizedError
from app.core.security import decode_token, is_token_blacklisted
from app.models.user import User, UserRole

logger = structlog.get_logger()


async def get_current_user(
    db: Annotated[AsyncSession, Depends(get_db)],
    authorization: Annotated[str | None, Header()] = None,
) -> User:
    """
    Get current authenticated user from JWT token.

    Raises:
        UnauthorizedError: If token is missing or invalid
        NotFoundError: If user not found
    """
    if not authorization:
        logger.warning("AUTH_DEBUG: No authorization header received")
        raise UnauthorizedError("Token gerekli")

    # Extract token from "Bearer <token>" format
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        logger.warning(
            "AUTH_DEBUG: Invalid token format",
            scheme=scheme,
            has_token=bool(token),
            auth_preview=authorization[:50] if authorization else "None",
        )
        raise UnauthorizedError("Geçersiz token formatı")

    # Check blacklist (revoked via /auth/logout)
    if is_token_blacklisted(token):
        raise UnauthorizedError("Token iptal edilmiş — lütfen tekrar giriş yapın")

    payload = decode_token(token)
    if not payload:
        logger.warning("AUTH_DEBUG: Token decode failed", token_suffix=token[-4:] if token else "N/A")
        raise UnauthorizedError("Geçersiz veya süresi dolmuş token")

    token_type = payload.get("type")
    if token_type != "access":
        raise UnauthorizedError("Geçersiz token tipi")

    user_id = payload.get("sub")
    if not user_id:
        raise UnauthorizedError("Token'da kullanıcı bilgisi yok")

    result = await db.execute(select(User).where(User.id == UUID(user_id)))
    user = result.scalar_one_or_none()

    if not user:
        raise NotFoundError("Kullanıcı")

    if not user.is_active:
        raise ForbiddenError("Hesabınız devre dışı bırakılmış")

    return user


async def get_current_user_optional(
    db: Annotated[AsyncSession, Depends(get_db)],
    authorization: Annotated[str | None, Header()] = None,
) -> User | None:
    """
    Get current user if authenticated, None otherwise.
    Used for endpoints that work with or without authentication.
    """
    if not authorization:
        return None

    try:
        return await get_current_user(db, authorization)
    except (UnauthorizedError, NotFoundError):
        return None


async def get_admin_user(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """
    Require admin role for endpoint access.

    Raises:
        ForbiddenError: If user is not an admin
    """
    if current_user.role not in (UserRole.ADMIN, UserRole.EDITOR):
        raise ForbiddenError("Admin yetkisi gerekli")
    return current_user


async def get_super_admin_user(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """
    Require super admin role for endpoint access.

    Raises:
        ForbiddenError: If user is not a super admin
    """
    if current_user.role != UserRole.ADMIN:
        raise ForbiddenError("Süper admin yetkisi gerekli")
    return current_user


# Type aliases for cleaner route signatures
CurrentUser = Annotated[User, Depends(get_current_user)]
CurrentUserOptional = Annotated[User | None, Depends(get_current_user_optional)]
AdminUser = Annotated[User, Depends(get_admin_user)]
SuperAdminUser = Annotated[User, Depends(get_super_admin_user)]
DbSession = Annotated[AsyncSession, Depends(get_db)]

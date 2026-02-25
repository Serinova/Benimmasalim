"""Lead capture endpoint for early user contact information collection.

This is critical for the "Concierge Support" model - if the user drops off
or the AI fails, we must have their phone number to call them.
"""

import re
import uuid
from uuid import UUID

import structlog
from fastapi import APIRouter, Header, HTTPException, status
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.api.v1.deps import CurrentUserOptional, DbSession
from app.config import settings
from app.models.user import User, UserRole

logger = structlog.get_logger()
router = APIRouter()


# ============ SCHEMAS ============


class LeadCaptureRequest(BaseModel):
    """Request to capture lead contact information."""

    first_name: str = Field(..., min_length=1, max_length=100, description="First name")
    last_name: str = Field(..., min_length=1, max_length=100, description="Last name")
    phone: str = Field(..., min_length=10, max_length=20, description="Phone number")
    email: str | None = Field(None, max_length=255, description="Email (optional if not logged in)")

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        """Validate and normalize phone number."""
        # Remove all non-digit characters except +
        cleaned = re.sub(r"[^\d+]", "", v)

        # Turkish phone format: +90 5XX XXX XX XX or 05XX XXX XX XX
        if cleaned.startswith("+90"):
            cleaned = cleaned  # Already in international format
        elif cleaned.startswith("90") and len(cleaned) == 12:
            cleaned = "+" + cleaned
        elif cleaned.startswith("0") and len(cleaned) == 11:
            cleaned = "+9" + cleaned  # Convert 05XX to +905XX
        elif len(cleaned) == 10 and cleaned.startswith("5"):
            cleaned = "+90" + cleaned  # Convert 5XX to +905XX

        # Validate length
        if len(cleaned) < 10:
            raise ValueError("Telefon numarası en az 10 karakter olmalı")

        return cleaned

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str | None) -> str | None:
        """Validate email format."""
        if v is None or v == "":
            return None

        # Basic email validation
        email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        if not re.match(email_pattern, v):
            raise ValueError("Geçersiz email formatı")

        return v.lower().strip()


class LeadCaptureResponse(BaseModel):
    """Response after capturing lead."""

    success: bool
    user_id: str
    is_new_user: bool
    message: str


# ============ ENDPOINTS ============


@router.post("/capture", response_model=LeadCaptureResponse)
async def capture_lead(
    request: LeadCaptureRequest,
    db: DbSession,
) -> LeadCaptureResponse:
    """
    Capture user contact information at the beginning of the flow.

    This endpoint is called BEFORE the user starts creating their story.
    It ensures we have their contact info for Concierge Support.

    Behavior:
    - If user exists (by email or phone): Update their info
    - If new user: Create a guest user record

    Returns a user_id that should be used for subsequent operations.
    """
    full_name = f"{request.first_name} {request.last_name}".strip()
    is_new_user = False
    user = None

    # Try to find existing user by email
    if request.email:
        result = await db.execute(select(User).where(User.email == request.email))
        user = result.scalar_one_or_none()

    # If not found by email, try phone
    if not user and request.phone:
        result = await db.execute(select(User).where(User.phone == request.phone))
        user = result.scalar_one_or_none()

    if user:
        # Update existing user
        user.full_name = full_name
        user.phone = request.phone
        if request.email and not user.email:
            user.email = request.email

        logger.info(
            "Lead updated for existing user",
            user_id=str(user.id),
            phone_suffix=request.phone[-4:] if request.phone else "***",
        )
    else:
        # Create new guest user
        is_new_user = True
        user = User(
            id=uuid.uuid4(),
            full_name=full_name,
            phone=request.phone,
            email=request.email,
            is_guest=True,
            role=UserRole.USER,
            is_active=True,
        )
        db.add(user)

        logger.info(
            "New lead captured",
            user_id=str(user.id),
            phone_suffix=request.phone[-4:] if request.phone else "***",
        )

    try:
        await db.commit()
    except IntegrityError as e:
        await db.rollback()
        logger.warning("Lead capture duplicate", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bu e-posta veya telefon numarası zaten kayıtlı. Giriş yapın veya farklı bilgi girin.",
        ) from e
    except Exception as e:
        await db.rollback()
        logger.exception("Lead capture failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
            if settings.app_env == "development"
            else "İletişim bilgisi kaydedilemedi.",
        ) from e

    return LeadCaptureResponse(
        success=True,
        user_id=str(user.id),
        is_new_user=is_new_user,
        message="İletişim bilgileriniz kaydedildi" if is_new_user else "Bilgileriniz güncellendi",
    )


@router.get("/{user_id}")
async def get_lead_info(
    user_id: UUID,
    db: DbSession,
    current_user: CurrentUserOptional,
    x_user_id: str | None = Header(None, alias="X-User-Id"),
) -> dict:
    """
    Get lead info by user_id.

    Used to restore session if user refreshes the page.
    Access control: JWT auth (ownership match) OR X-User-Id header
    matching user_id for guest users who are the same person.
    """
    _ERR_FORBIDDEN = "Bu bilgilere erişim yetkiniz yok"

    # Authenticated users: verify they own this user_id
    if current_user:
        if current_user.id != user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=_ERR_FORBIDDEN)
    else:
        # Guest fallback: X-User-Id header must match (backward compat)
        if not x_user_id or str(user_id) != x_user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=_ERR_FORBIDDEN)

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Kullanıcı bulunamadı")

    # Guest users can only access their own guest record via X-User-Id
    if not current_user and not user.is_guest:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=_ERR_FORBIDDEN)

    # Parse full name into first/last
    name_parts = (user.full_name or "").split(" ", 1)
    first_name = name_parts[0] if name_parts else ""
    last_name = name_parts[1] if len(name_parts) > 1 else ""

    return {
        "user_id": str(user.id),
        "first_name": first_name,
        "last_name": last_name,
        "phone": user.phone,
        "email": user.email,
        "is_guest": user.is_guest,
    }

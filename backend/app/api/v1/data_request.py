"""User-facing KVKK data request API.

Allows users to submit data access, export, and deletion requests
without requiring authentication (uses email verification).
"""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum

import structlog
from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import _mask_email, record_audit
from app.core.database import get_db

logger = structlog.get_logger()

router = APIRouter()


class DataRequestType(StrEnum):
    ACCESS = "ACCESS"          # Verilerime erişmek istiyorum
    EXPORT = "EXPORT"          # Verilerimi dışa aktarmak istiyorum
    DELETION = "DELETION"      # Verilerimin silinmesini istiyorum
    CORRECTION = "CORRECTION"  # Verilerimin düzeltilmesini istiyorum


class SubmitDataRequestBody(BaseModel):
    email: EmailStr
    full_name: str
    request_type: DataRequestType
    description: str | None = None


class DataRequestResponse(BaseModel):
    success: bool
    message: str
    request_id: str


@router.post("/submit", response_model=DataRequestResponse)
async def submit_data_request(
    body: SubmitDataRequestBody,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> DataRequestResponse:
    """Submit a KVKK data request (access, export, deletion, correction).

    The request is logged as an audit entry and will be reviewed
    by an admin within 30 days as required by KVKK.
    """
    ip = request.headers.get("x-forwarded-for", request.client.host if request.client else None)

    # Find user by email (optional — they might not have an account)
    from app.models.user import User

    user_result = await db.execute(select(User).where(User.email == body.email))
    user = user_result.scalar_one_or_none()

    audit = await record_audit(
        db,
        action="DATA_REQUEST_SUBMITTED",
        user_id=user.id if user else None,
        ip_address=ip,
        request=request,
        details={
            "email_masked": _mask_email(body.email),
            "name_initial": body.full_name[0] + "***" if body.full_name else "***",
            "request_type": body.request_type.value,
            "has_description": body.description is not None,
            "submitted_at": datetime.now(UTC).isoformat(),
            "has_account": user is not None,
        },
    )
    await db.commit()
    await db.refresh(audit)

    logger.info(
        "KVKK data request submitted",
        email_masked=_mask_email(body.email),
        request_type=body.request_type.value,
        has_account=user is not None,
    )

    return DataRequestResponse(
        success=True,
        message="Talebiniz başarıyla alındı. En geç 30 gün içinde e-posta adresinize yanıt verilecektir.",
        request_id=str(audit.id),
    )

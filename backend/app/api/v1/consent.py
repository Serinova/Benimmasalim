"""Consent management API — KVKK compliance.

Public endpoint: POST /record (anonymous consent recording).
Admin-only endpoint: GET /status/{email} (prevents email enumeration).
"""

from __future__ import annotations

import structlog
from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_admin_user
from app.core.database import get_db
from app.models.consent import ConsentRecord
from app.models.user import User

logger = structlog.get_logger()

router = APIRouter()


# ──────────────────────────────────────────────────────────────────
# Request / Response schemas
# ──────────────────────────────────────────────────────────────────

class RecordConsentRequest(BaseModel):
    email: EmailStr
    consent_type: str  # PHOTO_PROCESSING | KVKK_DISCLOSURE | MARKETING
    action: str = "given"  # "given" | "withdrawn"
    consent_version: str = "1.0"
    source: str | None = None  # e.g. "PhotoUploaderStep", "UserContactForm"


class ConsentStatusResponse(BaseModel):
    consent_type: str
    is_active: bool
    last_action: str
    last_action_at: str
    version: str


class ConsentRecordResponse(BaseModel):
    id: str
    consent_type: str
    action: str
    consent_version: str
    source: str | None
    created_at: str



@router.post("/record", response_model=ConsentRecordResponse)
async def record_consent(
    body: RecordConsentRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> ConsentRecordResponse:
    """Record a consent action (given or withdrawn).

    Called by frontend when user checks/unchecks a KVKK consent checkbox.
    """
    ip = request.headers.get("x-forwarded-for", request.client.host if request.client else None)

    record = ConsentRecord(
        email=body.email,
        consent_type=body.consent_type,
        action=body.action,
        consent_version=body.consent_version,
        source=body.source,
        ip_address=ip,
    )
    db.add(record)
    await db.commit()
    await db.refresh(record)

    logger.info(
        "Consent recorded",
        email=body.email,
        consent_type=body.consent_type,
        action=body.action,
    )

    return ConsentRecordResponse(
        id=str(record.id),
        consent_type=record.consent_type,
        action=record.action,
        consent_version=record.consent_version,
        source=record.source,
        created_at=record.created_at.isoformat(),
    )


@router.get("/status/{email}", response_model=list[ConsentStatusResponse])
async def get_consent_status(
    email: str,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(get_admin_user),
) -> list[ConsentStatusResponse]:
    """Get current consent status for an email address.

    Restricted to admin users — prevents email enumeration and KVKK data leakage.
    """
    from sqlalchemy import func

    # Subquery: latest record per consent_type for this email
    subq = (
        select(
            ConsentRecord.consent_type,
            func.max(ConsentRecord.created_at).label("max_created"),
        )
        .where(ConsentRecord.email == email)
        .group_by(ConsentRecord.consent_type)
        .subquery()
    )

    result = await db.execute(
        select(ConsentRecord).join(
            subq,
            (ConsentRecord.consent_type == subq.c.consent_type)
            & (ConsentRecord.created_at == subq.c.max_created)
            & (ConsentRecord.email == email),
        )
    )
    records = result.scalars().all()

    return [
        ConsentStatusResponse(
            consent_type=r.consent_type,
            is_active=r.action == "given",
            last_action=r.action,
            last_action_at=r.created_at.isoformat(),
            version=r.consent_version,
        )
        for r in records
    ]

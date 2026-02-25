"""Centralized audit logging utility.

Every security-relevant action should go through ``record_audit`` so that
IP, user-agent, and actor information are captured consistently.
"""

from __future__ import annotations

import uuid
from typing import Any

import structlog
from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog

logger = structlog.get_logger()

# PII fields that must never appear in audit details JSONB.
# Use masked versions instead (e.g. phone_suffix, email_domain).
_PII_KEYS = frozenset({
    "password", "phone", "address", "child_photo_url",
    "face_embedding", "voice_sample_url", "credit_card", "cvv",
})


def _sanitize_details(details: dict[str, Any] | None) -> dict[str, Any] | None:
    """Strip known PII keys from details before persisting."""
    if not details:
        return details
    sanitized = {}
    for key, val in details.items():
        if key in _PII_KEYS:
            sanitized[key] = "***"
        else:
            sanitized[key] = val
    return sanitized


def _mask_email(email: str) -> str:
    """``user@example.com`` → ``u***@example.com``"""
    if not email or "@" not in email:
        return "***"
    local, domain = email.rsplit("@", 1)
    return f"{local[0]}***@{domain}" if local else f"***@{domain}"


def _extract_request_meta(request: Request | None) -> tuple[str | None, str | None]:
    """Return (ip_address, user_agent) from a FastAPI request."""
    if request is None:
        return None, None
    ip = (
        request.headers.get("x-forwarded-for", "").split(",")[0].strip()
        or (request.client.host if request.client else None)
    )
    ua = request.headers.get("user-agent")
    return ip or None, ua


async def record_audit(  # noqa: RUF029 — kept async for consistent caller API
    db: AsyncSession,
    *,
    action: str,
    user_id: uuid.UUID | None = None,
    order_id: uuid.UUID | None = None,
    admin_id: uuid.UUID | None = None,
    details: dict[str, Any] | None = None,
    request: Request | None = None,
    ip_address: str | None = None,
) -> AuditLog:
    """Create an audit log entry with consistent metadata.

    Parameters
    ----------
    db : AsyncSession
    action : str  – e.g. ``"LOGIN_SUCCESS"``, ``"PAYMENT_COMPLETED"``
    user_id : UUID | None – the *subject* user
    order_id : UUID | None
    admin_id : UUID | None – the *actor* if an admin performs the action
    details : dict | None – extra structured data (PII auto-stripped)
    request : Request | None – FastAPI request to extract IP + UA
    ip_address : str | None – explicit IP override (e.g. from middleware)
    """
    req_ip, req_ua = _extract_request_meta(request)
    entry = AuditLog(
        action=action,
        user_id=user_id,
        order_id=order_id,
        admin_id=admin_id,
        details=_sanitize_details(details),
        ip_address=ip_address or req_ip,
        user_agent=req_ua,
    )
    db.add(entry)
    return entry

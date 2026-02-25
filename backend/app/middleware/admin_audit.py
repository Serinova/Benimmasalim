"""Generic admin audit middleware.

Automatically logs **all** admin mutation requests (POST, PUT, PATCH, DELETE)
so that no admin action goes unrecorded — even if the endpoint forgot to
call ``record_audit`` explicitly.

The middleware decodes the JWT from the Authorization header to identify the
admin and opens its own DB session for the audit entry, keeping it fully
decoupled from endpoint code.
"""

from __future__ import annotations

from uuid import UUID

import structlog
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

logger = structlog.get_logger()

_MUTATION_METHODS = frozenset({"POST", "PUT", "PATCH", "DELETE"})
_ADMIN_PREFIX = "/api/v1/admin/"


def _extract_admin_id_from_jwt(request: Request) -> UUID | None:
    """Decode the JWT from the Authorization header without DB lookup."""
    auth = request.headers.get("authorization", "")
    if not auth.lower().startswith("bearer "):
        return None
    token = auth.split(" ", 1)[1]
    try:
        from app.core.security import decode_token

        payload = decode_token(token)
        if payload and payload.get("type") == "access":
            return UUID(payload["sub"])
    except Exception:
        pass
    return None


class AdminAuditMiddleware(BaseHTTPMiddleware):
    """Starlette middleware that captures admin mutations into audit_logs."""

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        path = request.url.path
        method = request.method

        if not path.startswith(_ADMIN_PREFIX) or method not in _MUTATION_METHODS:
            return await call_next(request)

        response = await call_next(request)

        if response.status_code >= 400:
            return response

        try:
            admin_id = _extract_admin_id_from_jwt(request)
            ip = (
                request.headers.get("x-forwarded-for", "").split(",")[0].strip()
                or (request.client.host if request.client else None)
            )
            ua = request.headers.get("user-agent")

            from app.core.database import async_session_factory
            from app.models.audit_log import AuditLog

            async with async_session_factory() as db:
                entry = AuditLog(
                    action=f"ADMIN_{method}",
                    admin_id=admin_id,
                    details={
                        "path": path,
                        "status_code": response.status_code,
                    },
                    ip_address=ip or None,
                    user_agent=ua,
                )
                db.add(entry)
                await db.commit()
        except Exception:
            logger.warning("admin_audit_log_failed", path=path, method=method, exc_info=True)

        return response

"""Request/response logging middleware - request_id, method, path, duration.

Pure ASGI implementation (no BaseHTTPMiddleware) to avoid response body streaming deadlocks.
"""

import time
import uuid

import structlog
from starlette.types import ASGIApp, Receive, Scope, Send

logger = structlog.get_logger()

SKIP_LOG_PATHS = frozenset({"/health", "/favicon.ico"})

_SENSITIVE_PARAMS = frozenset({
    "token", "password", "secret", "api_key", "refresh_token",
    "access_token", "authorization", "credit_card", "cvv",
    "key",  # Gemini REST API uses ?key= for API key
})


def _sanitize_query(params: str) -> str | None:
    """Mask values of sensitive query parameters before logging."""
    if not params:
        return None
    from urllib.parse import parse_qs, urlencode
    parsed = parse_qs(params, keep_blank_values=True)
    sanitized = {}
    for key, values in parsed.items():
        if key.lower() in _SENSITIVE_PARAMS:
            sanitized[key] = ["***"]
        else:
            sanitized[key] = values
    return urlencode(sanitized, doseq=True) or None


def _get_request_id(headers: list[tuple[bytes, bytes]]) -> str:
    """X-Request-ID header varsa kullan, yoksa yeni UUID üret."""
    for name, val in headers:
        if name == b"x-request-id":
            return val.decode("latin-1")
    return str(uuid.uuid4())


class RequestLoggingMiddleware:
    """Pure ASGI middleware: request_id + start/finish logging."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            return await self.app(scope, receive, send)

        path = scope.get("path", "")
        if path in SKIP_LOG_PATHS:
            return await self.app(scope, receive, send)

        headers = scope.get("headers", [])
        request_id = _get_request_id(headers)
        method = scope.get("method", "")

        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(request_id=request_id)

        client_host = None
        if scope.get("client"):
            client_host = scope["client"][0]

        query_string = scope.get("query_string", b"").decode("latin-1")
        logger.info(
            "request_start",
            method=method,
            path=path,
            query=_sanitize_query(query_string),
            client=client_host,
        )

        start = time.perf_counter()
        status_code = 0

        async def send_wrapper(message):
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message.get("status", 0)
                resp_headers = list(message.get("headers", []))
                resp_headers.append((b"x-request-id", request_id.encode("latin-1")))
                message = {**message, "headers": resp_headers}
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        except Exception as exc:
            duration_ms = round((time.perf_counter() - start) * 1000, 2)
            logger.exception(
                "request_failed",
                method=method,
                path=path,
                duration_ms=duration_ms,
                error=str(exc),
                error_type=type(exc).__name__,
            )
            raise

        duration_ms = round((time.perf_counter() - start) * 1000, 2)
        log_level = "warning" if status_code >= 400 else "info"
        getattr(logger, log_level)(
            "request_finished",
            method=method,
            path=path,
            status_code=status_code,
            duration_ms=duration_ms,
        )

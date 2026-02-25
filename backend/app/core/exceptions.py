"""Custom exception classes for the application."""

from typing import Any

from fastapi import HTTPException, status


class AppException(HTTPException):
    """Base exception class for application errors."""

    def __init__(
        self,
        status_code: int,
        detail: str,
        headers: dict[str, str] | None = None,
    ) -> None:
        super().__init__(status_code=status_code, detail=detail, headers=headers)


class NotFoundError(AppException):
    """Resource not found error."""

    def __init__(self, resource: str, identifier: Any = None) -> None:
        detail = f"{resource} bulunamadı"
        if identifier:
            detail = f"{resource} bulunamadı: {identifier}"
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


class ValidationError(AppException):
    """Validation error."""

    def __init__(self, detail: str) -> None:
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)


class UnauthorizedError(AppException):
    """Authentication required error."""

    def __init__(self, detail: str = "Kimlik doğrulama gerekli") -> None:
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"},
        )


class ForbiddenError(AppException):
    """Permission denied error."""

    def __init__(self, detail: str = "Bu işlem için yetkiniz yok") -> None:
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=detail)


class ConflictError(AppException):
    """Resource conflict error."""

    def __init__(self, detail: str) -> None:
        super().__init__(status_code=status.HTTP_409_CONFLICT, detail=detail)


class RateLimitError(AppException):
    """Rate limit exceeded error."""

    def __init__(self, detail: str = "Çok fazla istek. Lütfen bekleyin.") -> None:
        super().__init__(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=detail)


class InvalidStateTransition(AppException):
    """Invalid order state transition error."""

    def __init__(self, from_status: str, to_status: str) -> None:
        detail = f"Geçersiz durum geçişi: {from_status} → {to_status}"
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)


class AIServiceError(AppException):
    """AI service error (Gemini, Stable Diffusion, etc.)."""

    def __init__(
        self,
        service: str,
        detail: str = "AI servisi şu anda kullanılamıyor. Lütfen tekrar deneyin.",
        *,
        reason_code: str = "AI_UNKNOWN",
        trace_id: str = "",
    ) -> None:
        if not trace_id:
            import uuid

            trace_id = uuid.uuid4().hex[:12]
        self.reason_code = reason_code
        self.trace_id = trace_id
        super().__init__(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"{service}: {detail} [code={reason_code}, trace={trace_id}]",
        )


class PaymentError(AppException):
    """Payment processing error."""

    def __init__(self, detail: str) -> None:
        super().__init__(status_code=status.HTTP_402_PAYMENT_REQUIRED, detail=detail)


class RegenerateLimitExceeded(AppException):
    """Cover regeneration limit exceeded."""

    def __init__(self, max_count: int = 3) -> None:
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Kapak yenileme hakkınız doldu (maksimum {max_count})",
        )


class FaceDetectionError(AppException):
    """Face detection failed error."""

    def __init__(
        self, detail: str = "Yüz tespit edilemedi. Lütfen net bir fotoğraf yükleyin."
    ) -> None:
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)


class ContentPolicyError(AppException):
    """Content policy violation — story failed validation (e.g. no_family banned words)."""

    def __init__(self, detail: str) -> None:
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=detail,
        )

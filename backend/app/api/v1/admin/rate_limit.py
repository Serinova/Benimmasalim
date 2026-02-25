"""Admin: rate limit sıfırlama."""

from fastapi import APIRouter

from app.api.v1.deps import AdminUser
from app.middleware.rate_limiter import reset_all_rate_limits

router = APIRouter()


@router.post("/reset-all")
def admin_reset_all_rate_limits(_: AdminUser) -> dict[str, bool | str | int]:
    """Tüm IP'ler için rate limit sayaçlarını sıfırla. Sadece admin."""
    deleted = reset_all_rate_limits()
    return {"ok": True, "message": "Tüm rate limitler sıfırlandı.", "deleted_keys": deleted}

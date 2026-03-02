"""Admin settings endpoint — dynamic key-value configuration (invoice company info, etc.)."""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import AdminUser, DbSession
from app.models.app_setting import AppSetting

router = APIRouter()

# Keys used for invoice company settings
INVOICE_KEYS = [
    "invoice_company_name",
    "invoice_company_address",
    "invoice_company_tax_id",
    "invoice_company_tax_office",
    "invoice_company_phone",
    "invoice_company_email",
]


class InvoiceSettings(BaseModel):
    invoice_company_name: str = Field("", description="Fatura başlığında firma adı")
    invoice_company_address: str = Field("", description="Firma adresi")
    invoice_company_tax_id: str = Field("", description="Vergi Kimlik No (VKN)")
    invoice_company_tax_office: str = Field("", description="Vergi dairesi")
    invoice_company_phone: str = Field("", description="Firma telefonu")
    invoice_company_email: str = Field("", description="Firma e-postası")


async def _load_settings(keys: list[str], db: AsyncSession) -> dict[str, str]:
    result = await db.execute(
        select(AppSetting).where(AppSetting.key.in_(keys))
    )
    rows = result.scalars().all()
    return {r.key: (r.value or "") for r in rows}


async def _save_settings(data: dict[str, str], db: AsyncSession) -> None:
    for key, value in data.items():
        existing = await db.execute(select(AppSetting).where(AppSetting.key == key))
        row = existing.scalar_one_or_none()
        if row:
            row.value = value
        else:
            db.add(AppSetting(key=key, value=value))
    await db.commit()


@router.get("/invoice", response_model=InvoiceSettings)
async def get_invoice_settings(
    db: DbSession,
    _admin: AdminUser,
) -> InvoiceSettings:
    """Fatura şirket bilgilerini getir."""
    from app.config import settings as app_settings

    saved = await _load_settings(INVOICE_KEYS, db)

    def _val(key: str, fallback: str) -> str:
        return saved.get(key, "") or fallback

    return InvoiceSettings(
        invoice_company_name=_val("invoice_company_name", app_settings.invoice_company_name),
        invoice_company_address=_val("invoice_company_address", app_settings.invoice_company_address),
        invoice_company_tax_id=_val("invoice_company_tax_id", app_settings.invoice_company_tax_id),
        invoice_company_tax_office=_val("invoice_company_tax_office", app_settings.invoice_company_tax_office),
        invoice_company_phone=_val("invoice_company_phone", app_settings.invoice_company_phone),
        invoice_company_email=_val("invoice_company_email", app_settings.invoice_company_email),
    )


@router.put("/invoice", response_model=InvoiceSettings)
async def update_invoice_settings(
    payload: InvoiceSettings,
    db: DbSession,
    _admin: AdminUser,
) -> InvoiceSettings:
    """Fatura şirket bilgilerini güncelle."""
    await _save_settings(payload.model_dump(), db)
    return payload


# ── Generic app-setting endpoints ────────────────────────────────────────────


class AppSettingPayload(BaseModel):
    key: str = Field(..., min_length=1, max_length=100)
    value: str | None = None


@router.get("/app-setting/{key}")
async def get_app_setting(
    key: str,
    db: DbSession,
    _admin: AdminUser,
) -> dict:
    """Tek bir app_setting anahtarını getir."""
    result = await db.execute(select(AppSetting).where(AppSetting.key == key))
    row = result.scalar_one_or_none()
    if row is None:
        return {"key": key, "value": None}
    return {"key": row.key, "value": row.value}


@router.put("/app-setting")
async def upsert_app_setting(
    payload: AppSettingPayload,
    db: DbSession,
    _admin: AdminUser,
) -> dict:
    """Bir app_setting anahtarını oluştur veya güncelle."""
    result = await db.execute(select(AppSetting).where(AppSetting.key == payload.key))
    row = result.scalar_one_or_none()
    if row:
        row.value = payload.value
    else:
        db.add(AppSetting(key=payload.key, value=payload.value))
    await db.commit()
    return {"key": payload.key, "value": payload.value}

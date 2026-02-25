"""Admin endpoints for homepage section management."""

import uuid as _uuid
from uuid import UUID

from fastapi import APIRouter, File, HTTPException, UploadFile
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select, update

from app.api.v1.deps import AdminUser, DbSession
from app.config import settings
from app.core.exceptions import NotFoundError
from app.models.homepage import HomepageSection, SectionType
from app.services.storage_service import storage_service

router = APIRouter()


# ─── Schemas ──────────────────────────────────────────────────────


class HomepageSectionResponse(BaseModel):
    """Response schema for a homepage section."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    section_type: SectionType
    title: str | None
    subtitle: str | None
    is_visible: bool
    sort_order: int
    data: dict


class HomepageSectionUpdate(BaseModel):
    """Update schema — all fields optional."""

    title: str | None = None
    subtitle: str | None = None
    is_visible: bool | None = None
    sort_order: int | None = None
    data: dict | None = None


class BulkVisibilityUpdate(BaseModel):
    """Toggle visibility for multiple sections at once."""

    section_ids: list[UUID]
    is_visible: bool


# ─── Endpoints ────────────────────────────────────────────────────


@router.get("", response_model=list[HomepageSectionResponse])
async def list_sections(
    db: DbSession,
    _admin: AdminUser,
) -> list[HomepageSection]:
    """List all homepage sections (admin view, includes hidden)."""
    result = await db.execute(
        select(HomepageSection).order_by(HomepageSection.sort_order)
    )
    return list(result.scalars().all())


@router.get("/{section_id}", response_model=HomepageSectionResponse)
async def get_section(
    section_id: UUID,
    db: DbSession,
    _admin: AdminUser,
) -> HomepageSection:
    """Get a single homepage section by ID."""
    result = await db.execute(
        select(HomepageSection).where(HomepageSection.id == section_id)
    )
    section = result.scalar_one_or_none()
    if not section:
        raise NotFoundError("Bölüm")
    return section


@router.patch("/{section_id}", response_model=HomepageSectionResponse)
async def update_section(
    section_id: UUID,
    payload: HomepageSectionUpdate,
    db: DbSession,
    _admin: AdminUser,
) -> HomepageSection:
    """Update a homepage section's content."""
    result = await db.execute(
        select(HomepageSection).where(HomepageSection.id == section_id)
    )
    section = result.scalar_one_or_none()
    if not section:
        raise NotFoundError("Bölüm")

    update_data = payload.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(section, key, value)

    await db.commit()
    await db.refresh(section)
    return section


@router.patch("/{section_id}/visibility", response_model=HomepageSectionResponse)
async def toggle_visibility(
    section_id: UUID,
    db: DbSession,
    _admin: AdminUser,
) -> HomepageSection:
    """Toggle a section's visibility."""
    result = await db.execute(
        select(HomepageSection).where(HomepageSection.id == section_id)
    )
    section = result.scalar_one_or_none()
    if not section:
        raise NotFoundError("Bölüm")

    section.is_visible = not section.is_visible
    await db.commit()
    await db.refresh(section)
    return section


@router.post("/bulk-visibility", response_model=list[HomepageSectionResponse])
async def bulk_update_visibility(
    payload: BulkVisibilityUpdate,
    db: DbSession,
    _admin: AdminUser,
) -> list[HomepageSection]:
    """Set visibility for multiple sections at once."""
    await db.execute(
        update(HomepageSection)
        .where(HomepageSection.id.in_(payload.section_ids))
        .values(is_visible=payload.is_visible)
    )
    await db.commit()

    result = await db.execute(
        select(HomepageSection).order_by(HomepageSection.sort_order)
    )
    return list(result.scalars().all())


# ─── Image Upload ─────────────────────────────────────────────────

_ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
_MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10 MB


@router.post("/upload-image")
async def upload_homepage_image(
    _admin: AdminUser,
    image: UploadFile = File(..., description="Yüklenecek resim (max 10MB)"),
) -> dict[str, str]:
    """Upload an image for homepage sections (e.g. preview cards).

    Returns the public URL of the uploaded image.
    """
    if image.content_type not in _ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Desteklenmeyen dosya tipi: {image.content_type}. "
            f"İzin verilenler: {', '.join(_ALLOWED_IMAGE_TYPES)}",
        )

    data = await image.read()
    if len(data) > _MAX_IMAGE_SIZE:
        raise HTTPException(
            status_code=400,
            detail="Dosya boyutu 10 MB'ı aşamaz.",
        )

    # Magic byte validation — don't trust Content-Type header alone
    import io

    from PIL import Image, UnidentifiedImageError
    _ALLOWED_FORMATS = {"JPEG", "PNG", "WEBP", "GIF"}
    try:
        img = Image.open(io.BytesIO(data))
        img.verify()
        if img.format not in _ALLOWED_FORMATS:
            raise HTTPException(status_code=400, detail=f"Desteklenmeyen görsel formatı: {img.format}")
        # Decompression bomb check
        img2 = Image.open(io.BytesIO(data))
        if img2.width * img2.height > 25_000_000:
            raise HTTPException(status_code=400, detail="Görsel boyutu çok büyük (max 25MP)")
    except UnidentifiedImageError:
        raise HTTPException(status_code=400, detail="Geçersiz görsel dosyası")
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=400, detail="Görsel doğrulanamadı")

    # Sanitize extension from verified format (not from untrusted Content-Type)
    fmt = (img.format or "JPEG").lower()
    ext = "jpg" if fmt == "jpeg" else fmt
    filename = f"{_uuid.uuid4()}.{ext}"
    blob_path = f"homepage/{filename}"

    from app.services.storage_provider import GCSStorageProvider

    if isinstance(storage_service.provider, GCSStorageProvider):
        bucket = storage_service.provider.get_bucket_for(settings.gcs_bucket_images)
        blob = bucket.blob(blob_path)
        blob.upload_from_string(data, content_type=image.content_type or "image/jpeg")
        # Uniform bucket-level access is enabled — skip legacy ACL make_public().
        # Public URL works because the bucket itself has allUsers read IAM policy.
        url: str = f"https://storage.googleapis.com/{settings.gcs_bucket_images}/{blob_path}"
    else:
        url = storage_service.provider.upload_bytes(
            data, blob_path, image.content_type or "image/jpeg"
        )

    return {"url": url}

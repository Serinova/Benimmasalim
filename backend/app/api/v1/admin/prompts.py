"""Admin Prompt Template API — sadeleştirilmiş CRUD.

Prompt şablonlarını listeleme, oluşturma, güncelleme, silme.
Cache yönetimi dahil.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_admin_user, get_db
from app.models.prompt_template import PromptCategory, PromptTemplate
from app.prompt.service import PromptService

router = APIRouter()


# ── Schemas ──────────────────────────────────────────────────────────────────

class PromptCreate(BaseModel):
    key: str
    name: str
    category: str = PromptCategory.STORY_SYSTEM
    description: str | None = None
    content: str
    content_en: str | None = None


class PromptUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    content: str | None = None
    content_en: str | None = None


class PromptResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    key: str
    name: str
    category: str
    description: str | None = None
    content: str
    content_en: str | None = None
    version: int
    is_active: bool
    modified_by: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class PromptListResponse(BaseModel):
    prompts: list[PromptResponse]
    total: int


# ── Endpoints ────────────────────────────────────────────────────────────────

@router.get("", response_model=PromptListResponse)
async def list_prompts(
    category: str | None = None,
    db: AsyncSession = Depends(get_db),
    _admin=Depends(get_admin_user),
) -> PromptListResponse:
    """Tüm aktif prompt template'larını listeler."""
    query = select(PromptTemplate).where(PromptTemplate.is_active == True)
    if category:
        query = query.where(PromptTemplate.category == category)
    query = query.order_by(PromptTemplate.category, PromptTemplate.key)

    result = await db.execute(query)
    prompts = result.scalars().all()

    return PromptListResponse(
        prompts=[PromptResponse.model_validate(p) for p in prompts],
        total=len(prompts),
    )


@router.post("", response_model=PromptResponse, status_code=status.HTTP_201_CREATED)
async def create_prompt(
    request: PromptCreate,
    db: AsyncSession = Depends(get_db),
    admin=Depends(get_admin_user),
) -> PromptResponse:
    """Yeni prompt template oluşturur."""
    existing = await db.execute(
        select(PromptTemplate).where(PromptTemplate.key == request.key)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"'{request.key}' anahtarı zaten mevcut",
        )

    prompt = PromptTemplate(
        key=request.key,
        name=request.name,
        category=request.category,
        description=request.description,
        content=request.content,
        content_en=request.content_en,
        modified_by=getattr(admin, "email", "admin"),
    )
    db.add(prompt)
    await db.commit()
    await db.refresh(prompt)

    return PromptResponse.model_validate(prompt)


@router.get("/cache-stats")
async def cache_stats(_admin=Depends(get_admin_user)) -> dict:
    """Cache istatistiklerini döner."""
    return PromptService.cache_stats()


@router.post("/clear-cache")
async def clear_cache(
    key: str | None = None,
    _admin=Depends(get_admin_user),
) -> dict:
    """Cache temizler."""
    PromptService.clear_cache(key)
    return {"success": True, "message": f"Cache temizlendi: {key or 'tümü'}"}


@router.get("/{key}", response_model=PromptResponse)
async def get_prompt(
    key: str,
    db: AsyncSession = Depends(get_db),
    _admin=Depends(get_admin_user),
) -> PromptResponse:
    """Tek prompt template döner."""
    result = await db.execute(
        select(PromptTemplate).where(
            PromptTemplate.key == key,
            PromptTemplate.is_active == True,
        )
    )
    prompt = result.scalar_one_or_none()
    if not prompt:
        raise HTTPException(status_code=404, detail=f"Prompt bulunamadı: {key}")
    return PromptResponse.model_validate(prompt)


@router.put("/{key}", response_model=PromptResponse)
async def update_prompt(
    key: str,
    request: PromptUpdate,
    db: AsyncSession = Depends(get_db),
    admin=Depends(get_admin_user),
) -> PromptResponse:
    """Prompt template günceller. Version otomatik artırılır."""
    result = await db.execute(
        select(PromptTemplate).where(
            PromptTemplate.key == key,
            PromptTemplate.is_active == True,
        )
    )
    prompt = result.scalar_one_or_none()
    if not prompt:
        raise HTTPException(status_code=404, detail=f"Prompt bulunamadı: {key}")

    if request.name is not None:
        prompt.name = request.name
    if request.description is not None:
        prompt.description = request.description
    if request.content is not None:
        prompt.content = request.content
    if request.content_en is not None:
        prompt.content_en = request.content_en

    prompt.version += 1
    prompt.modified_by = getattr(admin, "email", "admin")

    await db.commit()
    await db.refresh(prompt)

    PromptService.clear_cache(key)

    return PromptResponse.model_validate(prompt)


@router.delete("/{key}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_prompt(
    key: str,
    db: AsyncSession = Depends(get_db),
    _admin=Depends(get_admin_user),
) -> None:
    """Prompt'u deaktif eder (soft delete)."""
    result = await db.execute(
        select(PromptTemplate).where(
            PromptTemplate.key == key,
            PromptTemplate.is_active == True,
        )
    )
    prompt = result.scalar_one_or_none()
    if not prompt:
        raise HTTPException(status_code=404, detail=f"Prompt bulunamadı: {key}")

    prompt.is_active = False
    await db.commit()
    PromptService.clear_cache(key)

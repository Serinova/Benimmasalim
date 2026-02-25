"""Public endpoint for homepage sections — no auth required, cached-friendly."""

from fastapi import APIRouter
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select

from app.api.v1.deps import DbSession
from app.models.homepage import HomepageSection, SectionType

router = APIRouter()


class PublicSectionResponse(BaseModel):
    """Public response — no IDs exposed, only visible sections."""

    model_config = ConfigDict(from_attributes=True)

    section_type: SectionType
    title: str | None
    subtitle: str | None
    sort_order: int
    data: dict


@router.get("", response_model=list[PublicSectionResponse])
async def get_homepage_sections(db: DbSession) -> list[HomepageSection]:
    """
    Return all visible homepage sections ordered by sort_order.
    This is a public, unauthenticated endpoint.
    """
    result = await db.execute(
        select(HomepageSection)
        .where(HomepageSection.is_visible.is_(True))
        .order_by(HomepageSection.sort_order)
    )
    return list(result.scalars().all())

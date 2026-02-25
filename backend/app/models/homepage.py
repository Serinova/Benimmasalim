"""Homepage section management model."""

from enum import Enum as PyEnum

from sqlalchemy import Boolean, Integer, String, Text
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDMixin


class SectionType(str, PyEnum):
    """Available homepage section types."""

    HERO = "HERO"
    TRUST_BAR = "TRUST_BAR"
    HOW_IT_WORKS = "HOW_IT_WORKS"
    FEATURES = "FEATURES"
    PREVIEW = "PREVIEW"
    TESTIMONIALS = "TESTIMONIALS"
    PRICING = "PRICING"
    FAQ = "FAQ"
    CTA_BAND = "CTA_BAND"
    FOOTER = "FOOTER"


class HomepageSection(Base, UUIDMixin, TimestampMixin):
    """
    Stores editable content for each homepage section.

    Each section_type is unique — one row per section.
    The `data` JSONB column holds section-specific structured content.
    """

    __tablename__ = "homepage_sections"

    section_type: Mapped[SectionType] = mapped_column(
        SQLEnum(SectionType, name="section_type_enum"),
        unique=True,
        nullable=False,
        index=True,
    )
    title: Mapped[str | None] = mapped_column(String(200), nullable=True)
    subtitle: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_visible: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    data: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)

    def __repr__(self) -> str:
        return f"<HomepageSection {self.section_type.value}>"

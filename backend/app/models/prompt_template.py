"""PromptTemplate model — yeni sadeleştirilmiş versiyon.

Admin panelinden düzenlenebilir AI prompt şablonları.
Eski 8 migration yerine tek clean migration ile oluşturulur.
"""

from enum import StrEnum

from sqlalchemy import Boolean, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDMixin


class PromptCategory(StrEnum):
    """Prompt template kategorileri."""

    STORY_SYSTEM = "story_system"
    VISUAL_TEMPLATE = "visual_template"
    NEGATIVE_PROMPT = "negative_prompt"
    EDUCATIONAL = "educational"


class PromptTemplate(Base, UUIDMixin, TimestampMixin):
    """DB'de saklanan AI prompt şablonları.

    Admin panelinden kod değişikliği gerektirmeden düzenlenebilir.
    """

    __tablename__ = "prompt_templates"

    key: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False, default=PromptCategory.STORY_SYSTEM)
    description: Mapped[str | None] = mapped_column(Text)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    content_en: Mapped[str | None] = mapped_column(Text, nullable=True)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    modified_by: Mapped[str | None] = mapped_column(String(255))

    __table_args__ = (
        Index("idx_prompt_category", "category"),
        Index("idx_prompt_active", "is_active", postgresql_where="is_active = true"),
        Index("idx_prompt_key_active", "key", "is_active"),
    )

    def __repr__(self) -> str:
        return f"<PromptTemplate {self.key} v{self.version}>"

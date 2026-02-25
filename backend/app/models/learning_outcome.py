"""Learning outcome model - Educational objectives for stories."""

from sqlalchemy import Boolean, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDMixin


class LearningOutcome(Base, UUIDMixin, TimestampMixin):
    """
    Learning outcomes (Kazanımlar) that can be woven into stories.

    Categories: SelfCare, PersonalGrowth, SocialSkills, EducationNature

    Each outcome includes:
    - Visual assets for frontend display (icon, color theme)
    - Specific AI instructions for story generation
    """

    __tablename__ = "learning_outcomes"

    # ============ BASIC INFO ============
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)

    # ============ UI VISUAL ASSETS ============
    # Icon URL for the selection card (SVG/PNG)
    icon_url: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="URL of the SVG/PNG icon displayed on selection card"
    )

    # Color theme for card styling (hex code)
    color_theme: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
        comment="Hex color code for card border/background accent (e.g., #FF5733)",
    )

    # ============ AI LOGIC ============
    # Specific instruction for Gemini prompt injection
    # This is the EXACT sentence that will be fed to the AI
    ai_prompt: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Exact instruction for AI story generation with {child_name} placeholder",
    )

    # Alternative: more specific field name (keeping ai_prompt for backward compatibility)
    ai_prompt_instruction: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="Detailed AI instruction - preferred over ai_prompt"
    )

    # V2: Optional banned words for scenarios with flags (e.g. no_family -> "anne,baba,aile")
    banned_words_tr: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="V2: Comma-separated TR words banned from story output when flag active",
    )

    # ============ STORY VALIDATION & VISUAL HINTS ============
    # Comma-separated keywords for validating the outcome appears in story text
    keywords_tr: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Comma-separated TR keywords for story validation (e.g. 'diş,fırça,fırçalama')",
    )
    keywords_en: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Comma-separated EN keywords for story validation (e.g. 'brush,toothbrush,teeth')",
    )
    # Comma-separated visual hints injected into image prompts
    visual_hints_en: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Comma-separated EN visual hints for image prompts (e.g. 'toothbrush,brushing teeth')",
    )

    # ============ CATEGORIZATION ============
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    category_label: Mapped[str | None] = mapped_column(String(100))  # Turkish category name
    age_group: Mapped[str] = mapped_column(String(20), default="3-10")

    # ============ DISPLAY SETTINGS ============
    display_order: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    __table_args__ = (
        Index("idx_outcomes_category", "category", "is_active"),
        Index("idx_outcomes_order", "category", "display_order"),
    )

    def __repr__(self) -> str:
        return f"<LearningOutcome {self.name} ({self.category})>"

    @property
    def effective_ai_instruction(self) -> str | None:
        """Get the effective AI instruction, preferring ai_prompt_instruction over ai_prompt."""
        return self.ai_prompt_instruction or self.ai_prompt

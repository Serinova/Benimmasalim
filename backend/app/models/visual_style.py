"""Visual style model - Art styles for image generation."""

from sqlalchemy import Boolean, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDMixin


class VisualStyle(Base, UUIDMixin, TimestampMixin):
    """
    Visual styles for AI image generation.

    Examples: Default Storybook, 3D Pixar-ish, Watercolor Storybook, Ghibli-ish, Adventure Digital, Yumuşak Pastel
    """

    __tablename__ = "visual_styles"

    # Basic info
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    # Kullanıcıya gösterilen isim (boşsa name kullanılır). İsim değişince kod eşlemesi bozulmaz.
    display_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    thumbnail_url: Mapped[str] = mapped_column(Text, nullable=False)

    # AI prompt modifier (appended to image prompts)
    prompt_modifier: Mapped[str] = mapped_column(Text, nullable=False)

    # Aspect ratios — default: yatay A4 (landscape)
    cover_aspect_ratio: Mapped[str] = mapped_column(String(10), default="3:2")
    page_aspect_ratio: Mapped[str] = mapped_column(String(10), default="3:2")

    # PuLID Settings - Controls face consistency vs style strength
    # NULL = use per-style code fallback (style_config.py)
    # Non-NULL = admin override (takes precedence over code)
    id_weight: Mapped[float | None] = mapped_column(Float, nullable=True, default=None)
    true_cfg: Mapped[float | None] = mapped_column(Float, nullable=True, default=None)
    start_step: Mapped[int | None] = mapped_column(Integer, nullable=True, default=None)

    # Generation quality settings (fal.ai FLUX parameters)
    # NULL = use GenerationConfig defaults (num_inference_steps=28, guidance_scale=3.5)
    num_inference_steps: Mapped[int | None] = mapped_column(Integer, nullable=True, default=None)
    guidance_scale: Mapped[float | None] = mapped_column(Float, nullable=True, default=None)

    # V2: Optional style-specific negative prompt (EN)
    style_negative_en: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="V2: style-specific negative prompt tokens (EN)",
    )

    # Admin override: kod sabitleri yerine bu metinler kullanılır (boşsa constants kullanılır)
    leading_prefix_override: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Stil leading prefix (Admin’den; doluysa constants yerine kullanılır)",
    )
    style_block_override: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="STYLE: bloğu (Admin’den; doluysa constants yerine kullanılır)",
    )

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    def __repr__(self) -> str:
        return f"<VisualStyle {self.name}>"

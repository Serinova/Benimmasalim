"""Book template models for configuring page layouts."""

from enum import Enum

from sqlalchemy import JSON, Boolean, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDMixin


class PageType(str, Enum):
    """Page types in a book."""

    COVER = "cover"
    INNER = "inner"
    BACK = "back"
    DEDICATION = "dedication"


class TextPosition(str, Enum):
    """Text position relative to image."""

    TOP = "top"
    BOTTOM = "bottom"
    LEFT = "left"
    RIGHT = "right"
    OVERLAY = "overlay"  # Text on top of image


class BookTemplate(Base, UUIDMixin, TimestampMixin):
    """
    Book template configuration.

    Defines the layout rules for generating books.
    """

    __tablename__ = "book_templates"

    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)

    # Page dimensions (in mm)
    page_width_mm: Mapped[float] = mapped_column(Float, default=210.0)
    page_height_mm: Mapped[float] = mapped_column(Float, default=210.0)
    bleed_mm: Mapped[float] = mapped_column(Float, default=3.0)

    # Image settings
    image_dpi: Mapped[int] = mapped_column(Integer, default=300)
    image_format: Mapped[str] = mapped_column(String(10), default="PNG")

    # Default page count
    default_page_count: Mapped[int] = mapped_column(Integer, default=16)
    min_page_count: Mapped[int] = mapped_column(Integer, default=12)
    max_page_count: Mapped[int] = mapped_column(Integer, default=32)

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)

    def __repr__(self) -> str:
        return f"<BookTemplate {self.name}>"


class PageTemplate(Base, UUIDMixin, TimestampMixin):
    """
    Page template configuration.

    Defines how each page type (cover, inner, back) should be laid out.
    """

    __tablename__ = "page_templates"

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    page_type: Mapped[str] = mapped_column(String(20), default=PageType.INNER.value)

    # Physical dimensions (mm) - yatay A4 (297×210) kitap baskı formatı
    page_width_mm: Mapped[float] = mapped_column(Float, default=297.0)
    page_height_mm: Mapped[float] = mapped_column(Float, default=210.0)
    bleed_mm: Mapped[float] = mapped_column(Float, default=3.0)

    # Image area (percentage of page)
    image_width_percent: Mapped[float] = mapped_column(Float, default=100.0)
    image_height_percent: Mapped[float] = mapped_column(Float, default=70.0)
    image_x_percent: Mapped[float] = mapped_column(Float, default=0.0)  # Left offset
    image_y_percent: Mapped[float] = mapped_column(Float, default=0.0)  # Top offset

    # Image aspect ratio (for AI generation)
    image_aspect_ratio: Mapped[str] = mapped_column(String(10), default="1:1")

    # Text visibility - allows hiding text completely (e.g., for covers)
    text_enabled: Mapped[bool] = mapped_column(Boolean, default=True)

    # Text area (percentage of page) - only used if text_enabled=True
    text_width_percent: Mapped[float] = mapped_column(Float, default=90.0)
    text_height_percent: Mapped[float] = mapped_column(Float, default=25.0)
    text_x_percent: Mapped[float] = mapped_column(Float, default=5.0)
    text_y_percent: Mapped[float] = mapped_column(Float, default=72.0)

    # Text styling
    text_position: Mapped[str] = mapped_column(String(20), default=TextPosition.BOTTOM.value)
    text_vertical_align: Mapped[str] = mapped_column(String(20), default="bottom")  # top, center, bottom
    font_family: Mapped[str] = mapped_column(String(100), default="Nunito")
    font_size_pt: Mapped[int] = mapped_column(Integer, default=14)
    font_color: Mapped[str] = mapped_column(String(20), default="#2D2D2D")
    font_weight: Mapped[str] = mapped_column(String(20), default="normal")  # normal, bold, light, 100-900
    text_align: Mapped[str] = mapped_column(String(20), default="center")
    line_height: Mapped[float] = mapped_column(Float, default=1.5)

    # Background
    background_color: Mapped[str] = mapped_column(String(20), default="#FFFFFF")

    # Text Stroke (Outline)
    text_stroke_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    text_stroke_color: Mapped[str] = mapped_column(String(20), default="#FFFFFF")
    text_stroke_width: Mapped[float] = mapped_column(Float, default=1.0)

    # Text Background — beyaz bulut overlay (okunabilirlik için)
    text_bg_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    text_bg_color: Mapped[str] = mapped_column(String(20), default="#FFFFFF")
    text_bg_opacity: Mapped[int] = mapped_column(Integer, default=230)  # 0-255
    text_bg_shape: Mapped[str] = mapped_column(String(30), default="cloud")  # rectangle, rounded, soft_vignette, wavy, cloud
    text_bg_blur: Mapped[int] = mapped_column(Integer, default=50)  # 0-200 px blur radius
    # Cloud genişlik/yükseklik kontrolleri (% cinsinden metin alanına göre ek uzantı)
    text_bg_extend_top: Mapped[int] = mapped_column(Integer, default=60)    # metin üstüne % uzantı (0-200)
    text_bg_extend_bottom: Mapped[int] = mapped_column(Integer, default=15) # metin altına % uzantı (0-100)
    text_bg_extend_sides: Mapped[int] = mapped_column(Integer, default=10)  # yanlara % genişlik uzantısı (0-50)
    text_bg_intensity: Mapped[int] = mapped_column(Integer, default=100)    # iç alan yoğunluk % (50-100, 100=tam opak plato)

    # Cover Title — WordArt tarzı kapak başlığı (sadece cover page_type için)
    # cover_title_source: "gemini" → Gemini native text rendering (varsayılan), "overlay" → PIL WordArt
    cover_title_source: Mapped[str] = mapped_column(String(20), default="gemini")
    cover_title_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    cover_title_font_family: Mapped[str] = mapped_column(String(100), default="Lobster")
    cover_title_font_size_pt: Mapped[int] = mapped_column(Integer, default=48)
    cover_title_font_color: Mapped[str] = mapped_column(String(20), default="#FFD700")
    cover_title_arc_intensity: Mapped[int] = mapped_column(Integer, default=35)  # 0=düz, 100=çok kavisli
    cover_title_shadow_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    cover_title_shadow_color: Mapped[str] = mapped_column(String(20), default="#000000")
    cover_title_shadow_offset: Mapped[int] = mapped_column(Integer, default=3)  # px
    cover_title_stroke_width: Mapped[float] = mapped_column(Float, default=2.0)
    cover_title_stroke_color: Mapped[str] = mapped_column(String(20), default="#8B6914")
    cover_title_y_percent: Mapped[float] = mapped_column(Float, default=5.0)  # üstten %
    cover_title_preset: Mapped[str] = mapped_column(String(20), default="premium")  # classic, premium, minimal
    cover_title_effect: Mapped[str] = mapped_column(String(30), default="gold_shine")  # none, gold_shine, silver_shine, bronze_shine, rainbow
    cover_title_letter_spacing: Mapped[int] = mapped_column(Integer, default=0)  # ekstra px aralık (-5 ile 20 arası)

    # Margins (mm)
    margin_top_mm: Mapped[float] = mapped_column(Float, default=10.0)
    margin_bottom_mm: Mapped[float] = mapped_column(Float, default=10.0)
    margin_left_mm: Mapped[float] = mapped_column(Float, default=10.0)
    margin_right_mm: Mapped[float] = mapped_column(Float, default=10.0)

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Dedication page default text template (only for page_type="dedication")
    # Supports {child_name} placeholder
    dedication_default_text: Mapped[str | None] = mapped_column(Text, nullable=True)

    # JSON for additional styling options
    extra_styles: Mapped[dict | None] = mapped_column(JSON, default=None)

    def __repr__(self) -> str:
        return f"<PageTemplate {self.name} ({self.page_type})>"


class BackCoverConfig(Base, UUIDMixin, TimestampMixin):
    """
    Back cover configuration.

    Defines the static back cover design with company info, QR code, and tips.
    """

    __tablename__ = "back_cover_configs"

    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)

    # Company info
    company_name: Mapped[str] = mapped_column(String(200), default="Benim Masalım")
    company_logo_url: Mapped[str | None] = mapped_column(Text)
    company_website: Mapped[str] = mapped_column(String(200), default="www.benimmasalim.com")
    company_email: Mapped[str] = mapped_column(String(200), default="info@benimmasalim.com")
    company_phone: Mapped[str | None] = mapped_column(String(50))
    company_address: Mapped[str | None] = mapped_column(Text)

    # Colors and styling
    background_color: Mapped[str] = mapped_column(String(20), default="#F8F4F0")
    primary_color: Mapped[str] = mapped_column(String(20), default="#6B46C1")
    text_color: Mapped[str] = mapped_column(String(20), default="#333333")

    # QR Code settings
    qr_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    qr_size_mm: Mapped[float] = mapped_column(Float, default=30.0)
    qr_position: Mapped[str] = mapped_column(
        String(20), default="bottom_right"
    )  # bottom_right, bottom_left, center
    qr_label: Mapped[str] = mapped_column(String(100), default="Sesli Kitabı Dinle")

    # Parent tips section
    tips_title: Mapped[str] = mapped_column(String(200), default="Ebeveynlere Öneriler")
    tips_content: Mapped[str] = mapped_column(
        Text,
        default="""• Çocuğunuzla birlikte okuyun, soru sorun
• Her gün düzenli okuma alışkanlığı oluşturun  
• Hikayedeki karakterleri birlikte canlandırın
• Çocuğunuzun hayal gücünü destekleyin
• Okuma sonrası hikayeyi birlikte çizin""",
    )
    tips_font_size: Mapped[int] = mapped_column(Integer, default=10)

    # Additional text sections
    tagline: Mapped[str] = mapped_column(
        String(300), default="Her çocuk kendi masalının kahramanı!"
    )
    copyright_text: Mapped[str] = mapped_column(
        String(300), default="© 2024 Benim Masalım. Tüm hakları saklıdır."
    )

    # Decorative elements
    show_stars: Mapped[bool] = mapped_column(Boolean, default=True)
    show_border: Mapped[bool] = mapped_column(Boolean, default=True)
    border_color: Mapped[str] = mapped_column(String(20), default="#E0D4F7")

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)

    def __repr__(self) -> str:
        return f"<BackCoverConfig {self.name}>"


class AIGenerationConfig(Base, UUIDMixin, TimestampMixin):
    """
    AI generation configuration.

    Controls how AI generates images and text.
    """

    __tablename__ = "ai_generation_configs"

    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)

    # Image generation
    image_provider: Mapped[str] = mapped_column(String(50), default="fal")
    image_model: Mapped[str] = mapped_column(
        String(100), default="gemini-2.5-flash-exp-image-generation"
    )
    image_width: Mapped[int] = mapped_column(Integer, default=1024)
    image_height: Mapped[int] = mapped_column(Integer, default=1024)
    image_quality: Mapped[str] = mapped_column(String(20), default="high")

    # Default prompts
    style_prefix: Mapped[str] = mapped_column(
        Text, default="children's book illustration, vibrant colors, safe for children"
    )
    style_suffix: Mapped[str] = mapped_column(
        Text, default="high quality, detailed, professional artwork"
    )
    negative_prompt: Mapped[str | None] = mapped_column(Text)

    # Story generation
    story_provider: Mapped[str] = mapped_column(String(50), default="gemini")
    story_model: Mapped[str] = mapped_column(String(100), default="gemini-2.5-flash")
    story_temperature: Mapped[float] = mapped_column(Float, default=0.7)
    story_max_tokens: Mapped[int] = mapped_column(Integer, default=8192)

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)

    def __repr__(self) -> str:
        return f"<AIGenerationConfig {self.name}>"

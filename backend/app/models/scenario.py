"""Scenario model - Story templates for AI generation.

Scenarios are PURE CONTENT - they contain story templates and illustrations.
Marketing/pricing logic belongs to the Product model.

PROMPT TEMPLATES:
- cover_prompt_template: Used for book cover (page 0) - vertical, poster-style
- page_prompt_template: Used for inner pages - horizontal, text-friendly

DYNAMIC VARIABLES:
- Admin can define custom input fields per scenario (custom_inputs_schema)
- Users fill these fields during story creation
- Variables are injected into prompts using {variable_key} syntax
"""

import uuid as _uuid
from typing import Any

from pydantic import BaseModel
from sqlalchemy import Boolean, Float, ForeignKey, Index, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin

# =============================================================================
# CUSTOM INPUT SCHEMA TYPES
# =============================================================================


class CustomInputField(BaseModel):
    """
    Schema for a custom input field definition.

    Stored in custom_inputs_schema JSONB column.
    """

    key: str  # Variable key used in templates, e.g., "spaceship_name"
    label: str  # Display label for users, e.g., "Uzay Gemisi Adı"
    type: str  # "text", "number", "select", "textarea"
    default: str | None = None  # Default value
    options: list[str] | None = None  # For "select" type
    required: bool = True
    placeholder: str | None = None
    help_text: str | None = None  # Help text shown to users

    class Config:
        extra = "allow"


# =============================================================================
# DEFAULT PROMPT TEMPLATES - OPTIMIZED FOR FAL.AI FLUX + PULID
# =============================================================================
# IMPORTANT: These templates are designed for the PuLID pipeline:
# - NO physical descriptions (hair, eyes, skin) - PuLID extracts from photo
# - MUST include {clothing_description} for outfit consistency
# - ACTION-ONLY scene descriptions - style comes from StyleConfig
# - Natural flowing sentences (Flux prefers this over comma-separated tags)
# =============================================================================

# Scene-only: no {visual_style} or style tokens. Style is injected at image API (compose_visual_prompt).
DEFAULT_COVER_TEMPLATE = """Story "{book_title}". The scene shows a young child {scene_description}.
The child is wearing {clothing_description}.
Composition: space for the title at the top."""

DEFAULT_PAGE_TEMPLATE = """A young child {scene_description}.
The child is wearing {clothing_description}.
Composition: text overlay at the bottom."""


class Scenario(Base, UUIDMixin, TimestampMixin):
    """
    Scenario model containing story templates.

    Examples: Kapadokya Macerası, Yerebatan Sarnıcı, Göbeklitepe Macerası, Efes Antik Kent Macerası, Çatalhöyük Neolitik Kenti Macerası, Sümela Manastırı Macerası, Sultanahmet Camii Macerası, Galata Kulesi Macerası, Kudüs Eski Şehir Macerası, Abu Simbel Tapınakları Macerası, Tac Mahal Macerası

    Prompt Templates (OPTIMIZED FOR FAL.AI FLUX + PULID):
    - cover_prompt_template: For book cover (vertical, poster-style, title area)
    - page_prompt_template: For inner pages (horizontal, text overlay space)

    Available Variables:
    - {book_title}: Generated story title (cover only)
    - {scene_description}: ACTION-ONLY scene description (no physical traits!)
    - {clothing_description}: What the child is wearing (for outfit consistency)
    - {visual_style}: Selected visual style modifier

    REMOVED Variables (PuLID handles these from photo):
    - {child_description}: NO LONGER USED - conflicts with PuLID face extraction
    - {child_name}: Not needed in image prompts
    """

    __tablename__ = "scenarios"

    # ============ BASIC INFO ============
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    thumbnail_url: Mapped[str] = mapped_column(Text, nullable=False)

    # ============ PROMPT TEMPLATES ============
    # Cover prompt template - vertical, poster-style, space for title
    # Variables: {book_title}, {child_name}, {child_description}, {visual_style}
    cover_prompt_template: Mapped[str] = mapped_column(
        Text, nullable=False, default=DEFAULT_COVER_TEMPLATE
    )

    # Page prompt template - horizontal, space for text overlay
    # Variables: {child_name}, {child_description}, {visual_style}, {scene_description}
    page_prompt_template: Mapped[str] = mapped_column(
        Text, nullable=False, default=DEFAULT_PAGE_TEMPLATE
    )

    # ============ MEDIA ASSETS ============
    # Gallery images for carousel (JSONB array of URLs)
    gallery_images: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True, default=list)

    # ============ CUSTOM INPUTS (Dynamic Variables) ============
    # Admin-defined custom input fields for this scenario
    # Users fill these during story creation, values are injected into prompts
    # Structure: [{"key": "spaceship_name", "label": "Uzay Gemisi Adı", "type": "text"}, ...]
    custom_inputs_schema: Mapped[list[dict] | None] = mapped_column(
        JSONB,
        nullable=True,
        default=list,
        comment="Dynamic input fields defined by admin for this scenario",
    )

    # ============ AI STORY GENERATION ============
    # Template for Gemini to generate the story TEXT (not images)
    # This is different from cover/page_prompt_template which are for IMAGES
    ai_prompt_template: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="Template for AI story text generation (Gemini)"
    )

    # ============ CULTURAL & LOCATION SETTINGS ============
    # Location constraints ensure all scenes include specific location elements
    # Example: "Cappadocia fairy chimneys, hot air balloons, rock formations"
    location_constraints: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="Required location elements that must appear in every scene"
    )

    # Cultural elements to include in backgrounds (blurred bokeh style)
    # Example: {"primary": ["fairy chimneys", "balloons"], "colors": "warm earth tones"}
    cultural_elements: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
        default=None,
        comment="Cultural background elements for themed bokeh backgrounds",
    )

    # Theme identifier for scenario categorization
    # Example: "cappadocia", "space_adventure", "underwater"
    theme_key: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="Theme identifier for automatic clothing and background selection",
    )

    # ============ SCENARIO BIBLE (V3) ============
    # Cultural facts pack, side characters, puzzle types, tone rules for location-based generation
    # Structure: {"cultural_facts": [...], "allowed_side_characters": [...],
    #             "puzzle_types": [...], "tone_rules": [...]}
    scenario_bible: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
        default=None,
        comment="V3: Cultural facts pack, side characters, puzzle types, tone rules",
    )

    # ============ PROMPT SYSTEM V2 ============
    # Story-writing prompt (TR) — used in PASS-1 Gemini call.  Replaces ai_prompt_template.
    story_prompt_tr: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="V2: TR story-writing prompt for Gemini PASS-1 (replaces ai_prompt_template)",
    )

    # Short English location tag — normalised; e.g. "Cappadocia", "Istanbul"
    location_en: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="V2: English location name used in visual prompts",
    )

    # Flexible flags JSONB — e.g. {"no_family": true}
    flags: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
        server_default="{}",
        comment="V2: Flexible flags (no_family, indoor_only …)",
    )

    # Default number of story pages for this scenario
    default_page_count: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        server_default="6",
        comment="V2: Default page count for story generation",
    )

    # ============ MARKETING FIELDS ============
    # Promotional video URL for scenario detail panel (YouTube embed or direct video)
    marketing_video_url: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="YouTube embed or direct video URL for scenario marketing panel",
    )

    # Marketing gallery images (separate from content gallery_images)
    # Used in scenario detail/product cards for marketing purposes
    marketing_gallery: Mapped[list | None] = mapped_column(
        JSONB,
        nullable=True,
        default=list,
        comment="Marketing gallery image URLs for scenario product cards",
    )

    # Optional price override for display purposes (does not affect actual pricing)
    marketing_price_label: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="Display price label e.g. '299 TL'den başlayan fiyatlarla'",
    )

    # Feature bullet points shown on scenario product cards
    marketing_features: Mapped[list[str] | None] = mapped_column(
        JSONB,
        nullable=True,
        default=list,
        comment="Feature bullet points for scenario product cards",
    )

    # Promotional badge text shown on scenario cards
    marketing_badge: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="Promo badge text e.g. 'Yeni!', 'En Çok Tercih Edilen'",
    )

    # Target age range for this scenario
    age_range: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        comment="Target age range e.g. '3-8 yaş'",
    )

    # Estimated reading/activity duration
    estimated_duration: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        comment="Estimated duration e.g. '15 dakika'",
    )

    # Short tagline for scenario cards
    tagline: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="Short tagline for scenario product cards",
    )

    # Rating and social proof
    rating: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
        comment="Scenario rating score (0-5)",
    )
    review_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        comment="Number of reviews/orders for social proof",
    )

    # ============ PRODUCT LINK & OVERRIDE SETTINGS ============
    # linked_product_id: The base product whose settings this scenario inherits.
    # When set, all production settings (templates, paper, cover, AI config, pricing)
    # are pulled from that product unless an explicit override field is set below.
    linked_product_id: Mapped[_uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("products.id", ondelete="SET NULL"),
        nullable=True,
        comment="Base product whose production settings this scenario inherits",
    )
    linked_product = relationship("Product", foreign_keys=[linked_product_id], lazy="selectin")

    # ── Pricing overrides (None = use linked_product's value) ──
    price_override_base: Mapped[float | None] = mapped_column(
        Numeric(10, 2),
        nullable=True,
        comment="Override Product.base_price for this scenario",
    )
    price_override_extra_page: Mapped[float | None] = mapped_column(
        Numeric(10, 2),
        nullable=True,
        comment="Override Product.extra_page_price for this scenario",
    )

    # ── Template overrides (UUID strings; None = use linked_product's templates) ──
    cover_template_id_override: Mapped[str | None] = mapped_column(
        String(36),
        nullable=True,
        comment="Override Product.cover_template_id for this scenario",
    )
    inner_template_id_override: Mapped[str | None] = mapped_column(
        String(36),
        nullable=True,
        comment="Override Product.inner_template_id for this scenario",
    )
    back_template_id_override: Mapped[str | None] = mapped_column(
        String(36),
        nullable=True,
        comment="Override Product.back_template_id for this scenario",
    )

    # ── AI config override ──
    ai_config_id_override: Mapped[str | None] = mapped_column(
        String(36),
        nullable=True,
        comment="Override Product.ai_config_id for this scenario",
    )

    # ── Physical / print overrides ──
    paper_type_override: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="Override Product.paper_type (e.g. 'Kuşe 200gr')",
    )
    paper_finish_override: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        comment="Override Product.paper_finish (e.g. 'Parlak')",
    )
    cover_type_override: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        comment="Override Product.cover_type (e.g. 'Yumuşak Kapak')",
    )
    lamination_override: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        comment="Override Product.lamination",
    )
    orientation_override: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
        comment="Override Product.orientation ('portrait' or 'landscape')",
    )
    min_page_count_override: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="Override Product.min_page_count",
    )
    max_page_count_override: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="Override Product.max_page_count",
    )

    # ============ BOOK STRUCTURE (for marketing display) ============
    # These fields describe the physical book layout shown to customers.
    # They are purely informational — actual generation uses default_page_count + product settings.
    #
    # Example: 22 story pages + 2 greeting + 1 back info + 2 covers = 27 total
    story_page_count: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="Number of AI-generated story pages (e.g. 22). Shown in marketing.",
    )
    cover_count: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        server_default="2",
        comment="Number of cover pages (front + back = 2). Shown in marketing.",
    )
    greeting_page_count: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        server_default="2",
        comment="Number of greeting/karşılama pages (e.g. 2: dedication + scenario intro).",
    )
    back_info_page_count: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        server_default="1",
        comment="Number of back-info pages (e.g. 1: educational back page).",
    )

    # ============ OUTFIT DESIGN (per-scenario, gender-specific) ============
    # Scenario-specific outfit descriptions used in visual prompt generation.
    # These override the generic gender defaults in gemini_service.py.
    # Written in English for AI image generation compatibility.
    outfit_girl: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Outfit description for girl characters in this scenario (English, for AI prompts)",
    )
    outfit_boy: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Outfit description for boy characters in this scenario (English, for AI prompts)",
    )

    # ============ DISPLAY SETTINGS ============
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    display_order: Mapped[int] = mapped_column(Integer, default=0)

    __table_args__ = (Index("idx_scenarios_active_order", "is_active", "display_order"),)

    # ============ HELPER METHODS ============

    @property
    def total_page_count(self) -> int | None:
        """Computed total page count for marketing display.

        Returns None if story_page_count is not set.
        """
        if self.story_page_count is None:
            return None
        return (
            (self.story_page_count or 0)
            + (self.cover_count or 2)
            + (self.greeting_page_count or 2)
            + (self.back_info_page_count or 1)
        )

    def get_custom_input_fields(self) -> list[CustomInputField]:
        """Parse custom_inputs_schema into typed CustomInputField objects."""
        if not self.custom_inputs_schema:
            return []
        return [CustomInputField(**field) for field in self.custom_inputs_schema]

    def get_available_variables(self) -> list[str]:
        """
        Get list of all available variables for this scenario.

        Includes both standard variables and custom inputs.
        """
        # Standard variables (always available)
        standard = [
            "book_title",
            "child_name",
            "child_age",
            "child_gender",
            "scene_description",
            "clothing_description",
            "visual_style",
        ]

        # Custom variables from schema — guard against JSON strings stored in DB
        custom = []
        schema = self.custom_inputs_schema or []
        if isinstance(schema, str):
            import json
            try:
                schema = json.loads(schema)
            except Exception:
                schema = []
        for field in schema:
            if isinstance(field, dict):
                key = field.get("key")
                if key:
                    custom.append(key)
            elif isinstance(field, str):
                # field itself is a raw JSON string element — skip gracefully
                continue

        return standard + custom

    def get_cover_prompt(
        self,
        book_title: str,
        scene_description: str,
        clothing_description: str,
        visual_style: str,
        custom_variables: dict[str, Any] | None = None,
    ) -> str:
        """
        Generate cover prompt with all variables replaced.

        OPTIMIZED FOR FAL.AI PULID:
        - scene_description: ACTION-ONLY (e.g., "standing heroically at castle entrance")
        - clothing_description: What child wears (e.g., "a red t-shirt and blue shorts")
        - NO physical traits - PuLID extracts face from photo

        DYNAMIC VARIABLES:
        - custom_variables: Dict of user-provided values for custom inputs
        - Example: {"spaceship_name": "Apollo", "favorite_toy": "Red Teddy Bear"}
        """
        # Merge standard and custom variables
        all_vars = {
            "book_title": book_title,
            "scene_description": scene_description,
            "clothing_description": clothing_description,
            "visual_style": visual_style,
        }

        if custom_variables:
            all_vars.update(custom_variables)

        # Safe format - ignore missing variables
        return self._safe_format(self.cover_prompt_template, all_vars)

    def get_page_prompt(
        self,
        scene_description: str,
        clothing_description: str,
        visual_style: str,
        custom_variables: dict[str, Any] | None = None,
    ) -> str:
        """
        Generate page prompt with all variables replaced.

        OPTIMIZED FOR FAL.AI PULID:
        - scene_description: ACTION-ONLY (e.g., "running through sunflower field")
        - clothing_description: What child wears (for outfit consistency)
        - NO physical traits - PuLID extracts face from photo

        DYNAMIC VARIABLES:
        - custom_variables: Dict of user-provided values for custom inputs
        """
        all_vars = {
            "scene_description": scene_description,
            "clothing_description": clothing_description,
            "visual_style": visual_style,
        }

        if custom_variables:
            all_vars.update(custom_variables)

        return self._safe_format(self.page_prompt_template, all_vars)

    def get_story_prompt(
        self,
        child_name: str,
        child_age: int,
        child_gender: str,
        outcomes: list[str],
        custom_variables: dict[str, Any] | None = None,
    ) -> str:
        """
        Generate story text generation prompt (for Gemini).

        This is used to generate the STORY TEXT, not images.
        """
        if not self.ai_prompt_template:
            return ""

        all_vars = {
            "child_name": child_name,
            "child_age": child_age,
            "child_gender": child_gender,
            "outcomes": ", ".join(outcomes) if outcomes else "",
        }

        if custom_variables:
            all_vars.update(custom_variables)

        return self._safe_format(self.ai_prompt_template, all_vars)

    @staticmethod
    def _safe_format(template: str, variables: dict[str, Any]) -> str:
        """
        Safely format a template, ignoring missing variables.

        Uses a custom approach to handle missing keys gracefully.
        """
        import re

        result = template
        for key, value in variables.items():
            # Replace {key} with value
            pattern = r"\{" + re.escape(key) + r"\}"
            result = re.sub(pattern, str(value), result)

        return result

    def __repr__(self) -> str:
        return f"<Scenario {self.name}>"

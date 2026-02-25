"""BookContext — kitap bazlı tüm parametrelerin tek seferlik çözümlemesi.

Kitap üretimi başladığında BİR KEZ oluşturulur, TÜM sayfalara aynı şekilde uygulanır.
Bu sayede sayfalar arası stil/karakter/kıyafet tutarsızlığı ortadan kalkar.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import structlog

from app.prompt.style_config import StyleConfig, resolve_style

logger = structlog.get_logger()

MIN_ID_WEIGHT = 0.10   # Matches admin schema ge=0.10
MAX_ID_WEIGHT = 1.50   # Matches admin schema le=1.50


@dataclass
class BookContext:
    """Immutable (kullanım sırasında) kitap bağlamı."""

    child_name: str
    child_age: int
    child_gender: str

    style: StyleConfig
    style_modifier_raw: str = ""

    character_description: str = ""
    clothing_description: str = ""
    hair_description: str = ""

    location_name: str = ""
    location_elements: list[str] = field(default_factory=list)

    face_reference_url: str = ""

    page_count: int = 16
    story_title: str = ""

    scenario_name: str = ""

    # Companion / sidekick character (e.g. Luna the owl)
    companion_name: str = ""
    companion_species: str = ""       # "owl", "cat", "dragon" — NOT a human
    companion_appearance: str = ""    # visual description for prompt lock

    @classmethod
    def build(
        cls,
        *,
        child_name: str,
        child_age: int,
        child_gender: str,
        style_modifier: str = "",
        character_description: str = "",
        clothing_description: str = "",
        hair_description: str = "",
        location_name: str = "",
        location_elements: list[str] | None = None,
        face_reference_url: str = "",
        page_count: int = 16,
        story_title: str = "",
        scenario_name: str = "",
        id_weight_override: float | None = None,
        leading_prefix_override: str | None = None,
        style_block_override: str | None = None,
        companion_name: str = "",
        companion_species: str = "",
        companion_appearance: str = "",
    ) -> BookContext:
        """Stil çözümleme dahil BookContext oluşturur."""
        style = resolve_style(style_modifier)

        needs_rebuild = False
        new_id_weight = style.id_weight
        new_leading_prefix = style.leading_prefix
        new_style_block = style.style_block

        if id_weight_override is not None:
            safe_weight = max(MIN_ID_WEIGHT, min(MAX_ID_WEIGHT, id_weight_override))
            if safe_weight != id_weight_override:
                logger.warning(
                    "id_weight clamped",
                    original=id_weight_override,
                    clamped=safe_weight,
                    style=style.key,
                )
            new_id_weight = safe_weight
            needs_rebuild = True

        if leading_prefix_override:
            new_leading_prefix = leading_prefix_override
            needs_rebuild = True

        if style_block_override:
            new_style_block = style_block_override
            needs_rebuild = True

        if needs_rebuild:
            style = StyleConfig(
                key=style.key,
                anchor=style.anchor,
                leading_prefix=new_leading_prefix,
                style_block=new_style_block,
                cover_prefix=style.cover_prefix,
                cover_suffix=style.cover_suffix,
                inner_prefix=style.inner_prefix,
                inner_suffix=style.inner_suffix,
                negative=style.negative,
                id_weight=new_id_weight,
                start_step=style.start_step,
                true_cfg=style.true_cfg,
            )

        return cls(
            child_name=child_name,
            child_age=child_age,
            child_gender=child_gender,
            style=style,
            style_modifier_raw=style_modifier,
            character_description=character_description,
            clothing_description=clothing_description,
            hair_description=hair_description,
            location_name=location_name,
            location_elements=location_elements or [],
            face_reference_url=face_reference_url,
            page_count=page_count,
            story_title=story_title,
            scenario_name=scenario_name,
            companion_name=companion_name,
            companion_species=companion_species,
            companion_appearance=companion_appearance,
        )

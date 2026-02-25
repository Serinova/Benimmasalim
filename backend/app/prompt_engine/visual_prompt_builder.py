"""visual_prompt_builder — V3 pipeline integration with new prompt system.

Provides build_cover_prompt() and enhance_all_pages() that gemini_service.py
calls during V3 story generation.  These functions bridge the old V3 call
signatures to the new BookContext/PromptComposer pipeline.
"""

from __future__ import annotations

from typing import Any

import structlog

from app.prompt import (
    DEFAULT_COVER_TEMPLATE,
    DEFAULT_INNER_TEMPLATE,
    BookContext,
    PromptComposer,
)
from app.prompt.templates import DEFAULT_BACK_COVER_TEMPLATE
from app.services.ai.cast_validator import build_cast_block

logger = structlog.get_logger()


class VisualBeat:
    pass


def extract_visual_beat(*args, **kwargs):
    return None


def lint_prompt_corruption(*args, **kwargs) -> list:
    return []


def build_enhanced_negative(*args, **kwargs) -> str:
    from app.prompt.negative_builder import BASE_NEGATIVE
    return BASE_NEGATIVE


def compose_enhanced_prompt(*args, **kwargs) -> str:
    return ""


def _strip_embedded_text(prompt: str) -> str:
    return prompt


def _ensure_suffix(prompt: str, suffix: str) -> str:
    if not prompt.rstrip().endswith(suffix.rstrip()):
        return prompt.rstrip() + " " + suffix.strip()
    return prompt


def build_cover_prompt(
    character_bible: Any = None,
    visual_style: str = "",
    location_key: str = "",
    location_constraints: str = "",
    story_title: str = "",
    blueprint: dict | None = None,
    value_visual_motif: str = "",
    likeness_hint: str = "",
    has_pulid: bool = False,
    **kwargs,
) -> tuple[str, str]:
    """Build cover prompt for V3 pipeline.

    Translates the old V3 call signature (character_bible, visual_style, etc.)
    into the new BookContext/PromptComposer system.

    Returns:
        (cover_prompt, negative_prompt) tuple
    """
    child_name = getattr(character_bible, "child_name", "") if character_bible else ""
    child_age = getattr(character_bible, "child_age", 7) if character_bible else 7
    child_gender = getattr(character_bible, "child_gender", "") if character_bible else ""
    outfit = getattr(character_bible, "outfit_en", "") or getattr(character_bible, "fixed_outfit", "") if character_bible else ""
    hair = getattr(character_bible, "hair_style", "") if character_bible else ""
    companion = getattr(character_bible, "companion", None)
    # Face analyzer output — hair color, skin tone, eye shape from uploaded photo
    char_desc = (
        getattr(character_bible, "child_description", "")
        or getattr(character_bible, "appearance_tokens", "")
    ) if character_bible else ""

    ctx = BookContext.build(
        child_name=child_name,
        child_age=child_age,
        child_gender=child_gender,
        style_modifier=visual_style,
        clothing_description=outfit,
        hair_description=hair,
        face_reference_url="ref" if has_pulid else "",
        story_title=story_title,
        location_name=location_key,
        character_description=char_desc,
    )

    scene_parts: list[str] = []
    bp = blueprint or {}
    cover_scene = bp.get("cover_scene_en") or bp.get("cover_scene", "")
    if cover_scene:
        scene_parts.append(cover_scene)
    elif story_title:
        scene_parts.append(f"A magical adventure scene for '{story_title}'")

    if location_key:
        scene_parts.append(f"set in {location_key}")

    if location_constraints:
        scene_parts.append(f"Location Details (include relevant elements): {location_constraints}")

    if companion:
        comp_name = getattr(companion, "name", "")
        comp_species = getattr(companion, "species", "")
        comp_appearance = getattr(companion, "appearance", "")
        if comp_name and comp_species:
            scene_parts.append(
                f"accompanied by {comp_name} the {comp_species}"
                + (f" ({comp_appearance})" if comp_appearance else "")
            )

    if value_visual_motif:
        scene_parts.append(value_visual_motif)

    scene_description = ". ".join(scene_parts) if scene_parts else "A child on a magical adventure"

    composer = PromptComposer(ctx, cover_template=DEFAULT_COVER_TEMPLATE)
    result = composer.compose_cover(scene_description)

    logger.info(
        "V3_build_cover_prompt_composed",
        style=ctx.style.key,
        scene_length=len(scene_description),
        flux_prompt_length=len(result.prompt),
        negative_length=len(result.negative_prompt),
        has_pulid=has_pulid,
    )

    # Return (gemini_scene, flux_prompt, negative_prompt).
    # Callers (Gemini path) use gemini_scene; flux_prompt kept for potential Fal AI use.
    return scene_description, result.prompt, result.negative_prompt


def build_back_cover_prompt(
    character_bible: Any = None,
    visual_style: str = "",
    location_key: str = "",
    story_title: str = "",
    blueprint: dict | None = None,
    value_visual_motif: str = "",
    likeness_hint: str = "",
    has_pulid: bool = False,
    **kwargs,
) -> tuple[str, str, str]:
    """Build back cover prompt — closing scene, bottom 35% clear for text overlay.

    Returns:
        (scene_description, flux_prompt, negative_prompt) tuple — same as build_cover_prompt.
    """
    child_name = getattr(character_bible, "child_name", "") if character_bible else ""
    child_age = getattr(character_bible, "child_age", 7) if character_bible else 7
    child_gender = getattr(character_bible, "child_gender", "") if character_bible else ""
    outfit = (
        getattr(character_bible, "outfit_en", "") or getattr(character_bible, "fixed_outfit", "")
        if character_bible else ""
    )
    hair = getattr(character_bible, "hair_style", "") if character_bible else ""
    char_desc = (
        getattr(character_bible, "child_description", "")
        or getattr(character_bible, "appearance_tokens", "")
    ) if character_bible else ""

    ctx = BookContext.build(
        child_name=child_name,
        child_age=child_age,
        child_gender=child_gender,
        style_modifier=visual_style,
        clothing_description=outfit,
        hair_description=hair,
        face_reference_url="ref" if has_pulid else "",
        story_title=story_title,
        location_name=location_key,
        character_description=char_desc,
    )

    bp = blueprint or {}
    # Use dedicated back cover scene if provided, otherwise build a closing scene
    back_cover_scene = (
        bp.get("back_cover_scene_en")
        or bp.get("back_cover_scene")
        or ""
    )
    if not back_cover_scene:
        # Generate a closing/farewell scene based on location and story
        location_phrase = f" in {location_key}" if location_key else ""
        back_cover_scene = (
            f"Child stands{location_phrase}, looking back at the viewer with a joyful smile, "
            f"arms slightly raised in a happy farewell gesture. The adventure is complete, "
            f"golden warm light surrounds the child. Peaceful, magical atmosphere."
        )
        if value_visual_motif:
            back_cover_scene += f" {value_visual_motif}"

    composer = PromptComposer(ctx, cover_template=DEFAULT_BACK_COVER_TEMPLATE)
    result = composer.compose_cover(back_cover_scene)

    logger.info(
        "V3_build_back_cover_prompt_composed",
        style=ctx.style.key,
        scene_length=len(back_cover_scene),
        flux_prompt_length=len(result.prompt),
        negative_length=len(result.negative_prompt),
        has_pulid=has_pulid,
    )

    return back_cover_scene, result.prompt, result.negative_prompt


def enhance_all_pages(
    pages: list[dict] | None = None,
    blueprint: dict | None = None,
    character_bible: Any = None,
    visual_style: str = "",
    location_key: str = "",
    value_visual_motif: str = "",
    likeness_hint: str = "",
    has_pulid: bool = False,
    leading_prefix_override: str | None = None,
    style_block_override: str | None = None,
    **kwargs,
) -> dict[str, list[dict]]:
    """Enhance all page visual prompts with style, character, and composition.

    Takes raw Gemini page data and enhances each page's image_prompt_en
    using the new PromptComposer system.

    Returns:
        {"pages": enhanced_pages}
    """
    if pages is None:
        pages = kwargs.get("pages", [])

    if not pages:
        return {"pages": pages}

    child_name = getattr(character_bible, "child_name", "") if character_bible else ""
    child_age = getattr(character_bible, "child_age", 7) if character_bible else 7
    child_gender = getattr(character_bible, "child_gender", "") if character_bible else ""
    outfit = getattr(character_bible, "outfit_en", "") or getattr(character_bible, "fixed_outfit", "") if character_bible else ""
    hair = getattr(character_bible, "hair_style", "") if character_bible else ""
    companion = getattr(character_bible, "companion", None)
    char_desc = (
        getattr(character_bible, "child_description", "")
        or getattr(character_bible, "appearance_tokens", "")
    ) if character_bible else ""

    # Companion bilgisini ÖNCE çıkar — BookContext ve companion_suffix için gerekli
    _comp_name_str = ""
    _comp_species_str = ""
    _comp_appearance_str = ""
    companion_suffix = ""
    if companion:
        _comp_name_str = getattr(companion, "name", "")
        _comp_species_str = getattr(companion, "species", "")
        _comp_appearance_str = getattr(companion, "appearance", "")
        if _comp_name_str and _comp_species_str:
            _comp_desc = f", {_comp_appearance_str}" if _comp_appearance_str else ""
            companion_suffix = (
                f" {_comp_name_str} the {_comp_species_str}{_comp_desc} is present in the scene. "
                f"IMPORTANT: {_comp_name_str} is a {_comp_species_str} (an animal/creature, NOT a human child). "
                f"Draw {_comp_name_str} as a {_comp_species_str} only."
            )

    ctx = BookContext.build(
        child_name=child_name,
        child_age=child_age,
        child_gender=child_gender,
        style_modifier=visual_style,
        clothing_description=outfit,
        hair_description=hair,
        face_reference_url="ref" if has_pulid else "",
        page_count=len(pages),
        location_name=location_key,
        leading_prefix_override=leading_prefix_override or None,
        style_block_override=style_block_override or None,
        character_description=char_desc,
        # Companion bilgisi — cast lock ve negatif prompt için zorunlu
        companion_name=_comp_name_str,
        companion_species=_comp_species_str,
        companion_appearance=_comp_appearance_str,
    )

    composer = PromptComposer(ctx, inner_template=DEFAULT_INNER_TEMPLATE)

    # Pre-compute location keywords for consistent injection check
    _loc_words: list[str] = []
    if location_key:
        _loc_norm = location_key.lower().replace("-", " ")
        _loc_words = [w.strip() for w in _loc_norm.split() if len(w.strip()) > 3]

    enhanced_pages: list[dict] = []
    for page_data in pages:
        page = dict(page_data)
        raw_prompt = (page.get("image_prompt_en") or "").strip()
        page_num = page.get("page", 0)

        if not raw_prompt:
            enhanced_pages.append(page)
            continue

        scene = raw_prompt
        if companion_suffix and companion_suffix not in scene:
            scene = scene.rstrip(".") + "." + companion_suffix

        if value_visual_motif and value_visual_motif not in scene:
            scene = scene.rstrip(".") + ". " + value_visual_motif

        # Inject location if Gemini omitted it from the scene description
        if _loc_words and not any(kw in scene.lower() for kw in _loc_words):
            scene = scene.rstrip(".").rstrip() + f". Set in {location_key}."
            logger.debug(
                "Location injected into scene",
                page=page_num,
                location=location_key,
            )

        # ── Per-page expected cast (story-driven, NOT hard-coded) ──────────────
        # Read characters from page metadata if Gemini provided them.
        # Falls back to [child_name] + companion if present.
        _page_characters: list[str] = page.get("characters") or []
        if _page_characters:
            # Store expected cast for downstream validator
            page["expected_cast"] = _page_characters
            page["expected_human_count"] = sum(
                1 for c in _page_characters
                if c.lower() not in (_comp_species_str.lower(), _comp_name_str.lower())
            )
        else:
            # Default: one child + companion if present
            _default_cast = [child_name]
            if _comp_name_str:
                _default_cast.append(_comp_name_str)
            page["expected_cast"] = _default_cast
            page["expected_human_count"] = 1

        # Store the clean story scene BEFORE FLUX wrapping — used by Gemini.
        # Gemini already receives style/character/composition via its instruction;
        # it only needs the pure "what's happening in this scene" description.
        page["gemini_scene"] = scene

        result = composer.compose_page(scene, page_num)

        # ── Prepend per-page CAST block to final prompt ────────────────────────
        # Story-driven: uses expected_cast from page metadata (not hard-coded).
        # Supports future multi-child stories: expected_cast can have 2+ names.
        _cast_block = build_cast_block(
            child_name=child_name,
            child_gender=child_gender,
            expected_cast=page.get("expected_cast", [child_name]),
            companion_name=_comp_name_str,
            companion_species=_comp_species_str,
            companion_appearance=_comp_appearance_str,
        )
        final_prompt = _cast_block + "\n\n" + result.prompt if _cast_block else result.prompt

        # image_prompt_en = FLUX-structured prompt (kept for Fal AI / future use)
        page["image_prompt_en"] = final_prompt
        if not page.get("negative_prompt_en"):
            page["negative_prompt_en"] = result.negative_prompt

        enhanced_pages.append(page)

    logger.info(
        "V3_enhance_all_pages_completed",
        style=ctx.style.key,
        page_count=len(enhanced_pages),
        has_pulid=has_pulid,
    )

    return {"pages": enhanced_pages}

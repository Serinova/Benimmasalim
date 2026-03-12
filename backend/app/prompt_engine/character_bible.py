"""Character bible builder — stub module.

Provides the build_character_bible() function expected by
_story_writer.py (line 472).  Currently a minimal stub that
returns a CharacterBible with default values.

The CharacterBible carries identity/outfit/hair tokens used by
visual prompt enhancement.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class CharacterBible:
    """Immutable character description for visual prompt consistency."""

    prompt_block: str = ""
    identity_anchor: str = ""
    identity_anchor_minimal: str = ""
    outfit_en: str = ""
    hair_style: str = ""
    negative_tokens: str = ""
    extras: dict[str, Any] = field(default_factory=dict)


def build_character_bible(
    *,
    child_name: str = "",
    child_age: int = 6,
    child_gender: str = "erkek",
    child_description: str = "",
    outfit_en: str = "",
    hair_style_en: str = "",
    companion_name: str = "",
    companion_type: str = "",
    companion_appearance: str = "",
    has_photo: bool = False,
    **kwargs: Any,
) -> CharacterBible:
    """Build a CharacterBible from child + companion info.

    Currently a minimal stub — returns basic tokens.
    Real implementation will parse face analysis output and
    build rich identity anchors for PuLID consistency.
    """
    gender_en = "girl" if child_gender in ("kiz", "girl", "female") else "boy"
    age_str = f"{child_age}-year-old" if child_age else "young"

    identity = f"a {age_str} {gender_en}"
    if child_description and not child_description.startswith("http"):
        identity = f"{identity}, {child_description[:100]}"

    outfit = outfit_en or "colorful adventure clothes"
    hair = hair_style_en or ""

    prompt_parts = [identity]
    if outfit:
        prompt_parts.append(f"wearing {outfit}")
    if hair:
        prompt_parts.append(f"with {hair}")

    prompt_block = ", ".join(prompt_parts)

    negative = (
        "low quality, blurry, extra limbs, deformed hands, "
        "scary, horror, text, watermark, logo, "
        "different outfit, different hairstyle, outfit change"
    )

    return CharacterBible(
        prompt_block=prompt_block,
        identity_anchor=identity,
        identity_anchor_minimal=f"a {age_str} {gender_en}",
        outfit_en=outfit,
        hair_style=hair,
        negative_tokens=negative,
    )

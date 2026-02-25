"""İç sayfa prompt'u oluşturma.

Her iç sayfa aynı yapıda: stil + karakter + sahne + kompozisyon.
BookContext'ten gelen parametreler tüm sayfalarda aynı.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.prompt.sanitizer import normalize_clothing, sanitize
from app.prompt.templates import (
    BODY_PROPORTION,
    COMPOSITION_RULES,
    DEFAULT_INNER_TEMPLATE,
    SHARPNESS,
)

if TYPE_CHECKING:
    from app.prompt.book_context import BookContext


_GENDER_MAP = {"kız": "girl", "kiz": "girl", "female": "girl", "girl": "girl"}
_BOY_SET = {"erkek", "boy", "male"}


def build_page_prompt(
    ctx: BookContext,
    scene_description: str,
    page_number: int,
    *,
    template: str | None = None,
) -> str:
    """İç sayfa prompt'u oluşturur.

    Args:
        ctx: Kitap bağlamı
        scene_description: Gemini PASS-2'den gelen sahne tanımı
        page_number: Sayfa numarası (1-based)
        template: DB'den gelen özel template (None ise default kullanılır)
    """
    tpl = template or DEFAULT_INNER_TEMPLATE
    _gender_str = str(ctx.child_gender or "").strip().lower()
    # Explicit mapping — unknown/empty gender stays "child" to avoid boy+girl conflict
    if _gender_str in _GENDER_MAP:
        gender_en = "girl"
    elif _gender_str in _BOY_SET:
        gender_en = "boy"
    else:
        gender_en = "child"  # neutral — prevents double-child from gender mismatch

    clothing = normalize_clothing(ctx.clothing_description)
    if not clothing:
        from app.prompt.templates import get_default_clothing
        clothing = get_default_clothing(gender_en)
    
    from app.prompt.templates import get_default_hair
    hair = (ctx.hair_description or "").strip() or get_default_hair()

    body = tpl.format(
        clothing_description=clothing,
        hair_description=hair,
        scene_description=sanitize(scene_description, is_cover=False),
        child_name=ctx.child_name or "the child",
        child_age=ctx.child_age,
        child_gender=gender_en,
    )

    parts: list[str] = []

    # 1. SCENE FIRST — story action gets full token attention
    parts.append(body)

    # 2. Style anchor + leading rules (art direction)
    parts.append(ctx.style.anchor)
    parts.append(ctx.style.leading_prefix.strip())

    # 3. Character description lock (forensic hair/face/skin from photo analysis)
    if ctx.character_description:
        parts.append(
            f"CHARACTER IDENTITY LOCK — MAXIMUM FACIAL RESEMBLANCE REQUIRED: {ctx.character_description}. "
            f"CRITICAL: Preserve EXACT facial features (eye shape, nose shape, mouth shape, face shape, eyebrow shape), "
            f"EXACT hair color, EXACT hairstyle (length, texture, parting), and EXACT skin tone. "
            f"The face MUST be instantly recognizable as the SAME child from the reference photo on EVERY page. "
            f"DO NOT simplify, genericize, or cartoonize the facial features — maintain strong facial similarity."
        )

    # 4. Character consistency locks (hair, clothing, gender)
    parts.append(BODY_PROPORTION)
    if gender_en != "child":
        parts.append(
            f"GENDER LOCK: The main character is a {gender_en}. "
            f"Must remain a {gender_en} on every single page — no exceptions."
        )

    # 5. Cast lock — exactly one child + companion species lock
    child_name = ctx.child_name or "the child"
    comp_name = (ctx.companion_name or "").strip()
    comp_species = (ctx.companion_species or "").strip()
    comp_appearance = (ctx.companion_appearance or "").strip()

    if comp_name and comp_species:
        # Companion present: lock cast to exactly child + companion
        comp_desc = f"{comp_appearance}, " if comp_appearance else ""
        parts.append(
            f"CAST LOCK — EXACTLY two characters on this page: "
            f"(1) {child_name} the {gender_en} child, "
            f"(2) {comp_name} who is a {comp_species} ({comp_desc}NOT a human, NOT a child). "
            f"CRITICAL: {comp_name} is a {comp_species}, never draw {comp_name} as a human or child. "
            f"Only ONE human child ({child_name}) in the entire scene. "
            f"No other children, no extra kids, no background children."
        )
    else:
        # No companion: only one child
        parts.append(
            f"CAST LOCK — Only ONE human character: {child_name}. "
            f"No other children, no extra kids, no background children, no bystanders."
        )

    # 6. Composition + sharpness
    parts.append(COMPOSITION_RULES)
    parts.append(SHARPNESS)

    # 7. Style block last (reinforces rendering style)
    parts.append(ctx.style.style_block)

    return " ".join(p.strip() for p in parts if p.strip())

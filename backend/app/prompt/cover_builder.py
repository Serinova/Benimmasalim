"""Kapak prompt'u oluşturma.

Kapak görseli iç sayfalardan farklı konsepte sahiptir:
- Üst kısımda başlık alanı
- Panoramik lokasyon
- Çocuk alt 1/3'te
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.prompt.sanitizer import normalize_clothing, sanitize
from app.prompt.templates import (
    BODY_PROPORTION,
    COMPOSITION_RULES,
    DEFAULT_BACK_COVER_TEMPLATE,
    DEFAULT_COVER_TEMPLATE,
    SHARPNESS,
)

if TYPE_CHECKING:
    from app.prompt.book_context import BookContext


_GENDER_MAP = {"kız": "girl", "kiz": "girl", "female": "girl", "girl": "girl"}
_BOY_SET = {"erkek", "boy", "male"}


def _resolve_gender(gender_str: str) -> str:
    """Explicit gender mapping — unknown/empty → 'child' to prevent boy+girl conflict."""
    s = (gender_str or "").strip().lower()
    if s in _GENDER_MAP:
        return "girl"
    if s in _BOY_SET:
        return "boy"
    return "child"


def build_cover_prompt(
    ctx: BookContext,
    scene_description: str,
    *,
    template: str | None = None,
) -> str:
    """Kapak prompt'u oluşturur.

    Args:
        ctx: Kitap bağlamı (stil, karakter, kıyafet vb.)
        scene_description: Gemini PASS-2'den gelen sahne tanımı
        template: DB'den gelen özel template (None ise default kullanılır)
    """
    tpl = template or DEFAULT_COVER_TEMPLATE
    gender_en = _resolve_gender(str(ctx.child_gender or ""))

    clothing = normalize_clothing(ctx.clothing_description)
    if not clothing:
        from app.prompt.templates import get_default_clothing
        clothing = get_default_clothing(gender_en)
    
    from app.prompt.templates import get_default_hair
    hair = (ctx.hair_description or "").strip() or get_default_hair()

    body = tpl.format(
        clothing_description=clothing,
        hair_description=hair,
        scene_description=sanitize(scene_description, is_cover=True),
        child_name=ctx.child_name,
        child_age=ctx.child_age,
        story_title=ctx.story_title,
        child_gender=gender_en,
    )

    parts: list[str] = []

    # 1. SCENE FIRST — cover scene gets priority token attention
    parts.append(body)

    # 2. Style anchor + leading rules
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

    # 4. Character consistency locks
    parts.append(BODY_PROPORTION)
    if gender_en != "child":
        parts.append(
            f"GENDER LOCK: The main character is a {gender_en}. "
            f"Must remain a {gender_en} on every single page — no exceptions."
        )

    # 5. Cast lock — companion species lock + only one child
    child_name = ctx.child_name or "the child"
    comp_name = (ctx.companion_name or "").strip()
    comp_species = (ctx.companion_species or "").strip()
    comp_appearance = (ctx.companion_appearance or "").strip()

    if comp_name and comp_species:
        comp_desc = f"{comp_appearance}, " if comp_appearance else ""
        parts.append(
            f"CAST LOCK — EXACTLY two characters: "
            f"(1) {child_name} the {gender_en} child, "
            f"(2) {comp_name} who is a {comp_species} ({comp_desc}NOT a human, NOT a child). "
            f"CRITICAL: {comp_name} is a {comp_species}, never draw {comp_name} as a human. "
            f"Only ONE human child ({child_name}) in the entire scene."
        )
    else:
        parts.append(
            f"CAST LOCK — Only ONE human character: {child_name}. "
            f"No other children, no extra kids, no background children."
        )

    # 6. Composition + sharpness
    parts.append(COMPOSITION_RULES)
    parts.append(SHARPNESS)

    # 7. Style block last
    parts.append(ctx.style.style_block)

    return " ".join(p.strip() for p in parts if p.strip())


def build_back_cover_prompt(
    ctx: BookContext,
    scene_description: str,
    *,
    template: str | None = None,
) -> str:
    """Arka kapak prompt'u oluşturur.

    Ön kapakla aynı atmosfer/stil/karakter kullanılır.
    Başlık talimatı eklenmez — arka kapak tamamen görseldir.
    Sahne: ön kapak lokasyonunun devamı, arka/yan açı veya geniş panorama.

    Args:
        ctx: Kitap bağlamı (stil, karakter, kıyafet vb.)
        scene_description: Ön kapak sahne tanımının devamı
        template: DB'den gelen özel template (None ise default kullanılır)
    """
    tpl = template or DEFAULT_BACK_COVER_TEMPLATE
    gender_en = _resolve_gender(str(ctx.child_gender or ""))

    clothing = normalize_clothing(ctx.clothing_description)
    if not clothing:
        from app.prompt.templates import get_default_clothing
        clothing = get_default_clothing(gender_en)

    from app.prompt.templates import get_default_hair
    hair = (ctx.hair_description or "").strip() or get_default_hair()

    body = tpl.format(
        clothing_description=clothing,
        hair_description=hair,
        scene_description=sanitize(scene_description, is_cover=True),
        child_name=ctx.child_name,
        child_age=ctx.child_age,
        child_gender=gender_en,
    )

    parts: list[str] = []

    parts.append(body)
    parts.append(ctx.style.anchor)
    parts.append(ctx.style.leading_prefix.strip())

    if ctx.character_description:
        parts.append(
            f"CHARACTER IDENTITY LOCK — {ctx.character_description} "
            f"Preserve this exact hair color, hairstyle, and skin tone on every page."
        )

    parts.append(BODY_PROPORTION)
    if gender_en != "child":
        parts.append(
            f"GENDER LOCK: The main character is a {gender_en}. "
            f"Must remain a {gender_en} on every single page — no exceptions."
        )
    parts.append(COMPOSITION_RULES)
    parts.append(SHARPNESS)
    parts.append(ctx.style.style_block)

    return " ".join(p.strip() for p in parts if p.strip())

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
_HEAD_COVERING_KEYWORDS = ("hijab", "headscarf", "taqiyah", "takke", "head covering", "prayer cap")

_IHRAM_STATE_KEYWORDS = (
    "ihram garment", "in ihram", "dressed in ihram", "white ihram", "ihram cloth",
    "two-piece white", "two piece white", "state of ihram", "ihram (sacred",
    "ihram state", "other passengers", "ihram", "mikat",
)
# Sadece açık “tıraş” ifadeleri — “saç kesme”/taqsir kel yapmaz
_HALQ_STATE_KEYWORDS = (
    "hair has been shaved", "head shaved", "shaved head", "after shaving",
    "hair shaved", "shaving area", "after his hair",
    "newly shaved", "clean-shaved head", "tıraş edildi", "shaved bald",
)


def _detect_scene_ihram_state(scene_desc: str) -> str:
    """Sahne metninden ihram/halq durumunu tespit eder."""
    _lower = (scene_desc or "").lower()
    if any(kw in _lower for kw in _HALQ_STATE_KEYWORDS):
        return "halq"
    if any(kw in _lower for kw in _IHRAM_STATE_KEYWORDS):
        return "ihram"
    return "normal"


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
    
    # Detect ihram/halq state from scene description
    _ihram_state = _detect_scene_ihram_state(scene_description)

    # Check for head covering
    _clothing_lower = (clothing or "").lower()
    _needs_head_cover = any(kw in _clothing_lower for kw in _HEAD_COVERING_KEYWORDS)

    # İhram: only boys go bare-headed; girls keep hijab throughout Umrah
    if _ihram_state == "ihram" and gender_en == "boy":
        _needs_head_cover = False

    from app.prompt.templates import get_default_hair
    if _ihram_state == "ihram" and gender_en == "boy":
        hair = "head completely uncovered and bare (NO taqiyah, NO hat — ihram requires bare head)"
        clothing = (
            "two-piece seamless white ihram garment: upper cloth (rida) draped over left shoulder, "
            "lower cloth (izar) wrapped around waist — pure white, NO stitching, NO decoration. "
            "Simple tan sandals. CRITICAL: NO taqiyah, NO prayer cap — head is BARE during ihram."
        )
    elif _ihram_state == "halq" and gender_en == "boy":
        hair = "completely shaved bald head — smooth scalp, no hair at all (just completed halq ritual)"
    elif _needs_head_cover:
        if gender_en == "boy":
            hair = "wearing a small round white knitted taqiyah skull-cap on top of the head"
        else:
            hair = "hair fully covered by a properly wrapped hijab headscarf"
    else:
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
        if _ihram_state == "ihram" and gender_en == "boy":
            parts.append(
                f"CHARACTER IDENTITY LOCK — MAXIMUM FACIAL RESEMBLANCE REQUIRED: {ctx.character_description}. "
                f"CRITICAL: Preserve EXACT facial features (eye shape, nose shape, mouth shape, face shape, eyebrow shape) and EXACT skin tone. "
                f"HEAD LOCK — IHRAM: The boy's head MUST be COMPLETELY BARE — NO taqiyah, NO hat, NO head covering of any kind. "
                f"The face MUST be instantly recognizable as the SAME child from the reference photo on EVERY page."
            )
        elif _ihram_state == "halq" and gender_en == "boy":
            parts.append(
                f"CHARACTER IDENTITY LOCK — MAXIMUM FACIAL RESEMBLANCE REQUIRED: {ctx.character_description}. "
                f"CRITICAL: Preserve EXACT facial features (eye shape, nose shape, mouth shape, face shape, eyebrow shape) and EXACT skin tone. "
                f"HEAD LOCK — POST-HALQ: The boy's head is COMPLETELY SHAVED BALD — smooth scalp, zero hair. This is the halq ritual. "
                f"The face MUST be instantly recognizable as the SAME child from the reference photo on EVERY page."
            )
        elif _needs_head_cover:
            if gender_en == "boy":
                _head_lock = "HEAD COVERING LOCK: The boy wears ONLY a small round white knitted taqiyah skull-cap (NOT a turban, NOT a wrapped cloth, NOT a hood, NOT hijab, NOT headscarf — that is for girls)."
            else:
                _head_lock = "HEAD COVERING LOCK: The girl wears a properly wrapped hijab headscarf. Hair must NOT be visible."
            parts.append(
                f"CHARACTER IDENTITY LOCK — MAXIMUM FACIAL RESEMBLANCE REQUIRED: {ctx.character_description}. "
                f"CRITICAL: Preserve EXACT facial features (eye shape, nose shape, mouth shape, face shape, eyebrow shape) and EXACT skin tone. "
                f"{_head_lock} "
                f"The face MUST be instantly recognizable as the SAME child from the reference photo on EVERY page. "
                f"DO NOT simplify, genericize, or cartoonize the facial features — maintain strong facial similarity."
            )
        else:
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

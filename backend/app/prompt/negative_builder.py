"""Negatif prompt oluşturma — kitap bazlı, tek seferlik.

BookContext'ten stil negatifi + genel negatif + cinsiyet negatifi birleştirilir.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.prompt.book_context import BookContext

BASE_NEGATIVE = (
    "big eyes, chibi, oversized head, bobblehead, "
    "close-up, extreme close-up, portrait, headshot, selfie, face close-up, facial close-up, "
    "face filling frame, face dominates frame, head filling image, zoomed in on face, "
    "looking at camera, direct eye contact, staring at viewer, "
    "cropped body, cut-off legs, no legs visible, legs out of frame, "
    "waist-up only, waist-up shot, half body, upper body only, torso only, "
    "missing legs, missing feet, feet not visible, legs cropped out, "
    "tight framing, tight crop, narrow framing, zoomed in, "
    "stiff pose, empty background, blurred background, bokeh, blurry, depth of field, shallow focus, "
    "low quality, deformed hands, extra fingers, reversed hand, text, watermark, "
    "bad anatomy, "
    "scary, horror, dark atmosphere, weapons, monsters, violence, creepy, nightmare, threatening, blood, adult themes"
)

ANTI_PHOTO_FACE = (
    "photorealistic face, realistic skin pores, DSLR photo quality, "
    "professional photography lighting on face, studio portrait lighting, "
    "pasted face, face swap, collage, deepfake, real-person photo, "
    "face cutout, face overlay, photoshopped face"
)

_BOY_NEGATIVE = "dress, skirt, gown, tutu, girly clothes, feminine clothing, girl, female child"
_GIRL_NEGATIVE = (
    "boy, male child, masculine features, male character, "
    "buzz cut, male clothing, boy's outfit, he, him"
)

_CHARACTER_CONSISTENCY_NEGATIVE = (
    "different outfit, outfit change, costume change, different clothing, "
    "different hairstyle, hair color change, different hair length, "
    "different skin tone, age change, different child"
)

# Extra child / cast drift prevention — always applied
_CAST_LOCK_NEGATIVE = (
    "extra child, additional kid, second child, multiple children, "
    "twin, group of children, classmates, background child, side character child, "
    "random bystander child, another child, other children, "
    "second person, additional person, crowd, bystander, passerby, "
    "duplicate character, mirrored character, background figure"
)


def _build_companion_negative(companion_name: str, companion_species: str) -> str:
    """Companion türünü insan olarak çizmeyi engelleyen negatif prompt."""
    if not companion_name or not companion_species:
        return ""
    name = companion_name.strip()
    species = companion_species.strip().lower()
    # Companion'ın insan/çocuk olarak çizilmesini engelle
    return (
        f"human {name}, child {name}, girl {name}, boy {name}, "
        f"person named {name}, human character named {name}, "
        f"{name} as a human, {name} as a child, {name} as a person"
    )


def build_negative(ctx: BookContext) -> str:
    """Kitap için tek negatif prompt oluşturur."""
    parts: list[str] = [BASE_NEGATIVE]

    parts.append(_CHARACTER_CONSISTENCY_NEGATIVE)
    parts.append(_CAST_LOCK_NEGATIVE)

    if ctx.style.negative:
        parts.append(ctx.style.negative)

    if ctx.face_reference_url:
        parts.append(ANTI_PHOTO_FACE)

    gender = (ctx.child_gender or "").lower()
    if gender in ("erkek", "male", "boy"):
        parts.append(_BOY_NEGATIVE)
    elif gender in ("kız", "kiz", "female", "girl"):
        parts.append(_GIRL_NEGATIVE)
    # unknown/empty gender: no gender negative — avoids adding both which would conflict

    # Companion tür kilidi — companion insan olarak çizilmesin
    companion_neg = _build_companion_negative(
        getattr(ctx, "companion_name", ""),
        getattr(ctx, "companion_species", ""),
    )
    if companion_neg:
        parts.append(companion_neg)

    return ", ".join(parts)

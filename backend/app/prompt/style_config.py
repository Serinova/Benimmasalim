"""Stil tanımları ve çözümleme — tek kaynak.

Her stilin prompt prefix, suffix, anchor, negatif ve PuLID parametreleri burada.
Stil çözümleme _resolve_style_key() üzerinden tek kaskad ile yapılır.
"""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class StyleConfig:
    """Prompt building blocks for a visual style."""

    key: str
    anchor: str
    leading_prefix: str
    style_block: str
    cover_prefix: str
    cover_suffix: str
    inner_prefix: str
    inner_suffix: str
    negative: str
    id_weight: float = 1.0
    start_step: int = 1
    true_cfg: float = 1.0


_CONSISTENCY_NEG = (
    "photorealistic, big eyes, oversized eyes, huge eyes, exaggerated eyes, anime eyes, wide eyes, wide-eyed, "
    "giant cartoon eyes, doll eyes, caricature, cartoon caricature, exaggerated features, "
    "distorted proportions, unrealistic face, chibi, bobblehead, oversized head, giant head, big head, large head, disproportionate head, macrocephaly, bulbous head, "
    "wrong hair color, wrong skin color, wrong hair length, wrong hairstyle, altered hair, "
    "changing hairstyle, generic hair, different hair, hair color change, hair length change, "
    "different outfit, outfit change, clothing change, costume change, wrong clothing, "
    "adult, beard, mustache, wrinkles, aged, ancient costume, robe, period costume"
)

# Composition guards shared by all styles
_COMPOSITION_NEG = (
    "close-up, extreme close-up, portrait, headshot, selfie, face close-up, facial close-up, "
    "face filling frame, face dominates frame, head filling image, zoomed in on face, "
    "waist-up only, waist-up shot, half body, upper body only, torso only, "
    "cropped body, cut-off legs, no legs visible, legs out of frame, legs cropped out, "
    "tight framing, tight crop, narrow framing, zoomed in, "
    "blurred background, bokeh, depth of field, shallow focus"
)

# _FACE_LIKENESS_BLOCK removed — PuLID handles face identity at model level.
# Text face instructions compete with scene tokens for no benefit.

# Inner composition rules shared by all styles
_INNER_COMPOSITION_SUFFIX = (
    "CRITICAL WIDE SHOT REQUIREMENT: Child occupies maximum 25-30% of frame, "
    "rich detailed environment fills 70-75% of frame. "
    "Full body MUST be visible from head to feet, INCLUDING BOTH LEGS AND FEET. "
    "NEVER crop child's legs, NEVER waist-up framing, NEVER close-up on face. "
    "Camera maintains natural distance — child is PART of the scene, NOT the sole focus. "
    "SHARP FOCUS on entire scene from foreground to background — NO depth-of-field blur, NO bokeh, NO selective focus."
)

STYLES: dict[str, StyleConfig] = {
    "default": StyleConfig(
        key="default",
        anchor="2D hand-painted storybook.",
        leading_prefix=(
            "Art style: Cheerful 2D hand-painted storybook illustration. "
            "Crisp lineart, natural realistic proportions (NOT simplified, NOT distorted), "
            "vibrant warm colors (greens, blues, yellows, pinks), "
            "soft shading, subtle paper texture, bright light, detailed layered background. "
            "CRITICAL LIKENESS LOCK — MAXIMUM FACIAL RESEMBLANCE: "
            "PRESERVE EVERY EXACT FACIAL FEATURE from the reference photo: exact eye shape, exact nose shape, exact mouth shape, exact face shape, exact eyebrow shape. "
            "HAIR: Exact hair color (match the reference precisely), exact hairstyle (same cut, same length, same parting, same bangs), exact hair texture (straight/wavy/curly as shown). "
            "SKIN TONE: Exact skin tone from reference — do NOT lighten or darken. "
            "CLOTHING: Exact clothing as specified — same colors, same items. "
            "The child's face MUST be instantly recognizable as the SAME child from the reference photo. "
            "Apply the illustration style ONLY to rendering technique and background — keep the facial identity highly realistic and true to the photo. "
            "Do NOT simplify the child's face into a generic cartoon; keep the exact facial identity, hair shape, and clothing colors. "
            "NOT 3D, NOT anime, NOT digital, NO cinematic, NO film still, NO lens terms. "
            "NO caricature, NO exaggerated features, NO distorted proportions. "
        ),
        style_block=(
            "Cheerful 2D children's book, hand-painted, vibrant warm colors, "
            "MAXIMUM LIKENESS: PRESERVE EXACT FACIAL FEATURES (eye shape, nose, mouth, face shape, eyebrows), "
            "EXACT HAIR COLOR, EXACT HAIRSTYLE (length, texture, parting), EXACT SKIN TONE, AND EXACT CLOTHING. "
            "Face must be instantly recognizable from reference photo. "
            "Natural realistic child proportions, normal head size, small realistic eyes, "
            "NOT caricature, NOT exaggerated, NOT simplified, NOT generic face, NOT 3D, NOT Pixar, sharp focus, consistent character identity."
        ),
        cover_prefix="Wide environmental shot, full body visible. A 2D children's book cover illustration showing",
        cover_suffix="Soft lighting, warm colors, magical atmosphere. Character takes 30% of frame, detailed background 70%.",
        inner_prefix="Wide angle shot, full body visible, environmental scene. A whimsical children's book illustration of",
        inner_suffix=(
            "Soft diffused lighting, visible paper texture, warm inviting colors. "
            + _INNER_COMPOSITION_SUFFIX
        ),
        negative=(
            f"text overlay, logo, letters on image, head rotated, anime, manga, "
            f"3d render, CGI, generic face, simplified face, cartoon generic face, "
            f"altered facial features, different face, wrong face shape, "
            f"{_COMPOSITION_NEG}, {_CONSISTENCY_NEG}"
        ),
        id_weight=1.2,
        start_step=0,
        true_cfg=1.2,
    ),
    "pixar": StyleConfig(
        key="pixar",
        anchor="Pixar-quality 3D CGI animation.",
        leading_prefix=(
            "Art style: Pixar-quality 3D CGI animation. Smooth 3D surfaces, subsurface scattering, "
            "rim lighting, warm cinematic illumination, Disney/Pixar look. "
            "EYES: Naturally proportioned small eyes. "
            "CRITICAL LIKENESS LOCK — MAXIMUM FACIAL RESEMBLANCE: "
            "PRESERVE EVERY EXACT FACIAL FEATURE from the reference photo: exact eye shape, exact nose shape, exact mouth shape, exact face shape, exact eyebrow shape. "
            "HAIR: Exact hair color (match the reference precisely), exact hairstyle (same cut, same length, same parting, same bangs), exact hair texture (straight/wavy/curly as shown). "
            "SKIN TONE: Exact skin tone from reference — do NOT lighten or darken. "
            "CLOTHING: Exact clothing as specified — same colors, same items. "
            "The child's face MUST be instantly recognizable as the SAME child from the reference photo. "
            "Apply the 3D CGI style ONLY to rendering technique and surfaces — keep the facial identity and proportions true to the photo. "
            "Keep the exact facial identity, hair shape, and clothing colors from the description. "
            "NOT 2D, NOT hand-painted, NOT lineart, NOT watercolor. "
            "Child in frame, natural realistic proportions, no chibi, no bobblehead, no caricature. "
        ),
        style_block=(
            "Pixar 3D CGI children's book, vibrant warm colors, natural child proportions, normal head size, "
            "small realistically proportioned eyes (NOT oversized, NOT exaggerated), "
            "MAXIMUM LIKENESS: PRESERVE EXACT FACIAL FEATURES (eye shape, nose, mouth, face shape, eyebrows), "
            "EXACT HAIR COLOR, EXACT HAIRSTYLE (length, texture, parting), EXACT SKIN TONE, AND EXACT CLOTHING. "
            "Face must be instantly recognizable from reference photo. "
            "Smooth 3D shapes, soft shadows, sharp focus, consistent character identity."
        ),
        cover_prefix="Wide environmental shot, full body head-to-toe visible. Pixar-quality 3D CGI children's book cover featuring",
        cover_suffix=(
            "Subsurface scattering, rim lighting, warm cinematic glow. "
            "Character 30% of frame, detailed 3D modeled environment 70%. "
            "SHARP FOCUS on entire scene — NOT bokeh, NOT blurred background."
        ),
        inner_prefix=(
            "WIDE ANGLE SHOT. Full body visible head-to-toe, child occupies 25-30% of frame. "
            "Richly detailed 3D environment fills the background — NO blurred background. "
            "Pixar-quality 3D CGI render, smooth rounded 3D forms, subsurface scattering on skin, "
            "natural child proportions, realistically proportioned eyes, showing"
        ),
        inner_suffix=(
            "Rim lighting, ambient occlusion, soft global illumination, warm cinematic color grading. "
            "SHARP FOCUS on entire scene including background — NO depth-of-field blur, NO bokeh. "
            "Fully modeled detailed 3D environment visible. Child is small in the wide scene, "
            "environment and story details clearly visible. High-quality 3D render."
        ),
        negative=(
            f"text overlay, logo, letters on image, "
            f"close-up, portrait, headshot, selfie, face filling frame, "
            f"waist-up only, cropped body, "
            f"blurred background, bokeh, depth of field, "
            f"2d, flat, flat shading, lineart, hand-drawn, hand-painted, watercolor, gouache, "
            f"oil paint, pencil sketch, paper texture, brush strokes, cartoon 2d, anime, manga, "
            f"cel-shaded, oversized eyes, huge eyes, exaggerated eyes, anime eyes, "
            f"chibi, oversized head, bobblehead, caricature, "
            f"generic face, simplified face, altered facial features, different face, wrong face shape, "
            f"giant cartoon eyes, bug eyes, {_CONSISTENCY_NEG}"
        ),
        id_weight=1.2,
        start_step=0,
        true_cfg=1.2,
    ),
    "watercolor": StyleConfig(
        key="watercolor",
        anchor="Vivid watercolor storybook painting.",
        leading_prefix=(
            "Art style: Vibrant watercolor storybook painting on textured paper. "
            "RICH SATURATED PIGMENTS — deep teals, warm corals, golden yellows, lush greens. "
            "NOT pale, NOT washed-out, NOT faded. Layered washes with visible brushwork, "
            "wet-on-wet blooms, granulating pigments, warm luminous light. "
            "CRITICAL LIKENESS LOCK — MAXIMUM FACIAL RESEMBLANCE: "
            "PRESERVE EVERY EXACT FACIAL FEATURE from the reference photo: exact eye shape, exact nose shape, exact mouth shape, exact face shape, exact eyebrow shape. "
            "HAIR: Exact hair color (match the reference precisely), exact hairstyle (same cut, same length, same parting, same bangs), exact hair texture (straight/wavy/curly as shown). "
            "SKIN TONE: Exact skin tone from reference — do NOT lighten or darken. "
            "CLOTHING: Exact clothing as specified — same colors, same items. "
            "The child's face MUST be instantly recognizable as the SAME child from the reference photo. "
            "Apply watercolor technique ONLY to rendering and textures — do not let watercolor blooms alter or wash out the child's identity, face shape, hair, or exact clothing colors. "
            "Keep facial features clear and recognizable despite watercolor style. "
            "NO digital, NO flat, NO 3D. "
        ),
        style_block=(
            "Vibrant watercolor children's book, rich saturated colors, warm luminous tones, "
            "MAXIMUM LIKENESS: PRESERVE EXACT FACIAL FEATURES (eye shape, nose, mouth, face shape, eyebrows), "
            "EXACT HAIR COLOR, EXACT HAIRSTYLE (length, texture, parting), EXACT SKIN TONE, AND EXACT CLOTHING. "
            "Face must be instantly recognizable from reference photo. "
            "Natural child proportions, normal head size, small realistic eyes, "
            "paper texture, dreamy mood, sharp focus on character, consistent character identity. "
            "NOT pale, NOT washed-out, NOT simplified face."
        ),
        cover_prefix="Wide environmental shot, full body. A luminous vibrant watercolor painting on textured paper, book cover featuring",
        cover_suffix="Rich saturated pigment washes, bold color contrast, gallery-quality watercolor. Character 30% of frame, painted environment dominates.",
        inner_prefix=(
            "Wide angle environmental scene, full body visible. "
            "A vibrant watercolor painting on rough cold-pressed paper showing"
        ),
        inner_suffix=(
            "Rich saturated pigment washes, wet-on-wet blooms, visible granulation. "
            + _INNER_COMPOSITION_SUFFIX
        ),
        negative=(
            f"text overlay, logo, letters on image, head rotated, "
            f"3d render, CGI, photorealistic, "
            f"pale colors, washed out, faded, desaturated, low contrast, muddy colors, "
            f"wrong hair color, different hair color, altered hair color, "
            f"generic face, simplified face, washed out face, blurry face, altered facial features, "
            f"{_COMPOSITION_NEG}, {_CONSISTENCY_NEG}"
        ),
        id_weight=1.4,
        start_step=0,
        true_cfg=1.3,
    ),
    "soft_pastel": StyleConfig(
        key="soft_pastel",
        anchor="Soft pastel storybook illustration.",
        leading_prefix=(
            "Art style: Soft pastel storybook. Thin brown/gray outlines, gentle hand-drawn look, "
            "warm muted palette (beige, cream, coral, blues), pastel texture, cosy atmosphere, soft light. "
            "CRITICAL LIKENESS LOCK — MAXIMUM FACIAL RESEMBLANCE: "
            "PRESERVE EVERY EXACT FACIAL FEATURE from the reference photo: exact eye shape, exact nose shape, exact mouth shape, exact face shape, exact eyebrow shape. "
            "HAIR: Exact hair color (match the reference precisely), exact hairstyle (same cut, same length, same parting, same bangs), exact hair texture (straight/wavy/curly as shown). "
            "SKIN TONE: Exact skin tone from reference — do NOT lighten or darken. "
            "CLOTHING: Exact clothing as specified — same colors, same items. "
            "The child's face MUST be instantly recognizable as the SAME child from the reference photo. "
            "Apply soft pastel style ONLY to colors and mood — despite the soft style, do not smudge or lose the child's identity, specific face shape, hair, and exact clothing colors. "
            "Keep facial features clear and distinct. "
            "NOT 3D, NOT photorealistic, NOT bold cartoon. "
        ),
        style_block=(
            "Soft pastel children's book, gentle lines, warm muted colors, warm gentle mood, "
            "MAXIMUM LIKENESS: PRESERVE EXACT FACIAL FEATURES (eye shape, nose, mouth, face shape, eyebrows), "
            "EXACT HAIR COLOR, EXACT HAIRSTYLE (length, texture, parting), EXACT SKIN TONE, AND EXACT CLOTHING. "
            "Face must be instantly recognizable from reference photo. "
            "Natural child proportions, normal head size, small realistic eyes, "
            "NOT 3D, NOT Pixar, NOT simplified face, NOT smudged face, sharp focus on character, consistent character identity."
        ),
        cover_prefix="Wide environmental shot, full body. Soft pastel children's book cover illustration featuring",
        cover_suffix="Gentle lines, warm muted colors, warm gentle mood. Character 30% of frame, soft background 70%.",
        inner_prefix=(
            "Wide angle environmental scene, full body visible. "
            "Soft pastel storybook illustration with gentle hand-drawn lines showing"
        ),
        inner_suffix=(
            "Thin soft brown or gray outlines, no harsh black. Muted warm palette (beige, cream, soft coral, gentle blues). "
            "Subtle watercolor texture, soft diffused lighting, warm magical atmosphere. "
            + _INNER_COMPOSITION_SUFFIX
        ),
        negative=(
            f"text overlay, logo, letters on image, head rotated, "
            f"3d render, CGI, photorealistic, harsh black outlines, "
            f"generic face, simplified face, smudged face, blurry face, altered facial features, "
            f"{_COMPOSITION_NEG}, {_CONSISTENCY_NEG}"
        ),
        id_weight=1.1,
        start_step=0,
        true_cfg=1.1,
    ),
    "anime": StyleConfig(
        key="anime",
        anchor="Studio Ghibli anime cel-shaded.",
        leading_prefix=(
            "Art style: Studio Ghibli anime cel-shaded. Bold ink outlines, flat color fills, "
            "vibrant gradients, Miyazaki-style backgrounds, vivid sky, rich saturated colors. "
            "CRITICAL LIKENESS LOCK — MAXIMUM FACIAL RESEMBLANCE: "
            "PRESERVE EVERY EXACT FACIAL FEATURE from the reference photo: exact eye shape, exact nose shape, exact mouth shape, exact face shape, exact eyebrow shape. "
            "HAIR: Exact hair color (match the reference precisely), exact hairstyle (same cut, same length, same parting, same bangs), exact hair texture (straight/wavy/curly as shown). "
            "SKIN TONE: Exact skin tone from reference — do NOT lighten or darken. "
            "CLOTHING: Exact clothing as specified — same colors, same items. "
            "The child's face MUST be instantly recognizable as the SAME child from the reference photo. "
            "Apply Ghibli anime style ONLY to line art and color technique — do not change the child to a generic anime face; keep exact facial identity, specific hair shape, and exact clothing colors. "
            "PRESERVE the child's real hair color and skin tone in Ghibli style. Keep facial features recognizable. "
            "NOT 3D, NOT realistic, NOT Western cartoon, NOT watercolor. "
        ),
        style_block=(
            "Ghibli anime storybook, cel-shaded, bold outlines, vibrant colors, "
            "MAXIMUM LIKENESS: PRESERVE EXACT FACIAL FEATURES (eye shape, nose, mouth, face shape, eyebrows), "
            "EXACT HAIR COLOR, EXACT HAIRSTYLE (length, texture, parting), EXACT SKIN TONE, AND EXACT CLOTHING. "
            "Face must be instantly recognizable from reference photo. "
            "Natural child proportions, normal head size, small realistic eyes (NOT large anime eyes), "
            "NOT generic anime face, rich scenery, sharp focus, consistent character identity."
        ),
        cover_prefix="Wide environmental shot, full body. Studio Ghibli anime illustration, book cover featuring",
        cover_suffix="Cel-shaded with bold outlines, Miyazaki-style sky with towering clouds. Character 30% of frame, painted landscape background 70%.",
        inner_prefix=(
            "Wide angle environmental scene, full body visible. "
            "Studio Ghibli anime cel-shaded illustration with bold black outlines showing"
        ),
        inner_suffix=(
            "Flat cel-shaded color fills with subtle gradients, bold ink outlines, "
            "Ghibli-style layered background painting. "
            + _INNER_COMPOSITION_SUFFIX
        ),
        negative=(
            f"text overlay, logo, letters on image, head rotated, "
            f"3d render, CGI, photorealistic, "
            f"generic anime face, simplified anime face, altered facial features, "
            f"{_COMPOSITION_NEG}, {_CONSISTENCY_NEG}"
        ),
        id_weight=1.1,
        start_step=0,
        true_cfg=1.1,
    ),
    "adventure_digital": StyleConfig(
        key="adventure_digital",
        anchor="Digital painting adventure.",
        leading_prefix=(
            "Art style: Adventure 2D digital painting for children's storybook. "
            "Vibrant warm colors (greens, blues, golden yellows, browns), bright lighting, "
            "painterly brushwork, detailed textures, cheerful mood. "
            "CRITICAL LIKENESS LOCK — MAXIMUM FACIAL RESEMBLANCE: "
            "PRESERVE EVERY EXACT FACIAL FEATURE from the reference photo: exact eye shape, exact nose shape, exact mouth shape, exact face shape, exact eyebrow shape. "
            "HAIR: Exact hair color (match the reference precisely), exact hairstyle (same cut, same length, same parting, same bangs), exact hair texture (straight/wavy/curly as shown). "
            "SKIN TONE: Exact skin tone from reference — do NOT lighten or darken. "
            "CLOTHING: Exact clothing as specified — same colors, same items. "
            "The child's face MUST be instantly recognizable as the SAME child from the reference photo. "
            "Apply the digital painting style and brushwork ONLY to rendering technique, textures, and background — keep the facial identity highly realistic and true to the photo. "
            "Do NOT alter the child's facial identity, hair shape, or clothing colors with brushstrokes. Do NOT simplify into a generic painted face. "
            "NOT photorealistic, NOT photo-like, NOT CGI, NOT cartoon flat, NOT anime, "
            "NOT 3D, NOT 3D Pixar animation style, NOT 3D CG animated film look, NOT gouache. "
        ),
        style_block=(
            "Adventure 2D digital painting illustration — flat painted 2D art style. "
            "NOT photorealistic, NOT CGI render, NOT a photo, NOT 3D Pixar movie style, NOT 3D animated film, NOT 3D modeled characters. "
            "Characters are drawn as 2D painted illustrations with flat painted surfaces and brushwork shading — NOT as 3D objects. "
            "Vibrant warm colors, visible painterly brushwork, bright natural lighting, "
            "MAXIMUM LIKENESS: PRESERVE EXACT FACIAL FEATURES (eye shape, nose, mouth, face shape, eyebrows), "
            "EXACT HAIR COLOR, EXACT HAIRSTYLE (length, texture, parting), EXACT SKIN TONE, AND EXACT CLOTHING. "
            "Face must be instantly recognizable from reference photo. "
            "Natural child proportions, normal head size, small realistic eyes, "
            "NOT simplified face, NOT generic painted face, sharp focus, consistent character identity."
        ),
        cover_prefix="Wide environmental shot, full body. Vibrant digital painting adventure book cover featuring",
        cover_suffix="Colorful vibrant palette, textured backgrounds. Character 30% of frame, adventure environment 70%.",
        inner_prefix="Wide angle shot, full body visible. Richly detailed vibrant digital painting showing",
        inner_suffix=(
            "Warm natural lighting, detailed textures, painterly rendering, cheerful adventure mood, "
            "rich saturated colors. "
            + _INNER_COMPOSITION_SUFFIX
        ),
        negative=(
            f"text overlay, logo, letters on image, head rotated, "
            f"photorealistic, photo-realistic, realistic render, CGI, 3d render, 3d model, 3d character, "
            f"pixar style, disney 3d, cg animated, 3d animated film, 3d movie style, "
            f"anime, manga, "
            f"generic face, simplified face, generic painted face, altered facial features, different face, wrong face shape, "
            f"long neck, elongated neck, stretched neck, twisted neck, crooked neck, craned neck, "
            f"cross-eyed, wall-eyed, misaligned eyes, asymmetric gaze, off-axis eyes, lazy eye, "
            f"adult face, beard, mustache, ancient robe, toga, historical costume, period costume, "
            f"headscarf on child, hijab on child, veil on child, head covering on child, scarf on child head, "
            f"hood over child head, head wrap on child, "
            f"portrait, close-up, face filling frame, headshot, waist-up, cropped body, "
            f"{_COMPOSITION_NEG}, {_CONSISTENCY_NEG}"
        ),
        id_weight=1.2,
        start_step=0,
        true_cfg=1.2,
    ),
}


# ---------------------------------------------------------------------------
# Style resolution
# ---------------------------------------------------------------------------

def _normalize(text: str) -> str:
    """Türkçe karakterleri ASCII'ye çevirir, küçük harfe dönüştürür."""
    if not text:
        return ""
    t = text.lower().strip()
    for tr, ascii_ in (("ş", "s"), ("ı", "i"), ("ğ", "g"), ("ü", "u"), ("ö", "o"), ("ç", "c")):
        t = t.replace(tr, ascii_)
    return t


def _strip_negations(text: str) -> str:
    return re.sub(r"\b(?:NOT|not|No|no|WITHOUT|without|non)\s+[\w'-]+(?:\s+[\w'-]+)?", " ", text)


def _has(text: str, keyword: str) -> bool:
    return bool(re.search(r"\b" + re.escape(keyword) + r"\b", text, re.IGNORECASE))


def _has_any(text: str, keywords: list[str]) -> bool:
    return any(_has(text, kw) for kw in keywords)


_SOFT_PASTEL_KEYWORDS = [
    "soft pastel", "yumusak pastel", "pastel ruya", "cosy illustration", "warm pastel",
    "vintage", "retro", "golden books", "nostalgic",
]

_ANIME_KEYWORDS = ["ghibli", "cel-shading", "cel shading"]

_ADVENTURE_DIGITAL_KEYWORDS = [
    "adventure digital", "digital painting", "macera", "painterly", "earth tones",
    "game", "video game", "nintendo", "oyun",
]


def _detect_style_key(clean: str) -> str | None:
    """Normalize edilmiş metinden stil anahtarı döndürür. None = default fallback."""
    if _has_any(clean, _ANIME_KEYWORDS):
        return "anime"
    if _has(clean, "anime") and not _has_any(clean, _SOFT_PASTEL_KEYWORDS):
        return "anime"

    if _has_any(clean, ["pixar", "disney", "cizgi film", "superhero", "super kahraman", "dreamworks"]):
        return "pixar"
    if _has(clean, "cinematic") and _has_any(clean, ["3d", "cgi"]):
        return "pixar"

    if _has_any(clean, _SOFT_PASTEL_KEYWORDS):
        return "soft_pastel"
    if _has_any(clean, ["watercolor", "sulu boya", "suluboya", "watercolour"]):
        return "watercolor"
    if _has_any(clean, _ADVENTURE_DIGITAL_KEYWORDS):
        return "adventure_digital"

    if _has(clean, "2d"):
        return "default"
    if _has(clean, "3d") and not re.search(r"\b(?:not|no|non|without)\s+3d\b", clean, re.IGNORECASE):
        return "pixar"

    return None


def resolve_style(style_modifier: str) -> StyleConfig:
    """Stil modifier string'inden StyleConfig döndürür. Tek kaskad, tek kaynak."""
    if not style_modifier:
        return STYLES["default"]

    clean = _strip_negations(_normalize(style_modifier))

    _skip_default = (
        _ANIME_KEYWORDS + _ADVENTURE_DIGITAL_KEYWORDS + _SOFT_PASTEL_KEYWORDS
        + ["watercolor", "watercolour", "sulu boya", "suluboya", "anime"]
    )
    if (
        _has(clean, "2d")
        and _has_any(clean, ["children's book", "childrens book", "storybook", "picture-book", "picture book"])
        and not _has_any(clean, _skip_default)
    ):
        return STYLES["default"]

    key = _detect_style_key(clean)
    return STYLES[key or "default"]

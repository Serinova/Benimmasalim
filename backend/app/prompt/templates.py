"""Default prompt template'ları — DB yoksa fallback.

Admin panelinden düzenlenebilir versiyonlar DB'de saklanır.
Buradaki değerler sadece DB boşken kullanılır.
"""

from __future__ import annotations

# ── Hikaye yazım system prompt'u ─────────────────────────────────────────────
STORY_NO_FIRST_DEGREE_FAMILY_TR = (
    "🚫🚫🚫 EN ÖNCELİKLİ KURAL — AİLE YASAĞI 🚫🚫🚫\n"
    "Bu hikayede şu kelimeler KESİNLİKLE, HİÇBİR ŞEKİLDE GEÇMEYECEK:\n"
    "anne, annesi, annem, baba, babası, babam, kardeş, kardeşi, abla, ablası, "
    "abi, abisi, dede, dedesi, nine, ninesi, babaanne, anneanne, aile, ailesi, "
    "ebeveyn, ebeveynleri, anneciğim, babacığım, anası, babacık, annesinin, babasının.\n\n"
    "ÇOCUK MACERAYI TEK BAŞINA YAŞAMALI!\n"
    "Yardımcı karakter: hayvan arkadaş (tilki, güvercin, kedi vb.) VEYA "
    "yaşlı usta, bilge figür, peri gibi MENTOR karakterler.\n"
    "Hikayenin başlangıcında bile 'annesi söyledi', 'babası götürdü' gibi ifadeler YASAK!\n"
    "Çocuk macerayı kendi başına buluyor, keşfediyor, yaşıyor."
)

NO_FAMILY_BANNED_WORDS_TR = (
    "anne,baba,aile,kardeş,abla,abi,dede,nine,babaanne,anneanne,"
    "ebeveyn,annem,babam,anneciğim,babacığım"
)

def get_default_clothing(gender_en: str) -> str:
    """Return specific default clothing to ensure character consistency."""
    if gender_en.lower() == "boy":
        return "red t-shirt, blue denim overalls, and sneakers"
    return "yellow t-shirt, blue denim overalls, and pink sneakers"

def get_default_hair() -> str:
    """Return default hair to ensure character consistency."""
    return "natural hair"

# ── Görsel prompt template'ları ──────────────────────────────────────────────
DEFAULT_COVER_TEMPLATE = (
    # CHARACTER block comes FIRST — explicit age/gender/outfit before scene to prevent
    # the diffusion model from inventing a second child from the scene description.
    "An {child_age}-year-old {child_gender} named {child_name} with {hair_description}, "
    "wearing {clothing_description}. "
    "{scene_description}. "
    "BOOK TITLE: Render the EXACT text [{story_title}] as a beautifully integrated book title. "
    "PLACEMENT: Horizontally centered, confined strictly to the TOP 10% of the image — "
    "letters must NOT extend below the 10% line. "
    "SIZING: Proportional to the image width — title block width max 85% of image width, "
    "font size moderate (NOT oversized, NOT giant), split into 2 balanced lines if the text is long. "
    "STYLE: Hand-lettered storybook font, warm golden-amber gradient fill (bright gold center fading to deep amber at edges), "
    "thin dark-brown outline (1-2px), soft warm inner glow, subtle drop-shadow for gentle depth. "
    "The title should feel PAINTED INTO the scene — as if it belongs to the illustration, "
    "not stamped on top. Scatter 4-6 tiny golden stars around the title. "
    "STRICT RULE: Title must NEVER touch or overlap the child's head or body. "
    "Do NOT add any other text, subtitles, watermarks, or signatures anywhere in the image."
)

DEFAULT_BACK_COVER_TEMPLATE = (
    "An {child_age}-year-old {child_gender} named {child_name} with {hair_description}, "
    "wearing {clothing_description}. "
    "{scene_description}. "
    "BACK COVER: This is the back cover of the book — same world, same atmosphere, same character as the front cover. "
    "Show the character from a different angle (rear view, side view, or wide panorama) continuing the adventure. "
    "The scene should feel like a natural continuation of the front cover story. "
    "Full-bleed illustration, rich and detailed background. "
    "CRITICAL: NO TITLE on back cover. NO text, NO letters, NO words, NO book title, NO watermarks, NO signatures anywhere in the image. "
    "This is a pure illustration with zero text elements. "
)

DEFAULT_INNER_TEMPLATE = (
    # CHARACTER block first — prevents scene_description from introducing a conflicting character.
    "An {child_age}-year-old {child_gender} named {child_name} with {hair_description}, "
    "wearing {clothing_description}. "
    "{scene_description}. "
    "TEXT AREA RULE: The BOTTOM 25% of the image must have a softer, less detailed, or lighter background "
    "(sky, mist, open ground, blurred foliage) so that overlaid story text remains readable. "
    "Place the main action and the child in the UPPER 75% of the frame. "
    "Do NOT include ANY text, letters, words, or watermarks. "
)

# ── Kompozisyon kuralları ────────────────────────────────────────────────────
COMPOSITION_RULES = (
    "CRITICAL COMPOSITION — STRICT RULES: "
    "Wide environmental shot ONLY, child occupies 25-30% of frame maximum, rich detailed environment fills 70-75%. "
    "Full body MUST be visible from head to feet, INCLUDING BOTH LEGS AND FEET. "
    "NEVER crop child's legs, NEVER waist-up framing, NEVER close-up on face. "
    "Camera positioned at child's eye-level or slightly above, maintaining natural distance. "
    "Child is part of the scene, NOT the sole focus. "
    "BOTTOM 25% TEXT SAFE ZONE: Keep the bottom quarter of the image relatively open, soft, or low-contrast "
    "(e.g. ground, sky gradient, mist, gentle terrain) — story text will be overlaid here. "
    "IDENTICAL CHARACTER LOCK: Same clothing, same hairstyle, same skin tone, same proportions on EVERY page."
)

BODY_PROPORTION = (
    "Child in frame, natural realistic proportions, no chibi, no caricature. "
    "Small naturally proportioned eyes."
)
SHARPNESS = "Sharp focus entire scene, no blur, detailed background."

# ── Yüz referansı ───────────────────────────────────────────────────────────
LIKENESS_HINT = (
    "CRITICAL LIKENESS LOCK: Create a stylized illustration of the child from the reference photo. "
    "PRESERVE EXACTLY: the child's unique facial structure (face shape, eye shape, nose shape, mouth shape), "
    "EXACT hair color, EXACT hairstyle (length, texture, style), EXACT skin tone. "
    "The face MUST be instantly recognizable as the SAME child from the reference photo on EVERY page. "
    "Maintain strong facial similarity while keeping the 2D children's book illustration style. "
    "DO NOT simplify or genericize facial features — keep the child's distinctive characteristics. "
    "The illustration style applies to the background and rendering technique, NOT to the facial identity."
)

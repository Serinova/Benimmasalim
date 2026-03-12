"""Prompt temizleme: cinematic terim silme, TR→EN çeviri, güvenli kesme.

Tüm temizleme tek geçişte yapılır — sıralama garantili.
"""

from __future__ import annotations

import re

import structlog

logger = structlog.get_logger()

# ── Max lengths ──────────────────────────────────────────────────────────────
MAX_PROMPT_CHARS = 2048
MAX_BODY_CHARS = 720

# ── Cinematic / lens terimleri ───────────────────────────────────────────────
_CINEMATIC_TERMS: list[str] = [
    r"\bwide-angle\s+cinematic\s+shot\b",
    r"\bwide\s+angle\s+cinematic\s+shot\b",
    r"\bcinematic\b",
    r"\bwide-angle\b",
    r"\bextreme\s+wide\s+shot\b",
    r"\bf/8\b", r"\bf\/8\b",
    r"\blens\b", r"\bfilm still\b",
    r"\bheroically\b", r"\bheroic\b",
    r"\bepic\s+landscape\b", r"\bepic\s+composition\b",
    r"\bepic\s+background\b", r"\bepic\s+environment\b",
    r"\bepic\s+wide\s+shot\b", r"\bepic\s+wide\b",
    r"\bconcept\s+art\b",
    r"\bvolumetric\s+lighting\b", r"\bvolumetric\s+light\b",
    r"\bgod\s+rays\b",
    r"\bdramatic\s+lighting\b", r"\bdramatic\s+contrast\b",
    r"\bmovie\s+poster\b", r"\bposter\s+quality\b",
    r"\bDSLR\b", r"\bbokeh\b", r"\blens\s+flare\b",
    r"\bprofessional\s+photo\b", r"\bphotography\b", r"\bphotograph\b",
]
_CINEMATIC_RE = re.compile("|".join(f"({p})" for p in _CINEMATIC_TERMS), re.IGNORECASE)

_INNER_STRIP_TERMS = [
    r"\bChildren's\s+book\s+cover\b",
    r"\bchildren's\s+book\s+cover\b",
    r"\bbook\s+cover\s+illustration\b",
]
_INNER_STRIP_RE = re.compile("|".join(f"({p})" for p in _INNER_STRIP_TERMS), re.IGNORECASE)

# Duplicate character opener — Gemini sometimes starts scene_description with
# "A young girl/boy/child wearing [outfit]. [Name]..." which conflicts with the
# template's own character block. Strip these openers so the template block wins.
# Pattern covers: "A young child wearing X. Name..." or "A young boy with hair, wearing X. Name..."
_DUPLICATE_CHAR_OPENER_RE = re.compile(
    r"^A\s+young\s+(?:girl|boy|child)"
    r"(?:\s+with\s+[^,\.]+(?:hair|locks|curls)[^,\.]*,?)?"
    r"(?:\s+wearing\s+[^\.]+\.)?"
    r"\s*",
    re.IGNORECASE,
)

# ── TR → EN kıyafet çevirisi ────────────────────────────────────────────────
_COLOR_TR_EN: dict[str, str] = {
    "kırmızı": "red", "kirmizi": "red", "mavi": "blue",
    "yeşil": "green", "yesil": "green", "sarı": "yellow", "sari": "yellow",
    "beyaz": "white", "siyah": "black", "gri": "gray", "pembe": "pink",
    "mor": "purple", "turuncu": "orange", "lacivert": "navy blue",
    "kahverengi": "brown", "bordo": "burgundy", "turkuaz": "turquoise",
    "lila": "lilac", "bej": "beige", "haki": "khaki",
    "koyu": "dark", "açık": "light", "acik": "light",
    "renkli": "colorful", "çiçekli": "floral", "cicekli": "floral",
    "kareli": "plaid", "çizgili": "striped", "cizgili": "striped",
}
_GARMENT_TR_EN: dict[str, str] = {
    "tişört": "t-shirt", "tisort": "t-shirt", "tishort": "t-shirt",
    "tshirt": "t-shirt", "t shirt": "t-shirt",
    "gömlek": "shirt", "gomlek": "shirt", "kazak": "sweater",
    "mont": "jacket", "ceket": "jacket", "yelek": "vest",
    "hırka": "cardigan", "hirka": "cardigan",
    "sweatshirt": "sweatshirt", "polar": "fleece jacket",
    "kapüşonlu": "hooded", "kapusonlu": "hooded",
    "pantolon": "pants", "şort": "shorts", "sort": "shorts",
    "etek": "skirt", "tayt": "leggings",
    "kot pantolon": "jeans", "kot": "jeans", "jean": "jeans", "jeans": "jeans",
    "spor ayakkabısı": "sneakers", "spor ayakkabisi": "sneakers",
    "spor ayakkabı": "sneakers", "spor ayakkabi": "sneakers",
    "ayakkabı": "shoes", "ayakkabi": "shoes",
    "bot": "boots", "çizme": "boots", "cizme": "boots",
    "sandalet": "sandals", "terlik": "slippers",
    "şapka": "hat", "sapka": "hat", "bere": "beanie",
    "atkı": "scarf", "atki": "scarf", "eldiven": "gloves",
    "sırt çantası": "backpack", "sirt cantasi": "backpack",
    "elbise": "dress", "tulum": "jumpsuit", "pijama": "pajamas",
}

_CLOTHING_TR_EN: list[tuple[str, str]] = sorted(
    list(_COLOR_TR_EN.items()) + list(_GARMENT_TR_EN.items()),
    key=lambda x: len(x[0]),
    reverse=True,
)
_CLOTHING_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"\b" + re.escape(tr) + r"\b", re.IGNORECASE), en)
    for tr, en in _CLOTHING_TR_EN
]


def normalize_clothing(raw: str) -> str:
    """Kıyafet tanımını TR'den EN'e çevirir, temizler."""
    text = (raw or "").strip()
    if not text:
        return ""
    for pattern, en in _CLOTHING_PATTERNS:
        text = pattern.sub(en, text)
    text = re.sub(r"\s{2,}", " ", text)
    text = re.sub(r"\s*,\s*", ", ", text)
    return text.strip().rstrip(".")


_LOCATION_TR_EN: list[tuple[str, str]] = [
    (r"Yerebatan\s+Sarn[ıi]c[ıi]", "Basilica Cistern"),
    (r"Kapadokya", "Cappadocia"),
    (r"Göreme", "Goreme"),
    (r"Göbeklitepe", "Gobekli Tepe"),
    (r"Efes\s+Antik\s+Kent", "Ancient City of Ephesus"),
    (r"\bEfes\b", "Ephesus"),
    (r"Celsus\s+K[üu]t[üu]phanesi", "Library of Celsus"),
    (r"Ayasofya", "Hagia Sophia"),
    (r"Sultanahmet\s+Meydan[ıi]", "Sultanahmet Square"),
    (r"Sultanahmet\s+Camii", "Blue Mosque"),
    (r"Galata\s+K[öo]pr[üu]s[üu]", "Galata Bridge"),
    (r"Galata\s+Kulesi", "Galata Tower"),
    (r"\bHali[çc]\b", "Golden Horn"),
    (r"S[üu]mela\s+Manast[ıi]r[ıi]", "Sumela Monastery"),
    (r"\bS[üu]mela\b", "Sumela"),
    (r"Alt[ıi]ndere\s+Vadisi", "Altindere Valley"),
    (r"Karada[ğg]", "Karadag Mountain"),
    (r"Çatalhöyük\s+Neolitik\s+Kenti", "Catalhoyuk Neolithic Settlement"),
    (r"Çatalhöyük", "Catalhoyuk"),
    (r"Neolitik\s+Kent", "Neolithic Settlement"),
    (r"Kud[üu]s\s+Eski\s+[Şş]ehir", "Old City of Jerusalem"),
    (r"\bKud[üu]s\b", "Jerusalem"),
    (r"Kud[üu]s\s+Ta[şs][ıi]", "Jerusalem stone"),
    (r"Abu\s+Simbel\s+Tap[ıi]naklar[ıi]", "Abu Simbel Temples"),
    (r"Nasser\s+G[öo]l[üu]", "Lake Nasser"),
    (r"Nubya\s+[Çç][öo]l[üu]", "Nubian Desert"),
    (r"\bII\.\s*Ramses\b", "Ramesses II"),
    (r"Tac\s+Mahal", "Taj Mahal"),
    (r"Yamuna\s+Nehri", "Yamuna River"),
]


def normalize_location(prompt: str) -> str:
    """TR lokasyon adlarını EN karşılıklarına çevirir."""
    if not prompt:
        return prompt
    s = prompt
    for pattern, en in _LOCATION_TR_EN:
        s = re.sub(r"\b" + pattern + r"\b", en, s, flags=re.IGNORECASE)
    return s


def truncate_safe(text: str, max_length: int = MAX_BODY_CHARS) -> str:
    """2D-safe truncation: cümle sınırında keser, '2D'yi bölmez."""
    if not text or len(text) <= max_length:
        return text
    s = text.strip()

    zone_start = max(0, max_length - 100)
    search_zone = s[zone_start:max_length]
    last_clause = max(search_zone.rfind(", "), search_zone.rfind(". "))
    if last_clause > 0:
        cut_point = zone_start + last_clause + 2
        return s[:cut_point].rstrip(" ,.")

    cut = s[:max_length + 1].rsplit(" ", 1)[0] if " " in s[:max_length + 1] else s[:max_length]
    rest = s[len(cut):].lstrip()
    if cut.endswith("2") and rest.lower().startswith("d"):
        cut = cut + rest[0]
    return cut


def sanitize(prompt: str, *, is_cover: bool = False, max_length: int | None = None) -> str:
    """Tek geçişte prompt temizleme: lokasyon, cinematic terimler, kesme."""
    if max_length is None:
        max_length = MAX_BODY_CHARS
    if not prompt or not prompt.strip():
        return prompt

    s = prompt.strip()
    s = normalize_location(s)

    s = re.sub(
        r"\bwide eyes\b",
        "eyes opened in amazement (small, narrow, realistic)",
        s, flags=re.IGNORECASE,
    )

    s = _CINEMATIC_RE.sub(" ", s)

    if not is_cover:
        s = _INNER_STRIP_RE.sub(" ", s)

    # Remove duplicate character opener — "A young girl/boy with..." at start of
    # scene_description conflicts with the template's own character block and causes
    # diffusion models to render a second child.
    s = _DUPLICATE_CHAR_OPENER_RE.sub("", s).strip()

    s = re.sub(r"\s+", " ", s).strip()
    s = re.sub(r"\s*,\s*,\s*", ", ", s)
    s = s.strip(" ,")

    if len(s) > max_length:
        s = truncate_safe(s, max_length)

    return s

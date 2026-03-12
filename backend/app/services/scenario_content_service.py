"""Scenario content service: generate child-friendly intro text for scenario locations."""

from __future__ import annotations

import httpx
import structlog

from app.config import settings

logger = structlog.get_logger()


_PROMPT_LEAK_KEYWORDS = (
    "iconic elements",
    "include 1-2",
    "scene description",
    "silhouette",
    "visual prompt",
    "clothing_description",
    "child_description",
    "{",
    "dome cascade",
    "iznik tiles",
    "minaret",
)

# Placeholder / kod sızması — karşılama sayfasında asla görünmemeli
_INTRO_PLACEHOLDER_LEAK = (
    "[çocuk adı]",
    "[cocuk adi]",
    "kitap adı:",
    "kitap adi:",
)

# Senaryo description tarzı metin (özet liste, "Kafile ile... Kitap adı:" vb.) — tagline olarak kullanılmamalı
_DESCRIPTION_STYLE_LEAK = (
    "kafile ile",
    "kabe ilk",
    "tavaf",
    "sa'y",
    "mescid-i nebevi",
    "uhud",
    "hendek.",
)


def _looks_like_prompt(text: str) -> bool:
    """Return True if text appears to be a visual-prompt fragment or scenario description, not user-facing copy."""
    if not (text or "").strip():
        return True
    lower = text.lower()
    if any(kw.lower() in lower for kw in _PROMPT_LEAK_KEYWORDS):
        return True
    if any(leak in lower for leak in _INTRO_PLACEHOLDER_LEAK):
        return True
    # Senaryo description benzeri (virgülle ayrılmış özet) — karşılama sayfasında kullanma
    return bool(any(d in lower for d in _DESCRIPTION_STYLE_LEAK))


async def generate_scenario_intro_text(
    *,
    scenario: object | None,
    child_name: str,
    story_title: str,
) -> str | None:
    """Generate a child-friendly intro paragraph about the scenario location.

    Strategy:
    1. scenario.tagline  — short, clean Turkish marketing copy
    2. Gemini — generated from scenario.name (safe; no prompt fragments)

    NOTE: scenario.description and location_en are intentionally skipped
    because they contain visual-prompt fragments that would leak into the text.

    Returns:
        Intro text (max 500 chars) or None.
    """
    if scenario is None:
        return None

    # 1. Use tagline only if clean; never use scenario.description (often contains "Kitap adı: [Çocuk adı]")
    desc_raw = getattr(scenario, "description", None) or ""
    tagline = getattr(scenario, "tagline", None)
    if tagline and len(tagline.strip()) > 10 and not _looks_like_prompt(tagline):
        tagline_clean = tagline.strip()[:500]
        # Tagline description ile aynı/benzer olmasın (DB'de yanlış set edilmiş olabilir)
        if desc_raw and tagline_clean in desc_raw:
            return None
        return tagline_clean

    # 2. Gemini — use scenario.name (Turkish, always clean) as location reference
    scenario_name: str | None = getattr(scenario, "name", None)
    if not scenario_name:
        return None

    api_key = settings.gemini_api_key
    if not api_key:
        return None

    prompt = (
        f"'{story_title}' adlı kitabın karşılama sayfası için 2-4 cümlelik edebi bir tanıtım paragrafı yaz. "
        f"Konu: '{scenario_name}'. "
        f"Metinde kitabın içeriğini tanıt: Bu yolculukta okuyucu neler görecek, neler keşfedecek? "
        f"Çocuk dostu, akıcı ve merak uyandıran bir dil kullan. "
        f"Türkçe yaz. Sadece düz metin — başlık, madde işareti, parantez içi açıklama veya '[Çocuk adı]' gibi placeholder EKLEME."
    )

    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"gemini-2.5-flash:generateContent?key={api_key}"
    )
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.7, "maxOutputTokens": 200},
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
            result = resp.json()
        text: str = result["candidates"][0]["content"]["parts"][0]["text"].strip()
        # Final safety check — refuse to return if prompt leaked anyway
        if not text or _looks_like_prompt(text):
            logger.warning(
                "Gemini intro text contained prompt fragments — discarded",
                scenario=scenario_name,
            )
            return None
        return text[:500]
    except Exception as e:
        logger.warning("Gemini scenario intro text failed", error=str(e))
        return None

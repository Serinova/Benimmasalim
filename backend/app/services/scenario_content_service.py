"""Scenario content service: generate child-friendly intro text for scenario locations."""

from __future__ import annotations

import httpx
import structlog

from app.config import settings

logger = structlog.get_logger()


async def generate_scenario_intro_text(
    *,
    scenario: object | None,
    child_name: str,
    story_title: str,
) -> str | None:
    """Generate a child-friendly intro paragraph about the scenario location.

    Priority:
    1. scenario.description (if available and meaningful)
    2. scenario_bible.cultural_facts
    3. Gemini fallback — short child-friendly intro

    Returns:
        Intro text (max 500 chars) or None.
    """
    if scenario is None:
        return None

    # 1. Use scenario.description if available and meaningful
    description = getattr(scenario, "description", None)
    if description and len(description) > 20:
        return description[:500]

    # 2. Use scenario_bible cultural_facts
    scenario_bible = getattr(scenario, "scenario_bible", None)
    if scenario_bible:
        facts = scenario_bible.get("cultural_facts", [])
        if facts:
            return " ".join(str(f) for f in facts[:2])

    # 3. Gemini fallback
    location = getattr(scenario, "location_en", None) or getattr(scenario, "name", None)
    if not location:
        return None

    api_key = settings.gemini_api_key
    if not api_key:
        return None

    prompt = (
        f"'{story_title}' adlı çocuk kitabı için '{location}' hakkında "
        f"2-3 cümlelik, çocuk dostu, eğitici ve büyülü bir giriş paragrafı yaz. "
        f"Türkçe yaz. Sadece paragrafı yaz, başlık veya açıklama ekleme."
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
        return text[:500] if text else None
    except Exception as e:
        logger.warning("Gemini scenario intro text failed", error=str(e))
        return None

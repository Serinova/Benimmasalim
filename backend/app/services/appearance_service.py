"""Appearance detection service: clothing and hair from child photo via Gemini Vision."""

from __future__ import annotations

import base64

import httpx
import structlog

from app.config import settings

logger = structlog.get_logger()


async def detect_clothing_from_photo(photo_url: str, gender: str) -> str:
    """Detect clothing description from child's photo using Gemini Vision.

    Critical for outfit consistency across all book pages.
    PuLID handles face; clothing must be described in text for cross-page lock.

    Returns:
        Clothing description e.g. "a red striped t-shirt and blue shorts"
    """
    try:
        async with httpx.AsyncClient(timeout=45.0) as client:
            response = await client.get(photo_url)
            response.raise_for_status()
            image_bytes = response.content

        base64_data = base64.b64encode(image_bytes).decode("utf-8")

        api_key = settings.gemini_api_key
        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"gemini-2.5-flash:generateContent?key={api_key}"
        )

        payload = {
            "contents": [
                {
                    "parts": [
                        {"inlineData": {"mimeType": "image/jpeg", "data": base64_data}},
                        {
                            "text": """Analyze this child's photo and describe ONLY their clothing.

RULES:
- Describe what the child is WEARING (not face, not background)
- Be specific about colors and patterns
- Keep it concise (one phrase)

FORMAT: Respond with ONLY a clothing description that can complete:
"a child wearing ___"

EXAMPLES:
- "a bright red striped t-shirt and blue denim shorts"
- "a pink princess dress with sparkly details"
- "a yellow hoodie and gray sweatpants"

Just the clothing description, nothing else."""
                        },
                    ]
                }
            ],
            "generationConfig": {
                "temperature": 0.1,
                "maxOutputTokens": 100,
            },
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            result = response.json()

        clothing: str = result["candidates"][0]["content"]["parts"][0]["text"].strip()
        clothing = clothing.replace('"', "").replace("'", "")
        if clothing.lower().startswith("a child wearing "):
            clothing = clothing[16:]
        elif clothing.lower().startswith("wearing "):
            clothing = clothing[8:]

        logger.info("Clothing detected from photo", clothing=clothing[:50])
        return clothing

    except Exception as e:
        logger.warning("Clothing detection failed", error=str(e))
        from app.prompt.templates import get_default_clothing

        return get_default_clothing("boy" if gender == "erkek" else "girl")


async def detect_hair_from_photo(photo_url: str, gender: str) -> str:  # noqa: ARG001
    """Detect hair style from child's photo for character consistency.

    Returns:
        Short English phrase e.g. "long curly dark brown hair"
    """
    try:
        async with httpx.AsyncClient(timeout=45.0) as client:
            response = await client.get(photo_url)
            response.raise_for_status()
            image_bytes = response.content

        base64_data = base64.b64encode(image_bytes).decode("utf-8")

        api_key = settings.gemini_api_key
        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"gemini-2.5-flash:generateContent?key={api_key}"
        )

        payload = {
            "contents": [
                {
                    "parts": [
                        {"inlineData": {"mimeType": "image/jpeg", "data": base64_data}},
                        {
                            "text": """Analyze this child's photo and describe ONLY their hair with maximum precision.

RULES:
- Describe hair LENGTH: very short (above ears), short (ear-length), medium (chin to shoulder), long (below shoulder), very long
- Describe hair TEXTURE: pin-straight, straight, slightly wavy, wavy, curly, coily
- Describe hair COLOR with exact shade: jet black, dark brown, medium brown, warm brown, light brown, dark blonde, golden blonde, light blonde, strawberry blonde, auburn, red, etc.
- Describe bangs/fringe if present: thick straight bangs, side-swept bangs, no bangs
- Describe parting if visible: center part, side part, no visible part
- Keep it to ONE descriptive phrase, max 12 words

FORMAT: Respond with ONLY a hair description like:
"short straight dark brown hair with thick straight bangs"
"long wavy light brown hair, center part, no bangs"
"medium curly black hair, no bangs"

Just the hair description, nothing else."""
                        },
                    ]
                }
            ],
            "generationConfig": {
                "temperature": 0.1,
                "maxOutputTokens": 80,
            },
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            result = response.json()

        hair: str = result["candidates"][0]["content"]["parts"][0]["text"].strip()
        hair = hair.replace('"', "").replace("'", "").lower()
        if not hair.endswith("hair"):
            hair = hair + " hair"

        logger.info("Hair detected from photo", hair=hair[:50])
        return hair

    except Exception as e:
        logger.warning("Hair detection failed, using default", error=str(e))
        from app.prompt.templates import get_default_hair

        return get_default_hair()

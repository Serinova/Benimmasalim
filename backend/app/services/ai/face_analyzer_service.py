"""
Face Analyzer Service - Forensic-level facial description generation.

Uses Gemini Pro Vision to analyze uploaded photos and generate extremely detailed
text-based portrait descriptions for maximizing facial resemblance in AI image generation.

Features:
- Single image analysis with forensic-level detail
- Multi-view analysis for improved accuracy (combines multiple photos)
- Gemini 2.0 Flash for fast, accurate multimodal analysis
"""

import base64
import io

import httpx
import structlog
from PIL import Image

from app.config import settings
from app.core.rate_limit import rate_limit_retry

logger = structlog.get_logger()

# Best Gemini model for multimodal analysis
GEMINI_MULTIMODAL_MODEL = "gemini-2.5-flash"


        # Forensic Analysis System Prompt
FORENSIC_ANALYSIS_PROMPT = """You are an expert portrait artist and forensic facial analyst. Analyze this photograph and produce a PRECISE facial description so another artist can recreate this exact face.

## THE THREE MOST IMPORTANT FEATURES (describe these FIRST and with maximum detail):

### 1. HAIR (MOST CRITICAL — parents recognize their child by hairstyle)
- EXACT style: bowl-cut? side-swept? layered? cropped?
- Bangs/fringe: thick straight bangs? side-swept bangs? no bangs? How far do they cover the forehead?
- Parting: center part? side part? no visible part?
- Length: above ears? covering ears? to shoulders?
- Texture: pin-straight? wavy? curly?
- Color with undertones (e.g., "dark brown with slight warm undertones")
- Thickness/density and how it frames the face

### 2. SKIN TONE (CRITICAL — must be preserved exactly in illustrations)
- Be extremely specific: "light fair ivory skin", "warm golden-olive", "medium tan with warm undertones"
- Rosy cheeks, flush areas, freckles
- Overall complexion warmth (cool, warm, neutral)

### 3. FACE SHAPE & STRUCTURE
- Overall shape (oval, round, square, heart)
- Jawline, chin, cheekbone prominence
- Forehead height

### 4. EYES (describe accurately but NEVER use "large" or "big")
- Shape (almond, round, hooded, monolid) — use "small" or "narrow" if appropriate
- Color with variations
- Distance between eyes, eyelid characteristics
- Eyebrow shape and color

### 5. NOSE & MOUTH
- Nose bridge, tip, nostril shape
- Lip shape, fullness, philtrum

### 6. DISTINCTIVE FEATURES
- Dimples, moles, birthmarks, asymmetries

## Output Format

Return a SINGLE DENSE PARAGRAPH. Begin with "The face features " and then describe hair, skin tone, face shape, eyes, nose, and mouth in order.
Focus on exact physical details that are necessary to draw this exact face. DO NOT use generic positive adjectives (cute, beautiful, nice).

CRITICAL RULES:
- NEVER describe eyes as "large", "big", or "wide" — this is STRICTLY FORBIDDEN as it ruins the likeness in children's illustrations. Always use "small", "narrow", or neutral terms.
- HAIR description must be detailed enough to recreate the exact hairstyle
- SKIN TONE must be specific enough to match exactly

DO NOT include: name, beauty judgments, emotional interpretations, age guesses."""


        # Multi-view analysis prompt - for combining multiple photos
MULTI_VIEW_ANALYSIS_PROMPT = """You are an expert portrait artist analyzing MULTIPLE photographs of the SAME child to create the most accurate description possible.

## Your Task
Analyze ALL images together. Focus on CONSISTENT features — these are the TRUE characteristics.

## Focus Areas (in order of importance — parents recognize their child by these):
1. **HAIRSTYLE** (MOST CRITICAL) — Exact length, texture, bangs/fringe style, parting, color. Describe precisely enough to recreate.
2. **SKIN TONE** (CRITICAL) — Exact complexion: "light fair", "warm olive", "golden-tan", etc.
3. **FACE SHAPE** — Overall geometry, jawline, cheekbones
4. **EYES** — Shape and color. NEVER describe as "large" or "big" — use "small", "narrow", or neutral terms.
5. **NOSE & MOUTH** — Bridge, tip, lip shape
6. **UNIQUE FEATURES** — Dimples, freckles, moles, birthmarks

## Output Format
Return a SINGLE DENSE PARAGRAPH. Begin with "The face features " and then describe hairstyle, skin tone, and face shape in order.

CRITICAL RULES:
- NEVER describe eyes as "large", "big", or "wide" — this causes AI to exaggerate eye size in illustrations. STRICTLY FORBIDDEN.
- Be SPECIFIC and CONCRETE. This description will recreate this exact face in illustrations."""


class FaceAnalyzerService:
    """
    Service for generating detailed forensic-level facial descriptions
    using Gemini Pro Vision multimodal model.
    """

    def __init__(self):
        self.api_key = settings.gemini_api_key
        # Use Gemini 2.5 Flash for best multimodal reasoning
        self.model = "gemini-2.5-flash"
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"
        self.timeout = 30.0
        
        # Connection pooling
        self._http_limits = httpx.Limits(
            max_connections=100,
            max_keepalive_connections=20,
            keepalive_expiry=60,
        )

    async def _load_image_as_base64(self, image_source: str | bytes) -> tuple[str, str]:
        """
        Load image from URL or bytes and convert to base64.

        Args:
            image_source: Either a URL string or raw image bytes

        Returns:
            Tuple of (base64_data, mime_type)
        """
        if isinstance(image_source, bytes):
            # Direct bytes input
            image_bytes = image_source
        elif image_source.startswith(("http://", "https://")):
            # Download from URL
            async with httpx.AsyncClient(timeout=15.0, limits=self._http_limits) as client:
                response = await client.get(image_source)
                response.raise_for_status()
                image_bytes = response.content
        else:
            # Assume it's already base64
            return image_source, "image/jpeg"

        # Detect mime type and validate
        image = Image.open(io.BytesIO(image_bytes))
        mime_type = f"image/{image.format.lower()}" if image.format else "image/jpeg"

        # Convert to base64
        base64_data = base64.b64encode(image_bytes).decode("utf-8")

        return base64_data, mime_type

    @rate_limit_retry(service="gemini", max_attempts=3, timeout_attempts=3)
    async def analyze_face(
        self,
        image_source: str | bytes,
        child_age: int | None = None,
        child_gender: str | None = None,
    ) -> str:
        """
        Analyze a face image and generate a detailed forensic description.

        Args:
            image_source: Image URL or raw bytes
            child_age: Optional age for context (not included in description)
            child_gender: Optional gender for pronoun context ("erkek", "kiz")

        Returns:
            Detailed facial description string optimized for AI image generation

        Raises:
            httpx.HTTPStatusError: If API call fails
            ValueError: If image cannot be processed
        """
        logger.info("Starting forensic face analysis", has_age=child_age is not None)

        # Load and encode image
        base64_data, mime_type = await self._load_image_as_base64(image_source)

        # Build context hint
        context_hints = []
        if child_age:
            context_hints.append(f"This is a {child_age}-year-old child")
        # Gender context only for Gemini analysis accuracy — not used in output
        if child_gender:
            context_hints.append(f"Gender: {child_gender}")

        context_prefix = ". ".join(context_hints) + ".\n\n" if context_hints else ""

        # Construct the request
        url = f"{self.base_url}/models/{self.model}:generateContent?key={self.api_key}"

        payload = {
            "contents": [
                {
                    "parts": [
                        {"inlineData": {"mimeType": mime_type, "data": base64_data}},
                        {"text": context_prefix + FORENSIC_ANALYSIS_PROMPT},
                    ]
                }
            ],
            "generationConfig": {
                "temperature": 0.2,  # Low temperature for factual analysis
                "topP": 0.8,
                "maxOutputTokens": 4096,  # Increased to accommodate gemini-2.5-flash reasoning tokens
            },
            "safetySettings": [
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
            ],
        }

        async with httpx.AsyncClient(timeout=self.timeout, limits=self._http_limits) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            result = response.json()

        # Extract the description
        try:
            description = result["candidates"][0]["content"]["parts"][0]["text"]
            description = description.strip()

            logger.info(
                "Face analysis complete",
                description_length=len(description),
                word_count=len(description.split()),
            )

            return description

        except (KeyError, IndexError) as e:
            logger.error("Failed to parse face analysis response", error=str(e), response=result)
            raise ValueError("Failed to generate face description from image")

    async def get_enhanced_child_description(
        self,
        image_source: str | bytes,
        child_name: str,
        child_age: int,
        child_gender: str | None = None,
    ) -> str:
        """
        Generate a complete, enhanced child description combining forensic
        face analysis with basic child info.

        This is the main entry point for the image generation pipeline.

        Args:
            image_source: Child's photo URL or bytes
            child_name: Child's name
            child_age: Child's age
            child_gender: Optional gender ("erkek", "kiz")

        Returns:
            Complete description string ready for image generation prompts

        Example output:
            "A 5-year-old boy named Ali with a rounded face, distinct almond-shaped
            hazel eyes with slight epicanthic folds, a small button nose with a
            scattering of freckles across the bridge, and tousled wavy light-brown
            hair parted on the left. He has a shy, closed-mouth smile showing deep dimples."
        """
        # Get the forensic face description
        face_description = await self.analyze_face(
            image_source=image_source,
            child_age=child_age,
            child_gender=child_gender,
        )

        # Build the enhanced description — use "child" to let PuLID handle gender
        enhanced_description = (
            f"A {child_age}-year-old child named {child_name} with {face_description}"
        )

        logger.info(
            "Enhanced child description generated",
            child_name=child_name,
            total_length=len(enhanced_description),
        )

        return enhanced_description

    @rate_limit_retry(service="gemini", max_attempts=2, timeout_attempts=2)
    async def analyze_for_ai_director(
        self,
        image_source: str | bytes,
        child_name: str,
        child_age: int,
        child_gender: str | None = None,
    ) -> str:
        """
        Generate a CONCISE character description for AI-Director prompts.

        This is optimized for the "Double Locking" approach:
        - Short enough to include in every page prompt
        - Detailed enough to match PuLID face reference
        - Focus on: hair, eyes, skin tone, distinctive features

        Args:
            image_source: Child's photo URL or bytes
            child_name: Child's name
            child_age: Child's age
            child_gender: Gender ("erkek", "kiz")

        Returns:
            Concise description (30-50 words) like:
            "a 9-year-old boy named Uras with short curly black hair,
             warm brown eyes, golden-tan skin, and a cheerful round face"
        """
        logger.info("Starting AI-Director character analysis", child_name=child_name)

        # Load and encode image
        base64_data, mime_type = await self._load_image_as_base64(image_source)

        # Use "child" instead of "boy/girl" to prevent diffusion model from
        # overriding PuLID face reference with a generic gendered archetype.

        # Concise analysis prompt for AI-Director + iconic anchors
        analysis_prompt = f"""Analyze this child's photo and generate a PRECISE visual description. The THREE MOST IMPORTANT things to describe are HAIRSTYLE, SKIN TONE, and FACE SHAPE — these are what make parents recognize their child.

CHILD INFO:
- Name: {child_name}
- Age: {child_age}

YOUR TASK:
Create a SHORT but EXTREMELY SPECIFIC description (30-50 words) in this priority order:
1. HAIRSTYLE (MOST CRITICAL) — Describe with forensic precision: exact length (short/medium/long), texture (straight/wavy/curly), color, bangs/fringe (thick straight bangs? side-swept? no bangs?), parting (center/side/none), how hair falls around face. Example: "straight dark brown bowl-cut hair with thick blunt bangs covering entire forehead, no parting"
2. SKIN TONE (CRITICAL) — Be very specific: "light fair skin", "warm olive skin", "golden-tan complexion", "medium brown skin with rosy cheeks"
3. FACE SHAPE — round, oval, heart-shaped, etc. Include jawline and cheekbone details
4. Eye color and shape (keep eyes small and natural — do NOT describe as "large" or "big")
5. Other distinctive features (dimples, freckles, button nose, etc.)

CRITICAL RULES:
- NEVER describe eyes as "large", "big", or "wide" — always use "small", "narrow", or just the color/shape
- HAIRSTYLE must be precise enough that an artist could recreate it exactly
- SKIN TONE must be specific enough to match the photo exactly

OUTPUT FORMAT:
Return the description string FOLLOWED BY iconic anchors separated by a pipe character.
Iconic anchors are the 2-3 SINGLE MOST DISTINCTIVE visual features that make this child instantly recognizable even in a stylized illustration. Each anchor must be 2-5 words, extremely specific.

Format:
"a {child_age}-year-old child named {child_name} with [EXACT HAIRSTYLE], [SKIN TONE], [FACE SHAPE], [small eyes color], and [distinctive features] | ANCHORS: [anchor1], [anchor2], [anchor3]"

EXAMPLE OUTPUT:
"a 4-year-old child named Enes with straight dark brown bowl-cut hair with thick blunt bangs covering forehead, light fair skin with rosy cheeks, round soft face, small dark brown eyes, and a button nose | ANCHORS: thick blunt bangs covering forehead, rosy fair skin, round soft face"

Good anchor examples: "thick blunt bangs", "round red glasses", "prominent dimples", "gap-toothed smile", "curly auburn bob", "golden-tan skin"
Bad anchors (too generic): "brown hair", "nice smile", "cute face"

This description MUST match the photo so accurately that AI-generated illustrations preserve the child's exact look!"""

        # Construct the request
        url = f"{self.base_url}/models/{self.model}:generateContent?key={self.api_key}"

        payload = {
            "contents": [
                {
                    "parts": [
                        {"inlineData": {"mimeType": mime_type, "data": base64_data}},
                        {"text": analysis_prompt},
                    ]
                }
            ],
            "generationConfig": {
                "temperature": 0.3,  # Low for factual accuracy
                "topP": 0.8,
                "maxOutputTokens": 2048,  # Increased to accommodate gemini-2.5-flash reasoning tokens
            },
            "safetySettings": [
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
            ],
        }

        async with httpx.AsyncClient(timeout=self.timeout, limits=self._http_limits) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            result = response.json()

        try:
            description = result["candidates"][0]["content"]["parts"][0]["text"]
            description = description.strip().strip('"').strip("'")

            # Ensure it starts correctly
            if not description.lower().startswith("a "):
                description = f"a {child_age}-year-old child named {child_name} with {description}"

            logger.info(
                "AI-Director character description ready",
                child_name=child_name,
                description_length=len(description),
                description_preview=description[:80] + "...",
            )

            return description

        except (KeyError, IndexError) as e:
            logger.error("Failed to parse AI-Director analysis", error=str(e))
            # Fallback to generic description
            return f"a {child_age}-year-old child named {child_name} with a friendly expression"

    @rate_limit_retry(service="gemini", max_attempts=3, timeout_attempts=3)
    async def analyze_multiple_photos(
        self,
        image_sources: list[str | bytes],
        child_age: int | None = None,
        child_gender: str | None = None,
    ) -> str:
        """
        Analyze MULTIPLE photos of the same person for more accurate description.

        Multi-view analysis provides better results by:
        - Confirming consistent features across photos
        - Reducing errors from single-photo lighting/angle issues
        - Capturing features visible in different angles

        Args:
            image_sources: List of image URLs or bytes (2-5 photos recommended)
            child_age: Optional age for context
            child_gender: Optional gender ("erkek", "kiz")

        Returns:
            Consolidated facial description string

        Raises:
            ValueError: If no valid images provided
            httpx.HTTPStatusError: If API call fails
        """
        if not image_sources:
            raise ValueError("At least one image is required")

        # If only one image, use single-photo analysis
        if len(image_sources) == 1:
            return await self.analyze_face(
                image_source=image_sources[0],
                child_age=child_age,
                child_gender=child_gender,
            )

        logger.info(
            "Starting multi-view face analysis",
            photo_count=len(image_sources),
            has_age=child_age is not None,
        )

        # Load all images
        image_parts = []
        for i, source in enumerate(image_sources[:5]):  # Max 5 images
            try:
                base64_data, mime_type = await self._load_image_as_base64(source)
                image_parts.append({"inlineData": {"mimeType": mime_type, "data": base64_data}})
                logger.debug(f"Loaded image {i + 1}/{len(image_sources)}")
            except Exception as e:
                logger.warning(f"Failed to load image {i + 1}", error=str(e))
                continue

        if not image_parts:
            raise ValueError("No valid images could be loaded")

        # Build context hint
        context_hints = []
        if child_age:
            context_hints.append(f"This is a {child_age}-year-old child")
        if child_gender:
            context_hints.append(f"Gender: {child_gender}")
        context_hints.append(f"Analyzing {len(image_parts)} photos of the SAME person")

        context_prefix = ". ".join(context_hints) + ".\n\n"

        # Build multi-image request
        url = f"{self.base_url}/models/{self.model}:generateContent?key={self.api_key}"

        # Combine all images with the multi-view prompt
        content_parts = image_parts + [{"text": context_prefix + MULTI_VIEW_ANALYSIS_PROMPT}]

        payload = {
            "contents": [{"parts": content_parts}],
            "generationConfig": {
                "temperature": 0.2,
                "topP": 0.8,
                "maxOutputTokens": 4096,  # Increased to accommodate gemini-2.5-flash reasoning tokens
            },
            "safetySettings": [
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
            ],
        }

        async with httpx.AsyncClient(
            timeout=self.timeout * 2
        ) as client:  # Double timeout for multiple images
            response = await client.post(url, json=payload)
            response.raise_for_status()
            result = response.json()

        # Extract the description
        try:
            description = result["candidates"][0]["content"]["parts"][0]["text"]
            description = description.strip()

            logger.info(
                "Multi-view face analysis complete",
                photo_count=len(image_parts),
                description_length=len(description),
                word_count=len(description.split()),
            )

            return description

        except (KeyError, IndexError) as e:
            logger.error("Failed to parse multi-view analysis response", error=str(e))
            raise ValueError("Failed to generate face description from multiple images")

    async def get_enhanced_child_description_multi(
        self,
        image_sources: list[str | bytes],
        child_name: str,
        child_age: int,
        child_gender: str | None = None,
    ) -> str:
        """
        Generate enhanced child description from MULTIPLE photos.

        This is the recommended method when multiple photos are available.
        Provides more accurate and consistent descriptions.

        Args:
            image_sources: List of child's photo URLs or bytes
            child_name: Child's name
            child_age: Child's age
            child_gender: Optional gender ("erkek", "kiz")

        Returns:
            Complete description string ready for image generation prompts
        """
        # Get multi-view face description
        face_description = await self.analyze_multiple_photos(
            image_sources=image_sources,
            child_age=child_age,
            child_gender=child_gender,
        )

        # Build the enhanced description — use "child" to let PuLID handle gender
        enhanced_description = (
            f"A {child_age}-year-old child named {child_name} with {face_description}"
        )

        logger.info(
            "Multi-view enhanced child description generated",
            child_name=child_name,
            photo_count=len(image_sources),
            total_length=len(enhanced_description),
        )

        return enhanced_description


# Singleton instance for convenience
_face_analyzer: FaceAnalyzerService | None = None


def get_face_analyzer() -> FaceAnalyzerService:
    """Get or create the FaceAnalyzerService singleton."""
    global _face_analyzer
    if _face_analyzer is None:
        _face_analyzer = FaceAnalyzerService()
    return _face_analyzer

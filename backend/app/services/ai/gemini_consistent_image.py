"""
Gemini referans görselli görsel üretim servisi.

Fal generate_consistent_image ile aynı girdi/çıktı imzasını sunar:
referans çocuk fotoğrafı + compose_visual_prompt ile oluşturulan prompt
tek generateContent çağrısında Gemini'ye gönderilir.
"""

import asyncio
import base64
import time
import uuid
from typing import Any

import httpx
import structlog

from app.config import settings
from app.core.exceptions import AIServiceError
from app.core.rate_limit import rate_limit_retry
from app.prompt_engine import (
    LIKENESS_HINT_WHEN_REFERENCE,
    compose_visual_prompt,
    truncate_safe_2d,
)
from app.prompt_engine.constants import (
    DEFAULT_COVER_TEMPLATE_EN,
    DEFAULT_INNER_TEMPLATE_EN,
    MAX_FAL_PROMPT_CHARS,
)

logger = structlog.get_logger()

# Nano Banana: generateContent ile görsel üretimi (resmi model adı)
GEMINI_IMAGE_MODEL = "gemini-2.5-flash-image"
GEMINI_IMAGE_API_URL = (
    f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_IMAGE_MODEL}:generateContent"
)
DEFAULT_REF_MIME = "image/jpeg"


class GeminiConsistentImageService:
    """
    Fal generate_consistent_image ile uyumlu Gemini görsel üretimi.
    Referans görsel + composed prompt tek istekte gönderilir.
    """

    def __init__(self, api_key: str | None = None, timeout: float = 90.0):
        self.api_key = api_key or settings.gemini_api_key
        self.timeout = timeout
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is required for Gemini image generation")
        # Shared httpx client with connection pooling
        self._http_client: httpx.AsyncClient | None = None

    def _get_client(self) -> httpx.AsyncClient:
        """Lazy-init shared httpx client."""
        if self._http_client is None or self._http_client.is_closed:
            self._http_client = httpx.AsyncClient(
                timeout=self.timeout,
                limits=httpx.Limits(max_connections=100, max_keepalive_connections=20),
            )
        return self._http_client

    @rate_limit_retry(service="gemini", max_attempts=4, timeout_attempts=2)
    async def generate_consistent_image(
        self,
        prompt: str,
        child_face_url: str,
        clothing_prompt: str = "",
        style_modifier: str = "",
        width: int = 1024,
        height: int = 1024,
        id_weight: float | None = None,
        true_cfg_override: float | None = None,  # PuLID only — ignored by Gemini
        start_step_override: int | None = None,  # PuLID only — ignored by Gemini
        num_inference_steps_override: int | None = None,  # FLUX only — ignored by Gemini
        guidance_scale_override: float | None = None,  # FLUX only — ignored by Gemini
        use_queue: bool = True,
        is_cover: bool = False,
        page_number: int | None = None,
        preview_id: str | None = None,
        order_id: str | None = None,
        template_en: str = "",
        story_title: str = "",
        child_gender: str = "",
        child_age: int | str = "",
        style_negative_en: str = "",
        base_negative_en: str = "",
        leading_prefix_override: str | None = None,
        style_block_override: str | None = None,
        skip_compose: bool = False,
        precomposed_negative: str = "",
        seed: int | None = None,
        reference_embedding: list[float] | None = None,
        character_description: str = "",
    ) -> str | tuple[str, dict]:
        """
        Fal ile aynı imza: referans + composed prompt ile görsel üretir.
        Dönüş: image_url veya (image_url, { final_prompt, negative_prompt, gemini_params }).
        """
        style_text = (style_modifier or "").strip()
        style_negative = (style_negative_en or "").strip()

        logger.info(
            "GEMINI_GENERATE_INPUT_DEBUG",
            style_modifier_first80=style_text[:80] if style_text else "(empty)",
            has_style_negative=bool(style_negative),
            has_leading_prefix_override=bool(leading_prefix_override),
            has_style_block_override=bool(style_block_override),
            has_child_face_url=bool(child_face_url),
            clothing_prompt_first100=(clothing_prompt or "")[:100],
            is_cover=is_cover,
            skip_compose=skip_compose,
            prompt_first80=(prompt or "")[:80],
        )

        if skip_compose:
            full_prompt = prompt
            # For covers: strip any legacy "no text" bans that may be present in
            # DB-sourced templates (migration 072 and earlier). These contradict
            # the native title-rendering instruction we inject below.
            if is_cover:
                import re as _re  # noqa: PLC0415
                full_prompt = _re.sub(
                    r"CRITICAL:\s*Do NOT include ANY text[^.]*\.",
                    "",
                    full_prompt,
                    flags=_re.IGNORECASE,
                ).strip()
                full_prompt = _re.sub(
                    r"Do NOT include ANY text[^.]*\.",
                    "",
                    full_prompt,
                    flags=_re.IGNORECASE,
                ).strip()
                full_prompt = _re.sub(r"\s{2,}", " ", full_prompt).strip()
            _precomp_neg = (precomposed_negative or "").strip()
            # If the stored negative is too short (LLM-generated placeholder),
            # augment with the proper base negative automatically.
            if len(_precomp_neg) < 200:
                from app.prompt.negative_builder import BASE_NEGATIVE  # noqa: PLC0415
                _char_lock = (
                    "different outfit, outfit change, costume change, different clothing, "
                    "different hairstyle, hair color change, different hair length, "
                    "different skin tone, age change, different child"
                )
                _augmented = BASE_NEGATIVE + ", " + _char_lock
                if child_gender:
                    _gender_lower2 = str(child_gender).lower()
                    if _gender_lower2 in ("erkek", "boy", "male"):
                        _augmented += ", dress, skirt, gown, girly clothes, feminine clothing, girl, female child"
                    elif _gender_lower2 in ("kız", "kiz", "girl", "female"):
                        _augmented += ", boy, male child, masculine features, short hair, buzz cut, male clothing, boy's outfit, he, him"
                full_negative = _augmented + (", " + _precomp_neg if _precomp_neg else "")
            else:
                full_negative = _precomp_neg

            # V3 safety net: inject shortened likeness hint if lost.
            # ANTI_PHOTO_FACE_NEGATIVE is NOT re-injected — it fights PuLID.
            if child_face_url:
                _lh = LIKENESS_HINT_WHEN_REFERENCE.strip()
                _lh_sig = "stylized illustration"
                if _lh and _lh_sig not in full_prompt:
                    _style_sep = "\n\nSTYLE:"
                    _si = full_prompt.find(_style_sep)
                    if _si > 0:
                        full_prompt = f"{full_prompt[:_si]}, {_lh}{full_prompt[_si:]}"
                    else:
                        full_prompt = f"{_lh}, {full_prompt}"

            if len(full_prompt) > MAX_FAL_PROMPT_CHARS:
                _orig = len(full_prompt)
                full_prompt = truncate_safe_2d(full_prompt, MAX_FAL_PROMPT_CHARS)
                logger.warning(
                    "V3 skip_compose prompt truncated (Gemini)",
                    original_length=_orig,
                    truncated_length=len(full_prompt),
                    style_block_preserved="STYLE:" in full_prompt,
                )
            logger.info(
                "V3_SKIP_COMPOSE_PROMPT_STATS_GEMINI",
                prompt_length=len(full_prompt),
                negative_length=len(full_negative),
                has_style_block="STYLE:" in full_prompt,
            )
        else:
            likeness_hint = LIKENESS_HINT_WHEN_REFERENCE if child_face_url else ""
            effective_template = (template_en or "").strip()
            if not effective_template:
                effective_template = (
                    DEFAULT_COVER_TEMPLATE_EN if is_cover else DEFAULT_INNER_TEMPLATE_EN
                )
            full_prompt, negative_suffix = compose_visual_prompt(
                prompt,
                is_cover=is_cover,
                template_en=effective_template,
                clothing_description=clothing_prompt,
                story_title=(story_title or "").strip() if is_cover else "",
                child_gender=child_gender,
                child_age=child_age,
                style_prompt_en=style_text,
                style_negative_en=style_negative,
                base_negative_en=base_negative_en or "",
                likeness_hint=likeness_hint,
                leading_prefix_override=leading_prefix_override,
                style_block_override=style_block_override,
                character_description=character_description,
                face_reference_url=child_face_url or "",
            )
            if len(full_prompt) > MAX_FAL_PROMPT_CHARS:
                full_prompt = truncate_safe_2d(full_prompt, MAX_FAL_PROMPT_CHARS)
            full_negative = negative_suffix

        # Gender-specific negatives — V3 already includes them via
        # build_enhanced_negative(); only append for V2 legacy path.
        if not skip_compose:
            _gender_lower = str(child_gender).lower() if child_gender else ""
            if _gender_lower in ("erkek", "boy", "male"):
                full_negative += ", dress, skirt, gown, tutu, girly clothes, feminine clothing, pigtails, bows in hair, female child, girl, feminine face, lipstick"
            elif _gender_lower in ("kiz", "girl", "female"):
                full_negative += ", boy, male child, masculine features, short hair, buzz cut, crew cut, masculine face"

        ref_b64: str | None = None
        ref_mime = DEFAULT_REF_MIME
        if child_face_url:
            try:
                ref_b64, ref_mime = await _download_image_as_base64_cached(child_face_url)
            except Exception as dl_err:
                logger.warning("Child photo download failed, proceeding without ref", error=str(dl_err))
                ref_b64 = None

        has_ref = bool(ref_b64)

        # Build instruction text
        # For front covers WITH title: text ban is lifted so Gemini can render the book title natively.
        # For back covers (no title): text is STRICTLY BANNED.
        # For inner pages: text is banned.
        if is_cover and story_title:
            # FRONT COVER with title
            base_instruction = (
                "Generate a full-bleed 4:3 landscape children's book FRONT COVER illustration. "
                "Fill the entire frame edge-to-edge. "
                "Do NOT include any watermarks, logos, or signatures. "
            )
        elif is_cover and not story_title:
            # BACK COVER (no title)
            base_instruction = (
                "Generate a full-bleed 4:3 landscape children's book BACK COVER illustration. "
                "Fill the entire frame edge-to-edge. "
                "CRITICAL: This is the BACK COVER — it must be a pure illustration with ZERO text elements. "
                "Do NOT include ANY text, title, letters, words, book title, story title, writing, watermarks, logos, or signatures. "
                "This is a text-free visual illustration only. "
            )
        else:
            # INNER PAGE
            base_instruction = (
                "Generate a full-bleed 4:3 landscape children's book illustration. "
                "Fill the entire frame edge-to-edge. "
                "Do NOT include any text, letters, words, logos, or watermarks. "
            )

        _clothing_text = (clothing_prompt or "").strip()

        # Resolve illustration style — cascade priority:
        # 1. Admin DB style_block_override (explicit admin setting, highest priority)
        # 2. Hardcoded StyleConfig.style_block resolved from prompt_modifier keywords
        # 3. Raw prompt_modifier text
        # 4. Generic fallback
        from app.prompt.style_config import (
            resolve_style as _resolve_style_for_gemini,  # noqa: PLC0415
        )
        _st = _resolve_style_for_gemini(style_text) if style_text else None
        _gemini_style = (
            ((style_block_override or "").strip())
            or (_st.style_block.strip() if _st and _st.style_block else "")
            or style_text.strip()
            or "stylized children's book illustration"
        )

        # Resolve child age and gender for character identity
        _age_str = f"{child_age}-year-old" if child_age else "8-year-old"
        _gender_lower_cg = str(child_gender).lower() if child_gender else ""
        if _gender_lower_cg in ("erkek", "boy", "male"):
            _gender_str = "boy"
            _gender_pronoun = "He"
        elif _gender_lower_cg in ("kız", "kiz", "girl", "female"):
            _gender_str = "girl"
            _gender_pronoun = "She"
        else:
            _gender_str = "child"
            _gender_pronoun = "They"

        _modern_child_anchor = (
            f"CHARACTER: A modern-day {_age_str} {_gender_str} visiting the location. "
            f"MUST wear contemporary casual clothes (no historical costumes or robes). "
            f"MUST be visibly a young child. "
            f"HAIR MUST BE UNCOVERED AND VISIBLE (no headscarves, veils, or hats unless explicitly requested). "
        )

        # Build cover title instruction when story_title is available
        _cover_title_instruction = ""
        if is_cover and story_title:
            # Professional book cover title design — title is a premium design element
            _title_words = story_title.split()
            _mid = len(_title_words) // 2
            _line1 = " ".join(_title_words[:_mid]) if len(_title_words) > 3 else story_title
            _line2 = " ".join(_title_words[_mid:]) if len(_title_words) > 3 else ""
            _title_display = f'"{_line1}" on the first line and "{_line2}" on the second line' if _line2 else f'"{story_title}"'
            _cover_title_instruction = (
                f"BOOK TITLE — PREMIUM DESIGN ELEMENT: "
                f"The title text is: [{story_title}]. "
                f"Render EXACTLY this text centered at the top 10-15% of the image. "
                f"If the title is long, split into 2 centered lines: {_title_display}. "
                f"\n"
                f"TITLE DESIGN (CRITICAL — This is a professional children's book cover): "
                f"TYPOGRAPHY: Large, bold, elegant storybook letters with excellent legibility. "
                f"COLOR: Rich golden-amber gradient — deep warm gold at the base, bright luminous gold at the top, "
                f"with a brilliant near-white shimmer/highlight on the upper third of each letter (like sunlight hitting polished gold). "
                f"MATERIAL: 3D embossed effect — letters appear raised and premium, like metallic foil stamping. "
                f"OUTLINE: Thick dark brown or black beveled stroke around every letter for depth and contrast. "
                f"GLOW: Soft warm golden aura/halo radiating from behind the title block, creating a magical luminous effect. "
                f"SHADOW: Gentle drop shadow offset down-right to enhance 3D depth. "
                f"EMBELLISHMENTS: 4-8 small golden stars (★) scattered around the title at varying sizes for whimsy. "
                f"\n"
                f"CRITICAL CONSTRAINT — PREVENT COLOR BLEED: "
                f"The title's golden glow and warmth must ONLY affect the title itself and its immediate area (top 15%). "
                f"The REST of the scene (sky, environment, background below the title) must maintain its NATURAL colors and lighting. "
                f"DO NOT let the golden title color bleed into or tint the sky, clouds, or environment. "
                f"The scene should look natural and atmospheric — NOT overly yellow/golden. "
                f"The title is a separate design layer — treat it as overlaid premium foil lettering, NOT part of the scene lighting. "
                f"\n"
                f"LAYOUT: The title ends at 15% mark. The child and main scene start at 20% mark. NO overlap. "
            )
            logger.info("cover_title_instruction_added", title=story_title, has_two_lines=bool(_line2))

        # Shared composition mandate — applied to BOTH has_ref and else branches
        if is_cover:
            _composition_mandate = (
                "COMPOSITION: Wide angle shot. The child's FULL BODY (head to shoes) MUST be visible, "
                "occupying 20-30% of the frame. The detailed environment fills the rest. "
                "NO close-ups, NO cropped bodies, NO portraits. "
                "COVER LAYOUT: Reserve only the top 12-15% of the image (sky/clear area) for the book title. "
                "The child and main scene occupy the lower 85% of the image. "
                "Do not place the child's head above the 20% mark from the top. "
            )
        else:
            _composition_mandate = (
                "COMPOSITION: Wide angle shot. The child's FULL BODY (head to shoes) MUST be visible, "
                "occupying 20-30% of the frame. The detailed environment fills the rest. "
                "NO close-ups, NO cropped bodies, NO portraits. "
                "Ensure clear areas in the environment where text can be placed without obscuring the main action. "
            )

        # Gender lock for explicit female/male anchor
        if _gender_str == "girl":
            _gender_lock = "GENDER: Must clearly be a girl with loose uncovered hair. No masculine features. "
        elif _gender_str == "boy":
            _gender_lock = "GENDER: Must clearly be a boy. No feminine features or dresses. "
        else:
            _gender_lock = ""

        # CRITICAL OVERRIDE block — injected at the very start of text_instruction
        # to override Gemini's contextual priors (mosque → hijab, dark scene → fantasy costume, etc.)
        _critical_override = (
            "CRITICAL RULES: 1. Hair MUST be uncovered (no hijab/veil) everywhere. "
            "2. Full body MUST be visible (no close-ups). "
        )

        if has_ref:
            # --- PHOTO-FIRST approach: Gemini gets the image FIRST, then a SHORT direct instruction ---
            # Instead of 2000-word text descriptions, we tell Gemini to LOOK at the photo
            # and redraw that child in the requested illustration style.

            # Detect hair texture from character_description for a single targeted note
            _hair_note = ""
            _clean_char_desc = ""
            _face_description_note = ""
            if character_description:
                _clean_char_desc = character_description.split("|")[0].strip()
                _desc_lower = _clean_char_desc.lower()
                _face_description_note = f"FACIAL FEATURES TO COPY: {_clean_char_desc} "
                if any(kw in _desc_lower for kw in ("curly", "curl", "coil", "kinky", "ringlet")):
                    _hair_note = "HAIR: The child has CURLY hair — draw spiral curls, NOT straight, NOT wavy. "
                elif any(kw in _desc_lower for kw in ("wavy", "wave")):
                    _hair_note = "HAIR: The child has WAVY hair — draw visible waves, NOT straight. "

            # Age note for young children
            _age_note = ""
            try:
                _child_age_int = int(child_age) if child_age else 8
            except (ValueError, TypeError):
                _child_age_int = 8
            if _child_age_int <= 7:
                _age_note = (
                    f"AGE: Only {_child_age_int} years old — draw a VERY YOUNG child face: "
                    f"round chubby cheeks, soft small nose, baby-face proportions. NOT older than {_child_age_int}. "
                )

            # Outfit note - Only enforce if explicitly provided; never use hardcoded defaults
            if _clothing_text:
                _outfit_note = (
                    f"OUTFIT — CRITICAL CONSISTENCY: The child MUST wear EXACTLY this specific outfit on EVERY page and cover: {_clothing_text}. "
                    f"SAME colors, SAME items, SAME style. DO NOT change outfit, DO NOT modify clothing, DO NOT use different clothes. "
                    f"This exact outfit is mandatory for character consistency across the entire book. "
                )
            else:
                _outfit_note = ""

            # Secondary characters note
            _secondary_note = (
                "Other characters in the scene must look CLEARLY DIFFERENT from the main child — "
                "different age, different hair, different face. Adults must look visibly adult (taller, older face). "
            )

            # Build SHORT, DIRECT instruction — photo does the heavy lifting
            text_instruction = (
                # 0. Base layout rules (landscape, full-bleed)
                base_instruction
                + _critical_override
                # 1. Core task — direct photo-to-illustration conversion with MAXIMUM LIKENESS PRIORITY
                + "TASK: You are an expert portrait artist specializing in maintaining facial likeness. "
                "The attached photo is your PRIMARY REFERENCE for the main character's face. "
                "Your ABSOLUTE TOP PRIORITY is MAXIMUM FACIAL LIKENESS AND RESEMBLANCE to the reference photo. "
                "CRITICAL INSTRUCTIONS: "
                "1. Study the photo carefully and replicate EVERY facial feature with precision: "
                "   - EXACT eye shape, size, and placement (DO NOT simplify or make generic) "
                "   - EXACT nose shape and size (preserve the child's unique nose profile) "
                "   - EXACT mouth shape, lip fullness, and expression "
                "   - EXACT face shape and proportions (round, oval, square — match the photo exactly) "
                "   - EXACT eyebrow shape and thickness "
                "   - EXACT ear shape if visible "
                "2. Hair MUST be identical: EXACT color, EXACT length, EXACT texture (straight/wavy/curly), EXACT style/parting/bangs. "
                "3. Skin tone MUST match the photo exactly — do NOT lighten or darken. "
                "4. Apply the illustration style ONLY to: rendering technique, background environment, lighting atmosphere. "
                "5. The FACE itself should remain highly realistic and recognizable — DO NOT over-stylize, cartoonize, or simplify facial features. "
                "6. Think: 'If the child's parent saw this illustration, they should IMMEDIATELY recognize their child.' "
                "You MUST preserve the child's true identity. The illustration style is for the environment, NOT for changing the child's actual face. "
                + _face_description_note
                # 2. Hair and age targeted notes (short)
                + _hair_note
                + _age_note
                # 3. Style
                + f"STYLE: {_gemini_style}. "
                # 4. Composition
                + _composition_mandate
                # 5. Cover title (only for covers with a story title)
                + _cover_title_instruction
                # 6. Outfit
                + _outfit_note
                # 7. Head covering ban
                + "HEAD: The child's hair MUST BE UNCOVERED AND VISIBLE — NO headscarf, NO hijab, NO veil, NO hood. "
                "This applies even inside a mosque or religious site. "
                # 8. Secondary characters
                + _secondary_note
                # 9. Text ban — back covers have NO text at all, front covers allow title only
                + ("" if (is_cover and story_title) else "CRITICAL TEXT BAN: NO text, NO words, NO letters, NO title, NO watermarks anywhere in the image. ")
                # 10. Scene
                + "SCENE: " + full_prompt
            )
        else:
            # No reference photo — only enforce outfit if explicitly provided
            if _clothing_text:
                _outfit_anchor = (
                    f"OUTFIT — CRITICAL CONSISTENCY: The child MUST wear EXACTLY this specific outfit on EVERY page and cover: {_clothing_text}. "
                    f"SAME colors, SAME items, SAME style. DO NOT change outfit, DO NOT modify clothing, DO NOT use different clothes. "
                )
            else:
                _outfit_anchor = ""

            text_instruction = (
                base_instruction
                + _critical_override
                + _composition_mandate
                + _cover_title_instruction
                + f"STYLE: {_gemini_style}. "
                + _modern_child_anchor
                + _gender_lock
                + _outfit_anchor
                + f"The {_gender_str} must be actively engaged in the story action. "
                "Adults must look visibly adult. Environment must be sharp and detailed. "
                + ("" if (is_cover and story_title) else "CRITICAL TEXT BAN: NO text, NO words, NO letters, NO title, NO watermarks anywhere in the image. ")
                + "Scene description: " + full_prompt
            )

        # For front covers with title: allow title text — ban watermarks/logos/extra text.
        # For back covers (no title): ban ALL text including titles.
        # For inner pages: ban all text.
        if is_cover and story_title:
            # FRONT COVER - allow title only
            avoid_extra = (
                "border, frame, empty margin, cream border, vignette, faded edges, "
                "blank area around illustration, paper border, white frame, black bars, "
                "letterbox, pillarbox, padding, white space around scene, dark edges, "
                "watermark, logo, signature, stamp, copyright mark, artist signature, "
                "extra text beyond the title, random letters, subtitles, captions"
            )
        else:
            # BACK COVER or INNER PAGE - ban all text
            avoid_extra = (
                "border, frame, empty margin, cream border, vignette, faded edges, "
                "blank area around illustration, paper border, white frame, black bars, "
                "letterbox, pillarbox, padding, white space around scene, dark edges, "
                "text, letters, words, title, typography, written text, book title, story title, any text overlay, "
                "watermark, logo, signature, stamp, copyright mark, artist signature"
            )
        _NEG_CHAR_LIMIT = 1500
        if full_negative:
            neg_text = full_negative[:_NEG_CHAR_LIMIT]
            if len(full_negative) > _NEG_CHAR_LIMIT:
                logger.warning(
                    "Negative prompt truncated for Gemini",
                    original_len=len(full_negative),
                    truncated_len=_NEG_CHAR_LIMIT,
                )
            text_instruction += ". Avoid in the image: " + neg_text + ", " + avoid_extra
        else:
            text_instruction += ". Avoid in the image: " + avoid_extra

        parts: list[dict[str, Any]] = []
        if has_ref:
            parts.append({"inlineData": {"mimeType": ref_mime, "data": ref_b64}})
        parts.append({"text": text_instruction})

        # width/height'den Gemini destekli aspect ratio hesapla
        gemini_aspect = _width_height_to_gemini_aspect(width, height)

        gen_config: dict[str, Any] = {
            "responseModalities": ["TEXT", "IMAGE"],
        }
        if gemini_aspect:
            gen_config["imageConfig"] = {"aspectRatio": gemini_aspect}
        if seed is not None:
            gen_config["seed"] = seed

        payload: dict[str, Any] = {
            "contents": [{"parts": parts}],
            "generationConfig": gen_config,
        }

        logger.info(
            "Gemini consistent image request",
            prompt_length=len(full_prompt),
            has_ref=has_ref,
            width=width,
            height=height,
            aspect_ratio=gemini_aspect,
            seed=seed,
        )

        client = self._get_client()
        response = await client.post(
            f"{GEMINI_IMAGE_API_URL}?key={self.api_key}",
            json=payload,
        )

        # raise_for_status() so rate_limit_retry decorator can catch 429/5xx
        if response.status_code != 200:
            logger.error(
                "Gemini image API error",
                status=response.status_code,
                body=response.text[:500],
            )
            raise httpx.HTTPStatusError(
                message=f"Gemini API hatası: {response.status_code}",
                request=response.request,
                response=response,
            )

        data = response.json()
        image_bytes: bytes | None = None
        for candidate in data.get("candidates", []):
            for part in candidate.get("content", {}).get("parts", []):
                if "inlineData" in part:
                    idata = part["inlineData"]
                    if idata.get("mimeType", "").startswith("image/"):
                        image_bytes = base64.b64decode(idata["data"])
                        break
            if image_bytes:
                break

        if not image_bytes:
            logger.error(
                "Gemini image response had no image",
                keys=list(data.keys()),
                candidates=len(data.get("candidates", [])),
            )
            raise AIServiceError(
                "GeminiConsistentImage",
                "Görsel üretilemedi - yanıtta görsel yok.",
            )

        from app.services.storage_service import storage_service

        data_url = f"data:image/png;base64,{base64.b64encode(image_bytes).decode()}"
        folder = "gemini-generated"
        filename = f"{uuid.uuid4().hex}.png"
        image_url = await asyncio.to_thread(
            storage_service.upload_base64_image,
            data_url, folder, filename,
        )

        if page_number is not None:
            info: dict[str, Any] = {
                "page_index": page_number,
                "final_prompt": full_prompt,
                "negative_prompt": full_negative,
                "manifest": {
                    "provider": "gemini",
                    "model": GEMINI_IMAGE_MODEL,
                    "width": width,
                    "height": height,
                    "reference_used": has_ref,
                },
                "gemini_params": {
                    "model": GEMINI_IMAGE_MODEL,
                    "width": width,
                    "height": height,
                    "aspect_ratio": gemini_aspect,
                    "reference_used": has_ref,
                    "seed": seed,
                },
            }
            return (image_url, info)
        return image_url


# Gemini destekli aspect ratio'lar: "1:1","2:3","3:2","3:4","4:3","4:5","5:4","9:16","16:9","21:9"
_GEMINI_ASPECT_RATIOS: list[tuple[str, float]] = [
    ("1:1", 1.0),
    ("4:5", 0.8),
    ("3:4", 0.75),
    ("2:3", 0.667),
    ("9:16", 0.5625),
    ("5:4", 1.25),
    ("4:3", 1.333),
    ("3:2", 1.5),
    ("16:9", 1.778),
    ("21:9", 2.333),
]


def _width_height_to_gemini_aspect(width: int, height: int) -> str:
    """width/height oranını en yakın Gemini destekli aspect ratio string'ine çevir."""
    if height <= 0:
        return "4:3"
    ratio = width / height
    best_label = "4:3"
    best_diff = float("inf")
    for label, val in _GEMINI_ASPECT_RATIOS:
        diff = abs(ratio - val)
        if diff < best_diff:
            best_diff = diff
            best_label = label
    return best_label


# Shared client for image downloads (module-level)
_download_client: httpx.AsyncClient | None = None


def _get_download_client() -> httpx.AsyncClient:
    global _download_client
    if _download_client is None or _download_client.is_closed:
        _download_client = httpx.AsyncClient(timeout=30.0)
    return _download_client


async def close_download_client() -> None:
    """Shut down the module-level download client (call on app shutdown)."""
    global _download_client
    if _download_client and not _download_client.is_closed:
        await _download_client.aclose()
        _download_client = None


async def _download_image_as_base64(url: str) -> tuple[str | None, str]:
    """İndir, base64 ve mime döndür. Hata durumunda (None, 'image/jpeg')."""
    try:
        client = _get_download_client()
        resp = await client.get(url)
        resp.raise_for_status()
        raw = resp.content
        content_type = (resp.headers.get("content-type") or "").split(";")[0].strip()
        mime = content_type if content_type.startswith("image/") else "image/jpeg"
        return base64.b64encode(raw).decode("utf-8"), mime
    except Exception as e:
        logger.warning("Reference image download failed", url=url[:80], error=str(e))
        return None, DEFAULT_REF_MIME


# ---------------------------------------------------------------------------
# In-memory TTL cache: ayni cocuk fotosunu kitap icinde tekrar indirmez
# ---------------------------------------------------------------------------
_ref_cache: dict[str, tuple[str, str, float]] = {}  # url -> (b64, mime, monotonic_ts)
_REF_CACHE_TTL = 300  # 5 minutes (reduced from 10 to limit memory)
_REF_CACHE_MAX = 20   # max entries (~20 MB worst case)


async def _download_image_as_base64_cached(url: str) -> tuple[str | None, str]:
    """Cache'li indirme — ayni URL icin TTL suresi boyunca tekrar indirmez."""
    now = time.monotonic()
    cached = _ref_cache.get(url)
    if cached and (now - cached[2]) < _REF_CACHE_TTL:
        return cached[0], cached[1]

    b64, mime = await _download_image_as_base64(url)
    if b64:
        _ref_cache[url] = (b64, mime, now)
        # Evict expired entries first, then oldest if still over limit
        expired = [k for k, v in _ref_cache.items() if (now - v[2]) >= _REF_CACHE_TTL]
        for k in expired:
            _ref_cache.pop(k, None)
        while len(_ref_cache) > _REF_CACHE_MAX:
            oldest_key = min(_ref_cache, key=lambda k: _ref_cache[k][2])
            _ref_cache.pop(oldest_key, None)
    return b64, mime

"""Visual composer mixin for GeminiService.

Contains methods for building child descriptions, sanitizing scene
descriptions, and composing visual prompts for image generation.

Split from gemini_service.py for maintainability.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

from app.config import settings
from app.core.exceptions import AIServiceError

if TYPE_CHECKING:
    from app.models.scenario import Scenario
    from app.schemas.story import FinalPageContent, StoryResponse

logger = structlog.get_logger()


class _VisualComposerMixin:
    """Mixin providing visual prompt composition for GeminiService."""

    def _build_child_description(
        self,
        child_name: str,
        child_age: int,
        child_gender: str | None,
    ) -> str:
        """Build English child description for visual prompts.

        Uses 'child' instead of 'boy/girl' to let PuLID face reference
        determine gender — avoids generic gendered archetype overriding likeness.
        """
        return f"a {child_age} year old child named {child_name}"

    # Prompt leakage: template/instruction text must never end up in visual_prompt for Fal.ai
    # Turkish style/composition phrases that must NEVER appear in scene_description (FAL expects English)
    TURKISH_LEAKAGE = (
        "2 boyutlu",
        "çocuk resimli kitap",
        "karikatür illüstrasyonu",
        "Altta metin alanı",
        "Geniş çekim",
        "çerçevenin %30",
        "STİL:",
        "orta kalınlıkta kontürlü",
        "sadeleştirilmiş şekiller",
        "yumuşak pastel",
        "ince detaylar",
    )
    CONTAMINATION_MARKERS = (
        "GİRDİ DEÄİÅKENLERİ",
        '"pages":',
        "Sen, ödüllü",
        "Sen, odullu",  # ASCII fallback
        "ÇIKTI FORMATI",
        "Görevin:",
        "**GİRDİ",
        "**ÇIKTI",
        "KÜLTÜREL RUHUNU",
        "Görsel Stil:",
        "Sayfa Sayısı:",
        "HİKAYE RUHU VE TEMALAR",
        "HİKAYE AKIÅI",
        "GÖRSEL PROMPT KURALLARI",
        "ÇIKTI FORMATI (JSON)",
    )
    # PASS-2 scene_description'da olmaması gereken ifadeler (template/lens/style). Otomatik silinir.
    FORBIDDEN_IN_SCENE = (
        "space for title",
        "title safe area",
        "empty space at bottom",
        "empty space at bottom for captions",
        "bottom text space",
        "caption area",
        "watermark",
        "logo",
        "lens",
        "camera",
        "dslr",
        "bokeh",
        "cinematic",
        "photorealistic",
        "render",
        "cgi",
        "anime",
        "ghibli",
        "miyazaki",
        "manga",
        "cel-shaded",
        "pixar",
        "disney",
        "unreal",
        "octane",
        "blender",
        "full bady",  # Gemini typo; kompozisyon şablonda "full body when scene allows"
        "full body visible",  # scene'de olmasın, COMPOSITION_RULES ekliyor
    )
    MAX_VISUAL_PROMPT_LENGTH = 1200

    def _is_visual_prompt_contaminated(self, prompt: str) -> bool:
        """True if prompt contains instruction/template text (must not be sent to Fal.ai)."""
        if not prompt:
            return True
        if len(prompt) > self.MAX_VISUAL_PROMPT_LENGTH:
            return True
        prompt_lower = prompt.lower()
        for marker in self.CONTAMINATION_MARKERS:
            if marker in prompt or marker.lower() in prompt_lower:
                return True
        return False

    # Style phrases that Gemini sometimes leaks INTO scene_description.
    # These must be stripped because style is injected later at compose.
    STYLE_LEAK_PHRASES = [
        # 2D / picture-book tokens
        "2D children's picture-book cartoon illustration",
        "2D children's picture-book",
        "children's picture-book cartoon illustration",
        "clean crisp lineart with medium outlines",
        "clean crisp lineart",
        "simplified shapes",
        "soft pastel color palette",
        "smooth soft shading with gentle gradients",
        "smooth soft shading",
        "subtle paper texture",
        "warm soft ambient light",
        "storybook illustration feel",
        "foreground/midground/background layering",
        "NO cinematic look",
        "NO film still",
        "NO lens terms",
        "NO volumetric effects",
        "NO dramatic contrast",
        # 3D / Pixar tokens
        "Pixar Animation Studios",
        "pixar-inspired",
        "3D animated children's book",
        "3D rendered illustration",
        "subsurface scattering",
        "smooth polished 3D",
        "gentle global illumination",
        # Watercolor tokens
        "watercolor painting on textured paper",
        "visible wet brush strokes",
        "paint bleeding at edges",
        # Default storybook
        "soft children's book illustration",
        "warm pastel colors",
        "storybook art",
        "cozy lighting",
    ]

    def _sanitize_scene_description(self, scene_desc: str) -> str:
        """Remove instruction/template/style leakage from scene_description. PASS-2 çıktı zorunlu temizlik."""
        if not scene_desc:
            return "A child in an adventure scene."
        import re as _re

        # Very long scene_desc is almost certainly template leakage
        if len(scene_desc) > 1500:
            scene_desc = scene_desc[:1500]
        scene_lower = scene_desc.lower()
        earliest = len(scene_desc)
        # Strip Turkish style/composition text (FAL expects English only)
        for phrase in self.TURKISH_LEAKAGE:
            idx = scene_desc.find(phrase)
            if idx == -1:
                idx = scene_lower.find(phrase.lower())
            if idx != -1 and idx < earliest:
                earliest = idx
        for marker in self.CONTAMINATION_MARKERS:
            idx = (
                scene_desc.find(marker)
                if marker in scene_desc
                else scene_lower.find(marker.lower())
            )
            if idx != -1 and idx < earliest:
                earliest = idx
        if earliest < len(scene_desc):
            scene_desc = scene_desc[:earliest].strip()

        # Strip FORBIDDEN_IN_SCENE (template/lens/style — tek kaynak template'te)
        for phrase in self.FORBIDDEN_IN_SCENE:
            pattern = _re.compile(_re.escape(phrase), _re.IGNORECASE)
            scene_desc = pattern.sub("", scene_desc)
        # Strip leaked style phrases (case-insensitive)
        for phrase in self.STYLE_LEAK_PHRASES:
            pattern = _re.compile(_re.escape(phrase), _re.IGNORECASE)
            scene_desc = pattern.sub("", scene_desc)
        # Clean up messy punctuation left after stripping
        scene_desc = _re.sub(r"\.{2,}", ".", scene_desc)
        scene_desc = _re.sub(r",\s*,", ",", scene_desc)
        scene_desc = _re.sub(r"\s{2,}", " ", scene_desc)
        scene_desc = scene_desc.strip().strip(",").strip(".")
        scene_desc = scene_desc.strip()

        if not scene_desc or len(scene_desc) < 20:
            return "A child in an adventure scene."

        # ── Türkçe metin tespiti ──
        # Gemini bazen Türkçe hikaye metnini scene_description'a kopyalıyor.
        # Türkçe'ye özgü karakterler (ş, ğ, ı, İ, Å, Ä) ve yaygın Türkçe kelimeler tespit et.
        _TURKISH_SPECIFIC_CHARS = set("\u015f\u011f\u0131\u015e\u011e\u0130")  # ş ğ ı Å Ä İ
        _turkish_char_count = sum(1 for ch in scene_desc if ch in _TURKISH_SPECIFIC_CHARS)

        # 2+ Türkçe-özel karakter = kesinlikle Türkçe metin
        if _turkish_char_count >= 2:
            logger.warning(
                "Turkish text detected in scene_description (%d Turkish chars), replacing with fallback",
                _turkish_char_count,
                original=scene_desc[:120],
            )
            return "A child in an adventure scene."

        # Türkçe placeholder kontrolü — kısa placeholder metinleri
        _TURKISH_PLACEHOLDERS = [
            "kapak için", "kapak metni", "kısa metin", "hikaye metni",
            "sayfa metni", "başlık", "açıklama",
            "cover text placeholder",  # Pass-2 örneğinden kopyalanan placeholder
        ]
        scene_lower_check = scene_desc.lower()
        for _tp in _TURKISH_PLACEHOLDERS:
            if _tp in scene_lower_check:
                logger.warning(
                    "Placeholder detected in scene_description, replacing with fallback",
                    original=scene_desc[:120],
                )
                return "A child in an adventure scene."

        # Yaygın Türkçe kelime kontrolü (3+ Türkçe kelime = muhtemelen Türkçe)
        _TURKISH_COMMON = [
            "bir ", "ile ", "için ", "diye ", "gibi ", "ama ", "çok ",
            "dedi", "oldu", "geld", "gitt", "bakt", "koştu", "gördü",
            "fısıldadı", "mırıldandı", "söyledi", "sordu",
        ]
        _tr_word_count = sum(1 for w in _TURKISH_COMMON if w in scene_lower_check)
        if _tr_word_count >= 3:
            logger.warning(
                "Turkish words detected in scene_description (%d matches), replacing",
                _tr_word_count,
                original=scene_desc[:120],
            )
            return "A child in an adventure scene."

        return scene_desc[:800]

    def _compose_visual_prompts(
        self,
        story_response: StoryResponse,
        scenario: Scenario,
        child_name: str,
        child_description: str,
        visual_style: str,
        fixed_outfit: str = "",
        cover_template_en: str = "",
        inner_template_en: str = "",
    ) -> list[FinalPageContent]:
        """
        Compose SCENE-ONLY visual prompts (NO style tokens). Style is injected at image API call only.

        Scenario templates are INPUT-only (for Gemini). visual_prompt = scene + outfit + composition
        (location, scene_description, text space at top/bottom). No 2D/3D/Pixar/Ghibli/Children's book illustration.

        Args:
            story_response: Raw story response with scene_description (no style!)
            scenario: Scenario WITH prompt templates
            child_name: Child's name
            child_description: Full child description
            visual_style: Ignored here; style is applied at image generation (single point).
            fixed_outfit: Consistent clothing for all pages

        Returns:
            List of pages with scene-only visual_prompt (no style tokens)
        """
        if getattr(settings, "book_pipeline_version", "3") == "3":
            raise AIServiceError(
                "Gemini",
                "V2 _compose_visual_prompts is disabled when BOOK_PIPELINE_VERSION=3. Use V3 pipeline only.",
            )
        # =====================================================================
        # STYLE INDEPENDENCE: visual_prompt = scene + outfit + composition ONLY.
        # Style (2D/3D/Pixar/Ghibli/Children's book illustration) is added only
        # at image API call via compose_visual_prompt(..., style_text=request.visual_style).
        # =====================================================================

        location_constraints = getattr(scenario, "location_constraints", "") or ""
        cultural_elements = getattr(scenario, "cultural_elements", None)

        logger.info(
            "[VISUAL] COMPOSE VISUAL PROMPTS - scene-only (no style tokens)",
            scenario_name=scenario.name if scenario else "unknown",
            has_location_constraints=bool(location_constraints),
            has_cultural_elements=bool(cultural_elements),
            fixed_outfit=fixed_outfit,
        )

        # Define location keywords for contamination check
        LOCATION_KEYWORDS: dict[str, list[str]] = {
            "cappadocia": [
                "cappadocia",
                "kapadokya",
                "fairy chimney",
                "peri bacasi",
                "hot air balloon",
            ],
            "istanbul": [
                "istanbul",
                "bosphorus",
                "galata",
                "hagia sophia",
                "ayasofya",
                "blue mosque",
                "sultanahmet",
                "hippodrome",
            ],
            "yerebatan": [
                "basilica cistern",
                "yerebatan",
                "medusa head",
            ],
            "gobeklitepe": ["gobekli tepe", "gobeklitepe", "urfa"],
            "catalhoyuk": ["catalhoyuk", "neolithic", "neolitik", "konya plain"],
            "sumela": ["sumela", "sumela monastery", "altindere", "karadag", "trabzon monastery"],
            "ephesus": ["ephesus", "efes", "celsus", "library of celsus"],
            "kudus": ["jerusalem", "kudus", "dome of the rock", "old city walls", "jerusalem stone"],
            "abusimbel": ["abu simbel", "ramesses", "ramses", "nefertari", "nubian", "lake nasser"],
            "tacmahal": ["taj mahal", "tac mahal", "agra", "mughal", "yamuna"],
            "underwater": ["underwater", "ocean", "coral", "fish", "mermaid"],
            "space": ["space station", "galaxy", "nebula", "asteroid", "spaceship"],
        }

        # Themes sharing a parent city — don't cross-flag each other
        _ISTANBUL_THEMES: set[str] = {"istanbul", "yerebatan", "sultanahmet", "galata"}
        COMPATIBLE_THEMES: dict[str, set[str]] = dict.fromkeys(_ISTANBUL_THEMES, _ISTANBUL_THEMES)

        # Style keywords that should NOT be in scene_description
        STYLE_KEYWORDS = [
            "pixar",
            "disney",
            "ghibli",
            "anime",
            "cartoon",
            "watercolor",
            "illustration",
            "3d render",
            "cel-shaded",
            "storybook",
            "children's book illustration",
        ]

        # Determine scenario theme: prefer DB theme_key, fallback to name-based detection
        scenario_theme = getattr(scenario, "theme_key", None) or None
        if not scenario_theme:
            scenario_lower = scenario.name.lower() if scenario else ""
            if "kapadokya" in scenario_lower or "cappadocia" in scenario_lower:
                scenario_theme = "cappadocia"
            elif "yerebatan" in scenario_lower or "cistern" in scenario_lower:
                scenario_theme = "yerebatan"
            elif "efes" in scenario_lower or "ephesus" in scenario_lower:
                scenario_theme = "ephesus"
            elif "göbeklitepe" in scenario_lower or "gobeklitepe" in scenario_lower:
                scenario_theme = "gobeklitepe"
            elif "çatalhöyük" in scenario_lower or "catalhoyuk" in scenario_lower:
                scenario_theme = "catalhoyuk"
            elif "sümela" in scenario_lower or "sumela" in scenario_lower:
                scenario_theme = "sumela"
            elif "sultanahmet" in scenario_lower:
                scenario_theme = "sultanahmet"
            elif "galata" in scenario_lower:
                scenario_theme = "galata"
            elif "kudüs" in scenario_lower or "kudus" in scenario_lower or "jerusalem" in scenario_lower:
                scenario_theme = "kudus"
            elif "abu simbel" in scenario_lower or "abusimbel" in scenario_lower:
                scenario_theme = "abusimbel"
            elif "tac mahal" in scenario_lower or "tacmahal" in scenario_lower:
                scenario_theme = "tacmahal"
            elif "istanbul" in scenario_lower:
                scenario_theme = "istanbul"
            elif "uzay" in scenario_lower or "space" in scenario_lower:
                scenario_theme = "space"
            elif "deniz" in scenario_lower or "underwater" in scenario_lower:
                scenario_theme = "underwater"

        final_pages = []

        for page in story_response.pages:
            scene_desc = self._sanitize_scene_description(page.scene_description)
            scene_lower = scene_desc.lower()

            # ==================== CONTAMINATION CHECKS ====================
            contamination_flags = []

            # Check 1: Location contamination (wrong scenario elements)
            allowed_themes = COMPATIBLE_THEMES.get(scenario_theme or "", {scenario_theme or ""})
            for theme, keywords in LOCATION_KEYWORDS.items():
                if theme not in allowed_themes:
                    for kw in keywords:
                        if kw in scene_lower:
                            contamination_flags.append(
                                f"LOCATION:{kw.upper()}_IN_{scenario_theme.upper() if scenario_theme else 'UNKNOWN'}"
                            )

            # Check 2: Style leaked into scene_description (should be style-free!)
            for style_kw in STYLE_KEYWORDS:
                if style_kw in scene_lower:
                    contamination_flags.append(f"STYLE_LEAK:{style_kw.upper()}")

            # Check 3: Duplicate scene starters
            if scene_lower.count("a wide-angle") > 1:
                contamination_flags.append("DUPLICATE_SCENE_STARTER")

            if contamination_flags:
                logger.warning(
                    "PROMPT CONTAMINATION DETECTED!",
                    page=page.page_number,
                    scenario=scenario.name if scenario else "unknown",
                    contamination=contamination_flags,
                    scene_preview=scene_desc[:150],
                )

            # ==================== COMPOSE FINAL PROMPT ====================
            # SINGLE SOURCE OF TRUTH: Use scenario templates OR fallback
            is_cover = page.page_number == 0

            # Build cultural background hint if available
            cultural_hint = ""
            if cultural_elements:
                primary = cultural_elements.get("primary", [])
                if primary:
                    cultural_hint = f" Background elements: {', '.join(primary[:3])}."

            from app.prompt_engine import compose_visual_prompt
            from app.prompt_engine.constants import (
                DEFAULT_COVER_TEMPLATE_EN,
                DEFAULT_INNER_TEMPLATE_EN,
            )

            location_en = getattr(scenario, "location_en", None) or ""
            scene_text = (scene_desc + cultural_hint).strip()
            if location_en:
                scene_text = f"{location_en} setting. {scene_text}".strip()

            # ── Kapak sayfası: İç sayfayla AYNI yapıda template kullan ──
            # Senaryo cover_prompt_template'leri farklı yapıda (uzun/epik) olduğu
            # için kapak-iç sayfa tutarsızlığına neden oluyordu. Artık kapak da
            # DEFAULT_COVER_TEMPLATE_EN kullanır: "A young child wearing ... {scene_description}."
            # COMPOSITION_RULES normalize_safe_area_and_composition tarafından eklenir.
            if is_cover:
                template_en = cover_template_en or DEFAULT_COVER_TEMPLATE_EN
                logger.info(
                    "Using unified cover template (same structure as inner pages)",
                    source="db_param" if cover_template_en else "default_constant",
                )
            else:
                # Senaryo page_prompt_template varsa iç sayfalar için kullan
                _scenario_page_tpl = (
                    getattr(scenario, "page_prompt_template", None) or ""
                ).strip()
                if (
                    _scenario_page_tpl
                    and "{scene_description}" in _scenario_page_tpl
                    and len(_scenario_page_tpl) < 500
                ):
                    # Sadece kisa/hafif template'ler compose_visual_prompt ile uyumlu.
                    # Agir template'ler (1500+ char) kendi COMPOSITION/STYLE bolumleri
                    # iceriyor ve composer ile cifte sarma + uzunluk asimi yapiyorlar.
                    template_en = _scenario_page_tpl.replace("{visual_style}", "")
                    logger.info(
                        "Using scenario page_prompt_template for inner page",
                        scenario=scenario.name if scenario else "?",
                        template_preview=template_en[:120],
                    )
                else:
                    template_en = inner_template_en or DEFAULT_INNER_TEMPLATE_EN

            visual_prompt, _ = compose_visual_prompt(
                scene_description=scene_text,
                is_cover=is_cover,
                template_en=template_en,
                clothing_description=fixed_outfit,
                story_title=story_response.title if is_cover else "",
            )
            if self._is_visual_prompt_contaminated(visual_prompt):
                logger.warning(
                    "[VISUAL] visual_prompt contaminated after build - using minimal safe prompt",
                    page=page.page_number,
                )
                visual_prompt, _ = compose_visual_prompt(
                    scene_description="A child in an adventure scene.",
                    is_cover=is_cover,
                    template_en=template_en,
                    clothing_description=fixed_outfit,
                    story_title=story_response.title if is_cover else "",
                )

            # ==================== ENFORCE LOCATION CONSTRAINTS ====================
            if location_constraints:
                # Check if location is already in prompt
                loc_lower = location_constraints.lower()
                prompt_lower = visual_prompt.lower()
                # Only inject if missing (check first few words of constraint)
                loc_keywords = [w.strip() for w in loc_lower.split(",")[:2] if len(w.strip()) > 3]
                missing_loc = not any(kw in prompt_lower for kw in loc_keywords)
                if missing_loc:
                    # Truncate long constraints to avoid drowning clothing tokens
                    loc_short = (
                        location_constraints[:200].rsplit(" ", 1)[0]
                        if len(location_constraints) > 200
                        else location_constraints
                    )
                    visual_prompt = f"{visual_prompt} Setting: {loc_short}."
                    logger.info(f"ğŸ“ INJECTED location_constraints into page {page.page_number}")

            # Determine page metadata: cover vs inner
            is_cover_page = page.page_number == 0
            current_page_index = len(final_pages)  # 0-based position in book
            story_pn: int | None = None if is_cover_page else page.page_number

            # Create final page content (scene-only; no style tokens)
            final_pages.append(
                FinalPageContent(
                    page_number=page.page_number,
                    text=page.text,
                    scene_description=scene_desc,
                    visual_prompt=visual_prompt,  # Scene-only: style added at image API
                    page_type="cover" if is_cover_page else "inner",
                    page_index=current_page_index,
                    story_page_number=story_pn,
                    composer_version="v3",
                    pipeline_version="v3",
                )
            )

            logger.info(
                "PROMPT COMPOSED (scene-only)",
                page=page.page_number,
                page_type="cover" if is_cover_page else "inner",
                page_index=current_page_index,
                story_page_number=story_pn,
                pipeline_version="v3",
                scene_preview=scene_desc[:80] + "...",
                final_length=len(visual_prompt),
                contamination=contamination_flags if contamination_flags else "CLEAN",
            )


        return final_pages

    # =========================================================================
    # V3: BLUEPRINT PIPELINE — 2-pass with structured blueprint
    # =========================================================================


"""Learning-outcome helpers for story generation.

Extracted from _story_writer.py.  Provides _LearningOutcomesMixin, which is
inherited by _StoryWriterMixin → GeminiService.

Module-level constants FALLBACK_KEYWORDS / FALLBACK_VISUAL_HINTS are kept
as class attributes on _LearningOutcomesMixin for backward compatibility.
"""

from __future__ import annotations

import structlog
from app.services.ai._helpers import (
    DEFAULT_EDUCATIONAL_VALUES,
    EDUCATIONAL_VALUE_PROMPTS,
)

logger = structlog.get_logger()

# Hardcoded fallback keywords — used when DB keywords_tr/keywords_en are empty
FALLBACK_KEYWORDS: dict[str, list[str]] = {
    "diş fırçalama": ["brush", "toothbrush", "teeth", "diş", "fırça", "fırçalama"],
    "paylaşma": ["paylaş", "share", "birlikte", "together", "paylaşma"],
    "sabır": ["sabır", "patience", "bekle", "wait", "sabırlı", "patient"],
    "cesaret": ["cesaret", "courage", "brave", "korku", "cesur", "fear"],
    "temizlik": ["temiz", "clean", "yıka", "wash", "temizlik", "cleaning"],
    "özür dileme": ["özür", "sorry", "apologize", "af", "affet", "forgive"],
    "sorumluluk": ["sorumluluk", "responsibility", "sorumlu", "responsible", "görev"],
    "empati": ["empati", "empathy", "anlayış", "hisset", "compassion"],
    "doğa sevgisi": ["doğa", "nature", "ağaç", "tree", "çiçek", "flower", "bitki"],
    "yardımlaşma": ["yardım", "help", "yardımlaş", "helping", "yardımsever"],
}


# Hardcoded fallback visual hints — used when DB visual_hints_en is empty
FALLBACK_VISUAL_HINTS: dict[str, list[str]] = {
    "diş fırçalama": ["toothbrush", "tooth-brushing moment", "brushing teeth"],
    "paylaşma": ["sharing toys", "sharing food", "giving to friend"],
    "sabır": ["waiting patiently", "calm expression"],
    "cesaret": ["brave stance", "overcoming fear"],
    "temizlik": ["washing hands", "cleaning up"],
    "özür dileme": ["apologizing to friend", "saying sorry"],
    "sorumluluk": ["taking care of pet", "doing chores"],
    "empati": ["comforting friend", "showing kindness"],
    "doğa sevgisi": ["planting tree", "caring for nature"],
    "yardımlaşma": ["helping others", "lending a hand"],
}



class _LearningOutcomesMixin:
    """Mixin providing learning-outcome helpers."""

    # Class-level aliases kept for backward-compat (self._FALLBACK_KEYWORDS)
    _FALLBACK_KEYWORDS = FALLBACK_KEYWORDS
    _FALLBACK_VISUAL_HINTS = FALLBACK_VISUAL_HINTS
    @staticmethod
    def _get_learning_outcome_keywords(outcomes: list) -> list[str]:
        """Derive search keywords from outcome names for story validation.

        Priority: DB keywords_tr/keywords_en fields > hardcoded fallback dictionary.
        """
        keywords: list[str] = []
        for outcome in outcomes:
            # 1. Try DB fields first
            db_keywords_tr = getattr(outcome, "keywords_tr", None) or ""
            db_keywords_en = getattr(outcome, "keywords_en", None) or ""
            if db_keywords_tr:
                keywords.extend([k.strip() for k in db_keywords_tr.split(",") if k.strip()])
            if db_keywords_en:
                keywords.extend([k.strip() for k in db_keywords_en.split(",") if k.strip()])
            # 2. Fallback: hardcoded dictionary (match by partial name)
            if not db_keywords_tr and not db_keywords_en:
                name = (getattr(outcome, "name", None) or str(outcome)).lower()
                for key, vals in FALLBACK_KEYWORDS.items():
                    if key in name or any(k in name for k in key.split()):
                        keywords.extend(vals)
                        break
        return list(dict.fromkeys(keywords))  # dedupe, preserve order

    @staticmethod
    def _get_learning_outcome_visual_hints(outcomes: list) -> list[str]:
        """Visual hints for image prompts — at least one scene should visualise the outcome.

        Priority: DB visual_hints_en field > hardcoded fallback dictionary.
        """
        hints: list[str] = []
        for outcome in outcomes:
            # 1. Try DB field first
            db_hints = getattr(outcome, "visual_hints_en", None) or ""
            if db_hints:
                hints.extend([h.strip() for h in db_hints.split(",") if h.strip()])
            else:
                # 2. Fallback: hardcoded dictionary
                name = (getattr(outcome, "name", None) or str(outcome)).lower()
                for key, vals in FALLBACK_VISUAL_HINTS.items():
                    if key in name or any(k in name for k in key.split()):
                        hints.extend(vals)
                        break
        return list(dict.fromkeys(hints))

    @staticmethod
    def _story_reflects_learning_outcomes(
        story_text: str,
        keywords: list[str],
        min_occurrences: int = 2,
    ) -> bool:
        """True if story text contains learning-outcome keywords at least min_occurrences times (case-insensitive)."""
        if not keywords:
            return True
        text_lower = story_text.lower()
        total = sum(text_lower.count(kw.lower()) for kw in keywords)
        return total >= min_occurrences

    async def _build_educational_prompt_dynamic(self, outcomes: list) -> str:
        """
        Build educational values prompt with dynamic DB lookup.

        This async version fetches individual educational value prompts from the
        database, allowing admins to modify educational value instructions without
        code changes.

        Falls back to the hardcoded EDUCATIONAL_VALUE_PROMPTS dictionary if:
        - No database session is available
        - The prompt is not found in the database

        Args:
            outcomes: List of outcome objects (with name attribute) or strings

        Returns:
            Formatted prompt section for educational values
        """
        if not outcomes:
            outcomes = DEFAULT_EDUCATIONAL_VALUES

        value_sections = []

        for outcome in outcomes:
            # Get the value name/key
            if hasattr(outcome, "name"):
                value_name = outcome.name.lower().strip()
                # Prefer ai_prompt (verbatim) so learning outcome is enforced
                if hasattr(outcome, "ai_prompt_instruction") and outcome.ai_prompt_instruction:
                    value_sections.append(f"ğŸ“Œ {outcome.ai_prompt_instruction}")
                    continue
                elif hasattr(outcome, "ai_prompt") and outcome.ai_prompt:
                    value_sections.append(f"ğŸ“Œ {outcome.ai_prompt}")
                    continue
            else:
                value_name = str(outcome).lower().strip()

            # Try to normalize the key (remove diacritics for DB lookup)
            normalized_key = (
                value_name.replace("ş", "s")
                .replace("ı", "i")
                .replace("ö", "o")
                .replace("ü", "u")
                .replace("ğ", "g")
                .replace("ç", "c")
            )

            # Try DB lookup first
            db_prompt_key = f"EDUCATIONAL_{normalized_key}"
            db_prompt = await self._get_prompt(db_prompt_key, "")

            if db_prompt:
                value_sections.append(db_prompt)
                continue

            # Fall back to hardcoded dictionary
            matched = False
            for key, data in EDUCATIONAL_VALUE_PROMPTS.items():
                if key in value_name or value_name in key:
                    value_sections.append(f"""
ğŸ“Œ {data["theme"]}:
{data["instruction"]}
""")
                    matched = True
                    break

            # Fallback for unmatched values
            if not matched:
                value_sections.append(f"""
ğŸ“Œ {value_name.upper()}:
Bu değer hikayenin ANA TEMASINI oluşturmalı!
Çocuk bu değeri YAÅAYARAK öğrenmeli - sadece söz olarak değil, eylem olarak!
""")

        if not value_sections:
            # Ultimate fallback
            value_sections = [
                """
ğŸ“Œ MERAK VE KEÅİF:
Çocuk dünyayı keşfetmenin heyecanını yaşamalı!
Her köşede yeni bir sürpriz, her adımda yeni bir öğrenim fırsatı.
"""
            ]

        return "\n".join(value_sections)

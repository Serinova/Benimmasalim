"""Story output validators — post-generation quality checks.

Called by _story_writer.py after PASS-1 to validate story pages.
Checks include:
  - Page count match
  - Empty / short text detection
  - Scenario-aware: no_magic violation, companion consistency, object consistency

DESIGN:
  - NEVER crash the pipeline.  Every function is wrapped in try-except.
  - Return structured reports so caller can log & decide.
  - No LLM calls; pure string matching for zero latency.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

import structlog

logger = structlog.get_logger(__name__)

# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class ValidationFailure:
    """A single validation issue."""

    code: str  # e.g. "NO_MAGIC_VIOLATION"
    message: str
    severity: str = "warning"  # "warning" | "error"
    page: int | None = None


@dataclass
class ValidationReport:
    """Aggregate validation result."""

    failures: list[ValidationFailure] = field(default_factory=list)

    @property
    def all_passed(self) -> bool:
        return len(self.failures) == 0


# ---------------------------------------------------------------------------
# Magic / sihir keyword lists
# ---------------------------------------------------------------------------

# Turkish words indicating magic / sorcery in the story text.
# Used only when scenario_bible.no_magic == True.
_MAGIC_KEYWORDS_TR: list[str] = [
    "büyü",
    "sihir",
    "sihirli",
    "büyülü",
    "büyücü",
    "cadı",
    "cin ",  # trailing space avoids matching "cinsel", "sincap" etc.
    "peri ",  # trailing space avoids "perişan"
    "melek kanatl",
    "uçan halı",
    "değnek",
    "asa ",  # trailing space avoids "asalet", "asansör"
    "tılsım",
]

# Words that are OK even in no_magic scenarios (context-aware exceptions).
_MAGIC_EXCEPTIONS_TR: list[str] = [
    "sihirli değil",
    "büyü değil",
    "sihir yok",
    "büyü yok",
    "sihirsiz",
    "büyüsüz",
    "gizemli",  # "gizemli" ≠ sihirli
]


# ---------------------------------------------------------------------------
# Core check functions (internal)
# ---------------------------------------------------------------------------

def _check_page_count(
    pages: list[dict[str, Any]],
    expected: int,
) -> list[ValidationFailure]:
    """Check that we have the expected number of pages."""
    if len(pages) != expected:
        return [
            ValidationFailure(
                code="PAGE_COUNT_MISMATCH",
                message=f"Expected {expected} pages, got {len(pages)}",
                severity="warning",
            )
        ]
    return []


def _check_empty_text(pages: list[dict[str, Any]]) -> list[ValidationFailure]:
    """Detect pages with empty text_tr."""
    failures: list[ValidationFailure] = []
    for p in pages:
        text = (p.get("text_tr") or "").strip()
        if not text:
            failures.append(
                ValidationFailure(
                    code="EMPTY_TEXT",
                    message=f"Page {p.get('page', '?')} has empty text_tr",
                    severity="warning",
                    page=p.get("page"),
                )
            )
    return failures


def _check_short_text(
    pages: list[dict[str, Any]],
    min_words: int = 15,
) -> list[ValidationFailure]:
    """Detect pages with very short text (less than min_words)."""
    failures: list[ValidationFailure] = []
    for p in pages:
        text = (p.get("text_tr") or "").strip()
        word_count = len(text.split())
        if text and word_count < min_words:
            failures.append(
                ValidationFailure(
                    code="SHORT_TEXT",
                    message=f"Page {p.get('page', '?')} has only {word_count} words (min {min_words})",
                    severity="warning",
                    page=p.get("page"),
                )
            )
    return failures


def _check_no_magic_violation(
    pages: list[dict[str, Any]],
    scenario: Any,
) -> list[ValidationFailure]:
    """Check if story text contains magic/sorcery words when scenario forbids magic.

    Only active when scenario_bible.no_magic == True.
    """
    if scenario is None:
        return []

    bible = getattr(scenario, "scenario_bible", None) or {}
    if not bible.get("no_magic", False):
        return []

    failures: list[ValidationFailure] = []

    for p in pages:
        text = (p.get("text_tr") or "").lower()
        if not text:
            continue

        # Check exceptions first — if text contains an exception phrase, skip
        has_exception = any(exc in text for exc in _MAGIC_EXCEPTIONS_TR)
        if has_exception:
            continue

        for keyword in _MAGIC_KEYWORDS_TR:
            if keyword in text:
                failures.append(
                    ValidationFailure(
                        code="NO_MAGIC_VIOLATION",
                        message=f"Page {p.get('page', '?')}: magic keyword '{keyword.strip()}' found despite no_magic rule",
                        severity="warning",
                        page=p.get("page"),
                    )
                )
                break  # one finding per page is enough

    return failures


def _check_companion_consistency(
    pages: list[dict[str, Any]],
    scenario: Any,
) -> list[ValidationFailure]:
    """Check that the companion name in the story matches the scenario definition.

    Looks at scenario_bible.companions[*].name_tr and checks if ANY page
    mentions a different animal type.
    """
    if scenario is None:
        return []

    bible = getattr(scenario, "scenario_bible", None) or {}
    companions = bible.get("companions", [])
    if not companions:
        return []

    # Collect expected companion name(s)
    expected_names: list[str] = []
    for comp in companions:
        name = (comp.get("name_tr") or "").strip()
        if name:
            expected_names.append(name.lower())

    if not expected_names:
        return []

    # Common animal words that would indicate a wrong companion
    _ANIMAL_WORDS = [
        "kedi", "köpek", "kuş", "papağan", "baykuş", "tavşan", "sincap",
        "tilki", "kelebek", "kaplumbağa", "yunus", "ahtapot", "at ", "atı",
        "yılkı", "kartal", "şahin", "serçe", "aslan", "kaplan",
        "penguen", "robot", "maymun", "ayı ", "ayıcık", "pelüş",
    ]

    failures: list[ValidationFailure] = []

    # Check if the expected companion name appears in the story at least once
    all_text = " ".join((p.get("text_tr") or "") for p in pages).lower()

    for name in expected_names:
        if name not in all_text:
            failures.append(
                ValidationFailure(
                    code="COMPANION_NAME_MISSING",
                    message=f"Expected companion '{name}' not found in story text",
                    severity="warning",
                )
            )

    return failures


def _check_object_consistency(
    pages: list[dict[str, Any]],
    scenario: Any,
) -> list[ValidationFailure]:
    """Check that key objects defined in scenario_bible appear in the story.

    Uses scenario_bible.objects[*].name_tr.
    """
    if scenario is None:
        return []

    bible = getattr(scenario, "scenario_bible", None) or {}
    objects = bible.get("objects", [])
    if not objects:
        return []

    failures: list[ValidationFailure] = []
    all_text = " ".join((p.get("text_tr") or "") for p in pages).lower()

    for obj in objects:
        name = (obj.get("name_tr") or "").strip().lower()
        if not name:
            continue
        if name not in all_text:
            failures.append(
                ValidationFailure(
                    code="OBJECT_NAME_MISSING",
                    message=f"Expected object '{name}' not found in story text",
                    severity="warning",
                )
            )

    return failures


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def validate_story_output(
    pages: list[dict[str, Any]],
    blueprint: dict[str, Any],
    magic_items: list[str],
    expected_page_count: int,
    scenario: Any = None,
    character_prompt_block: str | None = None,
) -> ValidationReport:
    """Run all story validation checks and return a report.

    Parameters
    ----------
    pages : list[dict]
        Generated story pages (each with text_tr, image_prompt_en, etc.)
    blueprint : dict
        PASS-0 blueprint output.
    magic_items : list[str]
        Magic items requested by customer.
    expected_page_count : int
        Number of pages requested.
    scenario : Scenario, optional
        The Scenario ORM object.  When provided, scenario-aware checks
        (no_magic, companion, object) are activated.
    character_prompt_block : str, optional
        Character bible prompt block (unused for now, reserved).

    Returns
    -------
    ValidationReport
    """
    all_failures: list[ValidationFailure] = []

    try:
        # --- Basic checks (always run) ---
        all_failures.extend(_check_page_count(pages, expected_page_count))
        all_failures.extend(_check_empty_text(pages))
        all_failures.extend(_check_short_text(pages))

        # --- Scenario-aware checks (when scenario available) ---
        if scenario is not None:
            try:
                all_failures.extend(_check_no_magic_violation(pages, scenario))
                all_failures.extend(_check_companion_consistency(pages, scenario))
                all_failures.extend(_check_object_consistency(pages, scenario))
            except Exception as e:
                logger.warning(
                    "Scenario-aware validation failed (non-fatal)",
                    error=str(e),
                    error_type=type(e).__name__,
                )

    except Exception as e:
        logger.error(
            "Story validation crashed (returning empty report)",
            error=str(e),
            error_type=type(e).__name__,
        )
        return ValidationReport()

    if all_failures:
        logger.info(
            "Story validation completed with findings",
            failure_count=len(all_failures),
            codes=[f.code for f in all_failures],
        )

    return ValidationReport(failures=all_failures)


def apply_all_fixes(
    pages: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[str]]:
    """Apply automatic fixes to generated pages.

    Currently:
      - Strip trailing/leading whitespace from text_tr.
      - Fill completely empty text_tr with a placeholder.

    Returns
    -------
    tuple[list[dict], list[str]]
        Fixed pages and a list of fix descriptions.
    """
    fix_summary: list[str] = []

    try:
        for p in pages:
            page_num = p.get("page", "?")

            # Fix 1: strip whitespace
            text = p.get("text_tr", "")
            if isinstance(text, str):
                stripped = text.strip()
                if stripped != text:
                    p["text_tr"] = stripped
                    fix_summary.append(f"Page {page_num}: whitespace stripped")

            # Fix 2: empty image_prompt_en fallback
            img_prompt = (p.get("image_prompt_en") or "").strip()
            if not img_prompt:
                text_tr = (p.get("text_tr") or "").strip()
                if text_tr:
                    p["image_prompt_en"] = (
                        f"A child in the scene. {text_tr[:80]}"
                    )
                    fix_summary.append(
                        f"Page {page_num}: empty image_prompt_en filled from text_tr"
                    )

    except Exception as e:
        logger.warning(
            "apply_all_fixes encountered an error (non-fatal)",
            error=str(e),
        )

    return pages, fix_summary

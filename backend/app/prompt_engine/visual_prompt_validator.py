"""Visual prompt validator — stub module.

Provides the validate_all() and autofix() functions expected by
_story_writer.py (line 475-477).  Currently a pass-through stub;
location-aware visual checks will be added in Step 3.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class VisualValidationReport:
    """Result of visual prompt validation."""

    passed: bool = True
    failures: list[dict[str, Any]] = field(default_factory=list)
    auto_fixed: list[dict[str, Any]] = field(default_factory=list)


def validate_all(
    pages: list[dict[str, Any]],
    character_bible: Any,
    style_mapping: dict[str, Any],
) -> VisualValidationReport:
    """Validate visual prompts across all pages.

    Currently a stub — always returns passed.
    """
    return VisualValidationReport()


def autofix(
    pages: list[dict[str, Any]],
    character_bible: Any,
    style_mapping: dict[str, Any],
    report: VisualValidationReport,
) -> list[dict[str, Any]]:
    """Auto-fix visual prompt issues.

    Currently a stub — returns empty list (no fixes).
    """
    return []

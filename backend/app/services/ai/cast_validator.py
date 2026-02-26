"""Cast validator — conditional, story-driven image quality gate.

Validates generated images against the EXPECTED cast for each page.
Does NOT hard-code "only 1 child" — expected_humans comes from story metadata.

Usage:
    result = await validate_cast(image_url, expected_cast, child_name, companion_name)
    if not result.passed:
        # retry with strengthened prompt
"""

from __future__ import annotations

import structlog
from dataclasses import dataclass, field

logger = structlog.get_logger()


@dataclass
class CastValidationResult:
    passed: bool
    expected_humans: int
    detected_humans: int | None  # None = detection skipped / unavailable
    expected_cast: list[str]
    issues: list[str] = field(default_factory=list)
    retry_hint: str = ""  # Injected into next prompt attempt


def build_cast_block(
    child_name: str,
    child_gender: str,
    expected_cast: list[str],
    companion_name: str = "",
    companion_species: str = "",
    companion_appearance: str = "",
) -> str:
    """Build a CAST ON THIS PAGE block for injection at the TOP of a prompt.

    This is story-driven: expected_cast comes from page metadata, not hard-coded.
    Supports single-child, multi-child, and companion stories.

    Args:
        child_name: Main child's name
        child_gender: "boy" | "girl" | "child"
        expected_cast: List of character names expected on this page
        companion_name: Sidekick name (e.g. "Luna")
        companion_species: Sidekick species (e.g. "owl") — NOT a human
        companion_appearance: Visual description of sidekick

    Returns:
        CAST block string to prepend to prompt
    """
    if not expected_cast:
        expected_cast = [child_name] if child_name else ["the child"]

    cast_list = ", ".join(expected_cast)
    human_chars = [c for c in expected_cast if c.lower() != companion_name.lower()]
    expected_humans = len(human_chars)

    lines: list[str] = [
        f"CAST ON THIS PAGE: {cast_list}",
        "STRICT CAST RULES:",
        "  • Render ONLY the characters listed above — NO bystanders, NO extra children, NO background people.",
    ]

    if expected_humans == 1:
        lines.append(f"  • Exactly ONE human child visible: {human_chars[0]}.")
    elif expected_humans > 1:
        lines.append(f"  • Exactly {expected_humans} human children visible: {', '.join(human_chars)}.")

    if companion_name and companion_species:
        comp_desc = f" ({companion_appearance})" if companion_appearance else ""
        lines.append(
            f"  • {companion_name} is a {companion_species}{comp_desc} — "
            f"an ANIMAL/CREATURE, NEVER humanoid, NEVER a child."
        )

    return "\n".join(lines)


async def validate_cast(
    image_url: str,
    expected_cast: list[str],
    child_name: str,
    companion_name: str = "",
    companion_species: str = "",
    *,
    tolerance: int = 0,
) -> CastValidationResult:
    """Validate image cast against expected story cast.

    Currently uses heuristic validation (no vision API call) — logs for monitoring.
    When a vision detection service is available, plug it in here.

    Args:
        image_url: URL of generated image
        expected_cast: Characters expected on this page (from story metadata)
        child_name: Main child's name
        companion_name: Sidekick name (non-human)
        companion_species: Sidekick species
        tolerance: Allowed deviation in human count (0 = exact match required)

    Returns:
        CastValidationResult with pass/fail and retry hint
    """
    human_chars = [c for c in expected_cast if c.lower() != companion_name.lower()]
    expected_humans = len(human_chars)

    # ── Vision detection (plug in when available) ─────────────────────────────
    # detected_humans = await _detect_human_count(image_url)
    detected_humans = None  # Not yet implemented — monitoring only

    issues: list[str] = []
    retry_hint = ""

    if detected_humans is not None:
        if abs(detected_humans - expected_humans) > tolerance:
            issues.append(
                f"Human count mismatch: expected {expected_humans}, detected {detected_humans}"
            )
            if detected_humans > expected_humans:
                retry_hint = (
                    f"STRICT: Only {expected_humans} human child(ren) allowed. "
                    f"Remove all extra children, bystanders, background figures."
                )
            else:
                retry_hint = (
                    f"Main character {child_name} must be clearly visible in the scene."
                )

    passed = len(issues) == 0

    logger.info(
        "CAST_VALIDATION",
        image_url=image_url[:60] if image_url else "",
        expected_cast=expected_cast,
        expected_humans=expected_humans,
        detected_humans=detected_humans,
        passed=passed,
        issues=issues,
    )

    return CastValidationResult(
        passed=passed,
        expected_humans=expected_humans,
        detected_humans=detected_humans,
        expected_cast=expected_cast,
        issues=issues,
        retry_hint=retry_hint,
    )


def build_retry_prompt_injection(
    attempt: int,
    child_name: str,
    expected_humans: int,
    companion_name: str = "",
    companion_species: str = "",
) -> str:
    """Build escalating prompt injection for retry attempts.

    Attempt 1: Strengthen CAST block
    Attempt 2: Add explicit count + NO OTHER HUMANS
    Attempt 3: Maximum enforcement
    """
    if attempt == 1:
        return (
            f"RETRY ENFORCEMENT: The previous image had too many characters. "
            f"ONLY {expected_humans} human child(ren) allowed in this scene. "
            f"Remove ALL extra children, bystanders, background figures."
        )
    elif attempt == 2:
        extra = ""
        if companion_name and companion_species:
            extra = (
                f" {companion_name} must appear as a {companion_species} ONLY — "
                f"never as a human or child."
            )
        return (
            f"CRITICAL RETRY: Exactly {expected_humans} human child(ren) in frame. "
            f"NO OTHER HUMANS, NO CHILDREN IN BACKGROUND, NO BYSTANDERS.{extra} "
            f"Negative: extra child, second child, background child, crowd."
        )
    else:
        return (
            f"MAXIMUM ENFORCEMENT: {expected_humans} child(ren) ONLY. "
            f"Isolate {child_name} completely — no other human figures anywhere in the image. "
            f"Empty background of people."
        )

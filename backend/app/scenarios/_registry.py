"""Scenario Registry — single source of truth for all scenario content.

Usage::

    from app.scenarios import get_scenario_content, get_companion_map

    content = get_scenario_content("cappadocia")
    companion_map = get_companion_map()
"""

from __future__ import annotations

import structlog

from app.scenarios._base import CompanionAnchor, ScenarioContent

logger = structlog.get_logger()

# ─────────────────────────────────────────────
# REGISTRY — populated by scenario module imports
# ─────────────────────────────────────────────
_REGISTRY: dict[str, ScenarioContent] = {}


def register(scenario: ScenarioContent) -> ScenarioContent:
    """Register a scenario in the global registry. Returns the scenario for chaining."""
    if scenario.theme_key in _REGISTRY:
        logger.warning(
            "SCENARIO_REGISTRY_DUPLICATE",
            theme_key=scenario.theme_key,
            name=scenario.name,
        )
    _REGISTRY[scenario.theme_key] = scenario
    return scenario


def get_scenario_content(theme_key: str) -> ScenarioContent | None:
    """Get scenario content by theme_key. Returns None if not found."""
    return _REGISTRY.get(theme_key)


def get_all_scenarios() -> dict[str, ScenarioContent]:
    """Get all registered scenarios."""
    return dict(_REGISTRY)


def get_all_companions() -> dict[str, CompanionAnchor]:
    """Get all companions across all scenarios, keyed by lowercased Turkish name.

    This replaces the hardcoded ``_TR_TO_EN`` dict in ``_story_blueprint.py``.
    """
    result: dict[str, CompanionAnchor] = {}
    for sc in _REGISTRY.values():
        for comp in sc.companions:
            result[comp.name_tr.lower().strip()] = comp
    return result


def get_companion_map() -> dict[str, dict[str, str]]:
    """Get companion map in the legacy format used by ``generate_book.py``.

    Returns dict like::

        {"cesur yılkı atı": {"name": "Yılkı", "species": "wild horse", "appearance": "..."}}

    This replaces the hardcoded ``_COMPANION_MAP`` dict.
    """
    result: dict[str, dict[str, str]] = {}
    for sc in _REGISTRY.values():
        for comp in sc.companions:
            key = comp.name_tr.lower().strip()
            result[key] = {
                "name": comp.short_name,
                "species": comp.species,
                "appearance": comp.appearance,
            }
    return result


def _load_all_scenarios() -> None:
    """Import all scenario modules to trigger registration."""
    # Import each scenario module — their top-level register() calls populate _REGISTRY
    from app.scenarios import (  # noqa: F401
        abusimbel,
        amazon,
        cappadocia,
        catalhoyuk,
        dinosaur,
        ephesus,
        fairy_tale,
        galata,
        gobeklitepe,
        kudus,
        ocean,
        space,
        sultanahmet,
        sumela,
        toy_world,
        umre,
        yerebatan,
    )

    logger.info("SCENARIO_REGISTRY_LOADED", count=len(_REGISTRY))

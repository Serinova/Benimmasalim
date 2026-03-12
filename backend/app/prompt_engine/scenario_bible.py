"""Backward-compatibility shim for scenario_bible.

Prioritises the Scenario Registry for bible data; falls back to the
DB ``scenario_bible`` JSONB column for scenarios not yet in the registry.
"""

from app.prompt_engine import normalize_location_key_for_anchors  # noqa: F401


def get_scenario_bible(
    location_key: str,
    *,
    db_bible: dict | None = None,
) -> dict | None:
    """Return the scenario bible dict for a given location.

    Resolution order:
      1. Code registry (``app.scenarios``)
      2. DB JSONB column (``db_bible`` parameter)
      3. ``None`` → blueprint prompt builder omits the bible section
    """
    # 1) Try the code registry first
    from app.scenarios import get_scenario_content

    content = get_scenario_content(location_key)
    if content and content.scenario_bible:
        return content.scenario_bible

    # 2) Fall back to DB value
    if db_bible and isinstance(db_bible, dict):
        return db_bible

    return None

"""Backward-compatibility shim for scenario_bible."""

from app.prompt_engine import normalize_location_key_for_anchors  # noqa: F401


def get_scenario_bible(
    location_key: str,
    *,
    db_bible: dict | None = None,
) -> dict | None:
    """Return the scenario bible dict for a given location.

    If the scenario has a ``scenario_bible`` JSONB column in the DB, that
    value is returned directly.  Otherwise ``None`` is returned and the
    blueprint prompt builder will simply omit the bible section.
    """
    if db_bible and isinstance(db_bible, dict):
        return db_bible
    return None

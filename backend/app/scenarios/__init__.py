"""Scenario Registry — Public API.

All scenario content (prompts, outfits, companions, bible) is defined in code
as frozen dataclasses.  Marketing/display fields remain in the DB.

Usage::

    from app.scenarios import get_scenario_content, get_companion_map

    content = get_scenario_content("cappadocia")
    if content:
        print(content.story_prompt_tr)
        print(content.outfit_girl)
"""

from app.scenarios._base import (  # noqa: F401
    CompanionAnchor,
    ObjectAnchor,
    ScenarioContent,
)
from app.scenarios._registry import (  # noqa: F401
    get_all_companions,
    get_all_scenarios,
    get_companion_map,
    get_scenario_content,
    register,
)

# Eagerly load all scenario modules so the registry is fully populated
# before any pipeline code tries to look up companions.
from app.scenarios._registry import _load_all_scenarios as _load

_load()
del _load

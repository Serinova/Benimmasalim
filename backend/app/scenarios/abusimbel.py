"""Abu Simbel — PASİF senaryo. Placeholder.
Bu senaryo henüz aktif değil - temel yapı tutulmakta.
"""

from app.scenarios._base import ScenarioContent
from app.scenarios._registry import register

ABUSIMBEL = register(ScenarioContent(
    theme_key="abusimbel",
    name="Abu Simbel Macerası",
    location_en="Abu Simbel, Egypt",
    default_page_count=22,
    flags={"no_family": True},

    story_prompt_tr="# ABU SİMBEL MACERASI\n\nPasif senaryo — içerik hazırlanacak.",

    cover_prompt_template="",
    page_prompt_template="",

    outfit_girl="EXACTLY the same outfit on every page.",
    outfit_boy="EXACTLY the same outfit on every page.",

    companions=[],
    objects=[],
    cultural_elements={"atmosphere": "Ancient Egyptian, monumental, mysterious"},
    location_constraints="",
    scenario_bible={},
    custom_inputs_schema=[],
))

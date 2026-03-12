"""Yerebatan Sarnıcı — PASİF senaryo. Placeholder.
Bu senaryo henüz aktif değil - temel yapı tutulmakta.
NOT: DB'de theme_key NULL idi — burada "yerebatan" olarak kayıt ediyoruz.
"""

from app.scenarios._base import ScenarioContent
from app.scenarios._registry import register

YEREBATAN = register(ScenarioContent(
    theme_key="yerebatan",
    name="Yerebatan Sarnıcı Macerası",
    location_en="Basilica Cistern, Istanbul",
    default_page_count=22,
    flags={"no_family": False},

    story_prompt_tr="# YEREBATAN SARNICI MACERASI\n\nPasif senaryo — içerik hazırlanacak.",

    cover_prompt_template="",
    page_prompt_template="",

    outfit_girl="EXACTLY the same outfit on every page.",
    outfit_boy="EXACTLY the same outfit on every page.",

    companions=[],
    objects=[],
    cultural_elements={"atmosphere": "Underground, mysterious, water reflections, Ottoman/Byzantine"},
    location_constraints="",
    scenario_bible={},
    custom_inputs_schema=[],
))

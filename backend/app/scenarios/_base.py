"""Core dataclasses for the Scenario Registry.

All scenario content (prompts, outfits, companions, bible) lives here as
frozen, immutable Python objects — no DB round-trips, no admin-panel corruption.
"""

from __future__ import annotations

import warnings
from dataclasses import dataclass, field

# Turkish characters that must NOT appear in English-only fields (Flux AI)
_TR_CHARS = set("çşğüöıÇŞĞÜÖİ")


# ─────────────────────────────────────────────
# COMPANION ANCHOR  (G2-a from Scenario Master Skill)
# ─────────────────────────────────────────────
@dataclass(frozen=True)
class CompanionAnchor:
    """Immutable companion definition with visual consistency anchor.

    Pipeline references:
      - ``_extract_companion_from_pages()``  →  species, appearance
      - ``_resolve_companion_placeholder()`` →  name_tr, name_en
    """

    name_tr: str        # Display name in Turkish — "Cesur Yılkı Atı"
    name_en: str        # English translation — "brave wild Cappadocian horse"
    species: str        # Short species tag — "wild horse"
    appearance: str     # 20-40 word English appearance description for AI prompts
    short_name: str = ""  # Short name used in CAST LOCK — "Yılkı"

    def __post_init__(self) -> None:
        if not self.short_name:
            object.__setattr__(self, "short_name", self.name_tr.split()[-1])


# ─────────────────────────────────────────────
# OBJECT ANCHOR  (G2-b from Scenario Master Skill)
# ─────────────────────────────────────────────
@dataclass(frozen=True)
class ObjectAnchor:
    """Immutable key-object definition for visual consistency.

    Objects that appear across multiple pages (medallion, map, key, etc.)
    must look identical — this anchor ensures that.
    """

    name_tr: str             # "Göktürk Madalyonu"
    appearance_en: str       # Full English visual description
    prompt_suffix: str = ""  # Appended to every page prompt where object appears


# ─────────────────────────────────────────────
# SCENARIO CONTENT  (13-section card from Scenario Master Skill)
# ─────────────────────────────────────────────
@dataclass(frozen=True)
class ScenarioContent:
    """Complete, immutable scenario content definition.

    This replaces the mutable DB columns:
      story_prompt_tr, cover_prompt_template, page_prompt_template,
      outfit_girl, outfit_boy, scenario_bible, cultural_elements,
      custom_inputs_schema, location_constraints, flags, companions, objects.

    Marketing/display fields (thumbnail, rating, badge, …) remain in the DB.
    """

    # ── A: Basic Identity ──
    theme_key: str              # "cappadocia"
    name: str                   # "Kapadokya Macerası"

    # ── B: Technical ──
    location_en: str            # "Cappadocia"
    default_page_count: int     # 22
    flags: dict = field(default_factory=dict)  # {"no_family": True}

    # ── E: Story Prompt (Turkish) — min 400 words ──
    story_prompt_tr: str = ""

    # ── F: Visual Prompt Templates ──
    cover_prompt_template: str = ""
    page_prompt_template: str = ""

    # ── G: Hero Outfits (English) — EXACTLY same on every page ──
    outfit_girl: str = ""
    outfit_boy: str = ""

    # ── G2: Consistency Cards ──
    companions: list[CompanionAnchor] = field(default_factory=list)
    objects: list[ObjectAnchor] = field(default_factory=list)

    # ── H: Cultural Elements ──
    cultural_elements: dict = field(default_factory=dict)

    # ── C/G3: Location Constraints ──
    location_constraints: str = ""

    # ── I: Scenario Bible (JSON) ──
    scenario_bible: dict = field(default_factory=dict)

    # ── J: Custom Inputs Schema ──
    custom_inputs_schema: list[dict] = field(default_factory=list)

    # ── Build-time validation ──

    def __post_init__(self) -> None:
        """Validate scenario content at import time.

        Only raises ValueError for issues that produce genuinely broken output
        (Turkish chars in outfit → Flux AI generates garbage).
        All other issues emit warnings — existing scenarios are NOT broken.
        """
        # HARD ERROR: Turkish chars in outfit fields (Flux needs English)
        for fname in ("outfit_girl", "outfit_boy"):
            val = getattr(self, fname)
            if val and _TR_CHARS.intersection(val):
                found = "".join(sorted(_TR_CHARS.intersection(val)))
                raise ValueError(
                    f"[{self.theme_key}] {fname} contains Turkish characters "
                    f"({found}). Flux AI requires English-only outfit descriptions."
                )

        # SOFT WARNING: Story prompt too short
        if self.story_prompt_tr:
            wc = len(self.story_prompt_tr.split())
            if 0 < wc < 300:
                warnings.warn(
                    f"[{self.theme_key}] story_prompt_tr = {wc} words "
                    f"(minimum 300 recommended)",
                    stacklevel=2,
                )

    # ── Computed helpers ──

    @property
    def has_companion(self) -> bool:
        return len(self.companions) > 0

    @property
    def default_companion(self) -> CompanionAnchor | None:
        """First companion = default selection."""
        return self.companions[0] if self.companions else None

    def get_companion_by_name_tr(self, name_tr: str) -> CompanionAnchor | None:
        """Find companion by Turkish name (case-insensitive)."""
        lower = name_tr.lower().strip()
        for c in self.companions:
            if c.name_tr.lower().strip() == lower:
                return c
        return None

    def build_custom_inputs_for_api(self) -> list[dict]:
        """Build proper {label, value} options for the frontend API."""
        result = []
        for inp in self.custom_inputs_schema:
            item = dict(inp)  # shallow copy
            # Ensure options are {label, value} dicts
            if item.get("type") == "select" and "companion_ref" in item:
                item["options"] = [
                    {"label": c.name_tr, "value": c.name_tr}
                    for c in self.companions
                ]
                del item["companion_ref"]
            result.append(item)
        return result

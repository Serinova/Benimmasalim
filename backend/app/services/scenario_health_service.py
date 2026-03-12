"""Scenario Health Service — scores every registered scenario on content quality.

Pure Python; reads from the Scenario Registry only (no DB access).
Used by admin API to show per-scenario health badges and by CLI tool.

10 checks × 20 points each = 200 max. Grade based on percentage.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from app.scenarios._base import ScenarioContent


# ─────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────

# Turkish characters that must NOT appear in English-only fields
_TR_CHARS = set("çşğüöıÇŞĞÜÖİ")

# Placeholders that the pipeline can resolve automatically
_RESOLVABLE_PLACEHOLDERS = {
    "{child_name}", "{child_age}", "{child_gender}",
    "{clothing_description}", "{animal_friend}", "{animal_friend_en}",
    "{page_count}", "{hair_description}",
}

# Placeholders that the pipeline CANNOT resolve — should not appear
_UNRESOLVABLE_PLACEHOLDERS = {
    "{guide}", "{rehber}", "{companion}", "{helper}",
}

# scenario_bible keys that improve companion/visual consistency
_BIBLE_RECOMMENDED_KEYS = {
    "consistency_rules",
}

# Any of these count as "has locations" in bible
_BIBLE_LOCATION_KEYS = {"locations", "key_locations"}


# ─────────────────────────────────────────────
# Data types
# ─────────────────────────────────────────────

@dataclass
class ScenarioHealthCheck:
    """Single health-check result."""

    name: str       # criterion key, e.g. "story_prompt"
    label: str      # human-readable, e.g. "Hikaye Promptu"
    status: str     # "good" | "warning" | "critical"
    score: int      # 0-20
    max_score: int   # always 20
    message: str    # e.g. "Prompt 650 kelime — iyi"


@dataclass
class ScenarioHealthReport:
    """Aggregate health report for one scenario."""

    theme_key: str
    name: str
    total_score: int          # 0-200
    max_score: int            # 200
    grade: str                # "A" | "B" | "C" | "D" | "F"
    percentage: int           # 0-100
    checks: list[ScenarioHealthCheck] = field(default_factory=list)


# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────

def _word_count(text: str | None) -> int:
    """Return the number of whitespace-separated words."""
    if not text:
        return 0
    return len(text.split())


def _grade_from_percentage(pct: int) -> str:
    if pct >= 90:
        return "A"
    if pct >= 75:
        return "B"
    if pct >= 55:
        return "C"
    if pct >= 35:
        return "D"
    return "F"


# ─────────────────────────────────────────────
# CHECK 1: Story Prompt (unchanged)
# ─────────────────────────────────────────────

def _check_story_prompt(sc: ScenarioContent) -> ScenarioHealthCheck:
    """Check story_prompt_tr length (target ≥400 words)."""
    wc = _word_count(sc.story_prompt_tr)
    if wc >= 400:
        score, status, msg = 20, "good", f"Prompt {wc} kelime — mükemmel"
    elif wc >= 250:
        score, status, msg = 14, "warning", f"Prompt {wc} kelime — 400+ önerilir"
    elif wc >= 100:
        score, status, msg = 8, "warning", f"Prompt {wc} kelime — çok kısa"
    elif wc > 0:
        score, status, msg = 4, "critical", f"Prompt yalnızca {wc} kelime"
    else:
        score, status, msg = 0, "critical", "story_prompt_tr boş!"
    return ScenarioHealthCheck(
        name="story_prompt", label="Hikaye Promptu",
        status=status, score=score, max_score=20, message=msg,
    )


# ─────────────────────────────────────────────
# CHECK 2: Outfits (unchanged)
# ─────────────────────────────────────────────

def _check_outfits(sc: ScenarioContent) -> ScenarioHealthCheck:
    """Check outfit_girl and outfit_boy are defined."""
    girl_ok = _word_count(sc.outfit_girl) >= 8
    boy_ok = _word_count(sc.outfit_boy) >= 8

    if girl_ok and boy_ok:
        score, status, msg = 20, "good", "Kız ve erkek kıyafetleri tanımlı"
    elif girl_ok or boy_ok:
        missing = "Erkek" if girl_ok else "Kız"
        score, status, msg = 10, "warning", f"{missing} kıyafeti eksik"
    else:
        score, status, msg = 0, "critical", "Kıyafet tanımları boş!"
    return ScenarioHealthCheck(
        name="outfits", label="Kıyafet Tanımları",
        status=status, score=score, max_score=20, message=msg,
    )


# ─────────────────────────────────────────────
# CHECK 3: Companions (unchanged)
# ─────────────────────────────────────────────

def _check_companions(sc: ScenarioContent) -> ScenarioHealthCheck:
    """Check that at least one companion exists with sufficient appearance description."""
    comp_count = len(sc.companions)

    # Some scenarios intentionally have no companion (e.g. Umre)
    if comp_count == 0:
        bible = sc.scenario_bible or {}
        if bible.get("no_companion"):
            return ScenarioHealthCheck(
                name="companions", label="Companion (Yol Arkadaşı)",
                status="good", score=20, max_score=20,
                message="no_companion senaryosu — companion gerekmez",
            )
        return ScenarioHealthCheck(
            name="companions", label="Companion (Yol Arkadaşı)",
            status="critical", score=0, max_score=20,
            message="Hiç companion tanımlı değil!",
        )

    # Check appearance quality
    good_appearances = sum(
        1 for c in sc.companions if _word_count(c.appearance) >= 15
    )
    if good_appearances == comp_count:
        score, status = 20, "good"
        msg = f"{comp_count} companion, hepsi detaylı appearance"
    elif good_appearances > 0:
        score, status = 14, "warning"
        msg = f"{comp_count} companion, {comp_count - good_appearances} tanesi kısa appearance"
    else:
        score, status = 8, "warning"
        msg = f"{comp_count} companion var ama appearance açıklamaları kısa"
    return ScenarioHealthCheck(
        name="companions", label="Companion (Yol Arkadaşı)",
        status=status, score=score, max_score=20, message=msg,
    )


# ─────────────────────────────────────────────
# CHECK 4: Location Constraints (split from old bible check)
# ─────────────────────────────────────────────

def _check_location_constraints(sc: ScenarioContent) -> ScenarioHealthCheck:
    """Check location_constraints are populated and detailed."""
    has_constraints = _word_count(sc.location_constraints) >= 10

    if has_constraints:
        wc = _word_count(sc.location_constraints)
        if wc >= 50:
            score, status, msg = 20, "good", f"location_constraints detaylı ({wc} kelime)"
        else:
            score, status, msg = 14, "warning", f"location_constraints kısa ({wc} kelime)"
    else:
        score, status, msg = 0, "critical", "location_constraints eksik/boş!"
    return ScenarioHealthCheck(
        name="location_constraints", label="Lokasyon Kısıtları",
        status=status, score=score, max_score=20, message=msg,
    )


# ─────────────────────────────────────────────
# CHECK 5: Visual Prompts (unchanged)
# ─────────────────────────────────────────────

def _check_visual_prompts(sc: ScenarioContent) -> ScenarioHealthCheck:
    """Check cover_prompt_template and page_prompt_template quality."""
    cover_wc = _word_count(sc.cover_prompt_template)
    page_wc = _word_count(sc.page_prompt_template)

    cover_ok = cover_wc >= 30
    page_ok = page_wc >= 30

    if cover_ok and page_ok:
        score, status = 20, "good"
        msg = f"Cover ({cover_wc} kelime) + Page ({page_wc} kelime) — iyi"
    elif cover_ok or page_ok:
        missing = "page_prompt" if cover_ok else "cover_prompt"
        score, status = 10, "warning"
        msg = f"{missing}_template kısa veya boş"
    else:
        score, status = 0, "critical"
        msg = "Görsel prompt şablonları boş veya çok kısa!"
    return ScenarioHealthCheck(
        name="visual_prompts", label="Görsel Prompt Şablonları",
        status=status, score=score, max_score=20, message=msg,
    )


# ─────────────────────────────────────────────
# CHECK 6: Bible Required Keys (NEW)
# ─────────────────────────────────────────────

def _check_bible_keys(sc: ScenarioContent) -> ScenarioHealthCheck:
    """Check scenario_bible has recommended keys for consistency."""
    bible = sc.scenario_bible or {}

    if not bible:
        return ScenarioHealthCheck(
            name="bible_keys", label="Scenario Bible İçeriği",
            status="critical", score=0, max_score=20,
            message="scenario_bible tamamen boş!",
        )

    # Check for companion info
    has_companion_info = bool(bible.get("companions") or bible.get("no_companion"))

    # Check for recommended keys
    found_recommended = sum(1 for k in _BIBLE_RECOMMENDED_KEYS if k in bible)
    total_recommended = len(_BIBLE_RECOMMENDED_KEYS)

    # Check for locations (accepts multiple key names)
    has_locations = any(k in bible for k in _BIBLE_LOCATION_KEYS)

    all_ok = has_companion_info and found_recommended == total_recommended and has_locations
    if all_ok:
        score, status = 20, "good"
        msg = "Bible alanları tam — companion, locations, consistency_rules"
    elif has_companion_info and found_recommended == total_recommended:
        if not has_locations:
            score, status = 16, "warning"
            msg = "Bible'da locations/key_locations eksik"
        else:
            score, status = 20, "good"
            msg = "Bible alanları tam"
    elif has_companion_info and found_recommended > 0:
        missing = [k for k in _BIBLE_RECOMMENDED_KEYS if k not in bible]
        if not has_locations:
            missing.append("locations")
        score, status = 14, "warning"
        msg = f"Bible eksik key: {', '.join(missing)}"
    elif has_companion_info:
        score, status = 10, "warning"
        msg = "Bible'da consistency_rules/locations eksik"
    else:
        score, status = 6, "warning"
        msg = f"Bible'da companion bilgisi yok (key sayısı: {len(bible)})"
    return ScenarioHealthCheck(
        name="bible_keys", label="Scenario Bible İçeriği",
        status=status, score=score, max_score=20, message=msg,
    )


# ─────────────────────────────────────────────
# CHECK 7: Custom Inputs Schema (NEW)
# ─────────────────────────────────────────────

def _check_custom_inputs(sc: ScenarioContent) -> ScenarioHealthCheck:
    """Check custom_inputs_schema format for companion binding."""
    schema = sc.custom_inputs_schema or []
    has_companions = len(sc.companions) > 0

    # If no companion, no custom_inputs needed
    if not has_companions:
        return ScenarioHealthCheck(
            name="custom_inputs", label="Custom Inputs Schema",
            status="good", score=20, max_score=20,
            message="Companion yok — custom_inputs gerekmez",
        )

    # Find animal_friend entry
    animal_entry = next(
        (e for e in schema if e.get("key") == "animal_friend"), None
    )

    if not animal_entry:
        return ScenarioHealthCheck(
            name="custom_inputs", label="Custom Inputs Schema",
            status="critical", score=0, max_score=20,
            message="Companion var ama custom_inputs'ta 'animal_friend' key'i yok!",
        )

    # Check type
    inp_type = animal_entry.get("type", "")
    has_default = bool(animal_entry.get("default"))
    type_ok = inp_type in ("hidden", "select")

    if type_ok and has_default:
        score, status = 20, "good"
        msg = f"animal_friend: type={inp_type}, default dolu — ✓"
    elif type_ok:
        score, status = 10, "warning"
        msg = f"animal_friend: type={inp_type} ama default boş!"
    else:
        score, status = 6, "warning"
        msg = f"animal_friend: type='{inp_type}' — hidden/select olmalı"
    return ScenarioHealthCheck(
        name="custom_inputs", label="Custom Inputs Schema",
        status=status, score=score, max_score=20, message=msg,
    )


# ─────────────────────────────────────────────
# CHECK 8: Turkish Characters in Outfits (NEW)
# ─────────────────────────────────────────────

def _check_turkish_chars(sc: ScenarioContent) -> ScenarioHealthCheck:
    """Check that outfit fields don't contain Turkish characters (Flux needs English)."""
    problems = []
    for field_name in ("outfit_girl", "outfit_boy"):
        val = getattr(sc, field_name, "") or ""
        found = _TR_CHARS.intersection(val)
        if found:
            problems.append(f"{field_name}: {''.join(sorted(found))}")

    if not problems:
        score, status = 20, "good"
        msg = "Kıyafet tanımları İngilizce — ✓"
    else:
        score, status = 0, "critical"
        msg = f"Türkçe karakter! {'; '.join(problems)}"
    return ScenarioHealthCheck(
        name="turkish_chars", label="Kıyafet Dil Kontrolü",
        status=status, score=score, max_score=20, message=msg,
    )


# ─────────────────────────────────────────────
# CHECK 9: Object Anchors (NEW)
# ─────────────────────────────────────────────

def _check_objects(sc: ScenarioContent) -> ScenarioHealthCheck:
    """Check ObjectAnchor list — at least 1 recommended for visual consistency."""
    obj_count = len(sc.objects)
    has_companions = len(sc.companions) > 0

    # Companion-less scenarios may not need objects
    if not has_companions and obj_count == 0:
        return ScenarioHealthCheck(
            name="objects", label="Obje Anchor'ları",
            status="good", score=20, max_score=20,
            message="Companion yok — obje tanımı opsiyonel",
        )

    if obj_count >= 2:
        score, status, msg = 20, "good", f"{obj_count} obje anchor tanımlı — mükemmel"
    elif obj_count == 1:
        score, status, msg = 16, "good", f"1 obje anchor tanımlı — iyi"
    else:
        score, status, msg = 8, "warning", "Obje anchor yok — önemli objeler için tanım önerilir"
    return ScenarioHealthCheck(
        name="objects", label="Obje Anchor'ları",
        status=status, score=score, max_score=20, message=msg,
    )


# ─────────────────────────────────────────────
# CHECK 10: Unresolvable Placeholders (NEW)
# ─────────────────────────────────────────────

def _check_placeholders(sc: ScenarioContent) -> ScenarioHealthCheck:
    """Check for unresolvable placeholders in story_prompt_tr."""
    prompt = sc.story_prompt_tr or ""
    if not prompt:
        return ScenarioHealthCheck(
            name="placeholders", label="Placeholder Kontrolü",
            status="warning", score=10, max_score=20,
            message="Prompt boş — placeholder kontrolü yapılamadı",
        )

    # Find all {xxx} placeholders
    all_placeholders = set(re.findall(r"\{[a-z_]+\}", prompt))

    # Filter out resolvable ones
    unresolvable = all_placeholders - _RESOLVABLE_PLACEHOLDERS

    # Also check for known bad ones
    known_bad = all_placeholders & _UNRESOLVABLE_PLACEHOLDERS

    if known_bad:
        score, status = 0, "critical"
        msg = f"Çözülemeyen placeholder: {', '.join(sorted(known_bad))}"
    elif unresolvable:
        score, status = 10, "warning"
        msg = f"Bilinmeyen placeholder: {', '.join(sorted(unresolvable))}"
    else:
        score, status = 20, "good"
        msg = "Tüm placeholder'lar çözümlenebilir — ✓"
    return ScenarioHealthCheck(
        name="placeholders", label="Placeholder Kontrolü",
        status=status, score=score, max_score=20, message=msg,
    )


# ─────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────

_ALL_CHECKS = [
    _check_story_prompt,
    _check_outfits,
    _check_companions,
    _check_location_constraints,
    _check_visual_prompts,
    _check_bible_keys,
    _check_custom_inputs,
    _check_turkish_chars,
    _check_objects,
    _check_placeholders,
]


def score_scenario(content: ScenarioContent) -> ScenarioHealthReport:
    """Score a single ScenarioContent and return a health report."""
    checks = [check_fn(content) for check_fn in _ALL_CHECKS]
    total = sum(c.score for c in checks)
    max_score = sum(c.max_score for c in checks)
    pct = round(total * 100 / max_score) if max_score > 0 else 0
    return ScenarioHealthReport(
        theme_key=content.theme_key,
        name=content.name,
        total_score=total,
        max_score=max_score,
        grade=_grade_from_percentage(pct),
        percentage=pct,
        checks=checks,
    )


def get_all_scenario_health() -> list[ScenarioHealthReport]:
    """Score ALL registered scenarios and return sorted reports (worst first)."""
    from app.scenarios import get_all_scenarios

    registry = get_all_scenarios()
    reports = [score_scenario(sc) for sc in registry.values()]
    reports.sort(key=lambda r: r.total_score)
    return reports


def get_health_summary() -> dict:
    """Return aggregate statistics for the dashboard header."""
    reports = get_all_scenario_health()
    if not reports:
        return {"total": 0, "average_score": 0, "grade_counts": {}}

    avg_pct = sum(r.percentage for r in reports) / len(reports)
    grade_counts: dict[str, int] = {}
    for r in reports:
        grade_counts[r.grade] = grade_counts.get(r.grade, 0) + 1

    return {
        "total": len(reports),
        "average_percentage": round(avg_pct, 1),
        "average_grade": _grade_from_percentage(int(avg_pct)),
        "grade_counts": grade_counts,
    }

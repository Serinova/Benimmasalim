"""LLM output repair utilities for PASS-0 (blueprint) and PASS-1 (pages).

Handles:
- Missing / extra pages → trim or pad from nearest beat
- Missing required fields → minimal valid placeholders
- Schema-level fixes (story_arc, act, emotional_state)

Every repair function returns ``(repaired_data, repairs: list[str])``
where ``repairs`` is a human-readable log of what was fixed.
"""

from __future__ import annotations

import json
import logging
import math
import re

logger = logging.getLogger(__name__)

# ─── Constants ────────────────────────────────────────────────────────────────

_DEFAULT_NEGATIVE = (
    "text, watermark, logo, signature, low quality, blurry, "
    "extra limbs, deformed hands, scary horror, gore, violence, "
    "big eyes, chibi, oversized head"
)

_ROLE_EMOTION_MAP: dict[str, str] = {
    "dedication": "heyecanlı",
    "arrival": "meraklı",
    "obstacle": "kararlı",
    "puzzle": "odaklanmış",
    "small_victory": "gururlu",
    "surprise_discovery": "şaşkın",
    "main_discovery": "coşkulu",
    "closure": "mutlu",
    "adventure": "meraklı",
}

_ROLE_ACT_MAP: dict[str, str] = {
    "dedication": "1",
    "arrival": "1",
    "obstacle": "2",
    "puzzle": "2",
    "small_victory": "2",
    "surprise_discovery": "2",
    "main_discovery": "3",
    "closure": "3",
    "adventure": "2",
}


# ─── Enhanced JSON extraction ────────────────────────────────────────────────


def extract_and_repair_json(raw_text: str) -> dict | list:
    """Extract and repair JSON from raw LLM output.

    Improvements over the basic version:
    - Single quotes → double quotes (outside strings)
    - JavaScript-style comments removed
    - Unescaped control characters in strings
    - Better truncation repair (close all open brackets)
    """
    text = raw_text.strip()

    # 1. Extract from markdown code blocks
    json_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
    if json_match:
        text = json_match.group(1).strip()

    # 2. Try direct parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # 3. Remove JS-style comments
    text = re.sub(r"//[^\n]*", "", text)
    text = re.sub(r"/\*[\s\S]*?\*/", "", text)

    # 4. Find JSON boundaries
    arr_idx = text.find("[")
    obj_idx = text.find("{")

    if arr_idx != -1 and (obj_idx == -1 or arr_idx < obj_idx):
        start = arr_idx
    elif obj_idx != -1:
        start = obj_idx
    else:
        raise json.JSONDecodeError("No JSON structure found", text, 0)

    # 5. Find matching close bracket (state-machine tracking bracket stack)
    bracket_stack: list[str] = []
    end = -1
    in_str = False
    esc = False
    _CLOSE_FOR = {"[": "]", "{": "}"}
    for i in range(start, len(text)):
        ch = text[i]
        if esc:
            esc = False
            continue
        if ch == "\\":
            esc = True
            continue
        if ch == '"':
            in_str = not in_str
            continue
        if in_str:
            continue
        if ch in ("[", "{"):
            bracket_stack.append(ch)
        elif ch in ("]", "}"):
            if bracket_stack:
                bracket_stack.pop()
            if not bracket_stack:
                end = i
                break

    if end == -1:
        # Truncated — close all open brackets in reverse order
        text = text[start:]
        suffix = "".join(_CLOSE_FOR.get(b, "}") for b in reversed(bracket_stack))
        text += suffix
        logger.warning("JSON truncated, auto-closing %d brackets", len(bracket_stack))
    else:
        text = text[start : end + 1]

    # 6. Repair passes
    text = re.sub(r",(\s*[}\]])", r"\1", text)  # trailing commas
    text = re.sub(r"(\{|,)\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*:", r'\1"\2":', text)  # unquoted keys

    # Single quotes → double quotes (heuristic: outside already-double-quoted strings)
    text = _fix_single_quotes(text)

    # 7. Parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # 8. Last resort: strip control characters from string values
    text = re.sub(r'(?<=": ")([^"]*?)(?=")', lambda m: m.group(1).replace("\n", " "), text)

    return json.loads(text)  # let it raise if still broken


def _fix_single_quotes(text: str) -> str:
    """Replace single-quoted JSON strings with double-quoted.

    Simple heuristic: only replace if the text has more single-quote pairs
    than double-quote pairs (common LLM mistake).
    """
    if text.count("'") > text.count('"'):
        result: list[str] = []
        in_dq = False
        for ch in text:
            if ch == '"':
                in_dq = not in_dq
                result.append(ch)
            elif ch == "'" and not in_dq:
                result.append('"')
            else:
                result.append(ch)
        return "".join(result)
    return text


# ─── Blueprint (PASS-0) repair ───────────────────────────────────────────────


def repair_blueprint(blueprint: dict, page_count: int) -> tuple[dict, list[str]]:
    """Validate and repair a PASS-0 blueprint dict.

    Returns (repaired_blueprint, list_of_repair_descriptions).
    """
    repairs: list[str] = []

    # story_arc
    if "story_arc" not in blueprint or not isinstance(blueprint.get("story_arc"), dict):
        blueprint["story_arc"] = {
            "setup": "Çocuk lokasyona varır ve macera başlar.",
            "confrontation": "Engeller ve bulmacalarla karşılaşır.",
            "resolution": "Ana keşfi yapar ve eve döner.",
        }
        repairs.append("story_arc placeholder eklendi")

    arc = blueprint["story_arc"]
    for key in ("setup", "confrontation", "resolution"):
        if not arc.get(key):
            arc[key] = f"{key} — hikaye perdesi"
            repairs.append(f"story_arc.{key} placeholder eklendi")

    # pages
    pages: list[dict] = blueprint.get("pages", [])

    # Trim excess
    if len(pages) > page_count:
        pages = pages[:page_count]
        blueprint["pages"] = pages
        repairs.append(f"Fazla sayfalar kırpıldı → {page_count}")

    # Pad missing
    if len(pages) < page_count:
        missing_count = page_count - len(pages)
        for i in range(len(pages), page_count):
            neighbor = pages[-1] if pages else {}
            stub = _make_blueprint_page_stub(i + 1, page_count, neighbor)
            pages.append(stub)
        repairs.append(f"{missing_count} eksik sayfa stub eklendi")

    # Per-page field repair
    for i, page in enumerate(pages):
        pg_num = i + 1
        page["page"] = pg_num

        role = page.get("role", "adventure")
        if not role:
            role = "adventure"
            page["role"] = role

        if "act" not in page or page["act"] not in ("1", "2", "3", 1, 2, 3):
            page["act"] = _infer_act(pg_num, page_count, role)
            repairs.append(f"s{pg_num}: act atandı → {page['act']}")

        # Normalize act to string
        page["act"] = str(page["act"])

        if not page.get("emotional_state"):
            page["emotional_state"] = _ROLE_EMOTION_MAP.get(role, "meraklı")
            repairs.append(f"s{pg_num}: emotional_state → {page['emotional_state']}")

        page.setdefault("scene_goal", "Macera devam ediyor.")
        page.setdefault("conflict_or_question", "")
        page.setdefault("cultural_hook", "")
        page.setdefault("magic_touch", "")
        page.setdefault("visual_brief_tr", "Macera sahnesi")
        page.setdefault("shot_type", "WIDE_FULL_BODY")

    # Validate act distribution — ensure all 3 acts exist
    act_counts = {"1": 0, "2": 0, "3": 0}
    for page in pages:
        act_counts[str(page.get("act", "2"))] += 1

    if act_counts["1"] == 0:
        pages[0]["act"] = "1"
        if len(pages) > 1:
            pages[1]["act"] = "1"
        repairs.append("Perde 1 (giriş) sayfaları atandı")

    if act_counts["3"] == 0 and len(pages) >= 3:
        pages[-1]["act"] = "3"
        pages[-1]["role"] = "closure"
        pages[-2]["act"] = "3"
        pages[-2]["role"] = "main_discovery"
        repairs.append("Perde 3 (sonuç) sayfaları atandı")

    if act_counts["2"] == 0 and len(pages) >= 5:
        for page in pages[2:-2]:
            page["act"] = "2"
        repairs.append("Perde 2 (gelişme) sayfaları atandı")

    blueprint["page_count"] = page_count
    return blueprint, repairs


def _make_blueprint_page_stub(
    page_num: int, total: int, neighbor: dict
) -> dict:
    """Create a minimal blueprint page stub based on position and neighbor."""
    role = _role_for_position(page_num, total)
    act = _infer_act(page_num, total, role)
    return {
        "page": page_num,
        "act": act,
        "role": role,
        "emotional_state": _ROLE_EMOTION_MAP.get(role, "meraklı"),
        "shot_type": "WIDE_FULL_BODY",
        "scene_goal": neighbor.get("scene_goal", "Macera devam ediyor."),
        "conflict_or_question": "",
        "cultural_hook": "",
        "magic_touch": "",
        "visual_brief_tr": neighbor.get("visual_brief_tr", "Macera sahnesi"),
    }


def _role_for_position(page_num: int, total: int) -> str:
    if page_num == 1:
        return "dedication"
    if page_num <= max(2, math.floor(total * 0.12)):
        return "arrival"
    if page_num >= total - max(1, math.floor(total * 0.08)) + 1:
        return "closure" if page_num != total - max(1, math.floor(total * 0.08)) else "main_discovery"
    return "adventure"


def _infer_act(page_num: int, total: int, role: str) -> str:
    """Infer the 3-act number from role or page position."""
    act_from_role = _ROLE_ACT_MAP.get(role)
    if act_from_role:
        return act_from_role
    pct = page_num / total
    if pct <= 0.20:
        return "1"
    if pct <= 0.80:
        return "2"
    return "3"


# ─── Pages (PASS-1) repair ───────────────────────────────────────────────────


def repair_pages(
    pages: list[dict],
    blueprint: dict,
    page_count: int,
    skip_visual_prompts: bool = False,
) -> tuple[list[dict], list[str]]:
    """Validate and repair PASS-1 page output.
    
    Args:
        pages: Raw pages from Gemini
        blueprint: Blueprint JSON
        page_count: Expected page count
        skip_visual_prompts: If True, don't add placeholder image_prompt_en
    
    Returns (repaired_pages, list_of_repair_descriptions).
    """
    repairs: list[str] = []
    bp_pages: list[dict] = blueprint.get("pages", [])

    # Trim excess
    if len(pages) > page_count:
        pages = pages[:page_count]
        repairs.append(f"Fazla sayfalar kırpıldı → {page_count}")

    # Pad missing pages from blueprint beats
    if len(pages) < page_count:
        missing_count = page_count - len(pages)
        for i in range(len(pages), page_count):
            bp_page = bp_pages[i] if i < len(bp_pages) else {}
            stub = _make_page_stub(i + 1, bp_page, skip_visual_prompts)
            pages.append(stub)
        repairs.append(f"{missing_count} eksik sayfa placeholder eklendi")

    # Per-page field repair
    for i, page in enumerate(pages):
        pg_num = i + 1
        page["page"] = pg_num
        bp_page = bp_pages[i] if i < len(bp_pages) else {}

        # text_tr
        if not page.get("text_tr") or len(page["text_tr"].strip()) < 10:
            scene = bp_page.get("scene_goal", "Macera devam ediyor.")
            page["text_tr"] = f"{scene}"
            repairs.append(f"s{pg_num}: text_tr placeholder (scene_goal'den)")

        # image_prompt_en (skip if two-phase generation)
        if not skip_visual_prompts:
            if not page.get("image_prompt_en") or len(page["image_prompt_en"].strip()) < 10:
                brief = bp_page.get("visual_brief_tr", "Adventure scene")
                role = bp_page.get("role", "adventure")
                emotion = bp_page.get("emotional_state", "curious")
                page["image_prompt_en"] = (
                    f"A child in an {role} scene. {brief}. "
                    f"The child looks {emotion}. Warm lighting."
                )
                repairs.append(f"s{pg_num}: image_prompt_en placeholder (visual_brief'ten)")
        else:
            # Two-phase: leave image_prompt_en empty or remove it
            if "image_prompt_en" not in page or not page["image_prompt_en"]:
                page["image_prompt_en"] = ""  # Empty string, will be generated later

        # negative_prompt_en (only if not skip_visual_prompts)
        if not skip_visual_prompts:
            if not page.get("negative_prompt_en") or len(page["negative_prompt_en"].strip()) < 5:
                page["negative_prompt_en"] = _DEFAULT_NEGATIVE
                repairs.append(f"s{pg_num}: negative_prompt_en default eklendi")

    return pages, repairs


def _make_page_stub(page_num: int, bp_page: dict, skip_visual_prompts: bool = False) -> dict:
    """Create a minimal PASS-1 page from a blueprint page entry."""
    scene = bp_page.get("scene_goal", "Macera devam ediyor.")
    stub = {
        "page": page_num,
        "text_tr": scene,
    }
    
    if not skip_visual_prompts:
        brief = bp_page.get("visual_brief_tr", "Adventure scene")
        emotion = bp_page.get("emotional_state", "curious")
        role = bp_page.get("role", "adventure")
        stub["image_prompt_en"] = (
            f"A child in an {role} scene. {brief}. "
            f"The child looks {emotion}. Warm lighting."
        )
        stub["negative_prompt_en"] = _DEFAULT_NEGATIVE
    else:
        stub["image_prompt_en"] = ""  # Empty, will be generated later
        stub["negative_prompt_en"] = ""
    
    return stub

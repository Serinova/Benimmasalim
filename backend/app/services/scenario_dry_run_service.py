"""Scenario Dry-Run Service — runs V3 pipeline WITHOUT image generation.

Wraps the analysis functions from ``scripts/scenario_dry_run.py`` into an
async service callable from the admin API.

Usage::

    result = await run_scenario_dry_run(
        db=db_session,
        theme_key="cappadocia",
        child_name="Yusuf",
        child_age=7,
        child_gender="erkek",
    )
"""

from __future__ import annotations

import re
import time
from collections import Counter
from typing import Any

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.scenario import Scenario

logger = structlog.get_logger()


# ─────────────────────────────────────────────────
# ANALYSIS FUNCTIONS (adapted from scripts/scenario_dry_run.py)
# ─────────────────────────────────────────────────


def _check_content_safety(pages: list[dict]) -> dict:
    """Content safety — forbidden words with word-boundary matching."""
    BANNED_PATTERNS_TR = [
        (r"\böldür", "öldür"), (r"\bsaldır", "saldır"),
        (r"\byıkım\b", "yıkım"), (r"\bvahşet\b", "vahşet"),
        (r"\bşiddet\b", "şiddet"), (r"\bkan\b", "kan"),
    ]
    BANNED_WORDS_EN = [
        "blood", "kill", "attack", "destroy", "violent",
        "sexy", "nude", "naked", "bikini",
        "skin color", "skin tone", "hair color", "eye color",
    ]
    issues: list[dict] = []
    for page in pages:
        text = (page.get("text") or "").lower()
        prompt = (page.get("visual_prompt") or "").lower()
        for pattern, label in BANNED_PATTERNS_TR:
            if re.search(pattern, text):
                issues.append({"page": page.get("page_number"), "severity": "HIGH", "issue": f"Yasaklı kelime: '{label}'"})
        for word in BANNED_WORDS_EN:
            if " " in word:
                found = word in prompt
            else:
                found = bool(re.search(r"\b" + re.escape(word) + r"\b", prompt))
            if found:
                if word == "violent":
                    safe = ["non-violent", "non violent", "violent storm", "violently shak"]
                    if any(ctx in prompt for ctx in safe):
                        continue
                issues.append({"page": page.get("page_number"), "severity": "HIGH", "issue": f"Yasaklı: '{word}'"})
    return {"status": "PASS" if not issues else "FAIL", "issues": issues}


def _check_page_completeness(pages: list[dict], expected: int) -> dict:
    """Page count and short page check."""
    issues: list[dict] = []
    inner = [p for p in pages if p.get("page_type") == "inner"]
    if len(inner) != expected:
        issues.append({"severity": "HIGH", "issue": f"Beklenen {expected} sayfa, üretilen {len(inner)}"})
    short = [p for p in inner if len((p.get("text") or "").strip()) < 30]
    for p in short:
        issues.append({"page": p.get("page_number"), "severity": "HIGH", "issue": "Kısa metin"})
    return {"status": "PASS" if not issues else "FAIL", "issues": issues}


def _analyze_repetition(pages: list[dict]) -> dict:
    inner = [p for p in pages if p.get("page_type") == "inner"]
    openings: list[str] = []
    pattern_counts: dict[str, int] = {}
    for p in inner:
        text = (p.get("text") or "").strip()
        openings.append(" ".join(text.split()[:5]).lower())
        words = text.lower().split()
        for n in range(4, 7):
            for i in range(len(words) - n):
                ngram = " ".join(words[i : i + n])
                pattern_counts[ngram] = pattern_counts.get(ngram, 0) + 1
    repeated = sorted(((k, v) for k, v in pattern_counts.items() if v >= 3), key=lambda x: -x[1])[:5]
    similar = {k: v for k, v in Counter(openings).items() if v >= 3}
    score = 10
    if len(repeated) > 5:
        score -= 3
    elif len(repeated) > 2:
        score -= 1.5
    if similar:
        score -= 1
    return {"score": max(1, round(score, 1)), "repeated_patterns": len(repeated), "similar_openings": len(similar)}


def _analyze_dialogue(pages: list[dict]) -> dict:
    inner = [p for p in pages if p.get("page_type") == "inner"]
    pages_with = 0
    total = 0
    for p in inner:
        dialogues = re.findall(r'[""\u00ab\u00bb\'](.*?)[""\u00ab\u00bb\']', p.get("text", ""))
        if dialogues:
            pages_with += 1
            total += len(dialogues)
    ratio = pages_with / max(len(inner), 1)
    score = 10
    if ratio < 0.15:
        score -= 3
    elif ratio < 0.25:
        score -= 1.5
    return {"score": max(1, round(score, 1)), "dialogue_ratio": round(ratio * 100), "total_dialogues": total}


def _analyze_emotional_arc(pages: list[dict]) -> dict:
    inner = [p for p in pages if p.get("page_type") == "inner"]
    EMOTIONS = {
        "merak": ["merak", "acaba", "gizemli", "sır"],
        "heyecan": ["heyecan", "hızla", "koştu", "macera"],
        "korku": ["kork", "endişe", "tehlike", "titred", "karanlık"],
        "sevinç": ["sevinç", "mutlu", "güldü", "harika", "muhteşem"],
        "cesaret": ["cesaret", "cesur", "kararlı", "derin bir nefes"],
        "gurur": ["gurur", "başard", "kahraman", "zafer"],
    }
    all_found: set[str] = set()
    arc: list[dict] = []
    for p in inner:
        text = (p.get("text") or "").lower()
        page_em: dict[str, int] = {}
        for em, kws in EMOTIONS.items():
            cnt = sum(1 for kw in kws if kw in text)
            if cnt:
                page_em[em] = cnt
                all_found.add(em)
        dominant = max(page_em, key=page_em.get) if page_em else "nötr"
        arc.append({"page": p.get("page_number"), "dominant": dominant})
    score = 10
    if len(all_found) < 3:
        score -= 3
    elif len(all_found) < 4:
        score -= 1
    return {
        "score": max(1, round(score, 1)),
        "emotion_variety": len(all_found),
        "emotions_found": sorted(all_found),
        "arc_summary": [a["dominant"] for a in arc if a["dominant"] != "nötr"],
    }


def _analyze_page_rhythm(pages: list[dict]) -> dict:
    inner = [p for p in pages if p.get("page_type") == "inner"]
    counts = [len((p.get("text") or "").split()) for p in inner]
    if not counts:
        return {"score": 5, "avg_words": 0, "min_words": 0, "max_words": 0}
    avg = sum(counts) / len(counts)
    std_dev = (sum((c - avg) ** 2 for c in counts) / len(counts)) ** 0.5
    score = 10
    if std_dev > 25:
        score -= 2
    elif std_dev > 15:
        score -= 1
    return {
        "score": max(1, round(score, 1)),
        "avg_words": round(avg, 1),
        "min_words": min(counts),
        "max_words": max(counts),
        "std_dev": round(std_dev, 1),
    }


def _analyze_hooks(pages: list[dict]) -> dict:
    inner = [p for p in pages if p.get("page_type") == "inner"]
    HOOKS = ["acaba", "?", "!", "ama", "birden", "tam o sırada", "ansızın", "derken"]
    with_hook = 0
    for p in inner[:-1]:
        text = (p.get("text") or "").strip()
        sentences = [s.strip() for s in re.split(r"[.!?]", text) if s.strip()]
        last = sentences[-1].lower() if sentences else ""
        if any(h in last for h in HOOKS):
            with_hook += 1
    total_check = max(len(inner) - 1, 1)
    ratio = with_hook / total_check
    score = 10
    if ratio < 0.3:
        score -= 3
    elif ratio < 0.5:
        score -= 1.5
    return {"score": max(1, round(score, 1)), "hook_ratio": round(ratio * 100)}


def _calculate_fun_score(analyses: dict) -> dict:
    weights = {
        "repetition": 0.20,
        "dialogue": 0.20,
        "emotional_arc": 0.25,
        "rhythm": 0.15,
        "hooks": 0.20,
    }
    total = sum(analyses.get(k, {}).get("score", 5) * w for k, w in weights.items())
    final = round(total, 1)
    if final >= 9:
        grade = "A"
    elif final >= 7.5:
        grade = "B"
    elif final >= 6:
        grade = "C"
    elif final >= 4:
        grade = "D"
    else:
        grade = "F"
    return {"final_score": final, "grade": grade}


# ─────────────────────────────────────────────────
# MAIN ENTRY POINT
# ─────────────────────────────────────────────────


async def run_scenario_dry_run(
    *,
    db: AsyncSession,
    theme_key: str,
    child_name: str = "Yusuf",
    child_age: int = 7,
    child_gender: str = "erkek",
) -> dict[str, Any]:
    """Run V3 pipeline dry-run and return structured analysis results.

    Raises:
        ValueError: if scenario not found.
        Exception: if Gemini pipeline fails after retries.
    """
    import asyncio

    # 1. Fetch scenario from DB
    result = await db.execute(
        select(Scenario).where(
            (Scenario.theme_key == theme_key) | (Scenario.name.ilike(f"%{theme_key}%"))
        )
    )
    scenario = result.scalar_one_or_none()
    if not scenario:
        raise ValueError(f"Senaryo bulunamadı: '{theme_key}'")

    page_count = scenario.story_page_count or scenario.default_page_count or 21

    # Determine outfit
    if child_gender in ("kiz", "girl", "female"):
        fixed_outfit = scenario.outfit_girl or ""
    else:
        fixed_outfit = scenario.outfit_boy or ""

    # 2. Run V3 pipeline (with retries)
    from app.services.ai.gemini_service import GeminiService

    gemini = GeminiService()
    start_time = time.monotonic()

    max_retries = 2
    last_error: Exception | None = None
    for attempt in range(1, max_retries + 1):
        try:
            logger.info(
                "DRY_RUN_START",
                theme_key=theme_key,
                attempt=attempt,
                page_count=page_count,
            )
            story_response, final_pages, outfit, blueprint = await gemini.generate_story_v3(
                scenario=scenario,
                child_name=child_name,
                child_age=child_age,
                child_gender=child_gender,
                visual_style="children's book illustration, soft colors",
                page_count=page_count,
                fixed_outfit=fixed_outfit,
                generate_visual_prompts=True,
            )
            break
        except Exception as e:
            last_error = e
            logger.warning("DRY_RUN_ATTEMPT_FAILED", attempt=attempt, error=str(e)[:200])
            if attempt < max_retries:
                await asyncio.sleep(15 * attempt)
            else:
                raise last_error  # type: ignore[misc]

    elapsed = round(time.monotonic() - start_time, 1)

    # 3. Structure page data
    pages_data: list[dict] = []
    for fp in final_pages:
        pages_data.append({
            "page_number": fp.page_number,
            "page_type": fp.page_type,
            "text": fp.text,
            "visual_prompt": (fp.visual_prompt or "")[:500],  # truncate for response size
            "negative_prompt": (getattr(fp, "negative_prompt", "") or "")[:200],
        })

    # 4. Run analyses
    safety = _check_content_safety(pages_data)
    completeness = _check_page_completeness(pages_data, page_count)

    story_analyses = {
        "repetition": _analyze_repetition(pages_data),
        "dialogue": _analyze_dialogue(pages_data),
        "emotional_arc": _analyze_emotional_arc(pages_data),
        "rhythm": _analyze_page_rhythm(pages_data),
        "hooks": _analyze_hooks(pages_data),
    }
    fun = _calculate_fun_score(story_analyses)

    logger.info(
        "DRY_RUN_COMPLETE",
        theme_key=theme_key,
        elapsed=elapsed,
        fun_score=fun["final_score"],
        safety=safety["status"],
    )

    return {
        "scenario_name": scenario.name,
        "theme_key": theme_key,
        "title": story_response.title,
        "child": {"name": child_name, "age": child_age, "gender": child_gender},
        "page_count": len(pages_data),
        "inner_page_count": len([p for p in pages_data if p["page_type"] == "inner"]),
        "pages": pages_data,
        "audit": {
            "content_safety": {
                "status": safety["status"],
                "issue_count": len(safety["issues"]),
                "issues": safety["issues"][:10],
            },
            "page_completeness": {
                "status": completeness["status"],
                "issue_count": len(completeness["issues"]),
                "issues": completeness["issues"][:10],
            },
        },
        "story_quality": {
            "fun_score": fun["final_score"],
            "grade": fun["grade"],
            **{k: v for k, v in story_analyses.items()},
        },
        "elapsed_seconds": elapsed,
    }

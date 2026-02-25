# V2 vs V3 Pipeline Debug Report — Çatalhöyük Prompts

**Date:** 2026-02-17  
**Severity:** CRITICAL  
**Status:** Root cause identified, fix provided

---

## 1. Root Cause: V3 Pipeline Is DISABLED in Production

```
USE_BLUEPRINT_PIPELINE env var → NOT SET on Cloud Run
config.py default → use_blueprint_pipeline: bool = False
```

**Result:** Every single prompt goes through the **V2 Legacy** path. All V3 fixes (kids-safe rewrite, embedded-text stripping, unified negatives, scenario-aware anchors, shot-plan diversity) are **dead code in production**.

### Evidence

| Check | Result |
|-------|--------|
| `gcloud run describe` env vars | `USE_BLUEPRINT_PIPELINE` absent |
| `config.py` line 70 | `use_blueprint_pipeline: bool = False` |
| `gemini_service.py` line 2535 | `use_v3 = getattr(settings, "use_blueprint_pipeline", False)` → always `False` |
| Trial endpoint `v3_composed` flag | Pages arrive without `v3_composed=True` → `skip_compose=False` → V2 `compose_visual_prompt()` called |

---

## 2. Runtime Pipeline Trace (Current Production)

```
Frontend /create page
  → POST /api/v1/ai/test-story-structured
    → gemini_service.generate_story_structured()
      → use_v3 = False → V2 TWO-PASS generation
        → PASS-1: Gemini writes story (TR)
        → PASS-2: Gemini writes scene_description (EN) per page
        → compose_visual_prompt() called per page ← FIRST COMPOSITION (V2)
          → Adds: BODY_PROPORTION_DIRECTIVE
          → Adds: SHARPNESS_BACKGROUND_DIRECTIVE
          → Adds: COMPOSITION_RULES ("Wide shot, child 30% of frame...")
          → Adds: STYLE block + anchor + leading prefix
        → Injects location_constraints ("iconic elements required in every scene")
      → Returns FinalPageContent (v3_composed=False, negative_prompt="")

Frontend receives story → User clicks "Generate Preview"
  → POST /api/v1/trials/generate-preview
    → Receives story_pages (visual_prompt already composed)
    → _gen_composed_single():
      → v3_composed = False → skip_compose = False
      → Calls generate_consistent_image(skip_compose=False)
        → compose_visual_prompt() called AGAIN ← SECOND COMPOSITION (V2)
          → _is_already_composed() passthrough triggers IF:
            - "Child in frame, natu" marker found AND "Wide shot" found
          → Even passthrough re-adds: style anchor, leading prefix, STYLE block
          → But COMPOSITION_RULES not re-added (passthrough skips template)
```

---

## 3. Why V2 Artifacts Appear in Output

### 3a. "Wide shot, child 30% of frame" + "Full body head-to-feet visible"

**Source:** `COMPOSITION_RULES` constant in `constants.py:62-66`

```python
COMPOSITION_RULES = (
    "Wide shot, child 30% of frame, environment 70%. "
    "Full body head-to-feet visible, NO cropped legs. "
    "Same clothing, hairstyle, skin tone, facial features on every page."
)
```

**Injected by:** `compose_visual_prompt()` at `visual_prompt_composer.py:435-498`  
**When:** First composition during story generation (V2 PASS-2), only when `has_template=True`.

### 3b. "iconic elements required in every scene"

**Source:** Scenario `location_constraints` field in DB.  
**Example** (`create_catalhoyuk_scenario.py:192`):
```
"Çatalhöyük Neolithic city iconic elements required in every scene:
- Dense mud-brick houses with flat roofs..."
```

**Injected by:** `gemini_service.py:1901-1916` — appends `Setting: {location_constraints}` to visual prompt after composition.

**Stripping attempt exists** in `visual_prompt_composer.py:79` (`_RE_SETTING_INSTRUCTION` regex) but it only runs during the SECOND `compose_visual_prompt()` call (trial). The text is injected AFTER the first `compose_visual_prompt()` call, so the first call can't strip it. On the second call (passthrough), this regex MAY strip it, but passthrough doesn't re-process the full template flow.

### 3c. Kids-safe rewrites NOT applied

**Source:** `_kids_safe_rewrite()` and `_strip_embedded_text()` only exist in `visual_prompt_builder.py` — the V3 `compose_enhanced_prompt()` function.

**V2 path has NO kids-safe rewriting.** `compose_visual_prompt()` does not call any safety rewrite function.

| Function | File | Called in V2? | Called in V3? |
|----------|------|:---:|:---:|
| `_kids_safe_rewrite()` | `visual_prompt_builder.py` | NO | YES |
| `_strip_embedded_text()` | `visual_prompt_builder.py` | NO | YES |
| `pick_anchors()` (scenario-aware) | `iconic_anchors.py` | NO | YES |
| `build_enhanced_negative()` (unified) | `visual_prompt_builder.py` | NO | YES |

### 3d. Negative prompt lacks style.forbidden_terms

**V2 negative builder** (`negative_prompt_builder.py:24-57`):
- Uses `NEGATIVE_PROMPT` constant (base) — does NOT include `GLOBAL_NEGATIVE_PROMPT_EN`
- Calls `get_style_negative_default(style_modifier)` for style-specific negatives
- Does NOT use `style_adapter.forbidden_terms` or `StyleMapping`

**V3 negative builder** (`visual_prompt_builder.py:build_enhanced_negative()`):
- Uses `GLOBAL_NEGATIVE_PROMPT_EN` (enriched base)
- Includes `character_bible.negative_tokens`
- Includes `style_mapping.forbidden_terms` (from `style_adapter.py`)
- Includes gender-specific + cover text-blocking tokens
- Deduplicates

**Result:** V2 negatives miss `forbidden_terms` like "3D, CGI, Pixar, anime" for watercolor style, etc.

---

## 4. Files/Functions Responsible for V2 Artifacts

| Artifact | File | Function/Line | Fix |
|----------|------|---------------|-----|
| Pipeline selection | `config.py:70` | `use_blueprint_pipeline: bool = False` | Set `USE_BLUEPRINT_PIPELINE=true` env var |
| COMPOSITION_RULES injection | `visual_prompt_composer.py:435` | `compose_visual_prompt()` | Bypassed when V3 enabled |
| BODY_PROPORTION_DIRECTIVE | `visual_prompt_composer.py:698` | `compose_visual_prompt()` | Bypassed when V3 enabled |
| "iconic elements" in DB | `create_catalhoyuk_scenario.py:192` | `CATALHOYUK_LOCATION_CONSTRAINTS` | DB data — V3 `pick_anchors()` replaces this |
| Location constraint injection | `gemini_service.py:1901` | V2 PASS-2 loop | Only runs in V2 path |
| No kids-safe rewrite | `visual_prompt_composer.py` | (absent) | V3 has it in `visual_prompt_builder.py` |
| Weak negative prompt | `negative_prompt_builder.py:24` | `build_negative_prompt()` | V3 `build_enhanced_negative()` replaces this |
| Double composition | `fal_ai_service.py:405` | `compose_visual_prompt()` 2nd call | V3 sets `skip_compose=True` |

---

## 5. Minimal Fix: Enable V3 Pipeline in Production

### Step 1: Set environment variable on Cloud Run (IMMEDIATE)

```bash
gcloud run services update benimmasalim-backend \
  --region europe-west1 \
  --set-env-vars "USE_BLUEPRINT_PIPELINE=true" \
  --quiet
```

This single change activates:
- V3 three-pass story generation with `enhance_all_pages()`
- `compose_enhanced_prompt()` with shot-plan diversity (no fixed "Wide shot, child 30%")
- `_kids_safe_rewrite()` for injury/distress terms
- `_strip_embedded_text()` for no-text enforcement
- `build_enhanced_negative()` with `style.forbidden_terms`
- `pick_anchors()` scenario-aware anchor selection
- `v3_composed=True` flag → `skip_compose=True` in FAL service → no double composition

### Step 2: Clean up scenario location_constraints (RECOMMENDED)

The "iconic elements required in every scene" text in scenario DB data is irrelevant for V3 (it uses `pick_anchors()` from `iconic_anchors.py`), but should be cleaned to prevent confusion:

```sql
UPDATE scenarios
SET location_constraints = REGEXP_REPLACE(
  location_constraints,
  'iconic elements required in every scene[:\s]*',
  'iconic elements:'
)
WHERE location_constraints LIKE '%iconic elements required in every scene%';
```

### Step 3: Verify after enabling (MONITORING)

Check backend logs for these V3-specific log lines:
- `"Dispatching to V3 Blueprint Pipeline"` — confirms V3 active
- `"V3_SKIP_COMPOSE_PROMPT_STATS"` — confirms skip_compose path
- `"ID_WEIGHT_RESOLVED"` — confirms id_weight source logging
- Absence of `"PROMPT COMPOSED (scene-only)"` — confirms V2 not used

---

## 6. Risk Assessment for Enabling V3

| Risk | Mitigation |
|------|-----------|
| V3 story quality differs from V2 | V3 uses same Gemini model + 3-pass; quality ≥ V2 |
| Prompt length exceeds FAL limit | V3 has truncation + logging built in |
| Character consistency loss | V3 uses CharacterBible with outfit_text_exact |
| Style block missing | V3 `compose_enhanced_prompt()` appends STYLE block |
| Rollback | Set `USE_BLUEPRINT_PIPELINE=false` to revert instantly |

---

## 7. Summary

| Question | Answer |
|----------|--------|
| Which pipeline is active? | **V2 Legacy** (V3 disabled) |
| Why "Wide shot, child 30%"? | `COMPOSITION_RULES` injected by V2 `compose_visual_prompt()` |
| Why "iconic elements every scene"? | Scenario `location_constraints` DB field, injected by `gemini_service.py:1901` |
| Why no kids-safe rewrite? | Only exists in V3 `compose_enhanced_prompt()` |
| Why negative lacks forbidden_terms? | V2 `build_negative_prompt()` doesn't use `StyleMapping.forbidden_terms` |
| Fix? | **Set `USE_BLUEPRINT_PIPELINE=true` on Cloud Run** |

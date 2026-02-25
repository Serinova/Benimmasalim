# Prompt System V2 — Final Backend Review

**Date:** 2026-02-06  
**Status:** PASS — all 90 tests green, E2E Docker verified, migration applied.

---

## 1. Current Map (Phase A)

### Models

| Model | File | V2 Columns Added | Legacy Columns (kept for compat) |
|-------|------|-------------------|----------------------------------|
| Scenario | `app/models/scenario.py` | `story_prompt_tr`, `location_en`, `flags` (JSONB), `default_page_count` | `cover_prompt_template`, `page_prompt_template`, `ai_prompt_template` |
| PromptTemplate | `app/models/prompt_template.py` | `template_en` | — |
| LearningOutcome | `app/models/learning_outcome.py` | `banned_words_tr` | — |
| VisualStyle | `app/models/visual_style.py` | `style_negative_en` | — |
| StoryPreview | `app/models/story_preview.py` | — (already had `prompt_debug_json`, `generation_manifest_json`) | — |

### prompt_engine Modules

| Module | Purpose | Status |
|--------|---------|--------|
| `constants.py` | Negative prompts, style configs, PuLID weights | ✅ Complete |
| `prompt_sanitizer.py` | Location normalization, cinematic strip, truncation | ✅ Complete |
| `validators.py` | Placeholder check, cover/inner phrase rules, banned words | ✅ Complete |
| `negative_prompt_builder.py` | Merges base + strict + style-specific negative | ✅ Complete |
| `story_prompt_composer.py` | PASS-1 TR story prompt composition | ✅ Complete |
| `visual_prompt_composer.py` | PASS-2 EN visual prompt composition | ✅ Complete |
| `fal_request_builder.py` | FAL payload + debug output builder | ✅ Complete |

### Service Pipeline Chains

| Entry Point | Chain | V2 Status |
|-------------|-------|-----------|
| `orders.submit_preview_async` | → `process_preview_background` → `fal_service.generate_consistent_image` → `compose_visual_prompt` (PE) | ✅ V2 |
| `ai.test_structured_story_generation` | → `gemini_service.generate_story_structured` → PASS-1 (now reads `story_prompt_tr`) → PASS-2 → `compose_visual_prompt` (PE) | ✅ V2 |
| `trials.create_trial` | → `gemini_service.generate_story_structured` (same as above) | ✅ V2 |
| `generate_book.generate_full_book` | → `fal_service.generate_consistent_image` → `compose_visual_prompt` (PE) | ✅ V2 |
| `gemini_image_service.generate_image_from_scenario` | → `scenario.get_cover/page_prompt(visual_style="")` → `compose_visual_prompt` (PE) | ✅ V2 (style deferred) |

### Admin Routes

| Route | V2 Fields Exposed | Legacy Fields (kept) |
|-------|-------------------|----------------------|
| `/admin/scenarios` | `story_prompt_tr`, `location_en`, `flags`, `default_page_count` | `cover_prompt_template`, `page_prompt_template`, `ai_prompt_template` |
| `/admin/prompts` | `template_en` | — |
| `/admin/learning-outcomes` | `banned_words_tr` | `ai_prompt` |
| `/admin/visual-styles` | `style_negative_en` | — |

---

## 2. Findings & Fixes (Phases B–E)

### Fix 1: `PromptTemplate.to_dict()` missing `template_en`
- **File:** `app/models/prompt_template.py`
- **Problem:** `to_dict()` did not include the V2 `template_en` field.
- **Fix:** Added `"template_en": self.template_en` to the dict output.

### Fix 2: `gemini_service.generate_story_structured` using only `ai_prompt_template`
- **File:** `app/services/ai/gemini_service.py`
- **Problem:** PASS-1 read only `scenario.ai_prompt_template`, ignoring V2 `story_prompt_tr`.
- **Fix:** Changed to prefer `story_prompt_tr` with fallback to `ai_prompt_template`.
- Also: `location_en` now auto-generates location constraint if `location_constraints` is empty.

### Fix 3: `no_family` flag enforcement in PASS-1
- **File:** `app/services/ai/gemini_service.py`
- **Problem:** V2 `flags.no_family` was defined but never enforced.
- **Fix:** When `scenario.flags["no_family"] == true`, appends family-ban instruction to the story prompt.

### Fix 4: Style injection bypass in `gemini_image_service.py`
- **File:** `app/services/ai/gemini_image_service.py`
- **Problem:** `get_cover_prompt()` and `get_page_prompt()` received `visual_style_modifier` directly, bypassing the compose layer.
- **Fix:** Now passes `visual_style=""` to legacy methods. Style is injected by `compose_visual_prompt` via `style_text` parameter.

### Fix 5: `fal_ai_service.py` using local `NEGATIVE_PROMPT` (missing `extra fingers`)
- **File:** `app/services/ai/fal_ai_service.py`
- **Problem:** Local `NEGATIVE_PROMPT` lacked `extra fingers` token. Also used local `get_style_specific_negative` and `get_pulid_weight_for_style`.
- **Fix:** Hot calls now use prompt_engine canonical versions (`_PE_NEGATIVE_PROMPT`, `_pe_get_style_neg`, `_pe_get_pulid_weight`). Local definitions marked deprecated.

### Leftovers Resolution Summary

| Category | Count | Action |
|----------|-------|--------|
| Rewired to prompt_engine | 5 | `fal_ai_service.py` negative/style/weight calls |
| Deprecated (kept for compat) | 3 | Local `NEGATIVE_PROMPT`, `StyleConfig`, `FluxPromptBuilder` in `fal_ai_service.py` |
| Shim files (re-export) | 2 | `app/core/visual_prompt_composer.py`, `app/core/prompt_sanitizer.py` — zero direct imports remain |
| Already clean | All others | — |

---

## 3. Rules Enforced + Where (Phase C)

| Rule | Enforced In | Test |
|------|-------------|------|
| Scenario content is style-free | `gemini_service._compose_visual_prompts` produces scene-only prompts | `test_scene_only_prompt_has_no_style_tokens` |
| VisualStyle injected once at compose | `visual_prompt_composer.compose_visual_prompt(style_text=...)` | `test_style_injected_only_at_compose` |
| "Kapadokya" → "Cappadocia" | `prompt_sanitizer.normalize_location()` | `test_kapadokya_normalized_to_cappadocia` |
| No unresolved placeholders | `validators.validate_no_placeholders()` | `test_no_unresolved_placeholders` |
| Cover 768×1024, Inner 1024×768 | `fal_request_builder.build_fal_request()` | `test_dimensions_cover_inner` |
| Strict negative (big eyes/chibi/text/extra fingers) | `constants.STRICT_NEGATIVE_ADDITIONS` | `test_negative_contains_big_eyes_chibi_typographic` |
| no_family banned words | `validators.validate_banned_words()` + PASS-1 injection | `test_no_family_banned_words_enforced_if_flag` |
| Title-safe (cover) / text-safe (inner) | `visual_prompt_composer.compose_visual_prompt()` | `test_cover_inner_phrases` (in test_validators) |
| Wide-angle without lens terms | `prompt_sanitizer.sanitize_visual_prompt()` strips cinematic/lens | `test_strips_cinematic_terms` |

---

## 4. Routes + Payloads + Chains (Phase D)

### Story Generation (PASS-1)
```
POST /api/v1/ai/test-story-structured
Body: { scenario_id, child_name, child_age, child_gender, learning_outcome_ids, visual_style_id, child_photo_url }
→ gemini_service.generate_story_structured()
  → reads scenario.story_prompt_tr (fallback: ai_prompt_template)
  → reads scenario.location_en → builds location constraint
  → reads scenario.flags.no_family → appends banned instruction
  → _pass1_write_story() → Gemini Pro → TR story text
  → _pass2_format_story() → Gemini Flash → structured JSON
  → _compose_visual_prompts() → scene-only EN prompts (NO style)
Returns: { title, pages: [{ text, scene_description, visual_prompt }] }
```

### Image Generation (FAL)
```
POST /api/v1/orders/submit-preview-async
→ process_preview_background()
  → fal_service.generate_consistent_image(prompt, style_modifier, ...)
    → compose_visual_prompt(scene, style_text, style_negative) ← prompt_engine
    → build_negative_prompt(base, strict, style_neg) ← prompt_engine
    → FAL API call (cover: 768×1024, inner: 1024×768)
  → stores prompt_debug_json, generation_manifest_json in story_previews
```

### Observability Fields
```sql
SELECT prompt_debug_json, generation_manifest_json
FROM story_previews WHERE id = '<preview_id>';
```
- `prompt_debug_json`: `{page_index: {final_prompt, negative_prompt, ...}}`
- `generation_manifest_json`: `{page_index: {provider, model, width, height, reference_image_used, ...}}`

---

## 5. Test Results (Phase F)

```
90 passed, 1 skipped in 0.10s
```

| Suite | Tests | Status |
|-------|-------|--------|
| test_prompt_engine/test_fal_builder | 8 | ✅ |
| test_prompt_engine/test_negative | 5 | ✅ |
| test_prompt_engine/test_sanitizer | 11 | ✅ |
| test_prompt_engine/test_story_composer | 5 | ✅ |
| test_prompt_engine/test_validators | 16 | ✅ |
| test_prompt_engine/test_visual_composer | 6 | ✅ |
| test_prompt_sanitizer (legacy) | 7 | ✅ |
| test_style_independence (legacy) | 5 | ✅ |
| test_visual_prompt_composer (legacy) | 19 | ✅ |
| test_image_dimensions | 3 | ✅ |
| test_preview_detail_response | 5 | ✅ |
| test_e2e_preview_detail | 1 | ⏭ Skipped (needs live DB session) |

---

## 6. E2E Docker Results (Phase G)

```
=== 1) Docker Compose === All services running (healthy)
=== 2) Migrations === 023_prompt_v2 applied successfully
=== 3) Verify columns === prompt_debug_json, generation_manifest_json exist
=== 4) Health === 200 OK

V2 DB columns verified:
- scenarios: story_prompt_tr (text), location_en (varchar), flags (jsonb), default_page_count (integer)
- prompt_templates: template_en (text)
- visual_styles: style_negative_en (text)
- learning_outcomes: banned_words_tr (text)
- Seeded: COVER_TEMPLATE, INNER_TEMPLATE with EN placeholders
```

**Verdict: PASS**

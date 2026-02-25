# Story → Visual Prompt → Image Generation Pipeline Audit

**Date:** 2026-02-17  
**Scope:** Story generation (TR) → image_prompt_en generation (EN) → image generation & storage  
**Out of scope:** Text overlay / typography / PDF assembly  

---

## 1) Executive Summary

1. **Two coexisting pipelines**: V2 (two-pass LLM, feature-flagged OFF by default) and V3 (blueprint three-pass, feature-flagged via `settings.use_blueprint_pipeline`). Both dispatch through `gemini_service.generate_story_structured()`.
2. **V3 has a complete deterministic enhancement layer** (`enhance_all_pages`) with CharacterBible, SceneDirector, StyleAdapter, IconicAnchors, KidsSafeRewrite, and a 7-rule validator + auto-fixer.
3. **Image generation** uses Fal.ai Flux PuLID (`fal-ai/flux-pulid`) as primary provider, with Gemini Flash as fallback. PuLID face-consistency is applied when `child_face_url` is present.
4. **id_weight is per-style in code** (constants.py `STYLE_PULID_WEIGHTS`) but **all 7 DB seed styles use the model default 0.90** — the per-style weights only apply when the DB column is NULL and the code fallback kicks in.
5. **Legacy constants still hardcode "Wide shot, child 30% of frame"** in `COMPOSITION_RULES` and all `StyleConfig.suffix` values. The V3 path avoids these, but the V2 path and `compose_visual_prompt()` still inject them.
6. **The V3 pipeline runs a compose_visual_prompt() on top of enhance_all_pages()** — this means prompts are double-processed: first by the V3 deterministic enhancer, then by the V2 visual composer. This risks redundancy, truncation, and style block conflicts.
7. **Negative prompts are built at two layers** with different constants: V3 uses `GLOBAL_NEGATIVE_PROMPT_EN`, V2 uses `NEGATIVE_PROMPT`. The final negative is built by `negative_prompt_builder.py` which may not see the V3 forbidden_terms.
8. **`use_blueprint_pipeline` defaults to `False`** in config — meaning production currently runs the V2 legacy path unless explicitly enabled.
9. **Arq Redis workers** handle image generation (3 concurrent jobs, 30-min timeout, 3 attempts). Fallback to FastAPI `BackgroundTasks` if Redis is unavailable.
10. **Kids-safe rewrite is comprehensive** (28 regex patterns) and runs in the V3 enhancement pass. Story-level safety validators catch 27 TR + 23 EN banned words.

---

## 2) Architecture Diagram

```mermaid
flowchart TD
    A[User: Create Story] --> B{API Endpoint}
    B -->|POST /trials/create| C[trials.py: create_trial]
    B -->|POST /ai/test-story-structured| D[ai.py: test_structured_story_generation]
    
    C --> E[gemini_service.generate_story_structured]
    D --> E
    
    E --> F{use_blueprint_pipeline?}
    F -->|True V3| G[generate_story_v3]
    F -->|False V2| H[V2 Legacy Two-Pass]
    
    G --> G0[PASS-0: Blueprint<br/>gemini-2.0-flash T=0.7]
    G0 --> G1[PASS-1: Story Pages<br/>gemini-2.0-flash T=0.92]
    G1 --> G2[validate_story_output + apply_all_fixes]
    G2 --> G3[build_character_bible]
    G3 --> G4[enhance_all_pages<br/>SceneDirector + StyleAdapter<br/>KidsSafe + Anchors + Validator]
    G4 --> G5[validate_visual_prompts + autofix]
    
    H --> H1[PASS-1: Pure Author<br/>gemini-2.0-flash T=0.92]
    H1 --> H2[PASS-2: Technical Director<br/>gemini-2.0-flash T=0.5]
    H2 --> H3[_compose_visual_prompts]
    
    G5 --> I[compose_visual_prompt per page<br/>Template + PuLID + STYLE block]
    H3 --> I
    
    I --> J[StoryResponse + FinalPageContent]
    J --> K[trial_service.create_trial<br/>Store to StoryPreview DB]
    
    K --> L{Enqueue Method}
    L -->|Arq Redis| M[image_worker: generate_trial_preview]
    L -->|Fallback| N[BackgroundTasks]
    
    M --> O[Resolve VisualStyle from DB]
    O --> P[get_image_provider_for_generation]
    P --> Q{Provider}
    Q -->|Fal.ai| R[fal_ai_service.generate_consistent_image<br/>Flux PuLID / Flux Dev]
    Q -->|Gemini| S[GeminiFlashImageGenerator]
    
    R --> T[compose_visual_prompt AGAIN<br/>+ build_negative_prompt]
    T --> U[Fal.ai HTTP API<br/>queue.fal.run/fal-ai/flux-pulid]
    U --> V[Poll completion 2s intervals]
    V --> W[Image URL returned]
    
    S --> W
    
    W --> X[storage_service: upload to GCS<br/>benimmasalim-generated-books]
    X --> Y[trial_service.save_preview_images<br/>Update StoryPreview.preview_images]
    
    Y --> Z[User polls GET /trials/{id}/status]
    Z --> AA{is_preview_ready?}
    AA -->|Yes| AB[GET /trials/{id}/preview<br/>Returns story + 3 image URLs]
    AA -->|No| Z
```

---

## 3) Module Map Table

| Step | Entry Function | Key Files | Inputs | Outputs | Failure Points |
|------|---------------|-----------|--------|---------|----------------|
| **API Entry** | `create_trial()` | `api/v1/trials.py:177` | HTTP POST with child info, scenario, style | trial_id, token | Scenario not found (fallback mock) |
| **Story Gen (V3)** | `generate_story_v3()` | `services/ai/gemini_service.py:2246` | child meta, blueprint, style | StoryResponse, FinalPageContent[] | Gemini rate limit (429), timeout (120s), safety block |
| **PASS-0 Blueprint** | `_pass0_generate_blueprint()` | `gemini_service.py:1962`, `blueprint_prompt.py` | child info, scenario bible | Blueprint JSON (22 pages) | Page count mismatch (retry 2x) |
| **PASS-1 Pages** | `_pass1_generate_pages()` | `gemini_service.py:2103`, `page_prompt.py` | Blueprint, child info, style | pages[{text_tr, image_prompt_en}] | Invalid JSON, safety violation |
| **Story Validation** | `validate_story_output()` | `story_validators.py:839` | pages, blueprint, magic_items | StoryValidationReport | Non-fixable: family ban persistent |
| **CharacterBible** | `build_character_bible()` | `character_bible.py:235` | child_name, age, gender, description | CharacterBible (frozen) | None (always succeeds) |
| **V3 Enhancement** | `enhance_all_pages()` | `visual_prompt_builder.py:471` | pages, blueprint, bible, style, location | Enhanced pages + shot_plan + style_profile | Empty blueprint → fallback ShotPlan |
| **Visual Validation** | `validate_all()` | `visual_prompt_validator.py:301` | pages, bible, style_mapping | ValidationResult | Auto-fix fails silently on PLACEHOLDER |
| **V2 Compose** | `compose_visual_prompt()` | `visual_prompt_composer.py:516` | scene_desc, template, style, clothing | (positive_prompt, negative_prompt) | Truncation at 2048 chars drops STYLE block |
| **Image Gen** | `generate_consistent_image()` | `fal_ai_service.py:251` | prompt, negative, face_url, style, size | Image URL | Fal 429/timeout, prompt contamination |
| **Storage** | `upload_generated_image()` | `storage_service.py:211` | image_bytes, order_id, page_num | GCS URL | GCS upload failure (3 retries) |
| **Queue** | `generate_trial_preview` | `workers/image_worker.py:129` | trial_id | Updated StoryPreview | Redis unavail → BackgroundTasks fallback |

---

## 4) Current "Rules" Inventory

### Character Consistency Rules

| Rule | Where | Status |
|------|-------|--------|
| CharacterBible with identity_tokens (7 tokens: same face/hair/skin/features, natural proportions, small eyes, no chibi) | `character_bible.py` `_IDENTITY_TOKENS` | ✅ Active in V3 |
| outfit_text_exact verbatim lock | `character_bible.py:86` | ✅ Active in V3 |
| Outfit preset per gender (erkek/kız) | `character_bible.py:40-53` | ✅ Active |
| PuLID face consistency via reference_image_url | `fal_ai_service.py:478` | ✅ Active when child_face_url present |
| id_weight per style | `constants.py:328-364` | ⚠️ Code exists but DB seeds all use 0.90 |
| Negative tokens: wrong hair/skin/outfit | `character_bible.py:103-108` | ✅ Active in V3 |
| LIKENESS_HINT_WHEN_REFERENCE | `constants.py:204` | ✅ Prepended in compose_visual_prompt |
| Gender-specific negative terms | `fal_ai_service.py:409-413` | ✅ Active (dress/skirt for boys, etc.) |

### Style Handling Rules

| Rule | Where | Status |
|------|-------|--------|
| StyleAdapter with 9 style families + forbidden_terms | `style_adapter.py:_STYLE_DEFS` | ✅ Active in V3 |
| StyleConfig with leading_prefix per style | `constants.py:244-319` | ✅ Active in compose_visual_prompt |
| Style anchor at prompt start (highest token weight) | `style_adapter.py` + `visual_prompt_composer.py:719` | ✅ Active |
| STYLE: block appended to prompt | `visual_prompt_composer.py:732-737` | ✅ Active |
| Style mismatch validator (forbidden terms in positive) | `visual_prompt_validator.py:_check_style_mismatch` | ✅ Active in V3 |
| Per-style negative defaults | `constants.py:STYLE_NEGATIVE_DEFAULTS` | ✅ Active |
| DB style_block_override / leading_prefix_override | `visual_style.py` model columns | ✅ Available (admin) |

### Diversity Rules

| Rule | Where | Status |
|------|-------|--------|
| SceneDirector: max 2 consecutive same shot_type | `scene_director.py:_avoid_streak` | ✅ Active in V3 |
| SceneDirector: max 2 consecutive same action_type | `scene_director.py:_avoid_streak` | ✅ Active in V3 |
| Min 6 distinct camera setups per book | `scene_director.py:validate_shot_diversity` | ✅ Active in V3 |
| child_frame_pct varies 20-40% | `scene_director.py:205` | ✅ Active in V3 |
| Near-duplicate detection (95% word overlap) | `visual_prompt_validator.py:_check_near_duplicates` | ✅ Active in V3 |
| Story-level diversity (85% word overlap) | `story_validators.py:validate_visual_prompt_diversity` | ✅ Active |

### Kids-Safe Rules

| Rule | Where | Status |
|------|-------|--------|
| 28 unsafe visual patterns → safe rewrites | `visual_prompt_builder.py:_UNSAFE_VISUAL_PATTERNS` | ✅ Active in V3 |
| 27 TR + 23 EN banned words in story text | `story_validators.py:SAFETY_BANNED_WORDS_*` | ✅ Active |
| Auto-fix safety violations (korku→heyecan, etc.) | `story_validators.py:fix_safety_violations` | ✅ Active |
| Gemini safety settings: BLOCK_MEDIUM_AND_ABOVE (4 categories) | `gemini_service.py` all API calls | ✅ Active |
| Family ban (no anne/baba/kardeş) | `story_validators.py:validate_family_ban` | ✅ Active |

---

## 5) Quality Findings

### 5.1 Story Quality Issues

| # | Severity | Finding | Evidence |
|---|----------|---------|----------|
| S1 | **Medium** | V3 blueprint pipeline is feature-flagged OFF (`use_blueprint_pipeline=False`) — production likely runs V2 legacy | `config.py`: `use_blueprint_pipeline: bool = False` |
| S2 | **Low** | V2 PASS-1 max attempts reduced from 4 to 2 for rate limit safety — less resilience | `gemini_service.py:2602` |
| S3 | **Low** | Learning outcomes reflection check (`_story_reflects_learning_outcomes`) requires only 2 occurrences — easy to satisfy superficially | `gemini_service.py` (V2 path) |
| S4 | **Info** | Sentence count enforced 3-6 per page — good for age-appropriate reading | `story_validators.py:validate_sentence_count` |

### 5.2 Prompt Alignment Issues

| # | Severity | Finding | Evidence |
|---|----------|---------|----------|
| P1 | **Critical** | **Double composition**: V3 `enhance_all_pages()` produces a fully composed prompt, then `compose_visual_prompt()` wraps it AGAIN with template, BODY_PROPORTION, SHARPNESS, COMPOSITION_RULES, and another STYLE block. This creates redundant/conflicting directives. | `gemini_service.py:2430-2460` calls `compose_visual_prompt(scene_description=image_prompt_en)` where `image_prompt_en` is already enhanced |
| P2 | **High** | `compose_visual_prompt` passthrough check (`_is_already_composed`) looks for `BODY_PROPORTION_DIRECTIVE[:20]` AND `"Wide shot"` — but V3 prompts start with style anchor (e.g., "Transparent watercolor painting."), not "Wide shot". So passthrough may NOT trigger, causing double processing. | `visual_prompt_composer.py:581` |
| P3 | **High** | Prompt truncation at 2048 chars (`MAX_FAL_PROMPT_CHARS`): after double-composition, the combined prompt easily exceeds 2048 chars, causing the STYLE block to be dropped entirely. | `visual_prompt_composer.py:742-762` |
| P4 | **Medium** | `fal_request_builder.py` does NOT set `max_sequence_length=512`; only `fal_ai_service.py` does. If anything bypasses `fal_ai_service`, prompts get truncated to 128 tokens (~30 words). | `fal_request_builder.py:12` vs `fal_ai_service.py:474` |
| P5 | **Medium** | V3 negative prompt (`build_enhanced_negative`) uses `GLOBAL_NEGATIVE_PROMPT_EN` + style forbidden terms. But `compose_visual_prompt` later calls `build_negative_prompt()` which uses the DIFFERENT `NEGATIVE_PROMPT` constant + `get_style_negative_default()`. The final negative may lose V3's forbidden_terms. | `visual_prompt_builder.py:445` vs `visual_prompt_composer.py:772` |

### 5.3 Style Contradiction Issues

| # | Severity | Finding | Evidence |
|---|----------|---------|----------|
| ST1 | **Medium** | `DEFAULT_STYLE.leading_prefix` contains "NOT digital" — contradictory when the user selects Adventure Digital style (though style resolver correctly routes to `ADVENTURE_DIGITAL_STYLE`, not `DEFAULT_STYLE`, this phrase persists in the default fallback) | `constants.py:239` |
| ST2 | **Low** | All 7 DB seed styles have `style_negative_en = NULL` and `leading_prefix_override = NULL`. The code falls back to hardcoded constants, but admin has never customized these DB columns. | `seed_data.py:505-555` |
| ST3 | **Low** | DB seed `id_weight` is uniformly `0.90` (model default). The per-style weights in `STYLE_PULID_WEIGHTS` (0.70-0.78) only kick in when `id_weight` is `None` — but the DB value `0.90` overrides them. This means face preservation is stronger than intended, risking bobblehead effect. | `fal_ai_service.py:344-345`, DB default `0.90` |

### 5.4 Repetition Issues

| # | Severity | Finding | Evidence |
|---|----------|---------|----------|
| R1 | **Medium** | Legacy `COMPOSITION_RULES` hardcodes "Wide shot, child 30% of frame" — injected by `normalize_safe_area_and_composition()` in the V2 compose path. Every page gets the same framing directive. | `constants.py:62-66`, `visual_prompt_composer.py:674-679` |
| R2 | **Medium** | `BODY_PROPORTION_DIRECTIVE` and `SHARPNESS_BACKGROUND_DIRECTIVE` are prepended to EVERY page identically — adds ~100 chars of identical prefix to all prompts. | `visual_prompt_composer.py:700-713` |
| R3 | **Low** | When anchor keyword matching finds no matches (`best_score == 0`), it falls back to the "outdoor" group — meaning the same 2 outdoor anchors appear on ALL unmatched pages. | `iconic_anchors.py:461-468` |

### 5.5 Identity Drift Issues

| # | Severity | Finding | Evidence |
|---|----------|---------|----------|
| ID1 | **High** | DB seed styles use `id_weight=0.90` uniformly. The code's per-style differentiation (Pixar=0.78, watercolor=0.72, anime=0.76) is effectively bypassed. Watercolor/pastel styles get too-strong face preservation (0.90 vs intended 0.72-0.74), which fights the art style. | `seed_data.py` vs `constants.py:STYLE_PULID_WEIGHTS` |
| ID2 | **Medium** | PuLID `start_step=2` (early injection) is hardcoded — changed from 5 for "hair preservation" per comment. This aggressive face injection may cause style degradation on delicate styles (watercolor, pastel). | `fal_ai_service.py:83` |
| ID3 | **Low** | `ShotPlan` uses `random.choice([-3, -2, 0, 2, 3])` for frame_pct jitter — pipeline is non-deterministic. Same inputs produce different shot plans on repeated runs. | `scene_director.py:205` |

---

## 6) Observability

### What Exists Now

| Log/Metric | Location | Level |
|------------|----------|-------|
| Story generation complete (title, page_count, validation_passed) | `gemini_service.py:2473` | info |
| Visual prompt enhancement complete (pages, style, location, distinct_shots) | `visual_prompt_builder.py:488` | info |
| Visual prompt auto-fix applied (fix count) | `gemini_service.py` integration | info |
| V3 validation failures post-enhancement | `gemini_service.py:2408` | warning |
| Fal generation timing + model | `fal_ai_service.py` | info |
| Rate limit retry attempts | `rate_limit.py` decorator | warning |
| Prompt contamination guard | `fal_ai_service.py:315-341` | error |
| Trial generation progress | `StoryPreview.generation_progress` JSONB | db field |
| Prompt debug JSON | `StoryPreview.prompt_debug_json` JSONB | db field |
| Generation manifest JSON | `StoryPreview.generation_manifest_json` JSONB | db field |

### Missing Logs / Metrics That Would Help

| Missing | Why Needed |
|---------|------------|
| **Prompt diff before/after compose_visual_prompt** | To detect how much the V2 composer changes the V3-enhanced prompt |
| **STYLE block truncation events** | Critical — silent truncation means the model gets no style guidance |
| **Validator report per book** | Currently logged as warnings but individual rules/pages not traceable |
| **Fal.ai full payload snapshot** | For debugging image quality issues — currently only prompt hash stored |
| **id_weight actually used per image** | To verify DB vs code fallback is applying correctly |
| **Time per pipeline step** | PASS-0 vs PASS-1 vs enhancement vs composition vs image gen breakdown |
| **Near-duplicate rate per book** | Metric to track prompt diversity over time |
| **Queue depth / wait time** | Arq queue monitoring for capacity planning |

---

## 7) Recommended Next Steps (NO IMPLEMENTATION)

### Phase 1: Fix Critical Double-Composition (P1, P2, P3)

**Goal:** Eliminate the `compose_visual_prompt()` call on V3-enhanced prompts.

1. When `use_blueprint_pipeline=True`, skip `compose_visual_prompt()` entirely — the V3 `enhance_all_pages()` already produces a complete prompt with style, composition, character bible, and safety suffix.
2. Pass the V3 negative prompt directly instead of rebuilding via `build_negative_prompt()`.
3. This also resolves P3 (truncation) and P5 (negative prompt mismatch).

### Phase 2: Fix DB id_weight Override (ID1, ST3)

**Goal:** Ensure per-style id_weight differentiation works.

1. Set DB `visual_styles.id_weight = NULL` for all 7 styles (let code fallback apply).
2. OR update each DB row to match the intended values: watercolor=0.72, pixar=0.78, anime=0.76, soft_pastel=0.74, default=0.75, adventure=0.72.
3. Add logging when `id_weight` is resolved — log source (DB vs code fallback).

### Phase 3: Enable V3 Pipeline in Production (S1)

**Goal:** Switch `use_blueprint_pipeline=True`.

1. Run A/B comparison: generate same story with V2 and V3, compare prompt quality.
2. Flip `use_blueprint_pipeline=True` in production config.
3. Monitor for rate limit issues (V3 makes 2 Gemini calls vs V2's 2, plus a 10s buffer).

### Phase 4: Add Observability (Section 6 gaps)

1. Log prompt length before/after `compose_visual_prompt()`.
2. Log STYLE block truncation as a metric (not just silent drop).
3. Store full Fal.ai payload in `prompt_debug_json`.
4. Add per-step timing to `generation_manifest_json`.

### Phase 5: Clean Up Legacy Constants

1. Remove or guard `COMPOSITION_RULES` — it's only needed in V2.
2. Remove "NOT digital" from `DEFAULT_STYLE.leading_prefix`.
3. Populate `display_name`, `style_negative_en`, `leading_prefix_override` in DB seed data.

---

## 8) "What Changed Lately?" Detection

**Git status:** This project is NOT a git repository (confirmed from workspace metadata). No commit history is available.

**Recent file modification analysis** (based on code content and comment timestamps):

| Change | Evidence |
|--------|----------|
| V3 visual prompt system added recently | `visual_prompt_builder.py`, `visual_prompt_validator.py`, `character_bible.py`, `scene_director.py` — all contain V3-specific architecture |
| `style_adapter.py` refactored with `_STYLE_DEFS` and `forbidden_terms` | Contains `STYLE_ADAPTER_MAP` legacy alias for backwards compat |
| `GLOBAL_NEGATIVE_PROMPT_EN` expanded | Now includes "typography, bokeh, depth of field blur, weapon, bobblehead, selfie, portrait, face filling frame" |
| `scene_director.py` added `TOP_DOWN` angle, `COMFORTING` action, `is_indoor` flag | These are V3-specific additions |
| `iconic_anchors.py` expanded to 18+ locations | Includes `galata`, `sultanahmet`, `catalhoyuk`, `kudus`, `abu_simbel`, `tac_mahal` and more |
| PuLID `start_step` changed from 5 to 2 | `fal_ai_service.py:83` comment: "Early injection (was 5, changed for hair preservation)" |
| Trial rate limit adjusted for polling | `middleware/rate_limiter.py`: `/api/v1/trials/status` now has 600/hour limit |
| Frontend polling: 429-specific backoff added | `frontend/src/app/create/page.tsx`: exponential backoff for rate limit errors |

---

## Quick Check Answers

### Q1: Do we still have "always wide shot 30% child" hardcoded?
**YES.** In `constants.py:62-66` (`COMPOSITION_RULES`) and all `StyleConfig.suffix` values. Injected via `normalize_safe_area_and_composition()` in the V2 compose path. The V3 path (`enhance_all_pages`) does NOT use this — it varies 20-40% via SceneDirector. But V3 prompts THEN pass through `compose_visual_prompt()` which may re-inject it.

### Q2: Do we have contradictory style language?
**YES.** `DEFAULT_STYLE.leading_prefix` contains "NOT digital" — problematic if style resolution falls back to default for an adventure/digital style. The V3 `_STYLE_DEFS` are clean of contradictions.

### Q3: Do we accidentally force anchors on every page?
**Partially.** Anchors are context-scored, but when no keywords match (`best_score == 0`), the fallback picks the "outdoor" group. Every page for a known location gets 1-2 anchors, though they ARE varied by scene context.

### Q4: Do we generate unsafe visuals literally?
**NO.** 28 regex patterns in `_kids_safe_rewrite` transform unsafe terms. Additionally, story-level `validate_kids_safety` catches 50 banned words (TR+EN). Defense in depth.

### Q5: Do we produce near-duplicate prompts?
**Detected but not prevented.** Two validators exist (95% and 85% thresholds), but they only flag — they don't auto-fix. The shared character bible + style block prefix means all pages have ~60% identical words by design.

### Q6: Is id_weight applied consistently for all styles?
**NO.** DB seeds all use `0.90` (model default), overriding the per-style code values (0.70-0.78). The code differentiation is effectively bypassed.

### Q7: Does negative_prompt include forbidden terms per style?
**YES in V3** (`build_enhanced_negative` joins `GLOBAL_NEGATIVE_PROMPT_EN` + `character_bible.negative_tokens` + `style_mapping.forbidden_terms`). **But the V2 compose layer rebuilds the negative** via `build_negative_prompt()` which uses different source constants — the V3 forbidden_terms may be lost.

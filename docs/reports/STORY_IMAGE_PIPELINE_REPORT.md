# Story → Image Pipeline: Detailed Technical Report

> **Date:** 2026-02-17  
> **Scope:** Story generation (TR) → Image prompt generation (EN) → Image generation (Fal.ai) → Storage + Workers  
> **Out of scope:** PDF assembly, typography/text overlay

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [Module Map](#2-module-map)
3. [Pipeline Stages (Detailed)](#3-pipeline-stages-detailed)
4. [Findings & Severity](#4-findings--severity)
5. [Root-Cause Analysis](#5-root-cause-analysis)
6. [Proposed Fix Plan](#6-proposed-fix-plan)
7. [Test Plan](#7-test-plan)
8. [Observability Metrics](#8-observability-metrics)

---

## 1. Architecture Overview

### Flow Diagram

```mermaid
flowchart TD
    A[User: create_trial API] --> B[Story Generation<br/>gemini_service.py]
    B -->|FinalPageContent[]| C[Visual Beat Extraction<br/>visual_prompt_builder.py]
    C -->|VisualBeat[]| D[Shot Planning<br/>scene_director.py]
    D -->|ShotPlan[]| E[Prompt Enhancement<br/>visual_prompt_builder.py]
    
    subgraph "V3 Enhancement Pipeline"
        E --> E1[CharacterBible injection]
        E1 --> E2[Kids-safe rewrite]
        E2 --> E3[Embedded text strip]
        E3 --> E4[Style block append]
        E4 --> E5[Iconic anchors]
        E5 --> E6[Negative prompt build]
    end
    
    E6 --> F[Validation + Autofix<br/>visual_prompt_validator.py]
    
    F -->|v3_composed=True| G{Image Provider}
    G -->|Fal.ai| H[fal_ai_service.py<br/>Flux PuLID]
    G -->|Gemini| I[gemini_consistent_image.py<br/>Gemini Flash]
    
    H --> J[GCS Storage<br/>storage_service.py]
    I --> J
    J --> K[DB: StoryPreview<br/>preview_images / page_images]
    
    subgraph "Worker Dispatch"
        L[Arq Redis Queue<br/>image_worker.py]
        M[FastAPI BackgroundTasks<br/>fallback]
    end
    
    F --> L
    L -.->|fallback| M
    L --> G
    M --> G
```

### V2 vs V3 Pipeline Paths

| Aspect | V2 (Legacy) | V3 (Blueprint) |
|--------|-------------|-----------------|
| **Controller** | `settings.use_blueprint_pipeline == False` | `settings.use_blueprint_pipeline == True` |
| **LLM Passes** | 2-pass (creative + technical) | 3-pass (blueprint + creative + technical) |
| **Prompt Composition** | `compose_visual_prompt()` called on every page | `enhance_all_pages()` produces final prompts |
| **Flag** | `v3_composed = False` | `v3_composed = True` |
| **Downstream** | `fal_ai_service` runs `compose_visual_prompt` | `skip_compose = True` — prompt used as-is |
| **Negative Build** | `NEGATIVE_PROMPT` + per-style additions | `GLOBAL_NEGATIVE_PROMPT_EN` + bible + style + gender + cover |

---

## 2. Module Map

### Core Pipeline Modules

| Stage | Module | Entry Function | Key Files | Inputs | Outputs |
|-------|--------|---------------|-----------|--------|---------|
| 1. Story Gen | `gemini_service` | `generate_story_v3()` | `services/ai/gemini_service.py` | Child info, scenario, style, page_count | `list[FinalPageContent]` with `v3_composed=True` |
| 2. Beat Extract | `visual_prompt_builder` | `extract_visual_beat()` | `prompt_engine/visual_prompt_builder.py` | `page_data` dict (text_tr, blueprint) | `VisualBeat` (action, emotion, environment, objects) |
| 3. Shot Planning | `scene_director` | `build_shot_plan()` | `prompt_engine/scene_director.py` | Blueprint pages | `list[ShotPlan]` (shot_type, angle, child_pct) |
| 4. Character | `character_bible` | `build_character_bible()` | `prompt_engine/character_bible.py` | Child name/age/gender/description | `CharacterBible` (prompt_block, outfit_text_exact, negative_tokens) |
| 5. Style | `style_adapter` | `adapt_style()` | `prompt_engine/style_adapter.py` | visual_style string | `StyleMapping` (style_block, forbidden_terms, leading_prefix) |
| 6. Anchors | `iconic_anchors` | `pick_anchors()` | `prompt_engine/iconic_anchors.py` | location_key, scene_text, environment | `list[str]` (1-2 location-specific anchors) |
| 7. Enhancement | `visual_prompt_builder` | `enhance_all_pages()` | `prompt_engine/visual_prompt_builder.py` | pages, blueprint, bible, style, location | Enhanced pages with `image_prompt_en` + `negative_prompt_en` |
| 8. Validation | `visual_prompt_validator` | `validate_all()` / `autofix()` | `prompt_engine/visual_prompt_validator.py` | pages, bible, style | `ValidationResult` + auto-fixed pages |
| 9. Image Gen | `fal_ai_service` | `generate_consistent_image()` | `services/ai/fal_ai_service.py` | prompt, face_url, style, id_weight | image_url |
| 10. Storage | `storage_service` | `upload_base64_image()` | `services/storage_service.py` | image data, path | GCS URL |

### Constants Module (`prompt_engine/constants.py`)

| Constant | Value | Purpose |
|----------|-------|---------|
| `NEGATIVE_PROMPT` | 24 tokens | V2 base negative (legacy, still used in V2 path) |
| `GLOBAL_NEGATIVE_PROMPT_EN` | 30 tokens | V3 base negative (enriched with body/anatomy) |
| `MAX_FAL_PROMPT_CHARS` | 2048 | Fal.ai max prompt length (~512 tokens) |
| `MAX_VISUAL_PROMPT_BODY_CHARS` | 720 | Body section max (prevents style truncation) |
| `COMPOSITION_RULES` | "Wide shot, child 30%..." | Framing directive |
| `BODY_PROPORTION_DIRECTIVE` | "Child in frame, natural..." | Anti-chibi/bobblehead |
| `STYLE_PULID_WEIGHTS` | dict (0.70–0.78) | Per-style id_weight for PuLID |
| `LIKENESS_HINT_WHEN_REFERENCE` | "Same face and hair..." | Injected when face reference present |

### Worker / Storage Modules

| Component | Module | Details |
|-----------|--------|---------|
| Queue | `workers/image_worker.py` | Arq (Redis-backed), `max_jobs=3`, `job_timeout=1800s`, `max_tries=3` |
| Enqueue | `workers/enqueue.py` | `enqueue_trial_preview()`, `enqueue_trial_remaining()` |
| Storage | `services/storage_service.py` | GCS (`benimmasalim-generated-books`), 3 retries w/ exponential backoff |
| DB Model | `models/story_preview.py` | `preview_images` (JSONB), `page_images` (JSONB), `generated_prompts_cache` |
| Fallback | `api/v1/trials.py` | FastAPI `BackgroundTasks` if Arq enqueue fails |

---

## 3. Pipeline Stages (Detailed)

### 3.1 Story Generation (Turkish)

**Entry:** `gemini_service.generate_story_v3()`

The V3 pipeline uses a 3-pass LLM approach:
1. **PASS-1 (Blueprint):** Structured outline — pages, beats, learning outcomes
2. **PASS-2 (Creative):** Full Turkish text per page from blueprint
3. **PASS-3 (Technical):** Image prompts (EN) per page from story + blueprint

**Key Rules Enforced:**
- Family ban (`STORY_NO_FIRST_DEGREE_FAMILY_TR`): No parents/siblings — child adventures alone with mentor/animal companions
- Page count: configurable (default 16: 1 cover + 15 inner)
- Safety: model `gemini-2.0-flash`, `enable_safety_checker=True`
- Retries: Gemini SDK built-in; application-level retry via `rate_limit_retry`

**Output:** `list[FinalPageContent]` carrying `v3_composed=True`, `negative_prompt`, `visual_prompt`

### 3.2 Visual Beat Extraction

**Entry:** `visual_prompt_builder.extract_visual_beat()`

Parses Turkish story text into structured English scene components:
- **Emotion:** `_EMOTION_MAP_TR` (17 entries: heyecan→excited, merak→curious, etc.)
- **Objects:** `_OBJ_MAP` (40+ entries: balon→hot air balloon, peri bacası→fairy chimney, etc.)
- **Environment:** Extracted from blueprint `environment` field or inferred from keywords
- **Action:** Derived from verb patterns in Turkish text

### 3.3 Prompt Enhancement

**Entry:** `visual_prompt_builder.enhance_all_pages()`  
**Core:** `compose_enhanced_prompt()`

Assembly order (9 layers):
1. Strip existing composition/character (prevent double-injection)
2. Kids-safe rewrite (`_kids_safe_rewrite`: 40+ patterns — injuries, crying, fear, violence)
3. Embedded text strip (`_strip_embedded_text`: 7 patterns — quotes, "written on", "the word X")
4. Strip no-text suffix (re-added at end)
5. Character Bible block (verbatim `prompt_block`)
6. Scene description (from VisualBeat or LLM output)
7. Iconic anchors (1-2 per page, context-aware via `pick_anchors`)
8. Camera/composition from ShotPlan (`shot_type`, `camera_angle`, `child_frame_pct`)
9. Style block + "no text, no watermark, no logo" suffix

**Negative Prompt Build:** `build_enhanced_negative()`
- `GLOBAL_NEGATIVE_PROMPT_EN` (base)
- `character_bible.negative_tokens` (character-specific)
- `style_mapping.forbidden_terms` (style-specific)
- Gender-specific additions (male: no dress/skirt; female: no boy/male)
- Cover-specific: extra text-blocking tokens
- Deduplication via `_dedup_negative_tokens()`

### 3.4 Validation & Autofix

**Entry:** `visual_prompt_validator.validate_all()` + `autofix()`

| Rule | ID | Severity | Check | Autofix |
|------|----|----------|-------|---------|
| A | PLACEHOLDER | error | Prompt too short (<50 chars) or generic pattern | No (needs re-generation) |
| B | OUTFIT_LOCK | error | `outfit_text_exact` not found verbatim | Injects outfit text after character name |
| C | SHOT_STREAK | error | 3+ consecutive same shot_type or action | No (needs shot plan adjustment) |
| D | NO_TEXT_MISSING | error | Missing "no text" directive | Appends suffix |
| E | STYLE_MISMATCH | error | Forbidden terms in positive prompt | Removes forbidden terms |
| F | ANCHOR_CONTEXT | warning | Outdoor anchors in underground scene | Removes offending anchors |
| G | EMBEDDED_TEXT | error | Quotes or text-rendering instructions | Strips via `_strip_embedded_text()` |
| — | NEAR_DUPLICATE | warning | >95% word overlap between adjacent pages | No (informational) |

### 3.5 Image Generation (Fal.ai)

**Entry:** `fal_ai_service.FalAIService.generate_consistent_image()`

**Model:** `fal-ai/flux-pulid` (Flux.1 Dev + PuLID face identity)

**Key Parameters:**
| Parameter | Value | Source |
|-----------|-------|--------|
| `num_inference_steps` | 28 | `GenerationConfig` |
| `guidance_scale` | 3.5 | `GenerationConfig` |
| `width × height` | 1024 × 724 | A4 landscape ratio |
| `id_weight` | 0.70–0.78 | `STYLE_PULID_WEIGHTS` or DB override |
| `start_step` | 2 | `PuLIDConfig` (early injection for hair/face) |
| `num_steps` | 4 | `PuLIDConfig` |
| `enable_safety_checker` | true | `GenerationConfig` |

**V3 Path (`skip_compose=True`):**
- Receives pre-composed prompt directly
- No `compose_visual_prompt()` call
- `precomposed_negative` used as-is
- Gender-specific negatives **not** re-appended (already included by V3 builder)

**V2 Path (`skip_compose=False`):**
- Calls `compose_visual_prompt()` for template rendering + style injection
- Appends gender-specific negatives
- Full composition pipeline runs

**id_weight Resolution:**
```
if db.visual_styles.id_weight IS NOT NULL:
    use db value → source="db"
else:
    use get_pulid_weight_for_style(style_modifier) → source="code_fallback"
```

### 3.6 Storage & Workers

**Dispatch Chain:**
```
create_trial()
  → try: enqueue_trial_preview() via Arq (Redis)
  → catch: BackgroundTasks.add_task() as fallback
```

**Storage:** GCS bucket `benimmasalim-generated-books`
- Path: `stories/{story_id}/page_{page_num}.png`
- Upload retries: 3 attempts, exponential backoff (2s, 4s, 8s)

**Idempotency:** Before generating remaining pages, checks `page_images` dict for already-generated pages and skips them.

**Prompt Caching:** `StoryPreview.generated_prompts_cache` stores all 16 prompts after Phase 1 (preview). Phase 2 (remaining) reuses cached prompts + style params — no re-calling Gemini.

---

## 4. Findings & Severity

### Critical (Production impact)

| # | Finding | Location | Impact |
|---|---------|----------|--------|
| C-1 | **V2 legacy path still active in codebase** — `compose_visual_prompt()` + gender negatives applied when `v3_composed=False` or flag not propagated | `fal_ai_service.py:~L170` | Any trial falling to V2 path gets double-composed prompts |
| C-2 | **Prompt truncation at 2048 chars** — long V3 prompts (character bible + style block + anchors + composition) can exceed `MAX_FAL_PROMPT_CHARS` | `visual_prompt_builder.py` → `fal_ai_service.py` | Style block or suffix gets silently cut by Fal.ai |
| C-3 | **No end-to-end prompt length guard in enhance_all_pages** — truncation logging exists at the image-gen layer but the builder doesn't enforce the limit | `visual_prompt_builder.py:enhance_all_pages` | Prompts ship to Fal exceeding 2048 chars |

### High (Quality impact)

| # | Finding | Location | Impact |
|---|---------|----------|--------|
| H-1 | **Style drift in long prompts** — when prompt is truncated, `STYLE:` block at the end is first to be cut, removing style DNA | All styles with long character descriptions | Fal defaults to photorealistic/generic when style block missing |
| H-2 | **NEGATIVE_PROMPT vs GLOBAL_NEGATIVE_PROMPT_EN divergence** — V2 uses `NEGATIVE_PROMPT` (missing "scary, horror, gore"), V3 uses `GLOBAL_NEGATIVE_PROMPT_EN` | `constants.py:L18 vs L72` | V2 path missing safety-critical negative tokens |
| H-3 | **Style-specific negatives not consistently applied** — `adapt_style().forbidden_terms` only used in V3 `build_enhanced_negative()`; V2 path uses `get_style_negative_default()` which has different token lists | `style_adapter.py` vs `constants.py` | V2 watercolor prompts may accidentally contain 3D/CGI tokens |
| H-4 | **Outfit text injection fragile** — `OUTFIT_LOCK` autofix inserts after "named {child_name}" pattern; if prompt structure changes, outfit injection fails silently | `visual_prompt_validator.py:autofix()` | Character outfit inconsistency across pages |
| H-5 | **LLM can still generate text-rendering instructions** — despite `_strip_embedded_text()`, novel patterns (e.g., "lettering on stone", "carved rune spelling") may bypass regex | `visual_prompt_builder.py:_TEXT_QUOTE_PATTERNS` | AI renders readable text in images |

### Medium (Consistency impact)

| # | Finding | Location | Impact |
|---|---------|----------|--------|
| M-1 | **Shot streak detection only on consecutive pages** — non-adjacent pages with same shot/action not flagged | `visual_prompt_validator.py:_check_streaks` | Book can have 70% wide shots if not consecutive |
| M-2 | **Anchor diversity tracked only within single generation call** — `used_anchor_contexts` resets between preview (3 pages) and remaining (13 pages) calls | `visual_prompt_builder.py:enhance_all_pages` | Same anchors may repeat across preview + remaining batches |
| M-3 | **Near-duplicate threshold (95%) too high** — character bible + style block create ~60% shared content, so only identical scenes are caught | `visual_prompt_validator.py:_check_near_duplicates` | Visually similar but textually distinct prompts pass validation |
| M-4 | **`_EMOTION_MAP_TR` covers 17 emotions only** — rarer Turkish emotion words unmapped → defaults to "curious" | `visual_prompt_builder.py:_extract_emotion` | Many pages show same "curious" expression |
| M-5 | **No prompt diff logging** — after autofix, the before/after prompt is not logged | `visual_prompt_validator.py:autofix()` | Cannot audit what autofix changed in production |

### Low (Operational)

| # | Finding | Location | Impact |
|---|---------|----------|--------|
| L-1 | **No distributed tracing** — request ID not propagated through Arq workers | `image_worker.py` | Cannot trace a single trial through story gen → image gen → storage |
| L-2 | **No cost tracking** — Fal.ai/Gemini API costs per trial not logged | `fal_ai_service.py`, `gemini_service.py` | Cannot measure per-trial cost |
| L-3 | **DB `visual_styles.id_weight` column nullable** — admin can set NULL to get code fallback, but no UI makes this visible | `models/visual_style.py` | Admins unaware of effective id_weight per style |
| L-4 | **No Arq queue depth monitoring** — no metrics endpoint for queue depth/lag | `workers/image_worker.py` | Cannot alert on queue backlog |

---

## 5. Root-Cause Analysis

### 5.1 Style Drift

**Symptom:** Watercolor prompt produces Pixar-like images; anime prompt produces flat 2D.

**Root Causes:**
1. **Truncation removes STYLE: block.** Fal.ai has a 512-token (~2048 char) limit. The V3 pipeline builds prompts as: `leading_prefix` + `character_bible` + `scene` + `anchors` + `composition` + `STYLE: block` + `suffix`. When total exceeds 2048, Fal silently truncates from the end — the `STYLE:` block and `no text` suffix are lost first.

2. **`leading_prefix` and `style_block` contain overlapping tokens.** For Pixar: `leading_prefix` says "Pixar-quality 3D CGI" AND `style_block` says "Pixar 3D CGI children's book." When one is truncated, the remaining style signal is weaker.

3. **V2 path has no style_block injection.** If a trial falls to V2 (flag not set), `compose_visual_prompt()` uses `StyleConfig.prefix/suffix` which are different from `StyleMapping.style_block`.

**Evidence:** `constants.py:L260-267` (PIXAR_STYLE has 6 separate style-carrying fields), `MAX_FAL_PROMPT_CHARS=2048` at `constants.py:L51`.

### 5.2 Repetitive Composition

**Symptom:** Multiple pages show identical framing — "wide shot, child 30%, environment 70%."

**Root Causes:**
1. **COMPOSITION_RULES is a static string** injected into every page: `"Wide shot, child 30% of frame, environment 70%."` This is the same across all pages.

2. **ShotPlan diversity is limited.** `build_shot_plan()` rotates through `_SHOT_ROTATION` but the final prompt always includes `COMPOSITION_RULES` as a fixed block, overriding shot-plan variations.

3. **Near-duplicate detection threshold too high (95%).** When ~60% of every prompt is identical boilerplate (bible + style + composition), even moderately different scenes don't trigger the warning.

**Evidence:** `constants.py:L62-66` (COMPOSITION_RULES), `visual_prompt_builder.py:compose_enhanced_prompt()` always injects `ShotPlan.prompt_fragment` but also has static composition parts.

### 5.3 Truncation

**Symptom:** Some pages miss "no text, no watermark, no logo" suffix in final image; style block absent.

**Root Causes:**
1. **No pre-flight length check in `enhance_all_pages()`.** The builder assembles the full prompt but does not check against `MAX_FAL_PROMPT_CHARS` before returning. The guard only exists at the image-gen layer.

2. **Character bible can be long.** With detailed appearance tokens + outfit, `CharacterBible.prompt_block` can be 200-400 chars. Combined with style block (100-200 chars) and scene (200-400 chars), total easily exceeds 2048.

3. **Truncation happens silently at Fal.ai.** When logged at image-gen level, it's too late — the prompt is already submitted.

**Evidence:** `constants.py:L49-53` (MAX_FAL_PROMPT_CHARS=2048, MAX_VISUAL_PROMPT_BODY_CHARS=720), `fal_ai_service.py` has a length guard with logging but it's a post-hoc check.

### 5.4 id_weight Override

**Symptom:** All styles render with same face preservation strength; watercolor/pastel appear with disproportionate face features.

**Root Cause (FIXED):**
- DB seeds had `id_weight=0.90` for all visual styles, overriding the per-style code weights (watercolor=0.72, soft_pastel=0.74, pixar=0.78).
- **Fix applied:** Alembic migration `048_fix_id_weight_null_for_code_fallback.py` sets `visual_styles.id_weight = NULL` for all seeded styles.
- Runtime now: `NULL` → falls back to `get_pulid_weight_for_style()` which returns per-style values from `STYLE_PULID_WEIGHTS`.
- Logging added: `ID_WEIGHT_RESOLVED` event with `source="db"` or `source="code_fallback"`.

**Current State:** Fixed. Per-style weights now active: watercolor=0.72, pastel=0.74, anime=0.76, pixar=0.78.

### 5.5 Negative Prompt Mismatch

**Symptom:** V2 path missing safety negatives; V3 path missing some style-specific negatives.

**Root Causes:**
1. **Two separate negative constants.** `NEGATIVE_PROMPT` (V2) and `GLOBAL_NEGATIVE_PROMPT_EN` (V3) evolved independently. V2 is missing: "scary, horror, gore, violence, weapon."

2. **Gender negatives applied differently.** V2 path appends gender negatives in `fal_ai_service.py`. V3 path includes them in `build_enhanced_negative()`. If a V3 prompt somehow hits the V2 path (edge case), gender negatives are doubled.

3. **Cover text-blocking tokens only in V3.** `_COVER_TEXT_BLOCKING` is added by `build_enhanced_negative(is_cover=True)` but V2 path has no equivalent.

**Current State:** Partially fixed. V3 path now has unified negative builder. V2 path still uses old constants.

---

## 6. Proposed Fix Plan

### Phase 1: Prompt Length Safety (Fixes C-2, C-3, H-1)

- [ ] **P1.1** Add `_enforce_length_limit()` in `enhance_all_pages()` that truncates the prompt *before* the style block, preserving `STYLE:` block + suffix at the end.
- [ ] **P1.2** Implement token budget allocation: `MAX_FAL_PROMPT_CHARS` split as: `leading_prefix` (max 250) + `body` (max 720) + `style_block` (max 200) + `suffix` (max 50) = 1220 chars with 828 chars buffer for character bible + composition.
- [ ] **P1.3** Add per-page prompt length to `enhance_all_pages()` output metadata for logging.
- [ ] **P1.4** Log warning when any prompt exceeds 1800 chars (pre-truncation soft limit).

### Phase 2: Composition Diversity (Fixes M-1, M-2, M-3)

- [ ] **P2.1** Replace static `COMPOSITION_RULES` with per-page composition derived from `ShotPlan` — remove the fixed "Wide shot, child 30%" for non-wide shots.
- [ ] **P2.2** Add global shot-distribution check: book must have at least 3 different shot types across all pages.
- [ ] **P2.3** Persist `used_anchor_contexts` in `generated_prompts_cache` so Phase 2 (remaining pages) continues diversity from Phase 1 (preview pages).
- [ ] **P2.4** Lower near-duplicate threshold to 85% or use TF-IDF with boilerplate removal before comparison.

### Phase 3: V2 Deprecation (Fixes C-1, H-2, H-3)

- [ ] **P3.1** Add `settings.use_blueprint_pipeline` default to `True` in production config.
- [ ] **P3.2** Add deprecation warning log to V2 path (`compose_visual_prompt` codepath).
- [ ] **P3.3** Unify `NEGATIVE_PROMPT` and `GLOBAL_NEGATIVE_PROMPT_EN` — make `NEGATIVE_PROMPT` a re-export of `GLOBAL_NEGATIVE_PROMPT_EN`.
- [ ] **P3.4** After 30 days of V3-only production: remove V2 codepath (`compose_visual_prompt`, V2 templates, `generate_story_structured`).

### Phase 4: Robustness (Fixes H-4, H-5, M-4, M-5)

- [ ] **P4.1** Add LLM-based fallback for embedded text detection — if regex misses, a lightweight classifier (e.g., Gemini Flash function call) checks for text-rendering intent.
- [ ] **P4.2** Expand `_EMOTION_MAP_TR` to 30+ entries; add fuzzy matching for unlisted emotions.
- [ ] **P4.3** Log prompt before/after autofix diff (structured log with `page`, `rule`, `chars_removed`, `before_hash`, `after_hash`).
- [ ] **P4.4** Add outfit injection test with varied prompt structures (not just "named X" pattern).

### Phase 5: Operational (Fixes L-1, L-2, L-3, L-4)

- [ ] **P5.1** Propagate `trace_id` (UUID) from `create_trial()` through Arq job → image gen → storage for distributed tracing.
- [ ] **P5.2** Log estimated Fal.ai cost per image (based on model + inference steps + resolution).
- [ ] **P5.3** Add `/admin/styles/effective-weights` endpoint showing effective id_weight per style (DB vs code fallback).
- [ ] **P5.4** Expose Arq queue metrics via Prometheus endpoint (`arq_queue_depth`, `arq_job_duration_seconds`, `arq_job_failures_total`).

---

## 7. Test Plan

### Unit Tests (Existing: 397 passing)

| Test File | Count | Coverage |
|-----------|-------|----------|
| `test_kids_safe_no_text.py` | 32 | Injury rewrite, text stripping, validator Rule G, autofix |
| `test_v3_no_double_compose.py` | 17 | V3 bypass of compose_visual_prompt, truncation logging |
| `test_v3_negative_unity.py` | 40 | Unified negative build, gender, cover, dedup |
| `test_id_weight_resolution.py` | 17 | Per-style weights, DB override, code fallback |
| `test_anchors_context_aware.py` | 68 | Scene classification, compatibility, diversity |
| `test_visual_composer.py` | Various | V2 composition, template rendering |
| `test_fal_builder.py` | Various | Fal request building, dimensions |
| `test_negative.py` | Various | V2 negative prompt tokens |

### Tests to Add

| Area | Test Description | Priority |
|------|-----------------|----------|
| Truncation | Prompt > 2048 chars → style block preserved, body truncated | P1 |
| Truncation | Prompt length logged with metadata per page | P1 |
| Composition diversity | Book of 16 pages has >= 3 distinct shot types | P2 |
| Composition diversity | Anchors vary across preview + remaining batches | P2 |
| V2 deprecation | V2 path logs deprecation warning | P3 |
| Emotion mapping | 30+ Turkish emotions mapped correctly | P4 |
| Autofix logging | Before/after hash logged for every fix | P4 |
| End-to-end | Full trial: story gen → prompt → Fal request validates all rules | P5 |

### Integration Tests (Missing)

| Test | Description |
|------|-------------|
| **Trial E2E** | Create trial → verify all 3 preview prompts pass `validate_all()` → verify Fal request payload matches expected schema |
| **Arq Worker** | Enqueue job → verify worker picks up → verify GCS upload → verify DB updated |
| **Style Consistency** | Generate 16 prompts for each of 6 styles → verify style_block present in all, forbidden_terms absent |

---

## 8. Observability Metrics

### Currently Logged

| Event | Logger | Fields |
|-------|--------|--------|
| `V3_PROMPT_LENGTH` | `gemini_service` | `page`, `prompt_len`, `truncated`, `chars_removed` |
| `V3_STYLE_BLOCK_CHECK` | `gemini_service` | `page`, `has_style_block` |
| `ID_WEIGHT_RESOLVED` | `fal_ai_service` | `id_weight`, `source`, `style_modifier` |
| `REMAINING_PAGES_IDEMPOTENCY` | `trials` | `already_generated`, `to_generate` |
| `REMAINING_STYLE_FROM_CACHE` | `trials` | `style_modifier`, `id_weight` |
| `ARQ_TASK_START/DONE/FAILED` | `image_worker` | `job_id`, `trial_id`, `duration` |

### Metrics to Add

| Metric | Type | Labels | Purpose |
|--------|------|--------|---------|
| `pipeline_prompt_length_chars` | histogram | `page_type`, `style` | Track prompt lengths across styles |
| `pipeline_prompt_truncated_total` | counter | `style`, `truncation_type` | Alert on frequent truncation |
| `pipeline_validation_failures_total` | counter | `rule`, `severity` | Track which rules fail most |
| `pipeline_autofix_applied_total` | counter | `rule` | Track autofix frequency |
| `pipeline_image_gen_duration_seconds` | histogram | `provider`, `style` | Fal.ai latency per style |
| `pipeline_image_gen_failures_total` | counter | `provider`, `error_type` | Rate limit / timeout tracking |
| `pipeline_arq_queue_depth` | gauge | `queue_name` | Queue backlog monitoring |
| `pipeline_arq_job_duration_seconds` | histogram | `job_type` | Worker performance |
| `pipeline_cost_per_image_usd` | histogram | `provider`, `model` | Cost tracking |
| `pipeline_style_block_missing_total` | counter | `style` | Style drift detection |

### Structured Log Enhancements

```python
# Add to enhance_all_pages() output
logger.info("V3_ENHANCEMENT_COMPLETE",
    total_pages=len(pages),
    avg_prompt_len=avg_len,
    max_prompt_len=max_len,
    truncated_count=truncated,
    validation_passed=result.passed,
    autofix_count=len(fixes),
    style=style_mapping.style_tag,
)

# Add to autofix()
logger.info("AUTOFIX_APPLIED",
    page=issue.page,
    rule=issue.rule,
    before_len=len(original),
    after_len=len(fixed),
    chars_removed=len(original) - len(fixed),
)
```

---

## Appendix: File Reference Index

| File | Lines | Role |
|------|-------|------|
| `backend/app/services/ai/gemini_service.py` | ~800 | Story generation (V2+V3), FinalPageContent |
| `backend/app/prompt_engine/visual_prompt_builder.py` | ~710 | V3 enhancement pipeline core |
| `backend/app/prompt_engine/visual_prompt_composer.py` | ~300 | V2 composition (legacy) |
| `backend/app/prompt_engine/visual_prompt_validator.py` | ~460 | Validation + autofix (Rules A-G) |
| `backend/app/prompt_engine/constants.py` | ~720 | All prompt constants, style configs, PuLID weights |
| `backend/app/prompt_engine/character_bible.py` | ~200 | Character identity persistence |
| `backend/app/prompt_engine/style_adapter.py` | ~310 | Style resolution + mapping |
| `backend/app/prompt_engine/scene_director.py` | ~250 | Shot planning + camera diversity |
| `backend/app/prompt_engine/iconic_anchors.py` | ~300 | Location-specific anchor selection |
| `backend/app/services/ai/fal_ai_service.py` | ~1250 | Fal.ai PuLID image generation |
| `backend/app/services/ai/gemini_consistent_image.py` | ~400 | Gemini Flash image generation |
| `backend/app/api/v1/trials.py` | ~2290 | Trial API + worker dispatch |
| `backend/app/workers/image_worker.py` | ~200 | Arq worker definitions |
| `backend/app/workers/enqueue.py` | ~150 | Job enqueueing functions |
| `backend/app/services/storage_service.py` | ~300 | GCS upload with retry |
| `backend/app/models/story_preview.py` | ~120 | DB model for preview/page images |

---

*Report generated by pipeline audit — 2026-02-17.*

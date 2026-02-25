# PROMPT LEFTOVERS AUDIT — PHASE-0.5 (Final)

> Generated: 2026-02-05  
> Scope: `backend/` only (app, tests, scripts, alembic, models)  
> Mode: **READ-ONLY** — zero code changes

---

## A) Summary

**Leftovers found: 47 unique prompt-system artifacts**

Every artifact is classified as either:

| Tag | Meaning |
|-----|---------|
| `PROMPT_SYSTEM` | Dedicated prompt composition / sanitization / validation module — candidate for deletion or rewire into `prompt_engine` |
| `AI_PIPELINE_CORE` | Essential AI pipeline logic (generation, API calls, DB columns, admin CRUD) — keep as-is |
| `MIGRATION_SCRIPT` | One-off or backfill script — keep for history or mark as obsolete |
| `OBSERVABILITY` | Debug / manifest columns used for pipeline tracing — keep |

---

## B-1) File / Folder Scan

### Prompt-dedicated modules (PROMPT_SYSTEM)

| # | File Path | Why Matched | Referenced By | Action |
|---|-----------|-------------|---------------|--------|
| 1 | `app/core/prompt_sanitizer.py` | Entire file: `sanitize_visual_prompt`, `CINEMATIC_LENS_TERMS`, `STRICT_NEGATIVE_ADDITIONS`, `get_strict_negative_additions`, `truncate_safe_2d`, `INNER_PAGE_STRIP_*` | `visual_prompt_composer.py`, `fal_ai_service.py` (L767), tests × 3 | **REWIRE** → absorb into `prompt_engine` |
| 2 | `app/core/visual_prompt_composer.py` | Entire file: `compose_visual_prompt`, `normalize_location`, `validate_no_placeholders`, `validate_cover_inner_phrases`, `render_template`, `get_display_visual_prompt`, `LIKENESS_HINT_WHEN_REFERENCE` | `ai.py` (L761, L1181), `orders.py` (L13), `admin/orders.py` (L40), `fal_ai_service.py` (L795, L1092), `fal_service.py` (×5), `gemini_image_service.py` (×3), tests × 2 | **REWIRE** → becomes `prompt_engine` core |
| 3 | `app/prompt_engine/README.md` | Design stub created in Phase-0 | — | **KEEP** (design doc for new engine) |
| 4 | `app/core/sanitizer.py` | Input sanitization for prompt injection (L1-60: `PROMPT_INJECTION_PATTERNS`, dangerous-char filter) | `ai.py` (L14), `gemini_service.py` (L30) | **KEEP** — security layer, not prompt composition |

### Prompt template system (AI_PIPELINE_CORE — admin-editable prompts)

| # | File Path | Why Matched | Referenced By | Action |
|---|-----------|-------------|---------------|--------|
| 5 | `app/models/prompt_template.py` | ORM model `PromptTemplate`, `PromptCategory` enum | `__init__.py`, `prompt_template_service.py`, `admin/prompts.py`, scripts × 2 | **KEEP** — admin CRUD for AI prompts |
| 6 | `app/services/prompt_template_service.py` | `PromptTemplateService`: cache + render + variable defs for admin-editable prompt templates | `gemini_service.py` (L615), `admin/prompts.py` (L300, L318, L341, L567) | **KEEP** — dynamic prompt management |
| 7 | `app/api/v1/admin/prompts.py` | Admin CRUD routes for `prompt_templates` + seed-defaults + `NEGATIVE_PROMPT` constant (L459) | Admin router | **KEEP** — admin panel feature |

### Style system embedded in fal_ai_service (AI_PIPELINE_CORE)

| # | File Path | Lines | Why Matched | Action |
|---|-----------|-------|-------------|--------|
| 8 | `app/services/ai/fal_ai_service.py` | L128-190 | `NEGATIVE_PROMPT`, `ANTI_REALISTIC_NEGATIVE`, `ANTI_ANIME_NEGATIVE`, `get_style_specific_negative` | **REWIRE** → extract to `prompt_engine/negatives.py` |
| 9 | `app/services/ai/fal_ai_service.py` | L237-470 | `StyleConfig` dataclass, `DEFAULT_STYLE`, `WATERCOLOR_STYLE`, `PIXAR_STYLE`, `SUPERHERO_STYLE`, `ANIME_STYLE`, `REALISTIC_STYLE`, `STYLE_PULID_WEIGHTS`, `get_pulid_weight_for_style`, `FluxPromptBuilder` | **REWIRE** → extract to `prompt_engine/styles.py` + `prompt_engine/flux_builder.py` |
| 10 | `app/services/ai/fal_ai_service.py` | L1423-1475 | `_build_full_prompt` (internal prompt composition with location keyword detection) | **REWIRE** → move to `prompt_engine` |
| 11 | `app/services/ai/fal_ai_service.py` | L787-810 | `compose_visual_prompt` call inside `generate_consistent_image`, negative suffix merge | **REWIRE** — call site remains, composition moves to engine |

### Image generator legacy prompt builder (AI_PIPELINE_CORE)

| # | File Path | Lines | Why Matched | Action |
|---|-----------|-------|-------------|--------|
| 12 | `app/services/ai/image_generator.py` | L153-180 | `BaseImageGenerator._build_full_prompt` — appends style + quality + negative | **REWIRE** → replace with `prompt_engine` compose |

### Gemini service prompt methods (AI_PIPELINE_CORE)

| # | File Path | Lines | Why Matched | Action |
|---|-----------|-------|-------------|--------|
| 13 | `app/services/ai/gemini_service.py` | L1235-1250 | `_build_safe_visual_prompt` — scene-only visual prompt composer | **REWIRE** → move to `prompt_engine` |
| 14 | `app/services/ai/gemini_service.py` | L1252-1310 | `_compose_visual_prompts` — iterates pages, adds outfit/cultural hint, style-keyword contamination check | **REWIRE** → move to `prompt_engine` |
| 15 | `app/services/ai/gemini_service.py` | L583-615 | `PromptTemplateService` usage for dynamic system prompts | **KEEP** — AI pipeline core |

### Scripts (MIGRATION_SCRIPT)

| # | File Path | Why Matched | Action |
|---|-----------|-------------|--------|
| 16 | `scripts/backfill_visual_prompt_strip_style.py` | One-off backfill: strips style tokens from stored `visual_prompt` in `story_pages` | **DELETE** — one-off migration, already run |
| 17 | `scripts/update_prompts_for_fal.py` | One-off: updates scenario templates + visual style modifiers for Flux pipeline | **DELETE** — one-off migration |
| 18 | `scripts/sync_outcomes_prompts.py` | Syncs `learning_outcomes` ↔ `prompt_templates` | **KEEP** — still needed for admin sync |
| 19 | `scripts/update_all_styles_and_scenarios.py` | Comprehensive style + scenario seed with Kapadokya prompts, `STYLE_PULID_WEIGHTS` | **REWIRE** → will need update when `prompt_engine` lands |

### Scenario model prompt templates (AI_PIPELINE_CORE)

| # | File Path | Lines | Why Matched | Action |
|---|-----------|-------|-------------|--------|
| 20 | `app/models/scenario.py` | L99-133 | `cover_prompt_template`, `page_prompt_template`, `ai_prompt_template` columns | **KEEP** — Gemini input templates (scenario-level) |

### Visual style admin routes (AI_PIPELINE_CORE)

| # | File Path | Why Matched | Action |
|---|-----------|-------------|--------|
| 21 | `app/api/v1/admin/visual_styles.py` | CRUD for `VisualStyle` model (prompt_modifier, id_weight) | **KEEP** — admin feature |
| 22 | `app/api/v1/scenarios.py` L238 | `GET /visual-styles` public route | **KEEP** |

### Book generation task (AI_PIPELINE_CORE)

| # | File Path | Lines | Why Matched | Action |
|---|-----------|-------|-------------|--------|
| 23 | `app/tasks/generate_book.py` | L27, L216-222 | Imports `FluxPromptBuilder`, calls `convert_tags_to_natural` | **REWIRE** — update import path when `FluxPromptBuilder` moves |

### Service __init__ re-exports (AI_PIPELINE_CORE)

| # | File Path | Lines | Why Matched | Action |
|---|-----------|-------|-------------|--------|
| 24 | `app/services/ai/__init__.py` | L19, L54 | Re-exports `FluxPromptBuilder` | **REWIRE** — update when `FluxPromptBuilder` moves |

---

## B-2) Code Reference Scan (Symbols)

### `compose_visual_prompt` — 15 call sites

| # | File | Line(s) | Caller / Context |
|---|------|---------|------------------|
| 1 | `app/core/visual_prompt_composer.py` | 99-144 | Definition |
| 2 | `app/api/v1/ai.py` | 761-767 | `test_structured_story_generation` response builder |
| 3 | `app/api/v1/ai.py` | 1181-1182 | `test_image` endpoint |
| 4 | `app/services/ai/fal_ai_service.py` | 797-800 | `generate_consistent_image` |
| 5 | `app/services/ai/fal_ai_service.py` | 1092-1093 | `generate_image_with_composed_prompt` |
| 6 | `app/services/ai/fal_service.py` | 76-77, 130-131, 256-257, 418-419, 482-483 | 5 generation methods |
| 7 | `app/services/ai/gemini_image_service.py` | 125-126, 298-299, 487-488 | 3 Imagen generation methods |
| 8 | `tests/test_visual_prompt_composer.py` | multiple | Unit tests |
| 9 | `tests/test_style_independence.py` | 53, 70, 85, 91, 102, 111 | Style independence tests |

### `sanitize_visual_prompt` — 4 call sites

| # | File | Line(s) | Context |
|---|------|---------|---------|
| 1 | `app/core/prompt_sanitizer.py` | 75-111 | Definition |
| 2 | `app/core/visual_prompt_composer.py` | 10, 138 | Import + call in `compose_visual_prompt` |
| 3 | `tests/test_prompt_sanitizer.py` | 7, 47, 55, 63, 72, 85, 93, 102 | Unit tests |

### `STRICT_NEGATIVE_ADDITIONS` / `get_strict_negative_additions` — 5 references

| # | File | Line(s) | Context |
|---|------|---------|---------|
| 1 | `app/core/prompt_sanitizer.py` | 66-72, 114-116 | Definition |
| 2 | `app/core/visual_prompt_composer.py` | 10, 141 | Import + call |
| 3 | `tests/test_preview_detail_response.py` | 9, 48-50 | Asserts typographic present |
| 4 | `tests/test_e2e_preview_detail.py` | 12, 98-100 | Same assertion |

### `FluxPromptBuilder` — 10 references

| # | File | Line(s) | Context |
|---|------|---------|---------|
| 1 | `app/services/ai/fal_ai_service.py` | 430-530 | Definition (class + static methods) |
| 2 | `app/services/ai/fal_ai_service.py` | 538, 543, 557, 562, 696, 816, 1469 | Internal usage |
| 3 | `app/services/ai/__init__.py` | 19, 54 | Re-export |
| 4 | `app/tasks/generate_book.py` | 27, 216-222 | Import + `convert_tags_to_natural` |

### `normalize_location` — 4 references

| # | File | Line(s) | Context |
|---|------|---------|---------|
| 1 | `app/core/visual_prompt_composer.py` | 62-69 | Definition |
| 2 | `app/core/visual_prompt_composer.py` | 131 | Called in `compose_visual_prompt` |
| 3 | `tests/test_visual_prompt_composer.py` | 9, 49-57 | Unit tests |

### `VisualPromptValidationError` — 4 references

| # | File | Line(s) | Context |
|---|------|---------|---------|
| 1 | `app/core/visual_prompt_composer.py` | 33-37 | Definition |
| 2 | `app/core/visual_prompt_composer.py` | 56, 81, 89 | Raised in validation functions |
| 3 | `app/api/v1/orders.py` | 13, 589, 904 | Import + catch in background tasks |
| 4 | `tests/test_visual_prompt_composer.py` | 6, 18, 25, 30, 35, 72, 78, 87, 92 | Unit tests |

### `prompt_debug_json` — 10 references

| # | File | Line(s) | Context | Classification |
|---|------|---------|---------|----------------|
| 1 | `app/models/story_preview.py` | 154 | Column definition | OBSERVABILITY — KEEP |
| 2 | `app/api/v1/orders.py` | 529, 545, 551, 578, 702, 992-993 | Collector + DB persist | OBSERVABILITY — KEEP |
| 3 | `app/api/v1/admin/orders.py` | 43, 175 | Read for display | OBSERVABILITY — KEEP |
| 4 | `app/core/visual_prompt_composer.py` | 154 | Docstring ref | PROMPT_SYSTEM — REWIRE |
| 5 | `scripts/backfill_visual_prompt_strip_style.py` | 4-5 | Comment | MIGRATION_SCRIPT — DELETE |
| 6 | `tests/test_visual_prompt_composer.py` | 169-175 | Test `get_display_visual_prompt` | PROMPT_SYSTEM — REWIRE tests |
| 7 | `alembic/versions/021_*` | 1-32 | Migration | OBSERVABILITY — KEEP |

### `generation_manifest_json` — 9 references

| # | File | Line(s) | Context | Classification |
|---|------|---------|---------|----------------|
| 1 | `app/models/story_preview.py` | 158 | Column definition | OBSERVABILITY — KEEP |
| 2 | `app/api/v1/orders.py` | 713-714, 1003-1004 | DB persist | OBSERVABILITY — KEEP |
| 3 | `app/api/v1/admin/orders.py` | 65, 175, 312 | Read for display | OBSERVABILITY — KEEP |
| 4 | `tests/test_preview_detail_response.py` | 23, 29 | Test | OBSERVABILITY — KEEP |
| 5 | `tests/test_e2e_preview_detail.py` | 21, 38, 82-84 | E2E test | OBSERVABILITY — KEEP |
| 6 | `alembic/versions/022_*` | 1-32 | Migration | OBSERVABILITY — KEEP |
| 7 | `scripts/backfill_visual_prompt_strip_style.py` | 4 | Comment | MIGRATION_SCRIPT — DELETE |

### `_build_safe_visual_prompt` / `_build_full_prompt`

| # | File | Line(s) | Context | Classification |
|---|------|---------|---------|----------------|
| 1 | `app/services/ai/gemini_service.py` | 1235-1250 | Definition (scene-only composer) | PROMPT_SYSTEM — REWIRE |
| 2 | `app/services/ai/gemini_service.py` | 1372, 1383 | Call sites inside story generation | AI_PIPELINE_CORE |
| 3 | `app/services/ai/fal_ai_service.py` | 1423-1475 | Definition (Fal full prompt with keyword detection) | PROMPT_SYSTEM — REWIRE |
| 4 | `app/services/ai/fal_ai_service.py` | 787 | Call site | AI_PIPELINE_CORE |
| 5 | `app/services/ai/image_generator.py` | 153-180 | Legacy builder (style+quality+negative) | PROMPT_SYSTEM — REWIRE |
| 6 | `app/services/ai/image_generator.py` | 217, 326, 452, 502 | Call sites | AI_PIPELINE_CORE |
| 7 | `tests/test_style_independence.py` | 32, 38 | Test of `_build_safe_visual_prompt` | PROMPT_SYSTEM |

### `LIKENESS_HINT_WHEN_REFERENCE`

| # | File | Line(s) | Context |
|---|------|---------|---------|
| 1 | `app/core/visual_prompt_composer.py` | 96 | Definition |
| 2 | `app/services/ai/fal_ai_service.py` | 796, 799 | Import + use |
| 3 | `tests/test_style_independence.py` | 9, 89 | Import + test |

### `StyleConfig` / Style constants

| # | File | Line(s) | Context |
|---|------|---------|---------|
| 1 | `app/services/ai/fal_ai_service.py` | 237-310 | 6 style definitions (dataclass + constants) |
| 2 | `app/services/ai/fal_ai_service.py` | 314-414 | `STYLE_PULID_WEIGHTS` + `get_pulid_weight_for_style` |
| 3 | `app/models/scenario.py` | 54 | Comment referencing `StyleConfig` |
| 4 | `app/tasks/generate_book.py` | 10 | Docstring referencing `StyleConfig` |

---

## B-3) API Routes Scan

Routes that accept / emit prompt-related fields:

| # | Controller Method | Route | Prompt-Related Fields | Module Used | Classification |
|---|-------------------|-------|-----------------------|-------------|----------------|
| 1 | `ai.py` `test_structured_story_generation` | `POST /test-story-structured` | accepts `visual_style`, emits `visual_prompt` per page | `compose_visual_prompt` | PROMPT_SYSTEM (compose call) |
| 2 | `ai.py` `test_image` | `POST /test-image` | accepts prompt, emits composed image | `compose_visual_prompt` | PROMPT_SYSTEM (compose call) |
| 3 | `ai.py` `test_image_fal` | `POST /test-image-fal` | accepts `child_photo_url`, `visual_style` | → `fal_ai_service.generate_consistent_image` → compose | AI_PIPELINE_CORE |
| 4 | `ai.py` `test_fal_session` | `POST /test-fal-session` | accepts `child_photo_url`, `visual_style_modifier` | → `fal_ai_service` | AI_PIPELINE_CORE |
| 5 | `orders.py` `submit_preview_async` | `POST /submit-preview-async` | accepts `visual_style`, `child_photo_url`, `story_pages[].visual_prompt` | → `fal_ai_service` → `compose_visual_prompt` via prompt_debug | PROMPT_SYSTEM (compose + debug) |
| 6 | `orders.py` `send_preview` | `POST /send-preview` | accepts same fields | → same chain | PROMPT_SYSTEM (compose + debug) |
| 7 | `orders.py` `confirm/{token}` | `GET /confirm/{token}` | reads `visual_prompt` from stored pages | — | AI_PIPELINE_CORE |
| 8 | `admin/orders.py` previews | `GET /previews*` | emits `prompt_debug_json`, `generation_manifest_json`, visual_prompt via `_story_pages_for_display` | `get_display_visual_prompt` | PROMPT_SYSTEM (display helper) |
| 9 | `admin/prompts.py` CRUD | `GET/POST/PUT/DELETE /prompts/*` | Full CRUD for `prompt_templates` table | `PromptTemplate` model | AI_PIPELINE_CORE — KEEP |
| 10 | `admin/visual_styles.py` CRUD | `GET/POST/PATCH/DELETE /visual-styles/*` | CRUD for `visual_styles` (prompt_modifier, id_weight) | `VisualStyle` model | AI_PIPELINE_CORE — KEEP |
| 11 | `trials.py` `create_trial` | `POST /trials/create` | accepts `visual_style`, `child_photo_url`, `story_pages[].visual_prompt` | → `fal_ai_service` | AI_PIPELINE_CORE |
| 12 | `admin/book_config.py` | `POST/PATCH /ai-configs` | accepts `negative_prompt` field | `AIConfig` model | AI_PIPELINE_CORE — KEEP |
| 13 | `admin/scenarios.py` | `POST/PATCH /scenarios` | accepts `cover_prompt_template`, `page_prompt_template` | `Scenario` model | AI_PIPELINE_CORE — KEEP |
| 14 | `ai.py` `generate_story` | `POST /generate-story` | internal Gemini call, no direct prompt field in response | `GeminiService` | AI_PIPELINE_CORE |
| 15 | `ai.py` `generate_cover` | `POST /generate-cover` | checks `child_photo_url` | → `fal_ai_service` | AI_PIPELINE_CORE |

---

## B-4) DB / Migrations Scan

### Prompt-system columns on `story_previews`

| Column | Migration | Purpose | Classification | Action |
|--------|-----------|---------|----------------|--------|
| `prompt_debug_json` (JSONB) | `021_add_prompt_debug_json_to_story_preview.py` | Per-page final_prompt + negative for debugging | OBSERVABILITY | **KEEP** |
| `generation_manifest_json` (JSONB) | `022_add_generation_manifest_json_to_story_preview.py` | Per-page provider/model/size/hashes | OBSERVABILITY | **KEEP** |
| `generated_prompts_cache` (JSONB) | `017_try_before_you_buy.py` (L37) | Cache of Gemini-generated prompts for preview | AI_PIPELINE_CORE | **KEEP** |

### `prompt_templates` table

| Migration | Purpose | Action |
|-----------|---------|--------|
| `014_add_prompt_templates.py` | Creates `prompt_templates` table + initial seeds | **KEEP** — admin feature |
| `015_seed_full_prompt_templates.py` | Seeds educational + system prompts | **KEEP** |

### Scenario prompt template columns

| Column | Migration | Purpose | Action |
|--------|-----------|---------|--------|
| `cover_prompt_template` | `baf6123b9d1f_add_cover_and_page_prompt_templates_to_.py` | Per-scenario cover image template | **KEEP** — scenario config |
| `page_prompt_template` | same | Per-scenario inner page template | **KEEP** |
| `ai_prompt_template` | `001_initial_schema.py` (L93) | AI director system prompt per scenario | **KEEP** |
| `ai_prompt` → `image_prompt` | `003_update_order_pages_for_preview.py` | Rename on `order_pages` | **KEEP** — historical |

### Other prompt-related columns

| Table | Column | Migration | Action |
|-------|--------|-----------|--------|
| `visual_styles` | `prompt_modifier` | `001_initial_schema.py` (L125) | **KEEP** — admin feature |
| `visual_styles` | `id_weight` | `019_add_id_weight_to_visual_styles.py` | **KEEP** |
| `learning_outcomes` | `ai_prompt` | `002_update_learning_outcomes.py` | **KEEP** |
| `learning_outcomes` | `ai_prompt_instruction` | `011_add_learning_outcome_visual_assets.py` | **KEEP** |
| `ai_configs` | `negative_prompt` | `004_add_book_templates.py` (L88) | **KEEP** — admin configurable |

---

## B-5) Tests & Docs Scan

| # | File | What It Tests | Classification | Action |
|---|------|--------------|----------------|--------|
| 1 | `tests/test_prompt_sanitizer.py` | `sanitize_visual_prompt`: banned tokens stripped, 2D preserved, Kapadokya→Cappadocia | PROMPT_SYSTEM | **REWIRE** — move to `prompt_engine` test suite |
| 2 | `tests/test_visual_prompt_composer.py` | `compose_visual_prompt`, `normalize_location`, `validate_no_placeholders`, `validate_cover_inner_phrases`, `render_template`, `get_display_visual_prompt` | PROMPT_SYSTEM | **REWIRE** — move to `prompt_engine` test suite |
| 3 | `tests/test_style_independence.py` | Scene-only invariant (no style tokens in Gemini output), style injected at compose, likeness hint, Kapadokya normalization | PROMPT_SYSTEM | **REWIRE** — adapt for `prompt_engine` |
| 4 | `tests/test_preview_detail_response.py` | Cache-bust + manifest shape + `STRICT_NEGATIVE_ADDITIONS` typographic check | OBSERVABILITY + PROMPT_SYSTEM | **UPDATE** — keep manifest tests, update negative import |
| 5 | `tests/test_e2e_preview_detail.py` | E2E: preview detail returns manifest + strict negative includes typographic | OBSERVABILITY + PROMPT_SYSTEM | **UPDATE** — same as above |
| 6 | `app/prompt_engine/README.md` | Design stub for new prompt engine architecture | DOCUMENTATION | **KEEP** |
| 7 | `docs/PROMPT_SYSTEM_API_INVENTORY.md` | Phase-0 API inventory | DOCUMENTATION | **KEEP** |
| 8 | `docs/PROMPT_COMPOSITION_FLOW_MAP.md` | Phase-0 flow map | DOCUMENTATION | **KEEP** |
| 9 | `docs/PROMPT_TEARDOWN_PLAN.md` | Phase-0 teardown plan | DOCUMENTATION | **KEEP** |

---

## C) Final Cleanup Checklist

When building `prompt_engine`, the following must be addressed:

### Phase 1: Extract & Centralize (MUST)

- [ ] **Move** `app/core/prompt_sanitizer.py` → `app/prompt_engine/sanitizer.py`
  - Carry: `sanitize_visual_prompt`, `CINEMATIC_LENS_TERMS`, `STRICT_NEGATIVE_ADDITIONS`, `get_strict_negative_additions`, `truncate_safe_2d`
  - Update 5 importers

- [ ] **Move** `app/core/visual_prompt_composer.py` → `app/prompt_engine/composer.py`
  - Carry: `compose_visual_prompt`, `normalize_location`, `validate_*`, `render_template`, `get_display_visual_prompt`, `LIKENESS_HINT_WHEN_REFERENCE`
  - Update ~15 importers (ai.py, orders.py, admin/orders.py, fal_ai_service.py, fal_service.py ×5, gemini_image_service.py ×3)

- [ ] **Extract** `FluxPromptBuilder` + `StyleConfig` + style constants from `fal_ai_service.py` (L128-530) → `app/prompt_engine/flux_builder.py` + `app/prompt_engine/styles.py`
  - Update `fal_ai_service.py`, `__init__.py`, `generate_book.py`

- [ ] **Extract** `NEGATIVE_PROMPT` + `ANTI_REALISTIC_NEGATIVE` + `ANTI_ANIME_NEGATIVE` + `get_style_specific_negative` from `fal_ai_service.py` (L128-230) → `app/prompt_engine/negatives.py`

- [ ] **Extract** `_build_full_prompt` from `fal_ai_service.py` (L1423-1475) → `app/prompt_engine/composer.py`

- [ ] **Extract** `_build_safe_visual_prompt` + `_compose_visual_prompts` from `gemini_service.py` (L1235-1310) → `app/prompt_engine/gemini_composer.py`

- [ ] **Replace** `BaseImageGenerator._build_full_prompt` in `image_generator.py` (L153-180) with `prompt_engine` call

### Phase 2: Test Migration (MUST)

- [ ] Move `tests/test_prompt_sanitizer.py` → `tests/test_prompt_engine/test_sanitizer.py`
- [ ] Move `tests/test_visual_prompt_composer.py` → `tests/test_prompt_engine/test_composer.py`
- [ ] Move `tests/test_style_independence.py` → `tests/test_prompt_engine/test_style_independence.py`
- [ ] Update imports in `test_preview_detail_response.py` and `test_e2e_preview_detail.py` for `STRICT_NEGATIVE_ADDITIONS`

### Phase 3: Cleanup Scripts (OPTIONAL)

- [ ] Delete `scripts/backfill_visual_prompt_strip_style.py` (one-off, already executed)
- [ ] Delete `scripts/update_prompts_for_fal.py` (one-off, already executed)
- [ ] Update `scripts/update_all_styles_and_scenarios.py` — import paths if `StyleConfig` moves

### Phase 4: DB Columns (KEEP — NO ACTION)

- `prompt_debug_json` → **KEEP** for observability
- `generation_manifest_json` → **KEEP** for pipeline tracing
- `prompt_templates` table → **KEEP** for admin CRUD
- All scenario/visual_style columns → **KEEP** for admin configuration

---

## D) Suggested Verification Commands (DO NOT RUN)

```bash
# Verify no imports remain from old paths after migration:
rg "from app\.core\.prompt_sanitizer import" backend/app/ backend/tests/
rg "from app\.core\.visual_prompt_composer import" backend/app/ backend/tests/

# Verify FluxPromptBuilder moved:
rg "from app\.services\.ai\.fal_ai_service import.*FluxPromptBuilder" backend/

# Verify all compose_visual_prompt calls use new path:
rg "compose_visual_prompt" backend/app/ --count

# Verify tests still pass:
cd backend && python -m pytest tests/test_prompt_sanitizer.py tests/test_visual_prompt_composer.py tests/test_style_independence.py tests/test_preview_detail_response.py tests/test_e2e_preview_detail.py -v

# Verify no orphan sanitizer references:
rg "sanitize_visual_prompt|CINEMATIC_LENS_TERMS|STRICT_NEGATIVE" backend/app/ --count

# Count remaining prompt_debug_json references (expected: observability only):
rg "prompt_debug_json" backend/app/ --count
```

---

## E) Architecture Note

After completing the checklist above, the prompt system will live entirely under `app/prompt_engine/` with this structure:

```
app/prompt_engine/
├── __init__.py          # Public API: compose_visual_prompt, normalize_location, etc.
├── composer.py          # compose_visual_prompt, get_display_visual_prompt, _build_full_prompt
├── sanitizer.py         # sanitize_visual_prompt, CINEMATIC_LENS_TERMS, truncate_safe_2d
├── negatives.py         # NEGATIVE_PROMPT, STRICT_NEGATIVE_ADDITIONS, ANTI_*_NEGATIVE
├── styles.py            # StyleConfig, DEFAULT/WATERCOLOR/PIXAR/... + STYLE_PULID_WEIGHTS
├── flux_builder.py      # FluxPromptBuilder (compose_prompt, build_cover_prompt, etc.)
├── gemini_composer.py   # _build_safe_visual_prompt, _compose_visual_prompts
├── validators.py        # validate_no_placeholders, validate_cover_inner_phrases
├── normalizers.py       # normalize_location (Kapadokya→Cappadocia)
└── README.md            # Architecture overview (already exists)
```

All current call sites in `fal_ai_service.py`, `fal_service.py`, `gemini_service.py`, `gemini_image_service.py`, `image_generator.py`, `orders.py`, `ai.py`, and `admin/orders.py` will import from `app.prompt_engine` instead of scattered locations.

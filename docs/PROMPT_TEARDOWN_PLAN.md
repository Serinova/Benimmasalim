# Prompt System Teardown Plan (Phase 1 Prep)

**Purpose:** List what to delete, keep, or patch when rebuilding the prompt system. No changes in Phase 0; this is the removal/replacement plan for Phase 1.

---

## Legend

- **MUST DELETE** — Remove or retire (old composer / duplicate logic).
- **MUST KEEP** — Do not remove; FAL/API call, manifest writing, cache-bust, order flow.
- **MUST PATCH** — Replace internal prompt builder with new composer call; keep surrounding flow.

---

## 1) Core composer and sanitizer

| Item | Verdict | Notes |
|------|---------|------|
| `app/core/visual_prompt_composer.py` (current) | **MUST PATCH** | Replace with new `prompt_engine` composer. Keep function signatures used by callers where possible (e.g. `compose_visual_prompt(rendered_or_template, is_cover, style_text, style_negative, ...)` → delegate to new engine). Risk: all image paths depend on it. |
| `app/core/prompt_sanitizer.py` | **MUST PATCH** | Move or wrap: sanitize_visual_prompt, get_strict_negative_additions, truncate_safe_2d, STRICT/CINEMATIC/INNER constants. New engine should own single sanitizer. Risk: duplicate Kapadokya normalization with composer—consolidate in one place. |
| `app/core/sanitizer.py` (input sanitization) | **MUST KEEP** | sanitize_for_prompt, sanitize_scenario_prompt, sanitize_visual_style for API/security. Not part of visual prompt composition. |

---

## 2) FAL service

| Item | Verdict | Notes |
|------|---------|------|
| `FalAIService.generate_consistent_image` | **MUST KEEP** | FAL call, dimensions, PuLID, return (url, {manifest, final_prompt, negative_prompt}). |
| `FalAIService._build_full_prompt` | **MUST PATCH** | Replace with call to new composer (scene-only build). Or remove if new composer accepts raw scene string and handles clothing/composition. Integration: single call to new engine "build scene" then "compose final" before API. |
| `FluxPromptBuilder.compose_prompt` (scene_only=True path) | **MUST PATCH** | Replace with new engine scene builder. scene_only=False path can be deprecated if unused. |
| `FluxPromptBuilder.get_style_config`, `get_style_specific_negative`, `get_pulid_weight_for_style` | **MUST PATCH** | Move into new `style_registry` / engine; FAL keeps only "get style text" and "get negative" from engine. |
| StyleConfig / DEFAULT_STYLE / PIXAR_STYLE / etc. | **MUST PATCH** | Becomes part of new style_registry; FAL no longer holds style definitions. |
| NEGATIVE_PROMPT (base) in fal_ai_service | **MUST KEEP** | Base negative for FAL; merge with engine’s negative_suffix in one place. |

**Integration point:** In `generate_consistent_image`, replace the block that calls `_build_full_prompt` + `compose_visual_prompt` with one call to new engine: e.g. `final_prompt, negative_suffix = prompt_engine.compose(scene=prompt, style_key=style_modifier, is_cover=...)`, then `full_negative = NEGATIVE_PROMPT + ", " + negative_suffix`.

---

## 3) Gemini service

| Item | Verdict | Notes |
|------|---------|------|
| `GeminiService.generate_story_structured` (Pass1 + Pass2) | **MUST KEEP** | Story and page structure generation. |
| `GeminiService._compose_visual_prompts` | **MUST PATCH** | Keep scenario template + location logic; delegate "build one scene prompt" to new engine (scene-only, no style). Output remains list of scene-only visual_prompt. |
| `GeminiService._build_safe_visual_prompt` | **MUST PATCH** | Replace with new engine "build scene prompt" (outfit, cultural, composition, length). Same file or engine. |
| `_sanitize_scene_description` | **MUST PATCH** | Move into engine or keep as internal Gemini helper; ensure no style tokens. |

**Integration point:** In `_compose_visual_prompts`, where `_build_safe_visual_prompt` is called, call new engine’s scene builder instead (same inputs: scene_desc, outfit, cultural, is_cover, max_length).

---

## 4) Orders and preview flow

| Item | Verdict | Notes |
|------|---------|------|
| `process_preview_background` | **MUST KEEP** | Orchestration, FAL call per page, GCS upload, email, DB commit. |
| `process_remaining_pages` | **MUST KEEP** | Same; do not change flow. |
| Writing `preview.prompt_debug_json` / `preview.generation_manifest_json` | **MUST KEEP** | Standard fields; ensure new engine returns same shape (final_prompt, negative_prompt, optional final_prompt_after_sanitize). |
| Updating `preview.story_pages[].visual_prompt` with composed prompt | **MUST KEEP** | UI consistency. |
| `_display_visual_prompt` / `_display_prompt_remaining` (orders) | **MUST PATCH** | Use new engine’s "display prompt" (from debug or compose) instead of current `prompt_debug_collector` + compose_visual_prompt. |
| `get_display_visual_prompt` (composer) | **MUST PATCH** | Move to new engine; admin/orders call engine. |

---

## 5) AI endpoints (ai.py)

| Item | Verdict | Notes |
|------|---------|------|
| `test_structured_story_generation` | **MUST PATCH** | Keep Gemini call; replace per-page `compose_visual_prompt(...)` with new engine compose (same contract: input scene + style → output final_prompt for response). |
| `test_image_generation` (Imagen) | **MUST PATCH** | Replace `compose_visual_prompt(...)` with new engine. |
| `test_fal_image_generation` | **MUST KEEP** (flow) | FAL call; prompt comes from FAL service which will be patched. |
| `test_image_flash` / `test_image_modular` | **MUST PATCH** | Any direct composer call or generator-internal prompt build → route through new engine. |
| `generate_story` / `generate_cover` / `regenerate_cover` | **MUST KEEP** | Placeholder endpoints; no prompt logic to remove. |

---

## 6) Admin

| Item | Verdict | Notes |
|------|---------|------|
| `_story_pages_for_display` (admin/orders) | **MUST PATCH** | Call new engine’s get_display_visual_prompt(preview) instead of current `get_display_visual_prompt` from composer. |
| Preview detail responses (story_pages with visual_prompt) | **MUST KEEP** | Contract unchanged; source of visual_prompt becomes new engine. |

---

## 7) Other services (fal_service, gemini_image_service, image_generator)

| Item | Verdict | Notes |
|------|---------|------|
| `app/services/ai/fal_service.py` (legacy FAL) | **MUST PATCH** | Every `compose_visual_prompt` call → new engine. |
| `app/services/ai/gemini_image_service.py` | **MUST PATCH** | Same; composer calls → new engine. |
| `app/services/ai/image_generator.py` | **MUST PATCH** | `_build_full_prompt` and any prompt concatenation → new engine; keep strategy interface. |

---

## 8) Trials

| Item | Verdict | Notes |
|------|---------|------|
| `create_trial` (Gemini + 3 images) | **MUST KEEP** (flow) | Story from Gemini; images from FAL. FAL path patched as above. |
| Stored `story_pages[].visual_prompt` | **MUST KEEP** | Same shape; value comes from Gemini + _compose_visual_prompts (patched). |

---

## 9) What to delete (after new engine is wired)

| Item | Verdict | When |
|------|---------|------|
| Duplicate Kapadokya normalization in `prompt_sanitizer.py` | **MUST DELETE** | After engine owns single normalize; keep one place. |
| Legacy `FluxPromptBuilder.compose_prompt(..., scene_only=False)` usage | **MUST DELETE** | If confirmed unused; else migrate to engine. |
| Old inline "style" concatenation in any remaining path | **MUST DELETE** | Once engine is single injection point. |

---

## Risk notes

- **Single integration point:** All "final prompt" and "negative suffix" must go through the new composer. Adding a second path (e.g. bypassing engine for one endpoint) will recreate inconsistency.
- **DB/response contract:** `prompt_debug_json` and `generation_manifest_json` shapes must stay compatible; add fields only if needed, do not remove or rename existing keys used by frontend/admin.
- **Order flow:** Do not change submit/confirm semantics, token handling, or background task triggers; only replace how the prompt string and debug blob are produced.
- **Tests:** Update tests that assert on composer output (e.g. test_visual_prompt_composer, test_style_independence) to use new engine; keep tests that assert on API behavior (status, response shape).

---

## Minimal integration points (where new composer will be called)

1. **FAL (one place):** `FalAIService.generate_consistent_image` — replace `_build_full_prompt` + `compose_visual_prompt` with one call to `prompt_engine.compose(scene=..., style_key=..., is_cover=..., ...)`.
2. **Gemini (one place per page):** `GeminiService._compose_visual_prompts` — replace `_build_safe_visual_prompt` with `prompt_engine.build_scene(...)`.
3. **API response (test-story-structured):** In `ai.py`, replace `compose_visual_prompt(...)` with `prompt_engine.compose(...)` for each page’s response visual_prompt.
4. **Display (admin + orders):** Replace `get_display_visual_prompt` usage with `prompt_engine.get_display_prompt(page, preview)` (or equivalent taking raw_prompt, page_number, style, prompt_debug_by_page).
5. **Legacy image paths:** `fal_service.py`, `gemini_image_service.py`, `image_generator.py` — each current `compose_visual_prompt` or internal prompt build → `prompt_engine.compose` or `prompt_engine.build_scene`.

No DB schema, migrations, storage, or cache-bust logic need to change for the teardown; only the source of the prompt string and debug blob.

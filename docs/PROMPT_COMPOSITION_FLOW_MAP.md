# Prompt Composition Flow Map (Phase 0)

All places where the system builds/merges scene prompt, injects style, applies sanitizer/normalizer, merges negative prompts, or writes `prompt_debug_json` / `generation_manifest_json`.  
**Format:** file path → function name (approximate line range) → what it adds/removes.

---

## 1) Scene-only prompt building (no style tokens)

| Location | Function | Line range | What it does |
|----------|----------|------------|--------------|
| `app/services/ai/gemini_service.py` | `_build_safe_visual_prompt` | ~1235–1250 | Builds scene-only prompt: `scene_desc` + outfit + cultural hint + composition ("Space for title at top" / "Text space at bottom"). Truncates to `MAX_VISUAL_PROMPT_LENGTH`. No style. |
| `app/services/ai/gemini_service.py` | `_compose_visual_prompts` | ~1252–~1700+ | Iterates Pass2 pages; uses scenario templates/location constraints; calls `_build_safe_visual_prompt` per page; contamination checks (location/style leak). Output: list of `FinalPageContent` with scene-only `visual_prompt`. |
| `app/services/ai/fal_ai_service.py` | `_build_full_prompt` | ~1423–~1480 | Takes `scene_action` (+ optional clothing); if prompt already has location keywords (CAPPADOCIA, ISTANBUL, etc.) uses it; else builds scene-only string. Returns scene-only (style added later in `generate_consistent_image`). |
| `app/services/ai/fal_ai_service.py` | `FluxPromptBuilder.compose_prompt` | ~499–530 | When `scene_only=True`: builds scene string (location, child action, clothing, cover/inner composition). When `scene_only=False`: adds "Children's book" style (legacy). |
| `app/services/ai/image_generator.py` | `_build_full_prompt` | ~153–180 | Legacy: concatenates prompt + style_prompt + quality tags + "AVOID: negative". Not used by main FAL path. |

---

## 2) Style injection (2D/3D/Ghibli/etc.)

| Location | Function | Line range | What it does |
|----------|----------|------------|--------------|
| `app/core/visual_prompt_composer.py` | `compose_visual_prompt` | ~99–144 | **Single injection point:** if `style_text` non-empty, appends `\n\nSTYLE:\n{style_text}`. Also runs likeness_hint, normalize_location, validate, sanitize. |
| `app/services/ai/fal_ai_service.py` | `generate_consistent_image` | ~784–807 | Gets `style_text = (style_modifier or "").strip()`, `style_negative = get_style_specific_negative(style_modifier)`; calls `compose_visual_prompt(..., style_text=style_text, style_negative=style_negative)`. |
| `app/services/ai/fal_ai_service.py` | `get_style_specific_negative` | ~193–~235 | Returns style-specific negative string (e.g. anime, watercolor, pixar) from keyword match. |
| `app/services/ai/fal_ai_service.py` | `FluxPromptBuilder.get_style_config` | ~452–469 | Maps `style_modifier` to `StyleConfig` (DEFAULT, WATERCOLOR, PIXAR, SUPERHERO, ANIME, REALISTIC). Used for id_weight and legacy compose_prompt when scene_only=False. |

**Note:** Gemini Pass2 and `_compose_visual_prompts` do **not** add style; style is applied only at image API call via `compose_visual_prompt(..., style_text=...)`.

---

## 3) Normalizer (Kapadokya → Cappadocia, etc.)

| Location | Function | Line range | What it does |
|----------|----------|------------|--------------|
| `app/core/visual_prompt_composer.py` | `normalize_location` | ~62–70 | Replaces `\bKapadokya\b` with "Cappadocia" (case-insensitive). |
| `app/core/prompt_sanitizer.py` | `sanitize_visual_prompt` | ~75–113 | Also does Kapadokya→Cappadocia (duplicate). Then strips cinematic/inner-cover terms, collapses spaces, truncates (2D-safe). |

**Duplication:** Both composer and sanitizer normalize location; composer runs normalize before sanitize, so sanitizer’s replace is redundant but harmless.

---

## 4) Sanitizer (cinematic strip, cover/inner phrases, truncate)

| Location | Function | Line range | What it does |
|----------|----------|------------|--------------|
| `app/core/visual_prompt_composer.py` | `compose_visual_prompt` | ~136–138 | Calls `sanitize_visual_prompt(prompt, max_length, is_cover)` after validate. |
| `app/core/prompt_sanitizer.py` | `sanitize_visual_prompt` | ~75–113 | Strips `CINEMATIC_LENS_TERMS`; if not cover, strips `INNER_PAGE_STRIP_TERMS` (e.g. "Children's book cover"); Kapadokya→Cappadocia; collapse spaces; truncate at word boundary (2D-safe). |
| `app/core/prompt_sanitizer.py` | `truncate_safe_2d` | ~121–128 | Truncates at word boundary without cutting "2D". |
| `app/services/ai/gemini_service.py` | `_sanitize_scene_description` | ~1216–~1240 | Cleans scene description (used inside `_build_safe_visual_prompt`). |
| `app/core/sanitizer.py` | `sanitize_for_prompt`, `sanitize_scenario_prompt`, `sanitize_visual_style` | ~162–262 | Input sanitization for API (injection, length). Not visual-prompt composition. |

---

## 5) Validators (placeholders, cover/inner phrases)

| Location | Function | Line range | What it does |
|----------|----------|------------|--------------|
| `app/core/visual_prompt_composer.py` | `validate_no_placeholders` | ~49–59 | Raises if `{scene_description}`, `{child_name}`, `{child_description}` still present. |
| `app/core/visual_prompt_composer.py` | `validate_cover_inner_phrases` | ~72–93 | Cover must not contain INNER_ONLY_PHRASES; inner must not contain COVER_ONLY_PHRASES. Raises `VisualPromptValidationError`. |
| `app/core/visual_prompt_composer.py` | `compose_visual_prompt` | ~132–135 | Calls both validators after normalize, before sanitize. |

---

## 6) Negative prompt merge (strict + style-specific)

| Location | Function | Line range | What it does |
|----------|----------|------------|--------------|
| `app/core/visual_prompt_composer.py` | `compose_visual_prompt` | ~139–141 | `negative_suffix = style_negative + ", " + get_strict_negative_additions()` (or strict only). Returns `(prompt, negative_suffix)`. |
| `app/core/prompt_sanitizer.py` | `get_strict_negative_additions` | ~114–116 | Returns `STRICT_NEGATIVE_ADDITIONS` (cinematic, text, watermark, big eyes, chibi, doll-like, etc.). |
| `app/services/ai/fal_ai_service.py` | `generate_consistent_image` | ~806–808 | `full_negative = NEGATIVE_PROMPT + ", " + negative_suffix`; sent to FAL. |
| `app/services/ai/fal_ai_service.py` | `get_style_specific_negative` | ~193–~235 | Style-specific negative string. |

---

## 7) Writing prompt_debug_json / generation_manifest_json

| Location | Function | Line range | What it does |
|----------|----------|------------|--------------|
| `app/services/ai/fal_ai_service.py` | `generate_consistent_image` | ~901–908 | Builds `out["final_prompt"]`, `out["negative_prompt"]`, `out["final_prompt_after_sanitize"]`; returned to caller. |
| `app/api/v1/orders.py` | `process_preview_background` | ~574–577, ~701–712 | Collects `prompt_debug_collector[page_index] = {final_prompt, negative_prompt}` from FAL return; assigns `preview.prompt_debug_json`; updates `preview.story_pages` with composed prompt; assigns `preview.generation_manifest_json` from `generation_manifest_collector`. |
| `app/api/v1/orders.py` | `process_remaining_pages` | ~873–879, ~991–1006 | Same: fills `prompt_debug_collector` / `generation_manifest_collector` from FAL return; merges into `preview.prompt_debug_json` and `preview.generation_manifest_json`; updates `preview.story_pages` with final_prompt. |
| `app/services/ai/fal_ai_service.py` | `generate_consistent_image` | ~893–900 | Builds per-page `manifest` (provider, model, dimensions, prompt_hash, negative_hash, reference_image_used); returned in `out["manifest"]`. |

---

## 8) Call sites of compose_visual_prompt (single entry point)

| File | Function | Line (approx) | Usage |
|------|----------|---------------|--------|
| `app/api/v1/ai.py` | `test_structured_story_generation` | ~761–770 | Composes each page’s response `visual_prompt` (Cappadocia + style). |
| `app/api/v1/ai.py` | `test_image_generation` | ~1181–1188 | Composes prompt for Imagen (prompt+style, style_text=""). |
| `app/services/ai/fal_ai_service.py` | `generate_consistent_image` | ~800–806 | Main FAL path: scene + style + normalize + sanitize. |
| `app/services/ai/fal_ai_service.py` | `generate_cover` (or cover path) | ~1092–1097 | Composes for cover (style_text=""). |
| `app/services/ai/fal_service.py` | Multiple image generators | ~76–81, ~130–135, ~256–261, ~418–423, ~482–487 | Compose before FAL call (style_text from param). |
| `app/services/ai/gemini_image_service.py` | Imagen/Flash paths | ~125–130, ~297–303, ~487–492 | Compose with style_text="" (scene-only for Gemini path). |
| `app/core/visual_prompt_composer.py` | `get_display_visual_prompt` | ~161–166 | Fallback compose when no debug (normalize + style for UI). |

---

## Flow summary (single page, FAL path)

1. **Input:** `page["visual_prompt"]` (scene-only from Gemini or client), `style_modifier` (e.g. "2D").
2. **FAL:** `_build_full_prompt(scene_action=prompt, ...)` → scene-only string (optional clothing).
3. **FAL:** `compose_visual_prompt(full_prompt_before_sanitize, style_text=style_modifier, style_negative=..., is_cover=...)` → (full_prompt, negative_suffix).
4. **FAL:** `full_negative = NEGATIVE_PROMPT + ", " + negative_suffix`; send (full_prompt, full_negative) to FAL API.
5. **FAL:** Return (image_url, {manifest, final_prompt, negative_prompt}).
6. **Orders:** Store in `prompt_debug_collector` → `preview.prompt_debug_json`; manifest → `preview.generation_manifest_json`; update `preview.story_pages[].visual_prompt` to final_prompt.

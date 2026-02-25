# Visual Generation Pipeline – Debug Report

## A) File Paths and Functions Involved

### Final prompt assembly (where the string sent to the image model is built)

| Location | Function / constant | Role |
|----------|--------------------|------|
| `backend/app/services/ai/fal_ai_service.py` | `generate_consistent_image()` | Entry from orders: builds `full_prompt` via `_build_full_prompt()`, then sends to FAL. |
| `backend/app/services/ai/fal_ai_service.py` | `_build_full_prompt()` | Assembles final prompt: either uses `scene_action` as-is (full template) or calls `FluxPromptBuilder.compose_prompt()`. |
| `backend/app/services/ai/fal_ai_service.py` | `FluxPromptBuilder.compose_prompt()` | Builds prompt from location + scene + clothing; uses `StyleConfig` prefix/suffix. |
| `backend/app/services/ai/fal_ai_service.py` | `COVER_QUALITY`, `PAGE_QUALITY`, `StyleConfig` (e.g. `DEFAULT_STYLE`, `PIXAR_STYLE`) | Default suffixes/prefixes that contained cinematic wording. |
| `backend/app/services/ai/fal_ai_service.py` | `NEGATIVE_PROMPT`, `get_style_specific_negative()` | Negative prompt sent to FAL. |
| `backend/app/services/ai/gemini_service.py` | `_compose_visual_prompts()`, `_build_safe_visual_prompt()` | Produces `visual_prompt` per page (scene + style); passed to FAL as `prompt` in orders. |
| `backend/app/services/ai/gemini_service.py` | Scene templates / instructions | Can include "wide-angle", "f/8", "cinematic" in examples. |
| `backend/app/api/v1/orders.py` | `process_preview_background()` | Calls `fal_service.generate_consistent_image(prompt=page["visual_prompt"], ...)` for each page. |

### New central sanitizer

| Location | Role |
|----------|------|
| `backend/app/core/prompt_sanitizer.py` | `sanitize_visual_prompt()`, `get_strict_negative_additions()` – single place to strip cinematic/lens terms and add strict negative. |

---

## B) Sources of “Hardcore Cinematic” Wording

### 1. Default/system prompts in FAL service

- **`COVER_QUALITY`** (lines ~113–119): `"cinematic lighting, high contrast, clear focal point"`.
- **`StyleConfig.cover_suffix`** (e.g. DEFAULT_STYLE): `"Cinematic lighting, high contrast, magical atmosphere, professional book cover design..."`.
- **PIXAR_STYLE.cover_suffix**: `"Dramatic lighting, cinematic composition, movie poster quality. Character 30% of frame, epic background 70%."`.
- **REALISTIC_STYLE.cover_prefix/suffix**: `"Extreme wide shot, cinematic composition..."`.
- **`FluxPromptBuilder.compose_prompt()`** (cover branch): uses `"Epic landscape with iconic landmarks"`, `"title space at top"` (can encourage poster/title look).

### 2. Gemini / scenario side

- **`backend/app/services/ai/gemini_service.py`** (e.g. ~480, 488, 502, 1085, 1111): templates with `"A wide-angle cinematic shot..."`, `"Wide angle f/8, detailed background..."`.
- **`backend/app/api/v1/admin/prompts.py`** (e.g. ~416, 432, 437): same wide-angle/cinematic/f/8 examples.
- **`backend/alembic/versions/015_seed_full_prompt_templates.py`**: seed prompts with `"wide-angle cinematic"`, `"Wide angle f/8"`, `"standing heroically"`, `"epic adventure mood"`.
- **`backend/scripts/update_kapadokya_scenario.py`**: `"god rays"`, `"Epic cinematic scale"`, `"text overlay"`.
- **`backend/scripts/create_istanbul_scenario.py`**: `"Epic cinematic scale"`, `"text overlay"`.

### 3. Cover vs inner page

- Cover path uses `StyleConfig.cover_prefix` / `cover_suffix` (epic, cinematic, dramatic).
- Inner pages use `prefix`/`suffix` (softer but still some “wide” framing). Both are now sanitized before send.

### 4. Text/watermark

- NEGATIVE_PROMPT already had `"text, watermark"` (fal_ai_service ~163).
- Some scenario/template text asks for `"title space at top"`, `"space for text overlay"` – not asking the model to draw text, but can nudge composition; strict negative now explicitly blocks `"text overlay, caption, title text, written text"`.

---

## C) Model Parameters (FAL)

- **`GenerationConfig`** (`fal_ai_service.py` ~73–79): `num_inference_steps=28`, `guidance_scale=3.5`. No “style preset” or “poster” flag found in payload.
- **Payload** uses: `prompt`, `negative_prompt`, `image_size`, `num_inference_steps`, `guidance_scale`, optional `reference_image_url`, `id_weight`, `start_step`, `seed`. No upscaler or “enhance” flag in the path used by orders.

---

## D) Example FINAL_PROMPT (before/after sanitizer)

**Before (typical Gemini full-template + style):**  
`A wide-angle cinematic shot of the majestic Cappadocia valley at golden sunrise, dozens of colorful hot air balloons... A 9-year-old boy named Uras standing heroically on a cliff edge... Studio Ghibli anime art style, cel-shaded animation, vibrant colors, epic adventure mood. Children's book cover illustration. Wide angle f/8, detailed background, child 30% of frame, landscape 70%.`

**After sanitize_visual_prompt():**  
`A  shot of the majestic Cappadocia valley at golden sunrise, dozens of colorful hot air balloons... A 9-year-old boy named Uras standing  on a cliff edge... Studio Ghibli anime art style, cel-shaded animation, vibrant colors,  adventure mood. Children's book illustration.  detailed background, child 30% of frame, landscape 70%.`

(Removed: "wide-angle", "cinematic", "heroically", "epic", "Wide angle f/8", "cover". Double spaces from removal are collapsed to single space in the actual implementation.)

**Strict negative appended to NEGATIVE_PROMPT:**  
`cinematic, wide-angle, f/8, film still, lens flare, god rays, volumetric lighting, concept art, movie poster, poster style, text, watermark, caption, title text, subtitle, logo, signature, text overlay, written text, letters, numbers on image`

---

## E) “2D” Truncation

- Truncation in `generate_consistent_image` is `prompt[:MAX_PROMPT_LENGTH].rsplit(" ", 1)[0]`. If the cut falls between `"2"` and `"D"` (e.g. "...2D children's..." → "...2" and "D children's..."), the visible part becomes “D children’s...”.
- **Fix in sanitizer:** when truncating, if the cut ends with `"2"` and the next character in the remaining string is `"D"` or `"d"`, we keep that character so the prompt still contains “2D”/“2d”.

---

## F) Patch Plan (Minimal Surgical Changes)

### 1. Added: `backend/app/core/prompt_sanitizer.py`

- `CINEMATIC_LENS_TERMS`: regex list for cinematic/lens/epic/dramatic/poster/photo terms.
- `sanitize_visual_prompt(prompt, max_length=1200)`: strips those terms, collapses spaces, truncates at word boundary with “2D” protection.
- `get_strict_negative_additions()`: returns the strict negative string above.

### 2. Changes in `backend/app/services/ai/fal_ai_service.py`

- **`generate_consistent_image()`**  
  - After `full_prompt = self._build_full_prompt(...)`: call `full_prompt = sanitize_visual_prompt(full_prompt)`.  
  - Set `full_negative = NEGATIVE_PROMPT + ", " + get_strict_negative_additions()`.  
  - Use `full_negative` in `payload["negative_prompt"]`.  
  - Add `logger.info("FINAL_PROMPT_SENT_TO_FAL", prompt_first_400=..., prompt_length=..., is_cover=...)`.

- **`_generate_with_composed_prompt()`**  
  - After building `full_negative` (with gender + style): prepend/append `get_strict_negative_additions()` to the negative string.  
  - Before building payload: `prompt = sanitize_visual_prompt(prompt)`.  
  - Use sanitized `prompt` in payload and in the existing print/log so “FINAL PROMPT SENT TO FAL” reflects the sanitized prompt.

### 3. No change (by design)

- Gemini templates and scenario seeds still contain cinematic wording; sanitizer removes it at the last moment so we don’t refactor the whole pipeline.
- StyleConfig prefix/suffix in FAL remain as-is; sanitizer strips any cinematic terms that end up in the final string.
- Guidance scale / steps unchanged; no new “poster” or “enhance” flags.

---

## G) Call Chain (Story → Prompt → Image)

1. **Story generation:** `gemini_service.generate_story_structured()` → produces pages with `scene_description` (and optionally style).
2. **Visual prompt per page:** `gemini_service._compose_visual_prompts()` → `_build_safe_visual_prompt()` → each page gets `visual_prompt` (scene + outfit + style + suffix like “Children's book illustration”).
3. **Orders background:** `orders.process_preview_background()` → for each page without image: `fal_service.generate_consistent_image(prompt=page["visual_prompt"], style_modifier=..., is_cover=(page_num==0), ...)`.
4. **FAL prompt build:** `FalAIService.generate_consistent_image()` → `full_prompt = self._build_full_prompt(scene_action=prompt, ...)` → either raw `prompt` (full template) or `FluxPromptBuilder.compose_prompt(...)`.
5. **Sanitize + negative:** `full_prompt = sanitize_visual_prompt(full_prompt)`; `full_negative = NEGATIVE_PROMPT + ", " + get_strict_negative_additions()`.
6. **Send:** `payload = { "prompt": full_prompt, "negative_prompt": full_negative, ... }` → `_generate_with_queue(model, payload)`.

Log for “page 1” (and any page): in backend logs, search for `FINAL_PROMPT_SENT_TO_FAL`; `prompt_first_400` (and optional full prompt in the print block in `_generate_with_composed_prompt`) shows the exact string sent to FAL after sanitization.

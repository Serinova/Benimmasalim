# Hardcore Prompt Influence Report – Full Audit

## 1) Prompt Pipeline Map (Call Chain + File:Line)

### (a) Reads prompts (request/DB)

| File | Line(s) | Function/Context | What is read |
|------|---------|------------------|--------------|
| **backend/app/api/v1/orders.py** | 437, 553, 827 | `process_preview_background`, `process_remaining_pages` | `page["visual_prompt"]`, `request_data["visual_style"]`, `request_data["story_pages"]` |
| **backend/app/api/v1/orders.py** | 393 | `submit_preview_async` | `request.story_pages` (text, visual_prompt), `request.visual_style` |
| **backend/app/services/ai/gemini_service.py** | 913, 1061 | `generate_story_two_pass`, PASS 2 | `_get_prompt("PURE_AUTHOR_SYSTEM", ...)`, `_get_prompt("AI_DIRECTOR_SYSTEM", ...)` from DB or fallback |
| **backend/app/services/ai/gemini_service.py** | 594-629 | `_get_prompt` | DB prompt_template_service or hardcoded fallback |
| **backend/app/services/ai/gemini_service.py** | 1330-1382 | `_compose_visual_prompts` | `page.scene_description`, scenario cultural_elements, style |
| **backend/app/services/ai/fal_ai_service.py** | 736-746 | `generate_consistent_image` | `prompt` (visual_prompt), `style_modifier`, `is_cover` |

### (b) Modifies prompts

| File | Line(s) | Function/Context | Modification |
|------|---------|------------------|--------------|
| **backend/app/services/ai/gemini_service.py** | 1085, 1111 | PASS 2 Technical Director prompt (instruction text) | Injects "A wide-angle cinematic shot of [LOCATION]... Wide angle f/8" into expected `scene_description` format |
| **backend/app/services/ai/gemini_service.py** | 1244-1251 | `_build_safe_visual_prompt` | Composes: scene_desc + outfit + cultural_hint + clean_style + suffix ("Children's book cover illustration." / "Children's book illustration.") |
| **backend/app/services/ai/fal_ai_service.py** | 783-791 | `generate_consistent_image` | Truncates prompt to MAX_PROMPT_LENGTH 1200 at word boundary (risk: "2D" → "D" if cut between 2 and D) |
| **backend/app/services/ai/fal_ai_service.py** | 810-818 | `generate_consistent_image` | `_build_full_prompt` → then `sanitize_visual_prompt` |
| **backend/app/services/ai/fal_ai_service.py** | 1401-1471 | `_build_full_prompt` | Either returns prompt AS-IS (full template) or calls `FluxPromptBuilder.compose_prompt` (adds style prefix/suffix) |
| **backend/app/services/ai/fal_ai_service.py** | 498-558 | `FluxPromptBuilder.compose_prompt` | Builds: location + "Wide shot showing a young child {scene}... Children's book cover/inner..."; uses StyleConfig cover_prefix/cover_suffix or prefix/suffix |
| **backend/app/core/prompt_sanitizer.py** | 57-82 | `sanitize_visual_prompt` | Strips CINEMATIC_LENS_TERMS; truncates at max_length with 2D protection |

### (c) Merges prompts

| File | Line(s) | Function/Context | Merge formula |
|------|---------|------------------|---------------|
| **backend/app/services/ai/gemini_service.py** | 1246 | `_build_safe_visual_prompt` | `prompt = f"{scene_desc}{outfit_injection}{cultural_hint} {clean_style}.{suffix}"` |
| **backend/app/services/ai/fal_ai_service.py** | 546-556, 498-527 | `compose_prompt` (location-first branch) | Cover: `f"{location or 'Detailed environment...'} Wide shot showing a young child {scene}, wearing {clothing_short}. ... Children's book cover, ..."`; Inner: same with "Children's book illustration" |
| **backend/app/services/ai/fal_ai_service.py** | 1464-1470 | `_build_full_prompt` | When NOT full template: `FluxPromptBuilder.compose_prompt(scene_action, clothing_prompt, get_style_config(style_modifier), is_cover)` → style_config.prefix/suffix or cover_prefix/cover_suffix wrap the scene |

### (d) Sends prompt to image model

| File | Line(s) | Function/Context | API |
|------|---------|------------------|-----|
| **backend/app/services/ai/fal_ai_service.py** | 858-876 | `generate_consistent_image` | Payload `{"prompt": full_prompt, "negative_prompt": full_negative, "image_size", "num_inference_steps", "guidance_scale", ...}` → `_generate_with_queue` or `_generate_direct` |
| **backend/app/services/ai/fal_ai_service.py** | 873-875 | (same) | Model: `FalModel.FLUX_PULID` or `FLUX_DEV` |

### Call chain (request → image API)

```
POST /api/v1/orders/submit-preview-async
  → orders.submit_preview_async (L319) 
    → StoryPreview saved with story_pages (visual_prompt from frontend/Gemini)
    → background_tasks.add_task(process_preview_background, request_data=...)

process_preview_background (orders.py L463)
  → for each page: fal_service.generate_consistent_image(
        prompt=page["visual_prompt"],   ← L553, L827
        style_modifier=visual_style,
        is_cover=(page_num==0),
        page_number=page_num)

FalAIService.generate_consistent_image (fal_ai_service.py L734)
  → truncate if len(prompt)>1200 (L784-791)
  → full_prompt_before_sanitize = _build_full_prompt(prompt, clothing_prompt, style_modifier, is_cover)  (L810)
  → full_prompt = sanitize_visual_prompt(full_prompt_before_sanitize)  (L818)
  → full_negative = NEGATIVE_PROMPT + ", " + get_strict_negative_additions()  (L820)
  → payload = { "prompt": full_prompt, "negative_prompt": full_negative, ... }  (L858-872)
  → _generate_with_queue(model, payload) or _generate_direct(model, payload)  (L874-875)
```

**Gemini side (origin of visual_prompt):**  
Story generation → PASS 2 Technical Director (gemini_service L1055-1175) with instruction containing "wide-angle cinematic", "f/8" → `scene_description` per page → `_compose_visual_prompts` (L1253) → `_build_safe_visual_prompt` (L1244) → `visual_prompt` = scene + outfit + style + suffix. These prompts are stored in `story_pages` and sent to backend on submit; background task uses them as `page["visual_prompt"]`.

---

## 2) Hardcore Influence Report (Sources + Evidence)

| # | Source type | File | Line range | Sample text injected | Affects | Severity |
|---|-------------|------|------------|---------------------|---------|----------|
| 1 | **Template (instruction)** | gemini_service.py | 1085, 1111 | "A wide-angle cinematic shot of [LOCATION]. ... Wide angle f/8, child 30% of frame." | All pages (scene_description) | HIGH |
| 2 | **Template (example)** | gemini_service.py | 480, 488, 502 | "A wide-angle cinematic shot of ...", "Wide angle f/8, detailed background..." | Gemini output format | HIGH |
| 3 | **Hardcoded default** | gemini_service.py | 1851 | "with rich, cinematic scene descriptions" | Author instructions | MEDIUM |
| 4 | **Fallback** | gemini_service.py | 594-629 | `_get_prompt(key, fallback)` → DB or fallback; fallbacks can contain cinematic wording if seeded | Story/director prompts | MEDIUM |
| 5 | **Hardcoded constant** | gemini_image_service.py | 35-45 | COVER_QUALITY_SUFFIX: "extreme wide shot, epic landscape composition", "poster style", "cinematic lighting", "f/8 depth of field" | Gemini Imagen path (if used) | HIGH |
| 6 | **Hardcoded default** | gemini_image_service.py | 260 | "standing heroically ready for adventure" | Cover scene when missing | HIGH |
| 7 | **Hardcoded constant** | admin/prompts.py | 416, 432, 437 | "A wide-angle cinematic shot of [LOCATION DETAILS]", "Wide angle f/8...", "standing heroically", "epic adventure mood" | Seed/default prompts in DB | HIGH |
| 8 | **Model/scenario** | scenario.py | 7, 77, 99, 217 | cover_prompt_template: "poster-style"; "standing heroically at castle entrance" | Cover template, docs | MEDIUM |
| 9 | **Hardcoded (negative)** | fal_ai_service.py | 140, 182 | NEGATIVE_PROMPT: "macro lens", "lens flare, depth of field photography" | All FAL generations | LOW (negative) |
| 10 | **Style config** | fal_ai_service.py | 249-252, 261-269, 280-283, 291-292, 299-300 | cover_prefix/suffix: previously "Extreme wide shot", "epic", "Cinematic lighting"; now 2D-safe in code | Cover page (FAL) | MITIGATED |
| 11 | **Config (preset)** | fal_ai_service.py | 386 | STYLE_PULID_WEIGHTS["cinematic"] = 0.50 | id_weight when style contains "cinematic" | LOW |
| 12 | **API test default** | api/v1/ai.py | 465 | scenes: "standing heroically", ... | Test/legacy endpoint | LOW |

---

## 3) Layer Priority / Weighting

- **Order in final prompt (FAL path):**  
  - If **full template** detected: final prompt = `visual_prompt` AS-IS (no prefix/suffix). So **visual_prompt is the only layer** (and already contains scene + outfit + style from Gemini).  
  - If **short action**: `compose_prompt` builds **location first**, then "Wide shot showing a young child {scene}, wearing {clothing}. ..." So order is: **location → scene (action) → clothing → fixed tail** (Children's book cover/inner). StyleConfig prefix/suffix are used only in the non–location-first branch (when `compose_prompt` is called with scene_action only); in the current location-first branch we don’t prepend StyleConfig prefix – we use a fixed string. So **first** = location or "Detailed environment", **last** = "Children's book cover, magical atmosphere, title space at top" or "Children's book illustration, warm colors, text space at bottom."

- **Cover vs inner:**  
  - **Cover applied only to page 0:** Yes. `is_cover=(page_num==0)` in orders.py (L549, L823); in `_build_full_prompt` we use `FluxPromptBuilder.get_style_config(style_modifier)` and `compose_prompt(..., is_cover=is_cover)`. In `compose_prompt`, `is_cover` selects cover vs inner wording (L549-556). So cover_prompt logic is only for page 0.  
  - **Override rule:** There is no explicit "if cover then override style". For cover we use the same style_config but with cover_prefix/cover_suffix instead of prefix/suffix.

- **"2D" truncation:**  
  - Truncation in `generate_consistent_image` (L791) is `prompt[:MAX_PROMPT_LENGTH].rsplit(" ", 1)[0]` – can cut between "2" and "D" if prompt ends with "2D children's...".  
  - **prompt_sanitizer** (L73-80) truncates with 2D protection: if cut ends with "2" and rest starts with "d", we keep "2D". So sanitizer output is safe; the **pre-sanitize** truncation at L791 is not 2D-safe. Recommendation: truncate only after sanitization, or use the same 2D-safe truncation in both places.

---

## 4) Failing Example (Page 1)

### A) Raw inputs from DB/request

- **style_prompt:** e.g. `"children's book illustration, pixar style, soft colors"` (from request_data["visual_style"]).
- **scenario_prompt:** Not passed to FAL; scenario affects Gemini output only.
- **visual_prompt (page 1):** From Gemini PASS 2, e.g.  
  `"A wide-angle cinematic shot of the magnificent Hagia Sophia interior. A 7-year-old girl named Elif standing in wonder, looking up at the ancient chandelier, wearing a red dress. Warm golden light. Wide angle f/8, detailed architecture, child 30% of frame. The child is wearing adventure jacket and comfortable pants. Children's book illustration."`
- **emotion_prompt:** Not passed to image gen.
- **cover_prompt_used:** False (page 1 = inner).

### B) Applied defaults/fallbacks

- If full-template detection triggers (e.g. "Hagia Sophia" in prompt): no StyleConfig prefix/suffix added; prompt used AS-IS then sanitized.
- Default style when style_modifier empty: `DEFAULT_STYLE` (prefix/suffix in fal_ai_service L245-252).

### C) Final merged prompt (after sanitization)

- Sanitizer removes: "wide-angle", "cinematic", "f/8", "Wide angle f/8".
- Example result:  
  `"A shot of the magnificent Hagia Sophia interior. A 7-year-old girl named Elif standing in wonder, looking up at the ancient chandelier, wearing a red dress. Warm golden light. detailed architecture, child 30% of frame. The child is wearing adventure jacket and comfortable pants. Children's book illustration."`  
  (Spaces collapsed; "shot" may remain; "detailed" remains.)

### D) Negative prompt

- `NEGATIVE_PROMPT` (fal_ai_service L127-166) + `STRICT_NEGATIVE_ADDITIONS` (prompt_sanitizer L52-57): location wrong, close-up, bokeh, text, watermark, cinematic, wide-angle, f/8, film still, lens flare, god rays, volumetric, concept art, movie poster, etc.

### Which substring caused drift

- **Before sanitizer:** "wide-angle cinematic", "Wide angle f/8" in the **first 77 tokens** (high weight for Flux) push toward photographic/cinematic look.
- **If sanitizer were skipped or order changed:** StyleConfig cover/inner strings previously contained "Extreme wide shot", "epic", "Cinematic lighting" – those would directly inject cinematic weight.
- **Gemini Imagen path (gemini_image_service):** COVER_QUALITY_SUFFIX and "standing heroically" + "f/8 depth of field" would add cinematic/heroic tone if that path is used.

---

## 5) Instrumentation (MANDATORY)

- **Already present:**  
  - `FINAL_PROMPT_SENT_TO_FAL` (fal_ai_service L832-843): prompt_first_400, prompt_length, is_cover, model, num_inference_steps, guidance_scale, image_width, image_height, id_weight.  
  - For **page_number == 1**: `PROMPT_DEBUG_FAL` (L846-856): A_style_prompt, B_scenario_prompt, C_visual_prompt, D_emotion_prompt, E_cover_or_inner, F_negative_prompt, G_final_merged_before/after_sanitize.
- **Add:**  
  - **DEBUG flag:** When `settings.debug` is True, log the same PROMPT_DEBUG_FAL structure for **every** page (not only page 1), and add `page_index` and, if available, `preview_id`/`order_id` for correlation.  
  - **Last moment before API:** Log is already immediately before payload build (L858). Optionally add one line: `logger.debug("FAL_PAYLOAD_FINAL", prompt_length=len(full_prompt), negative_length=len(full_negative), ...)` when `settings.debug` is True.

---

## 6) Minimal Patch Plan (Exact Changes)

### A) prompt_sanitizer (runs LAST before API)

- **Done:** Banned tokens removed (cinematic, wide-angle, f/8, lens, film still, heroically, epic, volumetric, god rays, bokeh, depth of field, poster, concept art, cover illustration, professional book cover design, extreme wide shot, standing heroically).  
- **Done:** 2D protection in truncation (sanitizer L73-80).  
- **Add:** Ensure the **pre-sanitize** truncation in fal_ai_service (L784-791) either is removed (and only sanitizer truncates) or uses the same 2D-safe truncation helper from sanitizer.

### B) Cover prompt only for cover page

- **Verified:** Cover logic uses `is_cover=(page_num==0)`; only page 0 gets cover wording. No change needed.

### C) Strict negative prompt

- **Done:** `get_strict_negative_additions()` and `full_negative = NEGATIVE_PROMPT + ", " + strict_negative` (fal_ai_service L819-820). No change needed.

### D) Save final_prompt to DB per page (debug)

- **Option 1:** Add column `StoryPreview.debug_final_prompts` (JSONB): `{"0": {"final_prompt": "...", "negative": "..."}, "1": {...}}`. When `settings.debug` is True, in `process_preview_background` after each FAL call (or in a wrapper), update this JSONB for the current page.  
- **Option 2:** Append to `StoryPreview.admin_notes` when debug: e.g. "DEBUG page 1 final_prompt (first 500): ...".  
- **Recommendation:** Option 1 with a migration; if no migration desired, use Option 2 for minimal change.

### E) DEBUG-based verbose logging

- In `generate_consistent_image`, after building `full_prompt` and `full_negative`:  
  `if getattr(settings, "debug", False): logger.info("PROMPT_DEBUG_FAL", page_index=page_number, A_style_prompt=..., B_scenario_prompt=..., C_visual_prompt=..., D_emotion_prompt=..., E_cover_or_inner=..., F_negative_prompt=..., G_final_before=..., G_final_after=..., model=..., num_inference_steps=..., guidance_scale=..., image_width=..., image_height=...)"`  
  for **every** page (not only page_number==1). This satisfies "toggle with DEBUG flag" and "log each layer + final merged + model params".

### F) Gemini Technical Director instruction

- **Recommendation:** In gemini_service.py, change the PASS 2 instruction (L1085, 1111) from "A wide-angle cinematic shot of [LOCATION]... Wide angle f/8" to "A clear scene of [LOCATION]. A {child_age}-year-old ... [LIGHTING]. Child 30% of frame, environment 70%." so Gemini never emits cinematic/f/8 in scene_description. This removes the source at origin.

### G) gemini_image_service.py

- Replace COVER_QUALITY_SUFFIX and PAGE_QUALITY_SUFFIX (L35-46) with 2D-friendly wording (no "extreme wide shot", "epic", "cinematic", "poster", "f/8 depth of field"). Replace "standing heroically ready for adventure" (L260) with "standing ready for adventure".

---

## 7) Pseudo-diff Summary

```diff
# 1) fal_ai_service.py – DEBUG log for every page
  if page_number == 1:
      logger.info("PROMPT_DEBUG_FAL", ...)
+ if getattr(settings, "debug", False):
+     logger.info("PROMPT_DEBUG_FAL", page_index=page_number, A_style_prompt=style_modifier, ...)

# 2) fal_ai_service.py – 2D-safe truncation before _build_full_prompt (or move truncation after sanitize)
  MAX_PROMPT_LENGTH = 1200
  if len(prompt) > MAX_PROMPT_LENGTH:
-     prompt = prompt[:MAX_PROMPT_LENGTH].rsplit(" ", 1)[0] if " " in prompt[:MAX_PROMPT_LENGTH] else prompt[:MAX_PROMPT_LENGTH]
+     from app.core.prompt_sanitizer import sanitize_visual_prompt
+     prompt = sanitize_visual_prompt(prompt, max_length=MAX_PROMPT_LENGTH)  # 2D-safe truncation

# 3) gemini_service.py – PASS 2 instruction (L1085)
- "scene_description": "A wide-angle cinematic shot of [LOCATION]. ... Wide angle f/8, child 30% of frame."
+ "scene_description": "A clear scene of [LOCATION]. A {child_age}-year-old {gender_term} named {child_name} [ACTION], wearing [CLOTHING]. [LIGHTING]. Child 30% of frame, environment 70%."

# 4) gemini_image_service.py – COVER_QUALITY_SUFFIX / PAGE_QUALITY_SUFFIX
  Replace "extreme wide shot", "epic", "cinematic", "poster", "f/8 depth of field" with 2D-friendly phrases.
  Replace "standing heroically ready for adventure" with "standing ready for adventure".
```

---

**Document version:** 1.0  
**Last updated:** After full audit and existing sanitizer/FAL default fixes.

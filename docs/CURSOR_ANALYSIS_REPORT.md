# Cursor Analysis Report: Output Mismatch Investigation

**Purpose:** Explain why generated images drift from the desired 2D children's book cartoon style (clean lineart, pastel, soft shading) toward cinematic/concept art/poster look, and what influences the final output.

---

## A) Executive Summary – Top 3 Root Causes

1. **Gemini Technical Director instructions and examples**  
   PASS 2 (Technical Director) in `gemini_service.py` and the seeded `AI_DIRECTOR_SYSTEM` in `admin/prompts.py` told the model to output `scene_description` in the form *"A wide-angle cinematic shot of [LOCATION]. ... Wide angle f/8, child 30% of frame"* and *"standing heroically"*. Those phrases were then included in `visual_prompt` and sent to FAL. Flux gives high weight to the first ~77 tokens, so *"wide-angle cinematic"* and *"f/8"* at the start strongly pushed outputs toward a cinematic look.

2. **Quality suffixes and cover defaults in Gemini Imagen path**  
   In `gemini_image_service.py`, `COVER_QUALITY_SUFFIX` and `PAGE_QUALITY_SUFFIX` (and the default cover scene *"standing heroically ready for adventure"*) injected terms like *"extreme wide shot"*, *"epic landscape"*, *"cinematic lighting"*, *"poster style"*, *"f/8 depth of field"*. When the Gemini Imagen path is used, these were appended to every cover/inner prompt and reinforced a cinematic/postery look.

3. **No last-line defense before the image API**  
   Even when some layers were 2D-friendly, any remaining cinematic wording from Gemini or templates was sent straight to FAL. A **prompt_sanitizer** that runs **last** before the API call (and a strict negative prompt) was missing initially; it is now in place and strips banned tokens and enforces negative prompt.

**Additional factors:**  
- Cover logic correctly applies only to page 0 (`is_cover=(page_num==0)`).  
- Negative prompt in FAL already blocked many unwanted elements; `STRICT_NEGATIVE_ADDITIONS` in `prompt_sanitizer.py` now explicitly blocks cinematic, text, watermark.  
- Truncation at 1200 chars could theoretically cut "2D" into "D"; `truncate_safe_2d` is used to avoid that.

---

## B) Prompt Pipeline Map (Call Chain)

### Entry points

| Entry | File:Line | Function | What is read |
|-------|-----------|----------|--------------|
| Submit preview | `backend/app/api/v1/orders.py` | `submit_preview_async` | `request.story_pages` (text, visual_prompt), `request.visual_style` |
| Background image gen | `backend/app/api/v1/orders.py` ~537–565 | `process_preview_background` | `page["visual_prompt"]`, `visual_style`, `child_photo_url` |
| Remaining pages | `backend/app/api/v1/orders.py` ~815–855 | `process_remaining_pages` | Same as above from `StoryPreview` |

### Call chain to image API

```
orders.py: process_preview_background (or process_remaining_pages)
  → for each page: fal_service.generate_consistent_image(
        prompt=page["visual_prompt"],      ← raw visual_prompt from DB/request
        style_modifier=visual_style,
        is_cover=(page_num == 0),
        page_number=page_num,
        preview_id=..., order_id=...)

fal_ai_service.py: FalAIService.generate_consistent_image (L735+)
  → if len(prompt) > 1200: prompt = truncate_safe_2d(prompt, 1200)   [L784-791]
  → full_prompt_before_sanitize = _build_full_prompt(prompt, clothing_prompt, style_modifier, is_cover)  [L810-815]
  → full_prompt = sanitize_visual_prompt(full_prompt_before_sanitize)  [L818]
  → full_negative = NEGATIVE_PROMPT + ", " + get_strict_negative_additions()  [L819-820]
  → payload = { "prompt": full_prompt, "negative_prompt": full_negative, "image_size", ... }  [L867-876]
  → _generate_with_queue(model, payload) or _generate_direct(model, payload)  [L901-903]
```

### Where visual_prompt comes from (Gemini path)

```
Frontend / Story generation
  → Gemini PASS 2 (Technical Director) with AI_DIRECTOR_SYSTEM from DB or fallback
  → scene_description per page (instruction asked for "wide-angle cinematic shot ... f/8" – NOW FIXED to "clear scene ...")
  → gemini_service._compose_visual_prompts → _build_safe_visual_prompt
  → visual_prompt = scene_desc + outfit + style + suffix ("Children's book cover illustration." / "Children's book illustration.")
  → Stored in story_pages and sent to backend; background task uses page["visual_prompt"]
```

### Key files and roles

| File | Role |
|------|------|
| `backend/app/api/v1/orders.py` | Reads `visual_prompt` from request/DB; calls `generate_consistent_image`; passes `preview_id`/`order_id` for debug logs |
| `backend/app/services/ai/fal_ai_service.py` | `generate_consistent_image`: truncate → `_build_full_prompt` → `sanitize_visual_prompt` → build negative → log FINAL_PROMPT_SENT_TO_FAL / PROMPT_DEBUG_FAL → send payload to FAL |
| `backend/app/services/ai/fal_ai_service.py` | `_build_full_prompt`: if full-template keywords present, return prompt AS-IS; else `FluxPromptBuilder.compose_prompt(...)` |
| `backend/app/services/ai/fal_ai_service.py` | `FluxPromptBuilder.compose_prompt`: builds "[location] Wide shot showing a young child {scene}, wearing {clothing}. ... Children's book cover/inner ..." |
| `backend/app/core/prompt_sanitizer.py` | `sanitize_visual_prompt`: strip CINEMATIC_LENS_TERMS; truncate with 2D-safe logic. `get_strict_negative_additions`: text/watermark/cinematic block list |
| `backend/app/services/ai/gemini_service.py` | PASS 2 instructions and examples produce scene_description → composed into visual_prompt |

---

## C) Hardcore Influence Report (Sources + Evidence)

After the surgical fixes applied in this audit:

| # | Source type | File | Line range | Sample text (before fix) | Status | Severity |
|---|-------------|------|------------|---------------------------|--------|----------|
| 1 | Template (instruction) | gemini_service.py | PASS 2 Technical Director | "A wide-angle cinematic shot of [LOCATION]. ... Wide angle f/8" | **FIXED** → "A clear scene of [LOCATION]. ... Child 30% of frame" | was HIGH |
| 2 | Template (example) | gemini_service.py | SCENE_DESCRIPTION_STRUCTURE | "A wide-angle cinematic shot of ...", "Wide angle f/8" | **FIXED** → "A clear scene of ...", "Detailed background" | was HIGH |
| 3 | Docstring | gemini_service.py | generate_json | "rich, cinematic scene descriptions" | **FIXED** → "clear, 2D-friendly scene descriptions" | was MEDIUM |
| 4 | Seed/default (DB) | admin/prompts.py | AI_DIRECTOR_SYSTEM | "A wide-angle cinematic shot of [LOCATION DETAILS]", "Wide angle f/8", "standing heroically", "epic adventure mood" | **FIXED** → "A clear scene of ...", "Detailed background", "standing on a cliff edge", "adventure mood" | was HIGH |
| 5 | Hardcoded constant | gemini_image_service.py | COVER_QUALITY_SUFFIX, PAGE_QUALITY_SUFFIX | "extreme wide shot", "epic", "cinematic lighting", "poster style", "f/8 depth of field" | **FIXED** (earlier) → "full body visible", "soft even lighting", "sharp background" (no lens/cinematic) | was HIGH |
| 6 | Hardcoded default | gemini_image_service.py | Cover scene_description | "standing heroically ready for adventure" | **FIXED** (earlier) → "standing ready for adventure" | was HIGH |
| 7 | Negative prompt | fal_ai_service.py | NEGATIVE_PROMPT | "macro lens", "lens flare", "depth of field photography" | Kept (blocks unwanted look) | LOW |
| 8 | Style config | fal_ai_service.py | StyleConfig cover_prefix/suffix | Previously "Extreme wide shot", "epic", "Cinematic lighting" | **MITIGATED** (earlier) – 2D-safe wording in code | was MEDIUM |
| 9 | Preset | fal_ai_service.py | STYLE_PULID_WEIGHTS["cinematic"] | id_weight 0.50 when style contains "cinematic" | Unchanged; only affects id_weight, not prompt text | LOW |
| 10 | Sanitizer (defense) | prompt_sanitizer.py | CINEMATIC_LENS_TERMS, STRICT_NEGATIVE_ADDITIONS | Strips cinematic/lens/postery terms; adds negative for text/watermark/cinematic | **IN PLACE** – runs last before API call | N/A (mitigation) |

**Cover vs inner pages:**  
- Cover-specific wording is applied only when `is_cover=True` (page 0). `orders.py` passes `is_cover=(page_num == 0)`. No cover_prompt leakage to inner pages.

---

## D) Failing Example: FINAL_PROMPT Before/After

**Scenario:** Page 1 (first inner page), Gemini had been instructed with the old PASS 2 wording and produced a scene_description containing cinematic phrasing.

**A) Raw input from DB/request (typical):**  
`visual_prompt`: *"A wide-angle cinematic shot of the magnificent Hagia Sophia interior with massive dome and golden mosaics. A 7-year-old girl named Elif standing in wonder, looking up at the ancient chandelier, wearing a red dress and white cardigan. Warm golden light streaming through windows. Wide angle f/8, detailed architecture, child 30% of frame. The child is wearing adventure jacket and comfortable pants. Children's book illustration."*

**B) Defaults/fallbacks applied:**  
- FAL path does not overwrite visual_prompt with a default; it uses it as the scene_action. If full-template keywords are detected, the prompt is used AS-IS (then sanitized). So the only “default” is the negative prompt and strict additions.

**C) Final merged prompt BEFORE sanitizer:**  
Same as raw input when full-template detection triggers (e.g. "Hagia Sophia", "Children's book" in prompt). So before sanitizer: the string above.

**D) Final merged prompt AFTER sanitizer:**  
- Stripped: "wide-angle", "cinematic", "f/8", "Wide angle f/8" (and any other CINEMATIC_LENS_TERMS).  
- Example result: *"A clear scene of the magnificent Hagia Sophia interior with massive dome and golden mosaics. A 7-year-old girl named Elif standing in wonder, looking up at the ancient chandelier, wearing a red dress and white cardigan. Warm golden light streaming through windows. detailed architecture, child 30% of frame. The child is wearing adventure jacket and comfortable pants. Children's book illustration."*  
(Exact spacing may vary due to collapsed spaces.)

**E) Negative prompt sent:**  
`NEGATIVE_PROMPT` (fal_ai_service) + `STRICT_NEGATIVE_ADDITIONS` (prompt_sanitizer), e.g. location wrong, close-up, bokeh, text, watermark, cinematic, wide-angle, f/8, film still, lens flare, god rays, volumetric, concept art, movie poster, text overlay, etc.

**F) Model parameters (logged):**  
- model: `fal-ai/flux-pulid` or `fal-ai/flux-dev`  
- num_inference_steps, guidance_scale, image_width (1024), image_height (768), id_weight  

**Explanation of drift:**  
The substrings *"wide-angle cinematic shot"*, *"Wide angle f/8"* (and similar in other pages) were in the first part of the prompt, which Flux weights heavily. That pushed the model toward a cinematic/photo look. Removing those tokens via the sanitizer and fixing Gemini/seed wording at the source reduces that drift.

---

## E) Formatting / Merge Bugs Verified

- **"2D" → "D":** Truncation is done with `truncate_safe_2d` (prompt_sanitizer and fal_ai_service). If the cut would leave "2" and drop "D", the word "2D" is preserved. No bug found.
- **cover_prompt on every page:** Cover-specific wording is only applied when `is_cover=True` (page 0). Not applied to inner pages.
- **Negative prompt:** Built as `NEGATIVE_PROMPT + ", " + get_strict_negative_additions()` and sent in the payload. Not overridden; appended correctly.
- **Prompt ordering:** For full-template prompts, the prompt is used as-is (then sanitized), so any cinematic wording was at the start. Sanitizer removes those terms. For short prompts, `compose_prompt` puts location first, then scene/clothing; tail is "Children's book cover/inner ...". No extra cinematic at the beginning after fixes.

---

## F) Minimal Fix Plan (Surgical – Implemented)

1. **prompt_sanitizer (runs LAST before API call)**  
   - **Done.** `sanitize_visual_prompt()` strips CINEMATIC_LENS_TERMS (cinematic, wide-angle, f/8, lens, film still, heroically, epic, concept art, volumetric, god rays, bokeh, depth of field, poster, cover illustration, etc.).  
   - **Done.** `get_strict_negative_additions()` returns a strict negative string (text, watermark, caption, cinematic, wide-angle, f/8, film still, lens flare, god rays, volumetric, concept art, movie poster, etc.).

2. **Preserve "2D"**  
   - **Done.** `truncate_safe_2d()` used for pre-sanitizer truncation and inside sanitizer; avoids cutting "2D" into "D".

3. **Cover only on cover page**  
   - **Verified.** `is_cover=(page_num == 0)` in both background task and remaining-pages task. Cover wording only for page 0.

4. **Strict negative prompt**  
   - **Done.** `full_negative = NEGATIVE_PROMPT + ", " + get_strict_negative_additions()` and sent in the FAL payload.

5. **Instrumentation (DEBUG toggle)**  
   - **Done.** Before the FAL call:  
     - `FINAL_PROMPT_SENT_TO_FAL`: prompt (first 400 chars), length, is_cover, model, num_inference_steps, guidance_scale, image_width, image_height, id_weight, page_index, preview_id, order_id.  
     - `PROMPT_DEBUG_FAL`: when `page_number == 1` or `settings.debug` – A_style_prompt, C_visual_prompt, E_cover_or_inner, F_negative_prompt, G_final_merged_before_sanitize, G_final_merged_after_sanitize, model params, preview_id, order_id.

6. **Save final_prompt to DB (when settings.debug)**  
   - **Done.** `generate_consistent_image` returns `(url, {"page_index", "final_prompt", "negative_prompt"})` when `settings.debug` and `page_number` is set. Background tasks (`process_preview_background`, `process_remaining_pages`) collect these and save to `StoryPreview.prompt_debug_json` (JSONB). Format: `{"0": {"final_prompt": "...", "negative_prompt": "..."}, ...}`.

---

## G) Banned Tokens List (Sanitizer)

The following (and their regex variants) are stripped by `sanitize_visual_prompt`:

- cinematic, wide-angle, wide angle, extreme wide shot  
- f/8, lens, film still  
- heroically, heroic, standing heroically  
- epic (landscape/composition/background/environment/wide)  
- concept art  
- volumetric lighting/light, god rays, dramatic lighting/contrast  
- movie poster, poster quality  
- DSLR, depth of field, bokeh, lens flare  
- professional photo, photography, photograph  
- cover illustration, professional book cover design  

Negative prompt additionally blocks: text, watermark, caption, title text, subtitle, logo, signature, text overlay, written text, letters, numbers on image.

---

**Report generated from full codebase audit and keyword search. All listed fixes have been applied in code unless marked "Not implemented".**

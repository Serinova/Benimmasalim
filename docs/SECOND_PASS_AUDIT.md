# Second-Pass Deep Audit: Image Generation Paths & Sanitizer Bypass

## 1) All image generation entry points

| Provider | File | Function | Call site(s) | Sanitize applied? | is_cover handling | Model params |
|----------|------|----------|--------------|-------------------|------------------|--------------|
| FAL (Flux PuLID/dev) | fal_ai_service.py | generate_consistent_image | orders.py (preview + remaining), tasks/generate_book.py, image_generator.py, ai.py (test) | **Yes** (L824) | is_cover from caller (page_num==0) | num_inference_steps, guidance_scale, image_size; no cinematic preset |
| FAL (Flux PuLID/dev) | fal_ai_service.py | _generate_with_composed_prompt | generate_cover (L985), generate_page (L1056) | **Yes** (L1104) | generate_cover→True, generate_page→False | same |
| FAL (flux/dev, flux-pulid) | fal_service.py | generate_cover | Legacy/template path; generate_page_image calls it | **Yes** (after patch) | L80: is_cover=True | flux/dev or flux/dev/image-to-image; 28 steps, 3.5 guidance |
| FAL (flux/dev, flux-pulid) | fal_service.py | generate_cover_from_mm | Legacy mm path | **Yes** (after patch) | is_cover=True | same |
| FAL (flux/dev, flux-pulid) | fal_service.py | generate_page_image | Legacy page path | **Yes** (after patch) | is_cover=False then calls generate_cover | same |
| FAL (flux/dev, flux-pulid) | fal_service.py | generate_image | trials.py L279, L508 | **Yes** (after patch) | is_cover=False | flux/dev |
| FAL (flux-pulid) | fal_service.py | generate_with_pulid | trials.py L270 | **Yes** (after patch) | is_cover=False | flux-pulid |
| Gemini Imagen | gemini_image_service.py | generate_image | generate_image_from_scenario, generate_cover, generate_page_illustration, etc. | **Yes** (after patch) | is_cover param (page_index==0 or True/False per caller) | sampleCount, aspectRatio; no preset |
| Gemini Flash (image) | gemini_image_service.py | GeminiFlashImageService.generate_image | generate_cover (L539), generate_page_illustration (L556) | **Yes** (after patch) | is_cover=True/False passed | generateContent; no cinematic preset |
| Imagen (direct) | ai.py | test_imagen endpoint | POST /test-imagen | **Yes** (after patch) | is_cover=False | imagen-3.0-generate-002 |

---

## 2) Bypasses found and fixed

| Bypass | File:Line (before fix) | Issue | Patch |
|--------|------------------------|--------|------|
| FalService prompt sent unsanitized | fal_service.py L81, L130, L161, L174, L423, L487 | full_prompt / prompt sent to FAL without sanitize_visual_prompt | Sanitize in generate_cover, generate_cover_from_mm, generate_page_image (is_cover=False), generate_image, generate_with_pulid (is_cover=False) |
| Test Imagen direct | ai.py L1175–L1183 | full_prompt sent to Imagen without sanitize | Sanitize full_prompt with is_cover=False before POST |
| Gemini Imagen generate_image | gemini_image_service.py L132 | full_prompt sent to Imagen without sanitize | Sanitize full_prompt with is_cover param before POST; add is_cover to generate_image and pass from callers |
| Gemini Flash generate_image | gemini_image_service.py L475 | full_prompt in "Generate an image: ..." without sanitize | Sanitize full_prompt; add is_cover param; pass is_cover=True/False from generate_cover / generate_page_illustration |

---

## 3) Sanitize is last in each path

- **fal_ai_service.generate_consistent_image:** full_prompt = sanitize_visual_prompt(...); payload["prompt"] = full_prompt; no concat after.
- **fal_ai_service._generate_with_composed_prompt:** prompt = sanitize_visual_prompt(prompt, is_cover=is_cover); payload["prompt"] = prompt; no concat after.
- **fal_service:** generate_cover/generate_cover_from_mm sanitize then pass to _generate_image; generate_page_image sanitizes then calls generate_cover (which sanitizes again with is_cover=True — redundant but safe). generate_image and generate_with_pulid sanitize immediately before building json.
- **gemini_image_service (Imagen):** full_prompt = sanitize_visual_prompt(...) then instances[].prompt = full_prompt; no concat after.
- **GeminiFlashImageService:** full_prompt = sanitize_visual_prompt(...) then "text": f"Generate an image: {full_prompt}"; no further concat.
- **ai.py test_imagen:** full_prompt = sanitize_visual_prompt(...) then instances[].prompt = full_prompt.

No helper modifies prompt after generate_consistent_image returns; prompt_debug_json stores the already-sanitized full_prompt.

---

## 4) Cover vs inner everywhere

- **orders.py:** is_cover=(page_num == 0) in process_preview_background and process_remaining_pages.
- **tasks/generate_book.py:** uses FalAIService; page.is_cover from order pages.
- **fal_ai_service:** generate_cover → _generate_with_composed_prompt(..., is_cover=True); generate_page → is_cover=False.
- **fal_service:** generate_cover/generate_cover_from_mm use is_cover=True; generate_page_image sanitizes with is_cover=False then calls generate_cover; generate_image/generate_with_pulid use is_cover=False (trials: no page context).
- **gemini_image_service:** generate_image_from_scenario passes is_cover=(page_index==0); generate_cover passes is_cover=True; generate_page_illustration passes is_cover=False.
- Inner pages never receive "Children's book cover" / "book cover illustration" when is_cover=False (stripped by sanitizer).

---

## 5) Model params

- FAL: num_inference_steps, guidance_scale, image_size; no "cinematic" preset; style affects only id_weight (STYLE_PULID_WEIGHTS), not prompt.
- Imagen/Gemini: sampleCount, aspectRatio (or aspect_ratio); no enhance/refine/cinematic preset in payload.
- Cover vs inner: same model; only prompt wording and is_cover differ. Preview and final both use same FalAIService path with same params.

---

## 6) Caching & DB

- **prompt_debug_json:** Stores result[1]["final_prompt"] from generate_consistent_image, which is the sanitized full_prompt (L916). So stored prompt is after sanitize.
- **Reuse:** story_pages[].visual_prompt is input to generate_consistent_image, which builds and sanitizes before API. No path reuses a stored prompt and sends it to an image API without going through a layer that sanitizes (we patched all entry points that send to image APIs).

---

## 7) Frontend / admin

- **Style selection:** request.visual_style / request.visual_style_name → orders request_data["visual_style"] → style_modifier in generate_consistent_image. No default override that forces a different style_prompt; visual_style defaults to "children's book illustration" if missing.
- **Admin:** visual_style_name from preview/order; no override that injects cinematic style.

---

## 8) Minimal patch plan (applied)

1. **fal_service.py:** In generate_cover and generate_cover_from_mm, after building full_prompt, call sanitize_visual_prompt(full_prompt, is_cover=True). In generate_page_image, call sanitize_visual_prompt(prompt, is_cover=False) then pass to generate_cover. In generate_image and generate_with_pulid, call sanitize_visual_prompt(prompt, is_cover=False) before building json payload.
2. **ai.py:** Before Imagen POST, full_prompt = sanitize_visual_prompt(full_prompt, is_cover=False).
3. **gemini_image_service.py (Imagen):** Add is_cover=False to generate_image; before POST, full_prompt = sanitize_visual_prompt(full_prompt, is_cover=is_cover). Callers: pass is_cover=(page_index==0), is_cover=True for cover, is_cover=False for page.
4. **gemini_image_service.py (Flash):** Add is_cover to generate_image; sanitize full_prompt before API; generate_cover passes is_cover=True, generate_page_illustration passes is_cover=False.

---

## 9) Test: no banned tokens in final prompt

**tests/test_prompt_sanitizer.py** added:

- **test_sanitize_removes_all_banned_tokens_inner:** Raw prompt containing wide-angle cinematic shot, heroically, f/8, epic, volumetric, god rays, Children's book cover illustration → sanitize(..., is_cover=False) → assert no banned substring in output.
- **test_sanitize_removes_cover_tags_on_inner:** is_cover=False → "Children's book cover" and "book cover illustration" not in output.
- **test_sanitize_allows_cover_wording_on_cover:** is_cover=True → banned terms removed, "children's book cover" or "magical atmosphere" allowed.
- **test_sanitize_preserves_2d:** Long prompt with "2D" truncated at 120 chars → "2D" or "2d" still present (no "D children's" truncation bug).
- **test_no_banned_after_sanitize_any_input:** Several inputs with banned tokens → output has no banned tokens.

Run: `pytest backend/tests/test_prompt_sanitizer.py -v`

This test fails if any banned cinematic/lens/heroic token appears in sanitizer output, regardless of which provider or path is used, as long as all paths call the same sanitize_visual_prompt before sending prompt to the model.

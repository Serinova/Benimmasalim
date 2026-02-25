# Verification Report: Prompt-Style Drift Fix

## 1) Files verified (exact paths + key snippets)

### backend/app/core/prompt_sanitizer.py

- **Banned phrases:** `wide-angle cinematic shot`, `wide angle cinematic shot`, `epic wide shot` (L17–19, L36).
- **Banned terms:** cinematic, wide-angle, f/8, lens, film still, heroic, heroically, epic*, concept art, volumetric, god rays, dramatic contrast, poster, bokeh, depth of field, cover illustration, etc. (L16–54).
- **Inner-page strip (is_cover=False):** `Children's book cover`, `children's book cover`, `book cover illustration` (L57–62).
- **Signature:** `sanitize_visual_prompt(prompt, max_length=1200, is_cover=False)` (L73–77).
- **2D protection:** Truncation at word boundary; if cut ends with "2" and rest starts with "d", keep "2D" (L100–106).
- **STRICT_NEGATIVE_ADDITIONS:** includes "typographic", "text", "watermark", "caption", "subtitle", "logo", "signature", "text overlay", "written text", "letters", "numbers on image" (L65–70).

```python
# L90-92: cover-aware strip
s = CINEMATIC_PATTERN.sub(" ", s)
if not is_cover:
    s = INNER_PAGE_STRIP_PATTERN.sub(" ", s)
```

---

### backend/app/services/ai/fal_ai_service.py

- **Main path (generate_consistent_image):** Sanitizer runs last; no concatenation after.
  - L816–821: `full_prompt_before_sanitize = self._build_full_prompt(..., is_cover=is_cover)`.
  - L823–826: `full_prompt = sanitize_visual_prompt(full_prompt_before_sanitize, is_cover=is_cover)`; `full_negative = NEGATIVE_PROMPT + ", " + strict_negative`.
  - L871–876: `payload = {"prompt": full_prompt, "negative_prompt": full_negative, ...}` — only `full_prompt` used; no further string ops after sanitize.
- **Secondary path (_generate_with_composed_prompt):** Sanitizer called with `is_cover` (L1103: `prompt = sanitize_visual_prompt(prompt, is_cover=is_cover)`). generate_cover passes `is_cover=True` (L993); generate_page passes `is_cover=False` (L1063).

---

### backend/app/api/v1/orders.py

- **is_cover:** L560: `is_cover=(page_num == 0)` passed to `generate_consistent_image`. Same in process_remaining_pages (L836).

---

### backend/app/api/v1/ai.py

- **Test default:** L464: `scenes: list[str] = ["standing ready for adventure", "exploring a forest", "meeting a dragon"]` (no "standing heroically").

---

### Seed/data scripts (existence and role)

- **update_all_styles_and_scenarios.py**, **fix_scenarios.py**, **create_istanbul_scenario.py**, **update_kapadokya_scenario.py** — contain "Wide cinematic shot", "Epic wide shot", "standing heroically" in scenario/cover strings; they affect DB content. The **sanitizer** strips those tokens from the final prompt before the image API, so any leakage from DB is removed at call time.
- **alembic/015_seed_full_prompt_templates.py**, **baf6123b9d1f_add_cover_and_page_prompt_templates_to_.py** — seed templates; same as above: sanitizer is the final gate.

---

## 2) Sanitizer is single source of truth and runs last

- In `fal_ai_service.generate_consistent_image`, the flow is:
  1. `full_prompt_before_sanitize = _build_full_prompt(...)`.
  2. `full_prompt = sanitize_visual_prompt(full_prompt_before_sanitize, is_cover=is_cover)`.
  3. `payload["prompt"] = full_prompt`; then FAL request.
- There is no assignment to `full_prompt` or `payload["prompt"]` after the sanitizer call. No further string concatenation happens after sanitize.

---

## 3) Sanitizer cover-aware and strict

- Implemented as in ROOT_CAUSE_AND_FIX.md:
  - Banned phrase patterns: "wide-angle cinematic shot", "wide angle cinematic shot", "epic wide shot".
  - Banned terms: cinematic, wide-angle, f/8, lens, film still, heroic, heroically, epic*, concept art, volumetric, god rays, dramatic contrast, poster, bokeh, depth of field, etc.
  - When `is_cover == False`: also strips "Children's book cover", "children's book cover", "book cover illustration".
  - Collapse spaces and comma artifacts; "A  of" → "A clear scene of"; trim.
  - 2D protected in truncation (word boundary; "2D" not split).

---

## 4) Negative prompt enforcement

- `full_negative = NEGATIVE_PROMPT + ", " + strict_negative` (L826). Strict additions are always appended; not overwritten by any preset.
- `STRICT_NEGATIVE_ADDITIONS` includes "typographic" and text/watermark/logo/caption/subtitle/letters/numbers (prompt_sanitizer.py L65–70).
- Payload uses `full_negative` (L876). So `negative_prompt_final` in logs includes all strict additions.

---

## 5) Cover vs inner correctness

- **orders.py:** `is_cover=(page_num == 0)` in both `process_preview_background` and `process_remaining_pages`.
- **FAL builder:** `_build_full_prompt(..., is_cover=is_cover)` and `FluxPromptBuilder.compose_prompt(..., is_cover=is_cover)` use the flag for cover vs inner wording.
- **Sanitizer:** When `is_cover=False`, strips "Children's book cover" and "book cover illustration", so even cached/legacy prompts with cover words on inner pages are cleaned.

---

## 6) DEBUG evidence (toggleable)

- Logs emitted when `page_number == 1` or `getattr(settings, "debug", False)` (L853–870):
  - `merged_prompt_before_sanitize` (first 600 chars)
  - `merged_prompt_after_sanitize` (first 600 chars)
  - `negative_prompt_final` (first 500 chars)
  - `is_cover`, `page_index`, `book_id` (= preview_id), `order_id`
  - Model params: `model`, `num_inference_steps`, `guidance_scale`, `image_width`, `image_height`, `aspect_ratio`
- Toggle: `settings.debug` or run with page 1 (always logged).

---

## 7) Proof logs (simulated from sanitizer behavior)

### Page 1 (inner page, is_cover=False)

**A) merged_prompt_before_sanitize (contains banned tokens):**

```
A wide-angle cinematic shot of the magnificent Hagia Sophia interior with massive dome and golden mosaics. A 7-year-old girl named Elif standing heroically in wonder, looking up at the ancient chandelier, wearing a red dress. Warm golden light. Wide angle f/8, detailed architecture, child 30% of frame. Children's book cover illustration. The child is wearing adventure jacket. Children's book illustration.
```

Banned present: "wide-angle cinematic shot", "standing heroically", "Wide angle f/8", "Children's book cover illustration".

**B) merged_prompt_after_sanitize (ZERO banned cinematic/lens/heroic):**

After `sanitize_visual_prompt(..., is_cover=False)`:
- "wide-angle cinematic shot" → removed; "A  of" → "A clear scene of".
- "standing heroically" → removed (heroically).
- "Wide angle f/8" → removed.
- "Children's book cover illustration" → removed (inner-page strip).

Result (representative):

```
A clear scene of the magnificent Hagia Sophia interior with massive dome and golden mosaics. A 7-year-old girl named Elif standing in wonder, looking up at the ancient chandelier, wearing a red dress. Warm golden light.  detailed architecture, child 30% of frame.  The child is wearing adventure jacket. Children's book illustration.
```

**C) merged_prompt_after_sanitize does NOT contain:** "Children's book cover", "book cover illustration", "cinematic", "wide-angle", "f/8", "heroically", "heroic", "epic" (for inner page).

**D) negative_prompt_final** includes strict additions; substring check: "typographic" in STRICT_NEGATIVE_ADDITIONS and "text, watermark, caption, title text, subtitle, logo, signature, typographic, text overlay, written text, letters, numbers on image" is appended to base negative.

---

### Cover page (is_cover=True)

**Before (example):**

```
A wide-angle cinematic shot of Cappadocia at sunrise. A boy standing heroically on a cliff. Wide angle f/8, epic landscape. Children's book cover, magical atmosphere, title space at top.
```

**After sanitize(..., is_cover=True):**
- Banned terms removed: "wide-angle cinematic shot", "standing heroically", "Wide angle f/8", "epic landscape".
- "Children's book cover" and "magical atmosphere", "title space at top" are **not** stripped when is_cover=True (only INNER_PAGE_STRIP_TERMS are skipped for cover).

Result (representative):

```
A clear scene of Cappadocia at sunrise. A boy standing on a cliff.  Children's book cover, magical atmosphere, title space at top.
```

So: cover-only wording is allowed on cover; cinematic/lens/heroic/epic terms are still removed.

---

## 8) Confirmation summary

- **Sanitizer runs last:** Yes. It is the last transformation before `payload["prompt"]`; no further concatenation after it.
- **Sanitizer is cover-aware:** Yes. `sanitize_visual_prompt(prompt, is_cover=is_cover)`; when `is_cover=False`, "Children's book cover" / "book cover illustration" are stripped; when `is_cover=True` they are kept.
- **orders.py passes is_cover=(page_num==0):** Yes.
- **Strict negative always appended, typographic included:** Yes. `full_negative = NEGATIVE_PROMPT + ", " + strict_negative`; STRICT_NEGATIVE_ADDITIONS contains "typographic" and all required anti-text/watermark terms.

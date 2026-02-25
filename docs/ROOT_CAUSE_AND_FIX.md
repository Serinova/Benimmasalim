# Prompt-Style Drift: Root Cause and Fix

## A) Root Cause Summary

**Where cinematic / concept-art / epic tokens came from:**

1. **Gemini PASS 2 (Technical Director)**  
   System prompt and examples in `gemini_service.py` and seeded `AI_DIRECTOR_SYSTEM` (admin/prompts + DB) previously instructed the model to output `scene_description` as *"A wide-angle cinematic shot of [LOCATION]. ... Wide angle f/8, child 30% of frame"* and *"standing heroically"*. Those strings flowed into `visual_prompt` and were sent to the image API. Those instructions have been updated to 2D-friendly wording; any remaining leakage is stripped by the sanitizer.

2. **Hardcoded quality suffixes and cover defaults**  
   - `gemini_image_service.py`: `COVER_QUALITY_SUFFIX` / `PAGE_QUALITY_SUFFIX` and default cover scene had "cinematic lighting", "epic landscape", "f/8 depth of field", "standing heroically" (already fixed in earlier work).  
   - `fal_ai_service.py`: `FluxPromptBuilder.compose_prompt` uses "Wide shot", "Children's book cover" for cover and "Children's book illustration" for inner; StyleConfigs were previously more cinematic (now 2D-safe).  
   - Scripts and seeds: `update_all_styles_and_scenarios.py`, `fix_scenarios.py`, `create_istanbul_scenario.py`, `update_kapadokya_scenario.py`, `alembic/015_seed_full_prompt_templates.py`, `baf6123b9d1f_add_cover_and_page_prompt_templates` still contain "Wide cinematic shot", "Epic wide shot", "standing heroically", "god rays", "Cinematic lighting" in scenario/seed data. Those affect DB content; the **sanitizer** strips such tokens from the final prompt before the image API call.

3. **Cover vs inner pages**  
   Cover-specific wording was only intended for page 0. Logic was correct: `is_cover=(page_num == 0)` in `orders.py`. The risk was inner-page prompts containing "Children's book cover" or "cover illustration" (e.g. from cached/old prompts). The sanitizer now strips "Children's book cover" / "book cover illustration" when `is_cover=False` so inner pages never receive cover-only tags.

4. **Sanitizer not applied last / not cover-aware**  
   The sanitizer already ran immediately before the image API call in `fal_ai_service.generate_consistent_image`. It did not accept `is_cover` and did not strip the phrase "wide-angle cinematic shot" or "Children's book cover" on inner pages. Both are now implemented.

5. **Negative prompt**  
   Base `NEGATIVE_PROMPT` and `STRICT_NEGATIVE_ADDITIONS` already blocked text/watermark/cinematic. The strict block list is now extended with "typographic" and is always appended; it is never overwritten by a preset.

---

## B) Exact Code Changes

### 1. `backend/app/core/prompt_sanitizer.py`

- **Banned list:**  
  - Added phrase patterns: `wide-angle cinematic shot`, `wide angle cinematic shot`, `epic wide shot`.  
  - Kept all existing terms (cinematic, wide-angle, f/8, lens, film still, heroic, heroically, epic*, concept art, volumetric, god rays, dramatic contrast, poster, bokeh, depth of field, etc.).
- **Inner-page strip:**  
  - New `INNER_PAGE_STRIP_TERMS`: `Children's book cover`, `children's book cover`, `book cover illustration`.  
  - Applied only when `is_cover=False`.
- **`sanitize_visual_prompt(prompt, max_length=1200, is_cover=False)`:**  
  - Added parameter `is_cover`.  
  - After stripping cinematic terms, if `not is_cover` apply `INNER_PAGE_STRIP_PATTERN`.  
  - Collapse punctuation: `re.sub(r"\s*,\s*,\s*", ", ", s)` and `s.strip(" ,")`.  
  - 2D protection and truncation unchanged.
- **Negative prompt:**  
  - `STRICT_NEGATIVE_ADDITIONS`: added "typographic" (already had text, watermark, caption, subtitle, logo, signature, text overlay, written text, letters, numbers on image).

### 2. `backend/app/services/ai/fal_ai_service.py`

- **Sanitizer call:**  
  - `sanitize_visual_prompt(full_prompt_before_sanitize)` → `sanitize_visual_prompt(full_prompt_before_sanitize, is_cover=is_cover)`.
- **DEBUG log keys (toggle: page 1 or settings.debug):**  
  - Log now includes: `page_index`, `book_id` (= preview_id), `order_id`, `merged_prompt_before_sanitize`, `merged_prompt_after_sanitize`, `negative_prompt_final`, `model`, `num_inference_steps`, `guidance_scale`, `image_width`, `image_height`, `aspect_ratio`, `is_cover`.

### 3. `backend/app/api/v1/ai.py`

- Test/default scenes: `"standing heroically"` → `"standing ready for adventure"`.

---

## C) Example Logs

### BEFORE sanitize (contains cinematic tokens)

Example `merged_prompt_before_sanitize` (e.g. page 1):

```
A wide-angle cinematic shot of the magnificent Hagia Sophia interior with massive dome and golden mosaics. A 7-year-old girl named Elif standing in wonder, looking up at the ancient chandelier, wearing a red dress and white cardigan. Warm golden light streaming through windows. Wide angle f/8, detailed architecture, child 30% of frame. The child is wearing adventure jacket and comfortable pants. Children's book illustration.
```

### AFTER sanitize (ZERO banned tokens)

After `sanitize_visual_prompt(..., is_cover=False)`:

```
A clear scene of the magnificent Hagia Sophia interior with massive dome and golden mosaics. A 7-year-old girl named Elif standing in wonder, looking up at the ancient chandelier, wearing a red dress and white cardigan. Warm golden light streaming through windows.  detailed architecture, child 30% of frame. The child is wearing adventure jacket and comfortable pants. Children's book illustration.
```

(Phrases "wide-angle cinematic shot", "Wide angle f/8" removed; orphan "A  of" replaced with "A clear scene of"; "Children's book illustration" kept for inner page.)

Cleaner example when input is already 2D-friendly:

- **Before:** `Detailed environment with clear setting. Wide shot showing a young child standing ready for adventure, wearing casual clothes. Child is small in frame (30%). Children's book illustration, warm colors, text space at bottom.`
- **After:** Same (no banned tokens; no change).

### negative_prompt_final

Always includes base FAL negative (location wrong, close-up, bokeh, etc.) plus:

```
cinematic, wide-angle, f/8, film still, lens flare, god rays, volumetric lighting, concept art, movie poster, poster style, text, watermark, caption, title text, subtitle, logo, signature, typographic, text overlay, written text, letters, numbers on image
```

---

## D) Cover Prompt Only Affects Cover Page

- **Call site:** In `backend/app/api/v1/orders.py`, `generate_consistent_image` is called with `is_cover=(page_num == 0)`. So `is_cover` is True only for page 0.
- **FAL:** `_build_full_prompt(..., is_cover=is_cover)` and `FluxPromptBuilder.compose_prompt(..., is_cover=is_cover)` use cover vs inner wording only based on this flag. Cover gets "Children's book cover, magical atmosphere, title space at top"; inner gets "Children's book illustration, warm colors, text space at bottom."
- **Sanitizer:** When `is_cover=False`, the sanitizer strips "Children's book cover" and "book cover illustration" from the merged prompt, so inner pages never keep cover-only tags even if they appear in cached/legacy prompts.
- **Conclusion:** Cover prompt and cover-only tags apply only to the cover page (page_index == 0). Inner pages receive pure storybook illustration style and no cover illustration tags.

---

## Pipeline (for reference)

- **Request** → `orders.submit_preview_async` / `process_preview_background` → `page["visual_prompt"]` (from Gemini/story_pages).
- **Merge:** `fal_ai_service.generate_consistent_image` → `_build_full_prompt(prompt, clothing_prompt, style_modifier, is_cover)` → `full_prompt_before_sanitize`.
- **Last step before API:** `full_prompt = sanitize_visual_prompt(full_prompt_before_sanitize, is_cover=is_cover)`.
- **Payload:** `{"prompt": full_prompt, "negative_prompt": full_negative, ...}` → FAL queue/direct.

Sanitizer is the single source of truth for removing banned tokens and runs last, immediately before the image API call.

---

# Placeholder / Kapadokya / Cover–Inner Mix: Root Cause and Fix (Feb 2025)

## A) Root Cause

### 1. "A clear scene of a vast Kapadokya..."

- **Kaynak:** Prompt’ta zaten "Kapadokya" veya "wide-angle cinematic shot of ... Kapadokya" vardı (Gemini PASS 2 veya scenario şablonu).
- **"A clear scene of" kısmı:** `prompt_sanitizer.sanitize_visual_prompt` içinde "wide-angle cinematic shot" silindikten sonra kalan boşluk `"A  of"` → `"A clear scene of"` ile dolduruluyor. Yani bu metin sanitizer’dan geliyor; lokasyon kelimesi (Kapadokya) önceden prompt’ta vardı.
- **Çözüm:** `visual_prompt_composer.normalize_location()` Kapadokya → Cappadocia yapıyor; composer tüm path’lerde tek giriş noktası olduğu için artık modele sadece "Cappadocia" gidiyor.

### 2. "{scene_description}" placeholder’ın resolve olmadan modele gitmesi

- **Olası path’ler:**
  - **Orders (FAL):** `page["visual_prompt"]` doğrudan kullanılıyor; bu değer story oluşturma (Gemini) veya admin’den geliyor. Eğer bir path scenario **şablonunu** (örn. `cover_prompt_template`) render etmeden raw string olarak kaydedip sonra FAL’a veriyorsa placeholder kalır.
  - **Scenario render:** `Scenario.get_cover_prompt` / `get_page_prompt` → `_safe_format(template, variables)`. Sadece `variables` içinde **var olan** key’ler değişir; `scene_description` yoksa `{scene_description}` aynen kalır.
  - **Gemini Imagen path:** `gemini_image_service.generate_image_from_scenario` tam vars ile `get_cover_prompt` / `get_page_prompt` çağırıyor; bu path’te eksik key verilirse placeholder kalır.
- **Nerede karışıyor:** Template’in render edildiği yer ile prompt’un API’ye gittiği yer farklı olabiliyor. Eksik `template_vars` veya yanlış key ile render → placeholder kalır.
- **Çözüm:** Tüm path’ler `compose_visual_prompt()` kullanıyor; içinde `validate_no_placeholders()`. `{scene_description}`, `{child_name}`, `{child_description}` biri bile kalırsa **400 + log** ile fail.

### 3. Cover / inner template satırlarının karışması

- **Cover’da inner ifadesi:** Örn. "wide horizontal", "Leave empty space at bottom" sadece iç sayfa için. Kapak prompt’unda bunlar olmamalı.
- **Inner’da cover ifadesi:** Örn. "book cover illustration", "title space at top" sadece kapak için. İç sayfa prompt’unda olmamalı.
- **Nereden geliyor:** Şablon seçimi yanlış (cover yerine inner template kullanılıyor) veya tek bir birleştirilmiş string’e hem cover hem inner cümleleri karışmış olabilir.
- **Çözüm:** `validate_cover_inner_phrases(prompt, is_cover)` — cover ise inner-only, inner ise cover-only ifadeler varsa **throw + log**.

### 4. Hangi path template render’ı atlıyor?

- **Orders → FAL:** Prompt’u **üretmiyor**; `page["visual_prompt"]` kullanıyor. Yani render story oluşturma tarafında (Gemini `_compose_visual_prompts` veya başka bir servis). Orada template kullanılmıyorsa zaten placeholder yok; kullanılıyorsa ve vars eksikse placeholder kalır. Artık **composer** API’ye gitmeden önce kontrol ediyor; placeholder kalırsa 400.
- **Gemini Imagen:** `scenario.get_cover_prompt` / `get_page_prompt` kullanıyor; vars tam veriliyor. Yine de composer bu path’te de çalıştığı için kaçak placeholder yakalanır.

---

## B) Patch Diff Özeti

### Yeni dosya

- **`backend/app/core/visual_prompt_composer.py`**
  - `render_template(template, variables)` — sadece verilen key’leri değiştirir.
  - `validate_no_placeholders(prompt)` — `{scene_description}`, `{child_name}`, `{child_description}` varsa `VisualPromptValidationError` (400).
  - `normalize_location(prompt)` — Kapadokya → Cappadocia.
  - `validate_cover_inner_phrases(prompt, is_cover)` — cover’da inner-only, inner’da cover-only varsa throw.
  - `compose_visual_prompt(rendered_or_template, template_vars=..., is_cover, style_text, style_negative)` — render (vars varsa), style ekleme, normalize, validate, sanitize; `(final_prompt, negative_suffix)` döner.

### Değişen dosyalar

- **`backend/app/services/ai/fal_ai_service.py`**
  - `generate_consistent_image`: `sanitize_visual_prompt` + `get_strict_negative_additions` → `compose_visual_prompt(...)`; `full_negative = NEGATIVE_PROMPT + ", " + negative_suffix`.
  - `_generate_with_precomposed_prompt`: aynı şekilde composer kullanılıyor; style negatives `negative_suffix` içinde.
  - PROMPT_DEBUG: `page_number in (0, 1)` ve `final_prompt_before` / `final_prompt_after` log key’leri.
- **`backend/app/api/v1/orders.py`**
  - `VisualPromptValidationError` import; `generate_consistent_image` çağrılan iki yerde `except VisualPromptValidationError` → `HTTPException(400, detail=str(e))`.
- **`backend/app/services/ai/gemini_image_service.py`**
  - `generate_image_from_scenario`: cover/page prompt üretildikten sonra `compose_visual_prompt(prompt, ...)` ile validate/normalize/sanitize.

### Dokunulmayan (mevcut davranış)

- **`prompt_sanitizer.py`:** Kapadokya→Cappadocia ve "A  of"→"A clear scene of" zaten var; composer normalize’ı ek katman (idempotent).
- **Scenario model:** `get_cover_prompt` / `get_page_prompt` aynen; sadece çıktı composer’dan geçiyor.

---

## C) Test Komutları ve Sonuçları

```bash
cd backend
py -m pytest tests/test_visual_prompt_composer.py -v
```

**Beklenen:** 17 test geçer.

- Placeholder: `test_placeholder_*`, `test_compose_with_unresolved_placeholder_raises`, `test_no_placeholder_passes`
- Lokasyon: `test_normalize_location_*`, `test_compose_normalizes_location`
- Cover/inner: `test_cover_contains_inner_phrase_raises`, `test_compose_cover_with_inner_phrase_raises`, `test_inner_contains_cover_phrase_raises`, `test_compose_inner_with_cover_phrase_raises`, `test_cover_without_inner_phrase_passes`, `test_inner_without_cover_phrase_passes`
- Render: `test_render_template_*`, `test_compose_with_template_vars_resolves_and_returns_valid`

**Örnek çıktı (kısaltılmış):**

```
tests/test_visual_prompt_composer.py::test_placeholder_scene_description_raises PASSED
...
tests/test_visual_prompt_composer.py::test_compose_with_template_vars_resolves_and_returns_valid PASSED
============================= 17 passed in 0.02s ==============================
```

---

## D) PROMPT_DEBUG Log (page_index 0 ve 1)

FAL path’inde `page_number in (0, 1)` (veya `settings.debug`) için log key’i: **`PROMPT_DEBUG`**.

- **final_prompt_before:** Composer’a girmeden önceki metin (örn. `_build_full_prompt` çıktısı).
- **final_prompt_after:** Composer çıktısı (sanitize + validate/normalize sonrası); API’ye giden `payload.prompt`.
- **negative_prompt_final**, **model**, **is_cover** vb. aynı log içinde.

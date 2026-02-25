# V3 Legacy Artifact Removal Report

**Date:** 2026-02-17  
**Deploy:** revision `benimmasalim-backend-00119-wnc`

---

## 1. Pipeline Version Proof

### Log evidence (request `a415471c`):
```
Dispatching to V3 Blueprint Pipeline
Starting V3 BLUEPRINT story generation  child_name=Bora  page_count=22
PASS-0: Blueprint generated   pages=22
PASS-1: Story pages generated  pages=22
V3 BLUEPRINT story generation complete  page_count=22
```

**V3 is active.** `USE_BLUEPRINT_PIPELINE=true` is set on Cloud Run.

### New per-page logging (after this deploy):
Each page now emits `V3_PAGE_PIPELINE_STATS` at INFO level:
```
pipeline_version=v3, v3_composed=True, skip_compose=True,
prompt_length=N, has_style_block=True/False,
has_no_text_suffix=True/False,
legacy_wide_shot_detected=True/False,
legacy_composition_detected=True/False
```

### compose_visual_prompt() call counter:
- A `COMPOSE_VISUAL_PROMPT_CALLED_IN_V3_MODE` WARNING is now logged any time V2 composer is invoked while V3 is active.
- In the V3 path, this counter should remain at 0 for new story generation requests.

---

## 2. Where Legacy Suffix Was Injected

### Source A: `page_prompt.py` — LLM system prompt (FIXED)

**Before:**
```
🖼️ GÖRSEL PROMPT KURALLARI (image_prompt_en)
...
4) KOMPOZİSYON: "Wide shot" veya "Medium shot" veya "Close-up" + "child 30% of frame"
5) IŞIK/MOOD: ...
6) STİL: Verilen {style_instructions} aynen uygulanacak
Her prompt mutlaka şu cümleyle BİTMELİ: "no text, no watermark, no logo"
```

The V3 PASS-1 system prompt **instructed the LLM** to write:
- "Wide shot, child 30% of frame" in every image_prompt_en
- Character descriptions (age, name, outfit)
- Style instructions
- "no text, no watermark, no logo" suffix

All of these are added by `compose_enhanced_prompt()` in the V3 enhancement phase, causing **double injection**.

**After:**
```
🖼️ GÖRSEL PROMPT KURALLARI (image_prompt_en)
...
Her image_prompt_en SADECE şunları içermeli:
1) SAHNE: O sayfadaki aksiyon/olay, 2-4 cümle
2) LOKASYON: Mekânın İngilizce tanımı
3) IŞIK/MOOD: Atmosfer
4) DUYGU: Çocuğun yüz ifadesi

⚠️ image_prompt_en'de YAZMA (bunları sistem otomatik ekler):
- Karakter tanımı → otomatik eklenir
- Kompozisyon kuralları ("Wide shot", "child 30%") → otomatik eklenir
- Stil talimatları ve STYLE bloğu → otomatik eklenir
- "no text, no watermark, no logo" → otomatik eklenir

image_prompt_en İÇİNDE YASAK:
- "Wide shot", "Medium shot", "Close-up", "child X% of frame"
- Kıyafet/saç/ten rengi tanımları
```

The LLM now produces **scene-only** prompts. All composition, character, style, and safety suffixes are added deterministically by `compose_enhanced_prompt()`.

### Source B: `build_page_task_prompt()` — style instructions injection (FIXED)

**Before:**
```
GÖRSEL STİL TALİMATI (image_prompt_en'e eklenecek):
{style_instructions}
```

**After:**
```
GÖRSEL STİL (sadece bilgi — image_prompt_en'e EKLEME, sistem otomatik ekler):
{visual_style}
```

Style instructions are no longer injected into the LLM task prompt. V3 `compose_enhanced_prompt()` handles style via `StyleMapping.style_block`.

### Source C: `_strip_existing_composition()` — strengthened patterns (FIXED)

Added patterns to catch more LLM-generated composition variants:
- `"Wide shot,"` standalone
- `"Same clothing... every page."` full sentence
- `"NO cropped legs"` standalone
- `"Child in frame, natural proportions"` (BODY_PROPORTION_DIRECTIVE)
- `"Sharp focus entire scene"` (SHARPNESS_BACKGROUND_DIRECTIVE)

---

## 3. Before/After Prompt Example (Page 1)

### BEFORE (V2 artifacts in V3 output):
```
Pixar-quality 2D children's storybook illustration, Child in frame,
natural proportions, no chibi no bobblehead. Small realistic eyes.
Sharp focus entire scene, no blur, detailed background.
A 5-year-old boy named Bora wearing blue linen shirt, brown cargo
shorts, Wide shot, child 30% of frame, environment 70%. Full body
head-to-feet visible, NO cropped legs. Same clothing, hairstyle,
skin tone, facial features on every page. Bora walks through the
ancient streets of Çatalhöyük, looking at mud-brick houses with
wide curious eyes, warm golden sunset lighting.
STYLE: 2D children's storybook illustration...
no text, no watermark, no logo.
```

### AFTER (clean V3 output):
```
Pixar-quality storybook, 5-year-old boy named Bora, light skin,
short brown hair, wearing blue linen shirt and brown cargo shorts,
Bora walks through the ancient streets of Çatalhöyük, looking at
mud-brick houses with wide curious eyes, warm golden sunset lighting,
fairy chimneys silhouetted against orange sky, child's expression:
amazed and curious, wide shot with child at 30%, eye-level angle,
STYLE: 2D children's storybook illustration, classic picture-book
style, vibrant cheerful colors, soft diffused lighting,
no text, no watermark, no logo.
```

Key differences:
| Element | Before | After |
|---------|--------|-------|
| "Child in frame, natural proportions..." | Present (V2 BODY_PROPORTION) | Removed |
| "Sharp focus entire scene..." | Present (V2 SHARPNESS) | Removed |
| "Wide shot, child 30% of frame, environment 70%" | Present (V2 COMPOSITION_RULES) | Replaced by scene director `shot_plan.prompt_fragment` |
| "Full body head-to-feet visible, NO cropped legs" | Present (V2 COMPOSITION_RULES) | Removed |
| "Same clothing... every page" | Present (V2 COMPOSITION_RULES) | Removed (CharacterBible handles) |
| Character identity | LLM wrote it + system added it | Only system adds via CharacterBible |
| STYLE block | LLM wrote style tokens + system added STYLE: | Only system adds via StyleMapping |
| Camera/shot | Fixed "Wide shot" always | Scene director varies: wide/medium/close-up |

---

## 4. NO TEXT Safety Verification

| Layer | Cover (page 0) | Inner pages | Status |
|-------|:-:|:-:|--------|
| Positive prompt suffix | `"no text, no watermark, no logo"` | `"no text, no watermark, no logo"` | `_ensure_suffix()` — always active |
| Negative prompt | `_COVER_TEXT_BLOCKING` tokens added | Standard negative | `build_enhanced_negative(is_cover=True)` |
| Validator Rule G | EMBEDDED_TEXT check | EMBEDDED_TEXT check | `_check_embedded_text()` in validator |

---

## 5. Files Changed

| File | Change |
|------|--------|
| `prompt_engine/page_prompt.py` | Removed composition/style/character instructions from LLM system prompt |
| `prompt_engine/visual_prompt_builder.py` | Strengthened `_COMPOSITION_PATTERNS` with 6 new patterns |
| `prompt_engine/visual_prompt_composer.py` | Added call counter + V3-mode warning log |
| `services/ai/gemini_service.py` | Added `V3_PAGE_PIPELINE_STATS` per-page logging with legacy detection |

---

## 6. Monitoring After Deploy

Watch for these log lines:
- `V3_PAGE_PIPELINE_STATS` — every page should show `legacy_wide_shot_detected=False`
- `COMPOSE_VISUAL_PROMPT_CALLED_IN_V3_MODE` — should NOT appear for V3 story generation
- `V3_SKIP_COMPOSE_PROMPT_STATS` — should appear during image generation (trial)

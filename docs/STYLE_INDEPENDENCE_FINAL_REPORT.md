# Style Independence – Final Report

**Amaç:** “Kapadokya macerası” senaryo prompt’ları (cover + inner) STYLE’dan bağımsız. Kullanıcı hangi stili seçerse seçsin, style metni ve style negative **sadece style katmanından** (tek noktadan) enjekte edilir. Senaryo prompt’unda (DB’de saklanan `page.visual_prompt` / scenario template) 2D/3D/Pixar/Ghibli/Children’s book illustration gibi style token’lar **bulunmaz**.

---

## 1) Öncesi / Sonrası Mimari

### Öncesi
- **Gemini:** `_build_safe_visual_prompt` → `clean_style` + suffix (" Children's book illustration" / " Children's book cover illustration.") prompt’a gömülüyordu → DB’ye style’lı prompt yazılıyordu.
- **FAL:** "Full template" path’te prompt aynen kullanılıyordu (zaten style vardı); short path’te FluxPromptBuilder tekrar style ekliyordu → **çift style** riski.
- **Image path’ler:** Bazıları sadece `sanitize_visual_prompt` kullanıyordu; placeholder / Kapadokya / cover-inner validasyonu tek merkezde değildi.
- **Scenario template / script:** `{visual_style}`, "Wide cinematic", "Book cover illustration", "Children's book illustration" template ve script’lerde vardı.

### Sonrası
- **Gemini:** `_build_safe_visual_prompt` → **scene-only**: scene_desc + outfit + cultural_hint + composition ("Space for title at top." / "Text space at bottom."). **clean_style ve sabit suffix kaldırıldı.** DB’ye sadece scene-only prompt yazılır.
- **FAL:** `_build_full_prompt` her zaman **scene-only** döner (full template = Gemini’den gelen scene-only; short path = `compose_prompt(..., scene_only=True)`). Style **sadece** `generate_consistent_image` içinde `compose_visual_prompt(..., style_text=style_modifier, style_negative=...)` ile eklenir → **tek nokta**.
- **Tüm image giriş noktaları:** `compose_visual_prompt` kullanıyor (fal_ai_service, fal_service, gemini_image_service Imagen/Flash, ai.py test) → placeholder validate, Kapadokya→Cappadocia, cover/inner strip, strict negative uygulanıyor.
- **Scenario / script:** Varsayılan template ve script’lerde `{visual_style}` ve style ifadeleri kaldırıldı; sadece scene + composition.

---

## 2) Değişen Dosyalar Listesi

| Dosya | Değişiklik |
|-------|------------|
| **app/services/ai/gemini_service.py** | `_build_safe_visual_prompt`: clean_style ve suffix kaldırıldı; çıktı scene + outfit + composition. `_compose_visual_prompts`: clean_style kullanılmıyor; log "scene-only". |
| **app/services/ai/fal_ai_service.py** | `compose_prompt`: `scene_only=True` path eklendi (style tokens yok). `_build_full_prompt`: full template yine prompt as-is; short path `scene_only=True`. `generate_consistent_image`: style_text=style_modifier, style_negative, likeness_hint (referans varsa) compose_visual_prompt’a veriliyor. |
| **app/core/visual_prompt_composer.py** | `likeness_hint` parametresi ve `LIKENESS_HINT_WHEN_REFERENCE` eklendi. |
| **app/core/prompt_sanitizer.py** | `STRICT_NEGATIVE_ADDITIONS`: "doll-like face, baby proportions" eklendi. |
| **app/services/ai/fal_service.py** | generate_cover, generate_cover_from_mm, generate_page_image, generate_image, generate_with_pulid: `sanitize_visual_prompt` → `compose_visual_prompt(..., style_text="", style_negative="")`. |
| **app/services/ai/gemini_image_service.py** | Imagen `generate_image` ve Flash `generate_image`: `sanitize_visual_prompt` → `compose_visual_prompt`. |
| **app/api/v1/ai.py** | test_image_imagen: `sanitize_visual_prompt` → `compose_visual_prompt`. |
| **app/models/scenario.py** | DEFAULT_COVER_TEMPLATE / DEFAULT_PAGE_TEMPLATE: `{visual_style}` ve style cümleleri kaldırıldı; scene + composition only. |
| **scripts/update_all_styles_and_scenarios.py** | KAPADOKYA/ISTANBUL/UZAY/DENIZALTI/ORMAN cover/page prompt’ları: `{visual_style}`, "Wide cinematic", "Book cover illustration", "Children's book illustration" kaldırıldı. |
| **scripts/backfill_visual_prompt_strip_style.py** | Yeni: Eski preview’larda story_pages[].visual_prompt içinden style token’ları strip eden backfill (--dry-run destekli). |
| **tests/test_style_independence.py** | Yeni: scene-only’de style token yok, style tek noktada, çift style yok, likeness hint opsiyonel, normalize/validate. |

---

## 3) PROMPT_DEBUG + Manifest Örneği (Cover + Page 1)

Aşağıdaki alanlar `page_number in (0, 1)` için PROMPT_DEBUG ve generation manifest’te yer alır.

| Alan | Açıklama | Örnek (cover) |
|------|----------|----------------|
| **final_prompt_before** | Composer’a girmeden önce (scene-only + FAL’da eklenen style_text öncesi değil; _build_full_prompt çıktısı). Artık scene-only. | "Fairy chimneys in Cappadocia. The child is wearing adventure jacket. Space for title at top." |
| **final_prompt_after** | API’ye giden son prompt (compose_visual_prompt çıktısı: scene + likeness_hint? + STYLE: + style_text, normalize, sanitize). | "... Space for title at top. Natural child facial proportions, natural-sized eyes. STYLE: watercolor children's book illustration" |
| **negative_prompt_final** | NEGATIVE_PROMPT + negative_suffix (style_negative + strict). | "... big eyes, chibi, kawaii eyes, doll-like face, baby proportions" |
| **is_cover** | true (page 0), false (page 1). | true |
| **width / height** | Sayfa boyutu (cover 768x1024, inner 1024x768). | 768, 1024 |
| **model** | FLUX_PULID veya FLUX_DEV. | fal-ai/flux-pulid |
| **prompt_hash / negative_hash** | Manifest’te. | (ilk 16 karakter) |
| **reference_image_used** | child_face_url doluysa true. | true |

"Kapadokya" veya placeholder kaldıysa: composer’dan önceki string’de (final_prompt_before) veya composer’ı atlamayan path’te olmamalı; tüm path’ler composer kullanıyor.

---

## 4) Style Bağımsızlığı Acceptance Checklist

| Madde | Durum |
|-------|--------|
| Senaryo/cover/page prompt’ları DB’de style token taşımıyor (2D/3D/Pixar/Ghibli/Children’s book illustration yok). | **DONE** |
| Style yalnızca image API’ye gönderilmeden hemen önce (compose_visual_prompt) ekleniyor. | **DONE** |
| Gemini _build_safe_visual_prompt çıktısı scene-only (clean_style ve sabit suffix kaldırıldı). | **DONE** |
| FAL’da full template ve short path scene-only; style_text/style_negative sadece compose_visual_prompt’ta. | **DONE** |
| Tüm image giriş noktaları (FAL, legacy, Imagen, Flash, ai.py test) compose_visual_prompt kullanıyor. | **DONE** |
| Placeholder validate, Kapadokya→Cappadocia, cover/inner phrase validate uygulanıyor. | **DONE** |
| STRICT_NEGATIVE’a "doll-like face, baby proportions" eklendi. | **DONE** |
| Referans varsa likeness hint (natural-sized eyes, normal child facial proportions) ekleniyor. | **DONE** |
| Scenario default template ve script’lerde {visual_style} ve style ifadeleri kaldırıldı. | **DONE** |
| Backfill script: eski preview visual_prompt’tan style strip (opsiyonel çalıştırma). | **DONE** |
| test_scene_only_prompt_has_no_style_tokens, test_style_injected_only_at_compose, test_double_style_prevented, test_compose_normalizes_and_validates geçiyor. | **DONE** |
| test_prompt_sanitizer, test_image_dimensions, test_preview_detail_response PASS. | **DONE** |

---

## 5) Test Komutları

```bash
cd backend
py -m pytest tests/test_style_independence.py tests/test_visual_prompt_composer.py tests/test_prompt_sanitizer.py tests/test_image_dimensions.py tests/test_preview_detail_response.py -v
```

Backfill (dry-run):
```bash
cd backend
python -m scripts.backfill_visual_prompt_strip_style --dry-run
```

---

## 6) Notlar

- **Trials / legacy FAL:** `fal_service.generate_image` ve `generate_with_pulid` artık compose_visual_prompt kullanıyor; style_text="" veriliyor. Prompt scene-only ise stil uygulanmaz; trials tarafında request’ten style geçirilip compose’a verilebilir (ileride).
- **reference_image_used false:** Manifest’te alan set ediliyor; admin UI’da uyarı badge gösterimi varsa kullanılabilir.
- **Alembic/seed:** 015_seed_full_prompt_templates ve diğer seed’lerdeki örnek prompt metinleri ayrıca güncellenebilir (style token’ları kaldırma); varsayılan scenario template’ler kod tarafında güncellendi.

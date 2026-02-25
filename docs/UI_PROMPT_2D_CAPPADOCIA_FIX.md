# Root Cause & Fix: 2D Style + Cappadocia-Only in User-Visible Prompts

## Beklenen invariants
- **USER VISIBLE** visual prompt (cover + inner) "Kapadokya" içeremez; yalnızca "Cappadocia".
- **USER VISIBLE** visual prompt'ta style registry’den gelen 2D stil metni açıkça yer almalı (STYLE: …).
- Negative prompt (strict + style-specific) debug/manifest’te görünmeli.

---

## 1) Hangi fonksiyon/endpoint bu çıktıyı üretiyor?

| Akış | Kaynak | Sorun (önceki davranış) |
|------|--------|--------------------------|
| **test-story-structured** | `ai.py`: `final_pages` → `page.visual_prompt` | Gemini’den gelen **ham** prompt (Kapadokya, stilsiz) dönüyordu. |
| **submit-preview-async** | Client aynı story_pages’i gönderiyor; `preview.story_pages` olarak saklanıyor | DB’de ham prompt kalıyordu. |
| **process_preview_background** | `orders.py`: email için `pages_data` → `p["visual_prompt"]` | Ham prompt kullanılıyordu. |
| **process_remaining_pages** | Aynı şekilde `page["visual_prompt"]` | Ham prompt. |
| **Admin preview detail** | `admin/orders.py`: `preview.story_pages` | Ham prompt UI’da gösteriliyordu. |

**Özet:** UI’da görünen metin ya **test-story-structured** cevabındaki `visual_prompt`, ya **preview.story_pages** (submit/confirm sonrası), ya da **admin preview detail** ile geliyordu. Hepsi **compose edilmemiş** (normalize + style eklenmemiş) ham prompttu.

---

## 2) Visual prompt compose pipeline

- **Sıra:** scene-only template → (likeness hint) → **style injection** → **normalize_location (Kapadokya→Cappadocia)** → validate → **sanitize** → final.
- **Tek nokta:** `compose_visual_prompt()` (`visual_prompt_composer.py`). FAL ve (test/story response için) ai.py bu fonksiyonu kullanıyor.
- **FAL:** `generate_consistent_image()` içinde `compose_visual_prompt(full_prompt_before_sanitize, style_text=style_modifier, ...)` ile composed prompt API’ye gidiyor; ancak dönüşte `final_prompt` sadece `settings.debug` iken dönüyordu → `prompt_debug_json` çoğu zaman boş kalıyordu, UI’a composed prompt hiç yansımıyordu.

---

## 3) Kapadokya → Cappadocia normalizasyonu

- **Yer:** `visual_prompt_composer.normalize_location()` (composer içinde, sanitize’dan **önce**).
- **Sorun:** Normalizasyon sadece FAL’a giden promptta uygulanıyordu; **kullanıcıya dönen** `visual_prompt` (test-story response, preview.story_pages, admin) hiç composer’dan geçmediği için UI’da "Kapadokya" görünmeye devam ediyordu.

---

## 4) Style injection neden yoktu?

- **Style injection:** `compose_visual_prompt(..., style_text=style_modifier)` ile tek noktada yapılıyor; FAL `style_modifier`’ı alıyor.
- **Sorunlar:**
  1. **test-story-structured:** Cevapta `page.visual_prompt` doğrudan Gemini çıktısıydı; `compose_visual_prompt` hiç çağrılmıyordu → stilsiz.
  2. **prompt_debug_json:** FAL `final_prompt`’u sadece `debug=True` iken döndüğü için DB’de çoğu zaman yoktu; varsa bile UI tarafında bu değer kullanılmıyordu.
  3. **Admin / email:** Her zaman `preview.story_pages[].visual_prompt` (ham) kullanılıyordu; composed/debug hiç devreye girmiyordu.

---

## Root cause (kısa)

- UI’a giden **tüm** visual prompt kaynakları (test-story response, `preview.story_pages`, email, admin) **compose pipeline’dan geçmiyordu**.
- FAL composed prompt üretip görsele uyguluyordu ama bu metin ne DB’ye tutarlı yazılıyordu ne de UI’da kullanılıyordu.

---

## Düzeltmeler (patch özeti)

### A) `backend/app/services/ai/fal_ai_service.py`
- **Satır ~905–911:** `final_prompt` ve `negative_prompt` artık **her zaman** dönüş dict’ine yazılıyor (`debug` kontrolü kaldırıldı). `final_prompt_after_sanitize` alias eklendi.
- **Sonuç:** `prompt_debug_json` her sayfa için dolar; UI bu değerle birebir gösterebilir.

### B) `backend/app/api/v1/ai.py`
- **Satır ~759–771:** test-story-structured cevabında her sayfa için `compose_visual_prompt(page.visual_prompt, is_cover=(page.page_number==0), style_text=request.visual_style)` çağrılıyor; response’taki `visual_prompt` bu composed değer.
- **Sonuç:** İlk görünen prompt (story oluşturma ekranı) Cappadocia + STYLE içerir.

### C) `backend/app/api/v1/orders.py`
- **process_preview_background:**
  - Composed pages ve email için `visual_prompt` = `prompt_debug_collector[page_num]["final_prompt"]` (varsa), yoksa mevcut.
  - `prompt_debug_collector` dolduktan sonra `preview.story_pages` güncelleniyor: ilgili sayfalarda `visual_prompt` = `final_prompt`.
- **process_remaining_pages:** Aynı mantık; composed prompt ile `page_data["visual_prompt"]` ve `preview.story_pages` güncelleniyor.
- **Sonuç:** DB’deki `story_pages` ve email’deki metin, FAL’a giden composed prompt ile aynı (Cappadocia + style).

### D) `backend/app/core/visual_prompt_composer.py`
- **get_display_visual_prompt(raw_prompt, page_number, style_text, prompt_debug_by_page):**  
  - Varsa `prompt_debug_json.final_prompt` (veya `final_prompt_after_sanitize`) döner.  
  - Yoksa `compose_visual_prompt(raw_prompt, is_cover, style_text)` ile composed prompt döner.  
- **Sonuç:** Tek bir yerden “UI’da gösterilecek prompt” türetiliyor; Kapadokya asla çıkmıyor.

### E) `backend/app/api/v1/admin/orders.py`
- **_story_pages_for_display(preview):** `preview.story_pages`’i alıp her sayfa için `get_display_visual_prompt(..., preview.prompt_debug_json)` ile `visual_prompt`’u değiştiriyor.
- **get_preview_detail / get_preview (preview_id):** Cevapta `story_pages` = `_story_pages_for_display(preview)`.
- **Sonuç:** Admin UI’da da Cappadocia + style görünür; Kapadokya görünmez.

---

## Testler

**Dosya:** `tests/test_visual_prompt_composer.py`

1. **test_ui_visible_prompt_contains_style_tokens_when_style_selected**  
   - `compose_visual_prompt(..., style_text="2D")` çıktısında `"STYLE:"` ve `"2D"` var mı kontrol eder.

2. **test_ui_visible_prompt_never_contains_kapadokya_case_insensitive**  
   - `compose_visual_prompt` ve `get_display_visual_prompt` ile "Kapadokya"/"KAPADOKYA" verildiğinde çıktıda "kapadokya" (küçük harf) yok, "Cappadocia" var.  
   - Debug’tan gelen `final_prompt` kullanıldığında da aynı kural geçerli.

**Çalıştırma:**
```bash
cd backend
py -m pytest tests/test_visual_prompt_composer.py -v
```
**Beklenen:** 19 passed (yeni 2 test dahil).

---

## Invariants doğrulama

| İnvariant | Nasıl sağlandı |
|-----------|-----------------|
| UI’da "Kapadokya" yok, yalnızca "Cappadocia" | test-story’de compose; orders’da story_pages = final_prompt; admin’de get_display_visual_prompt. |
| UI’da 2D stil metni (STYLE: …) var | compose_visual_prompt(..., style_text=request.visual_style / preview.visual_style_name). |
| Negative prompt debug/manifest’te | FAL her zaman final_prompt + negative_prompt döndürüyor; prompt_debug_json ve generation_manifest_json’a yazılıyor. |
| UI prompt = prompt_debug_json.final_prompt_after_sanitize | get_display_visual_prompt önce debug’taki final_prompt/final_prompt_after_sanitize’ı kullanıyor; orders/admin bu helper ile dönüyor. |

---

## Özet

- **Root cause:** UI’a giden tüm visual prompt kaynakları compose (normalize + style) pipeline’dan geçmiyordu; FAL’dan dönen composed prompt da çoğu zaman DB’ye yazılmıyor ve UI’da kullanılmıyordu.
- **Fix:** (1) FAL her zaman final_prompt/negative_prompt döndürüyor; (2) test-story response composed; (3) orders background’da story_pages composed ile güncelleniyor; (4) get_display_visual_prompt + admin _story_pages_for_display ile tüm UI çıktısı tek kaynaktan (composed/debug) türetiliyor.
- **Test:** 2 yeni test (style tokens + Kapadokya yok) eklendi; `py -m pytest tests/test_visual_prompt_composer.py -v` → 19 passed.

# Prompt Pipeline Audit – Style Independence & Sızıntı Denetimi

**Amaç:** Kullanıcı hangi stili seçerse seçsin (2D/3D/Default/Ghibli…), Kapadokya senaryosu prompt'u STYLE'dan bağımsız kalmalı; yalnızca scene + kompozisyon + text boşluğu + likeness kuralları içermeli.

---

## 1) Pipeline haritası

### 1.1 `page["visual_prompt"]` nerede oluşuyor?

| Kaynak | Dosya / fonksiyon | Açıklama |
|--------|-------------------|----------|
| **Ana akış (story)** | `gemini_service._compose_visual_prompts()` → `_build_safe_visual_prompt()` | Story cevabındaki `scene_description` + outfit + **clean_style** (tek kaynak) + suffix `" Children's book cover illustration."` / `" Children's book illustration."`. **Style burada gömülüyor** – request.visual_style veya default "children's book illustration" bir kez ekleniyor ve DB/preview’a yazılıyor. |
| **Scenario template (Imagen path)** | `Scenario.get_cover_prompt()` / `get_page_prompt()` | `cover_prompt_template` / `page_prompt_template` içinde `{visual_style}` var; render sırasında style string’i template’e enjekte ediliyor. Sadece `gemini_image_service.generate_image_from_scenario()` bu path’i kullanıyor. |
| **DB / seed** | `alembic/015_seed_full_prompt_templates.py`, `scripts/update_*_scenario.py` | Örnek prompt’lar ve eski template’ler "wide-angle cinematic", "Pixar Disney 3D", "Wide angle f/8", "Children's book illustration" içeriyor. Bunlar DB’deki scenario/prompt örneklerini etkiler; canlı prompt **Gemini çıktısı + _compose_visual_prompts** veya **scenario render** ile oluşur. |

**Sonuç:** `visual_prompt` story oluşturma anında **style ile birlikte** set ediliyor. Sonradan kullanıcı farklı bir stil seçse bile, sayfa prompt’u ilk oluşturulduğundaki stili taşımaya devam ediyor (style-independent değil).

### 1.2 Image çağrısına giden SON prompt nerede kesinleşiyor?

| Path | Son adım | Composer kullanımı |
|------|----------|--------------------|
| **Orders → FAL (PuLID)** | `fal_ai_service.generate_consistent_image()` → `compose_visual_prompt(full_prompt_before_sanitize, ...)` | Evet – validate, normalize, sanitize. |
| **FAL precomposed** | `fal_ai_service._generate_with_precomposed_prompt()` → `compose_visual_prompt()` | Evet. |
| **Gemini Imagen (scenario)** | `gemini_image_service.generate_image_from_scenario()` → `compose_visual_prompt()` | Evet. |
| **Gemini Imagen (generate_image)** | `GeminiImagenService.generate_image_with_template()` → **sadece** `sanitize_visual_prompt()` | **Hayır** – placeholder/cover-inner validate yok. |
| **Gemini Flash** | `GeminiFlashImageService.generate_image()` → **sadece** `sanitize_visual_prompt()` | **Hayır** – placeholder/cover-inner validate yok. |
| **Legacy FAL** | `fal_service.generate_cover()` / `generate_page_image()` / `generate_image()` / `generate_with_pulid()` | **Hayır** – sadece `sanitize_visual_prompt()`. Placeholder/ Kapadokya/ cover-inner tek merkezde değil. |
| **ai.py test** | `test_image_imagen`, `test_image_flash` → **sadece** `sanitize_visual_prompt()` | **Hayır** – composer yok. |

### 1.3 Cover / inner ayrımı – `is_cover` nereden geliyor?

- **orders.py:** `is_cover=(page_num == 0)` (L564, L865).  
- **fal_ai_service:** Aynı `page_number` ile `is_cover` geçiriliyor.  
- **gemini_image_service.generate_image_from_scenario:** `is_cover=(page_index == 0)`.

Cover = page 0, inner = page ≥ 1. Kaynak tutarlı.

### 1.4 Style text / negative nerede ekleniyor?

- **Story tarafı:** `gemini_service._compose_visual_prompts()` içinde `clean_style = _dedupe_style(visual_style or "children's book illustration")` ve `_build_safe_visual_prompt(..., clean_style=clean_style)` – style **visual_prompt string’ine gömülüyor**.  
- **Request:** `visual_style` / `request.visual_style` story oluşturma isteğinde geliyor; sonradan değiştirilmiyor.  
- **FAL tarafı:** `_build_full_prompt(scene_action=prompt, ..., style_modifier=visual_style)` – eğer prompt “full template” sayılmazsa `FluxPromptBuilder.compose_prompt(..., style_config=FluxPromptBuilder.get_style_config(style_modifier))` ile **ikinci kez** style eklenebiliyor (prefix/suffix). Yani hem Gemini çıktısında hem FAL’da style olabilir (double style riski).  
- **Negative:** `compose_visual_prompt` → `negative_suffix = style_negative + strict`; FAL’da `full_negative = NEGATIVE_PROMPT + ", " + negative_suffix`.  
- **Strict negative:** `prompt_sanitizer.STRICT_NEGATIVE_ADDITIONS` – cinematic, big eyes, chibi, kawaii eyes vb. Her zaman ekleniyor (composer kullanılan path’lerde).

### 1.5 Reference image (child_photo_url / PuLID) nerede bağlanıyor?

- **orders.py:** `child_photo_url = request_data.get("child_photo_url") or getattr(preview, "child_photo_url", None)`; yoksa log "PuLID disabled for remaining pages".  
- **fal_ai_service.generate_consistent_image:** `child_face_url` parametresi; doluysa `payload["reference_image_url"] = child_face_url`, model `FLUX_PULID`, manifest’te `"reference_image_used": bool(child_face_url)`.  
- **reference_image_used false:** `child_photo_url` veya `child_face_url` boş/None olduğunda. Tüm sayfalar aynı `child_photo_url` ile çağrılıyor; biri bile yoksa tüm sayfalarda false.

---

## 2) “Hardcode prompt” / style injection denetimi

### 2.1 Terimlerin hangi dosya/path’te eklendiği

| Terim / kavram | Dosya | Path / satır | Not |
|----------------|-------|--------------|-----|
| cinematic, film still, lens, f/8, wide-angle, poster, dramatic contrast, volumetric | `prompt_sanitizer.py` | CINEMATIC_PATTERN, STRICT_NEGATIVE_ADDITIONS | **Strip/negative** – prompt’tan çıkarılıyor veya negative’e ekleniyor; eklenmiyor. |
| pixar, 3d, disney | `fal_ai_service.py` | PIXAR_STYLE (prefix/suffix), get_style_config(), full_template_keywords | StyleConfig ile prompt’a **ekleniyor** (full template değilse). Ayrıca _build_full_prompt “full template” algılarken style eklemiyor ama prompt zaten Gemini’deki style’ı taşıyor. |
| big eyes, kawaii, chibi | `prompt_sanitizer.py` | STRICT_NEGATIVE_ADDITIONS | Sadece **negative**; prompt’a eklenmiyor. |
| Children's book illustration / cover | `gemini_service.py` | _build_safe_visual_prompt() L1245 | **Her visual_prompt’a** suffix olarak ekleniyor. |
| Children's book illustration, text space at bottom, title space at top | `fal_ai_service.py` | FluxPromptBuilder.compose_prompt() L551, L557 | **Short action path**’te (full template değilse) ekleniyor. |
| 2D children's book, Wide angle shot, watercolor/Pixar/Ghibli prefix-suffix | `fal_ai_service.py` | StyleConfig (DEFAULT_STYLE, PIXAR_STYLE, WATERCOLOR_STYLE, ANIME_STYLE…) | Style seçimine göre **prefix/suffix** ekleniyor. |
| Wide cinematic shot, {visual_style}, Book cover illustration | `scripts/update_all_styles_and_scenarios.py` | KAPADOKYA_*_PROMPT, ISTANBUL_*_PROMPT… | Script ile DB scenario template’leri güncelleniyor; **template içinde** style/lens ifadeleri var. |
| wide-angle cinematic, f/8, Pixar Disney 3D, Children's book illustration | `alembic/015_seed_full_prompt_templates.py` | Örnek prompt string’leri | Seed – DB’deki örnekler. |

### 2.2 Style seçimi OFF iken bu terimler prompt’a giriyor mu?

- **“Style OFF”** net tanımlı değil; muhtemelen “default” veya boş style.  
- **Giriyor çünkü:**  
  1. **Gemini path:** `_build_safe_visual_prompt` her zaman `clean_style` ve sabit suffix ekliyor (`" Children's book illustration"` / `" Children's book cover illustration."`). Default `visual_style` = `"children's book illustration"` (ai.py L69). Yani style “kapalı” olsa bile en azından bu metin ekleniyor.  
  2. **Scenario template path:** Template’te `{visual_style}` var; render’da ne verilirse o gidiyor (script/seed’te “Pixar”, “Wide cinematic” vb. geçebilir).  
  3. **FAL short path:** `FluxPromptBuilder.compose_prompt` her zaman bir StyleConfig kullanıyor (en azından DEFAULT_STYLE); içinde “children's book illustration”, “2D”, “Wide angle shot” vb. var.  
- **Kaldırma planı (özet):**  
  - Senaryo prompt’unu **style’dan ayır:** `visual_prompt` veya scenario render çıktısı sadece **scene + kompozisyon + text boşluğu + (isteğe bağlı) likeness kuralları** içersin; “Children's book illustration”, “pixar”, “2D” vb. **style katmanında** (FAL’da, request.visual_style ile) eklenmeli.  
  - Tek stil enjeksiyon noktası: **sadece image API çağrısına yakın** (composer veya FAL _build_full_prompt); story/scenario çıktısına style eklenmemeli veya sadece “neutral” placeholder kalmalı.

### 2.3 Senaryo prompt’unda style’a ait ifadeler

- **Şu an:** `gemini_service._build_safe_visual_prompt` suffix ile `" Children's book illustration"` / `" Children's book cover illustration."` ekliyor; ayrıca `clean_style` (pixar, ghibli, watercolor vb.) aynı string’e ekleniyor.  
- **İstenen:** Bu ifadeler **sadece style katmanından** gelsin; senaryo/scene çıktısı sadece sahne + kompozisyon + text alanı + likeness kuralları içersin.  
- **Yapılacak:** Scene-only çıktı üretmek (suffix ve clean_style’ı story/scenario tarafından eklememek); style’ı sadece image API’ye giden son adımda (composer veya FAL) eklemek.

---

## 3) Placeholder ve lokasyon doğrulama

### 3.1 Placeholder’ların API’ye gitmemesi

- **compose_visual_prompt** (visual_prompt_composer): `validate_no_placeholders()` ile `{scene_description}`, `{child_name}`, `{child_description}` kontrol ediliyor; biri varsa `VisualPromptValidationError` (400).  
- **Kullanmayan path’ler:**  
  - **fal_service.py** (legacy): Sadece sanitize – placeholder validate yok.  
  - **gemini_image_service.generate_image()** (Imagen, template’siz): Sadece sanitize – placeholder validate yok.  
  - **GeminiFlashImageService.generate_image():** Sadece sanitize – placeholder validate yok.  
  - **ai.py test_image_imagen / test_image_flash:** Sadece sanitize – placeholder validate yok.  
- **Sonuç:** Tüm image giriş noktalarında **compose_visual_prompt benzeri tek doğrulama katmanı yok**. Legacy FAL, Imagen doğrudan generate, Flash, ai.py test path’leri placeholder’ı kesmez.

### 3.2 “Kapadokya” → “Cappadocia” normalize

- **prompt_sanitizer.sanitize_visual_prompt:** İlk adımda `re.sub(r"\bKapadokya\b", "Cappadocia", s, flags=re.IGNORECASE)`.  
- **visual_prompt_composer:** `normalize_location()` aynı kuralı uyguluyor; composer’dan geçen tüm prompt’lar normalize.  
- **Kaçak:** Composer/sanitizer’dan **geçmeyen** path’lerde (legacy FAL, Imagen generate_image, Flash, ai.py test) Kapadokya aynen API’ye gidebilir.

---

## 4) Likeness / göz büyümesi (big eyes) problemi

### 4.1 reference_image_used false olan durumlar

- **Koşul:** `child_face_url` / `child_photo_url` boş veya None.  
- **orders.py:** Preview’da `child_photo_url` yoksa veya request’te yoksa log atılıyor, `child_face_url=child_photo_url or ""` ile FAL’a boş gidiyor; manifest’te `reference_image_used: false`.  
- **UI uyarı:** Kodda “reference_image_used false ise UI uyarı” üreten özel bir blok yok; sadece manifest alanı set ediliyor.

### 4.2 “big eyes” drift – mevcut önlemler

- **style_negative / STRICT_NEGATIVE_ADDITIONS** (prompt_sanitizer.py L66–71):  
  `"big eyes, chibi, oversized eyes, kawaii eyes"` **ekli**.  
- **Eksik öneri:** “doll-like face”, “baby proportions” metinde yok; eklenebilir.  
- **style_text:** Fal_ai_service StyleConfig’lerde “big eyes” veya “cute” geçmiyor; tetikleyici yok.  
- **PuLID:** `id_weight` STYLE_PULID_WEIGHTS’tan geliyor (anime/ghibli 0.18, pixar 0.35, realistic 0.50 vb.). `get_pulid_weight_for_style(style_modifier)` ile set ediliyor; referans varsa kullanılıyor.

### 4.3 “Likeness-first” blok metni

- **Şu an:** Composer’da veya FAL prompt’unda “normal child facial proportions, natural-sized eyes” gibi sabit bir blok yok.  
- **İstenen:** Referans varsa bu tür bir ifade eklenebilir; referans yoksa eklenmemeli ama (opsiyonel) uyarı üretilebilir.

---

## 5) Repro / Kanıt (PROMPT_DEBUG_FAL ve generation_manifest)

### 5.1 Nerede loglanıyor?

- **fal_ai_service.generate_consistent_image:**  
  `page_number in (0, 1)` veya `settings.debug` iken **PROMPT_DEBUG** (final_prompt_before, final_prompt_after, negative_prompt_final, is_cover, model).  
  Manifest: `prompt_hash`, `negative_hash`, `reference_image_used` vb. `result[1]["manifest"]` ile orders’a iletilir; `generation_manifest_collector[page_index]` içinde.

### 5.2 Örnek kanıt alanları (1 sipariş, cover + page 1)

- merged_prompt_before_sanitize → **final_prompt_before**  
- final_prompt_after_composer/sanitize (API’ye giden) → **final_prompt_after**  
- negative_prompt_final  
- is_cover, width, height, model, steps, guidance, prompt_hash, negative_hash  
- reference_image_used  

“Kapadokya” veya placeholder kalıyorsa: composer’dan önceki string’de (final_prompt_before) veya composer’ı atlayan bir path’te (legacy/Imagen/Flash/ai.py) kalıyor demektir; çağrı zinciri o path’e göre raporlanmalı.

---

## 6) Çıktı formatı

### (A) Bulgu listesi (RC1..RCn)

| ID | Bulgu | Dosya / satır | Kanıt |
|----|-------|----------------|-------|
| **RC1** | visual_prompt story oluşturulurken style ile gömülüyor; kullanıcı sonradan stil değiştirse bile sayfa prompt’u eski stili taşıyor. | gemini_service.py L1245, L1287–1288, L1376 | _build_safe_visual_prompt(clean_style=..., suffix=" Children's book illustration") |
| **RC2** | FAL “full template” path’inde prompt olduğu gibi kullanılıyor; style zaten Gemini’de. Kısa path’te ise FluxPromptBuilder tekrar style ekliyor → çift style riski. | fal_ai_service.py L1478–1513, L551–557 | compose_prompt(style_config=...) + Gemini’deki style |
| **RC3** | Scenario template’lerde {visual_style} ve script/seed’te “Wide cinematic”, “Pixar”, “f/8” vb. var; senaryo prompt’u style’dan bağımsız değil. | scripts/update_all_styles_and_scenarios.py, scenario model, 015_seed | KAPADOKYA_*_PROMPT, DEFAULT_*_TEMPLATE |
| **RC4** | Legacy FAL, Imagen generate_image, Gemini Flash, ai.py test path’leri compose_visual_prompt kullanmıyor → placeholder/Kapadokya/cover-inner validate yok. | fal_service.py L79, L129, L249, L405, L470; gemini_image_service.py L125, L481; ai.py L1176 | Sadece sanitize_visual_prompt |
| **RC5** | Gemini Imagen generate_image_with_template (template’siz generate_image) ve Flash path’inde placeholder sızıntısı ve Kapadokya normalize eksik. | gemini_image_service.py L108–126, L477–482 | sanitize only |
| **RC6** | reference_image_used false iken UI’da uyarı yok; “likeness-first” blok metni (normal proportions, natural eyes) yok. | orders.py, manifest consumer | Manifest’te alan var, UI’da kullanım yok |
| **RC7** | STRICT_NEGATIVE’da “doll-like face”, “baby proportions” yok. | prompt_sanitizer.py L66–71 | Sadece big eyes, chibi, kawaii eyes |

### (B) Patch planı

| # | Dosya | Değişiklik |
|---|--------|------------|
| 1 | **gemini_service.py** | _build_safe_visual_prompt’tan **clean_style ve sabit “Children's book illustration” suffix’i kaldır**. visual_prompt = sadece scene + outfit + cultural_hint + (opsiyonel) kompozisyon/text alanı. Style’ı burada ekleme. |
| 2 | **fal_ai_service.py** | _build_full_prompt / FluxPromptBuilder: Style’ı **tek kaynak** yap. Full template path’te bile son adımda request.visual_style’a göre style ekle (veya composer’a style_text ver). Böylece senaryo çıktısı style içermese bile FAL tarafında stil uygulanır. |
| 3 | **Scenario template / seed** | cover/page_prompt_template’ten {visual_style}’ı çıkar veya “neutral” placeholder yap; script/seed’teki “Wide cinematic”, “f/8”, “Pixar” vb. kaldır. Senaryo metni sadece scene + kompozisyon + text alanı. |
| 4 | **fal_service.py** | Tüm prompt kullanılan yerlere **compose_visual_prompt** (veya en azından validate_no_placeholders + normalize_location) ekle; 400 dön veya log. |
| 5 | **gemini_image_service.py** | generate_image (Imagen) ve GeminiFlashImageService.generate_image: API’ye göndermeden önce **compose_visual_prompt** ile geçir (template_vars=None); böylece placeholder/Kapadokya/cover-inner validate uygulanır. |
| 6 | **ai.py** | test_image_imagen, test_image_flash: Aynı şekilde **compose_visual_prompt** kullan veya placeholder/ Kapadokya kontrolü ekle. |
| 7 | **prompt_sanitizer.py** | STRICT_NEGATIVE_ADDITIONS’a “doll-like face, baby proportions” ekle (big eyes drift’i azaltmak için). |
| 8 | **visual_prompt_composer** | (Opsiyonel) Referans varsa “normal child facial proportions, natural-sized eyes” benzeri likeness blok’u style_text veya ayrı parametre ile ekleme seçeneği; referans yoksa ekleme, uyarı log’la. |
| 9 | **Frontend / manifest** | reference_image_used false ise UI’da uyarı göster (örn. “Yüz referansı yok; benzerlik sınırlı olabilir”). |

### (C) Yeni testler

| Test | Açıklama |
|------|----------|
| **Placeholder sızıntısı** | API’ye giden prompt’ta `{scene_description}`, `{child_name}`, `{child_description}` olmamalı; varsa assert/400. (Mevcut: test_visual_prompt_composer placeholder testleri.) |
| **Senaryo prompt’unda style token yasak** | Composer’a giren “senaryo çıktısı” (scene-only) string’inde "pixar", "Children's book illustration", "2D", "ghibli" vb. olmamalı – ya da bu test sadece “scene-only üretildi” kontratını doğrular (gemini_service patch sonrası). |
| **reference_image_used false ise uyarı** | (UI test veya API contract) Manifest’te reference_image_used=false döndüğünde response’ta uyarı flag’i veya mesajı beklenebilir. |
| **Kapadokya → Cappadocia** | Final prompt’ta “Kapadokya” yok, “Cappadocia” var. (Mevcut: test_visual_prompt_composer normalize testleri.) |

### (D) Done checklist (pytest dahil)

- [ ] gemini_service: visual_prompt’tan style ve sabit suffix kaldırıldı.  
- [ ] fal_ai_service: Style tek noktada (composer veya _build_full_prompt sonrası) uygulanıyor.  
- [ ] Scenario/seed: Template ve script’lerde style/cinematic ifadeleri kaldırıldı veya nötrleştirildi.  
- [ ] fal_service: Tüm image path’leri compose_visual_prompt (veya validate+normalize) kullanıyor.  
- [ ] gemini_image_service: Imagen ve Flash path’leri compose_visual_prompt kullanıyor.  
- [ ] ai.py: Test image endpoint’leri compose veya en azından placeholder/Kapadokya kontrolü yapıyor.  
- [ ] STRICT_NEGATIVE’a “doll-like face, baby proportions” eklendi.  
- [ ] `py -m pytest tests/test_visual_prompt_composer.py -v` geçiyor.  
- [ ] Yeni test: Senaryo çıktısında style token yok (patch sonrası).  
- [ ] Yeni test veya UI: reference_image_used false → uyarı.  
- [ ] 1 sipariş (cover + page 1) PROMPT_DEBUG + manifest ile koşturuldu; final_prompt_before/after, negative, reference_image_used, Kapadokya/placeholder yok raporlandı.

---

*Bu rapor pipeline’ı baştan sona denetleyerek style bağımsızlığı, placeholder/lokasyon doğrulama ve likeness/big-eyes önlemlerini özetler; patch ve testler bu bulgulara göre uygulanabilir.*

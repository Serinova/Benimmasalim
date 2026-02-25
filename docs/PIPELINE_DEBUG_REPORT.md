# Prompt Pipeline Debug Report – Stil Sapması Kök Nedenleri ve Kanıtlar

**Amaç:** Kullanıcı doğru görsel prompt yazsa bile çıktının neden stilden saptığını (2D→3D/Pixar, büyük gözler, sinematik hava, Kapadokya kuralı) kanıtlarla tespit etmek ve kalıcı fix planı üretmek.

---

## 1) Root Cause Listesi (Önem Sırasına Göre) + Kanıt

### RC1 – Sanitizer "wide angle"ı kompozisyon bağlamında da siliyor (2D/Pixar stil bozulması)
- **Kanıt:** `prompt_sanitizer.py` L22–23: `r"\bwide-angle\b"`, `r"\bwide angle\b"` CINEMATIC_LENS_TERMS içinde. `fal_ai_service.py` L121 (PAGE_QUALITY), L266 (PIXAR_STYLE): "Wide angle shot, full body visible" kullanılıyor. Sanitize sonrası "wide angle" silinince "Wide  shot" veya " shot" kalıyor → kompozisyon niyeti kayboluyor.
- **Log/DB:** PROMPT_DEBUG_FAL `merged_prompt_after_sanitize` içinde "Wide angle" yerine boşluk/kelime kaybı görülebilir.
- **Öneri:** Sadece sinematik **tam ifadeleri** sil (örn. "wide-angle cinematic shot", "wide angle cinematic shot"). Tek başına "wide angle"ı listeden çıkar; tireli "wide-angle" kalabilir (sinematik çağrışım).

### RC2 – Kapadokya görsel prompt’ta; kural "ONLY Cappadocia"
- **Kanıt:** `gemini_service.py` L1318–1319: `scenario_theme = "cappadocia"` Kapadokya senaryosu için set ediliyor. `_build_safe_visual_prompt` (L1243–1250) `scene_desc`’i olduğu gibi kullanıyor; Gemini bazen "Kapadokya" (Türkçe) üretebiliyor. `fal_ai_service.py` L1154: `has_cappadocia="cappadocia" in prompt.lower() or "kapadokya" in prompt.lower()` – yani prompt’ta "Kapadokya" da geçebiliyor. Görsel model için İngilizce "Cappadocia" tercih edilmeli.
- **Kanıt:** `ai.py` L786–789: CAPPADOCIA_IN_ISTANBUL / ISTANBUL_IN_CAPPADOCIA contamination kontrolleri var; lokasyon kuralı biliniyor.
- **Öneri:** Görsel prompt API’ye gitmeden önce **tek kaynaktan** normalizasyon: "Kapadokya" → "Cappadocia" (görsel prompt için).

### RC3 – DB/seed ve senaryo şablonlarında sinematik ifadeler (sanitizer’a kadar taşınıyor)
- **Kanıt:** `docs/ROOT_CAUSE_AND_FIX.md` L13–14: `update_kapadokya_scenario.py`, `015_seed_full_prompt_templates.py`, `fix_scenarios.py` içinde "Wide cinematic shot", "Epic wide shot", "standing heroically", "god rays" geçiyor. `update_kapadokya_scenario.py` L34: "standing heroically on a rocky outcrop". Bu metinler senaryo/şablon olarak DB’de; Gemini çıktısı veya template birleşimiyle `visual_prompt`’a giriyor.
- **Kanıt:** Sanitizer (L16–54) bu terimleri **son adımda** siliyor; yani API’ye gitmeden önce temizleniyor. Sorun: sanitizer’dan **önce** birleşen prompt çok sinematik olabiliyor; "wide angle" gibi kompozisyon kelimeleri de yanlışlıkla siliniyor (RC1).
- **Öneri:** Seed/script’leri 2D-friendly ifadelerle güncellemek (uzun vadeli). Kısa vadede sanitizer doğru çalışsın (RC1 fix).

### RC4 – Style injection noktaları (çift stil / yanlış prefix)
- **Kanıt:** `fal_ai_service.py` L1481–1514: `_build_full_prompt` "full template" tespit ederse prompt’u **olduğu gibi** döndürüyor; prefix eklemiyor. "FULL TEMPLATE DETECTED" log’u var. Template değilse `FluxPromptBuilder.compose_prompt` çağrılıyor (L1511–1516) → prefix/suffix ekleniyor. Yani stil enjeksiyonu: (1) Gemini `_build_safe_visual_prompt` içinde `clean_style` + "Children's book cover illustration." / "Children's book illustration." (gemini_service L1244–1245), (2) FAL tarafında sadece "short action" path’te FluxPromptBuilder prefix/suffix.
- **Kanıt:** `gemini_service.py` L1244: `suffix = " Children's book cover illustration." if is_cover else " Children's book illustration."` – cover/inner ayrımı doğru. Sanitizer inner’da "Children's book cover" / "book cover illustration" siliyor (L58–61).
- **Sonuç:** Style injection tek kaynak değil; Gemini’de bir kez, FAL’da sadece kısa prompt path’inde. Çift stil riski "full template" path’te yok (doğrudan kullanılıyor).

### RC5 – "Big eyes" / chibi için negatif eksik
- **Kanıt:** `prompt_sanitizer.py` STRICT_NEGATIVE_ADDITIONS (L64–69): "text, watermark, typographic" var; "big eyes", "chibi", "oversized eyes", "kawaii" yok. `fal_ai_service.py` ANTI_REALISTIC_NEGATIVE / ANTI_ANIME_NEGATIVE (L176–191) stil bazlı; 2D çocuk kitabı için ortak "no big eyes" yok.
- **Kanıt:** Script’lerde "facial proportions" geçiyor (`create_istanbul_scenario.py` L75, `update_visual_styles.py` L46) ama görsel prompt’a zorunlu negatif olarak eklenmiyor.
- **Öneri:** Style registry / ortak negatif listesine 2D için "big eyes, chibi, oversized eyes, kawaii eyes" eklenebilir.

### RC6 – Cache / CDN / GCS / Admin UI
- **Kanıt:** `docs/THIRD_PASS_AUDIT_OUTPUT_FIDELITY.md`: Admin, `page_images`’ı DB’den okuyor; cache-bust `?v=prompt_hash` veya `?v=updated_at` eklendi. Aynı GCS path overwrite edilirse CDN/browser eski görseli gösterebilir; cache-bust bu riski azaltıyor.
- **Kanıt:** `admin/orders.py` `_page_images_with_cache_bust` (L38–57): URL’lere `?v=` veya `&v=` ekleniyor.
- **Sonuç:** Cache etkisi var; mevcut cache-bust ile azaltılmış durumda.

### RC7 – Legacy fal_service ve is_cover
- **Kanıt:** `fal_service.py` L79–80 (generate_cover): `sanitize_visual_prompt(full_prompt, is_cover=True)`. L129–130 (generate_cover_from_mm): aynı. L249–250, L405–406, L470–471: inner path’lerde `is_cover=False`. Yani legacy servis sanitizer kullanıyor ve is_cover doğru.
- **Sonuç:** Legacy bypass yok; is_cover tutarlı.

---

## 2) API’ye Giden Son Prompt – Debug Çıktısı Şeması

Aşağıdaki alanlar **tek bir debug çıktısında** (log veya `prompt_debug_json` / manifest) yer almalı:

| Alan | Kaynak | Örnek |
|------|--------|--------|
| merged_prompt_before_sanitize | fal_ai_service L817–822, L858 | Gemini + style birleşimi; "wide angle" dahil |
| merged_prompt_after_sanitize | L825, L860 | Banned strip sonrası; 2D-safe |
| negative_prompt_final | L827, L863, L878 | NEGATIVE_PROMPT + STRICT_NEGATIVE_ADDITIONS (+ gender/style negatives) |
| is_cover | Caller (orders: page_num==0) | true / false |
| page_index | orders L564, fal L848 | 0, 1, 2, ... |
| width, height | orders L555 (get_page_image_dimensions) | 768, 1024 (cover) / 1024, 768 (inner) |
| num_inference_steps, guidance_scale | fal_ai_service generation_config | 28, 3.5 |
| seed | generation_config.seed | null veya sabit |
| model/provider | FalModel.FLUX_PULID / FLUX_DEV | fal-ai/flux-pulid |
| reference_image_used | child_face_url bool | true / false |

**Mevcut log:** `fal_ai_service.py` L854–870 (PROMPT_DEBUG_FAL, page_number==1 veya settings.debug). `generation_manifest_json` (DB): provider, model, steps, guidance, width, height, is_cover, prompt_hash, negative_hash, reference_image_used.

---

## 3) Style Injection Nerede Oluyor?

| Katman | Dosya / Yer | Ne ekleniyor? |
|--------|-------------|----------------|
| Frontend | create flow | visual_style, scene_description, child bilgisi; doğrudan prompt metni yazmıyor. |
| Backend compose | gemini_service._build_safe_visual_prompt | scene_desc + outfit + cultural_hint + clean_style + suffix ("Children's book cover illustration." / "Children's book illustration."). |
| DB template | Scenario cover_prompt_template, page_prompt_template | Senaryo bazlı; Gemini’ye girdi, çıktı visual_prompt’a _compose_visual_prompts ile taşınıyor (template doğrudan FAL’a gitmiyor). |
| Provider (FAL) | fal_ai_service._build_full_prompt | Sadece "short action" path’te: FluxPromptBuilder.compose_prompt → style prefix/suffix (StyleConfig). "Full template" path’te ekleme yok. |
| Sanitizer sonrası | Yok | Sanitize’dan sonra prompt’a ekleme yapılmıyor; payload doğrudan FAL’a gidiyor. |
| Legacy | fal_service | "High quality, detailed." + sanitize; style zaten prompt’ta kabul ediliyor. |

**Özet:** Style injection Gemini’de (clean_style + suffix) ve FAL’da yalnızca kısa prompt path’inde (FluxPromptBuilder). Sanitizer sonrası ekleme yok; legacy bypass yok.

---

## 4) Cache / CDN / GCS / Admin UI – Kanıt

- **Admin UI:** `page_images` API’den geliyor; `_page_images_with_cache_bust` ile URL’lere `?v=prompt_hash` veya `?v=updated_at` ekleniyor → aynı path overwrite’da bile yeni içerik istenebilir.
- **GCS overwrite:** Aynı object path (örn. `stories/{id}/page_0.png`) tekrar yazılırsa URL aynı kalır; cache-bust olmadan CDN/browser eski görseli dönebilir. Cache-bust eklendi.
- **Confirm sonrası:** process_preview_background / process_remaining_pages → page_images commit → status PENDING/CONFIRMED; bir sonraki admin isteğinde güncel page_images + cache-bust’lı URL’ler dönüyor.

---

## 5) 2D/3D Stil – Tek Kaynak Tasarım Önerisi (Style Registry)

**Fikir:** Pozitif ve negatif kuralları tek modülde topla; hem sanitizer hem negatif prompt hem lokasyon kuralı buradan beslenir.

- **Dosya:** `backend/app/core/style_registry.py` (veya `prompt_sanitizer.py` genişletilir).
- **İçerik taslağı:**
  - **Banned terms (sanitizer):** Sinematik/lens terimleri (mevcut CINEMATIC_LENS_TERMS); "wide angle" sadece tam ifade içinde (örn. "wide angle cinematic shot") silinsin; kompozisyon "Wide angle shot" kalsın.
  - **Inner-page strip:** "Children's book cover", "book cover illustration" (is_cover=False).
  - **STRICT_NEGATIVE_ADDITIONS:** Metin/watermark/typographic + isteğe bağlı 2D için "big eyes, chibi, oversized eyes, kawaii eyes".
  - **Location normalizer:** Görsel prompt için "Kapadokya" → "Cappadocia" (tek geçiş).
  - **Style-specific negatives:** Mevcut get_style_specific_negative (anime vs realistic) registry’den okunabilir.

**Kullanım:** Sanitizer ve FAL negatif birleştirme bu listeleri kullanır; yeni kural tek yerde eklenir.

---

## 6) Fix’ler – Uygulama Planı

### Fix 1 – Sanitizer: "wide angle" sadece sinematik ifadelerde silinsin
- **Dosya:** `backend/app/core/prompt_sanitizer.py`
- **Değişiklik:** `r"\bwide angle\b"` CINEMATIC_LENS_TERMS’ten çıkar. "wide-angle" (tireli) kalır. Böylece "Wide angle shot, full body visible" korunur; "wide angle cinematic shot" tam ifade pattern’i ile silinmeye devam eder.

### Fix 2 – Kapadokya → Cappadocia normalizasyonu
- **Dosya:** `backend/app/core/prompt_sanitizer.py` veya `fal_ai_service.py`
- **Değişiklik:** Sanitize’dan hemen önce (veya sanitizer içinde) görsel prompt’ta "Kapadokya" → "Cappadocia" tek geçiş (replace, case-insensitive: "Kapadokya" / "KAPADOKYA" → "Cappadocia"). Böylece görsel model için lokasyon kuralı (ONLY Cappadocia) korunur.

### Fix 3 – 2D için "no big eyes" negatif (opsiyonel)
- **Dosya:** `backend/app/core/prompt_sanitizer.py` STRICT_NEGATIVE_ADDITIONS veya style_registry
- **Değişiklik:** 2D çocuk kitabı için ortak negatif: "big eyes, chibi, oversized eyes, kawaii eyes" eklenir (isteğe bağlı; önce RC1/RC2 doğrulanır).

### Fix 4 – Regression test
- Sanitizer: "Wide angle shot, full body visible" girdisi → çıktıda "Wide angle shot" veya "Wide shot" kalmalı; "wide angle" tamamen silinmemeli (sadece "wide angle cinematic" gibi ifadeler silinmeli).
- Kapadokya: "Kapadokya vadisi" → normalize sonrası "Cappadocia vadisi" (veya en azından "Cappadocia" geçmeli).
- Mevcut testler: test_sanitize_removes_all_banned_tokens_inner, test_sanitize_removes_cover_tags_on_inner, test_sanitize_allows_cover_wording_on_cover korunur.

### Doğrulama checklist
- [ ] Cover (page 0): is_cover=true, 768×1024, "Children's book cover" sanitize’da silinmıyor.
- [ ] Inner (page ≥1): is_cover=false, 1024×768, "Children's book cover" / "book cover illustration" sanitize’da siliniyor.
- [ ] "Wide angle shot" (kompozisyon) prompt’ta kalıyor; "wide angle cinematic shot" gidiyor.
- [ ] Kapadokya senaryosunda görsel prompt’ta "Cappadocia" kullanılıyor (Kapadokya geçiyorsa normalize edilmiş).
- [ ] PROMPT_DEBUG_FAL / generation_manifest_json: merged_prompt_before/after_sanitize, negative_prompt_final, is_cover, width, height, model, reference_image_used dolu.
- [ ] Admin’de cache-bust’lı URL’ler dönüyor; aynı preview yeniden üretilince güncel görsel görünüyor.

---

## 7) Prompt Pipeline Haritası (Özet)

```
Frontend (visual_style, story_pages[].visual_prompt, child_photo_url)
  → orders.py: process_preview_background / process_remaining_pages
  → fal_ai_service.generate_consistent_image(prompt=page["visual_prompt"], style_modifier=visual_style, is_cover=(page_num==0), ...)
  → truncate_safe_2d if len>1200
  → _build_full_prompt(scene_action=prompt, ...)
       → full template keywords? → return prompt AS-IS
       → else FluxPromptBuilder.compose_prompt(...)  [prefix/suffix]
  → [FIX: Kapadokya→Cappadocia normalize]
  → sanitize_visual_prompt(full_prompt, is_cover=is_cover)  [FIX: wide angle sadece sinematik ifadede]
  → full_negative = NEGATIVE_PROMPT + STRICT_NEGATIVE_ADDITIONS
  → payload = { prompt, negative_prompt, image_size, ... }; reference_image_url if child_face_url
  → _generate_with_queue / _generate_direct
```

**DB:** Scenario (cover_prompt_template, page_prompt_template) → Gemini’ye girdi. Görsel çıktı `story_pages[].visual_prompt`; FAL’a bu değer gidiyor (template doğrudan FAL’a yazılmıyor).

**Provider farkları:** fal_ai_service (Flux PuLID/dev) sanitizer + manifest; gemini_image_service sanitizer kullanıyor; fal_service (legacy) sanitizer + is_cover kullanıyor.

---

## 8) Minimum Repro ve Manifest

- Aynı `visual_prompt` + aynı style ile FAL’da cover + page 1 üret; generation_manifest_json’da her sayfa için: provider, model, steps, guidance, width, height, is_cover, prompt_hash, negative_hash, reference_image_used karşılaştır.
- Cover: is_cover=true, 768×1024; page 1: is_cover=false, 1024×768; model ve reference aynı olmalı.
- prompt_debug_json (settings.debug) ile merged_prompt_before_sanitize / merged_prompt_after_sanitize / negative_prompt_final kontrol edilir.

---

## 9) Fix Branch Planı (Dosya Listesi + Patch Özeti)

| Dosya | Patch özeti |
|-------|--------------|
| `backend/app/core/prompt_sanitizer.py` | (1) CINEMATIC_LENS_TERMS’ten `r"\bwide angle\b"` kaldırıldı; "Wide angle shot" kompozisyonu korunuyor. (2) Sanitize başında Kapadokya→Cappadocia normalizasyonu (re.sub). (3) STRICT_NEGATIVE_ADDITIONS’a "big eyes, chibi, oversized eyes, kawaii eyes" eklendi. |
| `backend/tests/test_prompt_sanitizer.py` | test_wide_angle_composition_preserved: "Wide angle shot" çıktıda kalmalı. test_kapadokya_normalized_to_cappadocia: "Kapadokya" → "Cappadocia". |

**Komutlar:**
```bash
cd backend
py -m pytest tests/test_prompt_sanitizer.py -v
py -m pytest tests/test_image_dimensions.py tests/test_preview_detail_response.py -v
```

---

## 10) Doğrulama Checklist (Nasıl Doğrulanır)

- [ ] **Cover:** page_index=0, is_cover=true, 768×1024; "Children's book cover" sanitize’da silinmiyor (is_cover=True).
- [ ] **Inner:** page_index≥1, is_cover=false, 1024×768; "Children's book cover" / "book cover illustration" sanitize’da siliniyor.
- [ ] **Kompozisyon:** "Wide angle shot, full body visible" içeren prompt sanitize sonrası "wide angle" veya "Wide angle" içermeli.
- [ ] **Sinematik:** "wide angle cinematic shot", "cinematic", "f/8", "heroically" sanitize sonrası çıkmamalı.
- [ ] **Kapadokya kuralı:** Görsel prompt’ta "Kapadokya" geçiyorsa çıktıda "Cappadocia" olmalı; "kapadokya" kalmamalı.
- [ ] **Debug çıktısı:** PROMPT_DEBUG_FAL (page 1 veya settings.debug) merged_prompt_before_sanitize, merged_prompt_after_sanitize, negative_prompt_final, is_cover, width, height, model, reference_image_used log’da görünmeli.
- [ ] **Manifest:** generation_manifest_json’da provider, model, steps, guidance, width, height, is_cover, prompt_hash, negative_hash, reference_image_used dolu olmalı.
- [ ] **Cache:** Admin’de page_images URL’leri ?v= veya &v= içermeli; aynı preview yeniden üretilince güncel görsel görünmeli.
- [ ] **Regression:** `pytest tests/test_prompt_sanitizer.py tests/test_image_dimensions.py tests/test_preview_detail_response.py -v` → tümü geçmeli.

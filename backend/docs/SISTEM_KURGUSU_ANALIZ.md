# Sistem Kurgusu Analizi — Eksikler ve Tutarsızlıklar

## Özet

- **Doğru kurgulanan:** Hikaye akışı (PASS-1 → PASS-2), stil/stil bloğu ayrımı, sahne/stil ayrımı, negative prompt birleştirme, lokasyon (Cappadocia), PuLID/id_weight.
- **Tutarsızlık:** Görsel prompt şablonu (kapak/iç sayfa) için **üç farklı kaynak** kullanılıyor; tek kaynak yok.
- **Eksik / dikkat edilmesi gereken:** Senaryo şablonları kullanılmıyor, custom_inputs_schema görsel tarafa taşınmıyor, _compose_visual_prompts DB/şablon servisine bağlı değil.

---

## 1. Görsel şablon (template) — tutarsızlık

Aynı iş (kapak/iç sayfa görsel promptu) için üç farklı kaynak var:

| Kaynak | Nerede kullanılıyor | Açıklama |
|--------|----------------------|----------|
| **Scenario.cover_prompt_template / page_prompt_template** | Sadece `gemini_image_service.py` (get_cover_prompt / get_page_prompt) | Senaryoya göre farklı şablon tanımlanabilir; ana akışta kullanılmıyor. |
| **PromptTemplate tablosu** (COVER_TEMPLATE, INNER_TEMPLATE) | `generate_book.py`, `orders.py`, `ai.py` (preview) | Admin panelden tek global şablon; kitap üretim ve önizlemede kullanılıyor. |
| **Constants** (DEFAULT_COVER_TEMPLATE_EN, DEFAULT_INNER_TEMPLATE_EN) | **GeminiService._compose_visual_prompts** | Kod içi sabit; V2 hikaye + görsel akışında **sadece bunlar** kullanılıyor. |

Sonuç:

- **V2 akış (Gemini → görsel):** Şablon her zaman constants’tan geliyor. DB’deki COVER_TEMPLATE / INNER_TEMPLATE ve Scenario’daki cover/page_prompt_template **hiç kullanılmıyor**.
- **generate_book / orders:** DB’deki COVER/INNER kullanılıyor; Scenario şablonları yok.
- Senaryo bazlı “Kapadokya’ya özel şablon” tasarlanmış olsa bile, şu an **tek bir yerde bile** scenario şablonu kullanılmıyor (gemini_image_service ayrı/legacy bir servis).

Öneri:

- **Tek kaynak:** Ya tüm akışlar PromptTemplate tablosuna (COVER_TEMPLATE, INNER_TEMPLATE) bağlansın, ya da senaryo şablonları kullanılacaksa _compose_visual_prompts ve generate_book/orders senaryodan veya senaryo+DB hybrid’den okusun.
- **GeminiService._compose_visual_prompts:** En azından PromptTemplateService ile DB’den COVER/INNER okuması mantıklı; böylece admin panelden yapılan şablon değişikliği V2 akışına da yansır.

---

## 2. Senaryo (Scenario) — kullanılmayan alanlar

- **cover_prompt_template / page_prompt_template:** Yukarıdaki nedenle ana akışta kullanılmıyor. Sadece `GeminiImageService` kullanılıyorsa orada geçerli.
- **custom_inputs_schema:** Hikaye tarafında (custom_variables) kullanılıyor olabilir; görsel prompt compose’da `custom_variables` şablonlara enjekte edilmiyor. Yani senaryoya özel alanlar (örn. “gemi adı”) görsel metne taşınmıyorsa eksik kalır.
- **theme_key:** Kodda theme_key’e göre özel mantık (kıyafet/arka plan) yok; sadece scenario name’e göre (kapadokya, istanbul, uzay, deniz) theme çıkarılıyor. theme_key tutulup ileride kullanılabilir.

Öneri:

- Görsel şablonu senaryodan kullanmayacaksak: Scenario’daki cover/page_prompt_template’i “legacy/deprecated” diye işaretleyip dokümante etmek veya kaldırmak.
- Kullanacaksak: _compose_visual_prompts ve ilgili yerlerde scenario’dan template alınmalı; aksi halde senaryo şablonları anlamsız kalır.

---

## 3. Eksik veya zayıf noktalar

- **compose_visual_prompt’a custom_variables geçmemesi:** Senaryodaki custom_inputs_schema ile doldurulan alanlar (gemi adı, hayvan adı vb.) görsel prompt şablonunda `{spaceship_name}` gibi değişkenler varsa, compose’a bu dict verilmiyor; şablonlar da büyük ihtimalle sadece scene_description + clothing_description kullanıyor. Bu bilinçli tasarım olabilir (görselde sadece sahne+kıyafet); yoksa custom değişkenleri compose’a taşımak gerekir.
- **GeminiService’te DB session:** _compose_visual_prompts içinde PromptTemplateService kullanılmıyor; `self._db` var ama template almak için kullanılmıyor. DB’den şablon alınacaksa burada get_template_en çağrısı eklenmeli.
- **location_en eklemesi:** _compose_visual_prompts’ta `location_en` sahne metninin başına ekleniyor (“Cappadocia setting. …”). Bu iyi; senaryodan geliyor.

---

## 4. Doğru kurgulanan parçalar

- **Hikaye → sahne → görsel ayrımı:** Hikaye metni (PASS-1), sahne açıklamaları (PASS-2), görsel prompt (compose_visual_prompt) net ayrılmış; sahne = hikayeden, stil = stillerden.
- **Stil bloğu:** StyleConfig + style_block, DB’deki sahne/karakter sızıntısının temizlenmesi, watercolor/ghibli/pixar tutarlı.
- **Negative prompt:** build_negative_prompt, stil bazlı çıkarımlar (anime/3D), base + strict + style_negative birleşimi tutarlı.
- **Lokasyon:** location_constraints ve location_en senaryodan Gemini ve görsele taşınıyor; Kapadokya/Cappadocia normalizasyonu var.
- **PuLID / id_weight:** Stil bazlı ağırlık, LIKENESS_HINT ile yüz tutarlılığı kurgusu doğru.

---

## 5. Yapılacaklar (öneri sırasıyla)

1. **Tek şablon kaynağı:** GeminiService._compose_visual_prompts içinde template’i constants yerine PromptTemplateService.get_template_en(db, "COVER_TEMPLATE" / "INNER_TEMPLATE", default) ile al; böylece V2 akışı da admin paneldeki şablonlarla çalışır.
2. **Senaryo şablonları:** Senaryoya özel görsel şablon istenmiyorsa Scenario.cover/page_prompt_template’i dokümante et veya deprecated yap; isteniyorsa _compose_visual_prompts (ve gerekirse generate_book) senaryodan template okusun.
3. **Custom değişkenler:** Görsel prompt’ta senaryoya özel değişken (gemi adı vb.) kullanılacaksa compose_visual_prompt’a custom_variables eklenip şablonda kullanılmalı; kullanılmayacaksa mevcut durum bilinçli bırakılabilir.

Bu doküman sistem kurgusunun doğru olup olmadığını ve nerede eksik/tutarsız kaldığını özetler; isteğe göre kod tarafında tek şablon kaynağı ve senaryo kullanımı netleştirilir.

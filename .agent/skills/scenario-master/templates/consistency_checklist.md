# 🛡️ 7 Katmanlı Tutarlılık Kontrol Listesi

> Her senaryoyu production'a almadan önce bu 7 kontrolün TAMAMINI geç.

---

## 1. 👗 Kıyafet Kilidi

```
□ outfit_girl dolu ve İngilizce
□ outfit_boy dolu ve İngilizce
□ "EXACTLY same outfit on every page" metni var
□ Senaryo temasıyla uyumlu (uzay=astronot, deniz=dalış, tarih=dönem kıyafeti)
□ Detaylı (sadece "red dress" değil, "a flowing burgundy adventure dress with golden trim trim, brown leather boots" gibi)
□ Kıyafet story_prompt_tr'de referans edilmiş: "{clothing_description}" placeholder
```

**Pipeline bağlantısı:** `generate_book.py:_resolve_scenario_outfit()` → `BookContext.clothing_description` → `page_builder.py` outfit lock

---

## 2. 🦊 Companion CAST LOCK

```
□ custom_inputs_schema'da "animal_friend" key var
□ default alanı dolu (ör: "Cesur Yılkı Atı")
□ options LİSTE formatında: [{"label": "...", "value": "..."}]
□ ⛔ options'ta "[object Object]" YOK
□ Default değer _COMPANION_MAP sözlüğünde var
  ├── generate_book.py → _COMPANION_MAP
  └── _story_blueprint.py → _TR_TO_EN
□ story_prompt_tr'de companion'a referans var
□ G2-a kartı doldurulmuş (species, appearance_en, appearance_tr)
□ scenario_bible'da companion bilgisi var
```

**Pipeline bağlantısı:**
- `_story_blueprint.py:_resolve_companion_placeholder()` → `{animal_friend}` replace
- `generate_book.py:_extract_companion_from_pages()` → BookContext companion
- `page_builder.py:build_page_prompt()` → CAST LOCK ("EXACTLY two characters")

---

## 3. 🗝️ Önemli Obje Tutarlılığı

```
□ Story'de tekrarlayan önemli objeler tespit edilmiş
□ Her obje için G2-b kartı doldurulmuş
□ story_prompt_tr'de obje ANCHOR cümlesi var
□ image_prompt_en'e "holding/wearing [obje tanımı]" suffix eklenir
□ Obje ilk göründüğü sayfa ve son göründüğü sayfa belirli
```

**Pipeline bağlantısı:** Obje bilgisi `scenario_bible`'da saklanır, `blueprint_prompt.py` tarafından blueprint'e aktarılır.

---

## 4. 💇 Saç Tutarlılığı

```
□ PuLID fotoğraf varsa → face analyzer otomatik saç tanımı üretir ✅
□ PuLID yoksa → hair_description alanı kontrol et
□ PAGE_GENERATION_SYSTEM_PROMPT'ta saç uydurma yasağı var ✅
□ CHARACTER IDENTITY LOCK aktif (character_description doluysa)
□ Saç tanımı story_prompt_tr'de YASAK (AI prompt'a karışmasın)
```

**Pipeline bağlantısı:**
- `generate_book.py` → hair_description → `BookContext.hair_description`
- `page_builder.py:build_page_prompt()` → CHARACTER IDENTITY LOCK (satır 155-162)
- `_story_writer.py:_visual_prompt_enhancement()` → CharacterBible.hair_style

---

## 5. 🏛️ Mekan Sürekliliği

```
□ location_en İngilizce ve kısa
□ location_constraints dolu (iç/dış mekan elementleri)
□ story_prompt_tr'de mekan referansları var
□ page_prompt_template'de mekan placeholder var
□ G3 görsel akış haritası doldurulmuş
□ cover_prompt_template mekanı içeriyor
```

**Pipeline bağlantısı:**
- `_story_blueprint.py` → location_key → `build_blueprint_task_prompt()`
- `prompt_engine/__init__.py:build_page_task_prompt()` → `{location_display_name}` her sayfaya eklenir
- QA checks → `location_contamination` kontrolü

---

## 6. 🔒 Placeholder Çözümleme

```
□ {child_name} → pipeline otomatik ✅
□ {clothing_description} → pipeline otomatik ✅
□ {animal_friend} → _resolve_companion_placeholder() ✅ (default lazım)
□ {animal_friend_en} → _resolve_companion_placeholder() ✅ (_TR_TO_EN lazım)
□ Başka placeholder yok (ör: {guide}, {rehber} → pipeline tarafından çözülmez!)
□ Tüm placeholder'lar test edilmiş
```

---

## 7. ⛔ İçerik Güvenliği

```
□ Dini ritüel/ibadet sahnesi yok (Umre istisna)
□ Siyasi mesaj/güncel çatışma yok
□ Korku/şiddet ağırlıklı değil
□ Uygunsuz kıyafet yok (mini etek, kısa şort, karın açık)
□ no_family senaryolarda anne/baba/kardeş referansı yok
□ image_prompt_en'de ten/saç/göz rengi uydurma yok
□ flags objesi doğru set edilmiş (no_family: true/false)
```

---

## 📊 SONUÇ TABLOSU

| # | Kontrol | Durum | Not |
|---|---------|-------|-----|
| 1 | Kıyafet kilidi | □ ✅ / □ ❌ | |
| 2 | Companion CAST LOCK | □ ✅ / □ ❌ | |
| 3 | Obje tutarlılığı | □ ✅ / □ ❌ / □ N/A | |
| 4 | Saç tutarlılığı | □ ✅ / □ ❌ | |
| 5 | Mekan sürekliliği | □ ✅ / □ ❌ | |
| 6 | Placeholder çözümleme | □ ✅ / □ ❌ | |
| 7 | İçerik güvenliği | □ ✅ / □ ❌ | |

**Geçme koşulu: 7/7 ✅ — Tek bir ❌ bile üretimde sorun yaratır.**

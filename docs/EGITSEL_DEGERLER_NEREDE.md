# Eğitsel Değerler (AI Prompt Şablonları) – Nerede?

## Kısa cevap

**Hem veritabanında hem kod içinde.** Çalışma sırasında önce veritabanı ve kazanımlar, bulunamazsa kod içi sözlük kullanılıyor.

---

## 1. Veritabanı

### `prompt_templates` tablosu
- **category:** `educational`
- **key:** `EDUCATIONAL_<deger>` (örn. `EDUCATIONAL_cesaret`, `EDUCATIONAL_merak`)
- **content:** O eğitsel değer için AI’a giden talimat metni
- Migration **015_seed_full_prompt_templates** bu kayıtları ekler (kendi `EDUCATIONAL_PROMPTS` sözlüğünden).

### `learning_outcomes` tablosu
- Her kazanımın **ai_prompt** ve **ai_prompt_instruction** alanları var.
- Hikaye üretilirken seçilen kazanımlar kullanılır; önce bu alanlardaki metin tercih edilir (varsa doğrudan o metin kullanılır).

**Admin panel:**  
- **Prompt Şablonları** → `educational` kategorili şablonlar (EDUCATIONAL_xxx) burada düzenlenir.  
- **Kazanımlar (Eğitsel Hedefler)** → Her kazanımın “AI prompt” alanları burada düzenlenir.

---

## 2. Kod içi (fallback)

### `backend/app/services/ai/gemini_service.py`
- **EDUCATIONAL_VALUE_PROMPTS** (satır ~126): Büyük bir sözlük; her anahtar (örn. `"cesaret"`, `"merak"`, `"doğa"`) için:
  - `theme`: Başlık
  - `instruction`: AI’a verilen talimat metni
- **Kullanım:** Veritabanında veya kazanımda metin yoksa bu sözlükten alınır; hiçbiri yoksa genel fallback (“Bu değer hikayenin ANA TEMASINI oluşturmalı!…”).

### Akış (`_build_educational_prompt_dynamic`)
1. Seçilen her kazanım için:
   - Varsa **learning_outcomes.ai_prompt_instruction** veya **ai_prompt** → doğrudan kullanılır.
   - Yoksa **DB:** `prompt_templates` içinde `key = "EDUCATIONAL_<normalized_key>"` aranır.
   - DB’de yoksa **kod:** **EDUCATIONAL_VALUE_PROMPTS** sözlüğüne bakılır.
   - Orada da yoksa **genel fallback** (tek cümlelik talimat) kullanılır.
2. Tüm parçalar birleştirilip hikaye prompt’una “Eğitsel değerler” bölümü olarak eklenir.

---

## 3. Özet tablo

| Kaynak | Nerede | Ne zaman kullanılır |
|--------|--------|---------------------|
| **learning_outcomes** (ai_prompt / ai_prompt_instruction) | Veritabanı | Kazanım seçildiyse, bu alanlar doluysa **önce** bunlar |
| **prompt_templates** (category=educational, key=EDUCATIONAL_xxx) | Veritabanı | Kazanımda metin yoksa, DB’de bu key varsa **ikinci sıra** |
| **EDUCATIONAL_VALUE_PROMPTS** (gemini_service.py) | Kod | DB’de ilgili key yoksa **fallback** |
| Genel fallback cümlesi | Kod | Hiçbiri yoksa |

---

## 4. Sonuç

- **Admin’den değiştirmek istediğin eğitsel metinler:** Veritabanında (Prompt Şablonları + Kazanımlar). Bunlar öncelikli.
- **Kod:** Hem aynı içeriğin bir kopyasını (migration ile DB’ye basılmış hali) hem de ek / yedek değerleri tutuyor; DB’de karşılığı olmayan veya bulunamayan değerler için fallback.

Yani eğitsel değerler **hem veritabanında hem kodun içinde**; çalışma anında öncelik veritabanı ve kazanım alanlarındadır, kod sözlüğü yedek ve ek değerler içindir.

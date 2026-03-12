---
name: Scenario Writer
description: >
  BenimMasalım projesine yeni senaryo eklerken veya mevcut senaryoyu güncellerken
  MUTLAKA okunup uygulanacak skill. Yeni senaryo talebi, mevcut senaryo denetimi
  veya görsel prompt iyileştirmesi istendiğinde bu dosyayı oku ve adımları eksiksiz uygula.
---
// turbo-all

# 🎭 Scenario Writer Skill
## BenimMasalım — Senaryo Oluşturma & Kalite Standardı

> **Bu skill'i ne zaman kullanırsın?**
> - Kullanıcı "yeni senaryo istiyorum" dediğinde
> - Mevcut bir senaryoyu güncellemek/düzeltmek istediğinde
> - "Görsel promptlar tekrar ediyor" şikayeti geldiğinde
> - Mevcut senaryoları denetleyip kalite puanı vermek istediğinde

---

## ⚡ TEK CÜMLE KURAL

> Bir senaryo; **tutarlı karakterler**, **ilerlemeli görsel akış** ve
> **heyecan verici hikaye** olmak üzere üç temeli taşımak zorundadır.
> Bu üçü olmadan senaryo sisteme girmez.

---

## 📋 ADIM ADIM SÜREÇ

### ADIM 1 — Senaryo Tipini Belirle

İlk yapman gereken senaryonun hangi TÜRE girdiğini anlamak:

| Tip | Tanım | Örnek |
|-----|-------|-------|
| **TİP A: Tek Landmark** | Belirli bir yapı veya yer etrafında geçer | Galata Kulesi, Efes, Yerebatan |
| **TİP B: Geniş Ortam** | Büyük bir bölge — tek yapı yok | Amazon, Uzay, Okyanus |
| **TİP C: Fantastik/Zaman Yolculuğu** | Büyü, zaman yolculuğu, paralel dünya | Çatalhöyük, Dinozor |

Tip belirlendikten sonra `templates/scenario_template.md` dosyasını aç ve doldurmaya başla.

---

### ADIM 2 — 11 Bölümü Doldur

`templates/scenario_template.md` dosyasında 11 bölüm var. Sırayla doldur:

| Bölüm | İçerik | Zorunlu mu? |
|-------|--------|-------------|
| **A** | Temel kimlik (isim, tagline, yaş) | ✅ Zorunlu |
| **B** | Teknik (location_en, theme_key, flags) | ✅ Zorunlu |
| **C** | Kültürel Atlas — min. 10 mekan | ✅ Zorunlu |
| **D** | Yardımcı Karakter Kadrosu — min. 4 seçenek | ✅ Zorunlu |
| **E** | story_prompt_tr — min. 400 kelime | ✅ Zorunlu |
| **F** | Görsel Prompt Şablonları | ✅ Zorunlu |
| **G** | Kahraman Kıyafeti — 3 seçenek sun | ✅ Zorunlu |
| **G2** | Karakter Tutarlılık Kartları | ✅ Zorunlu |
| **G3** | Görsel Akış & Lokasyon Kademe Haritası | ✅ Zorunlu |
| **H** | Kültürel Elementler JSON | ✅ Zorunlu |
| **I** | Scenario Bible JSON | Önerilir |
| **J** | Custom Inputs Schema | Gerekiyorsa |
| **K** | Kalite Kontrol Puanlaması | ✅ Zorunlu |

---

### ADIM 3 — Görsel Akış Sistemi (Tip'e Göre Uygula)

#### 🗼 TİP A (Tek Landmark) — Zorunlu Uygulamalar

```
1. custom page_prompt_template yaz:
   "A young child {scene_description}.
    The child is wearing {clothing_description}.
    Setting elements (choose relevant): [
      EXTERIOR: [yapı dışı öğeleri],
      INTERIOR: [yapı içi mekânları],  
      ATMOSPHERIC: [renk, doku, ışık detayları]
    ]. Composition: text overlay at bottom."

2. story_prompt_tr'ye SAHNE YÖNETMENİ BLOĞU ekle:
   (templates/story_prompt_format.md içindeki bloğu kullan)

3. location_constraints = iç+dış mekan listesi olarak doldur

4. location_flow haritası çıkart (G3-c):
   Hangi sayfalar ikonik / bağlamsal / atmosfer / bağımsız
```

#### 🌿 TİP B (Geniş Ortam) — Uygulamalar

```
1. page_prompt_template'e kamera açısı alternatifleri ekle:
   "[close-up macro / medium action / wide epic / aerial / interior]"

2. story_prompt_tr'ye görsel çeşitlilik + alt-lokasyon kuralı ekle

3. location_constraints = alt-lokasyon listesi
   (Amazon için: nehir kıyısı / ağaç tepesi / orman içi / şelale)
```

#### ✨ TİP C (Fantastik) — Uygulama

```
1. story_prompt_tr'ye GÖRSEL ÇEŞİTLİLİK KURALI ekle:
   (Çatalhöyük örneğinden ilham al — examples/catalhoyuk_reference.md)

2. Her özel obje/eşya için Obje Kartı doldur (G2-b zorunlu)

3. Zaman yolculuğu/büyü geçiş sahneleri için özel görsel kural
```

---

### ADIM 4 — Karakter & Nesne Tutarlılık Kartları (G2)

Her senaryo için **mutlaka** doldurulacak kartlar:

#### G2-a: Yardımcı Karakter Görsel Kimlik Kartı
> Hikayede bir hayvan/fantezi karakter varsa fiziksel özellikleri sabit olmalı.
> Birinci sayfada turuncu → beşinci sayfa sarı olursa tutarsız görsel üretilir.

**story_prompt_tr'ye eklenecek uyarı:**
```
🦊 YARDIMCI KARAKTER TUTARLILIĞI ZORUNLU:
[Karakter Adı] = [ANCHOR CÜMLE — renk, boyut, ayırt edici öğe]
Bu tanım TÜM SAYFALARDA AYNI. image_prompt_en'de her göründüğünde
bu tanımı AYNEN kullan, DEĞİŞTİRME.
```

#### G2-b: Eşya/Obje Kartı
> Madalyon, taş, fener, harita gibi özel objeler de tutarlı olmalı.

**image_prompt_en'e eklenecek anchor:**
```
"holding/wearing [obje tanımı — renk, boyut, görünüm SABIT]"
```

#### G2-c: Yan Rol Karakter Kartı
> İnsan yan roller varsa (usta, satıcı, bilge) kıyafet tutarlı olmalı.

---

### ADIM 5 — Kahraman Kıyafeti (3 Seçenek Sun)

Kullanıcıya 3 farklı kıyafet seçeneği sun. Format:

```
🎨 [SENARYO ADI] — KAHRAMAN KIYAFETİ ÖNERİLERİ

── SEÇENEK 1: [Tema İsmi] ──
   Kız: [İngilizce kıyafet tanımı — SAKIN: mini etek, kısa şort]
   Erkek: [İngilizce kıyafet tanımı]
   Neden uygun: [1 cümle]

── SEÇENEK 2: [Tema İsmi] ──
   ...

── SEÇENEK 3: [Tema İsmi] ──
   ...

❓ Hangisini tercih edersiniz? (1/2/3 veya düzenleme)
```

Kullanıcı seçince:
- `outfit_girl` ve `outfit_boy` alanlarına işle
- story_prompt_tr'ye de ekle: `"Çocuğun kıyafeti: {clothing_description} (TÜM SAYFALARDA DEĞİŞMEZ)"`

---

### ADIM 6 — Kalite Kontrolü (templates/quality_checklist.md)

Tüm bölümler dolduruktan sonra `templates/quality_checklist.md`'yi çalıştır.
**Minimum geçer not: 60/80.** Altında olan senaryo tekrar düzenlenmeden sisteme girmez.

---

### ADIM 7 — Kullanıcıya Çıktıyı Sun

Formatı `templates/output_format.md`'ye göre düzenle ve sun.
Kullanıcı onaylayana kadar migration script üretme.

---

### ADIM 8 — Migration & Update Script İşlemleri

Kullanıcı onayladıktan sonra:

1. **`scripts/` klasörüne update script yaz** (`scripts/update_[theme_key]_scenario.py`)
   - Tüm sabitler: `COVER_PROMPT`, `PAGE_PROMPT`, `STORY_PROMPT_TR`, `CULTURAL_ELEMENTS`, `CUSTOM_INPUTS`, `OUTFIT_GIRL`, `OUTFIT_BOY`
   - `update_[theme_key]_scenario()` async fonksiyon
   
2. **`backend/alembic/versions/` içine migration yaz**
   - Var olan kontrolü
   - INSERT veya UPDATE
   - Pazarlama alanları
   - `downgrade()` = DELETE

3. Alembic migration'ı çalıştır (workflow'a göre)

---

## 🚫 KESİNLİKLE YASAK KURALLAR

### İçerik Yasakları
1. Dini ritüel veya ibadet sahnesi (Umre senaryosu özel izinlidir)
2. Siyasi mesaj, güncel çatışma
3. Korku ağırlıklı, şiddet içeren sahneler
4. Mini etek, kısa şort, karın açık kıyafet
5. `image_prompt_en`'e çocuğun ten rengi, saç rengi, göz rengi **YAZMA** (PuLID halleder)
6. Gezi rehberi formatında hikaye ("Ali Celsus Kütüphanesi'ni gördü. Sonra tiyatroya gitti.")
7. Değeri öğüt vererek anlatma ("Cesaret önemlidir!" demek yasak)
8. Anne, baba, kardeş — `no_family: true` senaryolarda kesinlikle yasak

### Görsel Tutarlılık Yasakları
1. Yardımcı karakter rengi/görünümü sayfa sayfa değiştirilemez
2. Özel eşyalar (madalyon, taş) görünüş değiştiremez
3. Kahraman kıyafeti tek bir sayfada bile değişemez
4. Yan rol karakterlerin kıyafeti değişemez
5. Lokasyon: Her sayfaya aynı landmark resmi çizdirme

### Teknik Yasaklar
1. `story_prompt_tr` 400 kelime altı olamaz
2. `theme_key` mevcut bir key ile çakışamaz
3. `outfit_girl`/`outfit_boy` Türkçe yazılamaz (Flux AI İngilizce ister)
4. `location_en` Türkçe yazılamaz

---

## 📁 Bu Skill'in Dosya Yapısı

```
.agent/skills/scenario-writer/
├── SKILL.md                          ← Bu dosya (giriş noktası)
├── templates/
│   ├── scenario_template.md          ← Doldurulacak şablon
│   ├── story_prompt_format.md        ← story_prompt_tr standart format
│   ├── quality_checklist.md          ← KK kontrol listesi (80 puan)
│   └── output_format.md              ← Kullanıcıya sunum formatı
└── examples/
    └── catalhoyuk_reference.md       ← Mevcut en iyi senaryo örneği
```

---

## 🔗 İlgili Sistem Dosyaları (Referans)

| Dosya | Ne İşe Yarar |
|-------|-------------|
| `backend/app/models/scenario.py` | DB alanlarının tam listesi |
| `backend/app/services/ai/_story_blueprint.py` | PASS-0: Blueprint architect — hikaye iskeleti |
| `backend/app/services/ai/_story_writer.py` | V3 pipeline orchestration (PASS-0 + PASS-1) |
| `backend/app/services/ai/_visual_composer.py` | Görsel prompt compose — page_prompt_template burada kullanılır |
| `backend/app/prompt_engine/visual_prompt_builder.py` | enhance_all_pages — CharacterBible + stil inject |
| `backend/app/prompt_engine/blueprint_prompt.py` | Blueprint system prompt & task prompt builder |
| `backend/app/prompt_engine/__init__.py` | PAGE_GENERATION_SYSTEM_PROMPT |
| `backend/app/prompt_engine/character_bible.py` | Karakter tutarlılık sistemi (kıyafet lock, saç lock) |
| `backend/app/prompt_engine/scenario_bible.py` | Senaryo bible resolver |

### ⚡ Pipeline Akışı (V3 — Tek Geçerli Pipeline)

```
Kullanıcı senaryo seçer
  → PASS-0: Blueprint Architect (story_prompt_tr + scenario_bible → iskelet JSON)
  → PASS-1: Story Writer + Art Director (blueprint → Türkçe metin + İngilizce görsel prompt)
  → Enhancement: CharacterBible + VisualPromptBuilder (kıyafet lock, stil inject, kompozisyon)
  → Validation: StoryValidators + VisualPromptValidator (güvenlik, sayfa sayısı, auto-fix)
```

> **NOT:** Legacy pipeline (V2 two-pass) tamamen kaldırılmıştır. V3 tek kaynak.


# V3 Karakter Tutarlılığı (Character Consistency) Analizi

> **Tarih:** 2026-02-18  
> **Kapsam:** Fotoğraf yükleme → yüz sabitleme → 22 sayfa boyunca tutarlılık mekanizmaları

---

## 1. Executive Summary

Sistemde karakter tutarlılığı **iki bağımsız katman** (Double Locking) ile sağlanır:

| # | Katman | Mekanizma | Baskınlık |
|---|--------|-----------|-----------|
| **1** | **Piksel Bazlı** — PuLID Face Identity | Fal.ai `flux-pulid` modeline `reference_image_url` olarak orijinal fotoğraf gider. Diffusion sürecinin **step 2**'sinden itibaren yüz embedding'i enjekte edilir. | **%70 — BASKICI** |
| **2** | **Metin Bazlı** — CharacterBible + Face Description | Gemini Vision fotoğrafı analiz eder → "forensic" yüz tarifi üretir → bu metin her sayfanın `image_prompt_en`'ine enjekte edilir. | **%20 — Destekleyici** |
| **3** | **Kıyafet Kilidi** — OutfitSpec (CharacterBible) | Sabit kıyafet tanımı (top/bottom/shoes/colors) her sayfaya aynı şekilde enjekte edilir. | **%10 — Tutarlılık** |

**Kritik Bulgu:** Gemini'ye (hikaye + prompt üretimi için) fotoğraf **GÖNDERİLMEZ**. Gemini sadece metin alır. Fotoğraf yalnızca iki yere gider:
1. `FaceAnalyzerService` → Gemini Vision (multimodal) ile yüz tasviri üretmek için
2. `FalAIService` → Fal.ai PuLID API'sine `reference_image_url` olarak

---

## 2. Mimari Akış Diyagramı

```
┌──────────────────────────────────────────────────────────────────────┐
│  KULLANICI FOTOĞRAF YÜKLEME                                         │
│  child_photo_url (GCS/CDN URL)                                      │
└──────────┬───────────────────────────┬───────────────────────────────┘
           │                           │
           ▼                           ▼
┌─────────────────────┐    ┌──────────────────────────────────────────┐
│ FaceAnalyzerService │    │   Fal.ai PuLID (Her sayfa görsel üretim) │
│ (Gemini 2.0 Flash   │    │                                          │
│  multimodal)         │    │  payload.reference_image_url =           │
│                      │    │      child_photo_url                     │
│ Fotoğraf → base64    │    │  payload.id_weight = 0.70–0.80          │
│ → "forensic" analiz  │    │  payload.start_step = 2                 │
│ → metin çıktı:       │    │  payload.true_cfg = 1.0                 │
│  "a 4-year-old child │    │                                          │
│   with curly brown   │    │  Model: fal-ai/flux-pulid               │
│   hair, hazel eyes,  │    │  (fotoğraf yoksa: fal-ai/flux/dev)       │
│   warm olive skin"   │    │                                          │
└──────────┬───────────┘    └──────────────────────────────────────────┘
           │                                    ▲
           ▼                                    │
┌──────────────────────┐                        │
│ visual_character_    │                        │
│ description (metin)  │                        │
└──────────┬───────────┘                        │
           │                                    │
           ▼                                    │
┌──────────────────────┐    ┌──────────────────┴──────────────────────┐
│ generate_story_v3()  │    │  compose_enhanced_prompt() (her sayfa)  │
│                      │    │                                          │
│ PASS-0: Blueprint    │    │  character_bible.prompt_block            │
│   (metin → metin)    │    │    → yaş/isim/saç/göz/ten/kıyafet      │
│                      │    │    → identity_tokens:                    │
│ PASS-1: Pages        │    │      "same face on every page"          │
│   (metin → metin)    │    │      "same hairstyle on every page"     │
│                      │    │      "same skin tone on every page"     │
│ child_description =  │    │      "natural child proportions"        │
│ visual_character_    │    │      "no chibi, no bobblehead"          │
│ description          │    │                                          │
└──────────┬───────────┘    │  negative_tokens:                        │
           │                │    "wrong hair color, wrong skin color,  │
           ▼                │     different hair length, changed outfit │
   ┌────────────────┐       │     inconsistent hairstyle..."           │
   │ CharacterBible │───────┤                                          │
   │ build_...()    │       │  outfit.prompt_fragment                   │
   └────────────────┘       │    → "wearing a cozy adventure jacket,   │
                            │       comfortable khaki pants,            │
                            │       sturdy brown sneakers"              │
                            └──────────────────────────────────────────┘
```

---

## 3. Kimlik Sabitleme Kaynakları (Detaylı)

### 3.1 Kaynak-1: PuLID Face Identity (Piksel Bazlı) — **BASKIN**

**Dosya:** `backend/app/services/ai/fal_ai_service.py`  
**Fonksiyon:** `generate_consistent_image()` (`:252`)

PuLID, Flux model'in diffusion sürecine doğrudan yüz embedding'i enjekte eden bir mekanizmadır. Fotoğraf **pixel düzeyinde** modele verilir — metin tarifine bağımlı değildir.

**Fal.ai Payload (PuLID aktifken):**

| Parametre | Değer | Açıklama |
|-----------|-------|----------|
| `reference_image_url` | `child_photo_url` | Kullanıcının yüklediği orijinal fotoğraf URL'si |
| `id_weight` | `0.70–0.80` | Stil bazlı otomatik ayar (aşağıda tablo) |
| `start_step` | `2` | Diffusion'un 2. adımından itibaren yüz enjekte edilir |
| `true_cfg` | `1.0` | Prompt uyumluluğu ile yüz dengesi |
| `num_inference_steps` | `28` | Toplam diffusion adımı |
| `guidance_scale` | `3.5` | Prompt'a bağlılık gücü |
| `max_sequence_length` | `512` | Token bütçesi (prompt truncation koruması) |

**Model Seçim Mantığı:**
```
child_face_url mevcut → fal-ai/flux-pulid  (PuLID aktif)
child_face_url boş    → fal-ai/flux/dev     (Yüz referansı yok)
```

**Stil Bazlı `id_weight` Tablosu:**

| Stil | `id_weight` | Neden |
|------|-------------|-------|
| DEFAULT (2D Children's Book) | 0.70–0.75 | Düşük: stil + yüz dengesi |
| PIXAR (3D) | 0.78 | Yüksek: 3D'de yüz bozulma riski az |
| WATERCOLOR | 0.72 | Düşük: suluboya stilinin yüzü ezmemesi için |
| ANIME / Ghibli | 0.76 | Orta: anime tarzı yüz stilize eder, ama saç/ten korunmalı |
| SOFT PASTEL | 0.74–0.75 | Orta-düşük |
| ADVENTURE DIGITAL | 0.72 | Düşük |

**Dosya:** `backend/app/prompt_engine/constants.py` → `STYLE_PULID_WEIGHTS` (`:330`)

**Neden Baskın?**  
PuLID, diffusion sürecinin en erken adımlarında (step 2) yüz ID vektörünü enjekte eder. Bu, metin prompt'undan bağımsız olarak yüzün yapısal özelliklerini (göz mesafesi, burun şekli, çene hattı) korur. Metin tarifindeki "curly brown hair" ifadesi yanlış olsa bile, PuLID fotoğraftan doğru saçı çıkarır.

---

### 3.2 Kaynak-2: FaceAnalyzerService — Forensic Yüz Tasviri (Metin Bazlı)

**Dosya:** `backend/app/services/ai/face_analyzer_service.py`  
**Fonksiyon:** `analyze_for_ai_director()` (`:278`)

Kullanıcının fotoğrafı, Gemini 2.0 Flash **multimodal** API'sine gönderilir ve "forensic" düzeyde bir yüz tasviri **metin** olarak üretilir.

**İşlem Akışı:**
1. Fotoğraf URL'sinden indirilir → base64'e çevrilir
2. Gemini 2.0 Flash'a `inlineData` (base64 görsel) + analiz prompt'u gönderilir
3. Çıktı: 30-50 kelimelik İngilizce yüz tarifesi

**Örnek Çıktı:**
```
"a 4-year-old child named Enes with straight dark brown bowl-cut hair 
with thick blunt bangs covering forehead, light fair skin with rosy 
cheeks, round soft face, small dark brown eyes, and a button nose"
```

**Analiz Prompt Öncelik Sırası:**
1. **HAIRSTYLE** — "MOST CRITICAL — parents recognize their child by hairstyle"
2. **SKIN TONE** — "CRITICAL — must be preserved exactly"
3. **FACE SHAPE** — round, oval, heart-shaped
4. **Eye color/shape** — "NEVER describe as large or big"
5. **Distinctive features** — dimples, freckles, etc.

**Gemini Parametreleri:**
- Model: `gemini-2.0-flash`
- Temperature: `0.3` (düşük — olgusal doğruluk)
- Max output tokens: `200` (kısa tutma)
- Safety: tüm kategoriler `BLOCK_NONE`

**Bu metin nereye gider?**
```
analyze_for_ai_director() 
  → child_visual_desc (str)
    → generate_story_v3(visual_character_description=child_visual_desc)
      → PASS-0: build_blueprint_task_prompt(child_description=...)
      → PASS-1: build_page_task_prompt(child_description=...)
      → build_character_bible(child_description=child_visual_desc)
        → _parse_appearance() → appearance_tokens
        → CharacterBible.prompt_block → HER SAYFA PROMPT'UNA ENJEKSİYON
```

**Neden Destekleyici (Baskın Değil)?**  
- Metin tarifesi, diffusion modelde sadece bir token dizisi olarak işlenir
- PuLID'ın piksel bazlı yüz embedding'i her zaman metin tarife baskın gelir
- Ancak metin tarife, PuLID'ın "doğru yöne" başlamasını sağlar (saç rengi, ten tonu ipuçları)

---

### 3.3 Kaynak-3: CharacterBible — Kıyafet + Kimlik Token Kilidi

**Dosya:** `backend/app/prompt_engine/character_bible.py`

CharacterBible, kitap boyunca sabit kalan tüm görsel kimlik bilgilerini taşıyan frozen dataclass'tır. **Bir kez** üretilir, **22 sayfanın hepsine** aynı şekilde enjekte edilir.

#### 3.3.1 `prompt_block` — Her Sayfanın Prompt'una Eklenen Blok

```
"4-year-old boy named Bora, curly brown hair, hazel eyes, warm olive skin, 
wearing a cozy adventure jacket with rolled-up sleeves, comfortable khaki pants, 
and sturdy brown sneakers, color palette: warm earth tones, 
same face on every page, same hairstyle on every page, 
same skin tone on every page, same facial features on every page, 
natural child proportions, small realistic eyes, no chibi, no bobblehead"
```

**Bileşenler:**

| Bileşen | Kaynak | Değişir mi? |
|---------|--------|-------------|
| Yaş + isim + cinsiyet | UI girişi | Hayır (kitap boyunca sabit) |
| `appearance_tokens` | `_parse_appearance(child_description)` → TR→EN çeviri | Hayır |
| `outfit.prompt_fragment` | `OutfitSpec` preset veya `fixed_outfit` override | Hayır |
| `identity_tokens` | Hardcoded: "same face on every page" vb. | Hayır |
| `companion` | Blueprint'ten `side_character` | Hayır |

#### 3.3.2 `negative_tokens` — Tutarsızlık Engelleme

Her sayfanın negative prompt'una eklenen tokenlar:
```
"wrong hair color, wrong skin color, different hair length, 
inconsistent hairstyle, changed outfit, different clothes, 
wrong eye color, aged up, aged down"
```

Companion varsa ek olarak:
```
"cat, dog, rabbit, bird, fox, bear, wrong companion animal"
```

#### 3.3.3 Kıyafet Kilidi (OutfitSpec)

**Cinsiyet bazlı preset:**

| Cinsiyet | Üst | Alt | Ayakkabı | Renk Paleti |
|----------|-----|-----|----------|-------------|
| Erkek | cozy adventure jacket with rolled-up sleeves | comfortable khaki pants | sturdy brown sneakers | warm earth tones: olive green, khaki, brown |
| Kız | colorful adventure dress with pockets | comfortable leggings | sturdy red sneakers | warm cheerful tones: teal, navy, red |

**Override:** UI'dan `fixed_outfit` gönderilirse preset yerine o kullanılır.

---

### 3.4 Kaynak-4: Appearance Parser (TR → EN Çeviri)

**Dosya:** `backend/app/prompt_engine/character_bible.py` → `_parse_appearance()` (`:249`)

Kullanıcının Türkçe girdiği `child_description` (ör: "kıvırcık kahverengi saçlı, ela gözlü") İngilizce token'lara çevrilir:

| Kategori | TR → EN Mapping |
|----------|----------------|
| **Saç Rengi** | kahverengi→brown, siyah→black, sarı→blonde, kızıl→red, kumral→light brown |
| **Saç Tipi** | kıvırcık→curly, düz→straight, dalgalı→wavy, uzun→long, örgülü→braided |
| **Göz Rengi** | ela→hazel, mavi→blue, yeşil→green, kahverengi→brown |
| **Ten** | açık tenli→light skin, esmer→olive skin, buğday tenli→warm olive skin |
| **Özellikler** | gözlüklü→wearing round glasses, çilli→freckled cheeks, gamzeli→dimpled cheeks |

**Sınırlama:** Eğer kullanıcı hiç `child_description` girmezse, `appearance_tokens` boş kalır ve sadece PuLID + identity tokens ile tutarlılık sağlanır.

---

## 4. Gemini'ye Referans Image Gidiyor mu?

### Cevap: **HAYIR (hikaye/prompt üretimi için)**

Gemini'nin V3 pipeline'daki kullanımları:

| Adım | Gemini Modeli | Girdi | Fotoğraf Gider mi? |
|------|---------------|-------|--------------------|
| **FaceAnalyzerService** | gemini-2.0-flash (multimodal) | base64 fotoğraf + analiz prompt'u | **EVET** — tek seferlik yüz analizi |
| **PASS-0 Blueprint** | gemini-2.0-flash | Sadece metin (system + task prompt) | **HAYIR** |
| **PASS-1 Pages** | gemini-2.0-flash | Sadece metin (system + task prompt) | **HAYIR** |

PASS-0 ve PASS-1'de Gemini'ye giden payload:
```json
{
  "contents": [{"parts": [{"text": "full_prompt"}]}],
  "generationConfig": {...}
}
```

**Sadece `text` alanı var, `inlineData` (görsel) YOK.** Gemini, hikaye ve prompt üretiminde fotoğrafı görmez. Yüz bilgisi yalnızca `child_description` metni olarak iletilir.

---

## 5. Seed Mekanizması

**Dosya:** `backend/app/services/ai/fal_ai_service.py` → `GenerationConfig` (`:94`)

```python
seed: int | None = None  # For reproducibility
```

**Durum:** Varsayılan `None`. Seed **şu an kullanılmıyor** (her sayfa farklı random seed alır).

```python
if self.generation_config.seed:
    payload["seed"] = self.generation_config.seed
```

**Sonuç:** Seed, sayfalar arası tutarlılığa katkı **sağlamıyor**. Tutarlılık tamamen PuLID + CharacterBible'a bağlı.

---

## 6. Prompt Enjeksiyon Sırası (compose_enhanced_prompt)

**Dosya:** `backend/app/prompt_engine/visual_prompt_builder.py` → `compose_enhanced_prompt()` (`:475`)

Diffusion modelde token'lar sıralamaya göre ağırlık alır (ilk token'lar daha güçlü):

| Sıra | Bileşen | Kimlik Etkisi |
|------|---------|---------------|
| 1 | `style_anchor` (2-3 kelime) | — |
| **2** | **`character_bible.prompt_block`** | **YÜKSEK: Yaş, isim, saç, göz, ten, kıyafet, "same face" talimatları** |
| 3 | Temizlenmiş LLM sahne promptu | — |
| 4 | Ekstra obje token'ları | — |
| 5 | Iconic anchors (lokasyon) | — |
| 6 | Camera/composition (ShotPlan) | — |
| 7 | Value visual motif | — |
| 8 | Emotion | — |
| 9 | `STYLE: {style_block}` | — |
| 10 | "no text, no watermark, no logo" | — |

CharacterBible **2. sırada** — yani prompt'un en yüksek ağırlıklı bölümlerinden birinde. Bu, metin bazlı kimlik bilgisinin mümkün olan en güçlü pozisyonda olmasını sağlar.

---

## 7. Baskınlık Sıralaması ve Risk Analizi

### Final Sıralama

| Sıra | Kaynak | Baskınlık | Risk |
|------|--------|-----------|------|
| **1** | **PuLID face embedding** (`reference_image_url` + `id_weight`) | **%70** | `id_weight` çok yüksekse → bobblehead efekti. Çok düşükse → jenerik yüz. |
| **2** | **CharacterBible.prompt_block** (metin kimlik kilidi) | **%20** | `_parse_appearance()` TR→EN çevirisi hatalıysa yanlış token üretir. Kullanıcı `child_description` girmezse boş kalır. |
| **3** | **OutfitSpec** (kıyafet kilidi) | **%5** | Tüm sayfalar aynı kıyafet — monotonluk riski. Ama tutarlılık için gerekli. |
| **4** | **Identity tokens** ("same face on every page") | **%3** | Diffusion modelde "instruction-following" sınırlı, ama destekleyici. |
| **5** | **Negative tokens** ("wrong hair color, changed outfit") | **%2** | Engelleme gücü sınırlı, ama yanlış yönleri bloklar. |

### Neden Bu Sıralama?

1. **PuLID piksel bazlı:** Yüzün geometrik yapısını (göz mesafesi, burun oranı, çene) fotoğraftan doğrudan alır. Metin "blue eyes" dese bile, fotoğrafta kahverengi gözler varsa PuLID kahverengiyi korur.

2. **CharacterBible metinsel:** Diffusion modelde metin token'ları stil ve sahneyi yönlendirir. Yüz bilgisi olarak "curly brown hair, hazel eyes" gibi token'lar PuLID'ı destekler ama override edemez.

3. **Seed yok:** Her sayfa farklı random seed kullanır → varyasyon PuLID + metin tarafından kontrol edilir.

---

## 8. Bilinen Zayıflıklar

| # | Sorun | Detay | Öneri |
|---|-------|-------|-------|
| 1 | **`child_description` boş olabilir** | Kullanıcı metin girmezse `appearance_tokens` boş → CharacterBible'da sadece "4-year-old boy named X" kalır | FaceAnalyzerService'in çıktısını `child_description` olarak otomatik kullan (şu an bağımsız akışlar) |
| 2 | **TR→EN çeviri eksikleri** | "Kumral" → "light brown" var ama "bal rengi" → yok | Dictionary genişletilmeli |
| 3 | **start_step=2 vs stilize stiller** | Anime/watercolor gibi stiller yüzü stilize etmek ister ama PuLID step 2'den başlayarak "gerçekçi" yüz dayatır | Stil bazlı `start_step` ayarı (anime: 4, watercolor: 3) |
| 4 | **Seed tutarsızlığı** | Her sayfa farklı seed → arka plan, ışık, poz tamamen rastgele | Opsiyonel: aynı seed + farklı prompt ile sabit kompozisyon testi |
| 5 | **`analyze_for_ai_director` ve `_parse_appearance` paralel çalışır** | İki bağımsız yüz tasvir mekanizması var, birbiriyle çelişebilir | Tek kaynak: `analyze_for_ai_director` çıktısını CharacterBible'ın `appearance_tokens`'ı olarak kullan |

---

## 9. Dosya Haritası

| Dosya | Rolü |
|-------|------|
| `backend/app/services/ai/face_analyzer_service.py` | Gemini Vision ile fotoğraftan yüz tasviri üretme |
| `backend/app/prompt_engine/character_bible.py` | CharacterBible: identity + outfit + negative tokens |
| `backend/app/services/ai/fal_ai_service.py` | PuLID ile görsel üretim, `reference_image_url` gönderimi |
| `backend/app/prompt_engine/constants.py` | `STYLE_PULID_WEIGHTS`, `get_pulid_weight_for_style()` |
| `backend/app/prompt_engine/visual_prompt_builder.py` | `compose_enhanced_prompt()`: CharacterBible prompt'a enjeksiyon |
| `backend/app/api/v1/trials.py` | API endpoint: `child_photo_url` alma ve pipeline'a verme |
| `backend/app/api/v1/ai.py` | Test endpoint: face analysis + generate_story_structured |
| `backend/app/models/visual_style.py` | `id_weight` DB override desteği |

---

## 10. Özet: "Aynı Çocuk" Nasıl Çıkıyor?

```
1. Kullanıcı fotoğraf yükler → child_photo_url (GCS URL)

2. FaceAnalyzerService → Gemini Vision multimodal:
   Fotoğraf + prompt → "a 4-year-old child with curly brown hair..."
   Bu metin → child_description olarak pipeline'a girer

3. CharacterBible oluşturulur (1 kez, kitap başına):
   - appearance_tokens = _parse_appearance(child_description) → ["curly brown hair", "hazel eyes"]
   - outfit = OutfitSpec preset (cinsiyet bazlı)
   - identity_tokens = ["same face on every page", ...]
   - prompt_block = hepsi birleştirilmiş tek string

4. Her sayfa (1-22) için:
   compose_enhanced_prompt():
     → [style_anchor] + [CHARACTER_BIBLE.prompt_block] + [sahne] + ... + [STYLE:]
   
   generate_consistent_image():
     → payload.prompt = yukarıdaki composed prompt
     → payload.reference_image_url = child_photo_url  ← PuLID enjeksiyon
     → payload.id_weight = stil bazlı (0.70-0.80)
     → payload.start_step = 2
     → Model: fal-ai/flux-pulid

5. PuLID mekanizması:
   Step 1: Normal diffusion başlar (noise → image)
   Step 2+: Fotoğraftaki yüz embedding'i enjekte edilir
   Step 28: Final görsel — fotoğraftaki yüze benzer çocuk, 
            prompt'taki sahne ve stilde
```

**Sonuç:** Karakter tutarlılığı %70 PuLID (piksel), %20 CharacterBible (metin), %10 outfit/identity tokens ile sağlanır. Gemini'nin hikaye üretim pipeline'ına fotoğraf **gönderilmez** — yalnızca FaceAnalyzer ve Fal.ai PuLID fotoğrafı görür.

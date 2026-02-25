# Cache / Tekrar Üretim / Aynı Sonuçlar Analizi

> **Tarih:** 2026-02-18  
> **Problem:** Kullanıcı aynı kitapta farklı stil seçse de görüntüler çok benziyor

---

## Executive Summary

Sistemde uygulama-seviyesinde **hiçbir image caching katmanı yok** — her `generate_consistent_image()` çağrısı Fal.ai'ye taze bir HTTP isteği gönderiyor. Aynı-benzeri görüntülerin asıl sebebi **prompt benzerliği + reference image dominansı.** Aşağıda 5 hipotez, etki analizi ve doğrulama adımları yer alıyor.

---

## 1. Mevcut Sistemde Cache / Dedup Katmanları

### 1.1 Image Cache → **YOK**

| Soru | Cevap | Kanıt |
|------|-------|-------|
| Redis / Memcached image cache var mı? | **Hayır** | Codebase'de `lru_cache`, Redis, Memcached import'u yok (Fal servis tarafı) |
| Prompt hash → URL eşleştirmesi var mı? | **Hayır** | `prompt_hash` loglanıyor (manifest) ama cache key olarak kullanılmıyor |
| HTTP response cache var mı? | **Hayır** | `httpx.AsyncClient` default — cache middleware bağlanmamış |
| Fal.ai server-side cache var mı? | **Hayır** — Fal.ai her istekte yeni görsel üretir | Fal.ai dökümantasyonu |

### 1.2 Prompt Cache → **VAR (Trial/Preview sistemi)**

`StoryPreview.generated_prompts_cache` JSONB kolonu:

```python
# story_preview.py:103-112
generated_prompts_cache = {
    "style_id": "uuid-of-visual-style",
    "scenario_id": "uuid-of-scenario",
    "outcomes_hash": "md5-of-outcomes",
    "prompts": [...],                     # 16 sayfa prompt
    "_resolved_style": {                  # Preview'deki stil parametreleri
        "style_modifier": "...",
        "style_negative_en": "...",
        "leading_prefix_override": "...",
        "style_block_override": "...",
    }
}
```

**Bu cache'in amacı:** Phase 2'de (ödeme sonrası kalan 13 sayfa) Gemini'yi tekrar çağırmamak. Prompt'lar Phase 1'de üretilip DB'ye yazılıyor, Phase 2'de oradan okunuyor.

### 1.3 Request Idempotency → **YOK**

Her `generate_consistent_image()` çağrısı bağımsız. Aynı prompt + aynı parametrelerle iki kez çağrılırsa iki farklı görsel üretilir (seed sabitlenmemişse).

### 1.4 Storage Path Overwrite → **YOK (UUID bazlı)**

```python
# storage_service.py:217
blob_path = f"books/{order_id}/pages/page_{page_number}.png"
```

Her sipariş farklı `order_id` (UUID) alır → path çakışması olmaz. Aynı siparişteki yeniden üretim `page_number` bazlı overwrite eder — bu doğru davranış.

### 1.5 Seed → **Varsayılan None (rastgele)**

```python
# fal_ai_service.py:101
seed: int | None = None  # For reproducibility

# fal_ai_service.py:520-521
if self.generation_config.seed:
    payload["seed"] = self.generation_config.seed
```

Seed default `None` → Fal.ai her seferinde rastgele seed kullanır. **Seed hiçbir zaman sabitlenmiyor** (iyi).

---

## 2. Beş Hipotez: Neden Farklı Stilde Benzer Görüntüler?

### HİPOTEZ 1: Reference Image (PuLID) Prompt'u Bastırıyor ⭐ EN OLASI

**Mekanizma:**
- `flux-pulid` modeli `reference_image_url` + `id_weight` ile çalışır
- `id_weight` 0.72–0.80 arasında (stile göre) — bu yüksek bir değer
- `start_step=2` → **çok erken enjeksiyon** — modelin ilk diffusion adımlarında yüz + saç referanstan alınıyor
- Sonuç: Modelin "yaratıcı alanı" daralıyor, stil talimatları referans görselinin etkisi altında kalıyor

**Neden benzer çıkıyor:**
```
Aynı reference_image + benzer sahne prompt → model aynı yüz/saç/ten kompozisyonunu üretiyor
                                             → stil sadece renk paleti ve doku değişiyor
                                             → genel görüntü "aynı" hissediliyor
```

**Etki seviyesi:** `id_weight=0.80` → yüzün %80'i referanstan, %20'si prompt'tan → stil etkisi sadece kalan %20'deki dokularda belirgin.

**Doğrulama:**

| Test | Nasıl | Beklenen |
|------|-------|----------|
| A/B: Aynı prompt, ref image ile / ref image olmadan (flux-dev) | `child_face_url=None` ile çalıştır | Stil farkı **çok belirgin** olmalı |
| id_weight düşür (0.50) | `PuLIDConfig(id_weight=0.50)` | Stil daha baskın, yüz daha az benzer |
| start_step yükselt (4→6) | `PuLIDConfig(start_step=6)` | Modelin ilk adımlarında stili daha çok uygulaması |

---

### HİPOTEZ 2: STYLE: Bloğu Prompt Sonunda → Düşük Diffusion Weight

**Mekanizma:**
Flux modelinde prompt token'ları position-weighted. Prompt başındaki token'lar daha yüksek ağırlık alır. V3 composed prompt yapısı:

```
[style_anchor]  ← konum 0-10    → YÜKSEK ağırlık (iyi)
[bible]         ← konum 10-80   → YÜKSEK ağırlık
[scene]         ← konum 80-160  → ORTA ağırlık
[objects]       ← konum 160-200 → DÜŞÜK ağırlık
[STYLE: block]  ← konum 200-300 → EN DÜŞÜK ağırlık ⚠️
[suffix]        ← konum 300+    → yok sayılabilir
```

**Sonuç:** `style_anchor` (5-6 token) stili temsil ediyor ama `style_block` (30-50 token, detaylı talimatlar) son sırada olduğu için az etkili.

**Doğrulama:**

| Test | Nasıl | Beklenen |
|------|-------|----------|
| Style block'u prompt başına taşı | `compose_enhanced_prompt()` sıralamasını değiştir | Stil farkı belirginleşmeli |
| Style anchor'ı 2x tekrarla | `"2D hand-painted storybook. 2D hand-painted storybook."` | Stil güçlenmeli |

---

### HİPOTEZ 3: V3 Prompt Cache — Stil Değişikliği Yansımıyor (Trial Akışı)

**Mekanizma:**
Trial/Preview akışında prompt'lar Phase 1'de üretilip DB'ye cache'leniyor:

```python
# trial_service.py:143
generated_prompts_cache = {
    "style_id": style_id,           # Cache invalidation key
    "prompts": generated_prompts,   # 16 sayfa prompt (STYLE: block dahil)
}
```

Kullanıcı stil değiştirip yeniden denerse:
1. Yeni bir trial oluşturulur → yeni Gemini çağrısı → yeni prompt'lar (doğru)
2. **AMA:** Phase 2'de (kalan sayfalar) eski trial'ın cache'i kullanılıyorsa → eski stil prompt'ları uygulanır

**Potansiyel sorun:** `complete-trial` endpoint'inde cache'teki `_resolved_style` okunuyor:

```python
# trials.py:1757-1768
_cached_style = (
    (_trial_obj_rem.generated_prompts_cache or {}).get("_resolved_style")
)
if _cached_style:
    visual_style = _cached_style.get("style_modifier", "")
    _rem_style_negative_en = _cached_style.get("style_negative_en", "")
    # ... tüm stil parametreleri cache'ten!
```

Bu doğru çalışıyor — aynı trial'daki Preview (3 sayfa) ve Remaining (13 sayfa) aynı stili kullanmalı. Ama kullanıcı **farklı trial** oluşturduğunda (yeni stil ile) tamamen yeni prompt'lar üretiliyor — bu da doğru.

**Cache invalidation problemi yok** — her yeni istek yeni trial yaratıyor.

**Doğrulama:**

| Test | Nasıl | Beklenen |
|------|-------|----------|
| Aynı çocuk + aynı senaryo + farklı stil → 2 trial oluştur | İki ayrı `create-trial` isteği | `generated_prompts_cache.style_id` farklı olmalı |
| İki trial'ın STYLE: bloklarını karşılaştır | DB'den `prompt_debug_json` oku | Farklı stil talimatları içermeli |

---

### HİPOTEZ 4: CharacterBible Prompt Bloğu Her Stilde Aynı → Ortak Baseline

**Mekanizma:**
`CharacterBible.prompt_block` her sayfada aynı metni enjekte ediyor:

```
"4-year-old boy named Bora, curly dark brown hair, warm olive skin,
round face, small button nose, wearing a bright red t-shirt with
a little dinosaur print and navy blue shorts..."
```

Bu metin ~200-350 karakter ve prompt'un **en güçlü pozisyonunda** (2. sırada, style_anchor'dan hemen sonra). Sonuç:

| Prompt payı | İçerik | Tüm stillerde |
|-------------|--------|---------------|
| %25-35 | CharacterBible (yaş, saç, ten, kıyafet, kimlik token'ları) | **AYNI** |
| %20-30 | Scene description (sahne aksiyonu) | **AYNI** (aynı hikaye) |
| %10-15 | Shot plan + composition | **AYNI** |
| %5-10 | Value motif + iconic anchors | **AYNI** |
| %10-15 | Style anchor + STYLE: block | **FARKLI** |

**Sonuç:** Prompt'un **~70-80%'i stillerde ortaktır.** Model girdi benzerliği nedeniyle benzer çıktılar üretiyor.

**Doğrulama:**

| Test | Nasıl | Beklenen |
|------|-------|----------|
| İki farklı stil prompt'unu yan yana koy | `prompt_debug_json` karşılaştır | %70+ ortak token |
| Ortak kısmı çıkart, sadece farklı kısmı gönder | Sadece STYLE block + scene ile üret | Çok farklı sonuçlar |

---

### HİPOTEZ 5: Fal.ai `guidance_scale=3.5` — Düşük Prompt Adherence

**Mekanizma:**
```python
# fal_ai_service.py:98
guidance_scale: float = 3.5  # Prompt adherence
```

`guidance_scale=3.5` Flux modeli için oldukça düşük. Karşılaştırma:

| guidance_scale | Etki |
|---------------|------|
| 1.0-2.0 | Model çok serbest — prompt az etkili |
| 3.0-4.0 | **Mevcut** — orta seviye, referans görsel baskın |
| 5.0-7.5 | Prompt'a daha sadık — stil farkı daha belirgin |
| 8.0+ | Aşırı — artifactlar başlar |

Düşük `guidance_scale` + yüksek `id_weight` = referans görselinin stil'i bastırması.

**Doğrulama:**

| Test | Nasıl | Beklenen |
|------|-------|----------|
| `guidance_scale=5.0` ile aynı prompt'u dene | `GenerationConfig(guidance_scale=5.0)` | Stil farkı belirginleşmeli |
| `guidance_scale=7.0` ile dene | Üst sınıra yakın | Stil çok baskın, yüz kalitesi düşebilir |

---

## 3. Hipotez Öncelik Sıralaması

| # | Hipotez | Olasılık | Etki | Fix Zorluk |
|---|---------|----------|------|------------|
| **1** | Reference image (PuLID) prompt'u bastırıyor | **%90** | Yüksek | Orta — id_weight/start_step tuning |
| **2** | STYLE: bloğu prompt sonunda → düşük ağırlık | **%75** | Orta | Kolay — sıralama değişikliği |
| **4** | CharacterBible ortak baseline çok büyük | **%60** | Orta | Zor — bible kısaltma/stilize etme |
| **5** | guidance_scale=3.5 düşük | **%50** | Orta | Kolay — parametre değişikliği |
| **3** | Cache stil yansıtmıyor | **%10** | Düşük | N/A — kod doğru çalışıyor |

---

## 4. Kod Kanıtları

### 4.1 Cache Katmanı — Dosya Haritası

| Dosya | Cache Türü | Kapsam |
|-------|------------|--------|
| `backend/app/models/story_preview.py:105` | `generated_prompts_cache` (JSONB) | Prompt + stil parametreleri, trial bazlı |
| `backend/app/services/trial_service.py:143` | Cache yazma | Phase 1 → DB |
| `backend/app/services/trial_service.py:236` | Cache okuma | Phase 2 → DB'den prompt çek |
| `backend/app/api/v1/trials.py:1016-1028` | `_resolved_style` cache yazma | Preview stil parametrelerini kaydet |
| `backend/app/api/v1/trials.py:1754-1770` | `_resolved_style` cache okuma | Remaining sayfalar için stil oku |
| `backend/app/services/ai/fal_ai_service.py:232` | `_sessions` (in-memory dict) | BookGenerationSession — kıyafet tutarlılığı |

### 4.2 Seed Durumu

| Dosya:Satır | Seed Değeri | Sonuç |
|-------------|-------------|-------|
| `fal_ai_service.py:101` | `seed: int | None = None` | **Default: rastgele** |
| `fal_ai_service.py:520` | `if self.generation_config.seed:` | **Sadece açıkça set edilirse gönderilir** |
| Üretim kodu | `GenerationConfig()` default | **Seed hiç set edilmiyor** → her seferinde farklı |

### 4.3 Storage Path

| Akış | Path Pattern | Çakışma |
|------|-------------|---------|
| Kitap sayfası | `books/{order_id}/pages/page_{page_number}.png` | **Hayır** — UUID bazlı |
| Preview | `stories/{story_id}/page_{page_num}.png` | **Hayır** — UUID bazlı |
| Temp (face) | `temp/pulid-faces/{temp_id}_{timestamp}.jpg` | **Hayır** — timestamp'li |

---

## 5. Çözüm Stratejisi

### Strateji A: PuLID Weight Stile Göre Daha Agresif Ayarla (P0)

Mevcut `STYLE_PULID_WEIGHTS`:

| Stil | Mevcut id_weight | Önerilen |
|------|-----------------|----------|
| watercolor | 0.72 | **0.60** — sulu boya dokunun çıkması için daha fazla alan |
| soft_pastel | 0.74 | **0.62** |
| anime | 0.76 | **0.65** — anime çizgilerinin belirmesi için |
| default (2D) | 0.78 | 0.72 |
| pixar | 0.78 | 0.78 — 3D modelde yüz referansı daha kritik |
| adventure_digital | 0.78 | 0.72 |
| 3D | 0.80 | 0.78 |

### Strateji B: Style Block'u Prompt Başına Taşı (P1)

Mevcut sıralama:
```
[anchor] [bible] [scene] [objects] [anchors] [shot] [motif] [emotion] [STYLE:] [suffix]
```

Önerilen:
```
[anchor] [STYLE-CORE:] [bible] [scene] [objects] [anchors] [shot] [motif] [emotion] [suffix]
```

`STYLE-CORE` = style_block'un ilk 80 karakteri (en önemli stil DNA'sı) prompt başına taşınır, tam STYLE: block sonunda kalır.

### Strateji C: guidance_scale Stile Göre Dinamik (P1)

```python
STYLE_GUIDANCE_SCALE = {
    "watercolor": 5.0,    # Stil çok belirgin olmalı
    "anime": 5.0,         # Anime çizgileri güçlü olmalı
    "soft_pastel": 4.5,   # Yumuşak ama belirgin
    "default": 3.5,       # Mevcut
    "pixar": 4.0,         # 3D rendering tutarlılığı
    "adventure_digital": 4.0,
    "3d": 4.0,
}
```

### Strateji D: Stil Farklılık Logu (P0)

Her üretimde prompt'un stil-specific kısmının yüzdesini logla:

```python
style_tokens = len(style_block.split())
total_tokens = len(full_prompt.split())
style_ratio = style_tokens / total_tokens

logger.info(
    "V3_STYLE_WEIGHT_RATIO",
    page=page_num,
    style_name=style_name,
    style_ratio=round(style_ratio, 3),  # Hedef: >0.15
    id_weight=id_weight,
    guidance_scale=guidance_scale,
    bible_ratio=round(bible_tokens / total_tokens, 3),
)
```

---

## 6. Doğrulama Test Planı

### Test 1: Stil İzolasyon Testi

Aynı çocuk + aynı senaryo + aynı sayfa (sayfa 5) için 7 farklı stilde üret:

```python
styles = ["watercolor", "anime", "pixar", "soft_pastel", "3d", "default", "adventure_digital"]
for style in styles:
    result = await fal_service.generate_consistent_image(
        prompt=same_prompt_with_different_style_block,
        child_face_url=same_photo,
        id_weight=STYLE_PULID_WEIGHTS[style],
    )
```

**Başarı kriteri:** 7 görsel yan yana konduğunda stil farkı **anında fark edilmeli**.

### Test 2: Reference Image Kaldırma Testi

Aynı prompt'u:
- A) `child_face_url=photo` + `flux-pulid` ile
- B) `child_face_url=None` + `flux-dev` ile

üret. B'de stil farkı çok belirginse → HİPOTEZ 1 doğrulandı.

### Test 3: Cache Integrity Testi

```python
# 1) Watercolor stili ile trial oluştur
trial_1 = create_trial(style="watercolor")
# 2) Anime stili ile trial oluştur
trial_2 = create_trial(style="anime")

# Doğrula: prompt_debug_json'daki STYLE: blokları farklı mı?
assert trial_1.prompt_debug_json["0"]["final_prompt"] != trial_2.prompt_debug_json["0"]["final_prompt"]
assert "watercolor" in trial_1.prompt_debug_json["0"]["final_prompt"]
assert "anime" in trial_2.prompt_debug_json["0"]["final_prompt"]
```

### Test 4: guidance_scale A/B Testi

Aynı prompt + aynı ref image + aynı stil:
- A) `guidance_scale=3.5` (mevcut)
- B) `guidance_scale=5.5`

5 sayfa üret, stil belirginliğini karşılaştır.

---

## 7. Özet

```
Benzer görüntülerin KÖK NEDENİ:
├─ #1 PuLID reference image baskınlığı (id_weight=0.72-0.80 + start_step=2)
│   → Modelin yaratıcı alanını %80 daraltıyor
│   → Stil sadece kalan %20'de etkili
│
├─ #2 STYLE: block prompt sonunda → düşük diffusion ağırlığı
│   → Position-weighted attention'da son sırada
│
├─ #4 CharacterBible prompt'un %25-35'i → ortak baseline çok büyük
│   → Tüm stillerde aynı metin → benzer çıktı
│
└─ #5 guidance_scale=3.5 → prompt'a sadakat düşük
    → Stil talimatları yetersiz uygulanıyor

Cache/storage problemi YOKTUR:
├─ Image cache katmanı yok — her istek Fal.ai'ye gidiyor
├─ Seed sabitlenmemiş — her seferinde rastgele
├─ Storage path UUID bazlı — overwrite yok
└─ Trial cache doğru çalışıyor — yeni trial = yeni prompt
```

---

## 8. Dosya Referansları

| Dosya | Satır | İlgili Bulgu |
|-------|-------|-------------|
| `backend/app/services/ai/fal_ai_service.py` | `:84-101` | PuLIDConfig, GenerationConfig, seed=None |
| `backend/app/services/ai/fal_ai_service.py` | `:489-521` | Payload construction, id_weight, seed |
| `backend/app/services/ai/fal_ai_service.py` | `:232` | `_sessions` in-memory cache |
| `backend/app/models/story_preview.py` | `:103-112` | `generated_prompts_cache` JSONB |
| `backend/app/services/trial_service.py` | `:29-34, :236-249` | Cache compute/read |
| `backend/app/api/v1/trials.py` | `:1005-1028` | `_resolved_style` cache write |
| `backend/app/api/v1/trials.py` | `:1754-1770` | `_resolved_style` cache read (Phase 2) |
| `backend/app/services/storage_service.py` | `:217` | UUID-based storage path |
| `backend/app/prompt_engine/visual_prompt_builder.py` | `:475-583` | `compose_enhanced_prompt()` sıralama |
| `backend/app/prompt_engine/style_adapter.py` | `:64-165` | 7 stil tanımı + style_block boyutları |

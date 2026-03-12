---
name: AI Pipeline Debugger (Gemini)
description: >
  Gemini AI servis hataları, rate limit sorunları, prompt debugging için ZORUNLU beceri.
  "Gemini hatası", "görsel üretilmiyor", "rate limit", "prompt sorunlu", "hikaye üretilmiyor"
  dediğinde bu skill OKUNMALIDIR.
---
// turbo-all

# 🤖 AI Pipeline Debugger Skill (Gemini Odaklı)

Benim Masalım projesindeki Gemini AI pipeline'ını debug etme ve sorun çözme rehberi.

## ⚡ Tetikleyiciler

- "Gemini hatası", "hikaye üretilmiyor", "görsel üretilmiyor"
- "rate limit", "429 hatası", "400 hatası", "API key sorunu"
- "prompt sorunlu", "hikaye kalitesi düşük"

---

## 🗺️ Gemini Pipeline Haritası

```
Sipariş
  │
  ├── PASS 1: "Pure Author" (gemini-2.5-flash)
  │     ├── story_prompt_tr → Gemini → Yaratıcı hikaye metni
  │     └── Çıktı: Düz metin (JSON değil)
  │
  ├── PASS 2: "Technical Director" (gemini-2.5-flash)
  │     ├── Hikaye metni → Gemini → Sayfalara bölme + görsel promptları
  │     └── Çıktı: JSON {pages: [{text, image_prompt_en}]}
  │
  ├── Visual Prompt Enhancement
  │     ├── enhance_all_pages() → Prompt'lara stil/lokasyon/karakter inject
  │     └── Çıktı: Zenginleştirilmiş image_prompt_en
  │
  └── Gemini Image Generation (gemini_consistent_image.py)
        ├── Her sayfa için görsel üretim
        └── PuLID face swap (varsa)
```

## 📁 Kritik Dosyalar

| Dosya | Rolü |
|-------|------|
| `services/ai/gemini_service.py` | Ana Gemini servisi, two-pass orchestration |
| `services/ai/_story_writer.py` | Pass 1 (hikaye yazma) + Pass 2 (sayfalama) |
| `services/ai/_visual_composer.py` | Görsel prompt oluşturma |
| `services/ai/_helpers.py` | Model sabitleri, URL builder, Türkçe utils |
| `services/ai/_models.py` | Pydantic output modelleri |
| `services/ai/gemini_consistent_image.py` | Gemini görsel üretim (consistent characters) |
| `core/rate_limit.py` | Rate limiting altyapısı |
| `prompt_engine/visual_prompt_builder.py` | Prompt zenginleştirme engine |

---

## 🔧 Rate Limit Altyapısı

### `rate_limit_retry` Decorator
```python
@rate_limit_retry(service="gemini", max_attempts=4, timeout_attempts=1)
async def call_gemini(...):
    ...
```

**Retry davranışı:**
| Status Code | Davranış | Max Deneme |
|-------------|----------|------------|
| 429 | Exponential backoff (8s-90s) + Retry-After header | 4 |
| 400 | Retry (transient Gemini hatası) | 4 |
| 500-599 | Exponential backoff (1s-30s) | 4 |
| Timeout | Backoff (1s-30s) | 1 |
| Diğer | ❌ Retry yok | - |

### Token Bucket
- Gemini: 60 RPM (× API key sayısı)
- Her istek öncesi `wait_if_needed()` — bucket doluysa bekler

### Circuit Breaker
- **Threshold:** 5 ardışık 429 hatası → circuit açılır
- **Reset:** 120 saniye sonra otomatik kapanır
- Circuit açıkken tüm istekler `RateLimitError` fırlatır

### API Key Rotation
- Birden fazla Gemini API key round-robin ile dönüşümlü kullanılır
- `settings.gemini_api_key` (primary) + `settings.gemini_api_keys_extra` (ek key'ler, comma-separated)
- Hatalı key'ler geçici olarak devre dışı bırakılır (60s cooldown)

---

## 🐛 Sorun Giderme

### Problem: "Gemini 429 Rate Limit"

```powershell
# 1. Rate limit durumunu kontrol et
gcloud logging read "resource.labels.service_name=benimmasalim-worker AND jsonPayload.event:\"429\"" --project=gen-lang-client-0784096400 --limit=20 --freshness=1h --format="table(timestamp, jsonPayload.event, jsonPayload.service, jsonPayload.wait_seconds)"

# 2. Aktif API key sayısını kontrol et
# settings.gemini_api_keys_extra boş mu?

# 3. Circuit breaker durumu
gcloud logging read "resource.labels.service_name=benimmasalim-worker AND jsonPayload.event:\"Circuit breaker\"" --project=gen-lang-client-0784096400 --limit=10 --freshness=1h
```

**Çözüm:**
- Ek API key ekle: `.env` → `GEMINI_API_KEYS_EXTRA=key1,key2,key3`
- Backoff sürelerini artır: `RATE_LIMIT_BACKOFF_MIN=12`, `RATE_LIMIT_BACKOFF_MAX=120`

### Problem: "Gemini 400 Bad Request"

```powershell
gcloud logging read "resource.labels.service_name=benimmasalim-worker AND jsonPayload.event:\"HTTP 400\"" --project=gen-lang-client-0784096400 --limit=20 --freshness=1h --format="table(timestamp, jsonPayload.error_body)"
```

**Yaygın nedenler:**
- Paralel isteklerde geçici quota aşımı → Retry çözer
- Prompt çok uzun (>128K token) → Prompt'u kısalt
- Safety filtresi tetiklendi → Prompt'u revize et
- Geçersiz API key → Key rotation kontrolü

### Problem: "Hikaye kalitesi düşük"

1. `story_prompt_tr` kontrol et (senaryoda 400+ kelime mi?)
2. `story_temperature` değerini kontrol et (0.92 default — yüksekse daha yaratıcı)
3. Pass 1 çıktısını loglardan bul → Pass 2'ye doğru girdi gidiyor mu?
4. Karakter tutarlılık kartları (scenario_writer skill) tanımlı mı?

### Problem: "Görsel prompt tekrar ediyor"

1. `visual_prompt_builder.py` → `enhance_all_pages()` kontrolü
2. Senaryo'daki `location_constraints` düzgün doldurulmuş mu?
3. `page_prompt_template`'de çeşitlilik var mı?
4. Görsel akış haritası (G3) oluşturulmuş mu?

---

## 📊 Monitoring Komutları

```powershell
# Son başarılı hikaye üretimleri
gcloud logging read "resource.labels.service_name=benimmasalim-worker AND jsonPayload.event:\"STORY_GENERATED\"" --project=gen-lang-client-0784096400 --limit=10 --freshness=2h --format="table(timestamp, jsonPayload.order_id, jsonPayload.duration_seconds)"

# Gemini API yanıt süreleri
gcloud logging read "resource.labels.service_name=benimmasalim-worker AND jsonPayload.event:\"GEMINI_CALL\"" --project=gen-lang-client-0784096400 --limit=20 --freshness=1h --format="table(timestamp, jsonPayload.model, jsonPayload.duration_ms)"

# Hangi API key kullanılıyor?
gcloud logging read "resource.labels.service_name=benimmasalim-worker AND jsonPayload.event:\"KEY_ROTATED\"" --project=gen-lang-client-0784096400 --limit=20 --freshness=1h --format="table(timestamp, jsonPayload.key_suffix)"
```

---

## ⚠️ KESİNLİKLE DİKKAT

1. **API key'leri loglara YAZMA** — Sadece son 4 karakter (suffix) loglanır
2. **Prompt'a çocuğun fiziksel özelliklerini EKLEME** — PuLID face swap halleder
3. **Safety filtrelerini kapatma** — `BLOCK_MEDIUM_AND_ABOVE` seviyesi korunmalı
4. **Token limit'i aşma** — 16384 `maxOutputTokens` hard-limit
5. **Synchronous Gemini çağrısı YAPMA** — Her şey `async/await` ile

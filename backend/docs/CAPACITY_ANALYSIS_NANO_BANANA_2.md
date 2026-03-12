# Kapasite Analizi: Nano Banana 2, Trial/Order Akışı, Tutarlılık

## 1. Mevcut Akış Özeti

### Trial (Deneme) Akışı
| Aşama | Görsel Sayısı | Açıklama |
|-------|---------------|----------|
| `trials/create` | 0 | Hikaye (Gemini) üretir, Arq ile `generate_trial_story` kuyruğa alır |
| `generate_trial_story` | 0 | Hikaye + sayfa promptları, sonra `generate_trial_preview` veya `generate_trial_composed_preview` kuyruğa alır |
| Trial preview | 3 | Cover + 2 story (veya 3 story) — ilk hızlı önizleme |
| Trial composed preview | 3 + dedication + intro | İlk 3 sayfa + karşılama 1 + karşılama 2 |
| Trial complete (remaining) | ~13–19 | Kalan story sayfaları (22 sayfalık kitap için) |

**Beklenen toplam:** cover + dedication + intro + ~19 story + back = ~22 görsel.

### "8 Fotoğraf" Durumu
- `trial_concurrency_slots = 8` → Trial background task semaphore (image sayısı DEĞİL).
- 8 görsel olması: cover + dedication + intro + 5 story = 8 — yani **trial_remaining** tamamlanmadan kesilmiş olabilir.
- Olası nedenler: semaphore timeout, job timeout, 429 rate limit cascade, worker crash.

---

## 2. Nano Banana 2 (Gemini 3.1 Flash Image) Limitleri

| Limit | Değer | Kaynak |
|-------|-------|--------|
| Model ID | `gemini-3.1-flash-image-preview` | AI Free API / Google docs |
| Input token | ~$0.25/M | Fiyatlandırma |
| Output (görsel) | ~$0.045–$0.15/görsel | Çözünürlüğe göre |
| RPM (preview) | Tier’a göre 10–60+ RPM | Düşük tier’da sıkı |
| TPM | Tier’a göre değişir | Rate limit |
| 429 oranı | ~%70 hata | Aşırı yük / limite yaklaşınca |

**Config’teki değerler:**
- `gemini_rpm_limit: 1000` (safety margin)
- `image_concurrency: 10` (job başına paralel görsel)
- `global_generation_slots: 50` → 50 job × 10 = 500 paralel Gemini çağrısı (teorik)
- 17 proje aynı API’yi paylaşıyorsa RPM hızla tükenir.

---

## 3. Tespit Edilen Darboğazlar

### 3.1 Semaphore ve Timeout
- `global_generation_slots: 50` — Redis distributed semaphore.
- `_SLOT_TIMEOUT = 1200` (20 dk) — Slot beklerken timeout.
- 6 trial aynı anda gelince 6 slot alır; kalan 44 slot diğer işlere açık.
- Sorun: Bir job 20 dk bekleyip timeout alırsa hiç çalışmadan fail olur.

### 3.2 Trial Concurrency
- `trial_concurrency_slots: 8` — Trial background task’leri için `asyncio.Semaphore(8)`.
- Bu sadece in-process; Arq worker ayrı instance’da çalıştığı için bu semaphore worker’da etkisiz.
- Arq worker `distributed_semaphore("image_gen", max_concurrent=50)` kullanıyor.

### 3.3 Job Timeout
- `image_worker.py`: job timeout 30 dakika.
- 22 sayfa × (Gemini çağrısı + compose) → tek job 5–15 dk sürebilir.
- Yoğun yük altında queue uzar, geç tamamlanan job’lar timeout’a yaklaşır.

### 3.4 429 Rate Limit
- `rate_limit_retry` decorator: max 4 deneme, 2 timeout denemesi.
- Backoff: 5–60 saniye (config: `rate_limit_backoff_min`, `rate_limit_backoff_max`).
- 17 proje aynı anda Gemini’ye gidince 429 artar; retry süresi uzar, job yavaşlar.

### 3.5 Senaryoların "Kaybolması"
- Senaryo listesi: `GET /api/v1/scenarios` — DB’den okur.
- Olası nedenler: (a) API timeout (yük altında yavaş), (b) DB connection pool tükenmesi, (c) frontend cache / error handling.
- Cloud Run 2 instance’a çıkınca DB bağlantı sayısı 2x olur; connection pool yetersiz kalabilir.

---

## 4. Önerilen Değişiklikler

### 4.1 Config (Hemen Uygulanabilir)

```python
# app/config.py
# Artır: distributed semaphore kapasitesi (17 proje paylaşımı)
global_generation_slots: int = 80  # 50 → 80

# Artır: slot bekleyebilme süresi (yük altında 20 dk yetmeyebilir)
# image_worker.py: _SLOT_TIMEOUT = 1800  # 20 dk → 30 dk

# Retry agresifliği (429 için)
rate_limit_backoff_min: int = 8   # 5 → 8
rate_limit_backoff_max: int = 90  # 60 → 90
rate_limit_circuit_threshold: int = 10  # 8 → 10 (daha geç circuit aç)
```

### 4.2 Trial Remaining — Eksik Görselleri Tamamlama
- `generate_remaining_images_inner` tamamlandıktan sonra: eksik sayfa var mı kontrol et.
- Eksik varsa `QUEUE_FAILED` veya `COMPLETING` bırakıp admin retry veya otomatik retry job’ı tetikle.
- Şu an: partial fail durumunda bazı sayfalar hiç üretilmeyebilir; tutarlı "tüm sayfalar" garantisi yok.

### 4.3 Kısmi Tamamlanma Sonrası Retry
- `trial_remaining` job sonunda: `len(generated_images)` vs beklenen sayfa sayısı.
- Eksikse: sadece eksik sayfalar için yeni Arq job kuyruğa al (idempotent).

### 4.4 API Anahtarı Rotasyonu
- `gemini_api_keys_extra` ile birden fazla anahtar kullanılıyor.
- 17 proje aynı anahtarları paylaşıyorsa RPM limiti tek noktada toplanır.
- Mümkünse proje bazlı ayrı Gemini projeleri/anahtarları; veya ortak pool’u büyüt.

### 4.5 Senaryo Listesi Dayanıklılığı
- `GET /scenarios` endpoint’i: read replica veya cache (Redis) ile hızlandırılabilir.
- DB connection pool: `sqlalchemy.pool_size` ve `max_overflow` artırılabilir (Cloud Run 2 instance için).

### 4.6 Worker Ölçeklendirme
- Arq worker sayısı: 1 worker = 1 process. Cloud Run’da worker ayrı servis.
- Worker’da `max_jobs=5` gibi düşük tutmak: aynı anda 5 job, her biri 50 slot’tan 1 alır.
- Böylece 5 × 22 = 110 görsel/job yerine daha kontrollü yük.

---

## 5. Hızlı Checklist (Tutarlılık için)

1. [ ] `global_generation_slots` 80’e çıkar.
2. [ ] `_SLOT_TIMEOUT` 1800 saniye yap.
3. [ ] `generate_remaining_images_inner` sonunda eksik sayfa kontrolü + otomatik retry.
4. [ ] 429 backoff: min 8, max 90 saniye.
5. [ ] `GET /scenarios` timeout ve connection pool incelemesi.
6. [ ] Cloud SQL / Redis connection pool (2 instance) gözden geçirme.

---

## 6. "8 Fotoğraf" İzolasyonu

Eğer sürekli 8 görsel üretiliyorsa:

1. **Log kontrolü:** `REMAINING_PAGES_COMPOSED` veya `generate_trial_remaining` log’larında `total` ve `composed` sayıları.
2. **Prompts sayısı:** `prompts_to_generate` length — beklenen sayfa sayısı (örn. 19) mı?
3. **Gemini hataları:** 429 veya timeout sonrası `generated_images` partial mı kalıyor?
4. **Worker timeout:** 30 dk’da bitmeyen job’lar `FAILED` mı oluyor?

Öneri: `generate_remaining_images_inner` içinde per-page try/except; tek sayfa fail olsa bile diğerlerini üretmeye devam et; sonunda eksik listesini logla ve (opsiyonel) retry job’ı kuyruğa al.

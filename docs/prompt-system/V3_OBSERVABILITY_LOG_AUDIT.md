# V3 Observability: Debug Log Audit

> **Tarih:** 2026-02-18  
> **Kapsam:** V3 pipeline'daki tüm log noktalarının istenen 12 alana göre denetimi

---

## 1. İstenen Log Schema vs. Mevcut Durum

| # | Alan | Mevcut? | Nerede | Eksik Nerede |
|---|------|---------|--------|-------------|
| 1 | `engine` (gemini / fal) | **KISMI** | Fal: `model=` loglanıyor; Gemini: yok | Gemini loglarında `engine=gemini` yok |
| 2 | `model_name` | **KISMI** | Gemini PASS-0/1: `model=self.story_model` ✓; Fal: `model=model_name` ✓ | `generate_story_v3` giriş logunda yok |
| 3 | `style_id` | **YOK** | Hiçbir log noktasında style UUID yok | Tüm pipeline boyunca eksik |
| 4 | `scenario_id` | **KISMI** | `V3_LOCATION_RESOLVED`: `scenario_id=` ✓ | PASS-0/1 loglarında yok, Fal loglarında yok |
| 5 | `value_id` | **YOK** | Hiçbir yerde outcome ID/name loglanmıyor | Tüm pipeline boyunca eksik |
| 6 | `child_id` / `order_id` / `page_idx` | **KISMI** | Fal: `order_id=`, `page_index=` ✓; Gemini: yok | PASS-0/1'de `order_id` yok, `child_id` hiçbir yerde yok |
| 7 | `prompt_hash` | **KISMI** | Fal manifest: `prompt_hash=sha256[:16]` ✓ | Gemini PASS-0/1 inputları için yok, V3_PAGE_PIPELINE_STATS'ta yok |
| 8 | `prompt_length` | **VAR** ✓ | `V3_PAGE_PIPELINE_STATS.prompt_length` ✓, `FINAL_PROMPT_SENT_TO_FAL.prompt_length` ✓ | Gemini input prompt uzunluğu yok |
| 9 | `reference_image_used` | **KISMI** | Fal: `has_face_ref=bool(child_face_url)` ✓ | Gemini: yok (ama Gemini'ye zaten gitmez) |
| 10 | `response_time` | **YOK** ⚠️ | Ne Gemini ne Fal çağrısında süresi ölçülüyor | Tüm API çağrılarında eksik |
| 11 | `retry_count` | **KISMI** | PASS-0/1: `attempt=` loglanıyor ✓; Fal queue: `polls=` ✓ | Son retry sayısı toplam olarak loglanmıyor |
| 12 | `error_code` | **KISMI** | 429 tespiti var; `_check_fal_response` HTTP code kontrol ediyor | Log'a `error_code=` alanı yazılmıyor |

### Özet Skor: **12 alandan 2 tam, 7 kısmi, 3 tamamen eksik**

---

## 2. Detaylı Log Noktası Haritası

### 2.1 Gemini Service — `gemini_service.py`

| Log Event | Satır | Mevcut Alanlar | Eksik Alanlar |
|-----------|-------|----------------|---------------|
| `"Starting V3 BLUEPRINT story generation"` | `:2512` | `scenario`, `child_name`, `page_count`, `magic_items` | `engine`, `model_name`, `style_id`, `scenario_id`, `value_id`, `order_id` |
| `"V3_LOCATION_RESOLVED"` | `:2525` | `scenario_id`, `scenario_name`, `location_key`, `location_display_name` | `engine`, `order_id` |
| `"PASS-0: Generating blueprint"` | `:2248` | `model`, `page_count`, `location`, `attempt` | `engine`, `style_id`, `scenario_id`, `order_id`, `prompt_length` |
| `"PASS-0: Blueprint page count mismatch"` | `:2285` | `expected`, `got`, `attempt` | `engine`, `order_id` |
| `"PASS-1: Generating story pages"` | `:2387` | `model`, `page_count`, `attempt` | `engine`, `style_id`, `scenario_id`, `value_id`, `order_id`, `prompt_length` |
| `"V3 auto-fixer applied corrections"` | `:2586` | `fixes` | `engine`, `order_id` |
| `"V3_PAGE_PIPELINE_STATS"` | `:2804` | `page_index`, `story_page_number`, `page_type`, `composer_version`, `v3_composed`, `skip_compose`, `prompt_length`, `negative_length`, `has_style_block` | `engine`, `style_id`, `scenario_id`, `order_id`, `prompt_hash`, `value_id` |
| `"V3_COVER_GENERATED"` | `:2718` | `page_index`, `page_type`, `composer_version`, `COVER_PROMPT_LENGTH`, `COVER_HAS_STYLE_BLOCK` | `engine`, `style_id`, `order_id` |
| `"V3 prompt truncated to Fal limit"` | `:2797` | `page`, `original_length`, `truncated_length` | `engine`, `order_id`, `style_block_lost` |

### 2.2 Fal AI Service — `fal_ai_service.py`

| Log Event | Satır | Mevcut Alanlar | Eksik Alanlar |
|-----------|-------|----------------|---------------|
| `"ID_WEIGHT_RESOLVED"` | `:352` | `id_weight`, `source`, `style_modifier_first60` | `engine`, `style_id`, `order_id`, `page_idx` |
| `"FAL_GENERATE_INPUT_DEBUG"` | `:367` | `style_modifier_first80`, `has_style_negative`, `has_leading_prefix_override`, `has_style_block_override` | `engine`, `style_id`, `order_id`, `page_idx` |
| `"V3_SKIP_COMPOSE_PROMPT_STATS"` | `:398` | `prompt_length`, `negative_length`, `has_style_block`, `is_cover` | `engine`, `style_id`, `order_id`, `page_idx` |
| `"FINAL_PROMPT_SENT_TO_FAL"` | `:456` | `prompt_first_400`, `prompt_length`, `is_cover`, `model`, `num_inference_steps`, `guidance_scale`, `image_width`, `image_height`, `id_weight`, `page_index`, `preview_id`, `order_id` | `engine`, `style_id`, `scenario_id`, `prompt_hash` |
| `"PROMPT_DEBUG"` | `:472` | `page_index`, `book_id`, `order_id`, `is_cover`, `skip_compose`, `style_key`, `width` | `engine`, `style_id`, `scenario_id`, `prompt_hash`, `value_id` |
| `"Generating image with PuLID face consistency"` | `:446` | `prompt_preview`, `prompt_length`, `has_face_ref`, `id_weight`, `style_detected`, `is_cover` | `engine`, `style_id`, `order_id`, `page_idx`, `response_time` |
| `"Job submitted to queue"` | `:1139` | `request_id`, `status_url`, `result_url` | `engine`, `order_id`, `page_idx` |
| `"Queue job completed"` | `:1179` | `request_id`, `polls`, `elapsed_approx` | `engine`, `order_id`, `page_idx`, `response_time_ms` (gerçek) |

### 2.3 Generate Book Task — `generate_book.py`

| Log Event | Satır | Mevcut Alanlar | Eksik Alanlar |
|-----------|-------|----------------|---------------|
| `"Starting book generation"` | `:137` | `order_id`, `existing_pages` | `engine`, `style_id`, `scenario_id`, `value_id`, `model_name` |
| `"Generating page with PuLID face consistency"` | `:294` | `page`, `scene_preview`, `has_face_ref` | `engine`, `style_id`, `order_id`, `prompt_hash`, `response_time` |
| `"Page generated with PuLID"` | `:399` | `order_id`, `page`, `is_cover` | `engine`, `response_time`, `prompt_hash` |
| `"BUILD_REPORT"` | `:558` | `used_version`, `order_id`, `total_pages`, `total_duration_seconds`, `pdf_url`, `has_audio` | `style_id`, `scenario_id`, `value_id`, `model_name` |

### 2.4 Request Logging Middleware — `request_logging.py`

| Log Event | Satır | Mevcut Alanlar |
|-----------|-------|----------------|
| `"request_finished"` | `:109` | `method`, `path`, `status_code`, `duration_ms` ✓ |

Bu middleware HTTP endpoint seviyesinde süre ölçüyor — **API endpoint süresi var, ama alt servis (Gemini/Fal) süresi yok.**

---

## 3. Kritik Eksiklikler — Öncelik Sırası

### P0 — Hemen Eklenmeli

| Eksik | Neden Kritik | Etki |
|-------|-------------|------|
| **`response_time`** (Gemini + Fal) | Yavaşlık kaynağı teşhis edilemiyor | Performans debug imkansız |
| **`style_id`** | Stil kaynaklı sorunlar izlenemez | "Stil etkisiz" bug'ı trace edilemez |
| **`order_id`** (Gemini PASS-0/1) | Hata hangi siparişe ait bilinmiyor | Production hata takibi imkansız |
| **`error_code`** | 429 / 500 / timeout ayrımı yapılamıyor | Rate limit vs. server error ayrımı yok |

### P1 — 1 Hafta İçinde

| Eksik | Neden Gerekli |
|-------|--------------|
| **`value_id`** (outcome name/id) | Değer enjeksiyonu debug — motif eksik mi? |
| **`prompt_hash`** (V3_PAGE_PIPELINE_STATS) | Aynı prompt tekrar mı gönderiliyor trace'i |
| **`engine=gemini\|fal`** | Log aggregation'da servis bazlı filtreleme |
| **`scenario_id`** (PASS-0/1, Fal) | Senaryo bazlı hata paterni tespiti |

### P2 — 1 Ay İçinde

| Eksik | Neden Gerekli |
|-------|--------------|
| **`child_id`** | Çocuk bazlı tutarlılık analizi |
| **Gemini input prompt_length** | PASS-0/1 prompt boyutu izleme |
| **`retry_count` (toplam)** | Son başarılı denemede kaç retry oldu? |

---

## 4. Önerilen Log Schema

### 4.1 Birleşik (Canonical) Log Schema

Her V3 pipeline adımında şu alanlar **zorunlu** olmalı:

```python
@dataclass
class V3LogContext:
    """Canonical context for all V3 pipeline log events."""
    engine: str                    # "gemini" | "fal" | "storage"
    model_name: str                # "gemini-2.0-flash" | "fal-ai/flux-pulid"
    order_id: str | None           # UUID — sipariş izleme
    preview_id: str | None         # UUID — trial/preview izleme
    style_id: str | None           # UUID — stil izleme
    style_name: str | None         # "watercolor" | "anime" — okunabilirlik
    scenario_id: str | None        # UUID — senaryo izleme
    scenario_name: str | None      # "Kapadokya" — okunabilirlik
    value_id: str | None           # outcome name: "cesaret" | "özgüven"
    page_idx: int | None           # 0=cover, 1..N=inner
    child_name: str | None         # PII: sadece first name (hash'lenebilir)
```

### 4.2 Gemini-Specific Log Events

```python
# PASS-0 giriş
logger.info(
    "V3_PASS0_START",
    engine="gemini",
    model_name=self.story_model,
    order_id=order_id,
    scenario_id=str(scenario.id),
    scenario_name=scenario.name,
    style_name=visual_style,
    page_count=page_count,
    prompt_length=len(full_prompt),
    prompt_hash=hashlib.sha256(full_prompt.encode()).hexdigest()[:16],
)

# PASS-0 tamamlanma
logger.info(
    "V3_PASS0_COMPLETE",
    engine="gemini",
    model_name=self.story_model,
    order_id=order_id,
    response_time_ms=round((time.monotonic() - t0) * 1000),
    blueprint_pages=len(blueprint.get("pages", [])),
    retry_count=attempt,
)

# PASS-1 giriş
logger.info(
    "V3_PASS1_START",
    engine="gemini",
    model_name=self.story_model,
    order_id=order_id,
    scenario_id=str(scenario.id),
    style_name=visual_style,
    value_id=value_message_tr[:50] if value_message_tr else None,
    page_count=page_count,
    prompt_length=len(full_prompt),
)

# PASS-1 tamamlanma
logger.info(
    "V3_PASS1_COMPLETE",
    engine="gemini",
    model_name=self.story_model,
    order_id=order_id,
    response_time_ms=round((time.monotonic() - t0) * 1000),
    pages_generated=len(pages),
    retry_count=attempt,
)
```

### 4.3 Fal-Specific Log Events

```python
# Görsel üretim isteği
logger.info(
    "V3_FAL_GENERATE_START",
    engine="fal",
    model_name=model_name,
    order_id=order_id,
    preview_id=preview_id,
    style_id=style_id,
    style_name=style_name,
    scenario_id=scenario_id,
    page_idx=page_number,
    prompt_length=len(full_prompt),
    prompt_hash=hashlib.sha256(full_prompt.encode()).hexdigest()[:16],
    negative_length=len(full_negative),
    reference_image_used=bool(child_face_url),
    id_weight=id_weight,
    guidance_scale=self.generation_config.guidance_scale,
    has_style_block="STYLE:" in full_prompt,
)

# Görsel üretim tamamlanma
logger.info(
    "V3_FAL_GENERATE_COMPLETE",
    engine="fal",
    model_name=model_name,
    order_id=order_id,
    page_idx=page_number,
    response_time_ms=round((time.monotonic() - t0) * 1000),
    queue_polls=polls,
    image_url_prefix=image_url[:60],
)

# Hata durumu
logger.error(
    "V3_FAL_GENERATE_ERROR",
    engine="fal",
    model_name=model_name,
    order_id=order_id,
    page_idx=page_number,
    error_code=getattr(exc, "response", {}).status_code if hasattr(exc, "response") else None,
    error_message=str(exc)[:200],
    retry_count=rate_limit_attempts,
    response_time_ms=round((time.monotonic() - t0) * 1000),
)
```

### 4.4 V3_PAGE_PIPELINE_STATS (Genişletilmiş)

```python
logger.info(
    "V3_PAGE_PIPELINE_STATS",
    # Mevcut alanlar (korunuyor)
    page_index=current_page_index,
    story_page_number=llm_page_num,
    page_type=page_type,
    composer_version="v3",
    v3_composed=True,
    skip_compose=True,
    prompt_length=len(final_prompt),
    negative_length=len(negative_prompt_en),
    has_style_block=has_style_block,
    # YENİ alanlar
    engine="gemini",
    order_id=order_id,
    style_id=style_id,
    style_name=visual_style,
    scenario_id=str(scenario.id),
    value_id=value_visual_motif[:30] if value_visual_motif else None,
    prompt_hash=hashlib.sha256(final_prompt.encode()).hexdigest()[:16],
    truncated=len(final_prompt) < original_len if original_len else False,
)
```

---

## 5. Ekleme Noktaları (Dosya:Satır)

### 5.1 `response_time` Ekleme

| Dosya | Satır | Değişiklik |
|-------|-------|-----------|
| `gemini_service.py:2246` | PASS-0 retry loop öncesi | `t0 = time.monotonic()` ekle |
| `gemini_service.py:2278` | PASS-0 response sonrası | `response_time_ms=round((time.monotonic() - t0) * 1000)` logla |
| `gemini_service.py:2385` | PASS-1 retry loop öncesi | `t0 = time.monotonic()` ekle |
| `gemini_service.py:2413` | PASS-1 response sonrası | `response_time_ms` logla |
| `fal_ai_service.py:488` | `generate_consistent_image` payload build öncesi | `t0 = time.monotonic()` ekle |
| `fal_ai_service.py:525-527` | generate sonrası | `response_time_ms` logla |

### 5.2 `style_id` Ekleme

`generate_story_v3` fonksiyonuna `style_id: str | None = None` parametresi ekle ve tüm iç log noktalarına yay.

| Dosya | Satır | Değişiklik |
|-------|-------|-----------|
| `gemini_service.py:2479` | `generate_story_v3` imzası | `style_id: str | None = None` parametre ekle |
| `gemini_service.py:2512` | Giriş logu | `style_id=style_id` ekle |
| `gemini_service.py:2804` | `V3_PAGE_PIPELINE_STATS` | `style_id=style_id` ekle |
| `fal_ai_service.py:252` | `generate_consistent_image` imzası | `style_id: str | None = None` parametre ekle |
| `fal_ai_service.py:456` | `FINAL_PROMPT_SENT_TO_FAL` | `style_id=style_id` ekle |
| `trials.py` (çağrı noktaları) | `generate_story_v3()` çağrıları | `style_id=str(vs.id)` geçir |

### 5.3 `order_id` Ekleme (Gemini)

`generate_story_v3` → `_pass0_generate_blueprint` → `_pass1_generate_pages` zincirine `order_id` yayılmalı.

| Dosya | Satır | Değişiklik |
|-------|-------|-----------|
| `gemini_service.py:2479` | `generate_story_v3` imzası | `order_id: str | None = None` parametre ekle |
| `gemini_service.py:2200` | `_pass0_generate_blueprint` imzası | `order_id: str | None = None` ekle |
| `gemini_service.py:2333` | `_pass1_generate_pages` imzası | `order_id: str | None = None` ekle |
| Tüm iç log'lar | | `order_id=order_id` ekle |

### 5.4 `error_code` Ekleme

| Dosya | Satır | Değişiklik |
|-------|-------|-----------|
| `gemini_service.py:1376` | PASS-1 HTTP error | `error_code=e.response.status_code` ekle |
| `gemini_service.py:2310` | PASS-0 429 handler | `error_code=429` ekle |
| `fal_ai_service.py:1192` | Queue FAILED | `error_code="QUEUE_FAILED"` ekle |
| `rate_limit.py:335` | Rate limit exhausted | `error_code=429` ekle |

### 5.5 `value_id` Ekleme

| Dosya | Satır | Değişiklik |
|-------|-------|-----------|
| `gemini_service.py:2512` | V3 giriş | `value_names=[o.name for o in outcomes]` ekle |
| `gemini_service.py:2804` | `V3_PAGE_PIPELINE_STATS` | `value_motif=value_visual_motif[:40]` ekle |
| `fal_ai_service.py:472` | `PROMPT_DEBUG` | `value_id=value_name` ekle (parametre olarak al) |

---

## 6. Mevcut İyi Loglar (Korunmalı)

Aşağıdaki log noktaları **iyi tasarlanmış** ve korunmalı:

| Log Event | Değerlendirme |
|-----------|--------------|
| `FINAL_PROMPT_SENT_TO_FAL` | ✓ İyi — `prompt_first_400` debug'a çok yararlı |
| `PROMPT_DEBUG` | ✓ İyi — page-level observability |
| `V3_PAGE_PIPELINE_STATS` | ✓ İyi — prompt_length + has_style_block |
| `V3_SKIP_COMPOSE_PROMPT_STATS` | ✓ İyi — Fal'a giden son hali |
| `ID_WEIGHT_RESOLVED` | ✓ İyi — PuLID debug |
| `BUILD_REPORT` | ✓ İyi — sipariş sonu özet |
| Request middleware `duration_ms` | ✓ İyi — HTTP seviye süre |

---

## 7. Uygulama Planı

### Sprint 1 (P0 — 2 saat)

```
1. response_time ekleme (4 nokta × 3 satır = ~12 satır)
   - gemini PASS-0: t0 + log
   - gemini PASS-1: t0 + log
   - fal generate_consistent_image: t0 + log
   - fal _generate_with_queue: gerçek elapsed (poll*interval yerine time.monotonic)

2. order_id propagation (gemini_service.py)
   - generate_story_v3 → _pass0 → _pass1 parametre zinciri
   - Tüm iç log'lara order_id= ekle

3. error_code ekleme (4 nokta × 1 satır)
   - HTTPStatusError handler'larına error_code=status_code

4. style_id log ekleme
   - V3_PAGE_PIPELINE_STATS, V3_COVER_GENERATED, FINAL_PROMPT_SENT_TO_FAL
```

### Sprint 2 (P1 — 1 saat)

```
5. value_id (outcome) log ekleme
   - V3 giriş + PAGE_STATS + PROMPT_DEBUG

6. prompt_hash ekleme
   - V3_PAGE_PIPELINE_STATS'a sha256[:16]

7. engine= prefix ekleme
   - Tüm Gemini loglarına engine="gemini"
   - Tüm Fal loglarına engine="fal"

8. scenario_id propagation
   - PASS-0/1 loglarına + Fal loglarına
```

### Sprint 3 (P2 — 30 dk)

```
9. Gemini input prompt_length logu
10. retry_count toplam logu (final success'te)
11. child_id (hash) PII-safe loglama
```

---

## 8. Structlog Bind Pattern (Önerilen)

Her request başında context'i bir kez bağla, tüm alt fonksiyonlarda otomatik taşınsın:

```python
# gemini_service.py — generate_story_v3 girişi
import structlog
log = structlog.get_logger().bind(
    engine="gemini",
    order_id=order_id,
    style_id=style_id,
    scenario_id=str(scenario.id),
    scenario_name=scenario.name,
    value_names=[o.name for o in outcomes],
    model_name=self.story_model,
)

# Sonraki tüm log çağrılarında bu alanlar otomatik eklenir:
log.info("V3_PASS0_START", page_count=page_count)
# → {"event": "V3_PASS0_START", "engine": "gemini", "order_id": "...", "page_count": 16, ...}
```

```python
# fal_ai_service.py — generate_consistent_image girişi
log = structlog.get_logger().bind(
    engine="fal",
    order_id=order_id,
    preview_id=preview_id,
    style_id=style_id,
    page_idx=page_number,
    model_name=model_name,
)
```

Bu pattern ile **her alt fonksiyona parametre geçirmeye gerek kalmaz** — structlog context'i thread-local taşır.

---

## 9. Dosya Referansları

| Dosya | İlgili Satırlar | Rol |
|-------|----------------|-----|
| `backend/app/services/ai/gemini_service.py` | `:2248, :2387, :2512, :2804` | Gemini PASS-0/1 logları |
| `backend/app/services/ai/fal_ai_service.py` | `:352, :398, :446, :456, :472, :1139, :1179` | Fal logları |
| `backend/app/tasks/generate_book.py` | `:73, :137, :294, :399, :558` | Book generation task logları |
| `backend/app/core/rate_limit.py` | `:272-340` | Retry decorator (retry_count kaynağı) |
| `backend/app/middleware/request_logging.py` | `:81-114` | HTTP request süre logu |
| `backend/app/api/v1/trials.py` | `:456-527, :886-1038` | Trial generation çağrı noktaları |

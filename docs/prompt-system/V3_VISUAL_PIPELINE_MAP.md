# V3 Görsel Pipeline Haritası

> Son güncelleme: 2026-02-17

---

## Executive Summary

V3 pipeline, kullanıcı UI seçimlerinden başlayarak 3 aşamalı bir Gemini LLM çağrısı (PASS-0 Blueprint + PASS-1 Pages) ile hikaye metni + görsel promptları üretir, ardından deterministik post-LLM prompt enhancement (CharacterBible + SceneDirector + StyleAdapter + VisualBeat) uygular, Fal.ai Flux-PuLID ile görsel üretir ve GCS'ye yazar.

---

## 1. Uçtan Uca Akış Diyagramı

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           UI (Frontend)                                 │
│  child_name, child_age, child_gender, child_photo_url,                 │
│  scenario_name, learning_outcomes[], visual_style, magic_items[]        │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │ POST /api/v1/trials/create
                                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│              API Endpoint: trials.py → CreateTrialRequest               │
│  File: backend/app/api/v1/trials.py:179                                │
│  - DB'den Scenario, LearningOutcome, VisualStyle resolve edilir        │
│  - page_count: Product.default_page_count veya 16                      │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│         gemini_service.generate_story_structured()                       │
│  File: backend/app/services/ai/gemini_service.py:2887                   │
│  - requested_version="v3" → generate_story_v3() çağrılır               │
│  - V2 artık bloklanmış (AIServiceError)                                │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │
             ┌───────────────────┼───────────────────┐
             ▼                                       ▼
┌──────────────────────────┐         ┌──────────────────────────────────┐
│  PASS-0: Blueprint       │         │  (10s rate-limit buffer)         │
│  _pass0_generate_blueprint│         │                                  │
│  Line: 2192              │         │                                  │
│                          │         │                                  │
│  Gemini API:             │         │                                  │
│  ├─ Model: gemini-2.0-   │         │                                  │
│  │  flash (configurable) │         │                                  │
│  ├─ temp: 0.7            │         │                                  │
│  ├─ topK: 40             │         │                                  │
│  ├─ topP: 0.90           │         │                                  │
│  ├─ maxOutputTokens:     │         │                                  │
│  │  16000                │         │                                  │
│  ├─ responseMimeType:    │         │                                  │
│  │  application/json     │         │                                  │
│  └─ safetySettings:      │         │                                  │
│     BLOCK_MEDIUM_AND_    │         │                                  │
│     ABOVE (4 category)   │         │                                  │
│                          │         │                                  │
│  Output: Blueprint JSON  │         │                                  │
│  (title, pages[], side_  │         │                                  │
│  character, cultural_    │         │                                  │
│  facts_used)             │         │                                  │
└────────────┬─────────────┘         └──────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  PASS-1: Story Pages                                                    │
│  _pass1_generate_pages()                                                │
│  File: gemini_service.py:2333                                           │
│                                                                         │
│  Gemini API:                                                            │
│  ├─ Model: gemini-2.0-flash (configurable via gemini_story_model)       │
│  ├─ temperature: self.story_temperature                                 │
│  ├─ topK: 64                                                            │
│  ├─ topP: 0.95                                                          │
│  ├─ maxOutputTokens: 32000                                              │
│  ├─ responseMimeType: application/json                                  │
│  └─ safetySettings: BLOCK_MEDIUM_AND_ABOVE (4 category)                 │
│                                                                         │
│  Input: blueprint JSON + child_name/age/description + visual_style      │
│         + value_message_tr (eğitim değeri enjeksiyonu)                   │
│  Output: pages[] → her sayfa: text_tr, image_prompt_en,                 │
│          negative_prompt_en                                              │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  VALIDATION + AUTO-FIX                                                  │
│  File: backend/app/prompt_engine/story_validators.py                    │
│  - validate_story_output() → magic item count, cultural fact            │
│    uniqueness, safety, family ban                                       │
│  - apply_all_fixes() → auto-correct minor issues                        │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  VISUAL PROMPT ENHANCEMENT (Deterministic — no LLM call)                │
│  File: backend/app/prompt_engine/visual_prompt_builder.py               │
│                                                                         │
│  enhance_all_pages() :673                                               │
│  Her sayfa için:                                                        │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │ compose_enhanced_prompt() :475                                   │    │
│  │                                                                  │    │
│  │ Assembly order (diffusion weight, yüksek→düşük):                 │    │
│  │  1. style_anchor (2-3 kelime)                                    │    │
│  │  2. character_bible.prompt_block (identity + outfit_lock)        │    │
│  │  3. Scene description (LLM cleaned + kids-safe rewrite)          │    │
│  │  4. Key objects (TR→EN çeviri, story text'ten)                   │    │
│  │  5. Iconic anchor elements (lokasyona özgü)                      │    │
│  │  6. Camera/composition (SceneDirector shot_plan)                 │    │
│  │  7. value_visual_motif (eğitim değeri görseli)                   │    │
│  │  8. Emotion (çocuğun ifadesi)                                    │    │
│  │  9. STYLE: block (tam stil açıklaması)                           │    │
│  │ 10. Safety suffix: "no text, no watermark, no logo"              │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                         │
│  build_enhanced_negative() :619                                         │
│  → GLOBAL_NEGATIVE + character_bible.negative_tokens                    │
│    + style.forbidden_terms + gender negatives                           │
│    + text-blocking tokens                                               │
│                                                                         │
│  Post-processing:                                                       │
│  - _kids_safe_rewrite() → şiddet/korku → çocuk dostu alternatif         │
│  - _strip_embedded_text() → quoted text → glowing symbol                │
│  - _remove_shot_conflict() → close-up + full body çelişkisi             │
│  - _sanitize_v3_prompt_text() → broken fragment temizliği               │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  VISUAL PROMPT VALIDATION + AUTO-FIX                                    │
│  File: backend/app/prompt_engine/visual_prompt_validator.py             │
│  validate_all() → shot conflict, value motif, character identity check  │
│  autofix() → otomatik düzeltme                                          │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  COVER PROMPT ÜRETİMİ                                                   │
│  File: visual_prompt_builder.py → build_cover_prompt()                  │
│  - character_bible + style + location anchors + title context           │
│  - value_visual_motif eklenir                                           │
│  - Ayrı cover_negative üretilir                                         │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  FinalPageContent[] oluşturulur (gemini_service.py:2734-2828)           │
│  Her sayfa:                                                             │
│  ├─ visual_prompt = final_prompt (enhanced image_prompt_en)             │
│  ├─ negative_prompt = enhanced negative                                 │
│  ├─ v3_composed = True   ← downstream'de re-compose atlanır            │
│  ├─ pipeline_version = "v3"                                             │
│  └─ composer_version = "v3"                                             │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  trials.py → Sayfa verileri API response'a yazılır                      │
│  Background task başlar → generate_preview (3 preview image)            │
│  VEYA                                                                   │
│  generate_book.py → Ödeme sonrası tüm sayfalar generate edilir          │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  IMAGE GENERATION (Fal.ai / Gemini Dispatch)                            │
│                                                                         │
│  image_provider_dispatch.py:25                                          │
│  get_image_provider_for_generation(provider_name)                       │
│  ├─ "fal" → FalAIService (singleton)                                    │
│  └─ "gemini" / "gemini_flash" → GeminiConsistentImageService            │
│                                                                         │
│  Ana çağrı: generate_consistent_image()                                 │
│  File: fal_ai_service.py:252                                            │
│                                                                         │
│  V3 path (skip_compose=True):                                           │
│  ├─ prompt zaten compose edilmiş → re-compose YOK                       │
│  ├─ Sadece length guard + gender negatives (V2 legacy path'te)          │
│  └─ precomposed_negative doğrudan kullanılır                            │
│                                                                         │
│  Model seçimi (fal_ai_service.py:455-517):                              │
│  ├─ child_face_url VAR → FalModel.FLUX_PULID ("fal-ai/flux-pulid")     │
│  └─ child_face_url YOK → FalModel.FLUX_DEV ("fal-ai/flux/dev")         │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │ FAL.AI PAYLOAD (fal_ai_service.py:492-521)                      │    │
│  │                                                                  │    │
│  │ {                                                                │    │
│  │   "prompt": final_prompt,           // enhanced V3 prompt        │    │
│  │   "negative_prompt": full_negative, // enhanced V3 negative      │    │
│  │   "image_size": {                                                │    │
│  │     "width": 1024,   // default, override by template            │    │
│  │     "height": 724    // yatay A4 (1024/724 ≈ landscape)         │    │
│  │   },                                                             │    │
│  │   "num_inference_steps": 28,        // GenerationConfig          │    │
│  │   "guidance_scale": 3.5,            // prompt adherence          │    │
│  │   "max_sequence_length": 512,       // KRITIK: 128→512           │    │
│  │                                                                  │    │
│  │   // PuLID (sadece child_face_url varsa):                        │    │
│  │   "reference_image_url": child_face_url,                         │    │
│  │   "id_weight": 0.72-0.80,          // stile göre auto-detect     │    │
│  │   "start_step": 2,                 // erken yüz enjeksiyonu      │    │
│  │   "true_cfg": 1.0,                 // prompt + face balance      │    │
│  │                                                                  │    │
│  │   // Opsiyonel:                                                  │    │
│  │   "seed": int | null               // reproducibility            │    │
│  │ }                                                                │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                         │
│  Gönderim: _generate_with_queue() (varsayılan, güvenilir)               │
│  ├─ POST https://queue.fal.run/{model} → request_id                     │
│  ├─ Poll: GET status_url (2s interval, max 150 poll = 5 min)            │
│  ├─ COMPLETED → GET response_url → result JSON                          │
│  └─ Alternatif: _generate_direct() → POST https://fal.run/{model}      │
│                                                                         │
│  Response format:                                                       │
│  _extract_image_url() :1219                                             │
│  ├─ data["images"][0]["url"]    (ana format)                            │
│  ├─ data["image"]["url"]        (alternatif)                            │
│  └─ data["output"]["url"]       (alternatif)                            │
│  → Dönen: Fal CDN URL (https://fal.media/files/...)                     │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  POST-GENERATION: Upscale + Resize + Storage                            │
│  File: backend/app/tasks/generate_book.py:340-390                       │
│                                                                         │
│  1. Fal CDN'den image_bytes indirilir (httpx GET)                       │
│  2. Upscale (opsiyonel):                                                │
│     ├─ Model: FalModel.REAL_ESRGAN ("fal-ai/real-esrgan")              │
│     └─ Factor: 2x veya 4x (template'e göre)                            │
│  3. Resize: resize_image_bytes_to_target() → baskı hedef boyutu         │
│  4. GCS Upload:                                                         │
│     storage.upload_generated_image()                                    │
│     File: storage_service.py:211                                        │
│     → blob: "books/{order_id}/pages/page_{page_number}.png"             │
│     → URL:  https://storage.googleapis.com/{BUCKET}/books/...           │
│  5. DB Update:                                                          │
│     OrderPage.image_url = final_url                                     │
│     OrderPage.image_generation_status = "completed"                     │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  DB KAYIT: OrderPage modeli                                             │
│  File: backend/app/models/order_page.py                                 │
│  Tablo: order_pages                                                     │
│                                                                         │
│  ├─ image_prompt: Text       → Gemini'nin ürettiği visual prompt        │
│  ├─ image_url: Text          → GCS URL (final görsel)                   │
│  ├─ preview_image_url: Text  → düşük kalite önizleme                    │
│  ├─ negative_prompt: Text    → V3 pre-composed negative                 │
│  ├─ v3_composed: Boolean     → True = skip_compose                      │
│  ├─ pipeline_version: "v3"                                              │
│  └─ status: PENDING → PREVIEW_GENERATED → FULL_GENERATED               │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 2. final_prompt / negative_prompt Üretim Noktaları

### 2.1 final_prompt (image_prompt_en)

| Aşama | Dosya | Fonksiyon | Açıklama |
|-------|-------|-----------|----------|
| **LLM Raw** | `gemini_service.py:2333` | `_pass1_generate_pages()` | Gemini JSON → `image_prompt_en` (ham prompt) |
| **Enhancement** | `visual_prompt_builder.py:475` | `compose_enhanced_prompt()` | CharacterBible + SceneDirector + StyleAdapter + Safety |
| **Cover** | `visual_prompt_builder.py` | `build_cover_prompt()` | Kapak sayfası için ayrı compose |
| **Truncation** | `gemini_service.py:2794` | `generate_story_v3()` | `MAX_FAL_PROMPT_CHARS` guard |
| **V3 skip** | `fal_ai_service.py:381` | `generate_consistent_image()` | `skip_compose=True` → re-compose yok, direkt Fal'a |

### 2.2 negative_prompt

| Aşama | Dosya | Fonksiyon | Açıklama |
|-------|-------|-----------|----------|
| **LLM Default** | `gemini_service.py:2450` | `_pass1_generate_pages()` | Gemini'nin ürettiği veya fallback negative |
| **V3 Build** | `visual_prompt_builder.py:619` | `build_enhanced_negative()` | GLOBAL + character + style + gender + text-blocking |
| **V3 skip** | `fal_ai_service.py:385` | `generate_consistent_image()` | `precomposed_negative` direkt kullanılır |

---

## 3. Gemini API Çağrı Parametreleri

### 3.1 PASS-0: Blueprint

```
Endpoint : https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent
Model    : settings.gemini_story_model veya "gemini-2.0-flash"
Auth     : ?key={GEMINI_API_KEY}

generationConfig:
  temperature      : 0.7
  topK             : 40
  topP             : 0.90
  maxOutputTokens  : 16000
  responseMimeType : "application/json"

safetySettings: (4 kategori, hepsi BLOCK_MEDIUM_AND_ABOVE)
  - HARM_CATEGORY_HARASSMENT
  - HARM_CATEGORY_DANGEROUS_CONTENT
  - HARM_CATEGORY_SEXUALLY_EXPLICIT
  - HARM_CATEGORY_HATE_SPEECH

Seed     : YOK (Gemini text API'de seed parametresi yok)
Steps    : N/A (text generation)
```

**Kaynak:** `gemini_service.py:2259-2274`

### 3.2 PASS-1: Story Pages

```
Endpoint : Aynı (generativelanguage.googleapis.com)
Model    : Aynı (gemini-2.0-flash)

generationConfig:
  temperature      : self.story_temperature (dinamik)
  topK             : 64
  topP             : 0.95
  maxOutputTokens  : 32000
  responseMimeType : "application/json"

safetySettings: Aynı 4 kategori
```

**Kaynak:** `gemini_service.py:2397-2412`

---

## 4. Fal.ai Görsel Üretim Parametreleri

### 4.1 Model Seçimi

| Koşul | Model | Fal Endpoint |
|-------|-------|-------------|
| `child_face_url` mevcut | `fal-ai/flux-pulid` | PuLID yüz korumalı |
| `child_face_url` yok | `fal-ai/flux/dev` | Standart Flux |
| Upscale | `fal-ai/real-esrgan` | Süper çözünürlük |

### 4.2 Tam Parametre Tablosu

| Parametre | Değer | Kaynak | Not |
|-----------|-------|--------|-----|
| `prompt` | final_prompt (V3 enhanced) | compose_enhanced_prompt() | Max ~2000 char |
| `negative_prompt` | build_enhanced_negative() | visual_prompt_builder.py | Dedup'lanmış |
| `image_size.width` | 1024 (varsayılan) | GenerationConfig / template | A4 landscape |
| `image_size.height` | 724 (varsayılan) | GenerationConfig / template | 1024/724 ≈ 1.41 |
| `num_inference_steps` | 28 | GenerationConfig | Kalite/hız dengesi |
| `guidance_scale` | 3.5 | GenerationConfig | Prompt bağlılığı |
| `max_sequence_length` | 512 | Hardcoded | Varsayılan 128 → 512 (uzun prompt) |
| `seed` | null veya int | GenerationConfig | Reproducibility |
| `reference_image_url` | child_face_url | Order.child_photo_url | PuLID yüz ref |
| `id_weight` | 0.72 - 0.80 | Style-based auto / DB | Yüz kimlik ağırlığı |
| `start_step` | 2 | PuLIDConfig | Erken yüz enjeksiyonu |
| `true_cfg` | 1.0 | Hardcoded | CFG loss weight |

**Kaynak:** `fal_ai_service.py:492-521`

### 4.3 PuLID id_weight Stil Bazlı

| Stil | id_weight | Kaynak |
|------|-----------|--------|
| 3D / Pixar | ~0.78 | constants.STYLE_PULID_WEIGHTS |
| Watercolor | ~0.72 | constants.STYLE_PULID_WEIGHTS |
| Anime | ~0.75 | constants.STYLE_PULID_WEIGHTS |
| Pastel | ~0.72 | constants.STYLE_PULID_WEIGHTS |
| DB override | VisualStyle.id_weight | Admin panel |

---

## 5. Output Format ve Storage

### 5.1 Fal.ai Response → URL Çıkarma

```
_extract_image_url(data) → str
File: fal_ai_service.py:1219

Desteklenen formatlar:
  1. data["images"][0]["url"]     → Ana format
  2. data["image"]["url"]          → Alternatif
  3. data["output"]["url"]         → Alternatif (list veya dict)
  4. data["output"][0]["url"]      → List alternatif

Dönen: Fal CDN URL (https://fal.media/files/...)
```

### 5.2 Storage Akışı

```
Fal CDN URL (geçici)
    │
    ├─ httpx.AsyncClient.get(image_url) → image_bytes
    │
    ├─ [Opsiyonel] fal_service.upscale_image() → Real-ESRGAN 2x/4x
    │
    ├─ resize_image_bytes_to_target() → baskı boyutu
    │
    └─ storage.upload_generated_image(image_bytes, order_id, page_number)
       │
       ├─ GCS (production):
       │   Bucket : settings.gcs_bucket_generated
       │   Path   : books/{order_id}/pages/page_{page_number}.png
       │   URL    : https://storage.googleapis.com/{BUCKET}/books/{order_id}/pages/page_N.png
       │
       └─ Local (development):
           Path   : local_storage/books/{order_id}/pages/page_{page_number}.png
           URL    : http://localhost:8000/api/v1/media/books/{order_id}/pages/page_N.png
```

**Kaynak:** `storage_service.py:211-220`, `storage_provider.py`

### 5.3 DB Kayıt

```sql
UPDATE order_pages SET
  image_url = '{GCS_URL}',
  status = 'FULL_GENERATED'       -- veya PREVIEW_GENERATED
WHERE order_id = '{order_id}'
  AND page_number = {page_number};
```

**Model:** `order_page.py:22` → `OrderPage` tablosu

---

## 6. Dosya Haritası

| Dosya | Rol | Kritik Fonksiyonlar |
|-------|-----|---------------------|
| `api/v1/trials.py` | API endpoint, trial oluşturma + preview | `POST /create` (:179), `POST /generate-preview` (:767) |
| `api/v1/orders.py` | Sipariş endpoint, ödeme sonrası üretim | `POST /send-preview` (:215), `POST /submit-preview-async` (:468) |
| `tasks/generate_book.py` | Background task: tüm sayfalar + PDF + audio | `generate_full_book()` (:50) |
| `services/ai/gemini_service.py` | LLM orchestrator: PASS-0 + PASS-1 + V3 compose | `generate_story_v3()` (:2479), `generate_story_structured()` (:2887) |
| `services/ai/fal_ai_service.py` | Fal.ai görsel üretim servisi | `generate_consistent_image()` (:252), `_generate_with_queue()` (:1109) |
| `services/ai/image_provider_dispatch.py` | Provider seçimi (Fal / Gemini) | `get_image_provider_for_generation()` (:25) |
| `services/ai/gemini_consistent_image.py` | Gemini ile görsel üretim (alternatif) | `generate_consistent_image()` (:66) |
| `prompt_engine/visual_prompt_builder.py` | Post-LLM prompt enhancement | `enhance_all_pages()` (:673), `compose_enhanced_prompt()` (:475) |
| `prompt_engine/character_bible.py` | Karakter tutarlılığı (identity + outfit) | `build_character_bible()`, `CharacterBible.prompt_block` |
| `prompt_engine/scene_director.py` | Kamera çeşitliliği + kadraj | `build_shot_plan()`, `ShotPlan.prompt_fragment` |
| `prompt_engine/style_adapter.py` | Stil parametreleri (7 stil) | `adapt_style()`, `StyleMapping` |
| `prompt_engine/iconic_anchors.py` | Lokasyona özgü görsel elemanlar | `pick_anchors()`, `LOCATION_ANCHORS` |
| `prompt_engine/visual_prompt_validator.py` | Prompt doğrulama + auto-fix | `validate_all()`, `autofix()` |
| `prompt_engine/story_validators.py` | Hikaye yapısı doğrulama | `validate_story_output()`, `apply_all_fixes()` |
| `prompt_engine/blueprint_prompt.py` | PASS-0 prompt şablonları | `BLUEPRINT_SYSTEM_PROMPT`, `build_blueprint_task_prompt()` |
| `prompt_engine/page_prompt.py` | PASS-1 prompt şablonları | `PAGE_GENERATION_SYSTEM_PROMPT`, `build_page_task_prompt()` |
| `prompt_engine/constants.py` | Sabitler: negative, template, style weights | `GLOBAL_NEGATIVE_PROMPT_EN`, `MAX_FAL_PROMPT_CHARS`, `STYLE_PULID_WEIGHTS` |
| `services/storage_service.py` | GCS/Local upload facade | `upload_generated_image()` (:211), `upload_temp_image()` (:306) |
| `services/storage_provider.py` | Storage backend abstraction | `GCSStorageProvider`, `LocalStorageProvider` |
| `models/order_page.py` | DB modeli: sayfa verileri | `OrderPage`: image_url, image_prompt, v3_composed, negative_prompt |
| `utils/resolution_calc.py` | Çözünürlük hesaplama + resize | `get_effective_generation_params()`, `resize_image_bytes_to_target()` |

---

## 7. Veri Akışı Özeti (Sequence)

```
1. UI → POST /api/v1/trials/create
         ↓
2. trials.py → Scenario + LearningOutcome + VisualStyle resolve (DB)
         ↓
3. gemini_service.generate_story_structured(requested_version="v3")
         ↓
4. generate_story_v3():
   a. _pass0_generate_blueprint()      → Gemini API → Blueprint JSON
   b. sleep(10)
   c. _pass1_generate_pages()           → Gemini API → pages[] (text_tr + image_prompt_en)
   d. validate_story_output()           → yapı doğrulama
   e. enhance_all_pages()               → deterministik prompt enhancement
   f. validate_visual_prompts()         → shot conflict, value motif check
   g. build_cover_prompt()              → kapak promptu
   h. FinalPageContent[] oluştur        → v3_composed=True
         ↓
5. trials.py → response + background task başlat
         ↓
6. Background: generate_consistent_image() per page
   a. V3 skip_compose → prompt direkt kullanılır
   b. Model: flux-pulid (yüz ref varsa) veya flux/dev
   c. Fal queue submit → poll → result URL
         ↓
7. Fal CDN URL → download → upscale (opsiyonel) → resize
         ↓
8. storage.upload_generated_image() → GCS/Local
         ↓
9. DB: OrderPage.image_url = GCS URL, status = COMPLETED
```

---

## 8. Kritik Notlar

1. **Gemini sadece TEXT üretir** — görsel üretimi yoktur. Gemini API `generateContent` endpoint'i metin/JSON döner; görsel prompt metinleri Gemini'den alınıp Fal.ai'ye gönderilir.

2. **Seed parametresi**: Gemini text API'de seed yoktur. Fal.ai'de `GenerationConfig.seed` desteklenir ama varsayılan `null` (her seferinde farklı sonuç).

3. **max_sequence_length=512**: Fal.ai varsayılanı 128 token. V3 promptları çok uzun olduğundan 512'ye çıkarılmış. Bu olmadan stil/composition direktifleri kesilir.

4. **V3 skip_compose**: `v3_composed=True` olan sayfalarda `fal_ai_service.generate_consistent_image()` prompt'u yeniden compose etmez — sadece length guard uygular.

5. **İki paralel image generation path**:
   - **Trial preview**: `trials.py` → `asyncio.gather()` ile paralel, `image_concurrency` semaphore
   - **Full book**: `generate_book.py` → sıralı (sayfa sayfa), upscale + PDF dahil

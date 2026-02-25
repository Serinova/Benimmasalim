# Fotoğraf / Görsel Analiz Akışı – Uçtan Uca Analiz

## 1) Akış diyagramı (madde madde)

```
[FRONTEND]
  Kullanıcı fotoğraf yükler (PhotoUploaderStep)
       │
       ├─► "Analiz Et" butonu → handleAnalyzePhoto() → Sadece simülasyon (1.5s bekleme), API çağrısı YOK
       │
       └─► Hikaye oluştur → POST /api/v1/ai/test-story-structured
              Body'de child_photo_url GÖNDERİLMİYOR (frontend eksik)
              │
              ▼
[BACKEND - ai.py]
  test_structured_story_generation(request)
       │
       ├─► if request.child_photo_url:
       │        face_analyzer = get_face_analyzer()
       │        child_visual_desc = await face_analyzer.analyze_for_ai_director(
       │            image_source=request.child_photo_url, child_name, child_age, child_gender)
       │   (child_photo_url yoksa child_visual_desc = "" kalır)
       │
       └─► gemini_service.generate_story_structured(..., visual_character_description=child_visual_desc)
              │
              ▼
  Response: story + metadata.child_visual_description (DB'ye kaydedilmez; sadece yanıtta döner)

[DOĞRUDAN TEST ENDPOINT'LERİ]
  POST /api/v1/ai/test-face-analysis        → analyze_face + get_enhanced_child_description
  POST /api/v1/ai/test-face-analysis-multi → analyze_face (tek) + analyze_multiple_photos + get_enhanced_child_description_multi
```

---

## 2) Görsel analiz nerede başlıyor?

| Yer | Açıklama |
|-----|----------|
| **Ana giriş (hikaye akışı)** | `backend/app/api/v1/ai.py` → `test_structured_story_generation()` (satır ~607). `request.child_photo_url` varsa `get_face_analyzer().analyze_for_ai_director(...)` çağrılır. |
| **Test – tek foto** | `POST /api/v1/ai/test-face-analysis` → `test_face_analysis()` → `analyze_face()` + `get_enhanced_child_description()`. |
| **Test – çoklu foto** | `POST /api/v1/ai/test-face-analysis-multi` → `test_multi_view_face_analysis()` → `analyze_face()` + `analyze_multiple_photos()` + `get_enhanced_child_description_multi()`. |

Frontend’de “Analiz Et” butonu gerçek bir görsel analiz API’si çağırmıyor; sadece 1.5 saniyelik simülasyon yapıyor.

---

## 3) Görsel analiz hangi modele gidiyor?

- **Model:** Google **Gemini 2.0 Flash** (multimodal).
- **Kullanım yeri:** `backend/app/services/ai/face_analyzer_service.py`
  - `self.model = "gemini-2.0-flash"`
  - `self.base_url = "https://generativelanguage.googleapis.com/v1beta"`
- **API:** `generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key=...`
- OpenAI / FAL görsel analiz bu akışta kullanılmıyor; FAL sadece görsel **üretimi** (fal_ai_service) için.

---

## 4) Görsel analize giden INPUT

| Bileşen | İçerik |
|--------|--------|
| **Görsel** | URL (`http(s)://`) veya raw bytes. URL ise `httpx` ile indirilir; bytes veya base64 ise `_load_image_as_base64()` ile base64 + mime type üretilir. |
| **Mime type** | PIL ile tespit: `image/{format}` (örn. `image/jpeg`). |
| **Prompt (tek yüz – forensic)** | `FORENSIC_ANALYSIS_PROMPT` (sabit sistem promptu) + opsiyonel context: yaş (“This is a X-year-old child”), cinsiyet (“Gender: boy/girl”). |
| **Prompt (AI-Director – hikaye akışı)** | `analysis_prompt`: çocuk adı, yaş, cinsiyet + “30–50 kelime kısa betimleme” talimatı (saç, göz, cilt, ayırt edici özellikler). |
| **Prompt (çoklu foto)** | `MULTI_VIEW_ANALYSIS_PROMPT` + aynı kişinin 2–5 fotoğrafı; context yaş/cinsiyet eklenir. |

**Örnek request payload (tek yüz – `analyze_face`):**

```json
{
  "contents": [{
    "parts": [
      { "inlineData": { "mimeType": "image/jpeg", "data": "<base64>" } },
      { "text": "[context_prefix]. " + FORENSIC_ANALYSIS_PROMPT }
    ]
  }],
  "generationConfig": {
    "temperature": 0.2,
    "topP": 0.8,
    "maxOutputTokens": 1024
  },
  "safetySettings": [ "BLOCK_NONE" x4 ]
}
```

---

## 5) Dönen OUTPUT nasıl parse ediliyor ve nereye kaydediliyor?

| Metod | Parse | Kayıt |
|-------|--------|------|
| **analyze_face** | `result["candidates"][0]["content"]["parts"][0]["text"]` → strip. KeyError/IndexError → `ValueError("Failed to generate face description from image")`. | Sadece return; DB’ye yazılmıyor. |
| **analyze_for_ai_director** | Aynı path; strip + tırnak temizleme. “a ” ile başlamıyorsa öne eklenir. Hata → fallback: `"a {age}-year-old {gender} named {name} with a friendly expression"`. | Sadece return; hikaye üretiminde `visual_character_description` olarak Gemini’ye gider. |
| **analyze_multiple_photos** | Aynı path; strip. Hata → `ValueError("Failed to generate face description from multiple images")`. | Sadece return. |
| **test_structured_story_generation** | `child_visual_desc` → `generate_story_structured(..., visual_character_description=child_visual_desc)`. Yanıtta `metadata.child_visual_description` (ilk 100 karakter) döner; DB’ye kaydedilmez. | Yok. |

Yani çıktı **düz metin**; JSON parse yok. Sadece Gemini’nin text cevabı alınıp string olarak kullanılıyor.

---

## 6) İlgili dosyalar listesi (path + rolü)

| Dosya | Rolü |
|-------|------|
| `backend/app/services/ai/face_analyzer_service.py` | Görsel analiz servisi: `_load_image_as_base64`, `analyze_face`, `get_enhanced_child_description`, `analyze_for_ai_director`, `analyze_multiple_photos`, `get_enhanced_child_description_multi`. Gemini’ye HTTP POST, cevap parse. |
| `backend/app/api/v1/ai.py` | Giriş noktaları: `test_structured_story_generation` (child_photo_url → analyze_for_ai_director), `test_face_analysis`, `test_multi_view_face_analysis`. Request/response şemaları. |
| `backend/app/core/rate_limit.py` | `@rate_limit_retry(service="gemini", ...)`: 429/timeout için retry, backoff, circuit breaker. |
| `backend/app/services/ai/gemini_service.py` | Hikaye ve teknik director çağrıları; `visual_character_description` burada prompt’a eklenir (görsel analiz değil, metin kullanımı). |
| `backend/app/config.py` | `gemini_api_key`, `gemini_rpm_limit`, timeout ile ilgili env. |
| `frontend/src/app/create/page.tsx` | `handleAnalyzePhoto` (sadece simülasyon), `test-story-structured` çağrısı (şu an **child_photo_url gönderilmiyor**). |
| `frontend/src/components/PhotoUploaderStep.tsx` | Foto seçimi, `onAnalyze` tetiklemesi (içerik create/page’deki simülasyon). |
| `backend/app/services/ai/__init__.py` | `FaceAnalyzerService`, `get_face_analyzer` export. |

---

## 7) Giriş noktası ve ana fonksiyonlar

| Giriş / fonksiyon | Dosya:satır | Açıklama |
|-------------------|-------------|----------|
| `POST /api/v1/ai/test-story-structured` | ai.py | Hikaye üretimi; body’de `child_photo_url` varsa görsel analiz tetiklenir. |
| `POST /api/v1/ai/test-face-analysis` | ai.py | Tek foto ile forensic + enhanced açıklama testi. |
| `POST /api/v1/ai/test-face-analysis-multi` | ai.py | Çoklu foto ile tek + çoklu + enhanced testi. |
| `get_face_analyzer()` | face_analyzer_service.py | Singleton FaceAnalyzerService. |
| `analyze_face(image_source, child_age, child_gender)` | face_analyzer_service.py | Tek görsel, forensic prompt, 1024 token. |
| `analyze_for_ai_director(image_source, child_name, child_age, child_gender)` | face_analyzer_service.py | Kısa (30–50 kelime) betimleme, 200 token. |
| `analyze_multiple_photos(image_sources, ...)` | face_analyzer_service.py | 2–5 görsel, MULTI_VIEW_ANALYSIS_PROMPT, 1500 token. |
| `_load_image_as_base64(image_source)` | face_analyzer_service.py | URL → GET veya bytes/base64 → base64 + mime_type. |

---

## 8) Prompt birleştirme mantığı

- **Forensic (tek yüz):**  
  `[context_prefix]. " + FORENSIC_ANALYSIS_PROMPT`  
  context_prefix: opsiyonel “This is a X-year-old child. Gender: boy/girl.”

- **AI-Director (hikaye akışı):**  
  Sabit `analysis_prompt` metni (içinde `child_name`, `child_age`, `gender_word` formatında talimat). Görsel + bu tek text part.

- **Çoklu foto:**  
  Tüm görseller `inlineData` part’ları; son part: `context_prefix + MULTI_VIEW_ANALYSIS_PROMPT`.

Style / negative prompt görsel analiz tarafında yok; bunlar görsel **üretim** (FAL/Gemini image) tarafında kullanılıyor.

---

## 9) Model çağrı kodu ve request (kısaca)

- **HTTP:** `httpx.AsyncClient(timeout=30 veya 60).post(url, json=payload)`.
- **URL:** `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={gemini_api_key}`.
- **Payload:** `contents[].parts[]` = sırayla image `inlineData` (mimeType + data base64) ve `text` (prompt). `generationConfig`: temperature, topP, maxOutputTokens. `safetySettings`: 4 kategori BLOCK_NONE.
- **Parse:** `response.json()["candidates"][0]["content"]["parts"][0]["text"]`.

---

## 10) Hata ihtimalleri: neden bazen çalışıyor bazen bozuluyor?

| Sebep | Açıklama |
|-------|----------|
| **child_photo_url gönderilmiyor** | Frontend `test-story-structured` çağrısında `child_photo_url` body’de yok → backend’de analiz hiç çalışmıyor. |
| **Timeout** | `face_analyzer_service`: 30s (çoklu için 60s). Yavaş ağ veya büyük görsel → `httpx.TimeoutException`; `rate_limit_retry` ile yeniden denenecek. |
| **Token / boyut** | Görsel base64 büyükse model limiti aşılabilir. PIL ile açılıyor ama resize/compress yok; büyük dosya riski. |
| **Rate limit (429)** | Gemini RPM aşımı. `@rate_limit_retry` 2–3 deneme + backoff; circuit breaker açılırsa süre boyunca tüm Gemini çağrıları bloke. |
| **Parse hatası** | `candidates[0]` yok (güvenlik/quality block, boş cevap) → KeyError/IndexError → ValueError veya fallback. |
| **Safety block** | Gemini güvenlik filtresi cevabı keserse `candidates` boş veya farklı yapıda olabilir; mevcut parse kırılır. |
| **Görsel yükleme hatası** | URL erişilemez veya geçersiz bytes → `_load_image_as_base64` içinde exception; üstte try/except ile log + fallback/raise. |

---

## 11) Debug önerileri (log eklenecek yerler)

1. **ai.py – test_structured_story_generation**  
   - Girişte: `logger.info("story_gen_request", has_child_photo_url=bool(request.child_photo_url), child_photo_url_preview=request.child_photo_url[:80] if request.child_photo_url else None)`.  
   - Face analiz sonrası: `logger.info("face_analysis_done", description_length=len(child_visual_desc), preview=child_visual_desc[:120])`.

2. **face_analyzer_service.py – _load_image_as_base64**  
   - URL path: `logger.debug("loading_image", source_type="url", url_preview=image_source[:80])`.  
   - Bytes path: `logger.debug("loading_image", source_type="bytes", size=len(image_bytes))`.  
   - Çıkış: `logger.debug("image_loaded", mime_type=mime_type, base64_len=len(base64_data))`.

3. **face_analyzer_service.py – analyze_face / analyze_for_ai_director**  
   - İstek öncesi: `logger.info("gemini_vision_request", model=self.model, prompt_len=len(text_part), image_base64_len=len(base64_data))`.  
   - Cevap sonrası: `logger.info("gemini_vision_response", has_candidates=("candidates" in result), candidates_len=len(result.get("candidates", [])))`.  
   - Parse hatası: `logger.error("gemini_vision_parse_failed", keys=list(result.keys()), candidates_0_keys=...)`.

4. **rate_limit.py – rate_limit_retry**  
   - Her retry: `logger.warning("rate_limit_retry", attempt=attempt, service=service, error=str(e))`.  
   - Circuit açık: `logger.warning("circuit_open", service=service, open_until=...)`.

5. **Frontend – create/page.tsx**  
   - Hikaye isteği body’sine `child_photo_url` eklenmeden önce: `console.log("story_request_body", { ...body, has_child_photo_url: !!childPhotoPreview })`.  
   - GCS upload sonrası story çağrısına `child_photo_url: photoUrl` eklenirse aynı log ile doğrulanabilir.

---

## 12) Kısa özet ve öneri

- **Görsel analiz:** Sadece **Gemini 2.0 Flash** ile yapılıyor; giriş `face_analyzer_service` ve `ai.py` test/structured endpoint’leri.
- **Ana sorun:** Create akışında frontend `child_photo_url` göndermediği için hikaye üretiminde yüz analizi fiilen **hiç tetiklenmiyor**.
- **Öneri:**  
  - Foto adımında GCS’e yükleyip URL alıyorsanız, `test-story-structured` body’sine `child_photo_url: photoUrl` ekleyin.  
  - İsterseniz “Analiz Et” butonunu gerçek bir endpoint’e (örn. `test-face-analysis` veya yeni bir `/ai/analyze-child-photo`) bağlayıp sonucu UI’da gösterebilirsiniz.

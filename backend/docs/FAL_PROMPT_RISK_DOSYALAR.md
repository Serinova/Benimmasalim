# Fal’a giden prompt – riskli / farklı davranan dosyalar

Bu dokümanda Fal’a **farklı** veya **stilsiz** prompt gidebilecek yerler ve yapılan düzeltmeler özetleniyor.

---

## 1. Ana akış (sipariş / admin stil testi) – DOĞRU

| Dosya | Kullanım | Fal’a giden |
|-------|----------|-------------|
| `app/api/v1/orders.py` | Sipariş görsel üretimi | `FalAIService.generate_consistent_image` → `compose_visual_prompt` ile **stil + şablon + oran** eklenir, aynı metin `payload["prompt"]` olarak gider. |
| `app/tasks/generate_book.py` | Kitap sayfa üretimi | Aynı: `generate_consistent_image` → tam composed prompt. |
| `app/api/v1/admin/visual_styles.py` | Stil testi | Aynı: `generate_consistent_image` → STYLE_TEST_SCENE + stil + şablon. |

Bu akışta **tek kaynak** `compose_visual_prompt`; prompt ile admin’de gördüğünüz metin aynı.

---

## 2. Düzeltilen: Session / cover-page yolu (stil düşüyordu)

| Dosya | Risk | Düzeltme |
|-------|------|----------|
| `app/services/ai/fal_ai_service.py` | `generate_cover` / `generate_page` → `_generate_with_composed_prompt` içinde `compose_visual_prompt(..., style_text="")` çağrılıyordu. **Stil (leading_prefix + STYLE bloğu) eklenmiyordu.** | `style_prompt_en=style_modifier`, `style_negative_en=...` geçirilecek şekilde güncellendi. Session ile üretimde de stil artık ekleniyor. |

**Çağrı zinciri:** `generate_page_with_session` → `generate_cover` / `generate_page` → `_generate_with_composed_prompt`.  
Kullanıldığı yerler: `app/api/v1/ai.py`, `app/services/ai/image_generator.py` (session ile sayfa üretimi).

---

## 3. FalService (fal_service.py) – Trials / legacy

| Dosya | Kullanım | Risk |
|-------|----------|------|
| `app/services/ai/fal_service.py` | `generate_image`, `generate_with_pulid`, `generate_cover`, `generate_page_image` | Tüm compose çağrılarında **style_text=""** kullanılıyor. Stil **eklenmiyor**; prompt’un zaten “scene + style” içerdiği varsayılıyor. Trials’ta gelen `visual_prompt` Gemini’den geliyorsa bazen stil dahil olabilir; yoksa çıktı stilsiz/tekdüze olur. |
| `app/api/v1/trials.py` | Deneme kitapları önizleme | `fal_service.generate_image` / `generate_with_pulid` kullanıyor; **FalAIService değil**. Stil trials isteğinde ayrıca iletilmiyorsa prompt’ta olmayabilir. |

**Yapılan:** `fal_service.py` içindeki Fal API çağrılarına **max_sequence_length=512** eklendi (uzun prompt’un varsayılan 128 token ile kesilmesi azaltıldı).  
**Öneri:** Trials için uzun vadede `FalAIService.generate_consistent_image` + stil parametresi kullanılması; böylece sipariş akışı ile aynı composed prompt mantığı kullanılır.

---

## 4. Özet tablo

| Akış | Servis | Stil prompt’a ekleniyor mu? | max_sequence_length |
|------|--------|-----------------------------|----------------------|
| Sipariş / generate_book | FalAIService.generate_consistent_image | Evet | 512 |
| Admin stil testi | FalAIService.generate_consistent_image | Evet | 512 |
| Session (generate_page_with_session) | FalAIService.generate_cover/page → _generate_with_composed_prompt | Evet (düzeltme sonrası) | 512 |
| Trials | FalService.generate_image / generate_with_pulid | Hayır (prompt’ta varsa var) | 512 (eklendi) |

---

## 5. Kontrol listesi (yeni Fal çağrısı eklerken)

- Prompt’u **sadece** `compose_visual_prompt` ile üret; aynı çıktıyı `payload["prompt"]` yap.
- `compose_visual_prompt` çağrısında **stil ver**: `style_prompt_en` veya `style_text` (ve gerekirse `style_negative_en`).
- Fal payload’ında **max_sequence_length=512** kullan (flux-pulid / flux/dev için).
- Negatif için **build_negative_prompt** kullan; base + stil negatifi tek yerde birleşsin.

Bu sayede “bizim promptlardan başka Fal’a farklı bir şey gidiyor” riski azaltılmış olur; çıktının berbat olması büyük olasılıkla stil atlanması veya token kesilmesi kaynaklıydı.

---

## 6. Çift dosya (makarna) – hangisi aktif?

- **`app/prompt_engine/visual_prompt_composer.py`** = Tek gerçek implementasyon. Tüm güncellemeler burada yapılmalı.
- **`app/core/visual_prompt_composer.py`** = Sadece re-export (DEPRECATED); prompt_engine'den import eder. Inaktif.

## 7. Stil eşleşmemesi: Türkçe karakter (Yumuşak Pastel)

DB/frontend "Yumuşak Pastel" (ş) gönderiyordu; matcher "yumusak pastel" (ASCII) ile eşleşmiyordu, stil DEFAULT'a düştü. **Düzeltme:** `constants.py` içinde `_normalize_style_modifier_for_match` (ş→s, ı→i, ğ→g, ü→u, ö→o, ç→c) eklendi; `get_style_config`, `get_style_negative_default`, `get_pulid_weight_for_style`, `get_style_specific_negative` bu normalizasyonu kullanıyor.

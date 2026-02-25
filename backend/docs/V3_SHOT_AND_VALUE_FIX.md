# V3 Pipeline Fix — Shot Consistency + Value Injection

## Özet

- **Shot consistency:** Sayfa bazlı `shot_type`: `WIDE_FULL_BODY` (varsayılan) veya `CLOSE_UP`. CLOSE_UP sayfalarda "full body head-to-feet" kuralı kaldırıldı; çakışan ifadeler final prompt’ta olmaz.
- **Value injection:** Seçilen değer (örn. özgüven) için `value_message` (narrative’e kısa mesaj) ve `value_visual_motif` (her görsel prompt’ta tekrarlayan motif) eklendi.
- **Validator:** Final prompt’ta hem "close-up" hem "full body head-to-feet" varsa build fail; value_visual_motif zorunluysa ve bir sayfada yoksa build fail.

---

## 1) Shot type per page

- **Blueprint:** Her sayfa için opsiyonel `shot_type`: `"WIDE_FULL_BODY"` | `"CLOSE_UP"`. Varsayılan: `WIDE_FULL_BODY`.
- **scene_director:** `build_shot_plan()` blueprint’teki `shot_type`’ı okur. `CLOSE_UP` ise `ShotPlan.page_shot_type = CLOSE_UP` ve `prompt_fragment` içinde "full body head-to-feet" yok; "waist up or upper body, no full body requirement" kullanılır.
- **visual_prompt_builder:** `_remove_shot_conflict()` ile prompt’ta "close-up" varsa "full body head-to-feet" ifadesi kaldırılır.

### Örnek çıktı — Sayfa 1 (WIDE_FULL_BODY, dedication/arrival)

```json
{
  "page": 1,
  "text_tr": "Bora'nın Kapadokya macerası başlıyor...",
  "image_prompt_en": "2D hand-painted storybook. A 7-year-old boy named Bora, wearing a red adventure jacket and blue jeans. [scene description]. wide shot, eye-level angle, child occupies 35% of the frame, full body head-to-feet visible, no cropped legs. a small golden confidence charm bracelet visible on the child's wrist. child's expression: curious. STYLE: Soft pastel children's book... no text, no watermark, no logo"
}
```

- Sayfa 1’de "wide shot" + "full body head-to-feet visible, no cropped legs" birlikte; "close-up" yok → tutarlı kompozisyon.

### Örnek çıktı — Sayfa 9 (CLOSE_UP, puzzle)

Blueprint’te `"shot_type": "CLOSE_UP"` verildiğinde:

```json
{
  "page": 9,
  "text_tr": "Bora taştaki sembollere dokundu...",
  "image_prompt_en": "2D hand-painted storybook. A 7-year-old boy named Bora, wearing a red adventure jacket and blue jeans. [scene]. close-up, over-the-shoulder, child occupies 40% of the frame, waist up or upper body, no full body requirement. a small golden confidence charm bracelet visible on the child's wrist. child's expression: focused. STYLE: ... no text, no watermark, no logo"
}
```

- "close-up" + "waist up or upper body"; "full body head-to-feet" yok → çakışma yok.

---

## 2) Value injection — özgüven

- **value_message (narrative):** PASS-1 task prompt’a eklenir; yazar hikayeye doğal şekilde yedirir.
- **value_visual_motif (görsel):** Her sayfa ve kapak prompt’una eklenir.

### Özgüven için sabitler (gemini_service)

| Alan | Değer |
|------|--------|
| `VALUE_MESSAGE_TR["özgüven"]` | "Küçük adımlarla kendine güven kazanır." |
| `VALUE_VISUAL_MOTIF_EN["özgüven"]` | "a small golden confidence charm bracelet visible on the child's wrist" |

### Narrative örneği (value_message)

PASS-1’e giden blok:

```
DEĞER MESAJI (hikayede doğal şekilde, tek cümle veya his olarak yedir):
"Küçük adımlarla kendine güven kazanır."
Bu mesajı ahlak dersi gibi değil, olayların sonucu olarak hissettir.
```

Örnek `text_tr` cümlesi (özgüven seçili):  
"İlk denemede tam olmasa da, küçük adımlarla kendine güveni artıyordu."

### Görsel motif örneği (value_visual_motif)

Tüm sayfa ve kapak prompt’larının sonuna (STYLE’dan önce) eklenir:

- "a small golden confidence charm bracelet visible on the child's wrist"

Validator, `value_visual_motif` verildiğinde bu ifadeyi (veya anlamlı bir alt kümesini) her sayfanın `image_prompt_en` içinde arar; yoksa build fail eder.

---

## 3) Validator kuralları

| Kural | Açıklama |
|-------|----------|
| **SHOT_CONFLICT** | Aynı prompt’ta hem "close-up" hem "full body head-to-feet" varsa → hata. |
| **VALUE_MOTIF_MISSING** | `value_visual_motif` dolu ama bir sayfanın `image_prompt_en` içinde motif (veya anlamlı parçası) yok → hata. |

---

## Güncellenen dosyalar

- `backend/app/prompt_engine/scene_director.py` — `PageShotType`, `ShotPlan.page_shot_type`, blueprint’ten `shot_type` okuma.
- `backend/app/prompt_engine/visual_prompt_builder.py` — `_remove_shot_conflict()`, `value_visual_motif` parametresi, `compose_enhanced_prompt` ve `build_cover_prompt` / `enhance_all_pages`.
- `backend/app/prompt_engine/visual_prompt_validator.py` — `_check_shot_conflict()`, `_check_value_motif_present()`, `validate_all(..., value_visual_motif=)`.
- `backend/app/prompt_engine/blueprint_prompt.py` — Blueprint JSON şemasına `shot_type` alanı ve açıklaması.
- `backend/app/prompt_engine/page_prompt.py` — `build_page_task_prompt(..., value_message_tr=)` ve değer mesajı bloğu.
- `backend/app/services/ai/gemini_service.py` — `VALUE_MESSAGE_TR`, `VALUE_VISUAL_MOTIF_EN`, `get_value_visual_motif_for_outcomes`, `get_value_message_tr_for_outcomes`; `enhance_all_pages` / `build_cover_prompt` / `validate_visual_prompts` / `_pass1_generate_pages` için value ve motif kullanımı.

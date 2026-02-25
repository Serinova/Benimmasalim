# Prompt pipeline ve Fal.ai’a giden veri analizi

Bu dokümanda: **senaryo + stil → Gemini (isteğe bağlı) → compose → Fal’a giden prompt** akışı ve **uygulama çıktısı ile Fal UI’da aynı prompt’u yapıştırınca fark çıkmasının** nedenleri özetleniyor.

---

## 1. Fal’a hangi prompt gidiyor?

**Tek kaynak:** `compose_visual_prompt(...)` çıktısındaki `full_prompt`.

- Kod: `fal_ai_service.generate_consistent_image()` içinde  
  `full_prompt, negative_suffix = compose_visual_prompt(...)`  
  sonra `payload["prompt"] = full_prompt` ve `out["final_prompt"] = full_prompt`.
- Admin panelde “Test” sonrası gösterilen **final_prompt** = Fal’a gönderilen **aynı** metin (ek kesme/transform yok).

Yani admin’de kopyalayıp Fal UI’a yapıştırdığınız metin, uygulamanın Fal’a gönderdiği prompt ile birebir aynıdır.

---

## 2. Pipeline: Senaryo → Stil → Compose → Fal

### 2.1 Admin “Stil testi” akışı

```
Sabit sahne (STYLE_TEST_SCENE)
  "A young child in Cappadocia with fairy chimneys and hot air balloons in the sky, wide shot, looking up in amazement. Bright daylight."

+ Sabit kıyafet (STYLE_TEST_CLOTHING)
  "turquoise t-shirt, denim shorts, brown hiking boots"

+ Seçilen stil (VisualStyle.prompt_modifier)
  örn. "Yumuşak Pastel"

+ Şablon (INNER_TEMPLATE, DB veya default)
  "A young child wearing {clothing_description}. {scene_description}. Empty space at bottom for captions (no text in image)."

+ Stil negatifi (VisualStyle.style_negative_en veya get_style_negative_default)
```

- **Girdi:** `prompt` = STYLE_TEST_SCENE, `clothing_prompt` = STYLE_TEST_CLOTHING, `style_text` = style.prompt_modifier, `template_en` = INNER_TEMPLATE, `style_negative_en` = style.style_negative_en.
- **Çıktı:** `compose_visual_prompt(...)` → `full_prompt`, `full_negative`.

### 2.2 Compose içinde sıra (özet)

1. Şablon render: `A young child wearing {clothing}. {scene}. Empty space at bottom...`
2. Sanitize / normalizasyon (lokasyon, kıyafet, vb.)
3. **En başa** eklenenler (token ağırlığı için):
   - `BODY_PROPORTION_DIRECTIVE` (oran + “No chibi, no bobblehead” + “Small realistic eyes”)
   - `SHARPNESS_BACKGROUND_DIRECTIVE`
   - İsteğe bağlı: `LIKENESS_HINT_WHEN_REFERENCE` (referans foto varsa)
   - Stil `leading_prefix` (örn. Yumuşak Pastel: “Small realistic eyes, no chibi…” + stil cümleleri)
4. **Sonda** eklenen: `\n\nSTYLE:\n` + stil bloğu (constants’tan `style_block`).

Sonuç: Fal’a giden metin = bu composed `full_prompt` (kesilmeden; sadece compose **girdisi** sahne metni 2500 karakteri aşarsa önceden kısaltılıyor).

### 2.3 Sipariş / hikaye akışında (Gemini)

- **Senaryo:** Kullanıcı seçimi + kitap ayarları.
- **Stil:** Kullanıcının seçtiği çizim tarzı (prompt_modifier).
- **Gemini:** Hikaye + sayfa metinleri (scene_description) üretir; bazen “The child is wearing …” vb. ekler.
- **Her sayfa için:**  
  `scene_description` (Gemini çıktısı veya düzenlenmiş metin) + aynı şablon + aynı stil + clothing → yine `compose_visual_prompt(...)` → o sayfanın `full_prompt`’u.
- Fal’a her sayfa için giden prompt = o sayfanın compose çıktısı; yani **Gemini’nin sahne metni, compose’tan geçtikten sonra** Fal’a gider (doğrudan ham Gemini metni gönderilmez).

---

## 3. Fal’a giden tam payload (uygulama)

```python
payload = {
    "prompt": full_prompt,           # compose_visual_prompt çıktısı
    "negative_prompt": full_negative,
    "image_size": {"width": width, "height": height},
    "num_inference_steps": 28,       # generation_config
    "guidance_scale": 3.5,
    "max_sequence_length": 512,
}
# Referans foto varsa (stil testinde yükleme yapıldıysa):
if child_face_url:
    payload["reference_image_url"] = child_face_url
    payload["id_weight"] = id_weight   # stile göre (örn. 0.74 Yumuşak Pastel)
    payload["start_step"] = 5
    payload["true_cfg"] = 1.0
    model = "fal-ai/flux-pulid"
else:
    model = "fal-ai/flux/dev"
```

- **full_negative:** `build_negative_prompt(...)` çıktısı (base + stil negatifi, cinsiyet negatifi; token cap 48).

---

## 4. Uygulama görseli vs Fal UI’da aynı prompt (1. vs 2. resim farkı)

Admin’den kopyaladığınız **final_prompt** = Fal’a giden **prompt** ile aynı. Buna rağmen çıktı farklıysa sebep **metin değil, Fal’a giden diğer parametreler**dir:

| Fark | Uygulama (1. resim) | Fal UI’da sadece prompt yapıştırma (2. resim) |
|------|----------------------|-----------------------------------------------|
| **Referans foto (PuLID)** | Stil testinde foto yüklendiyse: `reference_image_url` + `id_weight` + `start_step` + `true_cfg` gider. Model **yüzü** referansa çeker; oran/göz stilleri bazen ikinci planda kalır. | Genelde **referans yok**. Sadece metin; model tamamen prompt’a göre çizer. |
| **negative_prompt** | Uygulama uzun negatif gönderir (big eyes, chibi, oversized head, …). | Kullanıcı sadece pozitif prompt yapıştırdıysa negatif farklı veya boş. |
| **Parametreler** | `num_inference_steps=28`, `guidance_scale=3.5`, `max_sequence_length=512`. | Fal UI varsayılanları farklı olabilir. |

**Özet:** 1. resim (uygulama) büyük ihtimalle **referans foto + PuLID** ile üretilmiş; yüz kimliği öne çıkınca “chibi / büyük göz” hissi artıyor. 2. resim (Fal UI) muhtemelen **referans olmadan** aynı prompt ile üretildiği için farklı (daha “sadece prompt’a göre”) çıkıyor. Yani fark, **hangi prompt’un Fal’a gittiği** değil, **referans + negatif + parametreler**den kaynaklanıyor.

---

## 5. Kontrol listesi (aynı sonucu Fal UI’da denemek için)

Fal UI’da uygulama ile aynı sonuca yaklaşmak için:

1. **Prompt:** Admin’deki `final_prompt`’u olduğu gibi yapıştırın (zaten Fal’a giden ile aynı).
2. **Negative prompt:** Admin’de dönen `negative_prompt`’u Fal UI’da negatif alanına yapıştırın.
3. **Referans:** Testte çocuk fotoğrafı yüklediyseniz, Fal UI’da da aynı referansı kullanın (flux-pulid endpoint’i).
4. **Parametreler:** Mümkünse `num_inference_steps=28`, `guidance_scale=3.5`, `max_sequence_length=512`; PuLID kullanıyorsanız `id_weight` (örn. 0.74), `start_step=5`, `true_cfg=1.0`.

Referans **kullanmadan** “sadece prompt” ile denemek isterseniz: stil testinde **foto yüklemeden** test edin; böylece uygulama da `flux/dev` ile referans olmadan üretir, Fal UI ile daha yakın sonuç alırsınız.

---

## 6. Dosya referansları

| Ne | Nerede |
|----|--------|
| Compose (tek kaynak) | `app/prompt_engine/visual_prompt_composer.py` → `compose_visual_prompt()` |
| Negatif birleştirme | `app/prompt_engine/negative_prompt_builder.py` → `build_negative_prompt()` |
| Stil / oran sabitleri | `app/prompt_engine/constants.py` (BODY_PROPORTION_DIRECTIVE, NEGATIVE_PROMPT, StyleConfig, get_style_negative_default) |
| Fal’a gönderim | `app/services/ai/fal_ai_service.py` → `generate_consistent_image()` içinde `payload["prompt"] = full_prompt` |
| Admin stil testi | `app/api/v1/admin/visual_styles.py` → `test_visual_style()`; `final_prompt` = Fal’a giden prompt |
| Sipariş sayfa prompt’u | `app/api/v1/orders.py`; `prompt_debug_json` / story_pages içinde `final_prompt` ve `visual_prompt` |

Bu yapı sayesinde **Fal’a giden prompt** her zaman `compose_visual_prompt` çıktısıdır; senaryo ve stil sistemi bu composed prompt’u üretmek için kullanılır.

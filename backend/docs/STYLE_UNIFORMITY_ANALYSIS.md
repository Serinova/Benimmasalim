# Stil Tekdüzeliği Analizi — Tüm Stillerin Benzer Görünmesi

## Özet

5 farklı stil (default story book, ghibli ish, watercolor, 3d pixar, 2d children book) seçildiğinde tüm çıktılar birbirine benziyor. Analiz sonucu: **StyleConfig prefix/suffix V2 path'ta hiç kullanılmıyor** — stil farklılaşması sadece sonda eklenen STYLE block ile yapılıyor; diffusion modelleri baştaki token'lara daha fazla ağırlık verdiği için stil etkisi zayıf kalıyor.

---

## Akış Analizi

### V2 Path (mevcut kullanım — template_en ile)

```
generate_consistent_image(template_en=cover_tpl | inner_tpl)
  → compose_visual_prompt(prompt, template_en, clothing, style_prompt_en)
```

`compose_visual_prompt` içinde:

1. **Template render:** `{scene_description}. A young child wearing {clothing_description}. Space for title at top.`
2. **normalize_safe_area_and_composition** → COMPOSITION_RULES eklenir
3. **Sadece 2D stiller için** başa prefix: `"2D children's picture-book illustration style. "`
4. **STYLE block** sonda: `\n\nSTYLE:\n{style_prompt}` (DB prompt_modifier)

### Kritik Bulgu

**StyleConfig (PIXAR_STYLE, WATERCOLOR_STYLE, ANIME_STYLE, vb.) V2 path'ta HİÇ KULLANILMIYOR.**

- `get_style_config(style_modifier)` sadece `FluxPromptBuilder._build_full_prompt` içinde kullanılıyor
- `_build_full_prompt` yalnızca `template_en` **olmadığında** (legacy path) çağrılıyor
- V2 path her zaman `template_en` ile çağrıldığı için StyleConfig prefix/suffix hiç devreye girmiyor

---

## Ortak Prompt Yapısı (Tüm Stiller İçin Aynı)

| Bileşen | İçerik | Stil farkı |
|---------|--------|------------|
| Scene | Gemini'den gelen sahne metni | Aynı |
| Template | "A young child wearing {X}." | Aynı |
| Safe area | "Space for title at top" / "Text space at bottom" | Aynı |
| COMPOSITION_RULES | "Wide shot, child 30% of frame, environment 70%, child NOT looking at camera. Natural child proportions..." | Aynı |
| 2D prefix | Sadece 2d/children's book/storybook için: "2D children's picture-book illustration style. " | Sadece 2D'de var |
| STYLE block | DB prompt_modifier — **en sonda** | Farklı |

---

## Neden Hepsi Benziyor?

1. **Stil bilgisi sonda:** Diffusion modelleri genelde prompt'un başındaki token'lara daha fazla ağırlık verir. STYLE block en sonda olduğu için stil etkisi zayıf kalıyor.

2. **StyleConfig kullanılmıyor:** PIXAR_STYLE, WATERCOLOR_STYLE, ANIME_STYLE vb. tanımlar var ama V2 path'ta hiç devreye girmiyor. Yani stil farklılaştıran prefix/suffix'ler prompt'a eklenmiyor.

3. **3D Pixar, Watercolor, Ghibli için başta stil yok:** Sadece 2D stiller "2D children's picture-book illustration style. " alıyor. Diğer stiller için başta hiç stil vurgusu yok.

4. **Model önyargısı:** Flux/PuLID büyük olasılıkla 3D animasyon verisiyle yoğun eğitilmiş. Stil baskısı zayıf olunca model varsayılan 3D Pixar benzeri çıktıya kayıyor.

5. **Gövde hep aynı:** Sahne + kıyafet + kompozisyon her stil için aynı yapıda. Fark sadece sonda uzun STYLE metni ile sağlanıyor; bu da yeterince etkili olmuyor.

---

## Önerilen Çözüm

**compose_visual_prompt** içinde `style_modifier` ile `get_style_config` kullanarak her stil için prompt'un **başına** stil-spesifik prefix eklenmeli:

| Stil | Önerilen baş prefix |
|------|---------------------|
| Pixar/3D/Disney | "Pixar Animation Studios 3D style. " |
| Watercolor | "Soft watercolor painting style. " |
| Anime/Ghibli | "Studio Ghibli anime style. " |
| Superhero | "3D superhero illustration style. " |
| Realistic | "Realistic children's book illustration. " |
| Vintage | "Vintage 1950s Golden Books style. " |
| Game | "Colorful video game art style. " |
| Storybook/Kaligrafik | "Elegant fairy tale storybook style. " |
| 2D/Children's book | (mevcut) "2D children's picture-book illustration style. " |
| Default | "Whimsical children's book illustration. " |

Bu prefix'ler StyleConfig'teki `prefix` değerlerinden türetilebilir (ilk cümle veya özet).

---

## Sonuç

Stillerin benzer görünmesinin nedeni **hardcoded tek bir efekt** değil, **StyleConfig stil prefix/suffix'lerinin V2 path'ta hiç kullanılmaması**. Stil farklılaşması yalnızca sonda eklenen STYLE block'a dayanıyor; bu da model tarafından yeterince ağırlıklandırılmıyor.

## Uygulanan Çözüm (2024-02)

1. **StyleConfig** dataclass'a `leading_prefix` alanı eklendi.
2. Her stil preset'ine stil-spesifik `leading_prefix` atandı:
   - PIXAR: "Pixar Animation Studios 3D style. "
   - WATERCOLOR: "Soft watercolor painting style. "
   - ANIME: "Studio Ghibli anime style. "
   - SUPERHERO: "3D superhero illustration style. "
   - REALISTIC: "Realistic children's book illustration. "
   - VINTAGE: "Vintage 1950s Golden Books style. "
   - GAME: "Colorful video game art style. "
   - STORYBOOK: "Elegant fairy tale storybook style. "
   - 2D/children's book: "2D children's picture-book illustration style. "
3. **get_style_leading_prefix(style_modifier)** fonksiyonu eklendi.
4. **compose_visual_prompt** içinde prompt'un başına bu prefix ekleniyor (STYLE block'tan önce).

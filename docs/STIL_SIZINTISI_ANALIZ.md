# Stil sızıntısı analizi – 3D Pixar testinde suluboya çıkması

## Sorun

3D Pixar stili ve verilen Pixar pozitif/negatif prompt’ları ile test yapıldığında çıktı **suluboya** stilde geliyor. Yani başka bir stil (suluboya) görsel prompta sızıyor.

## Akış (kısa)

1. **Admin → Stil testi:** `POST /api/v1/admin/visual-styles/{style_id}/test`
2. **Stil:** `style_id` ile DB’den `VisualStyle` alınıyor; `style_modifier = style.prompt_modifier`, `style_negative_en = style.style_negative_en`.
3. **Prompt:** `compose_visual_prompt(..., style_prompt_en=style_modifier, ...)` çağrılıyor.
4. **Hangi stilin kullanıldığı:** `get_style_config(style_modifier)` ile **constants.py**’daki eşleme yapılıyor; dönen `StyleConfig`’in `leading_prefix` ve `style_block`’u prompta kullanılıyor.

Yani **pozitif prompttaki stil metni** (Transparent watercolor… / Pixar-quality 3D CGI…) **DB’deki prompt_modifier metninden değil**, `get_style_config(style_modifier)` sonucundan geliyor. `prompt_modifier` sadece **hangi StyleConfig’in seçileceğini** belirliyor.

## Sızıntının nedeni: eşleme sırası

`get_style_config()` içinde stil eşlemesi **sabit bir sırayla** yapılıyor:

1. 2d (ve "not 2d" kontrolü)
2. paper_craft
3. soft_pastel
4. anime_vivid
5. anime_cheerful
6. anime / ghibli
7. **watercolor** ← "watercolor", "sulu boya", "suluboya" aranıyor
8. toy-like / toy / action figure
9. **pixar** ← "pixar", "disney", "cinematic" aranıyor

**Watercolor, Pixar’dan önce kontrol ediliyor.** Bu yüzden:

- 3D Pixar stili için `prompt_modifier` alanına uzun bir metin (veya benzeri) yazıldığında, metinde **hem “pixar” hem “watercolor”** geçebilir (ör. “Pixar 3D with soft watercolor sky” veya benzeri bir ifade).
- İlk eşleşen **watercolor** olduğu için `get_style_config` **WATERCOLOR_STYLE** döndürüyor; **PIXAR_STYLE** hiç denenmiyor.
- Sonuç: Görsel prompta **suluboya** `leading_prefix` ve `style_block` kullanılıyor → çıktı suluboya.

Ayrıca Admin’de **yanlış karttan** (suluboya stiline ait `style_id` ile) test yapılıyorsa, `style.prompt_modifier` zaten suluboya anahtar kelimelerini içerir ve yine watercolor eşleşir.

## Çözüm

**3D stilleri (Pixar, toy_3d) watercolor’dan önce** kontrol edilecek şekilde `get_style_config()` (ve aynı sırayı kullanan `get_style_anchor()`, `get_style_negative_default()`) güncellendi. Böylece:

- `prompt_modifier` içinde "pixar", "disney" veya "cinematic" geçiyorsa → **PIXAR_STYLE** seçilir (watercolor’a düşmez).
- "toy-like", "toy", "action figure" geçiyorsa → **TOY_3D_STYLE** seçilir.
- Hiçbiri yoksa, "watercolor" vb. ile **WATERCOLOR_STYLE** seçilmeye devam eder.

Böylece 3D Pixar stili ile test yapıldığında, modifier’da "pixar"/"disney"/"cinematic" varsa artık suluboya sızıntısı olmaz.

## Kontrol listesi (Admin tarafı)

- Test ettiğiniz satır/kart gerçekten **3D Pixar** stiline ait mi? (Doğru `style_id`.)
- 3D Pixar stilin **Prompt modifier** alanında **mutlaka** şunlardan en az biri geçsin: **pixar**, **disney**, **cinematic**. Örn: `cinematic 3D animation style, Disney Pixar quality, warm lighting, vibrant colors`.
- Aynı modifier içinde "watercolor" veya "sulu boya" geçirmeyin; geçerse ve kod eski sırada kalsaydı suluboya seçilirdi. Yeni sıra ile pixar önce arandığı için artık "pixar" varsa Pixar seçilir.

# Kullanıcı vs Admin: Hikaye Altındaki Prompt Farkı

## Neden farklı görünüyor?

1. **Kullanıcı (frontend)**  
   Hikaye altında gördüğü prompt, **create story** veya **sipariş gönder** anında ekranda olan veri:
   - `storyStructure.pages[].visual_prompt` → hikaye oluşturma API cevabından gelir.
   - Sipariş gönderildikten sonra frontend bu state’i yeniden çekmez; ekranda hep **ilk gelen prompt** kalır.

2. **Admin panel**  
   Preview detay **veritabanından** alınır:
   - `_story_pages_for_display(preview)` → `get_display_visual_prompt(..., prompt_debug_json)` kullanır.
   - Görsel üretildikten sonra `prompt_debug_json[].final_prompt` (Fal’a giden) kaydedilir; admin bu alanı öncelikli gösterir.
   - İsterseniz `story_pages[].visual_prompt` da backend tarafında bu final_prompt ile güncellenir.

Yani:
- **Kullanıcı:** İlk API cevabındaki / ekranda kalan prompt (görsel üretiminden önceki).
- **Admin:** DB’deki `prompt_debug_json.final_prompt` (Fal’a giden, güncel) veya güncellenmiş `story_pages.visual_prompt`.

Bu yüzden “hikaye altında” kullanıcı farklı, admin farklı prompt görebilir.

## Tek kaynak: Fal’a giden = prompt_debug

- Fal’a giden metin: `prompt_debug_json[page].final_prompt` (veya güncellenmiş `story_pages[].visual_prompt`).
- Admin zaten bu kaynağı kullanıyor (`get_display_visual_prompt` + `prompt_debug`).
- Kullanıcı tarafında da **aynı** metni göstermek için, kullanıcıya dönen tüm yerlerde bu kaynağı kullanmak gerekir.

## Önerilen çözüm

Kullanıcı “siparişim / hikayem” sayfasında veya onay sonrası detay görüyorsa:

- Bu sayfa **backend’den** preview/order detayı çekmeli (örn. token ile GET preview).
- Backend bu endpoint’te **admin ile aynı** mantığı kullanmalı: `prompt_debug_json.final_prompt` varsa onu, yoksa `story_pages[].visual_prompt` dönmeli (yani `_story_pages_for_display` / `get_display_visual_prompt`).
- Frontend bu response’taki `story_pages[].visual_prompt` alanını “hikaye altındaki prompt” olarak göstermeli.

Böylece:
- Görsel üretildikten sonra hem admin hem kullanıcı **Fal’a giden** prompt’u görür.
- Create flow’da (görsel üretilmeden önce) kullanıcı gördüğü prompt, yine backend’in compose ettiği ve ileride Fal’a gidecek metinle uyumlu olur (passthrough ile çift sarma kaldırıldığı için).

## Özet

| Kaynak        | Kullanıcı (şu an)     | Admin                |
|---------------|------------------------|----------------------|
| Veri          | İlk API cevabı (state) | DB (prompt_debug + story_pages) |
| Görünen prompt | İlk compose / ilk kayıt | Fal’a giden (final_prompt) |

Farkı kaldırmak için: Kullanıcı tarafında da preview/order detayı **backend’den** alınıp, **admin ile aynı** prompt kaynağı (prompt_debug / güncel story_pages) kullanılmalı.

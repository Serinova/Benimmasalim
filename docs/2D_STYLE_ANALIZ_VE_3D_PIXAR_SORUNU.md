# 2D Children's Book Stil Analizi – Kaynak ve 3D/Pixar Hissi Sorunu

## 1. "2D CHILDREN'S BOOK STYLE" nereden geliyor?

- **Stil adı:** Admin → Görsel Stiller’de gördüğünüz isim (örn. "2D CHILDREN'S BOOK STYLE") **sadece etiket**. Frontend’de varsayılan listede (Sihirli Animasyon, Sulu Boya, Anime Masalı vb.) bu isimle bir kart yok; bu stil muhtemelen Admin’den eklenen özel bir kayıt.
- **Prompt içeriği:** Tamamen **backend** → `backend/app/prompt_engine/constants.py`:
  - **Eşleme:** Sipariş/testte kullanılan `style_modifier` = DB’deki **VisualStyle.prompt_modifier** (veya frontend’in gönderdiği stil metni). `get_style_config(style_modifier)` bu metne bakıyor.
  - **"2d"** kelimesi geçiyorsa (ve "not 2d" yoksa) → **DEFAULT_STYLE** seçiliyor.
  - **DEFAULT_STYLE** = sadece `style_block` override; `leading_prefix` ise **StyleConfig** dataclass’ının default değeri:
    - `"Art style: Warm soft 2D hand-painted storybook illustration. Visible pencil underdrawing beneath soft gouache paint, cream-colored paper texture showing through, gentle muted earth tones... NOT 3D, NOT digital, NOT anime. "`
  - **style_block:** `"Warm soft 2D children's book illustration, hand-painted storybook look, visible brushwork, gentle colors... NOT 3D, NOT Pixar, NOT CGI..."`
- Yani gördüğünüz prompt ile sistemdeki 2D stil **aynı kaynaktan**; farklı bir yerden alınmıyor. İsim Admin’de ne yazıyorsa o, içerik her zaman constants’taki bu sabitlerden.

---

## 2. Neden 3D / Pixar hissi veriyor?

- **Prompt tarafı doğru:** "NOT 3D, NOT Pixar, NOT CGI", "hand-painted", "visible brushwork", "pencil underdrawing", "cream-colored paper texture" hepsi var.
- **Model davranışı:** Hem Fal hem Gemini, bu “organik doku” talimatlarını zayıf uyguluyor; çıktı **smooth, temiz, dijital** oluyor. Gölgelendirme hafif volümetrik olduğu için 3D/Pixar hissi oluşuyor.
- **Analiz özeti:**
  - "Visible pencil underdrawing", "cream-colored paper texture", "visible brushwork" çıktıda **yok**.
  - Yüzeyler düz, gradient’ler yumuşak; "flat gouache layers" yerine "digital polish" var.
  - Negatif prompt "3d render, cgi" içerse de model tam anlamıyla "el boyaması" dokusuna gitmiyor; stil olarak 2D ama **hissiyat** Pixar-ish kalıyor.

Yani **sorun kaynağı:** Prompt değil; **modelin "hand-painted / gouache / paper texture" ile "smooth digital 2D" arasında kalması**. İçerik (Kapadokya, çocuk, kıyafet, oran) doğru; stil dokusu yanlış.

---

## 3. Ne yapılabilir? (Prompt tarafında)

- **Pozitif promptu daha “doku odaklı” güçlendirmek:**
  - "Visible brush strokes", "rough paper texture", "flat color layers", "no smooth gradients", "matte painted surfaces", "traditional gouache opacity" gibi ifadeleri **başa** veya STYLE bloğuna ekleyebilirsiniz (constants.py → DEFAULT_STYLE / StyleConfig default leading_prefix).
- **Negatif promptu netleştirmek:**
  - "smooth rendering", "digital clean", "plastic surface", "Pixar", "CGI", "subsurface scattering", "rim lighting" zaten veya ek olarak kullanılabilir.
- **Stil eşlemesini kontrol etmek:**
  - Admin’de "2D CHILDREN'S BOOK STYLE" stilin **prompt_modifier** alanında mutlaka **"2d"** veya **"2D"** geçsin; yoksa `get_style_config` başka bir stile (ör. fallback) düşebilir. Fallback da DEFAULT_STYLE ama leading_prefix farklı olabilir.

---

## 4. Kısa cevap

| Soru | Cevap |
|------|--------|
| Stil ismi ile içerik farklı mı? | Hayır. İçerik constants’tan; isim Admin’den. Aynı 2D stilden geliyor. |
| İçerik başka yerden mi alınıyor? | Hayır. Hep `constants.py` + `compose_visual_prompt`. |
| 3D/Pixar hissinin kaynağı? | Modelin "hand-painted / texture" talimatını zayıf uygulaması; prompt doğru. |
| Ne yapılmalı? | Doku odaklı ifadeleri artırmak, negatifi netleştirmek; gerekirse DEFAULT_STYLE / leading_prefix’i güncellemek. |

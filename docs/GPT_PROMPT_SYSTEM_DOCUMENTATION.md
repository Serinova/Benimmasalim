# BenimMasalım - AI Prompt Sistemi Dokümantasyonu

Bu doküman, GPT projenizde yeni senaryolar, görsel stiller ve prompt'lar oluşturmanız için sistemin nasıl çalıştığını detaylı olarak açıklar.

---

## 📖 GENEL MİMARİ

Sistem **İKİ AŞAMALI** bir yapı kullanır:

```
[Kullanıcı Girdileri] → [PASS 1: Hikaye Yazımı] → [PASS 2: Görsel Promptlar] → [Fal.ai Görsel Üretim]
                              (Gemini)                    (Gemini)                  (Flux/PuLID)
```

### Temel Bileşenler:
1. **Senaryo (Scenario)** - Hikayenin teması ve mekanı
2. **Görsel Stil (Visual Style)** - Sanat stili (Anime, Pixar, Suluboya vb.)
3. **Kazanımlar (Learning Outcomes)** - Eğitsel değerler
4. **Prompt Template'leri** - AI talimatları

---

## 🎭 PASS 1: HİKAYE YAZIMI (Pure Author)

### Amaç
Duygusal, etkileyici, çocukları büyüleyen bir hikaye METNI yazmak.
JSON yok, görsel prompt yok - sadece SAFI HİKAYE.

### Sistem Promptu: `PURE_AUTHOR_SYSTEM`

```
🌟 SEN DÜNYA STANDARTLARINDA BİR ÇOCUK KİTABI YAZARISIN 🌟

Görevin: Çocukları büyüleyen, duygusal derinliği olan, hayal gücünü ateşleyen 
BİR BAŞYAPIT yazmak. Teknik format DÜŞÜNME - sadece HARİKA BİR HİKAYE YAZ!

📚 YAZIM İLKELERİ:

1️⃣ DUYUSAL DETAYLAR (Göster, Anlatma!)
   ❌ YANLIŞ: "Çocuk mutlu oldu."
   ✅ DOĞRU: "Kalbi sevinçten zıpladı. Yanakları kızardı, gözleri ışıl ışıl parladı."

2️⃣ DUYGUSAL DERİNLİK
   - Çocuğun İÇ DÜNYASINI yaz: merak, heyecan, korku, cesaret, şaşkınlık
   - "Ne hissetti?" sorusunu her sahnede sor

3️⃣ SESLİ OKUMAYA UYGUN RİTİM
   - Kısa ve uzun cümleler karışık
   - Tekrarlar: "Adım adım, taş taş, yükseldi, yükseldi..."
   - Ses efektleri: "Vızz!", "Pat pat pat ayak sesleri"

4️⃣ BÜYÜLÜ ANLAR
   - Her sayfada en az bir "WOW!" anı
   - Beklenmedik keşifler, sürprizler

5️⃣ KİŞİSEL MACERA
   ❌ YANLIŞ: Gezi rehberi tarzı bilgi yığını
   ✅ DOĞRU: Çocuğun KİŞİSEL deneyimi

⚠️ ASLA YAPMA:
- Turistik bilgi paragrafları
- Ansiklopedi cümleleri
- Robotik, duygusuz anlatım
```

### Girdi Değişkenleri:
- `{child_name}` - Çocuğun adı
- `{child_age}` - Çocuğun yaşı
- `{child_gender}` - Çocuğun cinsiyeti
- `{scenario_name}` - Senaryo adı (örn: "Kapadokya Macerası")
- `{scenario_description}` - Senaryo açıklaması
- `{educational_values}` - Seçilen kazanımlar

---

## 🎬 PASS 2: GÖRSEL PROMPTLAR (AI Director)

### Amaç
Hikayeyi sayfalara bölmek ve her sayfa için **Fal.ai'ye GÖNDERİLMEYE HAZIR** görsel promptlar üretmek.

### Sistem Promptu: `AI_DIRECTOR_SYSTEM`

```
🎬 SEN BİR UZMAN SANAT YÖNETMENİSİN

Görevin: Her sayfa için Fal.ai (Flux Model) görsel üretim API'sine 
GÖNDERİLMEYE HAZIR, TAM VE EKSİKSİZ bir prompt üretmek.

⭐ PROMPT YAPISI (Bu sırayı MUTLAKA takip et):

1️⃣ SAHNE & MEKAN (Scene & Location) - EN ÖNCE:
   "A wide-angle cinematic shot of [LOCATION DETAILS]. [SPECIFIC SETTING]."
   
   Örnekler:
   - Dış mekan: "vast Cappadocia valley with dozens of towering fairy chimneys, 
                 colorful hot air balloons floating in golden sunrise sky"
   - İç mekan: "deep inside an ancient underground city, rough carved stone tunnels, 
                flickering torchlight, mysterious shadows"

2️⃣ KARAKTER & AKSİYON (Character & Action):
   "A [AGE]-year-old [GENDER] child named [NAME], [ACTION], wearing [CLOTHING]."
   
   ⚠️ ASLA "standing and looking at camera" yazma!
   ✅ Dinamik pozlar: "gazing up in wonder", "reaching towards", "running through"

3️⃣ GÖRSEL STİL (Visual Style) - SONA EKLE:
   "[STYLE KEYWORDS]. Children's book illustration."
   
   Örnek: "Studio Ghibli anime art style, cel-shaded animation, soft pastel colors"

4️⃣ TEKNİK AYARLAR (Her prompt'un sonunda):
   "Wide angle f/8, detailed background, child 30% of frame, environment 70%."
```

### Tam Prompt Örneği:

```
"A wide-angle cinematic shot of the majestic Cappadocia valley at golden sunrise, 
dozens of colorful hot air balloons floating against orange-pink sky, towering 
fairy chimney rock formations stretching to the horizon. A 9-year-old boy named 
Uras standing heroically on a cliff edge, arms spread wide, wearing a red 
adventure jacket and blue jeans, wind blowing through his hair, gazing at the 
magical landscape. Studio Ghibli anime art style, cel-shaded animation, vibrant 
colors, epic adventure mood. Children's book cover illustration. Wide angle f/8, 
detailed background, child 30% of frame, landscape 70%."
```

### 🔒 KRİTİK KURAL: KIYAFET KİLİDİ

Çocuk TÜM KİTAP BOYUNCA AYNI KIYAFETİ giymelidir!

```
✅ DOĞRU:
- Sayfa 1: "...wearing a red adventure jacket and blue jeans..."
- Sayfa 5: "...wearing a red adventure jacket and blue jeans..."  
- Sayfa 15: "...wearing a red adventure jacket and blue jeans..."

❌ YANLIŞ:
- Sayfa 1: "...wearing a t-shirt..."
- Sayfa 5: "...putting on a warm coat..."
- Sayfa 15: "...wearing a hat and scarf..."
```

---

## 🎯 SENARYO (Scenario) YAPISI

Senaryo, hikayenin temasını ve mekanını tanımlar.

### Veritabanı Alanları:

| Alan | Açıklama | Örnek |
|------|----------|-------|
| `name` | Senaryo adı | "Kapadokya Macerası" |
| `description` | Açıklama | "Peri bacaları arasında büyülü bir yolculuk" |
| `thumbnail_url` | Önizleme resmi | URL |
| `cover_prompt_template` | Kapak için prompt şablonu | Aşağıda |
| `page_prompt_template` | İç sayfalar için prompt şablonu | Aşağıda |
| `ai_prompt_template` | Hikaye üretimi için Gemini talimatı | Opsiyonel |
| `location_constraints` | Mekan kısıtlamaları | "fairy chimneys, hot air balloons" |
| `cultural_elements` | Kültürel öğeler (JSON) | `{"primary": ["fairy chimneys"]}` |
| `theme_key` | Tema anahtarı | "cappadocia" |
| `custom_inputs_schema` | Dinamik girdiler (JSON) | Aşağıda |

### Prompt Template Değişkenleri:

```
{book_title}           - Kitap başlığı (sadece kapak)
{scene_description}    - Sahne açıklaması (AKSİYON-ODAKLI!)
{clothing_description} - Kıyafet açıklaması
{visual_style}         - Seçilen görsel stil
```

### Örnek Cover Prompt Template:

```
A beautiful children's book cover illustration for a story called "{book_title}".
The scene shows a young child {scene_description}.
The child is wearing {clothing_description}.
{visual_style}.
The composition is designed as a professional book cover with space for the title at the top.
```

### Örnek Page Prompt Template:

```
A children's book illustration showing a young child {scene_description}.
The child is wearing {clothing_description}.
{visual_style}.
The scene has a clear focal point with soft background, suitable for text overlay at the bottom.
```

### Custom Inputs Schema (Dinamik Girdiler):

Senaryoya özel ek alanlar tanımlanabilir:

```json
[
  {
    "key": "spaceship_name",
    "label": "Uzay Gemisi Adı",
    "type": "text",
    "default": "Yıldız Kaşifi",
    "required": true,
    "placeholder": "Örn: Apollo, Keşif-1"
  },
  {
    "key": "favorite_planet",
    "label": "En Sevdiği Gezegen",
    "type": "select",
    "options": ["Mars", "Jüpiter", "Satürn"],
    "required": false
  }
]
```

---

## 🎨 GÖRSEL STİL (Visual Style) YAPISI

Her görsel stil, AI görsel üretimine eklenen bir "stil modifiyeri" içerir.

### Veritabanı Alanları:

| Alan | Açıklama | Örnek |
|------|----------|-------|
| `name` | Stil adı | "Studio Ghibli Anime" |
| `thumbnail_url` | Önizleme resmi | URL |
| `prompt_modifier` | Fal.ai'ye eklenen stil | Aşağıda |
| `id_weight` | PuLID yüz benzerlik ağırlığı | 0.35 |
| `cover_aspect_ratio` | Kapak en-boy oranı | "2:3" |
| `page_aspect_ratio` | Sayfa en-boy oranı | "1:1" |

### Prompt Modifier Örnekleri:

#### 1. Studio Ghibli Anime
```
Studio Ghibli anime art style, cel-shaded animation, soft pastel colors, 
dreamy atmosphere, hand-painted backgrounds, whimsical character design, 
gentle lighting, nostalgic Japanese animation aesthetic
```

#### 2. Pixar/Disney 3D
```
Pixar Disney 3D animation style, vibrant saturated colors, expressive 
character design, cinematic lighting, magical atmosphere, detailed textures, 
professional CGI render quality
```

#### 3. Suluboya (Watercolor)
```
Watercolor painting style, soft brush strokes, gentle color washes, 
dreamy atmosphere, artistic illustration, hand-painted aesthetic, 
delicate details, traditional art feeling
```

#### 4. Vintage Retro
```
Vintage children's book illustration, retro 1950s art style, warm muted 
colors, nostalgic aesthetic, classic storybook look, gentle character 
design, timeless quality
```

#### 5. Gerçekçi Dijital
```
Digital painting, semi-realistic style, detailed character portraits, 
rich color palette, professional illustration, cinematic lighting, 
high quality digital art
```

### id_weight Değerleri:

PuLID yüz tutarlılığı için:
- **0.18-0.25**: Çok stilize (anime, cartoon) - yüz daha az gerçekçi
- **0.30-0.40**: Dengeli (çoğu stil için ideal)
- **0.45-0.55**: Gerçekçi stiller - yüz daha benzer

---

## 📚 KAZANIMLAR (Learning Outcomes) YAPISI

Eğitsel değerler hikayenin PLOT'unu yönlendirir.

### Veritabanı Alanları:

| Alan | Açıklama |
|------|----------|
| `name` | Kazanım adı (Türkçe) |
| `description` | Kısa açıklama |
| `category` | Kategori (SelfCare, PersonalGrowth, SocialSkills, EducationNature) |
| `ai_prompt` | AI'ya gönderilen talimat |
| `icon_url` | Kart ikonu |
| `color_theme` | Kart renk teması |

### Kategori ve Kazanım Örnekleri:

#### 🌱 Eğitim & Doğa (EducationNature)
```
- Doğa ve Hayvan Sevgisi
- Kitap Okuma Sevgisi
- Ekran Süresi Dengesi
- Merak ve Keşfetmek
- Çevre Temizliği
```

#### 👤 Kişisel Gelişim (PersonalGrowth)
```
- Cesaret ve Özgüven
- Sabırlı Olmak
- Hata Yapmaktan Korkmamak
- Liderlik
- Duygularını İfade Etme
```

#### 🧼 Öz Bakım (SelfCare)
```
- Diş Fırçalama Alışkanlığı
- Sağlıklı Beslenme
- Düzenli Uyku
- Tuvalet Eğitimi
- El Yıkama ve Hijyen
```

#### 🤝 Sosyal Beceriler (SocialSkills)
```
- Paylaşmak Güzeldir
- Özür Dilemek
- Kardeş Sevgisi
- Yardımseverlik
- Arkadaşlık Kurmak
```

### AI Prompt Örneği (Cesaret):

```
Çocuk bir KORKUYLA YÜZLEŞMELİ ve onu yenmeli!

- Karanlık bir mağara, yüksek bir yer, yabancı bir ortam olabilir
- Önce korku hissetmeli: "Kalbi küt küt atmaya başladı, dizleri titredi..."
- Sonra cesaret bulmalı: "Derin bir nefes aldı ve ilk adımı attı..."
- Başardığında gurur duymalı: "İçinde bir aslan gibi güçlü hissetti!"

ÖRNEK SAHNE: Karanlık yeraltı şehrine tek başına girmek zorunda kalır.
```

---

## 🖼️ FAL.AI GÖRSEL ÜRETİM

### Kullanılan Modeller:

1. **fal-ai/flux/dev** - Standart görsel üretim
2. **fal-ai/flux-pulid** - Yüz tutarlılığı ile üretim (çocuk fotoğrafından)

### Görsel Boyutları:

| Şablon Tipi | Boyut (px) | Açıklama |
|-------------|------------|----------|
| Yatay (A4 Landscape) | 1344x768 | Geniş sahneler |
| Dikey (Portrait) | 768x1344 | Uzun sahneler |
| Kare (Square) | 1024x1024 | Dengeli |
| Cep Boy | 832x1216 | Küçük kitap |

### Negative Prompt (Kaçınılacaklar):

```
close up, portrait, asian architecture, chinese text, japanese text, 
korean architecture, nsfw, nude, blood, gore, violence, scary, horror, 
deformed, mutated, disfigured, ugly, blurry, low quality, watermark, 
text, signature, multiple children, crowd, group of people
```

---

## 🔧 YENİ İÇERİK OLUŞTURMA REHBERİ

### Yeni Senaryo Eklerken:

1. **Benzersiz bir tema belirleyin**
   - Mekan: Uzay, Deniz altı, Orman, Şehir vb.
   - Kültür: Türk, Japon, Mısır vb.

2. **Cover Prompt Template yazın**
   ```
   A beautiful children's book cover for "{book_title}".
   [MEKAN SPESİFİK DETAYLAR].
   A young child {scene_description}, wearing {clothing_description}.
   {visual_style}.
   Professional book cover composition with title space at top.
   ```

3. **Page Prompt Template yazın**
   ```
   A children's book illustration of [MEKAN].
   A young child {scene_description}, wearing {clothing_description}.
   {visual_style}.
   Clear focal point, soft background, text overlay space at bottom.
   ```

4. **Location Constraints tanımlayın**
   ```
   "underwater coral reef, colorful fish, bubbles, ocean floor"
   ```

5. **Cultural Elements (JSON) ekleyin**
   ```json
   {
     "primary": ["coral reef", "tropical fish", "sea turtle"],
     "colors": "ocean blues and teals",
     "atmosphere": "magical underwater glow"
   }
   ```

### Yeni Görsel Stil Eklerken:

1. **Stil adı ve açıklaması**

2. **Prompt Modifier yazın** (İngilizce, detaylı)
   ```
   [STIL ADI] art style, [TEKNIK DETAYLAR], [RENK PALETİ], 
   [ATMOSFER], [KALİTE TANIMLAYICILARI]
   ```

3. **id_weight belirleyin**
   - Anime/Cartoon: 0.18-0.25
   - Balanced: 0.30-0.40
   - Realistic: 0.45-0.55

### Yeni Kazanım Eklerken:

1. **Kategori seçin**

2. **AI Prompt yazın** (Türkçe)
   ```
   Çocuk [ÖĞRENME HEDEFİ] yapmalı!
   
   - [SENARYO DETAYI 1]
   - [DUYGU DETAYI]
   - [ÇÖZÜM DETAYI]
   - [SONUÇ DETAYI]
   
   ÖRNEK SAHNE: [SOMUT BİR ÖRNEK]
   ```

---

## 📋 PROMPT TEMPLATE KATEGORİLERİ

Veritabanında saklanabilen prompt tipleri:

| Kategori | Key Örneği | Açıklama |
|----------|------------|----------|
| `story_generation` | PURE_AUTHOR_SYSTEM | Hikaye yazımı sistem promptu |
| `visual_director` | AI_DIRECTOR_SYSTEM | Görsel prompt üretimi |
| `educational` | EDUCATIONAL_cesaret | Kazanım talimatları |
| `image_negative` | NEGATIVE_PROMPT | Fal.ai negatif prompt |
| `image_style` | STYLE_watercolor | Stil modifiyerleri |

---

## ⚡ HIZLI BAŞVURU

### Prompt Yazarken Dikkat Edilecekler:

✅ **YAPILMASI GEREKENLER:**
- İngilizce yazın (görsel promptlar için)
- Detaylı ve spesifik olun
- Dinamik pozlar kullanın
- Tutarlı kıyafet tanımı yapın
- Stil bilgisini sona ekleyin

❌ **YAPILMAMASI GEREKENLER:**
- "standing and looking at camera" gibi statik pozlar
- Belirsiz tanımlar ("nice scene")
- Her sayfada farklı kıyafet
- Fiziksel özellik tanımı (PuLID hallediyor)
- Türkçe görsel prompt

### Örnek İş Akışı:

```
1. Kullanıcı seçer:
   - Senaryo: "Kapadokya Macerası"
   - Stil: "Studio Ghibli Anime"
   - Kazanımlar: ["Cesaret", "Merak"]
   - Çocuk: Uras, 7 yaş, erkek

2. PASS 1 çıktısı:
   "Uras'ın kalbi heyecanla çarpıyordu. Peri bacalarının arasından 
   süzülen sıcak rüzgar yüzünü okşadı..."
   (16 sayfalık duygusal hikaye)

3. PASS 2 çıktısı:
   Page 1: "A wide-angle shot of Cappadocia valley at sunrise, 
   dozens of hot air balloons floating... A 7-year-old boy named 
   Uras gazing up in wonder, wearing a red jacket... Studio Ghibli 
   anime style..."

4. Fal.ai görsel üretir
```

---

## 📞 DESTEK

Bu dokümantasyon, GPT projenizde yeni içerik oluşturmanız için hazırlanmıştır.
Sistem dinamik olarak veritabanından prompt'ları yükleyebilir, böylece admin 
panelinden değişiklik yapabilirsiniz.

**Dosya Konumu:** `/GPT_PROMPT_SYSTEM_DOCUMENTATION.md`
**Tarih:** 2026-02-04

# 2D vs 3D Stil Prompt Karşılaştırması

## Senin sistem prompt’ları (özet)

**2D:**  
2D children's picture-book cartoon illustration, clean crisp lineart with medium outlines (not thick), simplified shapes, soft pastel color palette, **smooth soft shading with gentle gradients**, subtle paper texture, **warm soft ambient light**, clear readable composition, **foreground/midground/background layering**, storybook illustration feel, NO cinematic look, NO film still, NO lens terms, NO volumetric effects, NO dramatic contrast.

**3D:**  
3D animated children's book illustration, family-friendly modern 3D animation, **soft shadows**, vibrant but **warm** colors, friendly character design with **natural human proportions and small realistic eyes**, **smooth stylized shapes, clean surfaces**, **gentle global illumination**, high-quality 3D render look, wholesome storybook mood, **clear foreground/midground/background depth**, readable simple background in sharp focus, **soft ambient light**, high detail but not cluttered, **consistent character across pages**.

---

## Ortak kelimeler / kavramlar (çıktıyı birbirine benzeten)

| Kavram | 2D’de | 3D’de |
|--------|--------|--------|
| **smooth** | smooth soft shading | smooth stylized shapes, clean surfaces |
| **soft** | soft pastel, soft shading, soft ambient light | soft shadows, soft ambient light |
| **gentle** | gentle gradients | gentle global illumination |
| **warm** | (pastel palette ile his) | vibrant but warm colors |
| **ambient light** | warm soft ambient light | soft ambient light |
| **foreground/midground/background** | foreground/midground/background layering | clear foreground/midground/background depth |
| **readable composition** | clear readable composition | readable simple background |
| **storybook** | storybook illustration feel | wholesome storybook mood |
| **natural proportions / eyes** | (sadece negatifte chibi/big eyes yok) | natural human proportions, small realistic eyes |
| **consistent character** | (yok) | consistent character across pages |

Bu ortaklıklar modeli “yumuşak, okunaklı, storybook, katmanlı sahne” ortak paydasına çekiyor; 2D’yi de 3D’yi de benzer bir “temiz, soft” görünüme yaklaştırıyor.

---

## Sadece 2D’de olanlar (ayırt edici)

- **2D**, **picture-book**, **cartoon illustration**
- **lineart**, **medium outlines**, **simplified shapes**
- **soft pastel color palette**, **gentle gradients**
- **subtle paper texture**
- **NO** cinematic, film still, lens terms, **volumetric effects**, dramatic contrast

Yani 2D tarafında “çizgi, düz renk katmanları, kağıt dokusu, 3D/cinematic değil” var ama **“smooth soft shading”** ifadesi 3D’ye kaymayı kolaylaştırıyor.

---

## Sadece 3D’de olanlar (ayırt edici)

- **3D**, **animated**, **3D animation**, **3D render**
- **soft shadows**, **global illumination**, **clean surfaces**
- **high-quality 3D render look**
- **consistent character across pages**

3D tarafı net; fakat “soft”, “gentle”, “warm”, “ambient” 2D ile aynı olduğu için his olarak 2D’ye yakın “yumuşak 3D” çıkabiliyor.

---

## Negatif prompt farkı

| | 2D negatif | 3D negatif |
|--|------------|------------|
| Uzunluk | Kısa | Çok uzun (flat 2D, lineart, watercolor, oil paint, sketch, paper texture, vb.) |
| 3D’yi itme | 3d render, CGI | (3D stili zaten 3D istiyor) |
| 2D’yi itme | (yok) | flat 2D, lineart, watercolor, oil paint, sketch, paper texture |

2D pozitifte “NOT 3D” yok; sadece negatifte “3d render, CGI” var. 3D tarafında ise 2D görünümü negatifte açıkça reddediliyor. Bu da 2D seçildiğinde modelin 3D’ye kaymasını engellemekte 2D’nin daha zayıf kalmasına neden olabilir.

---

## Sonuç: Neden çıktılar birbirine benziyor?

1. **Çok ortak kelime:** “smooth”, “soft”, “gentle”, “warm”, “ambient light”, “foreground/midground/background”, “storybook”, “readable”. Model iki prompt’u da “yumuşak, temiz, storybook” ortak kümesine çekiyor.
2. **2D’de “smooth soft shading / gentle gradients”:** Bu ifade 3D’deki “smooth shapes / soft shadows” ile aynı yöne (pürüzsüz, yumuşak gölge) itiyor; 2D’yi “düz çizgi / flat color”dan uzaklaştırıyor.
3. **2D’de pozitifte “NOT 3D” yok:** Sadece negatifte 3D var; 3D tarafında ise “flat 2D, lineart…” negatifte. Yani 2D stili 3D’den ayıran sinyal 2D prompt’unda daha zayıf.
4. **3D negatifi 2D’yi çok net reddediyor:** “flat 2D, lineart, watercolor, paper texture” vb. 2D’de ise 3D’yi reddeden kısım kısa. Bu da “ortada” bir görünümü (hem 2D hem 3D’ye benzeyen) destekleyebilir.

---

## Öneri: İki stili daha net ayırmak

**2D prompt’unu:**
- “smooth soft shading”, “gentle gradients” yerine veya yanına: **flat color areas**, **visible lineart**, **no 3D shading**, **no volumetric lighting**, **matte flat shading** ekle.
- Pozitifte açık yaz: **NOT 3D, NOT CGI, NOT rendered, NOT smooth 3D lighting.**
- **Lineart / outline / simplified flat shapes** vurgusunu artır; “smooth” ile “soft shading”ı azalt veya “light flat shading” ile değiştir.

**3D prompt’unu:**
- “soft”, “gentle” tekrarlarını azalt; **3D render**, **subsurface scattering**, **rim light**, **ambient occlusion** gibi 3D’ye özgü terimleri koru veya artır.
- Negatifte “flat 2D, lineart” zaten var; 2D’de de 3D’yi negatifte güçlü tut.

**Genel:** Ortak kelimeleri (smooth, soft, gentle, warm, ambient) her iki prompt’ta da azaltıp, 2D’de “flat / lineart / paper / no 3D”, 3D’de “3D render / shadows / illumination” tarafını netleştirirsen çıktılar daha farklılaşır.

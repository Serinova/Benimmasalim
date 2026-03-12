"""Galata'nın Kayıp Işık Haritası — Galata Kulesi'nde ışık bulmacası.

TİP A: Tek Landmark (Galata Kulesi + Beyoğlu). Companion yok.
Obje: Işık Haritası Parşömeni
"""

from app.scenarios._base import ObjectAnchor, ScenarioContent
from app.scenarios._registry import register

GALATA = register(ScenarioContent(
    theme_key="galata",
    name="Galata'nın Kayıp Işık Haritası",
    location_en="Galata Tower",
    default_page_count=22,
    flags={"no_family": False},

    story_prompt_tr="""
# GALATA'NIN KAYIP IŞIK HARİTASI

## YAPI: {child_name} Galata Kulesi'nde eski bir parşömen buluyor — "Işık Haritası." Haritadaki sembolleri takip ederek Galata, Karaköy ve Beyoğlu sokaklarında ışık bulmacaları çözüyor. Sihir yok — optik illüzyonlar, yansımalar ve İstanbul'un gerçek tarihi mekanları.

**BAŞLIK:** "[Çocuk adı]'ın Kayıp Işık Haritası: Galata"

---

### Bölüm 1 — Kule'de Keşif (Sayfa 1-4)
- {child_name} Galata Kulesi'nde. Taş duvarlardaki çatlaklar arasında katlanmış eski bir parşömen.
- Parşömen güneş ışığına tutulunca semboller parlıyor — bir harita!
- Haritada 5 işaret: her biri İstanbul'un farklı ışık yansımalarına karşılık geliyor.
- Kuleden bakınca ilk işaretin tam karşıdaki camiyle hizalandığını görüyor.

### Bölüm 2 — Karaköy'de İpuçları (Sayfa 5-9)
- Dar Galata sokaklarında iniyor. İlk işaret: eski bir çeşmenin aynasında yansıyan ışık.
- Yansımayı takip ederek gizli bir avluya ulaşıyor — ikinci sembol burada!
- Balıkçılarla dolu Karaköy rıhtımı — denizden yansıyan ışık üçüncü ipucu.
- Her sembol çözüldüğünde parşömen biraz daha renkleniyor.

### Bölüm 3 — Beyoğlu'nda Kovalamaca (Sayfa 10-14)
- İstiklal'de tramvay geçerken anlık bir yansıma fark ediyor — dördüncü sembol!
- Tünel'e indığinde eski duvardaki mozaikler beşinci ipucunu veriyor.
- Parşömen tamamen renklendiğinde son mesaj ortaya çıkıyor: "Geri dön. Cevap başladığın yerde."

### Bölüm 4 — Kule'ye Dönüş (Sayfa 15-18)
- Galata Kulesi'ne geri tırmanıyor — bu sefer farklı bakıyor.
- Parşömeni kulenin tepesindeki pencereye tutuyor — tüm İstanbul üzerinde ışık haritası beliriyor!
- Her işaret bir tarihi öyküye karşılık: Ceneviz, Osmanlı, Cumhuriyet.
- "Bu şehir ışıkla yazılmış bir kitap" anlayışı.

### Bölüm 5 — Kapanış (Sayfa 19-22)
- Gün batımında kuleden İstanbul manzarası — altın, kırmızı, mor.
- Parşömeni kulenin bir taşına geri saklıyor — gelecek kaşifler bulsun.
- "İstanbul'un ışığını gördüm. Her köşede bir hikaye."
- Merdivenleri inerken gülümsüyor — macera bitti ama başkaları için başlayacak.

---

## 🚫 KURALLAR
- Companion YOK. {child_name} tek başına.
- Sihir/büyü YOK — optik ilüzyonlar ve gerçek ışık yansımaları.
- Didaktik nasihat YASAK. Gezi rehberi formatı YASAK.
- DUYGU: amazed, smiling, determined.
- IŞIK odaklı atmosfer: golden hour, reflections, light beams.

Hikayeyi TAM OLARAK {page_count} sayfa yaz.
""",

    cover_prompt_template=(
        'A young child standing at the top of Galata Tower with Istanbul panorama behind, '
        'wearing {clothing_description}. {scene_description}. '
        'Galata Tower stone walls, Istanbul skyline with minarets and Bosphorus. '
        'Golden sunset light beams, warm cinematic atmosphere. {STYLE}'
    ),
    page_prompt_template=(
        'A young child {scene_description}, wearing {clothing_description}. '
        'Istanbul Galata/Beyoğlu setting: narrow cobblestone streets, Ottoman architecture, '
        'warm golden light, stone textures. Cinematic lighting. {STYLE}'
    ),

    outfit_girl=(
        "soft lavender wool peacoat with silver buttons, cream cable-knit turtleneck sweater, "
        "dark navy pleated skirt, black patent leather ankle boots, "
        "a small vintage leather crossbody bag, and a lavender beret. "
        "EXACTLY the same outfit on every page."
    ),
    outfit_boy=(
        "camel-brown wool blazer with elbow patches, white button-down oxford shirt, "
        "dark navy chino trousers, brown leather chelsea boots, "
        "a small canvas messenger bag, and a brown flat cap. "
        "EXACTLY the same outfit on every page."
    ),

    companions=[],  # No companion
    objects=[
        ObjectAnchor(
            name_tr="Işık Haritası Parşömeni",
            appearance_en="ancient folded parchment map with light-reactive symbols that glow in sunlight",
            prompt_suffix="holding ancient parchment with glowing light symbols — SAME on every page",
        ),
    ],

    cultural_elements={
        "primary": ["Galata Tower (14th century Genoese)", "Karaköy fishing harbor", "İstiklal Avenue and tramway",
                     "Tünel (historic underground funicular)"],
        "secondary": ["Old Genoese stone walls", "Bosphorus light reflections", "Istanbul sunset panorama"],
        "atmosphere": "Mysterious, light-filled, urban adventure",
    },

    location_constraints=(
        "Pages 1-4: Galata Tower interior and panoramic view. (Wide Shot, golden) "
        "Pages 5-9: Karaköy streets, old fountains, harbor. (Medium Shot, reflections) "
        "Pages 10-14: Beyoğlu, İstiklal, Tünel passage. (Dynamic, colorful) "
        "Pages 15-18: Return to Galata Tower top. (Wide panoramic, sunset) "
        "Pages 19-22: Sunset from tower, farewell. (Hero Shot, golden hour)"
    ),

    scenario_bible={},
    custom_inputs_schema=[],
))

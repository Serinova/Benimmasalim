"""Kutsal Topraklara Ziyaret — Umre senaryosu.

DB'den birebir alınmıştır. İçerik değiştirilmemiştir.
"""

from app.scenarios._base import ScenarioContent
from app.scenarios._registry import register

UMRE = register(ScenarioContent(
    # ── A: Temel Kimlik ──
    theme_key="umre_pilgrimage",
    name="Kutsal Topraklara Ziyareti",

    # ── B: Teknik ──
    location_en="Mecca and Medina",
    default_page_count=22,
    flags={"no_family": False},

    # ── E: Hikaye Promptu ──
    story_prompt_tr="""
# KUTSAL TOPRAKLARA ZİYARET — UMRE

## YAPI: {child_name} KAFİLE İLE UMRE YAPIYOR. UÇAK SAHNESİ YOK.

**KRİTİK — METİN UZUNLUĞU:** Her sayfa MUTLAKA kısa olsun; sayfaya sığmalı. Her sayfa 1-3 cümle, toplam 25-50 kelime. Daha uzun yazma; kurguyu bozmadan %30 kısa tut.

**KIYAFET:** Erkekler ihrama girince 2 parça dikişsiz beyaz bez, BAŞ AÇIK (takke yok). Saç kesilene kadar ihramda. Saç kesildikten sonra takke (saç SADECE kesilir, tıraş/0'a vurma YOK; erkek kel çizilmez). Kızlar hicap giyer.

**AKIŞ:** Havalimanı → ihram hazırlığı ve giriş → (Cidde varışı sonrası) Kabeye doğru ihramla yürüyüş, Lebbeyk sesleri → Kabe ilk görüş (ilk görüşte duaların kabulü dileği vurgula) → Tavaf 3 sayfa → Sa'y 2 sayfa → Saç kesme 1 sayfa → Mekke'deki kubbeli mescide ziyaret 2 sayfa → Medine yolculuğu → Mescid-i Nebevi (Resulullah hakkında bilgi, hissiyat) → Uhud tepesi 1 sayfa → Hendek Savaşı 1 sayfa → Eve dönüş.

---

### Sayfa 1-2: Havalimanı, kafile, ihram hazırlığı
- {child_name} kafile ile havalimanında buluşuyor. Heyecanlı. Uçak sahnesi YOK.
- İhrama hazırlanıyorlar: beyaz, dikişsiz 2 parça bez. Niyet, telbiye. Baş açık kalacak (erkekler için).

### Sayfa 3: Cidde varışı, Kabeye doğru yürüyüş
- Cidde'ye varıldı. Kabeye doğru ihramlı yürüyüş. "Lebbeyk Allahümme Lebbeyk" sesleri her yerde.

### Sayfa 4-5: Kabe ilk görüş
- Mescid-i Haram'a adım. Kabe ilk kez görülüyor. Gözyaşları, huşu.
- İlk görüşte edilen duaların kabul edildiği inancı vurgula. {child_name} içinden ne dilerse kalbiyle orada.

### Sayfa 6-8: Tavaf (3 sayfa)
- Tavafa başlama — Hacerülesved, 7 tur. İhramda, baş açık.
- Tavafın anlamı: Kabe etrafında birlikte dönmek, tek yürek. Kısa vurgu.
- Tavaf bitişi. Makam-ı İbrahim, Zemzem bir yudum.

### Sayfa 9-10: Sa'y (2 sayfa)
- Safa'dan Merve'ye 7 gidiş-geliş başlıyor. Hz. Hacer'in hikâyesi kısaca.
- Sa'y bitişi. Yoruldu ama tamamladı.

### Sayfa 11: Saç kesme
- Saç kesiliyor (tıraş değil, sadece kesim). İhramdan çıkış. Yenilenme, huzur. Sebebi ve hissiyatı kısa. Metinde "tıraş", "0'a vurma", "kel" GEÇMESİN.
- KRİTİK: Kız çocuğun saçını SADECE KADIN keser (anne, teyze, abla veya kadın kuaför). Erkek berber kızın saçına dokunmaz. Erkek çocuğun saçını erkek berber keser. Hikâyede ve sahne tasvirinde buna uygun yaz (kız ise kadın karakteri saç keserken göster).

### Sayfa 12-13: Mekke — kubbeli mescit ziyareti (2 sayfa)
- Mekke'deki kubbeli mescide ziyaret. Tarih, maneviyat.
- Orada anlatılanlar, {child_name}'ın hissettiği huzur. 2 sayfa toplam.

### Sayfa 14: Medine yolculuğu
- Medine'ye yolculuk. Yeşil kubbe uzaktan. Artık takke (erkek). Kızlar hicap.

### Sayfa 15: Mescid-i Nebevi, Resulullah
- Mescid-i Nebevi. Yeşil kubbe. Resulullah (sav) hakkında bilgi, saygı, hissiyat. Görselleştirme yok, sadece anlatım.

### Sayfa 16: Uhud tepesi
- Uhud tepesi ziyareti. Tarihî önemi kısaca, bir sayfa.

### Sayfa 17: Hendek Savaşı
- Hendek (Ahzab) hatırası. Bir sayfa vurgu.

### Sayfa 18+: Eve dönüş ve kapanış
- Eve dönüş. "Kutsal topraklar beni değiştirdi." Kısa, duygusal kapanış. Kalan sayfa sayısına göre 1-2 sayfa.

---

## 🚫 GÖRSEL KURALLAR
- Sayfa 1-2: Henüz ihram yok veya hazırlık (erkekte baş açık).
- Sayfa 3-10: İHRAM — 2 parça beyaz bez, BAŞ AÇIK (takke yok).
- Sayfa 11: Saç kesme anı (sadece kesim; tıraş/kel YOK). Kız çocuk varsa saçını KADIN keser (anne/teyze/kadın kuaför); erkek berber kızın saçına dokunmaz. Erkek çocukta erkek berber olabilir.
- Sayfa 12-22: Takke (erkek), normal saç — kel çizilmez. Kızlar hicap.
- Peygamber/melek görseli YOK. Vaaz yok, yaşayarak anlat.
- İlk sayfa [Sayfa 1] ile başla. Uçak, kabin, uçuş sahnesi ÇİZME.
- G2 tutarlılık KURALI: Çocuk karakteri her sayfada aynı tutarlı kıyafetle göster. Yüz ve saç görünümü değişmez!
- IŞIK VE DOKU (LIGHTING & TEXTURE): Mekke mermer dokusu (marble texture) ve sinematik kutsal ışık (cinematic lighting, golden glow) kesinlikle yer ver!
- Asla didaktik nasihat verme veya vaaz bildirme. YASAK!

Hikayeyi TAM OLARAK {page_count} sayfa yaz. Her sayfa 1-3 cümle (25-50 kelime). Kısa tut; sayfaya sığsın.
""",

    # ── F: Görsel Prompt Şablonları ──
    cover_prompt_template=(
        'An {child_age}-year-old {child_gender} named {child_name} with {hair_description}, '
        'wearing {clothing_description}. {scene_description}. Standing in the grand white marble '
        'courtyard before the magnificent black Kaaba draped in ornate golden Kiswah calligraphy '
        'embroidery. Towering golden minarets and grand Ottoman domes rising against a deep twilight '
        'sky, peaceful distant pilgrims in white ihram (small, no faces). Warm reverent golden light '
        'reflecting off polished marble, soft ambient glow from the minarets, gentle volumetric light '
        'around the Kaaba. Slightly low-angle shot: child 20% foreground, sacred architecture 80%. '
        'Sacred palette: pure white marble, deep black and gold Kiswah, warm amber glow, emerald '
        'green accents. NO airplanes, NO airport, NO glowing lights, NO magic, NO fairies, NO '
        'Prophet/angel depictions.'
    ),
    page_prompt_template=(
        'An {child_age}-year-old {child_gender} named {child_name} with {hair_description}, '
        'wearing {clothing_description}. {scene_description}. Locations: [Kaaba: black with golden '
        'Kiswah, white marble courtyard / Safa-Marwa: marble corridor / Masjid Nabawi: green dome / '
        'Zemzem: marble]. Islamic geometric patterns, calligraphy. Cinematic reverent lighting, warm '
        'golden glow, detailed marble texture. Close-up on the child\'s expressive face, wide for '
        'sacred architecture. Expressive emotion (amazed, smiling, determined). No eye contact with '
        'camera. Reverent and realistic. NO glowing lights, NO magic, NO fairies, NO Prophet '
        'depictions. {STYLE}'
    ),

    # ── G: Kıyafetler ──
    outfit_girl=(
        "pure white cotton modest long-sleeve dress reaching ankles with no patterns or decorations, "
        "PROPERLY WRAPPED white hijab: fabric wraps FULLY around the head and neck — NO hair visible, "
        "NO neck visible, fabric drapes softly over shoulders and chest, neat pin-free folds, same "
        "style as a modern proper hijab wrap (NOT a loose veil, NOT a hood, NOT fabric merely draped "
        "on top of head). comfortable beige leather flat sandals, small white cotton drawstring backpack. "
        "Simple and clean appearance inspired by ihram purity, no jewelry. EXACTLY the same outfit on "
        "every page — same pure white dress, same properly wrapped white hijab, same beige sandals."
    ),
    outfit_boy=(
        "pure white cotton knee-length kurta tunic with no patterns or decorations, small round white "
        "knitted taqiyah skull-cap sitting snugly on top of the head (NOT a turban, NOT a wrapped cloth, "
        "NOT a keffiyeh, NOT a hood — ONLY a small round knitted cap), light beige loose-fitting cotton "
        "pants, comfortable tan leather sandals, small white cotton drawstring backpack. Simple and clean "
        "appearance inspired by ihram purity. EXACTLY the same outfit on every page — same white kurta, "
        "same small round white taqiyah cap, same beige pants, same sandals."
    ),

    # ── G2: Tutarlılık — companion/obje yok ──
    companions=[],
    objects=[],

    # ── H: Kültürel Elementler ──
    cultural_elements={
        "values": ["Humility", "Patience", "Gratitude", "Unity", "Perseverance"],
        "primary": [
            "Masjid al-Haram and the Kaaba (black Kiswah with golden calligraphy)",
            "White marble courtyard reflecting sacred golden light",
            "Tawaf: 7 circuits around the Kaaba in white ihram",
            "Sa'y: 7 walks between Safa and Marwa marble corridor",
            "Zamzam well and blessed water",
        ],
        "location": "Mecca and Medina, Saudi Arabia",
        "secondary": [
            "Masjid al-Nabawi and Green Dome (Medina)",
            "Uhud Hill — site of historic battle",
            "Khandaq (Trench) site near Medina",
            "Mecca's domed mosques and minarets",
            "Hair cutting ceremony — renewal and ihram exit",
        ],
        "atmosphere": "Peaceful, reverent, spiritual, humble, transformative",
        "color_palette": "white (purity), gold (sacred), green (Medina), black (Kaaba)",
    },

    # ── C/G3: Lokasyon Kısıtları ──
    location_constraints=(
        "Setting follows the Umrah pilgrimage route. "
        "Kademe haritası ve Kamera kullanımları: "
        "Pages 1-2: Airport/preparation hall, white ihram garments. (Medium Shot, humble) "
        "Pages 3: Jeddah arrival, walking toward Mecca. (Wide Shot, anticipation) "
        "Pages 4-5: Masjid al-Haram entrance, first view of the Kaaba. (Hero Shot, awe-inspiring) "
        "Pages 6-8: Tawaf — circling the Kaaba, white marble courtyard. (Wide + Close-up) "
        "Pages 9-10: Sa'y — Safa to Marwa marble corridor. (Medium Shot, walking) "
        "Pages 11: Barber area, hair trimming. (Close-up, symbolic) "
        "Pages 12-13: Domed mosque visit in Mecca. (Wide Shot, reverent) "
        "Pages 14: Road to Medina, green dome in distance. (Wide landscape) "
        "Pages 15-17: Masjid al-Nabawi, Uhud hill, Khandaq trench site. (Wide + Medium) "
        "Pages 18+: Return journey, emotional farewell. (Hero Shot, warm glow)"
    ),

    # ── I: Scenario Bible ──
    scenario_bible={},

    # ── J: Custom Inputs ──
    custom_inputs_schema=[],
))

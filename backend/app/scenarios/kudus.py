"""Kudüs Macerası — Eski Şehir keşif macerası.

TİP A: Tek Landmark (Kudüs Eski Şehir).
Companion: Sevimli Zeytin Dalı Serçesi (SABİT — kullanıcıya seçtirilmez)
Obje: Antik Harita
"""

from app.scenarios._base import CompanionAnchor, ObjectAnchor, ScenarioContent
from app.scenarios._registry import register

KUDUS = register(ScenarioContent(
    theme_key="kudus",
    name="Kudüs Macerası",
    location_en="Old City of Jerusalem",
    default_page_count=22,
    flags={"no_family": False},

    # ── E: Hikaye Promptu (iyileştirilmiş — ~900 kelime) ──
    story_prompt_tr="""\
# KUDÜS MACERASI — ESKİ ŞEHRİN SIRLARI

## YAPI: {child_name} yanında {animal_friend} ile Kudüs Eski Şehri'nde gizli bir harita bulur. Haritadaki dört sembol dört bilmeceye karşılık gelir. Her bilmeceyi çözdükçe şehrin HERKES İÇİN ortak olan güzelliklerini keşfeder. Kültürel zenginlik, barış ve birlikte yaşam vurgusu.

**BAŞLIK:** "[Çocuk adı]'ın Kudüs Macerası". Alt başlık EKLEME.

**KARAKTER:** {child_name} ({child_age} yaşında, {child_gender}). Yardımcı: {animal_friend} — her sayfada AYNI görünüm, DEĞİŞTİRME.

**KARAKTER ARC — İÇ YOLCULUK:**
{child_name} başta yabancı bir şehirde biraz çekingen — sokaklar dar, sesler yabancı, her şey çok eski.
{animal_friend} yanına konunca rahatlar ama bilmeceleri henüz kendisi çözemiyor.
Macera boyunca adım adım cesaret ve özgüven kazanır: önce {animal_friend}'ın yardımıyla (ilk bilmece), sonra KENDİ AKLYLA (mozaik sırrını çözme).
Sonunda {child_name} gözlerinde artık çekingenlik değil, anlayış var — ama bu DEĞİŞİM ASLA SÖYLENMEZ, sadece EYLEMLERİYLE hissettirilir.

**DİNİ HASSASİYET:** Tarafsız, saygılı, kültürel zenginlik vurgusu. Dini polemik YOK. Politik referans YOK. Sadece mimari, doğa ve insan hikayeleri.

**YASAK:** Korku/şiddet YASAK. Didaktik nasihat YASAK.

---

### Bölüm 1 — Eski Şehir'de İlk Adımlar (Sayfa 1-4) 🎯 Duygu: MERAK + hafif TEDİRGİNLİK
- {child_name} Kudüs Eski Şehri'nin taş sokaklarına giriyor. 🔊 Uzaktan çan sesi, ezan, sokak satıcılarının sesleri iç içe. Hava kuru taş, baharat ve taze ekmek kokuyor. Biraz çekiniyor — sokaklar dar ve kalabalık.
- {animal_friend} daldan dala atlayarak gelip {child_name}'in omzuna konuyor! "Sen de mi burayı merak ediyorsun?" diye gülümser. {animal_friend} gagasındaki küçük zeytin dalını sallıyor.
- Bir taş duvardaki çatlakta katlanmış eski bir harita buluyorlar! {child_name} dikkatlice açıyor — sararmış kağıt, ✋ dokusu pürüzlü ve kırılgan. Üzerinde dört sembol: güneş, su damlası, yaprak, yıldız. "Bu bir bilmece haritası!" diye fısıldar.
- {animal_friend} haritanın bir köşesini gagasıyla gösteriyor — ilk sembol güneşe doğru işaret ediyor. "Birinci ipucu orada mı? Hadi gidelim!"
🪝 HOOK: Dört bilmece, dört sır — ama çözecek zamanları var mı?

---

### Bölüm 2 — Taş Sokaklar ve Bilmeceler (Sayfa 5-9) 🎯 Duygu: HEYECAN → KEŞİF
- Dar taş sokaklarda ilerliyor. 🔊 Ayakları altında eski taşların tıkırtısı. Baharatçı çarşısında renkli tezgahlar — zerdeçal, kırmızıbiber, kimyon yığınları. Bir satıcı {child_name}'e küçük bir kuru incir uzatıyor — tadı tatlı ve güneşli.
- İlk bilmece: bir taş çeşmenin yanında oyma — "Suyu takip et, kaynak seni bekler." {animal_friend} çeşmenin oluğundaki su izini fark ediyor! Birlikte izliyorlar → gizli bir avlu!
- İkinci bilmece: eski bir kapının üzerindeki taş oymalar — güneş sembolü ve bir ok. {child_name} düşünüyor... "Güneşin doğduğu yöne bak!" Doğuya dönünce duvarın arkasında gizli bir geçit görüyor.
- Geçidin sonunda antik taş merdiven. {child_name} artık tereddüt etmiyor — iniyor. {animal_friend} yanında uçarak eşlik ediyor.
🪝 HOOK: Merdivenin sonunda ne var? Üçüncü bilmece onları nereye götürecek?

---

### Bölüm 3 — Zeytin Ağacı ve Sabır (Sayfa 10-14) 🎯 Duygu: HUZUR → ANLAYIŞ
- Eski bir zeytin ağacının altına geliyorlar. 🔊 Yaprakların hışırtısı, uzaktan güvercin sesleri. Ağacın gövdesi kocaman — belki binlerce yaşında! ✋ {child_name} parmaklarını kabuğuna dokunduruyor — sert, sıcak, yılların izleriyle dolu.
- Üçüncü bilmece ağacın kökünde gizli — küçük bir taş plaka: "Sabırla büyüyen, herkese gölge veren..." {child_name} ağaca bakıyor: "Bu ağaç! Binlerce yıldır burada duruyor ve herkes altında dinleniyor." {animal_friend} dalında neşeyle zıplıyor!
- Taş surların üstüne çıkıyorlar — şehrin panoraması! Kubbeler, minareler, çan kuleleri hep birlikte, altın güneş ışığında. {child_name} bir an duraksıyor: "Hepsi bir arada... ne güzel."
- Haritadaki son sembol — yıldız — surların içindeki bir odayı gösteriyor! "Son bilmece orada!"
🪝 HOOK: Gizli odada onları ne bekliyor?

---

### Bölüm 4 — Sırrın Açılması (Sayfa 15-18) 🎯 Duygu: KEŞF → ZAFER
- Gizli odaya giriyorlar — duvarda muhteşem eski bir mozaik! 🔊 İçeride derin bir sessizlik, sadece kendi nefes sesleri. Farklı kültürlerin sembolleri bir arada: güneş, ay, yıldız, zeytin dalı, su damlası.
- Son bilmece mozaiğin ortasında: boş bir yer var, tam haritanın boyutunda! {child_name} anlıyor — "Harita buraya ait!"
- {child_name} TEREDDÜT ETMİYOR. Haritayı mozaiğin ortasına YERLEŞTİRİYOR. 🔊 Mozaik bir an parıldıyor — tüm semboller birbirine bağlanıyor!
- "Tüm yollar birbirine bağlanıyor!" diye fısıldıyor, gözlerinde hayranlık. {animal_friend} neşeyle kanat çırpıp {child_name}'in etrafında dönüyor.
🪝 HOOK: Mozaiğin mesajı ne?

---

### Bölüm 5 — Kapanış (Sayfa 19-22) 🎯 Duygu: HUZUR + GURUR
- Gün batımında surlardan şehre bakış — altın ışıkta kubbeler ve ağaçlar. 🔊 Uzaktan akşam sesleri, kuşların yuvaya dönüşü. Hava serin ve temiz.
- Haritayı güvenli bir yere saklıyor — duvardaki çatlağa geri koyuyor. "Bu herkesin haritası. Burada kalsın."
- {child_name} {animal_friend}'a bakıp gülümsüyor: "Biz iyi bir ekibiz." {animal_friend} gagasındaki zeytin dalını {child_name}'in avucuna bırakıyor — küçük bir hediye.
- Son adımını atarken ufka bakıyor. Gözlerinde artık çekingenlik yok — parlak, meraklı bir ışık var. "Bir dahaki macera nereye olacak acaba?"

---

## 🚫 KURALLAR
- {animal_friend} her sayfada AYNI görünüm — DEĞİŞTİRME.
- DİNİ POLEMİK YOK. Tarafsız, saygılı, kültürel zenginlik vurgusu.
- Korku/şiddet/gore YASAK.

## ⚠️ YAZIM KURALLARI

❌ YANLIŞ (Gezi Rehberi): "{child_name} Kudüs'e geldi. Kudüs 3.000 yıllık bir şehirdir ve üç dinin kutsal mekânıdır."
✅ DOĞRU (Macera): "{child_name}'in ayağı bir taşa takıldı — çatlaktan katlanmış eski bir kağıt görünüyordu!"

❌ YANLIŞ (Doğrudan Öğüt): "{child_name} farklı kültürlerin barış içinde yaşaması gerektiğini öğrendi."
✅ DOĞRU (Subliminal): "{child_name} surlardan baktı. Kubbeler, çan kuleleri, minareler — hepsi aynı altın ışıkta parlıyordu."

## 💬 DİYALOG KURALI
Her 3-4 sayfada en az 1-2 kısa diyalog. {child_name} {animal_friend}'a konuşur, kuş jest/ses ile tepki verir.

Hikayeyi TAM OLARAK {page_count} sayfa yaz. Her sayfa 2-4 cümle, akıcı ve macera dolu.
""",

    # ── F: Görsel Prompt Şablonları (genişletilmiş) ──
    cover_prompt_template=(
        'An {child_age}-year-old {child_gender} named {child_name} with {hair_description}, '
        'wearing {clothing_description}. {scene_description}. Ancient Jerusalem Old City stone walls '
        'and golden dome in background. Warm golden sunset light, ancient olive trees. '
        'Low-angle hero shot: child 25% foreground, ancient city walls 75%. Rich warm palette: '
        'honey gold, cream limestone, olive green, terracotta. {STYLE}'
    ),
    page_prompt_template=(
        'An {child_age}-year-old {child_gender} named {child_name} with {hair_description}, '
        'wearing {clothing_description}. {scene_description}. '
        'EXTERIOR elements: [Jerusalem Old City narrow stone alleys, ancient limestone walls, '
        'olive trees, golden domes, spice market stalls, stone fountains]. '
        'INTERIOR elements: [Hidden rooms with ancient mosaics, carved stone doors, '
        'candlelit corridors, faded wall symbols]. '
        'ATMOSPHERIC: [warm golden sunlight on limestone, dust motes, olive leaves, spice aromas]. '
        'Shot variety: Wide establishing / Medium action / Close-up detail / Low angle hero. '
        'Color palette: honey gold, cream limestone, olive green, terracotta, warm brown. '
        'Cinematic warm lighting, detailed ancient stone texture. '
        'Dynamic pose, expressive emotion. No eye contact with camera. {STYLE}'
    ),

    # ── G: Kıyafetler ──
    outfit_girl=(
        "cream cotton modest dress with delicate olive embroidery, light sage-green linen cardigan, "
        "comfortable brown leather sandals, a small woven shoulder bag, and an olive silk headscarf. "
        "EXACTLY the same outfit on every page."
    ),
    outfit_boy=(
        "light khaki linen shirt with mandarin collar, cream cotton trousers, "
        "brown leather sandals, small canvas messenger bag, and a beige linen flat cap. "
        "EXACTLY the same outfit on every page."
    ),

    # ── G2: Tutarlılık Kartları — SABİT companion ──
    companions=[
        CompanionAnchor(
            name_tr="Sevimli Zeytin Dalı Serçesi",
            name_en="tiny olive-brown sparrow with a small olive branch in its beak",
            species="sparrow",
            appearance="tiny olive-brown sparrow with a small olive branch in its beak and bright curious dark eyes",
            short_name="Serçe",
        ),
    ],
    objects=[
        ObjectAnchor(
            name_tr="Antik Harita",
            appearance_en="ancient yellowed folded parchment map with four symbols (sun, water drop, leaf, star), fragile texture",
            prompt_suffix="holding ancient yellowed parchment map with four symbols — SAME on every page",
        ),
    ],

    # ── H: Kültürel Elementler ──
    cultural_elements={
        "primary": [
            "Jerusalem Old City ancient limestone walls",
            "Narrow stone alleys with merchant stalls",
            "Ancient olive trees (thousands of years old)",
            "Spice market (souk) with colorful displays",
            "City wall panorama — domes, minarets, bell towers together",
        ],
        "secondary": [
            "Ancient stone fountains with water channels",
            "Hidden rooms with mosaic art",
            "Carved stone doors with symbols",
            "Golden sunset light on limestone architecture",
        ],
        "values": ["Curiosity", "Respect", "Cultural appreciation", "Peace", "Unity in diversity"],
        "atmosphere": "Ancient, peaceful, culturally rich, warm, harmonious",
        "sensitivity_rules": [
            "Tarafsız dini anlatım — NO religious polemic",
            "NO political references",
            "Cultural heritage and architecture focus ONLY",
            "ALL cultures shown equally and respectfully",
        ],
    },

    # ── C/G3: Lokasyon Kısıtları ──
    location_constraints=(
        "Pages 1-4: Old City entrance, narrow stone streets. (Wide Shot, warm golden light) "
        "Pages 5-9: Stone alleys, spice market, fountain, hidden courtyard. (Medium Shot, colorful) "
        "Pages 10-14: Ancient olive garden, city wall panorama. (Wide + Close-up, golden hour) "
        "Pages 15-18: Hidden room with mosaic, secret passage. (Close-up, golden glow) "
        "Pages 19-22: Sunset view from city walls, departure. (Hero Shot, golden hour)"
    ),

    # ── I: Scenario Bible (genişletilmiş) ──
    scenario_bible={
        "companion_pack": {
            "zeytin_sercesi": {
                "species": "sparrow",
                "appearance_en": "tiny olive-brown sparrow with a small olive branch in its beak and bright curious dark eyes",
                "role": "Çocuğun meraklı keşif arkadaşı, bilmece ipuçlarını bulan, daldan dala atlayan",
            },
        },
        "key_objects": {
            "antik_harita": {
                "appearance_en": "ancient yellowed folded parchment map with four symbols (sun, water drop, leaf, star)",
                "first_page": 3,
                "last_page": 18,
                "prompt_suffix": "holding ancient yellowed parchment map — SAME on every page",
            },
        },
        "side_characters": {
            "baharatci": {
                "outfit_en": "friendly middle-aged spice merchant in white cotton shirt and brown leather apron",
                "appears_on": [5, 6],
                "rule": "SAME outfit on every appearance",
            },
        },
        "location_zone_map": {
            "old_city_streets": "pages 1-9",
            "olive_garden_walls": "pages 10-14",
            "hidden_room": "pages 15-18",
            "sunset_departure": "pages 19-22",
        },
        "sensitivity_rules": [
            "Tarafsız dini anlatım — NO religious polemic",
            "NO political references",
            "Cultural heritage and architecture focus ONLY",
        ],
        "consistency_rules": [
            "Sparrow companion MUST have EXACTLY the same olive-brown color and olive branch on EVERY page",
            "Ancient map MUST have the same four symbols on pages 3-18",
            "Child's outfit MUST NOT change throughout the story",
            "City architecture shown respectfully — all traditions represented equally",
        ],
    
        "companions": "see_scenario_companions_list",
        "locations": "see_location_constraints",
    },

    # ── J: Custom Inputs — SABİT companion ──
    custom_inputs_schema=[
        {
            "key": "animal_friend",
            "type": "hidden",
            "default": "Sevimli Zeytin Dalı Serçesi",
        },
    ],
))

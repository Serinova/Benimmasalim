"""Mercan Şehrin Sinyali — Derin okyanus keşfi ve sualtı dünyasının korunması.

TİP B: Geniş Ortam (Okyanus). Companion: Dostça Yunus (SABİT — kullanıcıya seçtirilmez).
Objeler: Mercan Pusulası, Kristal Okyanus Küresi
"""

from app.scenarios._base import CompanionAnchor, ObjectAnchor, ScenarioContent
from app.scenarios._registry import register

OCEAN = register(ScenarioContent(
    # ── A: Temel Kimlik ──
    theme_key="ocean",
    name="Mercan Şehrin Sinyali",
    location_en="Deep Ocean",
    default_page_count=22,
    flags={"no_family": True},

    # ── E: Hikaye Promptu (iyileştirilmiş — ~750 kelime) ──
    story_prompt_tr="""\
# MERCAN ŞEHRİN SİNYALİ — DERİN OKYANUS KEŞFİ

## YAPI: {child_name} TEK BAŞINA, AİLE YOK. Yanında sadece Dalga (sevimli gri yunus).

**KRİTİK — METİN UZUNLUĞU:** Her sayfa 1-3 cümle, toplam 25-50 kelime. Kısa tut, sayfaya sığsın.

**KARAKTER:** {child_name} ({child_age} yaşında, {child_gender}). Yardımcı: Dalga — sevimli gri yunus, parlak zeki gözleri ve kalıcı gülümsemesiyle. Her sayfada AYNI görünüm — DEĞİŞTİRME.

**KARAKTER ARC — İÇ YOLCULUK:**
{child_name} başta karanlık sudan ve bilinmezden korkan, yüzeyin altına inmeye çekingen bir çocuk. Su yüzeyinde güvende hissediyor, derinlik onu tedirgin ediyor.
Macera boyunca adım adım cesaret kazanır: önce Dalga'nın yol göstericiliğiyle, sonra derin denizdeki en karanlık anda TEK BAŞINA karar vererek.
Hikayenin sonunda {child_name} artık derinlikten korkmayan, bilinmeze merakla bakan, okyanusa saygıyla yaklaşan bir çocuk — ama bu DEĞİŞİM ASLA SÖYLENMEMELİ, sadece EYLEMLERİYLE hissettirilmeli.

**YASAK:** Anne, baba, aile üyesi, kaptan, dalgıç, yetişkin YOK. Sahnelerde sadece çocuk + yunus. Büyü yok — biyolüminesans doğal ışık. Köpekbalığı saldırısı, korkunç yaratık YOK.

**AKIŞ (6 BÖLÜM):**

### BÖLÜM 1 — Dalış Başlıyor (Sayfa 1-3) 🎯 Duygu: MERAK + hafif TEDİRGİNLİK
- {child_name} küçük denizaltı aracının camından okyanus yüzeyine bakıyor. Su masmavi, güneş ışınları dalgaların arasından süzülüyor.
- Dalga cam dışından yüzdüğünü gösteriyor — burnunu cama değdiriyor, {child_name} gülerek karşılık veriyor. "Seninle geleceğim" diyor fısıldayarak.
- Su yüzeyinin altına dalış — ışık değişiyor, her şey mavi-yeşil tonlara dönüyor. {child_name} yutkunuyor ama gözlerini ayıramıyor.
- 🔊 Denizaltının hafif motor sesi, baloncukların şıpırtısı. Cam soğuk ve nemli.

### BÖLÜM 2 — Mercan Resifi (Sayfa 4-7) 🎯 Duygu: HEYECAN → ŞAŞKınlık
- İlk mercan resifi görünüyor — mor, turuncu, pembe mercanlar. Palyaço balıkları anemoneler arasında saklanıyor.
- {child_name} burnunu cama yapıştırıyor: "Bak Dalga! Renkli çiçeklere benziyorlar!" Dalga sevinçle takla atıyor.
- Deniz yıldızları kayaların üzerinde yavaşça hareket ediyor. Dev bir deniz kaplumbağası uzaktan süzülüp geçiyor.
- Bir mercan kümesinin arasında tuhaf bir parıltı — {child_name} yaklaşınca eski bir pusula bulunuyor. Bronz gövdesi mercanlarla kaplı, turkuaz iğnesi hâlâ ışıl ışıl.
- "Bu pusula bir yere işaret ediyor..." diyor {child_name}, aleti çevirirken. İğne kararlıca derinlikleri gösteriyor.
- 🪝 HOOK: "Ama pusulanın iğnesi, ışığın ulaşamadığı karanlık derinliklere doğru dönüyordu..."

### BÖLÜM 3 — Batık Gemi (Sayfa 8-11) 🎯 Duygu: GİZEM → KEŞİF COŞKUSU
- Pusulayı takip ederek eski bir batık gemiye ulaşıyorlar. Direkler yosunla kaplı, güverte kumu kabarık.
- Geminin içi — mürekkepli şişeler, eski haritalar, kapalı sandıklar. Işık lombozlardan süzülüyor, yeşil-mavi gölgeler dans ediyor.
- {child_name} bir sandığı açıyor — içinde kristal bir küre! Beyzbol topu büyüklüğünde, içi mavi ışıkla dolu, okyanus akıntılarının haritası parlıyor.
- "Bu... okyanusun haritası gibi!" fısıldıyor {child_name}. Dalga küreye burnuyla dokunuyor, ışıklar daha parlak yanıyor.
- Kürenin içindeki bir ışık noktası sürekli yanıp sönüyor — çok derinlerdeki bir şeyi çağırıyor.
- 🪝 HOOK: "Kristal küredeki sinyal gittikçe hızlanıyordu — sanki bir şey onları bekliyormuş gibi..."

### BÖLÜM 4 — Karanlık Derinlik (Sayfa 12-15) 🎯 Duygu: KORKU → CESARET
- Daha derine dalış — güneş ışığı kayboluyor, etraf karanlığa gömülüyor. {child_name} koltuğunda geriye yaslanıyor, kalbi hızlanıyor.
- 🔊 Derin denizin sessizliği — sadece denizaltının motor uğultusu ve kendi nefes sesi.
- Biyolüminesans yaratıklar beliriyor — parıldayan jellyfish'ler, ışıklı anglerfish'ler. {child_name} önce irkiliyor, sonra "Kendi ışıklarını kendileri yapıyorlar..." diye fısıldıyor.
- Dalga endişeyle etrafta dönüyor — bu derinliklere o da alışık değil.
- Bir anda denizaltının ışıkları kısılıyor! Sadece kristal kürenin mavi ışığı kalıyor. {child_name} paniğe kapılmak üzereyken duraksıyor.
- {child_name} derin bir nefes alıyor. Küreyi kaldırıyor ve karanlıkta yol buluyor — bu sefer Dalga'nın yardımı OLMADAN, KENDİ karariyla.
- 🪝 HOOK: "Kürenin ışığı devasa bir kaya duvarını aydınlattığında, {child_name} nefesini tuttu..."

### BÖLÜM 5 — Mercan Şehri (Sayfa 16-19) 🎯 Duygu: ŞAŞKınlık → HAYRANLIK → SEVİNÇ
- Kaya duvarında bir geçit — geçince devasa bir sualtı mağarası! Tavanı biyolüminesans planktonlarla kaplanmış, yıldızlı gökyüzü gibi parlıyor.
- İçeride antik yapılar — mercan sütunlar, kabukla kaplı kemerler, taş duvarlarında okyanus motifleri (balıklar, dalgalar, güneş).
- Kristal küre bir taş yuvaya tam oturuyor — tıklama sesi! Mağara canlanıyor — tüm duvarlar ışıkla dolup taşıyor.
- "Bu okyanusun kalbi..." fısıldıyor {child_name}, gözleri kocaman açılmış. Dev su bitkileri salınıyor, biyolüminesans balıklar dans ediyor.
- Dalga sevinçle suyun içinde takla üstüne takla atıyor. {child_name} gülerek alkışlıyor.
- Bahçenin merkezinde ışık yayan eski bir mozaik — okyanus akıntılarının başlangıç noktası. Sular berraklaşıyor, deniz hayvanları toplanıyor.
- {child_name} avucunu mozaiğin üzerine koyuyor — sıcak ve titreşiyor. "Anlıyorum," diyor yumuşakça. "Burası canlı."

### BÖLÜM 6 — Yüzeye Dönüş ve Gurur (Sayfa 20-22) 🎯 Duygu: HUZUR + GURUR
- Kristal küreyi yuvadan dikkatle alıyor — hatıra olarak. Pusulayı da cebine koyuyor.
- Yüzeye çıkış — ışık adım adım artıyor, karanlık mavi→turkuaz→açık mavi. {child_name} gülümsüyor: "Dönüyoruz Dalga."
- 🔊 Su yüzeyine çıkınca dalga sesi, martı çığlıkları, tuzlu rüzgar yüzünü yalıyor.
- Gün batımında okyanus altın ve turuncu ışıkla parıldıyor. Dalga son kez burnuyla {child_name}'in eline dokunuyor.
- {child_name} kristal küreyi ışığa tutuyor — içindeki okyanus haritası hâlâ parlıyor.
- {child_name} ufka bakıyor, gözlerinde artık korku değil sakin bir güven var. Küre avucunda sıcacık atıyor.
- Son cümle atmosfer: "Dalga bir takla daha attı ve derinliklere süzüldü — belki yarın yeni bir sinyal gelirdi..."

---

## 🚫 KURALLAR
- AİLE/YETİŞKİN YOK. Sahnelerde sadece {child_name} + Dalga (yunus).
- Büyü/sihir YOK. Biyolüminesans doğal ışıktır, sihirli değil.
- Dalga her sayfada AYNI görünüm — gri vücut, parlak gözler, gülümseme — DEĞİŞMEZ.
- Mercan Pusulası bulunduktan sonraki her sayfada görünmeli — AYNI bronz tasarım.
- Kristal Küre bulunduktan sonra her sayfada görünmeli — AYNI mavi ışıklı küre.
- Korkunç/tehlikeli deniz yaratıkları YOK (köpekbalığı saldırısı vb.).
- İlk sayfa [Sayfa 1] ile başla. Uçak/yolculuk sahnesi YOK.

## ⚠️ YAZIM KURALLARI

❌ YANLIŞ (Gezi Rehberi): "{child_name} mercan resifini gördü. Mercan resifleri tropikal denizlerde bulunur. Sonra batık gemiye gitti."
✅ DOĞRU (Macera): "Mercan kümesinin arasında bir şey parıldadı — {child_name} uzanıp kavradığında avucundaki bronz pusula ışıl ışıldı!"

❌ YANLIŞ (Doğrudan Öğüt): "{child_name} okyanusun ne kadar değerli olduğunu anladı. Onu korumak gerektiğini öğrenmişti."
✅ DOĞRU (Subliminal): "{child_name} avucunu mozaiğin üzerine koydu — sıcak ve canlıydı. 'Burası nefes alıyor' diye fısıldadı."

❌ YANLIŞ (Pasif Kahraman): "{child_name} Dalga'nın arkasından gitti. Dalga her şeyi gösterdi."
✅ DOĞRU (Aktif Kahraman): "{child_name} küreyi kaldırdı ve karanlıkta yol buldu — bu sefer kendi kararıyla."

## 💬 DİYALOG KURALI
Her 3-4 sayfada en az 1 kısa diyalog olmalı. {child_name} Dalga'ya konuşur, Dalga burnuyla dokunarak, takla atarak, sevinçle yüzerek tepki verir. Companion konuşamaz.

## ⛔ İÇERİK YASAKLARI
- Anne, baba, aile üyesi, kaptan YASAK (no_family)
- Dini/siyasi referans YASAK
- Gezi rehberi formatı YASAK
- Korkunç yaratık, köpekbalığı saldırısı YASAK

Hikayeyi TAM OLARAK {page_count} sayfa yaz. Her sayfa 1-3 cümle (25-50 kelime).
""",

    # ── F: Görsel Prompt Şablonları (iyileştirilmiş) ──
    cover_prompt_template=(
        'Story "{book_title}". A young child inside a small glass submarine cockpit, '
        'face pressed against the window in wonder, wearing {clothing_description}. '
        '{scene_description}. '
        'A friendly grey dolphin swimming alongside the submarine window. '
        'Vibrant coral reef in foreground, tropical fish swirling around, '
        'golden light beams streaming from the ocean surface above. '
        'Rich underwater blues, teals, and coral pinks. '
        'Cinematic wide shot, child in foreground 30%, underwater world 70%. '
        'Space for title at top. {STYLE}'
    ),
    page_prompt_template=(
        'A young child {scene_description}, wearing {clothing_description}. '
        'Setting elements (choose relevant based on scene): '
        'SHALLOW: [colorful coral reef, tropical fish, sea stars, anemones, '
        'golden sunbeams filtering through turquoise water, sandy ocean floor]. '
        'SHIPWRECK: [old sunken ship with moss-covered hull, barnacle-encrusted porthole windows, '
        'green-blue filtered light through old timber, scattered treasure chests]. '
        'DEEP SEA: [pitch-dark ocean depths, bioluminescent jellyfish glowing blue-purple, '
        'anglerfish with glowing lure, deep sea creatures with natural light]. '
        'UNDERWATER CITY: [massive underwater cavern with bioluminescent ceiling like stars, '
        'ancient coral pillars, shell-encrusted archways, ocean mosaic floor glowing warm]. '
        'SURFACE: [ocean surface at sunset, golden-orange light on waves, seabirds silhouettes, '
        'calm turquoise water transitioning to deep blue]. '
        'Shot variety: [close-up detail / medium action / wide epic / interior submarine / underwater panoramic]. '
        'Composition: full body visible in action, cool ocean palette (deep blue, teal, coral pink, '
        'bioluminescent purple, golden surface light). Text overlay space at bottom. {STYLE}'
    ),

    # ── G: Kıyafetler ──
    outfit_girl=(
        "sky-blue wetsuit with white wave pattern down the sides, "
        "a small waterproof utility belt with bronze buckle, "
        "clear diving goggles pushed up on forehead, "
        "aquamarine water shoes with coral-pink soles. "
        "EXACTLY the same outfit on every page."
    ),
    outfit_boy=(
        "navy-blue wetsuit with orange stripe accents on arms and legs, "
        "a small waterproof utility belt with bronze buckle, "
        "clear diving goggles pushed up on forehead, "
        "dark blue water shoes with neon-green soles. "
        "EXACTLY the same outfit on every page."
    ),

    # ── G2: Tutarlılık Kartları ──
    companions=[
        CompanionAnchor(
            name_tr="Dostça Yunus",
            name_en="friendly grey bottlenose dolphin",
            species="dolphin",
            appearance=(
                "friendly medium-sized grey bottlenose dolphin with bright intelligent eyes, "
                "a permanent gentle smile, smooth silver-grey skin, and a small notch on dorsal fin"
            ),
            short_name="Dalga",
        ),
    ],
    objects=[
        ObjectAnchor(
            name_tr="Mercan Pusulası",
            appearance_en=(
                "ancient compass with coral-encrusted bronze casing, "
                "glowing turquoise needle that always points downward, palm-sized"
            ),
            prompt_suffix=(
                "holding ancient coral compass with glowing turquoise needle "
                "— SAME appearance on every page"
            ),
        ),
        ObjectAnchor(
            name_tr="Kristal Okyanus Küresi",
            appearance_en=(
                "crystal sphere the size of a baseball, filled with glowing blue light, "
                "showing ocean currents and seafloor map with pulsing signal dot"
            ),
            prompt_suffix=(
                "carrying crystal sphere with glowing blue ocean map inside "
                "— SAME appearance on every page"
            ),
        ),
    ],

    # ── H: Kültürel Elementler ──
    cultural_elements={
        "primary": [
            "coral reef ecosystem with tropical fish and anemones",
            "sunken ship interior with barnacles and old maps",
            "deep sea bioluminescence (jellyfish, anglerfish)",
            "submarine exploration cockpit with glass windows",
            "ancient underwater city ruins with coral pillars",
        ],
        "secondary": [
            "crystal sphere ocean map with glowing currents",
            "ancient coral-encrusted compass with turquoise needle",
            "giant kelp forest swaying in undersea currents",
            "ocean floor thermal vents with mineral chimneys",
            "sea star meadow on sandy ocean floor",
            "bioluminescent plankton ceiling like underwater stars",
            "ancient mosaic depicting ocean current origins",
        ],
        "colors": "deep ocean blues, vibrant coral pinks, teal, bioluminescent purple, golden surface light",
        "atmosphere": "mysterious, serene, awe-inspiring, gradually darker then magical",
    },

    # ── C/G3: Lokasyon Kısıtları ──
    location_constraints=(
        "Pages 1-3: Submarine at ocean surface, initial dive — bright turquoise water, "
        "golden sunbeams from above (Wide Shot, warm-cool transition). "
        "Pages 4-7: Shallow coral reef — vibrant corals, tropical fish, sea stars, "
        "compass discovery (Medium Shot + Close-up detail on compass). "
        "Pages 8-11: Sunken ship interior — green-blue filtered light, old timber, "
        "barnacles, crystal sphere discovery (Interior moody, Medium Shot). "
        "Pages 12-15: Deep ocean descent — pitch dark, bioluminescent creatures, "
        "submarine lights dim, child alone with crystal light (Close-up dramatic, low-key lighting). "
        "Pages 16-19: Hidden underwater city/garden — massive cavern with glowing ceiling, "
        "coral pillars, ocean mosaic floor, magical bright light (Wide epic panoramic). "
        "Pages 20-22: Ascent to surface, sunset — light gradually returning, "
        "golden-orange surface light, farewell (Hero Shot, cinematic golden hour)."
    ),

    # ── I: Scenario Bible ──
    scenario_bible={
        "companion": {
            "name": "Dalga (Dostça Yunus)",
            "personality": (
                "Neşeli, meraklı, koruyucu bir yunus. Heyecanlandığında takla atar, "
                "endişelendiğinde çocuğun etrafında döner. Doruk noktasında (karanlık derinlik) "
                "yardım EDEMEZ — çocuk kendi cesaretiyle yol bulmalı."
            ),
            "role": "Yol gösterici ve duygusal destek, ama kriz anında pasif",
            "visual_lock": "Grey bottlenose dolphin, bright eyes, gentle smile, notch on dorsal fin — EVERY PAGE SAME",
        },
        "key_objects": {
            "pusula": {
                "name": "Mercan Pusulası",
                "description": "Eski bir denizciye ait, mercanlarla kaplı bronz pusula. Turkuaz iğnesi derinlikleri gösterir.",
                "first_appear": "Sayfa 6-7",
                "visual_lock": "Coral-encrusted bronze compass, turquoise needle — SAME on every page",
            },
            "kure": {
                "name": "Kristal Okyanus Küresi",
                "description": "Beyzbol büyüklüğünde kristal küre. İçinde mavi ışıkla parlayan okyanus akıntı haritası ve yanıp sönen sinyal noktası var.",
                "first_appear": "Sayfa 10",
                "visual_lock": "Crystal sphere with blue glowing ocean map — SAME on every page",
            },
        },
        "zones": {
            "surface": "Sıcak, aydınlık, güvenli — turkuaz su, altın güneş ışınları",
            "coral_reef": "Renkli, canlı, neşeli — mercanlar, tropikal balıklar, deniz yıldızları",
            "shipwreck": "Gizemli, loş, keşif dolu — yeşil-mavi ışık, yosunlu ahşap, eski haritalar",
            "deep_sea": "Karanlık, soğuk, gerilimli — biyolüminesans tek ışık kaynağı, sessizlik",
            "coral_city": "Büyülü, muhteşem, hayranlık — devasa mağara, yıldızlı tavan, mercan sütunlar",
            "ascent": "Huzurlu, sıcak — ışık yavaşça döner, altın gün batımı",
        },
        "emotional_arc": {
            "S1-S3": "Merak + hafif tedirginlik (derinlik korkusu)",
            "S4-S7": "Heyecan + şaşkınlık (resif güzelliği, pusula keşfi)",
            "S8-S11": "Gizem + keşif coşkusu (batık gemi, kristal küre)",
            "S12-S15": "Korku → cesaret (karanlık, ışıklar söner, çocuk TEK BAŞINA karar verir)",
            "S16-S19": "Şaşkınlık + hayranlık + sevinç (mercan şehri canlanıyor)",
            "S20-S22": "Huzur + gurur (yüzeye çıkış, veda, sıcak kapanış)",
        },
        "consistency_rules": [
            "Dalga (yunus) HER sayfada aynı grey + smile + notched dorsal fin görünüm",
            "Mercan Pusulası bulunduktan sonra HER sayfada aynı bronz+turkuaz tasarım",
            "Kristal Küre bulunduktan sonra HER sayfada aynı mavi ışıklı küre",
            "Derinlik arttıkça ortam KARARIR, biyolüminesans ARTAR",
            "Yüzeye çıkışta ışık ADIM ADIM döner (karanlık→mavi→turkuaz→altın)",
            "Çocuğun dalış kıyafeti TÜM SAYFALARDA birebir aynı",
        ],
        "no_family": True,
        "no_magic": True,
        "child_solo": True,
    
        "companions": "see_scenario_companions_list",
        "locations": "see_location_constraints",
    },

    # ── J: Custom Inputs — SABİT companion (kullanıcıya seçtirilmez) ──
    custom_inputs_schema=[
        {
            "key": "animal_friend",
            "type": "hidden",
            "default": "Dostça Yunus",
        },
    ],
))

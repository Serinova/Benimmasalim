"""Kutsal Topraklara Ziyaret — Umre senaryosu.

TİP D: Manevi Yolculuk. Companion: YOK (kafile ile).
Objeler: YOK (manevi deneyim). Kıyafet: İhram (S3-10) → Normal (S12+).
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

    # ── E: Hikaye Promptu (İslami kurallara göre iyileştirilmiş — ~800 kelime) ──
    story_prompt_tr="""\
# KUTSAL TOPRAKLARA ZİYARET — UMRE

## YAPI: {child_name} KAFİLE İLE UMRE YAPIYOR. AİLE İLE BİRLİKTE. UÇAK SAHNESİ YOK.

**KRİTİK — METİN UZUNLUĞU:** Her sayfa 1-3 cümle, toplam 25-50 kelime. Kısa tut, sayfaya sığsın.

**İSLAMİ UMRE SÜRECİ — DOĞRU SIRALAMA:**
1. Mikat'ta İhrama Giriş: Gusül abdesti, ihram giyinme, 2 rekât ihram namazı, niyet, telbiye
2. Mekke'ye Varış: Lebbeyk sesleriyle yürüyüş, Mescid-i Haram'a giriş
3. Kabe İlk Görüş: Gözler yaşarır, ilk görüşte dua kabuldür
4. Tavaf: Hacerülesved hizasından başlayarak 7 şavt (tur), Kabe etrafında saat yönünün tersine
5. Tavaf Namazı: 2 rekât namaz, tercihen Makam-ı İbrahim arkasında
6. Zemzem İçme: Ayakta, Kabe'ye bakarak, "bismillah" ile
7. Sa'y: Safa-Merve arası 7 gidiş-geliş (Safa'dan başlar)
8. Saç Kesme (Taksir): Erkek en az 1/4 baştan kısaltır (KAZITMA/KEL YASAK), kız parmak ucu kadar keser
9. İhramdan çıkış — umre tamamlandı

**KIYAFET KURALLARI:**
- İHRAM (Erkek — S3-S10): Rida (üst örtü) ve İzar (alt örtü) — iki parça dikişsiz beyaz bez. BAŞ TAMAMEN AÇIK (takke, şapka, kapüşon YOK). Ayakta sandalet.
- İHRAM (Kız — S3-S10): Normal İslami kıyafet — uzun beyaz elbise + düzgünce bağlanmış beyaz hicap. Eller ve yüz açık. Topuklu ayakkabı yok, sandalet.
- İHRAM SONRASI (S12+): Erkek → beyaz kurta + beyaz yuvarlak takke küçük + bej pantolon. Kız → ayni → beyaz elbise + beyaz hicap.
- İHRAMDA YASAKLAR: Dikişli giysi (erkek), koku sürünme, tırnak kesme, saç kesme (henüz vakti değil), kavga etme.

**KARAKTER:** {child_name} ({child_age} yaşında, {child_gender}).

---

### BÖLÜM 1 — Hazırlık ve İhram (Sayfa 1-2) 🎯 Duygu: HEYECAN + SAYGI
- Sayfa 1: {child_name} kafile ile havalimanı toplantı alanında buluşuyor. Heyecanlı yüzler, bavullar. "Artık gerçek oluyor!" diyor {child_name}, kalbi gümbür gümbür. ✋ İhram bezlerinin kumaşı yumuşak ve hafif, sabun gibi temiz kokuyor.
- Sayfa 2: Mikat'ta ihrama hazırlık — gusül abdesti, ihram giyiniliyor. {child_name} iki parça beyaz beze sarılıyor (erkek) / beyaz elbise ve hicap giyiyor (kız). "Allahümme lebbeyke umraten" diye niyet ediyor. İlk kez Telbiye okunuyor: "Lebbeyk Allahümme Lebbeyk..." 🔊 Ses kafilenin geneline yayılıyor, herkes birlikte söylüyor.
- 🪝 HOOK: "Yüzlerce ses tek ses olmuştu — ve bu ses Mekke'ye doğru yükseliyordu..."

### BÖLÜM 2 — Mekke'ye Yürüyüş ve İlk Kabe Görüşü (Sayfa 3-5) 🎯 Duygu: BEKLENTİ → HUŞU → GÖZYAŞI
- Sayfa 3: İhramla Mekke'ye yürüyüş. Sokaklar beyaz ihramlı insanlarla dolu. "Lebbeyk" sesleri her yandan. {child_name} sessizleşiyor — büyük bir şey yaklaşıyor.
- Sayfa 4: Mescid-i Haram'ın devasa kapılarından giriş. ✋ Soğuk beyaz mermer ayak altında serin. Adım adım ilerleniyor. 🔊 Kalabalığın uğultusu, uzaktan dua sesleri.
- Sayfa 5: VE İŞTE — Kabe! Siyah Kisvesiyle, altın hat yazılarıyla, görkemli ve mütevazı aynı anda. {child_name}'in gözleri doluyor. Kalbi sıkışıyor. **İlk görüşte edilen dua kabul olunur** — {child_name} gözlerini kapayıp kalbinden ne geçerse sessizce dua ediyor.
- 🪝 HOOK: "Kabe'nin Hacerülesved köşesi parlıyordu — tavaf buradan başlayacaktı..."

### BÖLÜM 3 — Tavaf (Sayfa 6-8) 🎯 Duygu: BİRLİK + SPİRİTÜEL DERİNLİK
- Sayfa 6: Tavafa başlama — Hacerülesved hizasından işaret ederek "Bismillahi Allahu Ekber." İlk şavt. Binlerce beyaz ihramlı insan aynı yöne, saat yönünün TERSİNE yürüyor. {child_name} akıntıya kapılıyor ama huzurlu.
- Sayfa 7: 3., 4. şavt — ritim oturuyor. ✋ Mermer serin, ayaklar yorulmaya başlıyor ama kalp hafifliyor. {child_name} fısıldayarak dua ediyor. Yanındaki yaşlı bir teyze gülümsüyor, "Allah kabul etsin" diyor.
- Sayfa 8: 7. şavt tamamlandı! Tavaf namazı — Makam-ı İbrahim'in arkasında 2 rekât. Sonra Zemzem suyu — {child_name} Kabe'ye bakarak ayakta içiyor, "Bismillah." Suyun tadı… farklı, yumuşak, serinletici. 👃 Temiz, derin, tarifi zor.
- 🪝 HOOK: "Zemzem boğazından akarken buz gibi ve sıcacık aynı anda hissediyordu — Sa'y için Safa tepesine bakması gerekiyordu..."

### BÖLÜM 4 — Sa'y (Sayfa 9-10) 🎯 Duygu: AZİM + DAYANIKLILIK + TARİHÎ BAĞLANTI
- Sayfa 9: Safa tepesine çıkıyor, Kabe'ye bakarak dua ediyor. Sonra Merve'ye doğru ilk yürüyüş. Hz. Hacer'in hikayesi hatırlanıyor — oğlu İsmail için su aradı, aynı iki tepe arasında 7 kez koştu. ✋ Mermer zemin, fluorescent aydınlatma, uzun koridor. Yeşil ışık bölgesinde erkekler hafifçe koşuyor (hervele).
- Sayfa 10: 7. gidiş-geliş tamamlanıyor! {child_name} yorgun ama mutlu. Bacakları ağrıyor, ama kalbinde bir hafiflik var. "Hz. Hacer bundan çok daha zor koşmuştu" diyor {child_name} sessizce.
- 🪝 HOOK: "Sa'y bitmişti — ama ihramdan çıkmak için bir adım daha vardı..."

### BÖLÜM 5 — Saç Kesme ve İhramdan Çıkış (Sayfa 11) 🎯 Duygu: YENİLENME + HUZUR
- Sayfa 11: Taksir zamanı. KIZ ise: annesi / bir kadın saçının ucundan parmak ucu kadar kesiyor — {child_name} gülümsüyor, "Yenilendim." ERKEK ise: erkek berber, başın en az dörtte birinden kısaltıyor (KAZITMAK / KEL YASAK — sadece kısaltma!). Saç yere düşünce {child_name} derin bir nefes alıyor. İhram çıkarılıyor. Umre ibadetleri TAMAMLANDI. ✋ Normal kıyafet giymek garip ama rahatlatıcı.

### BÖLÜM 6 — Mekke Mescit Ziyareti (Sayfa 12-13) 🎯 Duygu: DERİNLİK + MANEVİYAT
- Sayfa 12: Mekke'deki büyük kubbeli mescide ziyaret. ✋ Mermer sütunlar serin, kubbe altı akustik — her fısıltı yankılanıyor. Altın ışık kubbelerden süzülüyor.
- Sayfa 13: {child_name} sessizce oturuyor, düşünüyor. Artık takke (erkek) veya hicap (kız) var. Kalabalığın dua uğultusu, huzur. "Buranın havası bile farklı" diyor sessizce.
- 🪝 HOOK: "Ama Medine bekliyordu — ve Yeşil Kubbe uzaktan çoktan görünmeye başlamıştı..."

### BÖLÜM 7 — Medine ve Mescid-i Nebevi (Sayfa 14-15) 🎯 Duygu: SEVGİ + SAYGI + DERİN BAĞLILIK
- Sayfa 14: Medine'ye yolculuk. Yeşil alanlar, hurma ağaçları. Uzakta Yeşil Kubbe — kalp hızlanıyor. "Resulullah'ın (sav) şehri" fısıldıyor {child_name}.
- Sayfa 15: Mescid-i Nebevi. Yeşil kubbe, görkemli minareler, geniş mermer avlu. İçeride sakin, derin huzur. Resulullah (sav) hakkında anlatılanlar — ama görselleştirme yok, sadece hissiyat ve anlatım. {child_name}'in gözleri doluyor — bu sefer de saygıdan.

### BÖLÜM 8 — Uhud ve Hendek (Sayfa 16-17) 🎯 Duygu: TARİH + DERİN DÜŞÜNCE
- Sayfa 16: Uhud tepesi ziyareti. Savaş alanının panoraması. Hz. Hamza ve şehitlerin hatırası. {child_name} tepeye bakıyor — rüzgar esiyor, sessizlik hakim.
- Sayfa 17: Hendek (Ahzab) Savaşı alanı. Hendeğin kalıntıları. Sahabenin azmi ve birliği. {child_name} derin düşüncelerde: bu topraklar çok şey gördü.

### BÖLÜM 9 — Eve Dönüş (Sayfa 18-22) 🎯 Duygu: HUZUR + DÖNÜŞÜM
- Sayfa 18-19: Son günler Medine'de — Mescid-i Nebevi'de son namazlar. Veda. 🔊 Ezan sesi, mermer serin, palmiye yaprakları hışırtısı.
- Sayfa 20: Eve dönüş yolculuğu. {child_name} pencereden bakıyor. Kutsal topraklar geride kalıyor ama kalbinde kalıyor.
- Sayfa 21-22: Evde. Bavulunu açıyor — Zemzem şişesi, tesbih, küçük hediyeler. Ama asıl değişim içinde. Gülümsüyor. Dua ediyor. Farklı bir {child_name}.
- Son cümle: "{child_name} gözlerini kapadı ve fısıldadı: 'İnşallah yine gideriz...' Kalbi hâlâ Kabe'nin etrafında dönüyordu."

---

## 🚫 KURALLAR
- Uçak, kabin, uçuş sahnesi ÇİZME/YAZMA.
- Peygamber (sav), melek görselleştirme YASAK — sadece anlatım ve hissiyat.
- Saç kesme: SADECE kısaltma (taksir). Kazıtma/kel/0'a vurma YASAK.
- KIZ çocuğun saçını SADECE KADIN keser.
- Didaktik vaaz/nasihat YASAK — yaşayarak anlat.
- Büyü/sihir YASAK — maneviyat doğaldır.
- İlk sayfa [Sayfa 1] ile başla.

## ⚠️ YAZIM KURALLARI

❌ YANLIŞ (Vaaz): "{child_name} namaz kılmanın ne kadar önemli olduğunu öğrendi. Allah'a itaat etmeliyiz."
✅ DOĞRU (Yaşayarak): "{child_name} alnını mermere koydu — serin ve pürüzsüzdü. Bir an her şey durdu."

❌ YANLIŞ (Gezi Rehberi): "Kabe, İslam'ın en kutsal mabedidir. Her yıl milyonlarca Müslüman ziyaret eder."
✅ DOĞRU (Macera Anı): "Kabe oradaydı — siyah ve altın, görkemli ve mütevazı aynı anda. {child_name}'in gözleri doldu."

## 💬 DİYALOG KURALI
Her 3-4 sayfada en az 1 kısa diyalog. {child_name} ve kafile üyeleri arasında samimi konuşmalar. Dualar fısıltıyla.

## ⛔ İÇERİK YASAKLARI
- Uçak/uçuş sahnesi YASAK
- Peygamber/melek görseli YASAK
- Tıraş/kel görseli YASAK
- Didaktik vaaz YASAK
- Büyü/sihir YASAK

Hikayeyi TAM OLARAK {page_count} sayfa yaz. Her sayfa 1-3 cümle (25-50 kelime).
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
        'Kiswah, white marble courtyard / Safa-Marwa: marble corridor with fluorescent lighting / '
        'Masjid Nabawi: green dome, grand interior / Zemzem: marble area near Kaaba / '
        'Uhud: hilltop panorama / Hendek: trench remnants near Medina]. '
        'Islamic geometric patterns, calligraphy on walls. Cinematic reverent lighting, warm '
        'golden glow, detailed marble texture, volumetric light through domes. Close-up on the '
        'child\'s expressive face for emotional moments, wide for sacred architecture. Expressive '
        'emotion (amazed, teary, smiling, determined, peaceful). No eye contact with camera. '
        'Reverent and realistic. NO glowing lights, NO magic, NO fairies, NO Prophet depictions. '
        '{STYLE}'
    ),

    # ── G: Kıyafetler ── (İhram öncesi/sonrası outline — prompt'ta detaylı anlatılıyor)
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

    # ── G2: No companion/objects — spiritual journey ──
    companions=[],
    objects=[],

    # ── H: Kültürel Elementler ──
    cultural_elements={
        "values": ["Humility", "Patience", "Gratitude", "Unity", "Perseverance", "Submission to Allah"],
        "primary": [
            "Masjid al-Haram and the Kaaba (black Kiswah with golden calligraphy)",
            "White marble courtyard reflecting sacred golden light",
            "Tawaf: 7 shawts counter-clockwise around the Kaaba starting from Hajar al-Aswad",
            "Sa'y: 7 walks between Safa and Marwa marble corridor (Hajar's story)",
            "Zamzam sacred water — drunk standing, facing Kaaba",
        ],
        "location": "Mecca and Medina, Saudi Arabia",
        "secondary": [
            "Ihram garments: two unsewn white cloths (rida + izar) for men",
            "Talbiyah chant: Labbayk Allahumma Labbayk",
            "Maqam Ibrahim prayer station behind the Kaaba",
            "Masjid al-Nabawi and Green Dome (Medina)",
            "Uhud Hill — site of historic battle and martyrs",
            "Khandaq (Trench) site near Medina",
            "Hair cutting ceremony (taqsir) — renewal and ihram exit",
            "Islamic geometric patterns and Arabic calligraphy",
        ],
        "atmosphere": "Peaceful, reverent, spiritual, humble, transformative, deeply moving",
        "color_palette": "white (purity), gold (sacred/Kaaba calligraphy), green (Medina), black (Kiswah)",
    },

    # ── C/G3: Lokasyon Kısıtları ──
    location_constraints=(
        "Setting follows the authentic Umrah pilgrimage route. "
        "Pages 1-2: Airport preparation, ihram dressing — Medium Shot, humble, excited. "
        "Page 3: Walking toward Mecca in ihram, Talbiyah chorus — Wide Shot, white crowd. "
        "Pages 4-5: Masjid al-Haram entrance, FIRST VIEW OF KAABA — Hero Shot, awe-inspiring, tears. "
        "Pages 6-8: Tawaf 7 circuits, Maqam Ibrahim prayer, Zamzam water — Wide circle + Close-up emotion. "
        "Pages 9-10: Sa'y Safa to Marwa marble corridor, hervele zone — Medium walking shots. "
        "Page 11: Hair cutting (taqsir) — Close-up symbolic, NOT shaving/bald. "
        "Pages 12-13: Mecca domed mosque interior — Wide reverent, golden-marble. "
        "Page 14: Road to Medina, Green Dome in distance — Wide landscape. "
        "Page 15: Masjid al-Nabawi interior — Wide grand, green and gold. "
        "Page 16: Uhud Hill panorama — Wide dramatic. "
        "Page 17: Khandaq trench site — Medium historical. "
        "Pages 18-22: Farewell, return journey, home — Hero Shot, warm, emotional."
    ),

    # ── I: Scenario Bible ──
    scenario_bible={
        "no_companion": True,
        "child_solo_with_group": True,
        "special_rules": {
            "ihram_rules": (
                "Pages 3-10: IHRAM. Men: Rida (upper) + Izar (lower), 2 unsewn white cloth pieces. "
                "Head COMPLETELY BARE (no cap, hat, hood). Feet in sandals only. "
                "Women: Normal modest Islamic dress + properly wrapped hijab. Hands and face visible. "
                "IHRAM PROHIBITIONS: No sewn garments (men), no perfume, no nail cutting, "
                "no hair cutting, no arguing."
            ),
            "post_ihram_pages": (
                "Pages 12-22: Normal clothes. Boys: white kurta + white taqiyah cap. "
                "Girls: white dress + white hijab. Hair visible but modest."
            ),
            "hair_cutting": (
                "Page 11: TAQSIR only (trimming). Men: at least 1/4 of head hair shortened. "
                "Women: fingertip-length cut from hair ends. "
                "Girls' hair MUST be cut by a WOMAN (mother, aunt, female hairdresser). "
                "Male barber NEVER touches girl's hair. "
                "ABSOLUTELY NO shaving, NO bald depiction, NO zero-cut."
            ),
            "prophet_rule": "NO visual depiction of Prophet Muhammad (sav) or angels. Narration and emotion only.",
            "airplane_rule": "NO airplane, cabin, or flight scenes. Start at airport meeting hall.",
            "umrah_sequence": (
                "1. Gusul → 2. Ihram wearing → 3. 2-rakat ihram prayer → 4. Niyyah → "
                "5. Talbiyah → 6. Enter Masjid al-Haram → 7. First Kaaba view (dua accepted) → "
                "8. Tawaf 7 shawts from Hajar al-Aswad → 9. Tawaf prayer at Maqam Ibrahim → "
                "10. Zamzam water → 11. Sa'y 7 walks Safa→Marwa → 12. Taqsir (hair cut) → "
                "13. Ihram exit = Umrah COMPLETE"
            ),
        },
        "zones": {
            "airport": "Excitement + preparation — caravan meeting, ihram dressing, first Talbiyah",
            "mecca_entry": "Sacred anticipation — white ihram crowd, Labbayk chorus, approaching Haram",
            "first_kaaba_view": "Overwhelming awe + tears — giant Kaaba in black and gold, dua moment",
            "tawaf": "Rhythmic unity + spiritual depth — 7 circuits, white marble, thousands moving as one",
            "zamzam": "Refreshment + gratitude — pure water, standing, facing Kaaba, bismillah",
            "say": "Determined perseverance — Safa-Marwa corridor, Hajar's story, hervele zone",
            "hair_cutting": "Symbolic renewal + peace — ihram exit, new beginning",
            "mecca_mosque": "Deep peace + reflection — domed interior, marble, golden light",
            "medina": "Warmth + love + respect — Green Dome, Masjid al-Nabawi, palm trees",
            "uhud_khandaq": "Historical depth + reflection — battlefields, martyrs, sahaba's sacrifice",
            "farewell": "Emotional transformation — goodbye, Zamzam bottle at home, changed heart",
        },
        "emotional_arc": {
            "S1-S2": "Excitement + sacred preparation (airport, ihram, first Talbiyah)",
            "S3": "Anticipation + awe building (walking to Haram, Labbayk chorus)",
            "S4-S5": "Overwhelming tears + awe (FIRST Kaaba view, accepted dua)",
            "S6-S8": "Unity + spiritual depth (Tawaf rhythm, Maqam Ibrahim, Zamzam taste)",
            "S9-S10": "Perseverance + historical empathy (Sa'y, Hajar's story, tired but fulfilled)",
            "S11": "Renewal + peace (hair cutting, ihram exit, deep breath)",
            "S12-S13": "Deep peace + reflection (Mecca mosque, marble acoustics, golden light)",
            "S14-S15": "Love + deep devotion (Medina arrival, Masjid al-Nabawi, Rasulullah)",
            "S16-S17": "Historical depth + contemplation (Uhud martyrs, Khandaq sacrifice)",
            "S18-S22": "Peace + transformation + longing (farewell, return, changed heart)",
        },
        "consistency_rules": [
            "İhram pages (S3-S10): White 2-piece unsewn cloth, HEAD COMPLETELY BARE (boys), hijab (girls)",
            "Post-ihram (S12+): Taqiyah cap (boys), hijab (girls), hair visible but modest",
            "Hair cutting (S11): ONLY TRIMMING, shaving/bald NEVER depicted",
            "Girl's hair cut by WOMAN ONLY (mother/aunt/female hairdresser)",
            "Prophet/angel visual NEVER drawn — narration and emotion only",
            "Marble texture and golden sacred light in ALL Mecca scenes",
            "Child's face and hair appearance CONSISTENT across all pages",
            "Airplane/cabin/flight scenes NEVER drawn",
            "Tawaf direction: counter-clockwise around Kaaba",
            "Sa'y starts from Safa, ends at Marwa (odd = Safa→Marwa, even = Marwa→Safa)",
        ],
        "key_locations": [
            "Airport preparation hall — ihram garments, excited crowd, no airplane",
            "Masjid al-Haram courtyard — white marble, Kaaba with golden Kiswah",
            "Tawaf circle — counter-clockwise, Hajar al-Aswad starting point",
            "Maqam Ibrahim — prayer station behind Kaaba, glass enclosure",
            "Zamzam well area — marble, drinking standing facing Kaaba",
            "Safa-Marwa marble corridor — fluorescent lighting, hervele green-light zone",
            "Barber/hair cutting area — symbolic renewal, NOT shaving",
            "Mecca domed mosque — interior with marble columns and golden dome light",
            "Road to Medina — green landscape, palm trees, Green Dome in distance",
            "Masjid al-Nabawi — Green Dome, grand white marble interior, minarets",
            "Uhud Hill — panoramic battlefield view, memorial",
            "Khandaq (Trench) site — trench remnants near Medina",
        ],
    },

    # ── J: Custom Inputs ──
    custom_inputs_schema=[],
))

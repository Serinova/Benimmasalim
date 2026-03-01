"""
Umre Yolculuğu: Kutsal Topraklarda — Düzeltilmiş
==================================================
- Modular prompt (500 char limit, tüm placeholder'lar mevcut)
- Hikaye: Umre ibadet sırasına göre (İhram → Tavaf → Sa'y → Zemzem → Tıraş)
- Çocuğun iç dünyası: Her ibadetin manevi anlamı ile iç savaşları birleşiyor
- Outfit: update_all_outfits.py standardı (EXACTLY lock phrase)
- custom_inputs_schema: list formatı
- Yüz benzerliği: CHARACTER block önce
"""

import asyncio
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sqlalchemy import select

from app.core.database import async_session_factory
from app.models.scenario import Scenario

# ============================================================================
# MODULAR PROMPT COMPONENTS (500 char limit!)
# ============================================================================

UMRE_COVER_PROMPT = (
    "An {child_age}-year-old {child_gender} named {child_name} "
    "with {hair_description}, wearing {clothing_description}. "
    "{scene_description}. "
    "Masjid al-Haram and black Kaaba with golden Kiswah in distance. "
    "White marble courtyard, golden minarets, grand domes. "
    "Peaceful pilgrims in white ihram (distant, no faces). "
    "Golden spiritual light. Wide shot: child 20%, architecture 80%. "
    "NO Prophet/angel depictions."
)

UMRE_PAGE_PROMPT = (
    "An {child_age}-year-old {child_gender} named {child_name} "
    "with {hair_description}, wearing {clothing_description}. "
    "{scene_description}. "
    "Locations: [Kaaba: black with golden Kiswah, white marble courtyard / "
    "Safa-Marwa: marble corridor, green-lit zone / "
    "Masjid Nabawi: green dome, date palms / Zemzem: marble, blessed water]. "
    "Islamic geometric patterns, calligraphy (decorative). "
    "Golden light, reverent. NO Prophet depictions."
)

# ============================================================================
# OUTFIT DEFINITIONS (update_all_outfits.py standardı)
# ============================================================================

OUTFIT_GIRL = (
    "pure white cotton modest long-sleeve dress reaching ankles with no patterns or decorations, "
    "white cotton hijab headscarf covering hair completely with simple neat edges, "
    "comfortable beige leather flat sandals, small white cotton drawstring backpack. "
    "Simple and clean appearance inspired by ihram purity, no jewelry. "
    "EXACTLY the same outfit on every page — same pure white dress, same white hijab, same beige sandals."
)

OUTFIT_BOY = (
    "pure white cotton knee-length kurta tunic with no patterns or decorations, "
    "white knit taqiyah prayer cap on head, light beige loose-fitting cotton pants, "
    "comfortable tan leather sandals, small white cotton drawstring backpack. "
    "Simple and clean appearance inspired by ihram purity. "
    "EXACTLY the same outfit on every page — same white kurta, same white taqiyah, same beige pants."
)

# ============================================================================
# STORY BLUEPRINT (Umre İbadet Sırasına Göre)
# ============================================================================

UMRE_STORY_PROMPT_TR = """
# UMRE YOLCULUĞU — KUTSAL TOPRAKLARDA MANEVİ KEŞİF

## TEMEL YAPI: 7 BÖLÜM, 22 SAYFA

Bu hikaye bir manevi yolculuk. {child_name}, büyükleriyle birlikte umre
yapmaya gidiyor. Her ibadet adımında çocuğun İÇ DÜNYASI'ndaki bir
duyguyla yüzleşmesi ve o ibadetin manevi anlamıyla dönüşmesi anlatılır.

⚠️ ÖNEMLİ KURALLAR:
- Umre ibadeti DOĞRU SIRAYLA yapılmalı: İhram → Telbiye → Tavaf → Sa'y → Zemzem → Tıraş
- Çocuk büyükleriyle birlikte (anne-baba-aile KARAKTERİ gösterilmez, sadece "yanındaki büyükler" olarak bahsedilir)
- Anne-baba yüzü, kıyafeti, fiziksel özellikleri ASLA tarif edilmez
- Her ibadette çocuğun bir İÇ SAVAŞI var → ibadet onu dönüştürüyor
- Vaaz edici DEĞİL, YAŞAYARAK öğrenme
- Hz. Muhammed, peygamberler, melekler GÖRSELLEŞTİRİLMEZ (sadece hikâye anlatımı)
- Namaz/ibadet close-up YOK, yüzler detaylı gösterilmez
- Korku/baskı/travma YOK
- Saygılı, huzurlu, duygusal ton

---

### BÖLÜM 1 — HAZIRLIK: İHRAMA GİRİŞ (Sayfa 1-4)
Havaalanında heyecan. Büyükleriyle kutsal topraklara gidiş. Mikat'a
yaklaşırken ihrama giriş — beyaz, sade, dikişsiz kıyafet.
**İÇ SAVAŞ: KİBİR / GÖSTERİŞ** — Çocuk güzel kıyafetlerini çıkarmak
istemiyor. "Neden herkes aynı giyiniyor?"
**DÖNÜŞÜM**: İhram = eşitlik. Zengin-fakir, büyük-küçük fark yok.
"Allah'ın önünde herkes eşit." Çocuk beyazın sadeliğinde huzur buluyor.
- S1: Havaalanı heyecanı, büyükleriyle yolculuk
- S2: Mikat'a yaklaşma, ihram hazırlığı
- S3: İhrama giriş — "Neden herkes aynı?" ✓ İÇ SAVAŞ
- S4: "Allah'ın önünde herkes eşit" — huzur ✓ İLK FARKINDALIK
**Değer**: Tevazu, eşitlik, sadelik

---

### BÖLÜM 2 — TELBİYE VE İLK GÖRÜŞ: KABE (Sayfa 5-8)
Telbiye okuyarak Mekke'ye giriş: "Lebbeyk Allahümme Lebbeyk..."
(Buyur Allah'ım, emrindeyim!) Mescid-i Haram'a ilk adım.
Ve Kabe... İlk görüş anı. Gözyaşları.
**İÇ SAVAŞ: SABIR / ACELECİLİK** — Çocuk hemen Kabe'ye koşmak istiyor.
**DÖNÜŞÜM**: Telbiye = teslimiyet. "Acele etme, her adım bir dua."
Yavaşça, huşu içinde yaklaşma. Kabe'yi görünce kalbinin durduğunu hissediyor.
- S5: Telbiye okuyarak yürüyüş — "Lebbeyk..."
- S6: Mescid-i Haram'a giriş — devasa avlu
- S7: KABE'Yİ İLK GÖRÜŞ — gözyaşları! ✓ DORUK DUYGU
- S8: "Kalbim durdu..." — huşu, hayranlık
**Değer**: Teslimiyet, huşu, sabır

---

### BÖLÜM 3 — TAVAF: KABE'NİN ETRAFINDA 7 TUR (Sayfa 9-12)
Hacerülesved köşesinden başlayarak Kabe'nin etrafında 7 tur.
Binlerce insan birlikte dönüyor — farklı ülkeler, farklı diller,
tek yürek. Yanındaki büyüğün elini tutarak yürüyor.
**İÇ SAVAŞ: BENCİLLİK / BEN-MERKEZCİLİK** — "Neden herkes aynı
yöne dönüyor? Ben farklı gitmek istiyorum."
**DÖNÜŞÜM**: Tavaf = birlik. Herkes aynı merkeze yöneliyor.
"Tek başıma değilim, hepimiz biriz." Çocuk kalabalığın içinde
birlik hissediyor, kalbinde sıcaklık.
- S9: Tavafa başlama — Hacerülesved köşesi
- S10: 7 tur — binlerce insan, farklı diller, tek yürek
- S11: "Neden hep aynı yöne?" → "Hepimiz biriz" ✓ BİRLİK ZİRVESİ
- S12: Makam-ı İbrahim'de dua — huzur
**Değer**: Birlik, topluluk, bencillikten kurtulma

---

### BÖLÜM 4 — SA'Y: SAFA VE MERVE ARASI 7 GİDİŞ-GELİŞ (Sayfa 13-16)
Safa Tepesi'nden Merve Tepesi'ne 7 kez gidip gelme. Yanındaki büyük, Hz. Hacer'in
hikâyesini anlatıyor: "Oğlu İsmail susuzluktan ağlıyordu. Hacer
çaresizce iki tepe arasında koştu. 7 kez. Vazgeçmedi."
**İÇ SAVAŞ: UMUTSUZLUK / VAZGEÇME** — Çocuk yoruluyor. "Çok uzun,
bitiyor mu?" Ayakları ağrıyor.
**DÖNÜŞÜM**: Sa'y = umut ve sebat. Hz. Hacer vazgeçmedi, su bulundu.
"Vazgeçmediğinde mucize gelir." Çocuk son turda güç buluyor.
- S13: Safa Tepesi'nden başlama — uzun koridor
- S14: Hz. Hacer'in hikâyesi — büyük anlatıyor ✓ DUYGU
- S15: Yorgunluk — "Bitiyor mu?" Yeşil ışıklı bölgede hızlanma ✓ İÇ SAVAŞ
- S16: Son tur — "Vazgeçmediğinde mucize gelir!" ✓ SEBAT ZİRVESİ
**Değer**: Sebat, umut, vazgeçmeme

---

### BÖLÜM 5 — ZEMZEM: KUTSAL SU (Sayfa 17-18)
Sa'y'dan sonra Zemzem suyu içme. Hz. İsmail'in ayağının dibinden
fışkıran mucizevi su — binlerce yıldır akıyor.
**İÇ SAVAŞ: NANKÖRLÜK / ŞÜKRETMEME** — Çocuk her şeyi doğal
karşılıyor, "su işte."
**DÖNÜŞÜM**: Zemzem = şükür. "Bu su binlerce yıldır Hz. Hacer'in
duasıyla akıyor. Her yudum bir nimet." İlk yudum — ferahlık,
gözlerinde minnet.
- S17: Zemzem suyu — "Binlerce yıldır akıyor!"
- S18: İlk yudum — ferahlık, minnet, şükür ✓ ŞÜKÜR ZİRVESİ
**Değer**: Şükür, nimet bilinci

---

### BÖLÜM 6 — MEDİNE: YEŞİL KUBBE VE HUZUR (Sayfa 19-21)
Medine'ye yolculuk. Mescid-i Nebevi, yeşil kubbe, hurma ağaçları.
Huzurlu atmosfer. Hz. Muhammed'in mescidi (hikâye olarak anlatılır).
**İÇ SAVAŞ: GÜRÜLTÜ / İÇ HUZURSUZLUK** — Çocuğun zihni hep meşgul,
düşünceler durmak bilmiyor.
**DÖNÜŞÜM**: Medine = huzur. Yeşil kubbenin altında sessizlik.
"Bazen susmak en güçlü duadır." Çocuk ilk kez gerçek iç huzuru
hissediyor.
- S19: Medine'ye varış — hurma ağaçları, sıcak karşılama
- S20: Mescid-i Nebevi — yeşil kubbe, huzur ✓ HUZUR ZİRVESİ
- S21: Sessizlik anı — "İç huzur buldum"
**Değer**: İç huzur, tefekkür, sakinlik

---

### BÖLÜM 7 — FİNAL: DÖNÜŞ VE YENİ BEN (Sayfa 22)
Saç kesme/tıraş ile ihramdan çıkış — yenilenme sembolü.
Eve dönüş. Çocuk değişmiş: daha sabırlı, daha şükredici, daha
mütevazı. "Ben aynı ben değilim. Umre beni değiştirdi."
Sevdikleriyle sarılma, minnet.
- S22: Saç kesme — yenilenme. Eve dönüş, yeni ben ✓ DÖNÜŞÜM DORUĞU
**Değer**: Manevi dönüşüm, yenilenme, minnet

---

## İÇ SAVAŞ → DÖNÜŞÜM HARİTASI:
1. İhram: Kibir/gösteriş → Tevazu ve eşitlik
2. Telbiye/Kabe: Sabırsızlık/acelecilik → Teslimiyet ve huşu
3. Tavaf: Bencillik → Birlik ve topluluk
4. Sa'y: Umutsuzluk/vazgeçme → Sebat ve umut
5. Zemzem: Nankörlük → Şükür ve nimet bilinci
6. Medine: İç huzursuzluk → Huzur ve tefekkür
7. Tıraş/Dönüş: Eski ben → Yeni, dönüşmüş ben

## DOPAMIN ZİRVELERİ:
1. S4: İhram — eşitlik farkındalığı
2. S7: Kabe ilk görüş — gözyaşları (doruk duygu)
3. S11: Tavaf — birlik hissi
4. S16: Sa'y son tur — sebat zaferi
5. S18: Zemzem — şükür
6. S20: Medine — iç huzur
7. S22: Dönüşüm — yeni ben

## GÜVENLİK KURALLARI:
- Peygamber/melek görseli YOK
- İbadet close-up YOK
- Yüzler detaylı gösterilmez
- Korku/baskı/travma YOK
- Mezhep ayrımcılığı YOK
- Vaaz edici DEĞİL, yaşayarak öğrenme
"""

# ============================================================================
# CULTURAL ELEMENTS
# ============================================================================

UMRE_CULTURAL_ELEMENTS = {
    "location": "Mecca and Medina, Saudi Arabia",
    "pilgrimage": "Umrah (minor pilgrimage)",
    "ritual_order": [
        "1. Ihram (sacred state, white garments, equality)",
        "2. Talbiyah (Labbayk Allahumma Labbayk — devotional chant)",
        "3. Tawaf (7 circuits around Kaaba, counterclockwise)",
        "4. Sa'y (7 walks between Safa and Marwa hills)",
        "5. Zamzam water (blessed spring water)",
        "6. Halq/Taqsir (hair cutting — renewal symbol)",
    ],
    "holy_sites": [
        "Kaaba and Masjid al-Haram (Mecca)",
        "Masjid al-Nabawi and Green Dome (Medina)",
        "Safa and Marwa Hills",
        "Zamzam Well",
    ],
    "atmosphere": "Peaceful, reverent, spiritual, humble, transformative",
    "color_palette": "white (purity), gold (sacred), green (Medina), black (Kaaba)",
    "values": ["Humility", "Patience", "Gratitude", "Unity", "Perseverance"],
}

# ============================================================================
# CUSTOM INPUTS (list formatı — frontend uyumlu)
# ============================================================================

UMRE_CUSTOM_INPUTS = [
    {
        "key": "favorite_location",
        "label": "En Merak Ettiği Yer",
        "type": "select",
        "options": ["Kabe ve Mescid-i Haram", "Mescid-i Nebevi (Medine)", "Safa-Marwa Tepeleri", "Zemzem Suyu"],
        "default": "Kabe ve Mescid-i Haram",
        "required": False,
        "help_text": "Hikayede çocuğun en çok vakit geçireceği yer",
    },
    {
        "key": "travel_with",
        "label": "Kimle Gidiyor",
        "type": "select",
        "options": ["Büyükleriyle", "Geniş grupla", "Dede/Nine ile"],
        "default": "Büyükleriyle",
        "required": False,
        "help_text": "Umre yolculuğuna kiminle gittiği",
    },
    {
        "key": "special_dua",
        "label": "Özel Dua Konusu",
        "type": "select",
        "options": ["Sevdiklerinin sağlığı için", "Bilgi ve başarı için", "Dünya barışı için", "Tüm insanlık için"],
        "default": "Sevdiklerinin sağlığı için",
        "required": False,
        "help_text": "Çocuğun özel olarak ettiği dua",
    },
]

# ============================================================================
# DATABASE UPDATE FUNCTION
# ============================================================================


async def update_umre_scenario():
    """Umre senaryosunu günceller."""

    async with async_session_factory() as db:
        result = await db.execute(
            select(Scenario).where(
                (Scenario.theme_key == "umre_pilgrimage")
                | (Scenario.name.ilike("%Umre%"))
            )
        )
        scenario = result.scalar_one_or_none()

        if not scenario:
            scenario = Scenario(name="Umre Yolculuğu: Kutsal Topraklarda", is_active=True)
            db.add(scenario)

        scenario.description = (
            "Büyükleriyle birlikte Mekke ve Medine'ye manevi bir yolculuk! "
            "Kabe'yi görme, tavaf, Safa-Marwa, Zemzem, yeşil kubbe. "
            "Saygı, tevazu ve şükür dolu bir deneyim."
        )
        scenario.theme_key = "umre_pilgrimage"
        scenario.cover_prompt_template = UMRE_COVER_PROMPT
        scenario.page_prompt_template = UMRE_PAGE_PROMPT
        scenario.story_prompt_tr = UMRE_STORY_PROMPT_TR
        scenario.outfit_girl = OUTFIT_GIRL
        scenario.outfit_boy = OUTFIT_BOY
        scenario.cultural_elements = UMRE_CULTURAL_ELEMENTS
        scenario.custom_inputs_schema = UMRE_CUSTOM_INPUTS
        scenario.marketing_badge = "Manevi Yolculuk"
        scenario.age_range = "7-10"
        scenario.tagline = "Kutsal topraklarda unutulmaz bir manevi deneyim"
        scenario.is_active = True
        scenario.display_order = 14

        await db.commit()
        print(f"Umre scenario updated: {scenario.id}")


if __name__ == "__main__":
    asyncio.run(update_umre_scenario())

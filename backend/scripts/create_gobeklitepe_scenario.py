"""
Göbeklitepe Macerası — Birleştirilmiş Güncelleme
=================================================
- Modular prompt (500 char limit, tüm placeholder'lar mevcut)
- Hikaye: Macera odaklı (gezi rehberi DEĞİL)
- Outfit: update_all_outfits.py standardı (EXACTLY lock phrase)
- custom_inputs_schema: list formatı (frontend uyumlu)
- Yüz benzerliği: CHARACTER block önce, fiziksel özellik yok
"""

import asyncio
import os
import sys
import uuid

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sqlalchemy import select

from app.core.database import async_session_factory
from app.models.scenario import Scenario

# ============================================================================
# MODULAR PROMPT COMPONENTS (500 char limit!)
# ============================================================================

GOBEKLITEPE_COVER_PROMPT = (
    "An {child_age}-year-old {child_gender} named {child_name} "
    "with {hair_description}, wearing {clothing_description}. "
    "{scene_description}. "
    "Ancient Gobeklitepe T-shaped megalithic pillars with animal carvings in background. "
    "Harran Plain steppe, golden sunset light on limestone. "
    "Wide shot: child 30%, ancient pillars 70%. "
    "Epic archaeological wonder atmosphere."
)

GOBEKLITEPE_PAGE_PROMPT = (
    "An {child_age}-year-old {child_gender} named {child_name} "
    "with {hair_description}, wearing {clothing_description}. "
    "{scene_description}. "
    "Elements: [T-pillars: 3-5m limestone megaliths, animal carvings (fox, lion, snake, vulture) / "
    "Circular enclosures: stone rings / Harran Plain: golden steppe / "
    "Stone quarry: unfinished pillars in bedrock]. "
    "Warm sandstone gold, amber, sage green tones."
)

# ============================================================================
# OUTFIT DEFINITIONS (update_all_outfits.py standardı)
# ============================================================================

OUTFIT_GIRL = (
    "sand-yellow cotton t-shirt with small compass emblem on chest, "
    "light olive green cotton shorts reaching knees, tan brown leather sandals, "
    "wide-brim straw sun hat with brown ribbon, small woven crossbody bag. "
    "EXACTLY the same outfit on every page — same yellow shirt, same olive shorts, same straw hat."
)

OUTFIT_BOY = (
    "burnt orange cotton polo shirt, "
    "stone beige cargo shorts with button-flap pockets, dark brown leather sandals, "
    "khaki bucket hat, small tan canvas satchel bag across body. "
    "EXACTLY the same outfit on every page — same orange polo, same beige shorts, same bucket hat."
)

# ============================================================================
# STORY BLUEPRINT (Macera odaklı)
# ============================================================================

GOBEKLITEPE_STORY_PROMPT_TR = """
# GÖBEKLİTEPE MACERASI — 12.000 YILLIK GİZEM

## TEMEL YAPI: 7 BÖLÜM, 22 SAYFA

Bu hikaye bir arkeoloji macerası. {child_name}, Göbeklitepe'de dikilitaşlardan
canlanan bir Bilge Tilki ile 12.000 yıl öncesinin gizemini çözer.

⚠️ ÖNEMLİ KURALLAR:
- Bu bir MACERA hikayesi, gezi rehberi DEĞİL
- Her bölümde çocuk AKTİF katılımcı (gözlemci değil)
- Endişe → Eylem → Başarı döngüsü her bölümde
- Yardımcı karakter: Bilge Tilki (dikilitaştaki tilki kabartmasından canlanan)
- Çocuk TEK BAŞINA macerada (aile yok)
- Korku/şiddet/gore YOK, eğitici ve heyecanlı
- Dini ritüel/ibadet sahnesi YOK

---

### BÖLÜM 1 — GİRİŞ: GİZEMLİ DİKİLİTAŞLAR (Sayfa 1-4)
{child_name} Şanlıurfa'da bir tepeye tırmanırken dev taş sütunlar görür.
Bir dikilitaştaki tilki kabartması parlamaya başlar — Bilge Tilki canlanır!
"12.000 yıllık bir gizem var, çözmeme yardım eder misin?"
- S1: Harran Ovası'nda tepeye tırmanma, uzakta garip taşlar
- S2: Dev T-şekilli dikilitaşlara yaklaşma, hayvan kabartmaları
- S3: Tilki kabartması parlıyor, Bilge Tilki canlanıyor!
- S4: "12.000 yıllık bir gizem!" — macera başlıyor ✓ İLK HEYECAN
**Değer**: Merak, keşif cesareti

---

### BÖLÜM 2 — DAİRESEL TAPINAK: TAŞLARIN SIRRI (Sayfa 5-8)
Bilge Tilki çocuğu dairesel taş yapıların içine götürür. Her dikilitaşta
farklı hayvan kabartması — aslan, yılan, akbaba, akrep. "Bu hayvanlar
bir mesaj veriyor, ama sırayı bulmamız lazım!"
- S5: Dairesel taş yapıya giriş, iç içe halkalar
- S6: Hayvan kabartmalarını inceleme — her biri farklı
- S7: "Sırayı bulmamız lazım!" — bulmaca başlıyor ✓ ENDİŞE
- S8: İlk ipucu bulundu — akbaba kabartması yukarı bakıyor
**Değer**: Gözlem, analitik düşünme

---

### BÖLÜM 3 — TAŞ OCAĞI: YARIM KALMIŞ DEV (Sayfa 9-12)
Bilge Tilki çocuğu taş ocağına götürür. Devasa bir dikilitaş hâlâ ana
kayaya bağlı — yarım kalmış! "Bunu yapmak için yüzlerce insan birlikte
çalışmış. Tek başına yapılamaz!" Çocuk taş aletleri deniyor.
- S9: Taş ocağına varış, yarım kalmış dev dikilitaş
- S10: "Bu kadar büyük taşı nasıl kesmişler?" — hayranlık
- S11: Taş aletleri deneme, çok zor! ✓ ZORLUK
- S12: "Yüzlerce insan birlikte çalışmış!" — işbirliği dersi ✓ MİMARİ ZİRVESİ
**Değer**: İşbirliği, azim, takım çalışması

---

### BÖLÜM 4 — GİZEMLİ SEMBOLLER: MESAJI ÇÖZMEK (Sayfa 13-16)
Dikilitaşlardaki hayvan kabartmaları bir harita oluşturuyor! Çocuk
Bilge Tilki'nin yardımıyla sembolleri birleştiriyor. Her hayvan bir yönü
gösteriyor — tilki kuzeyi, akbaba gökyüzünü, yılan yeraltını...
- S13: Sembolleri birleştirme fikri — "Bu bir harita!"
- S14: Tilki = kuzey, akbaba = gökyüzü, yılan = yeraltı
- S15: Haritayı takip etme, gizli bir geçit bulma ✓ KEŞİF HEYECANI
- S16: "Mesajı çözüyoruz!" — bulmaca tamamlanıyor ✓ BULMACA ZİRVESİ
**Değer**: Problem çözme, yaratıcı düşünme

---

### BÖLÜM 5 — YERİN ALTINDA: GİZLİ ODA (Sayfa 17-19)
Gizli geçit yeraltına iniyor. Karanlık ama Bilge Tilki'nin gözleri parlıyor
ve yol gösteriyor. Bir oda — içinde hiç görülmemiş kabartmalar, taş
figürinler ve obsidyen aletler!
- S17: Yeraltı geçidine giriş, karanlık, biraz korku ✓ ENDİŞE
- S18: Bilge Tilki yol gösteriyor, cesaret bulma
- S19: Gizli oda! Hiç görülmemiş kabartmalar! ✓ DORUK KEŞİF
**Değer**: Cesaret, güven

---

### BÖLÜM 6 — URFA ADAMI: İNSANLIĞIN İLK HEYKELİ (Sayfa 20-21)
Gizli odada özel bir taş heykel — Urfa Adamı! Dünyanın en eski insan
heykeli. Bilge Tilki: "12.000 yıl önce insanlar sanat yapıyordu,
birlikte çalışıyordu, yıldızları izliyordu. İnsanlık hep meraklıydı."
- S20: Urfa Adamı heykeli — "Dünyanın en eski insan heykeli!"
- S21: Bilge Tilki'nin bilgeliği — "İnsanlık hep meraklıydı" ✓ BİLGELİK DORUĞU
**Değer**: Tarih bilinci, insanlık mirası

---

### BÖLÜM 7 — FİNAL: DÖNÜŞ VE GURUR (Sayfa 22)
Çocuk yerüstüne çıkar. Gün batımında dikilitaşlara bakar. Bilge Tilki
tekrar kabartmaya dönüyor ama gülümsüyor. "Gizem çözüldü. Ama daha
çok gizem var — merakını hiç kaybetme!"
- S22: Gün batımı, dikilitaşlar, gurur ve şükran ✓ TATMIN DORUĞU
**Değer**: Merak, bilimsel düşünme, kültürel miras koruma

---

## DOPAMIN ZİRVELERİ:
1. S4: Bilge Tilki canlanıyor — macera başlıyor
2. S8: İlk ipucu bulundu
3. S12: Taş ocağı — işbirliği dersi
4. S16: Bulmaca çözüldü — harita tamamlandı
5. S19: Gizli oda keşfi — doruk
6. S21: Urfa Adamı — bilgelik
7. S22: Gurur ve dönüş

## GÜVENLİK KURALLARI:
- Korku/şiddet/gore YOK
- Dini ritüel/ibadet YOK
- Tehlikeli davranış teşviki YOK
- Yeraltı sahnesi korkutucu DEĞİL, heyecanlı
"""

# ============================================================================
# CULTURAL ELEMENTS
# ============================================================================

GOBEKLITEPE_CULTURAL_ELEMENTS = {
    "location": "Sanliurfa, Turkey (Harran Plain)",
    "historic_site": "Gobeklitepe, 12,000 years old (world's oldest temple)",
    "unesco": "UNESCO World Heritage Site",
    "architecture": [
        "T-shaped megalithic pillars (3-5m tall)",
        "Animal relief carvings (fox, lion, snake, vulture, scorpion)",
        "Circular stone enclosures (concentric rings)",
        "Stone quarry with unfinished pillars in bedrock",
    ],
    "atmosphere": "Ancient, mysterious, archaeological wonder",
    "color_palette": "golden sandstone, warm amber, dusty terracotta, sage green, sky blue",
    "educational_focus": [
        "World's oldest known temple (12,000 years)",
        "Predates Stonehenge by 6,000 years",
        "Hunter-gatherer society building monumental architecture",
        "Archaeological discovery and scientific method",
    ],
    "values": ["Curiosity", "Cooperation", "History appreciation", "Scientific thinking"],
}

# ============================================================================
# CUSTOM INPUTS (list formatı — frontend uyumlu)
# ============================================================================

GOBEKLITEPE_CUSTOM_INPUTS = [
    {
        "key": "favorite_animal",
        "label": "En Sevdiği Dikilitaş Hayvanı",
        "type": "select",
        "options": ["Tilki", "Aslan", "Yılan", "Akbaba", "Akrep"],
        "default": "Tilki",
        "required": False,
        "help_text": "Hikayede bu hayvan dikilitaştan canlanacak ve rehberlik edecek",
    },
    {
        "key": "special_discovery",
        "label": "Keşfetmek İstediği Şey",
        "type": "select",
        "options": ["Gizli Yeraltı Odası", "Kayıp Dikilitaş", "Antik Harita", "Sihirli Taş Figürini"],
        "default": "Gizli Yeraltı Odası",
        "required": False,
        "help_text": "Hikayede çocuğun keşfedeceği büyük sır",
    },
]

# ============================================================================
# DATABASE UPDATE FUNCTION
# ============================================================================


async def create_gobeklitepe_scenario():
    """Göbeklitepe senaryosunu oluşturur veya günceller."""

    async with async_session_factory() as db:
        result = await db.execute(
            select(Scenario).where(
                (Scenario.theme_key == "gobeklitepe")
                | (Scenario.name.ilike("%Göbeklitepe%"))
                | (Scenario.name.ilike("%Gobeklitepe%"))
            )
        )
        scenario = result.scalar_one_or_none()

        if not scenario:
            scenario = Scenario(id=uuid.uuid4())
            db.add(scenario)

        scenario.name = "Göbeklitepe Macerası"
        scenario.description = (
            "12.000 yıl öncesine yolculuk! Dünyanın EN ESKİ tapınağı "
            "Göbeklitepe'yi keşfet. 5m yüksek T-sütunlar, hayvan kabartmaları "
            "ve avcı-toplayıcıların mucizesi. UNESCO Dünya Mirası'nda "
            "prehistorik keşif!"
        )
        scenario.theme_key = "gobeklitepe"
        scenario.cover_prompt_template = GOBEKLITEPE_COVER_PROMPT
        scenario.page_prompt_template = GOBEKLITEPE_PAGE_PROMPT
        scenario.story_prompt_tr = GOBEKLITEPE_STORY_PROMPT_TR
        scenario.outfit_girl = OUTFIT_GIRL
        scenario.outfit_boy = OUTFIT_BOY
        scenario.cultural_elements = GOBEKLITEPE_CULTURAL_ELEMENTS
        scenario.custom_inputs_schema = GOBEKLITEPE_CUSTOM_INPUTS
        scenario.marketing_badge = "YENİ! Zaman Sıfır Noktası"
        scenario.age_range = "8-10"
        scenario.tagline = "12.000 yıllık gizemi çöz!"
        scenario.is_active = True
        scenario.display_order = 3

        await db.commit()
        print(f"Göbeklitepe scenario updated: {scenario.id}")


if __name__ == "__main__":
    asyncio.run(create_gobeklitepe_scenario())

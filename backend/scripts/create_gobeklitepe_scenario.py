"""
Göbeklitepe Macerası — Arkadaşlarla, geçit ile zamanda yolculuk
===============================================================
- {child_name} ARKADAŞLARI ile Göbeklitepe'de gezer; rehber gezisi DEĞİL, macera.
- Gizli bir geçit keşfederler → geçitten geçince 12.000 yıl öncesine giderler.
- Orada izlerler, gizlenirler, avcı-toplayıcılara yardım ederler, bir sorun çözerler, tarihe dokunurlar → geri dönerler.
- Kıyafet: arkeoloji saha kıyafeti (kız/erkek), hikayenin ruhuna uygun.
- Aşağıdan seçilen "en sevdiği" öğe hikaye akışını çok değiştirmez; hafif vurgu.
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
# OUTFIT — Arkeoloji saha kıyafeti (kız/erkek), hikayenin ruhuna uygun
# ============================================================================

OUTFIT_GIRL = (
    "beige cotton field shirt with button-down collar and chest pocket, "
    "olive green cargo pants with side pockets, tan leather ankle boots, "
    "wide-brim sand-colored canvas sun hat, small khaki field bag crossbody. "
    "EXACTLY the same outfit on every page — same beige shirt, same olive cargo pants, same sun hat."
)

OUTFIT_BOY = (
    "stone beige safari-style shirt with flap pockets, "
    "khaki cargo pants with button-flap pockets, brown leather work boots, "
    "tan canvas explorer hat, small olive field satchel across body. "
    "EXACTLY the same outfit on every page — same beige shirt, same khaki cargo, same explorer hat."
)

# ============================================================================
# STORY BLUEPRINT — Arkadaşlarla gezi, geçit keşfi, 12.000 yıl öncesine yolculuk
# ============================================================================

GOBEKLITEPE_STORY_PROMPT_TR = """
# GÖBEKLİTEPE MACERASI — ARKADAŞLARLA, TARİHE DOKUNUŞ

## YAPI: {child_name} ARKADAŞLARI İLE Göbeklitepe'de gezer. Rehber gezisi DEĞİL — macera. Gizli bir geçit keşfederler; geçitten geçince 12.000 yıl öncesine (Göbeklitepe'nin yaşandığı tarih) giderler. Orada izlerler, gizlenirler, avcı-toplayıcılara yardım ederler, bir sorun çözerler, tarihe dokunurlar; sonra geçitten geri dönüp bugüne gelirler.

**BAŞLIK:** Kitap adı sadece "[Çocuk adı]'ın Göbeklitepe Macerası" olmalı. Alt başlık EKLEME.

**KURGU:** Çocuk AİLE ile değil ARKADAŞLARI (2-3 kişi, aynı yaş grubu) ile Göbeklitepe'ye gelir. Rehber yok; kendi keşifleri. Gezerken gizli bir geçit/mağara ağzı bulurlar. İçeri girince kendilerini 12.000 yıl öncesinde (avcı-toplayıcıların dikilitaşları inşa ettiği dönem) bulurlar. Orada: avcı-toplayıcıları izlerler, gizlenirler, onların bir sorununa (kayıp eşya, taş taşıma, ipucu bulma vb.) yardım ederler — "tarihe dokunurlar". Sonra aynı geçitten geri geçip bugüne dönerler. Macera odaklı; korku/şiddet yok.

**EN SEVDİĞİ SEÇİMİ:** Aşağıdan seçilen öğe (T-sütunlar, hayvan kabartmaları vb.) hikayenin ana akışını DEĞİŞTİRMEZ. Sadece 1-2 sahnede hafif vurgu veya detay olarak geçebilir (örn. çocuğun en sevdiği hayvan kabartmada görünür). Ana olay: geçit → zaman yolculuğu → yardım → dönüş.

---

### Bölüm 1 — Arkadaşlarla Göbeklitepe'de (Sayfa 1-4)
- {child_name} arkadaşları ile Şanlıurfa'da, Göbeklitepe arkeolojik alanına gelir. Rehber değil, kendi başlarına geziyorlar.
- Dev T-sütunları, hayvan kabartmalarını görüp heyecanlanırlar. "12.000 yıl önce insanlar bunları yapmış!"
- Dolaşırken taşların arasında gizli bir geçit / mağara ağzı fark ederler. Merakla içeri bakarlar.
- "İçeri girelim mi?" — cesaret toplayıp geçide girerler. ✓ MACERA BAŞLIYOR

---

### Bölüm 2 — Geçit: 12.000 Yıl Öncesine (Sayfa 5-8)
- Geçitte yürürler; ışık değişir, sesler farklılaşır. Çıktıklarında manzara değişmiştir: aynı tepe ama inşaat hâlinde, insanlar taş taşıyor, dikilitaşlar yükseliyor.
- Şaşkınlık: "Zaman değişti! 12.000 yıl öncesindeyiz!" Avcı-toplayıcılar (deri/kürk kıyafet, taş aletler) görürler.
- Gizlenirler, uzaktan izlerler. İnsanların birlikte çalıştığını, taşları nasıl kaldırdıklarını görürler.
- Bir an onlara çok yaklaşan bir çocuk yaşında avcı-toplayıcı fark ederler; göz göze gelirler — ama kavga yok, merak var. ✓ ZAMAN YOLCULUĞU ZİRVESİ

---

### Bölüm 3 — Gizlenmek ve İzlemek (Sayfa 9-12)
- Taşların arkasında kalıp avcı-toplayıcıların günlük işlerini izlerler: taş yontma, ateş, basit barınak. "Tarihe dokunuyoruz."
- Bir sorun olur: İnşaatta çalışanlardan birinin önemli bir taş aleti kaybolur veya bir ipucu bulunamaz. {child_name} ve arkadaşları — gizlendikleri yerden — ipucu görürler (örn. taşın nerede kaldığı).
- Cesaret toplayıp (görünmeden veya hafif temasla) ipucu bırakırlar veya sorunu çözmelerine yardım ederler. Avcı-toplayıcılar memnun olur, çocuklar kendilerini iyi hisseder.
- "Onlara yardım ettik! Tarihe dokunduk." ✓ YARDIM / TARİHE DOKUNUŞ ZİRVESİ

---

### Bölüm 4 — Dairesel Yapı ve Hayvan Kabartmaları (Sayfa 13-16)
- Dairesel taş yapının etrafında dolaşırlar (gizlenerek). Hayvan kabartmaları: tilki, aslan, yılan, kuş. "Bunlar 12.000 yıl sonra hâlâ duracak."
- Küçük bir macera: Bir avcı-toplayıcı çocuk onları fark eder; korku yok, merak. Belki el işaretiyle selamlaşırlar veya küçük bir hediye (taş, çiçek) paylaşırlar.
- Geçidin nerede olduğunu hatırlayıp sessizce oraya doğru ilerlerler. "Geri dönme zamanı."
- Geçide girerler; ışık ve ses tekrar değişir. ✓ DÖNÜŞE HAZIRLIK

---

### Bölüm 5 — Bugüne Dönüş (Sayfa 17-20)
- Geçitten çıkınca her şey tekrar bugünkü hâline dönmüştür: aynı dikilitaşlar ama artık 12.000 yıl aşınmış, turist yolları.
- Arkadaşları ile birbirlerine bakarlar: "Gerçek miydi?" "Evet — onlara yardım ettik." Gurur ve hayal.
- Dikilitaşlara son bir kez bakarlar; hayvan kabartmalarını tanırlar. "Bunları yapan insanlara dokunduk."
- Gün batımında alandan ayrılırlar. "En iyi macera buydu." ✓ TATMIN

---

### Bölüm 6 — Kapanış (Sayfa 21-22)
- Eve / kalacak yere dönüş yolunda konuşurlar: tarih, merak, yardım, arkadaşlık.
- Kısa ve sıcak kapanış. "Göbeklitepe'yi unutmayacağız."

---

## KURALLAR
- Rehber YOK. Arkadaşlarla kendi keşifleri.
- Geçit → 12.000 yıl öncesi → izleme, gizlenme, yardım (bir sorun çözme) → geri dönüş. Ana akış bu.
- Seçilen "en sevdiği" öğe sadece hafif vurgu; akışı bozmasın.
- Korku/şiddet/gore YOK. Avcı-toplayıcılar tehdit değil, merak ve yardım objesi.
- Kitap adı SADECE "[Çocuk adı]'ın Göbeklitepe Macerası". Alt başlık ekleme.

Hikayeyi TAM OLARAK {page_count} sayfa yaz. Her sayfa 2-4 cümle, akıcı ve macera dolu.
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
# CUSTOM INPUTS — Hafif; seçilen öğe hikaye akışını çok değiştirmez (sadece vurgu)
# ============================================================================

GOBEKLITEPE_CUSTOM_INPUTS = [
    {
        "key": "favorite_element",
        "label": "En Sevdiği Öğe",
        "type": "select",
        "options": [
            "T-sütunlar (dev dikilitaşlar)",
            "Hayvan kabartmaları (tilki, aslan, yılan, kuş)",
            "Taş ocağı / inşaat",
            "Dairesel tapınak yapısı",
        ],
        "default": "Hayvan kabartmaları (tilki, aslan, yılan, kuş)",
        "required": False,
        "help_text": "Hikayede sadece hafif vurgu olarak geçer; ana akış (geçit, zaman yolculuğu, yardım) değişmez.",
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
            "Arkadaşlarla Göbeklitepe'de gezerken gizli bir geçit keşfedersin. "
            "Geçitten geçince 12.000 yıl öncesine gidersin; avcı-toplayıcılara "
            "yardım eder, tarihe dokunursun, sonra geri dönersin."
        )
        scenario.theme_key = "gobeklitepe"
        scenario.cover_prompt_template = GOBEKLITEPE_COVER_PROMPT
        scenario.page_prompt_template = GOBEKLITEPE_PAGE_PROMPT
        scenario.story_prompt_tr = GOBEKLITEPE_STORY_PROMPT_TR
        scenario.outfit_girl = OUTFIT_GIRL
        scenario.outfit_boy = OUTFIT_BOY
        scenario.cultural_elements = GOBEKLITEPE_CULTURAL_ELEMENTS
        scenario.custom_inputs_schema = GOBEKLITEPE_CUSTOM_INPUTS
        scenario.marketing_badge = "Arkadaşlarla Tarihe Dokunuş"
        scenario.age_range = "8-10"
        scenario.tagline = "Arkadaşlarla geçit keşfi, 12.000 yıl öncesine macera!"
        scenario.is_active = True
        scenario.display_order = 3

        await db.commit()
        print(f"Göbeklitepe scenario updated: {scenario.id}")


if __name__ == "__main__":
    asyncio.run(create_gobeklitepe_scenario())

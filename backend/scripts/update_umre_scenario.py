"""
Kutsal Topraklara Ziyaret — Umre senaryosu
==========================================
- Kitap adı: {child_name}'ın Kutsal Topraklara Ziyareti
- Kafile ile yolculuk (dede/nine değil). Uçak sahnesi yok.
- Havalimanında ihram hazırlığı → Cidde varışı → Kabeye doğru ihramla yürüyüş Lebbeyk → Kabe ilk görüş (duaların kabulü vurgusu) → Tavaf 3 sayfa → Sa'y 2 sayfa → Saç kesme 1 → Mekke kubbeli mescit 2 → Medine yolculuğu → Mescid-i Nebevi, Uhud, Hendek 1'er → Eve dönüş.
- Erkekler: ihramda baş açık; saç kesilene kadar ihram. Sonrası takke (saç 0'a vurulmaz, sadece kesilir; kel çizilmez). Kızlar: hicap.
- Metin sayfaya sığacak kadar KISA: sayfa başı 1-3 cümle (25-50 kelime). Kurguyu bozma.
- Kullanıcıya seçenek sunulmaz (custom_inputs boş/fixed).
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
    "Standing in the grand white marble courtyard before the magnificent black Kaaba draped in ornate golden Kiswah calligraphy embroidery. "
    "Towering golden minarets and grand Ottoman domes rising against a deep twilight sky, peaceful distant pilgrims in white ihram (small, no faces). "
    "Warm reverent golden light reflecting off polished marble, soft ambient glow from the minarets, gentle volumetric light around the Kaaba. "
    "Slightly low-angle shot: child 20% foreground, sacred architecture 80%. "
    "Sacred palette: pure white marble, deep black and gold Kiswah, warm amber glow, emerald green accents. "
    "NO airplanes, NO airport, NO glowing lights, NO magic, NO fairies, NO Prophet/angel depictions."
)

UMRE_PAGE_PROMPT = (
    "An {child_age}-year-old {child_gender} named {child_name} "
    "with {hair_description}, wearing {clothing_description}. "
    "{scene_description}. "
    "Locations: [Kaaba: black with golden Kiswah, white marble courtyard / "
    "Safa-Marwa: marble corridor / Masjid Nabawi: green dome / Zemzem: marble]. "
    "Islamic geometric patterns, calligraphy. "
    "Reverent and realistic. NO glowing lights, NO magic, NO fairies, NO Prophet depictions."
)

# ============================================================================
# OUTFIT DEFINITIONS (update_all_outfits.py standardı)
# ============================================================================

OUTFIT_GIRL = (
    "pure white cotton modest long-sleeve dress reaching ankles with no patterns or decorations, "
    "PROPERLY WRAPPED white hijab: fabric wraps FULLY around the head and neck — NO hair visible, NO neck visible, "
    "fabric drapes softly over shoulders and chest, neat pin-free folds, same style as a modern proper hijab wrap (NOT a loose veil, NOT a hood, NOT fabric merely draped on top of head). "
    "comfortable beige leather flat sandals, small white cotton drawstring backpack. "
    "Simple and clean appearance inspired by ihram purity, no jewelry. "
    "EXACTLY the same outfit on every page — same pure white dress, same properly wrapped white hijab, same beige sandals."
)

OUTFIT_BOY = (
    "pure white cotton knee-length kurta tunic with no patterns or decorations, "
    "small round white knitted taqiyah skull-cap sitting snugly on top of the head "
    "(NOT a turban, NOT a wrapped cloth, NOT a keffiyeh, NOT a hood — ONLY a small round knitted cap), "
    "light beige loose-fitting cotton pants, "
    "comfortable tan leather sandals, small white cotton drawstring backpack. "
    "Simple and clean appearance inspired by ihram purity. "
    "EXACTLY the same outfit on every page — same white kurta, same small round white taqiyah cap, same beige pants, same sandals."
)

# ============================================================================
# STORY BLUEPRINT — Kısa, sayfaya sığan, kafile ile, uçak yok
# ============================================================================

UMRE_STORY_PROMPT_TR = """
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

## GÖRSEL KURALLAR
- Sayfa 1-2: Henüz ihram yok veya hazırlık (erkekte baş açık).
- Sayfa 3-10: İHRAM — 2 parça beyaz bez, BAŞ AÇIK (takke yok).
- Sayfa 11: Saç kesme anı (sadece kesim; tıraş/kel YOK). Kız çocuk varsa saçını KADIN keser (anne/teyze/kadın kuaför); erkek berber kızın saçına dokunmaz. Erkek çocukta erkek berber olabilir.
- Sayfa 12-22: Takke (erkek), normal saç — kel çizilmez. Kızlar hicap.
- Peygamber/melek görseli YOK. Vaaz yok, yaşayarak anlat.
- İlk sayfa [Sayfa 1] ile başla. Uçak, kabin, uçuş sahnesi ÇİZME.

Hikayeyi TAM OLARAK {page_count} sayfa yaz. Her sayfa 1-3 cümle (25-50 kelime). Kısa tut; sayfaya sığsın.
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
        "6. Saç kesme (hair cutting — renewal symbol; trim only, no shave)",
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
# CUSTOM INPUTS — Umre için seçenek sunulmaz, direkt sabit senaryo
# ============================================================================

UMRE_CUSTOM_INPUTS: list[dict] = []

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
            scenario = Scenario(name="Kutsal Topraklara Ziyareti", is_active=True)
            db.add(scenario)

        scenario.name = "Kutsal Topraklara Ziyareti"
        scenario.description = (
            "Kafile ile Mekke ve Medine'ye umre ziyareti. "
            "Kabe ilk görüş, tavaf, Sa'y, saç kesme, Mescid-i Nebevi, Uhud, Hendek. "
            "Kitap adı: [Çocuk adı]'ın Kutsal Topraklara Ziyareti."
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

"""
Kapadokya Macerası — Rehberli gezi, macera, puzzle/zorluk
==========================================================
- Kitap adı: [Çocuk adı]'ın Kapadokya Macerası (alt başlık yok)
- Rehber ile gezi; çocuk maceraya atılır, sır/bulmaca çözer, zorluklarla karşılaşır ve aşar
- Peri bacaları (volkanik tüf, rüzgar/yağmur aşınması), Göreme, yeraltı, balon — kültürel yerler
- Çok ütopikleştirmeden, maceraperest ama gerçekçi
- Kurguyu bozabilecek kullanıcı seçenekleri kaldırıldı (custom_inputs boş)
"""

import asyncio
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sqlalchemy import select

from app.models import Scenario

# ============================================================================
# MODULAR PROMPT COMPONENTS (500 char limit!)
# ============================================================================

CAPPADOCIA_COVER_PROMPT = (
    "An {child_age}-year-old {child_gender} named {child_name} "
    "with {hair_description}, wearing {clothing_description}. "
    "{scene_description}. "
    "Towering Cappadocia fairy chimneys of eroded volcanic tuff with honeycomb cave textures, colorful hot air balloons drifting across a vast pink-orange sunrise sky. "
    "Goreme valley panorama, soft volumetric morning mist rolling through the valleys, golden sunrise backlighting with warm rim light on the child. "
    "Low-angle hero shot: child 25% foreground, sweeping fairy chimney landscape and balloons 75%. "
    "Warm earth palette: rose gold sunrise, sandy ochre rocks, lavender sky, balloon jewel tones. UNESCO site."
)

CAPPADOCIA_PAGE_PROMPT = (
    "An {child_age}-year-old {child_gender} named {child_name} "
    "with {hair_description}, wearing {clothing_description}. "
    "{scene_description}. "
    "Elements: [Fairy chimneys: cone-shaped volcanic tuff / Hot air balloons: colorful, sunrise / "
    "Underground city: multi-level caves, tunnels / Rock churches: ancient frescoes / "
    "Valleys: Goreme, Rose Valley / Village: stone houses in rocks]. "
    "Earth colors: ochre, beige, rose pink. Magical, adventurous."
)

# ============================================================================
# OUTFIT DEFINITIONS (update_all_outfits.py standardı)
# ============================================================================

OUTFIT_GIRL = (
    "warm coral-orange puffer vest over cream white long-sleeve henley shirt, "
    "light khaki cotton pants, tan brown suede hiking boots with orange laces, "
    "small beige canvas backpack on back. "
    "EXACTLY the same outfit on every page — same coral vest, same cream shirt, same khaki pants."
)

OUTFIT_BOY = (
    "forest green quilted vest over light gray long-sleeve t-shirt, "
    "tan khaki cargo pants with zippered pockets, dark brown leather hiking boots, "
    "olive green canvas backpack on back. "
    "EXACTLY the same outfit on every page — same green vest, same gray shirt, same khaki pants."
)

# ============================================================================
# STORY BLUEPRINT (Doğa Mucizesi + Balon + Yeraltı)
# ============================================================================

CAPPADOCIA_STORY_PROMPT_TR = """
# KAPADOKYA MACERASI

## YAPI: {child_name} REHBER İLE KAPADOKYA GEZİSİNDE. Çocuk maceraya atılır, sır/bulmaca çözer, zorluklarla karşılaşır ve onları aşar.

**BAŞLIK:** Kitap adı sadece "[Çocuk adı]'ın Kapadokya Macerası" olmalı. Alt başlık (Doğa Mucizesi Keşfi vb.) EKLEME.

**PERİ BACALARI (gerçekçi):** Volkanik tüf — Erciyes, Hasan Dağı, Güllüdağ'dan lav ve kül. Milyonlarca yıl rüzgar ve yağmurun aşındırmasıyla koni biçimli şekiller, şapka taşları. Ürgüp, Göreme vadisi. Büyülü varlık/peri YOK; doğa ve tarih var.

**KURGU:** Rehber (insan, yetişkin — yüzü detaylı tarif etme) çocuğu Kapadokya'nın kültürel ve doğal yerlerinde gezdiriyor. Çocuk AKTİF: yol bulma, küçük bulmaca/ipucu çözme, karanlık veya dar yerde cesaret toplama, yorulup devam etme. Zorluklar gerçekçi. Her zorluğu AŞAR. Sihir, peri, ışıklı varlık YOK.

---

### Bölüm 1 — Varış, rehber, peri bacaları (Sayfa 1-4)
- {child_name} Kapadokya'ya geliyor. Tur rehberi ile tanışıyor. Göreme vadisi, peri bacaları.
- Rehber peri bacalarının nasıl oluştuğunu anlatıyor: volkanik tüf (Erciyes, Hasan Dağı), rüzgar ve yağmurla aşınma. Çocuk merakla dinliyor.
- İlk zorluk: Peri bacaları arasında yol ayrımında hangi yöne gideceğini bulması gerekiyor (rehber ipucu veriyor). Çocuk çözüyor, yol buluyor. İlk başarı.

### Bölüm 2 — Yeraltı şehri (Sayfa 5-9)
- Yeraltı şehrine giriş. Dar tüneller, katlar. Rehber tarihi anlatıyor (binlerce yıl önce insanlar burada yaşamış).
- Zorluk: Karanlık bir geçitte rehber "çıkışı bul" diye küçük görev veriyor (taşlardaki işaretler). {child_name} ipuçlarını birleştiriyor, çıkışı buluyor. Cesaret ve çözüm.
- Odalar: mutfak, havalandırma. Tarih bilinci.

### Bölüm 3 — Kaya kiliseler, freskler (Sayfa 10-13)
- Göreme Açık Hava Müzesi. Kayaya oyulmuş kiliseler, eski resimler. Rehber kısaca anlatıyor.
- Küçük bulmaca: Rehber duvardaki bir sembolü bulmasını istiyor; çocuk arar, bulur. Keşif sevinci.
- Yoruluyor ama devam ediyor. "Biraz daha!" diye kendini motive ediyor.

### Bölüm 4 — Balon turu (Sayfa 14-17)
- Sabah erken sıcak hava balonu turu. Rehber ve grup ile. Yükseliş, gökyüzünden peri bacaları ve vadiler.
- Hafif zorluk: İlk başta yükseklik heyecanı; nefes alıp sakinleşiyor, manzaraya odaklanıyor. Üstesinden gelme.
- İniş, güvenli. "Yaptım!" gururu.

### Bölüm 5 — Pembe vadi, son zorluk (Sayfa 18-20)
- Pembe Vadi'de yürüyüş. Gün batımına doğru kayalar pembe, turuncu. Rehber doğanın renklerini anlatıyor.
- Son meydan okuma: Uzun yürüyüşte "bitene kadar devam" — ayakları ağrıyor ama rehber teşvik ediyor, {child_name} bitiriyor. Sebat.
- Tepeden Kapadokya manzarası. "Her zorluğu aştım." tatmini.

### Bölüm 6 — Kapanış (Sayfa 21-22)
- Gezinin sonu. Rehber tebrik ediyor: "Zorlukları aştın, sırları çözdün."
- {child_name} eve dönüşe hazırlanıyor. Kısa ve duygusal kapanış.

---

## KURALLAR
- Sihir, peri, ışıklı varlık YOK. Rehber = gerçek insan (yüz detayı verme).
- Her bölümde en az bir küçük zorluk/görev ve çocuğun onu aşması.
- Yerler gerçek: Göreme, peri bacaları, yeraltı şehri, kaya kiliseler, Pembe vadi, balon.
- Korku/şiddet yok; gerilim hafif ve hep aşılır.
- Kitap adı SADECE "[Çocuk adı]'ın Kapadokya Macerası". Alt başlık ekleme.

Hikayeyi TAM OLARAK {page_count} sayfa yaz. Her sayfa 2-4 cümle, akıcı ve macera dolu.
"""

# ============================================================================
# CULTURAL ELEMENTS
# ============================================================================

CAPPADOCIA_CULTURAL_ELEMENTS = {
    "location": "Cappadocia (Nevsehir, Urgup, Goreme), Central Anatolia, Turkey",
    "unesco": "Goreme National Park — UNESCO World Heritage Site (1985)",
    "geological_wonder": "Fairy chimney formations (60 million years of volcanic activity + erosion)",
    "key_sites": [
        "Fairy chimneys (peri bacalari) — cone-shaped volcanic tuff",
        "Hot air balloon rides (world-famous sunrise flights)",
        "Derinkuyu Underground City (8-10 levels deep)",
        "Goreme Open Air Museum (rock-carved churches, 1000-year frescoes)",
        "Rose Valley (pink-hued rocks at sunset)",
    ],
    "atmosphere": "Magical, adventurous, geological wonder",
    "color_palette": "ochre, beige, rose pink, golden sunrise, earth tones",
    "values": ["Nature appreciation", "Adventure", "History", "Geological wonder"],
}

# ============================================================================
# CUSTOM INPUTS — Kurguyu bozabilecek seçenekler kaldırıldı (sabit senaryo)
# ============================================================================

CAPPADOCIA_CUSTOM_INPUTS: list[dict] = []

# ============================================================================
# DATABASE UPDATE FUNCTION
# ============================================================================


async def update_cappadocia_scenario():
    """Kapadokya senaryosunu günceller."""
    from app.core.database import async_session_factory

    async with async_session_factory() as session:
        result = await session.execute(
            select(Scenario).where(
                (Scenario.theme_key == "cappadocia")
                | (Scenario.theme_key == "cappadocia_fairy_chimneys")
                | (Scenario.name.ilike("%Kapadokya%"))
                | (Scenario.name.ilike("%Cappadocia%"))
            )
        )
        scenario = result.scalar_one_or_none()

        if not scenario:
            print("Kapadokya scenario not found — skipping")
            return

        scenario.name = "Kapadokya Macerası"
        scenario.description = (
            "Rehber ile Kapadokya gezisi. Çocuk maceraya atılır, sır ve bulmaca çözer, "
            "peri bacaları, yeraltı şehri, kaya kiliseler ve balon turunda zorluklarla "
            "karşılaşır ve hepsini aşar. Kitap adı: [Çocuk adı]'ın Kapadokya Macerası."
        )
        scenario.cover_prompt_template = CAPPADOCIA_COVER_PROMPT
        scenario.page_prompt_template = CAPPADOCIA_PAGE_PROMPT
        scenario.story_prompt_tr = CAPPADOCIA_STORY_PROMPT_TR
        scenario.outfit_girl = OUTFIT_GIRL
        scenario.outfit_boy = OUTFIT_BOY
        scenario.cultural_elements = CAPPADOCIA_CULTURAL_ELEMENTS
        scenario.custom_inputs_schema = CAPPADOCIA_CUSTOM_INPUTS
        scenario.marketing_badge = "YENİ! Balon Macerası"
        scenario.age_range = "6-10"
        scenario.tagline = "Kapadokya'nın büyüsünü keşfet!"
        scenario.is_active = True

        await session.commit()
        print(f"Kapadokya scenario updated: {scenario.id}")


if __name__ == "__main__":
    asyncio.run(update_cappadocia_scenario())

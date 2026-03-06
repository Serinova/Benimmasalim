"""
Kudüs Macerası — Rehberli gezi, macera, puzzle/zorluk (Efes/Galata modeli)
===========================================================================
- Kitap adı: [Çocuk adı]'ın Kudüs Macerası (alt başlık yok)
- Rehber ile gezi; çocuk maceraya atılır, sır/bulmaca çözer, zorluklarla karşılaşır ve aşar
- Yerler: Eski Şehir surları, taş sokaklar, Kubbetüs-Sahra (mimari), çarşı, dört mahalle, sur panoraması
- Kıyafet: seyahatin ruhuna özgü — kız: mütevazi elbise + tesettür; erkek: beyaz kurta + takke (update_all_outfits)
- Kültürel hassasiyet: 3 dine eşit saygı, dini ritüel/ibadet sahnesi YOK, mimari/çarşı/arkeoloji odak
- Kurguyu bozabilecek kullanıcı seçenekleri yok (custom_inputs boş)
"""

import asyncio
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sqlalchemy import select, or_
from app.core.database import async_session_factory
from app.models.scenario import Scenario

# ============================================================================
# MODULAR PROMPT COMPONENTS
# ============================================================================

KUDUS_COVER_PROMPT = (
    "An {child_age}-year-old {child_gender} named {child_name} "
    "with {hair_description}, wearing {clothing_description}. "
    "{scene_description}. "
    "Ancient Jerusalem Old City walls built of warm honey-gold limestone blocks in the foreground, the iconic golden Dome of the Rock gleaming in the distance with intricate blue Iznik tile patterns. "
    "Narrow cobblestone alleyways with weathered stone arches, olive trees, and ancient worn steps. "
    "Warm late-afternoon golden light bathing the Jerusalem stone in amber warmth, soft volumetric haze rising from the ancient streets, gentle rim lighting on the child. "
    "Slightly low-angle shot: child 25% foreground, layers of historic architecture 75%. "
    "Holy city palette: warm honey gold limestone, gleaming dome gold, soft blue sky, olive green accents. Peaceful, UNESCO site."
)

KUDUS_PAGE_PROMPT = (
    "An {child_age}-year-old {child_gender} named {child_name} "
    "with {hair_description}, wearing {clothing_description}. "
    "{scene_description}. "
    "Elements: [Walls: Ottoman golden limestone / Dome of Rock: golden dome, blue tiles / "
    "Souq: spices, copper lanterns, crafts / Alleys: narrow cobblestone, arched / "
    "Four Quarters: diverse architecture / Jerusalem stone: warm golden glow]. "
    "Golden light, peaceful, historic. NO religious ritual, architecture and culture only."
)

# ============================================================================
# OUTFIT — Seyahatin ruhuna özgü (Kudüs ziyareti; kız tesettür, erkek takke)
# ============================================================================

OUTFIT_GIRL = (
    "soft ivory white cotton long-sleeve modest dress reaching ankles, "
    "PROPERLY WRAPPED white hijab: fabric wraps FULLY around head and neck — NO hair visible, NO neck visible, "
    "fabric drapes softly over shoulders and chest (modern proper hijab wrap, NOT a loose veil, NOT fabric on top of head only), "
    "comfortable light beige flat sandals, small white cotton drawstring bag. "
    "EXACTLY the same outfit on every page — same ivory dress, same properly wrapped white hijab, same beige sandals."
)

OUTFIT_BOY = (
    "clean white cotton knee-length kurta tunic shirt, "
    "white knit taqiyah prayer cap on head, light beige loose-fitting cotton pants, "
    "comfortable tan leather sandals, small white cotton drawstring bag. "
    "EXACTLY the same outfit on every page — same white kurta, same white taqiyah, same beige pants."
)

# ============================================================================
# STORY BLUEPRINT — Rehber ile gezi, puzzle, zorlukları aşma (kültürel hassasiyet)
# ============================================================================

KUDUS_STORY_PROMPT_TR = """
# KUDÜS MACERASI

## YAPI: {child_name} REHBER İLE KUDÜS ESKİ ŞEHİR GEZİSİNDE. Çocuk maceraya atılır, sır/bulmaca çözer, zorluklarla karşılaşır ve onları aşar.

**BAŞLIK:** Kitap adı sadece "[Çocuk adı]'ın Kudüs Macerası" olmalı. Alt başlık (Eski Şehir Macerası vb.) EKLEME.

**KURGU:** Rehber (tur rehberi, yetişkin insan — yüzü detaylı tarif etme) çocuğu Eski Şehir'de gezdiriyor. Çocuk AKTİF: yol bulma, rehberin verdiği küçük görevler (haritada Şam Kapısı'nı bul, çarşıda belirli bir baharatı bul, dört mahalleden birinin yolunu bul), yorulup devam etme. Zorluklar gerçekçi. Her zorluğu AŞAR. Sihir, konuşan hayvan (Bilge Kedi vb.) YOK.

**KÜLTÜREL HASSASİYET:** 3 dine EŞİT saygı. Dini ritüel/ibadet sahnesi YOK. Peygamber veya dini figür görseli YOK. Odak: MİMARİ (surlar, kubbe, taş işçiliği), ÇARŞI (baharat, zanaat), ARKEOLOJİ, HOŞGÖRÜ. Yapılar "tarihî anıt ve mimari şaheser" olarak anlatılır. Siyasi mesaj YOK.

**YERLER (gerçek):** Kudüs Eski Şehir, UNESCO Dünya Mirası. Şam Kapısı, Osmanlı surları (16. yüzyıl). Altın rengi Kudüs taşı, dar taş sokaklar, kemerli geçitler. Kubbetüs-Sahra (dışarıdan mimari — kubbe, çiniler). Kapalı çarşı: baharat, bakır, el sanatları. Dört mahalle: farklı mimari ve atmosfer. Surların üstü: panoramik manzara.

---

### Bölüm 1 — Varış, Şam Kapısı (Sayfa 1-4)
- {child_name} Kudüs Eski Şehir'e geliyor. Tur rehberi ile tanışıyor. Şam Kapısı, dev taş surlar.
- Rehber kısaca anlatıyor: "Bu surların ardında 5000 yıllık tarih var." Çocuk merakla dinliyor.
- İlk zorluk: Haritada Şam Kapısı'nı bul — rehber ipucu veriyor, çocuk kapıyı gösteriyor. İlk başarı.
- Altın rengi Kudüs taşı güneşte parlıyor. "Ne kadar güzel!" Hayranlık.

### Bölüm 2 — Taş sokaklar, Kubbetüs-Sahra manzarası (Sayfa 5-8)
- Dar sokaklarda yürüyüş. Kemerli geçitler, taş binalar. Rehber: "İleride altın kubbe görünecek — tarihî bir yapı."
- Yüksek bir noktadan Kubbetüs-Sahra (dışarıdan) görünüyor — altın kubbe, mavi çiniler. Mimari olarak anlat; ibadet/ritüel YOK.
- Küçük görev: Rehber "Bu sokakta kaç kemer var, sayalım" diyor. Çocuk sayıyor. Keşif sevinci.

### Bölüm 3 — Çarşı: baharat ve zanaat (Sayfa 9-12)
- Kapalı çarıya giriş. Baharat tezgahları, bakır fenerler, el işi dükkanları. Rehber kokuları ve renkleri anlatıyor.
- Zorluk: Rehber "Zerdeçalı bul — hangi tezgah?" diyor. Çocuk dolaşıyor, buluyor. Başarı.
- Bir mozaik veya seramik atölyesi (isteğe bağlı) — "Taşları birleştiriyorlar!" Kültürel zenginlik.

### Bölüm 4 — Dört mahalle (Sayfa 13-16)
- Rehber: "Eski Şehir dört mahalleden oluşur, her biri kendine özgü." Sokaklar arasında geziyorlar.
- Küçük bulmaca: Rehber "Şimdi surlara doğru gideceğiz — hangi yön?" Haritaya bakıp çocuk yönü buluyor. Sebat.
- Farklı mimari detaylar, aynı altın taş. "Farklılıklar zenginliktir!" Mesaj (din adı vermeden).

### Bölüm 5 — Surlar, panoramik manzara (Sayfa 17-19)
- Surların üstüne çıkılıyor (veya sur yolunda). Eski Şehir ayakların altında — kubbeler, taş çatılar. Rehber tarihi anlatıyor.
- Yoruluyor; rehber "Biraz dinlenelim, manzarayı sevelim" diyor. Çocuk nefes alıyor, devam ediyor. Cesaret.
- "Bu şehir insanlığın ortak hazinesi." UNESCO perspektifi.

### Bölüm 6 — Kapanış (Sayfa 20-22)
- Şam Kapısı'na doğru dönüş. Rehber tebrik ediyor: "Zorlukları aştın, Kudüs'ü keşfettin."
- {child_name} eve dönüşe hazırlanıyor. Kısa ve duygusal kapanış. Hoşgörü ve barış vurgusu (soyut, siyasi olmadan).

---

## KURALLAR
- Rehber = gerçek insan (yüz detayı verme). Sihir, Bilge Kedi veya konuşan hayvan YOK.
- Her bölümde en az bir küçük zorluk/görev ve çocuğun onu aşması.
- Yerler gerçek: Şam Kapısı, surlar, taş sokaklar, Kubbetüs-Sahra (sadece dış mimari), çarşı, dört mahalle, sur panoraması.
- Dini ritüel/ibadet sahnesi YOK. Peygamber/dini figür görseli YOK. 3 dine eşit saygı.
- Kitap adı SADECE "[Çocuk adı]'ın Kudüs Macerası". Alt başlık ekleme.

Hikayeyi TAM OLARAK {page_count} sayfa yaz. Her sayfa 2-4 cümle, akıcı ve macera dolu.
"""

# ============================================================================
# CULTURAL ELEMENTS
# ============================================================================

KUDUS_CULTURAL_ELEMENTS = {
    "location": "Old City of Jerusalem, UNESCO World Heritage Site",
    "historic_significance": "5000+ years, multicultural heritage",
    "architecture": [
        "Ottoman city walls (16th century), Şam Kapısı",
        "Golden Dome of the Rock (exterior architecture only)",
        "Jerusalem stone (golden limestone), narrow alleys, arched passageways",
        "Four quarters with distinct architecture",
    ],
    "cultural_elements": [
        "Covered souq: spices, crafts, copper lanterns",
        "Artisan workshops: mosaic, ceramics",
        "Archaeological and historic layers",
    ],
    "sensitivity_rules": [
        "NO religious ritual or worship scenes",
        "NO prophet or religious figure depiction",
        "Equal respect for all three faiths; no political message",
        "Focus on architecture, souq, and cultural heritage",
    ],
    "atmosphere": "Peaceful, multicultural, golden light, historic",
    "values": ["Tolerance", "Peace", "Cultural diversity", "Respect"],
}

# ============================================================================
# CUSTOM INPUTS — Kurguyu bozmayacak şekilde boş
# ============================================================================

KUDUS_CUSTOM_INPUTS: list[dict] = []


# ============================================================================
# DATABASE UPDATE
# ============================================================================


async def update_jerusalem_scenario():
    """Kudüs senaryosunu günceller. Çift senaryo varsa birini siler."""
    async with async_session_factory() as db:
        result = await db.execute(
            select(Scenario).where(
                or_(
                    Scenario.theme_key == "kudus",
                    Scenario.theme_key == "jerusalem_old_city",
                    Scenario.name.ilike("%Kudüs%"),
                    Scenario.name.ilike("%Kudus%"),
                    Scenario.name.ilike("%Jerusalem%"),
                )
            )
        )
        scenarios = result.scalars().all()

        if len(scenarios) > 1:
            keep = scenarios[0]
            for s in scenarios[1:]:
                await db.delete(s)
                print(f"Deleted duplicate Kudüs scenario: {s.name} ({s.id})")
            scenario = keep
        elif len(scenarios) == 1:
            scenario = scenarios[0]
        else:
            scenario = Scenario(name="Kudüs Macerası", is_active=True)
            scenario.theme_key = "kudus"
            db.add(scenario)

        scenario.name = "Kudüs Macerası"
        scenario.description = (
            "Rehber ile Kudüs Eski Şehir gezisi. Surlar, taş sokaklar, çarşı, "
            "dört mahalle, panoramik manzara. Çocuk zorlukları aşar, bulmaca çözer. "
            "Kitap adı: [Çocuk adı]'ın Kudüs Macerası."
        )
        scenario.theme_key = "kudus"
        scenario.cover_prompt_template = KUDUS_COVER_PROMPT
        scenario.page_prompt_template = KUDUS_PAGE_PROMPT
        scenario.story_prompt_tr = KUDUS_STORY_PROMPT_TR
        scenario.outfit_girl = OUTFIT_GIRL
        scenario.outfit_boy = OUTFIT_BOY
        scenario.cultural_elements = KUDUS_CULTURAL_ELEMENTS
        scenario.custom_inputs_schema = KUDUS_CUSTOM_INPUTS
        scenario.marketing_badge = "Kültürel Keşif"
        scenario.age_range = "7-10"
        scenario.tagline = "5000 yıllık kültürlerin mozaiği"
        scenario.is_active = True

        await db.commit()
        print(f"Kudüs scenario updated: {scenario.id}")


if __name__ == "__main__":
    asyncio.run(update_jerusalem_scenario())

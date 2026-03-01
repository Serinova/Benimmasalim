"""
TÜM SENARYOLARIN KIYAFETLERİNİ GÜNCELLE — NET, SPESİFİK, TUTARLI
================================================================

Sorun: Eski kıyafet tarifleri belirsiz ("white or pastel t-shirt", "graphic t-shirt")
AI modeli belirsiz tariflerden her sayfada farklı kıyafet üretiyordu.

Çözüm: Her senaryo için sabit renkler ve net materyal tarifleri.
Her sayfada birebir aynı kıyafet çıkması için "EXACTLY the same outfit on every page" vurgusu.

Çalıştırma:
    cd backend
    python -m scripts.update_all_outfits
"""

import asyncio
from sqlalchemy import select, update
from app.core.database import async_session_factory
from app.models.scenario import Scenario

# =============================================================================
# NET, SPESİFİK KIYAFETLER — HER SENARYO İÇİN
# =============================================================================
# KURAL: Renk, materyal, desen, aksesuar eksiksiz belirtilmeli.
# "or" veya "optional" kelimesi yasak — AI belirsizlikten kötü sonuç üretir.

OUTFITS = {
    # ── 1. GALATA KULESİ ──────────────────────────────────────────────────
    "Galata": {
        "outfit_girl": (
            "bright cherry-red cotton hoodie with small white heart logo on chest, "
            "dark navy blue denim jeans, white canvas sneakers with red laces, "
            "small light gray backpack on back. "
            "EXACTLY the same outfit on every page — same red hoodie, same navy jeans, same white sneakers."
        ),
        "outfit_boy": (
            "royal blue zip-up cotton jacket over white crew-neck t-shirt, "
            "dark gray cargo pants with side pockets, black and white striped sneakers, "
            "small navy blue backpack on back. "
            "EXACTLY the same outfit on every page — same blue jacket, same gray pants, same striped sneakers."
        ),
    },

    # ── 2. KAPADOKYA ─────────────────────────────────────────────────────
    "Kapadokya": {
        "outfit_girl": (
            "warm coral-orange puffer vest over cream white long-sleeve henley shirt, "
            "light khaki cotton pants, tan brown suede hiking boots with orange laces, "
            "small beige canvas backpack on back. "
            "EXACTLY the same outfit on every page — same coral vest, same cream shirt, same khaki pants."
        ),
        "outfit_boy": (
            "forest green quilted vest over light gray long-sleeve t-shirt, "
            "tan khaki cargo pants with zippered pockets, dark brown leather hiking boots, "
            "olive green canvas backpack on back. "
            "EXACTLY the same outfit on every page — same green vest, same gray shirt, same khaki pants."
        ),
    },

    # ── 3. GÖBEKLİTEPE ──────────────────────────────────────────────────
    "Göbeklitepe": {
        "outfit_girl": (
            "sand-yellow cotton t-shirt with small compass emblem on chest, "
            "light olive green cotton shorts reaching knees, tan brown leather sandals, "
            "wide-brim straw sun hat with brown ribbon, small woven crossbody bag. "
            "EXACTLY the same outfit on every page — same yellow shirt, same olive shorts, same straw hat."
        ),
        "outfit_boy": (
            "burnt orange cotton polo shirt, "
            "stone beige cargo shorts with button-flap pockets, dark brown leather sandals, "
            "khaki bucket hat, small tan canvas satchel bag across body. "
            "EXACTLY the same outfit on every page — same orange polo, same beige shorts, same bucket hat."
        ),
    },

    # ── 4. EFES ANTİK KENTİ ─────────────────────────────────────────────
    "Efes": {
        "outfit_girl": (
            "soft lavender purple cotton t-shirt with small sun emblem, "
            "light blue denim shorts reaching knees, white canvas sneakers, "
            "wide-brim white sun hat with lavender ribbon, small white crossbody bag. "
            "EXACTLY the same outfit on every page — same lavender shirt, same blue shorts, same white hat."
        ),
        "outfit_boy": (
            "sky blue cotton t-shirt with small Greek column emblem, "
            "sand-colored cotton chino shorts, white canvas sneakers with blue stripes, "
            "white baseball cap, small beige canvas backpack on back. "
            "EXACTLY the same outfit on every page — same blue shirt, same sand shorts, same white cap."
        ),
    },

    # ── 5. ÇATALHÖYÜK ────────────────────────────────────────────────────
    "Çatalhöyük": {
        "outfit_girl": (
            "terracotta rust-colored cotton t-shirt with small geometric pattern on chest, "
            "dark brown cotton cargo shorts, tan leather ankle boots, "
            "light brown canvas bucket hat, small leather crossbody satchel. "
            "EXACTLY the same outfit on every page — same terracotta shirt, same brown shorts, same leather boots."
        ),
        "outfit_boy": (
            "ochre yellow cotton t-shirt with small arrowhead emblem, "
            "dark olive green cotton shorts, tan leather ankle boots, "
            "brown canvas explorer hat, small leather hip pouch on belt. "
            "EXACTLY the same outfit on every page — same ochre shirt, same olive shorts, same leather boots."
        ),
    },

    # ── 6. SÜMELA MANASTIRI ──────────────────────────────────────────────
    "Sümela": {
        "outfit_girl": (
            "dark emerald green waterproof rain jacket with hood, "
            "over cream white long-sleeve thermal shirt, dark navy blue hiking leggings, "
            "dark brown waterproof hiking boots with green laces, small olive green backpack. "
            "EXACTLY the same outfit on every page — same green jacket, same navy leggings, same brown boots."
        ),
        "outfit_boy": (
            "dark teal blue waterproof rain jacket with hood, "
            "over light gray long-sleeve thermal shirt, dark charcoal hiking pants, "
            "dark brown waterproof hiking boots with teal laces, small dark gray backpack. "
            "EXACTLY the same outfit on every page — same teal jacket, same charcoal pants, same brown boots."
        ),
    },

    # ── 7. SULTANAHMET CAMİİ ─────────────────────────────────────────────
    "Sultanahmet": {
        "outfit_girl": (
            "soft white cotton long-sleeve modest dress reaching ankles with delicate blue floral embroidery on hem, "
            "white cotton hijab headscarf covering hair neatly, comfortable cream flat shoes, "
            "small white shoulder bag with blue strap. "
            "EXACTLY the same outfit on every page — same white dress with blue embroidery, same white hijab."
        ),
        "outfit_boy": (
            "clean white cotton long-sleeve shirt, light beige cotton loose-fitting pants, "
            "white knit taqiyah prayer cap on head, comfortable tan leather sandals, "
            "small beige canvas shoulder bag. "
            "EXACTLY the same outfit on every page — same white shirt, same beige pants, same white taqiyah cap."
        ),
    },

    # ── 8. KUDÜS ─────────────────────────────────────────────────────────
    "Kudüs": {
        "outfit_girl": (
            "soft ivory white cotton long-sleeve modest dress reaching ankles, "
            "white cotton hijab headscarf covering hair completely with neat edges, "
            "comfortable light beige flat sandals, small white cotton drawstring bag. "
            "EXACTLY the same outfit on every page — same ivory dress, same white hijab, same beige sandals."
        ),
        "outfit_boy": (
            "clean white cotton knee-length kurta tunic shirt, "
            "white knit taqiyah prayer cap on head, light beige loose-fitting cotton pants, "
            "comfortable tan leather sandals, small white cotton drawstring bag. "
            "EXACTLY the same outfit on every page — same white kurta, same white taqiyah, same beige pants."
        ),
    },

    # ── 9. ABU SİMBEL ────────────────────────────────────────────────────
    "Abu Simbel": {
        "outfit_girl": (
            "pure white linen sleeveless dress reaching knees with gold ankh pendant necklace, "
            "tan leather gladiator sandals with gold buckle, "
            "small woven papyrus basket bag on arm. "
            "EXACTLY the same outfit on every page — same white dress, same gold ankh necklace, same tan sandals."
        ),
        "outfit_boy": (
            "pure white linen short-sleeve tunic reaching knees with thin gold rope belt, "
            "tan leather gladiator sandals with gold buckle, "
            "small rolled papyrus scroll tucked in belt. "
            "EXACTLY the same outfit on every page — same white tunic, same gold belt, same tan sandals."
        ),
    },

    # ── 10. TAC MAHAL ────────────────────────────────────────────────────
    "Tac Mahal": {
        "outfit_girl": (
            "soft rose pink silk kurta top with delicate silver thread embroidery on neckline, "
            "matching rose pink loose shalwar pants, gold-strapped flat sandals, "
            "small pink jasmine flower garland on wrist. "
            "EXACTLY the same outfit on every page — same pink kurta with silver embroidery, same pink shalwar."
        ),
        "outfit_boy": (
            "ivory white cotton kurta shirt with gold thread embroidery along collar, "
            "light cream loose pajama pants, tan leather mojri shoes with curved toe, "
            "small white handkerchief in kurta pocket. "
            "EXACTLY the same outfit on every page — same ivory kurta with gold collar, same cream pants."
        ),
    },

    # ── 11. YEREBATAN SARNICI ────────────────────────────────────────────
    "Yerebatan": {
        "outfit_girl": (
            "deep teal cotton zip-up explorer jacket with reflective silver stripes on sleeves, "
            "dark navy blue waterproof pants, black rubber rain boots with teal trim, "
            "small yellow LED flashlight headlamp on forehead, dark gray utility backpack. "
            "EXACTLY the same outfit on every page — same teal jacket with silver stripes, same navy pants, same black boots."
        ),
        "outfit_boy": (
            "dark navy blue cotton zip-up explorer jacket with reflective orange stripes on sleeves, "
            "dark charcoal waterproof pants, black rubber rain boots with orange trim, "
            "small yellow LED flashlight headlamp on forehead, dark gray utility backpack. "
            "EXACTLY the same outfit on every page — same navy jacket with orange stripes, same charcoal pants, same black boots."
        ),
    },

    # ── 12. AMAZON ORMANLARI ─────────────────────────────────────────────
    "Amazon": {
        "outfit_girl": (
            "khaki canvas explorer vest with four front pockets over light sage green breathable cotton shirt, "
            "dark olive cargo shorts with zippered pockets reaching knees, sturdy brown leather hiking boots, "
            "small silver binoculars around neck, wide-brim khaki fabric hat with mosquito net rolled up. "
            "EXACTLY the same outfit on every page — same khaki vest, same green shirt, same olive shorts, same brown boots."
        ),
        "outfit_boy": (
            "olive green cotton explorer shirt with rolled-up sleeves and chest pocket, "
            "dark khaki cargo pants with zippered side pockets, sturdy dark brown leather hiking boots, "
            "tan canvas backpack with water bottle in side pocket, wide-brim brown explorer hat with chin strap. "
            "EXACTLY the same outfit on every page — same olive shirt, same khaki pants, same brown boots, same explorer hat."
        ),
    },

    # ── 13. UZAY MACERASI ────────────────────────────────────────────────
    "Uzay": {
        "outfit_girl": (
            "bright white NASA-style child space suit with pink and blue mission patches on shoulders, "
            "silver metallic utility belt with small gadget pouches, white space boots with pink soles, "
            "clear bubble space helmet with pink frame (helmet can be removed in indoor scenes), "
            "small silver star-shaped badge on chest. "
            "EXACTLY the same outfit on every page — same white space suit with pink patches, same silver belt, same white boots."
        ),
        "outfit_boy": (
            "bright white NASA-style child space suit with blue and orange mission patches on shoulders, "
            "silver metallic utility belt with small gadget pouches, white space boots with blue soles, "
            "clear bubble space helmet with blue frame (helmet can be removed in indoor scenes), "
            "small gold rocket-shaped badge on chest. "
            "EXACTLY the same outfit on every page — same white space suit with blue patches, same silver belt, same white boots."
        ),
    },

    # ── 14. DİNOZOR ZAMANI ───────────────────────────────────────────────
    "Dinozor": {
        "outfit_girl": (
            "silver-gray nylon explorer jumpsuit with glowing blue LED trim lines along arms and legs, "
            "protective black knee pads with small holographic time display, "
            "dark gray high-tech hiking boots with blue LED lights on sides, "
            "transparent time-traveler goggles pushed up on forehead with blue frames, "
            "black utility belt with glowing blue time crystal remote control. "
            "EXACTLY the same outfit on every page — same silver jumpsuit with blue trim, same goggles, same gray boots."
        ),
        "outfit_boy": (
            "dark navy blue nylon time-traveler jacket with metallic silver shoulder pads, "
            "dark gray cargo pants with zippered tech pockets and black knee guards, "
            "sturdy dark brown ankle-high boots with orange grip soles, "
            "digital compass watch on left wrist with blue holographic display, "
            "dark gray canvas backpack with visible glowing blue time crystal inside. "
            "EXACTLY the same outfit on every page — same navy jacket with silver shoulders, same gray pants, same brown boots."
        ),
    },

    # ── 15. OKYANUS MACERASI ─────────────────────────────────────────────
    "Okyanus": {
        "outfit_girl": (
            "teal and coral pink neoprene diving wetsuit with white trim stripes along arms, "
            "clear full-face diving mask with coral pink frame pushed up on forehead, "
            "compact metallic silver oxygen tank on back, bright yellow diving fins, "
            "waterproof wrist computer on left arm showing depth gauge display. "
            "EXACTLY the same outfit on every page — same teal-pink wetsuit, same coral mask, same yellow fins."
        ),
        "outfit_boy": (
            "navy blue and bright orange neoprene diving wetsuit with reflective white stripes, "
            "clear full-face diving mask with blue frame pushed up on forehead, "
            "compact metallic silver oxygen tank on back, bright orange diving fins, "
            "waterproof yellow flashlight clipped to belt on right hip. "
            "EXACTLY the same outfit on every page — same navy-orange wetsuit, same blue mask, same orange fins."
        ),
    },

    # ── 16. UMRE ─────────────────────────────────────────────────────────
    "Umre": {
        "outfit_girl": (
            "pure white cotton modest long-sleeve dress reaching ankles with no patterns or decorations, "
            "white cotton hijab headscarf covering hair completely with simple neat edges, "
            "comfortable beige leather flat sandals, small white cotton drawstring backpack. "
            "Simple and clean appearance inspired by ihram purity, no jewelry. "
            "EXACTLY the same outfit on every page — same pure white dress, same white hijab, same beige sandals."
        ),
        "outfit_boy": (
            "pure white cotton knee-length kurta tunic with no patterns or decorations, "
            "white knit taqiyah prayer cap on head, light beige loose-fitting cotton pants, "
            "comfortable tan leather sandals, small white cotton drawstring backpack. "
            "Simple and clean appearance inspired by ihram purity. "
            "EXACTLY the same outfit on every page — same white kurta, same white taqiyah, same beige pants."
        ),
    },
}


async def update_all_outfits():
    """Tüm senaryolardaki kıyafet tanımlarını net ve spesifik hale günceller."""

    print("\n" + "=" * 70)
    print("👕 TÜM SENARYO KIYAFETLERİNİ GÜNCELLEME")
    print("=" * 70)

    async with async_session_factory() as db:
        # Tüm senaryoları al
        result = await db.execute(select(Scenario))
        scenarios = list(result.scalars().all())

        print(f"\n📊 Toplam {len(scenarios)} senaryo bulundu.\n")

        updated = 0
        skipped = 0

        for scenario in scenarios:
            # Hangi kıyafet seti bu senaryoyla eşleşiyor?
            matched_key = None
            for key in OUTFITS:
                if key.lower() in (scenario.name or "").lower() or key.lower() in (scenario.theme_key or "").lower():
                    matched_key = key
                    break

            if not matched_key:
                print(f"  ⚠️  Eşleşme yok: {scenario.name} (theme: {scenario.theme_key})")
                skipped += 1
                continue

            outfit = OUTFITS[matched_key]
            old_girl = (scenario.outfit_girl or "")[:50]
            old_boy = (scenario.outfit_boy or "")[:50]

            scenario.outfit_girl = outfit["outfit_girl"]
            scenario.outfit_boy = outfit["outfit_boy"]
            updated += 1

            print(f"  ✅ {scenario.name}")
            print(f"     Eski (girl): {old_girl}...")
            print(f"     Yeni (girl): {outfit['outfit_girl'][:60]}...")
            print(f"     Eski (boy):  {old_boy}...")
            print(f"     Yeni (boy):  {outfit['outfit_boy'][:60]}...")
            print()

        await db.commit()

        print("=" * 70)
        print(f"\n📊 SONUÇ:")
        print(f"   ✅ Güncellenen: {updated}")
        print(f"   ⚠️  Atlanılan:  {skipped}")
        print(f"\n{'=' * 70}")
        print("👕 Tüm kıyafetler artık NET, SPESİFİK ve TUTARLI!")
        print("   Her sayfada birebir aynı kıyafet çıkacak.")
        print("=" * 70 + "\n")


if __name__ == "__main__":
    asyncio.run(update_all_outfits())

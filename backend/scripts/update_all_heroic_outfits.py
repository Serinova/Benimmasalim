import asyncio
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sqlalchemy import select
from app.core.database import async_session_factory
from app.models.scenario import Scenario

# Net, spesifik, kahramansı, tematik ve maceracı kıyafetler.
# MİNİ ETEK VEYA KISA ŞORT KESİNLİKLE YASAK!
# "EXACTLY the same outfit on every page" zorunlu.

OUTFITS = {
    # ── 1. GALATA KULESİ (Şehir Gizemi) ──────────────────────────────────────────────────
    "Galata": {
        "outfit_girl": (
            "a vintage brown leather jacket over a cream turtleneck, tailored olive cargo pants, and ankle boots, "
            "with a delicate pocket watch chain and driving gloves. "
            "EXACTLY the same outfit on every page — same brown jacket, same turtleneck, same cargo pants. "
            "No outfit changes. NO skirts or shorts. Same child character, consistent face and hair across all pages."
        ),
        "outfit_boy": (
            "a vintage brown leather jacket over a dark turtleneck, tailored olive cargo pants, and ankle boots, "
            "with a newsboy cap and driving gloves. "
            "EXACTLY the same outfit on every page — same brown jacket, same turtleneck, same cargo pants. "
            "No outfit changes. NO short shorts. Same child character, consistent face and hair across all pages."
        ),
    },

    # ── 2. KAPADOKYA (Çöl Çölü/Peri Bacası Kaşifi) ─────────────────────────────────────────────────────
    "Kapadokya": {
        "outfit_girl": (
            "a striking coral-orange aviator bomber jacket over a cream thermal shirt, tailored khaki climbing trousers, "
            "sturdy tan suede hiking boots, a vintage leather crossbody satchel, and a pair of brass adventurer goggles resting on the forehead. "
            "EXACTLY the same outfit on every page — same orange jacket, same climbing trousers, same boots. "
            "No outfit changes. NO skirts or shorts. Same child character."
        ),
        "outfit_boy": (
            "a rugged forest-green aviator bomber jacket over a gray thermal shirt, tailored khaki climbing trousers, "
            "dark brown leather hiking boots, a vintage leather crossbody satchel, and a pair of brass adventurer goggles resting on the forehead. "
            "EXACTLY the same outfit on every page — same green jacket, same climbing trousers, same boots. "
            "No outfit changes. NO short shorts. Same child character."
        ),
    },

    # ── 3. GÖBEKLİTEPE (Antik Arkeolog) ──────────────────────────────────────────────────
    "Göbeklitepe": {
        "outfit_girl": (
            "a rugged sand-yellow linen safari tunic over a white tee, breathable light olive trousers, "
            "sturdy tan leather boots, a wide-brimmed classic explorer hat with a sun-faded ribbon, and a leather tool belt with a magnifying glass. "
            "EXACTLY the same outfit on every page — same yellow tunic, same olive trousers, same explorer hat. "
            "No outfit changes. NO skirts or shorts. Same child character."
        ),
        "outfit_boy": (
            "a rugged burnt-orange linen safari tunic over a dark tee, breathable khaki trousers, "
            "sturdy brown leather boots, a classic fedora explorer hat, and a leather tool belt with a magnifying glass. "
            "EXACTLY the same outfit on every page — same orange tunic, same khaki trousers, same explorer hat. "
            "No outfit changes. NO short shorts. Same child character."
        ),
    },

    # ── 4. EFES ANTİK KENTİ (Greko-Romen Arkeolog) ─────────────────────────────────────────────
    "Efes": {
        "outfit_girl": (
            "a stylish lavender utility shirt with rolled-up sleeves, tailored white linen trousers, "
            "tan leather adventuring boots, a light beige sun-helmet, and a small vintage leather journal tucked into a woven belt. "
            "EXACTLY the same outfit on every page — same lavender shirt, same white trousers, same sun-helmet. "
            "No outfit changes. NO skirts or shorts. Same child character."
        ),
        "outfit_boy": (
            "a sky-blue utility shirt with rolled-up sleeves, tailored sand-colored linen trousers, "
            "tan leather adventuring boots, a light beige sun-helmet, and a small vintage leather journal tucked into a woven belt. "
            "EXACTLY the same outfit on every page — same blue shirt, same sand trousers, same sun-helmet. "
            "No outfit changes. NO short shorts. Same child character."
        ),
    },

    # ── 5. ÇATALHÖYÜK (Neolitik Kaşif) ────────────────────────────────────────────────────
    "Çatalhöyük": {
        "outfit_girl": (
            "a striking crimson linen tunic over a long-sleeved cream shirt, tailored charcoal-grey climbing pants, "
            "rugged desert boots, a braided leather belt with small pouches, and a glowing ancient stone amulet around the neck. "
            "EXACTLY the same outfit on every page — same crimson tunic, same amulet, same climbing pants. "
            "No outfit changes. NO skirts or shorts. Same child character."
        ),
        "outfit_boy": (
            "a striking burnt-orange linen tunic over a long-sleeved dark shirt, tailored charcoal-grey climbing pants, "
            "rugged desert boots, a braided leather belt with small pouches, and a glowing ancient stone amulet around the neck. "
            "EXACTLY the same outfit on every page — same orange tunic, same amulet, same climbing pants. "
            "No outfit changes. NO short shorts. Same child character."
        ),
    },

    # ── 6. SÜMELA MANASTIRI ──────────────────────────────────────────────
    "Sümela": {
        "outfit_girl": (
            "a dark emerald green waterproof explorer jacket with a hood, "
            "over a cream white thermal shirt, dark navy blue durable hiking trousers, "
            "dark brown waterproof hiking boots with green laces, and a rugged olive green backpack. "
            "EXACTLY the same outfit on every page — same green jacket, same navy trousers, same brown boots. "
            "No outfit changes. NO skirts or shorts."
        ),
        "outfit_boy": (
            "a dark teal waterproof explorer jacket with a hood, "
            "over a light gray thermal shirt, dark charcoal durable hiking trousers, "
            "dark brown waterproof hiking boots with teal laces, and a rugged dark gray backpack. "
            "EXACTLY the same outfit on every page — same teal jacket, same charcoal trousers, same brown boots. "
            "No outfit changes. NO short shorts."
        ),
    },

    # ── 7. SULTANAHMET CAMİİ (Değişmedi, uygun) ─────────────────────────────────────────────
    "Sultanahmet": {
        "outfit_girl": (
            "soft white cotton long-sleeve modest dress reaching ankles with delicate blue floral embroidery on hem, "
            "PROPERLY WRAPPED white hijab: fabric wraps FULLY around head and neck — NO hair visible, NO neck visible, "
            "fabric drapes softly over shoulders (modern proper hijab wrap, NOT a loose veil), comfortable cream flat shoes, "
            "small white shoulder bag with blue strap. "
            "EXACTLY the same outfit on every page — same white dress, same properly wrapped white hijab."
        ),
        "outfit_boy": (
            "clean white cotton long-sleeve shirt, light beige cotton loose-fitting pants, "
            "white knit taqiyah prayer cap on head, comfortable tan leather sandals, "
            "small beige canvas shoulder bag. "
            "EXACTLY the same outfit on every page — same white shirt, same beige pants, same white taqiyah cap."
        ),
    },

    # ── 8. KUDÜS (Değişmedi, uygun) ─────────────────────────────────────────────────────────
    "Kudüs": {
        "outfit_girl": (
            "soft ivory white cotton long-sleeve modest dress reaching ankles, "
            "PROPERLY WRAPPED white hijab: fabric wraps FULLY around head and neck — NO hair visible, NO neck visible, "
            "fabric drapes softly over shoulders and chest (modern proper hijab wrap), "
            "comfortable light beige flat sandals, small white cotton drawstring bag. "
            "EXACTLY the same outfit on every page — same ivory dress, same properly wrapped white hijab, same beige sandals."
        ),
        "outfit_boy": (
            "clean white cotton knee-length kurta tunic shirt, "
            "white knit taqiyah prayer cap on head, light beige loose-fitting cotton pants, "
            "comfortable tan leather sandals, small white cotton drawstring bag. "
            "EXACTLY the same outfit on every page — same white kurta, same white taqiyah, same beige pants."
        ),
    },

    # ── 9. ABU SİMBEL (Mısır Arkeoloğu) ────────────────────────────────────────────────────
    "Abu Simbel": {
        "outfit_girl": (
            "a crisp white linen explorer tunic with gold trim, breathable beige desert trousers, "
            "durable leather gladiator-style boots, a wide-brimmed sun hat, and a glowing gold ankh pendant on a leather cord. "
            "EXACTLY the same outfit on every page — same white tunic, same beige trousers, same boots. "
            "No outfit changes. NO skirts or shorts."
        ),
        "outfit_boy": (
            "a crisp white linen explorer tunic with bronze trim, breathable tan desert trousers, "
            "durable leather gladiator-style boots, a wide-brimmed sun hat, and a glowing gold ankh pendant on a leather cord. "
            "EXACTLY the same outfit on every page — same white tunic, same tan trousers, same boots. "
            "No outfit changes. NO short shorts."
        ),
    },

    # ── 10. TAC MAHAL (Değişmedi, uygun) ────────────────────────────────────────────────────
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
            "a deep teal cotton zip-up explorer jacket with reflective silver stripes on sleeves, "
            "dark navy blue waterproof trousers, black rubber rain boots with teal trim, "
            "small yellow LED flashlight headlamp on forehead, dark gray utility backpack. "
            "EXACTLY the same outfit on every page — same teal jacket, same navy trousers, same black boots. "
            "No outfit changes. NO skirts or shorts."
        ),
        "outfit_boy": (
            "a dark navy blue cotton zip-up explorer jacket with reflective orange stripes on sleeves, "
            "dark charcoal waterproof trousers, black rubber rain boots with orange trim, "
            "small yellow LED flashlight headlamp on forehead, dark gray utility backpack. "
            "EXACTLY the same outfit on every page — same navy jacket, same charcoal trousers, same black boots. "
            "No outfit changes. NO short shorts."
        ),
    },

    # ── 12. AMAZON ORMANLARI (Derin Orman Kaşifi) ─────────────────────────────────────────────
    "Amazon": {
        "outfit_girl": (
            "a rugged olive-green jungle utility shirt over a bright yellow tee, breathable dark brown cargo pants, "
            "sturdy waterproof jungle boots, a wide-brimmed adventure hat, and a leather crossbody satchel with a glowing animal-tooth charm. "
            "EXACTLY the same outfit on every page — same utility shirt, same hat, same cargo pants. "
            "No outfit changes. NO skirts or shorts."
        ),
        "outfit_boy": (
            "a rugged olive-green jungle utility shirt over a bright orange tee, breathable dark brown cargo pants, "
            "sturdy waterproof jungle boots, a wide-brimmed adventure hat, and a leather crossbody satchel with a glowing animal-tooth charm. "
            "EXACTLY the same outfit on every page — same utility shirt, same hat, same cargo pants. "
            "No outfit changes. NO short shorts."
        ),
    },

    # ── 13. UZAY MACERASI ────────────────────────────────────────────────
    "Uzay": {
        "outfit_girl": (
            "sleek futuristic white and electric-blue EVA astronaut suit for a child, glowing neon azure piping along the seams, "
            "high-tech helmet with a transparent gold-tinted visor, compact jetpack life-support system, durable articulated space gloves and boots, "
            "a utility belt with glowing space tools, small Turkish flag patch on the chest. NO other national flags. "
            "EXACTLY the same outfit on every page — same astronaut suit, same helmet. "
            "No outfit changes. NO skirts or shorts."
        ),
        "outfit_boy": (
            "sleek futuristic white and carbon-black EVA astronaut suit for a child, glowing neon azure piping along the seams, "
            "high-tech helmet with a transparent gold-tinted visor, compact jetpack life-support system, durable articulated space gloves and boots, "
            "a utility belt with glowing space tools, small Turkish flag patch on the chest. NO other national flags. "
            "EXACTLY the same outfit on every page — same astronaut suit, same helmet. "
            "No outfit changes. NO short shorts."
        ),
    },

    # ── 14. DİNOZOR ZAMANI (Tarihöncesi Kaşif) ───────────────────────────────────────────────
    "Dinozor": {
        "outfit_girl": (
            "a rugged tan utility shirt over a white tee, dark green cargo pants with climbing boots, "
            "a distressed leather aviator jacket, and a utility belt with a compass pouch and a fossil-tooth necklace. "
            "EXACTLY the same outfit on every page — same tan utility shirt, same leather jacket, same cargo pants. "
            "No outfit changes. NO skirts or shorts."
        ),
        "outfit_boy": (
            "a rugged tan utility shirt over a dark tee, dark green cargo pants with climbing boots, "
            "a distressed leather aviator jacket, and a utility belt with a compass pouch and a fossil-tooth necklace. "
            "EXACTLY the same outfit on every page — same tan utility shirt, same leather jacket, same cargo pants. "
            "No outfit changes. NO short shorts."
        ),
    },

    # ── 15. OKYANUS MACERASI ─────────────────────────────────────────────
    "Okyanus": {
        "outfit_girl": (
            "a teal and coral pink neoprene diving wetsuit with white trim stripes along arms, "
            "clear full-face diving mask with coral pink frame pushed up on forehead, "
            "compact metallic silver oxygen tank on back, bright yellow diving fins, "
            "waterproof wrist computer on left arm showing depth gauge display. "
            "EXACTLY the same outfit on every page — same teal-pink wetsuit, same coral mask, same yellow fins."
        ),
        "outfit_boy": (
            "a navy blue and bright orange neoprene diving wetsuit with reflective white stripes, "
            "clear full-face diving mask with blue frame pushed up on forehead, "
            "compact metallic silver oxygen tank on back, bright orange diving fins, "
            "waterproof yellow flashlight clipped to belt on right hip. "
            "EXACTLY the same outfit on every page — same navy-orange wetsuit, same blue mask, same orange fins."
        ),
    },

    # ── 16. UMRE (Değişmedi, uygun) ─────────────────────────────────────────────────────────
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
            "small round white knitted taqiyah skull-cap sitting snugly on top of the head "
            "(NOT a turban, NOT a wrapped cloth, NOT a keffiyeh, NOT a hood — ONLY a small round knitted cap), "
            "light beige loose-fitting cotton pants, "
            "comfortable tan leather sandals, small white cotton drawstring backpack. "
            "Simple and clean appearance inspired by ihram purity. "
            "EXACTLY the same outfit on every page — same white kurta, same small round white taqiyah cap, same beige pants."
        ),
    },
}

async def update_heroic_outfits():
    print("\n" + "=" * 70)
    print("👕 KAHRAMANSI VE ÖZGÜN KIYAFET GÜNCELLEMESİ BAŞLIYOR")
    print("=" * 70)

    async with async_session_factory() as db:
        result = await db.execute(select(Scenario))
        scenarios = list(result.scalars().all())

        updated = 0
        skipped = 0

        for scenario in scenarios:
            matched_key = None
            for key in OUTFITS:
                if key.lower() in (scenario.name or "").lower() or key.lower() in (scenario.theme_key or "").lower():
                    matched_key = key
                    break
            
            # Additional check for space/güneş sistemi
            if not matched_key and ("güneş" in (scenario.name or "").lower() or "uzay" in (scenario.name or "").lower()):
                matched_key = "Uzay"

            if not matched_key:
                print(f"  ⚠️  Eşleşme yok: {scenario.name} (theme: {scenario.theme_key})")
                skipped += 1
                continue

            outfit = OUTFITS[matched_key]
            scenario.outfit_girl = outfit["outfit_girl"]
            scenario.outfit_boy = outfit["outfit_boy"]
            updated += 1

            print(f"  ✅ Güncellendi: {scenario.name} (Eşleşen Kategori: {matched_key})")

        await db.commit()

        print("=" * 70)
        print(f"\n📊 SONUÇ:")
        print(f"   ✅ Güncellenen: {updated}")
        print(f"   ⚠️  Atlanılan:  {skipped}")
        print("👕 Tüm kıyafetler artık KAHRAMANSI, TEMATİK ve benzersiz!")
        print("   Mini etek ve şortlar engellendi.")
        print("=" * 70 + "\n")

if __name__ == "__main__":
    asyncio.run(update_heroic_outfits())

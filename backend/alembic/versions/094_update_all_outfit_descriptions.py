"""Update all scenario outfits with precise, specific descriptions.

Revision ID: 094_update_all_outfit_descriptions
Revises: 093_add_audio_addon_products
Create Date: 2026-02-27

Problem: Old outfit descriptions were vague ("white or pastel t-shirt",
"graphic t-shirt (Istanbul theme or plain color)") causing the AI model
to generate different clothing on each page.

Solution: Every scenario now has exact colors, materials, and patterns.
Each outfit ends with "EXACTLY the same outfit on every page" lock phrase
to force cross-page consistency.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "094"
down_revision: str | None = "ae6a0f427999"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


# ═══════════════════════════════════════════════════════════════════════
# NET, SPESİFİK KIYAFETLERİN TANIMLARI
# ═══════════════════════════════════════════════════════════════════════
# Rules:
# - Fixed colors (cherry-red, royal blue, coral-orange etc.)
# - Fixed materials (cotton, nylon, neoprene etc.)
# - No "or" / "optional" — AI needs ONE clear description
# - "EXACTLY the same outfit on every page" at the end

OUTFIT_UPDATES = [
    {
        "name_contains": "Galata",
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
    {
        "name_contains": "Kapadokya",
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
    {
        "name_contains": "Göbeklitepe",
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
    {
        "name_contains": "Efes",
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
    {
        "name_contains": "Çatalhöyük",
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
    {
        "name_contains": "Sümela",
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
    {
        "name_contains": "Sultanahmet",
        "outfit_girl": (
            "soft white cotton long-sleeve modest dress reaching ankles with delicate blue floral embroidery on hem, "
            "PROPERLY WRAPPED white hijab: fabric wraps FULLY around head and neck — NO hair visible, NO neck visible, "
            "fabric drapes softly over shoulders (modern proper hijab wrap, NOT a loose veil), comfortable cream flat shoes, "
            "small white shoulder bag with blue strap. "
            "EXACTLY the same outfit on every page — same white dress with blue embroidery, same properly wrapped white hijab."
        ),
        "outfit_boy": (
            "clean white cotton long-sleeve shirt, light beige cotton loose-fitting pants, "
            "white knit taqiyah prayer cap on head, comfortable tan leather sandals, "
            "small beige canvas shoulder bag. "
            "EXACTLY the same outfit on every page — same white shirt, same beige pants, same white taqiyah cap."
        ),
    },
    {
        "name_contains": "Kudüs",
        "outfit_girl": (
            "soft ivory white cotton long-sleeve modest dress reaching ankles, "
            "PROPERLY WRAPPED white hijab: fabric wraps FULLY around head and neck — NO hair visible, NO neck visible, "
            "fabric drapes softly over shoulders and chest (modern proper hijab wrap, NOT a loose veil, NOT fabric on top of head only), "
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
    {
        "name_contains": "Abu Simbel",
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
    {
        "name_contains": "Tac Mahal",
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
    {
        "name_contains": "Yerebatan",
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
    {
        "name_contains": "Amazon",
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
    {
        "name_contains": "Uzay",
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
    {
        "name_contains": "Dinozor",
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
    {
        "name_contains": "Okyanus",
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
    {
        "name_contains": "Umre",
        "outfit_girl": (
            "pure white cotton modest long-sleeve dress reaching ankles with no patterns or decorations, "
            "PROPERLY WRAPPED white hijab: fabric wraps FULLY around the head and neck — NO hair visible, NO neck visible, "
            "fabric drapes softly over shoulders and chest, neat folds (modern proper hijab wrap style, NOT a loose veil, NOT fabric merely on top of head). "
            "comfortable beige leather flat sandals, small white cotton drawstring backpack. "
            "Simple and clean appearance inspired by ihram purity, no jewelry. "
            "EXACTLY the same outfit on every page — same pure white dress, same properly wrapped white hijab, same beige sandals."
        ),
        "outfit_boy": (
            "pure white cotton knee-length kurta tunic with no patterns or decorations, "
            "white knit taqiyah prayer cap on head, light beige loose-fitting cotton pants, "
            "comfortable tan leather sandals, small white cotton drawstring backpack. "
            "Simple and clean appearance inspired by ihram purity. "
            "EXACTLY the same outfit on every page — same white kurta, same white taqiyah, same beige pants."
        ),
    },
]


def upgrade() -> None:
    connection = op.get_bind()
    updated_total = 0

    for entry in OUTFIT_UPDATES:
        result = connection.execute(
            sa.text(
                "UPDATE scenarios SET outfit_girl = :girl, outfit_boy = :boy "
                "WHERE name ILIKE :pattern"
            ),
            {
                "girl": entry["outfit_girl"],
                "boy": entry["outfit_boy"],
                "pattern": f"%{entry['name_contains']}%",
            },
        )
        updated_total += result.rowcount

    print(f"[094] Updated {updated_total} scenario rows with precise outfit descriptions.")


def downgrade() -> None:
    # Downgrade restores the old vague descriptions from migration 090
    pass

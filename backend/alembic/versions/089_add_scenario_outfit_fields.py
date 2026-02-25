"""Add outfit_girl and outfit_boy fields to scenarios.

Revision ID: 089_add_scenario_outfit_fields
Revises: 088_add_scenario_book_structure
Create Date: 2026-02-25

Adds:
- outfit_girl: Scenario-specific outfit for girl characters (English, for AI prompts)
- outfit_boy: Scenario-specific outfit for boy characters (English, for AI prompts)

Also seeds outfit data for all existing scenarios.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "089_add_scenario_outfit_fields"
down_revision: str | None = "088_add_scenario_book_structure"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# Outfit data keyed by scenario name (partial match)
SCENARIO_OUTFITS = [
    {
        "name_contains": "Kapadokya",
        "outfit_girl": "dusty rose linen explorer dress, wide-brim straw hat, brown leather ankle boots",
        "outfit_boy": "khaki explorer shirt, rolled-up canvas pants, brown leather boots, small backpack",
    },
    {
        "name_contains": "Göbeklitepe",
        "outfit_girl": "sand-colored linen tunic dress, braided leather belt, soft leather sandals, small satchel bag",
        "outfit_boy": "beige linen shirt, khaki cargo shorts, leather sandals, canvas satchel bag",
    },
    {
        "name_contains": "Efes",
        "outfit_girl": "soft white linen dress with golden trim, leather sandals, small woven basket",
        "outfit_boy": "white linen tunic, brown leather belt, leather sandals, small scroll in hand",
    },
    {
        "name_contains": "Çatalhöyük",
        "outfit_girl": "warm terracotta linen dress, clay bead necklace, soft leather moccasins",
        "outfit_boy": "ochre linen tunic, woven belt, soft leather moccasins, small clay pot",
    },
    {
        "name_contains": "Sümela",
        "outfit_girl": "forest green hooded cloak over cream dress, leather boots, small lantern",
        "outfit_boy": "dark green hooded cloak, brown tunic, leather boots, small lantern",
    },
    {
        "name_contains": "Sultanahmet",
        "outfit_girl": "turquoise embroidered dress with golden details, soft slippers, small decorative bag",
        "outfit_boy": "deep blue vest over white shirt, traditional shalwar pants, soft leather slippers",
    },
    {
        "name_contains": "Galata",
        "outfit_girl": "burgundy wool coat, white blouse, ankle boots, small telescope",
        "outfit_boy": "navy blue wool coat, white shirt, dark pants, leather boots, small telescope",
    },
    {
        "name_contains": "Kudüs",
        "outfit_girl": "cream linen dress with colorful embroidery, leather sandals, woven headscarf",
        "outfit_boy": "cream linen shirt, beige pants, leather sandals, small woven bag",
    },
    {
        "name_contains": "Abu Simbel",
        "outfit_girl": "white linen dress with golden ankh necklace, leather sandals, small papyrus scroll",
        "outfit_boy": "white linen tunic with golden collar detail, leather sandals, small papyrus scroll",
    },
    {
        "name_contains": "Tac Mahal",
        "outfit_girl": "soft pink silk dress with silver embroidery, jeweled sandals, flower garland",
        "outfit_boy": "ivory white kurta shirt, light beige pants, leather sandals, small lotus flower",
    },
    {
        "name_contains": "Yerebatan",
        "outfit_girl": "teal explorer dress, waterproof boots, small glowing lantern",
        "outfit_boy": "dark teal explorer jacket, waterproof pants, boots, small glowing lantern",
    },
]


def upgrade() -> None:
    op.add_column(
        "scenarios",
        sa.Column("outfit_girl", sa.Text(), nullable=True),
    )
    op.add_column(
        "scenarios",
        sa.Column("outfit_boy", sa.Text(), nullable=True),
    )

    # Seed outfit data for existing scenarios
    connection = op.get_bind()
    for entry in SCENARIO_OUTFITS:
        connection.execute(
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


def downgrade() -> None:
    op.drop_column("scenarios", "outfit_girl")
    op.drop_column("scenarios", "outfit_boy")

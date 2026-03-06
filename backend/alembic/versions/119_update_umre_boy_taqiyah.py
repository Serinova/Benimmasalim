"""Update Umre scenario outfit_boy with clearer taqiyah description.

Revision ID: 119_taqiyah
Revises: 118
Create Date: 2026-03-05
"""

from alembic import op

revision = "119_update_umre_boy_taqiyah"
down_revision = "118_update_hijab_outfit_descriptions"
branch_labels = None
depends_on = None

NEW_OUTFIT_BOY = (
    "pure white cotton knee-length kurta tunic with no patterns or decorations, "
    "small round white knitted taqiyah skull-cap sitting snugly on top of the head "
    "(NOT a turban, NOT a wrapped cloth, NOT a keffiyeh, NOT a hood — ONLY a small round knitted cap), "
    "light beige loose-fitting cotton pants, "
    "comfortable tan leather sandals, small white cotton drawstring backpack. "
    "Simple and clean appearance inspired by ihram purity. "
    "EXACTLY the same outfit on every page — same white kurta, same small round white taqiyah cap, same beige pants, same sandals."
)

OLD_OUTFIT_BOY = (
    "pure white cotton knee-length kurta tunic with no patterns or decorations, "
    "white knit taqiyah prayer cap on head, light beige loose-fitting cotton pants, "
    "comfortable tan leather sandals, small white cotton drawstring backpack. "
    "Simple and clean appearance inspired by ihram purity. "
    "EXACTLY the same outfit on every page — same white kurta, same white taqiyah, same beige pants."
)


def upgrade() -> None:
    op.execute(
        f"UPDATE scenarios SET outfit_boy = '{NEW_OUTFIT_BOY}' "
        "WHERE theme_key = 'umre_pilgrimage'"
    )


def downgrade() -> None:
    op.execute(
        f"UPDATE scenarios SET outfit_boy = '{OLD_OUTFIT_BOY}' "
        "WHERE theme_key = 'umre_pilgrimage'"
    )

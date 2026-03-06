"""Update hijab outfit descriptions to properly wrapped style.

Revision ID: 118_update_hijab_outfit_descriptions
Revises: 117_back_cover_visual_fields
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "118_update_hijab_outfit_descriptions"
down_revision = "117_back_cover_visual_fields"
branch_labels = None
depends_on = None

_PROPERLY_WRAPPED_SUFFIX = (
    "PROPERLY WRAPPED hijab: fabric wraps FULLY around head and neck — "
    "NO hair visible, NO neck visible, fabric drapes softly over shoulders and chest "
    "(modern proper hijab wrap style, NOT a loose veil, NOT fabric merely on top of head)."
)

_SCENARIOS = [
    {
        "name_pattern": "%Umre%",
        "outfit_girl": (
            "pure white cotton modest long-sleeve dress reaching ankles with no patterns or decorations, "
            "PROPERLY WRAPPED white hijab: fabric wraps FULLY around the head and neck — NO hair visible, NO neck visible, "
            "fabric drapes softly over shoulders and chest, neat folds (modern proper hijab wrap style, NOT a loose veil, NOT fabric merely on top of head). "
            "comfortable beige leather flat sandals, small white cotton drawstring backpack. "
            "Simple and clean appearance inspired by ihram purity, no jewelry. "
            "EXACTLY the same outfit on every page — same pure white dress, same properly wrapped white hijab, same beige sandals."
        ),
    },
    {
        "name_pattern": "%Sultanahmet%",
        "outfit_girl": (
            "soft white cotton long-sleeve modest dress reaching ankles with delicate blue floral embroidery on hem, "
            "PROPERLY WRAPPED white hijab: fabric wraps FULLY around head and neck — NO hair visible, NO neck visible, "
            "fabric drapes softly over shoulders (modern proper hijab wrap, NOT a loose veil), comfortable cream flat shoes, "
            "small white shoulder bag with blue strap. "
            "EXACTLY the same outfit on every page — same white dress with blue embroidery, same properly wrapped white hijab."
        ),
    },
    {
        "name_pattern": "%Kudüs%",
        "outfit_girl": (
            "soft ivory white cotton long-sleeve modest dress reaching ankles, "
            "PROPERLY WRAPPED white hijab: fabric wraps FULLY around head and neck — NO hair visible, NO neck visible, "
            "fabric drapes softly over shoulders and chest (modern proper hijab wrap, NOT a loose veil, NOT fabric on top of head only), "
            "comfortable light beige flat sandals, small white cotton drawstring bag. "
            "EXACTLY the same outfit on every page — same ivory dress, same properly wrapped white hijab, same beige sandals."
        ),
    },
]


def upgrade() -> None:
    conn = op.get_bind()
    for s in _SCENARIOS:
        conn.execute(
            sa.text(
                "UPDATE scenarios SET outfit_girl = :outfit_girl "
                "WHERE name ILIKE :pattern"
            ),
            {"outfit_girl": s["outfit_girl"], "pattern": s["name_pattern"]},
        )


def downgrade() -> None:
    pass  # Non-destructive — no rollback needed

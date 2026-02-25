"""Add VisualStyle 'Yumuşak Pastel' (soft pastel / Ghibli-inspired cosy illustration).

Revision ID: 028_soft_pastel
Revises: 027_style_neg_defaults
Create Date: 2026-02-08

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

from app.prompt_engine.constants import get_style_negative_default

revision: str = "028_soft_pastel"
down_revision: str = "027_style_neg_defaults"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

PROMPT_MODIFIER = (
    "The illustration style is soft pastel storybook with gentle hand-drawn lines, "
    "warm muted colors (beige, cream, soft coral), cosy domestic atmosphere, Ghibli-inspired softness"
)


def upgrade() -> None:
    conn = op.get_bind()
    # Insert only if name does not exist
    conn.execute(
        sa.text("""
            INSERT INTO visual_styles (id, name, thumbnail_url, prompt_modifier, cover_aspect_ratio, page_aspect_ratio, id_weight, is_active, created_at, updated_at)
            SELECT gen_random_uuid(), 'Yumuşak Pastel', '/styles/watercolor.jpg', :mod, '2:3', '1:1', 0.74, true, now(), now()
            WHERE NOT EXISTS (SELECT 1 FROM visual_styles WHERE name = 'Yumuşak Pastel')
        """),
        {"mod": PROMPT_MODIFIER},
    )
    # Set style_negative_en for the new style (and any existing row with this name)
    neg = get_style_negative_default(PROMPT_MODIFIER)
    conn.execute(
        sa.text("UPDATE visual_styles SET style_negative_en = :neg WHERE name = 'Yumuşak Pastel'"),
        {"neg": neg},
    )


def downgrade() -> None:
    op.execute(sa.text("DELETE FROM visual_styles WHERE name = 'Yumuşak Pastel'"))

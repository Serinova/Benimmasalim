"""Add 'Foto Masal' (Photo Storybook) visual style — Nano Banana 2 optimized.

Revision ID: 128_add_photo_storybook_style
Revises: 127_kudus_guide_no_options
Create Date: 2026-03-06

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

from app.prompt_engine.constants import get_style_negative_default

revision: str = "128_add_photo_storybook_style"
down_revision: str = "127_kudus_guide"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

PROMPT_MODIFIER = (
    "photo-realistic child in illustrated storybook environment, "
    "hybrid photo-illustration style, realistic child face and body, "
    "vibrant illustrated magical background"
)

STYLE_BLOCK = (
    "Hybrid photo-illustration children's book style. "
    "The child character: photo-realistic face, natural skin texture, real hair, "
    "accurate proportions — NOT cartoonized, NOT stylized, NOT simplified. "
    "The environment: vibrant illustrated storybook world, painterly textures, "
    "warm magical lighting, rich colors, whimsical details. "
    "Sharp focus on child, dreamy illustrated background."
)

LEADING_PREFIX = (
    "Art style: The CHILD looks photo-realistic and natural — "
    "their face, skin, hair, and body are rendered with high photographic fidelity. "
    "The ENVIRONMENT and BACKGROUND are rendered as a vibrant, colorful "
    "children's book illustration with painterly details, magical lighting, "
    "and whimsical atmosphere. "
    "This creates a hybrid effect: a real-looking child immersed in a fantastical illustrated world. "
    "NOT fully cartoon, NOT fully photorealistic — the child is realistic, the world is illustrated. "
)


def upgrade() -> None:
    conn = op.get_bind()
    neg = get_style_negative_default(PROMPT_MODIFIER)
    conn.execute(
        sa.text("""
            INSERT INTO visual_styles (
                id, name, display_name, thumbnail_url, prompt_modifier,
                cover_aspect_ratio, page_aspect_ratio,
                style_negative_en, leading_prefix_override, style_block_override,
                is_active, created_at, updated_at
            )
            SELECT
                gen_random_uuid(), 'Foto Masal', 'Foto Masal',
                '/styles/photo-storybook.jpg', :mod,
                '3:2', '3:2',
                :neg, :leading, :style_block,
                true, now(), now()
            WHERE NOT EXISTS (SELECT 1 FROM visual_styles WHERE name = 'Foto Masal')
        """),
        {
            "mod": PROMPT_MODIFIER,
            "neg": neg,
            "leading": LEADING_PREFIX,
            "style_block": STYLE_BLOCK,
        },
    )


def downgrade() -> None:
    op.execute(sa.text("DELETE FROM visual_styles WHERE name = 'Foto Masal'"))

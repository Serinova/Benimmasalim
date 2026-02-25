"""Normalize id_weight and true_cfg across all visual styles.

Adventure Digital (best likeness) = id_weight 0.9, true_cfg 1.0.
Apply same template to all styles.

Revision ID: 061_normalize_all_style_id_weights
Revises: 060_fix_pixar_style_composition
Create Date: 2026-02-20
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "061_normalize_all_style_id_weights"
down_revision: str = "060_fix_pixar_style_composition"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Watercolor: 1.3 → 0.9  (true_cfg update moved to 062 where column is added)
    op.execute(sa.text("""
        UPDATE visual_styles SET id_weight = 0.9
        WHERE name ILIKE '%watercolor%' OR name ILIKE '%sulu boya%' OR name ILIKE '%suluboya%';
    """))

    # Soft Pastel: 1.3 → 0.9
    op.execute(sa.text("""
        UPDATE visual_styles SET id_weight = 0.9
        WHERE name ILIKE '%pastel%' OR name ILIKE '%soft%pastel%';
    """))

    # Anime/Ghibli: 1.2 → 0.9
    op.execute(sa.text("""
        UPDATE visual_styles SET id_weight = 0.9
        WHERE name ILIKE '%ghibli%' OR name ILIKE '%anime%';
    """))

    # 2D Default / Children's Book: 1.17 → 1.0
    op.execute(sa.text("""
        UPDATE visual_styles SET id_weight = 1.0
        WHERE (name ILIKE '%2D%children%' OR name ILIKE '%likeness%first%' OR name ILIKE '%storybook%')
          AND name NOT ILIKE '%watercolor%'
          AND name NOT ILIKE '%pastel%'
          AND name NOT ILIKE '%adventure%'
          AND name NOT ILIKE '%pixar%'
          AND name NOT ILIKE '%ghibli%';
    """))


def downgrade() -> None:
    pass  # Not worth reverting individually

"""Add true_cfg and start_step columns to visual_styles.

Both columns are nullable — NULL means "use style_config.py fallback".
Non-NULL admin override takes precedence over code defaults.

Revision ID: 062_add_true_cfg_start_step_to_visual_styles
Revises: 061_normalize_all_style_id_weights
Create Date: 2026-02-20
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "062_add_true_cfg_start_step_to_visual_styles"
down_revision: str = "061_normalize_all_style_id_weights"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "visual_styles",
        sa.Column("true_cfg", sa.Float(), nullable=True, comment="PuLID true_cfg override (NULL = code fallback)"),
    )
    op.add_column(
        "visual_styles",
        sa.Column("start_step", sa.Integer(), nullable=True, comment="PuLID start_step override (NULL = code fallback)"),
    )

    # Seed true_cfg = 1.0 for all styles (normalized in 061 for id_weight)
    op.execute(sa.text("""
        UPDATE visual_styles SET true_cfg = 1.0
        WHERE name ILIKE '%watercolor%' OR name ILIKE '%sulu boya%' OR name ILIKE '%suluboya%'
           OR name ILIKE '%pastel%' OR name ILIKE '%soft%pastel%'
           OR name ILIKE '%ghibli%' OR name ILIKE '%anime%'
           OR name ILIKE '%2D%children%' OR name ILIKE '%likeness%first%' OR name ILIKE '%storybook%';
    """))


def downgrade() -> None:
    op.drop_column("visual_styles", "start_step")
    op.drop_column("visual_styles", "true_cfg")

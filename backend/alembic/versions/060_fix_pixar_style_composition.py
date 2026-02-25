"""Fix Pixar style: add composition guards and lower id_weight.

Problems fixed:
- Missing face likeness block (child doesn't resemble the photo)
- Missing close-up/portrait/bokeh in negative (background blurry)
- id_weight too high → child face dominates frame

Revision ID: 060_fix_pixar_style_composition
Revises: 059_lower_2d_storybook_id_weight
Create Date: 2026-02-20
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "060_fix_pixar_style_composition"
down_revision: str = "059_lower_2d_storybook_id_weight"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        sa.text(
            """
            UPDATE visual_styles
            SET id_weight = 1.0
            WHERE name ILIKE '%pixar%'
               OR name ILIKE '%3D%pixar%'
               OR name ILIKE '%pixar%3D%';
            """
        )
    )


def downgrade() -> None:
    op.execute(
        sa.text(
            """
            UPDATE visual_styles
            SET id_weight = 1.2
            WHERE name ILIKE '%pixar%'
               OR name ILIKE '%3D%pixar%'
               OR name ILIKE '%pixar%3D%';
            """
        )
    )

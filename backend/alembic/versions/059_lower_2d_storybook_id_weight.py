"""Lower 2D Children's Book (default) style id_weight from 1.3 to 1.17.

High id_weight causes PuLID to over-focus on the face:
- Eyes become oversized
- Background scene goes blurry
- Child takes up too much frame

Revision ID: 059_lower_2d_storybook_id_weight
Revises: 058_lower_adventure_digital_id_weight
Create Date: 2026-02-20
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "059_lower_2d_storybook_id_weight"
down_revision: str = "058_lower_adventure_digital_id_weight"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Match by name (display name in DB) OR by prompt_modifier containing "hand-painted storybook"
    op.execute(
        sa.text(
            """
            UPDATE visual_styles
            SET id_weight = 1.17
            WHERE name ILIKE '%2D%children%'
               OR name ILIKE '%likeness%first%'
               OR name ILIKE '%storybook%2D%'
               OR (prompt_modifier ILIKE '%hand-painted storybook%' AND id_weight >= 1.3);
            """
        )
    )


def downgrade() -> None:
    op.execute(
        sa.text(
            """
            UPDATE visual_styles
            SET id_weight = 1.3
            WHERE name ILIKE '%2D%children%'
               OR name ILIKE '%likeness%first%'
               OR name ILIKE '%storybook%2D%'
               OR (prompt_modifier ILIKE '%hand-painted storybook%' AND id_weight = 1.17);
            """
        )
    )

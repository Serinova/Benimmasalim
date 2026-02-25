"""Switch default AI config image provider from gemini to fal.

Fal.ai PuLID provides superior face likeness compared to Gemini Imagen 3.

Revision ID: 056_switch_default_provider_to_fal
Revises: 055_fix_yerebatan_description
Create Date: 2026-02-20
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "056_switch_default_provider_to_fal"
down_revision: str = "055_fix_yerebatan_description"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        sa.text(
            """
            UPDATE ai_generation_configs
            SET image_provider = 'fal'
            WHERE is_default = TRUE AND (image_provider = 'gemini' OR image_provider = 'gemini_flash');
            """
        )
    )


def downgrade() -> None:
    op.execute(
        sa.text(
            """
            UPDATE ai_generation_configs
            SET image_provider = 'gemini_flash'
            WHERE is_default = TRUE AND image_provider = 'fal';
            """
        )
    )

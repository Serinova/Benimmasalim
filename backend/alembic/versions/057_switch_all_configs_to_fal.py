"""Switch ALL AI generation configs to use fal provider.

Previous migration (056) only updated is_default=TRUE configs.
Product-specific configs also need to be updated.

Revision ID: 057_switch_all_configs_to_fal
Revises: 056_switch_default_provider_to_fal
Create Date: 2026-02-20
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "057_switch_all_configs_to_fal"
down_revision: str = "056_switch_default_provider_to_fal"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        sa.text(
            """
            UPDATE ai_generation_configs
            SET image_provider = 'fal'
            WHERE image_provider IN ('gemini', 'gemini_flash');
            """
        )
    )


def downgrade() -> None:
    op.execute(
        sa.text(
            """
            UPDATE ai_generation_configs
            SET image_provider = 'gemini_flash'
            WHERE image_provider = 'fal';
            """
        )
    )

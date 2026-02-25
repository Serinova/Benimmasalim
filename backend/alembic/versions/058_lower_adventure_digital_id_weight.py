"""Lower Adventure Digital id_weight from 1.0 to 0.9.

Less face-focus = more room for scene/story details.

Revision ID: 058_lower_adventure_digital_id_weight
Revises: 057_switch_all_configs_to_fal
Create Date: 2026-02-20
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "058_lower_adventure_digital_id_weight"
down_revision: str = "057_switch_all_configs_to_fal"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        sa.text(
            """
            UPDATE visual_styles
            SET id_weight = 0.9
            WHERE name ILIKE '%adventure%digital%'
               OR name ILIKE '%macera%dijital%';
            """
        )
    )


def downgrade() -> None:
    op.execute(
        sa.text(
            """
            UPDATE visual_styles
            SET id_weight = 1.0
            WHERE name ILIKE '%adventure%digital%'
               OR name ILIKE '%macera%dijital%';
            """
        )
    )

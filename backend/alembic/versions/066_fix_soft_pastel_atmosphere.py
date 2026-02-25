"""Fix soft_pastel prompt_modifier: replace 'cosy domestic atmosphere' with
'warm magical atmosphere' so the style works correctly with outdoor/historical
scenarios (Cappadocia, Abu Simbel, Göbeklitepe, etc.).

Revision ID: 066_fix_soft_pastel_atmosphere
Revises: 065_fix_child_safe_scenario_prompts
Create Date: 2026-02-21
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "066_fix_soft_pastel_atmosphere"
down_revision: str = "065_fix_child_safe_scenario_prompts"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        sa.text(
            "UPDATE visual_styles "
            "SET prompt_modifier = REPLACE(prompt_modifier, 'cosy domestic atmosphere', 'warm magical atmosphere') "
            "WHERE prompt_modifier LIKE '%cosy domestic atmosphere%'"
        )
    )
    op.execute(
        sa.text(
            "UPDATE visual_styles "
            "SET prompt_modifier = REPLACE(prompt_modifier, 'cozy warmth and dreamy softness', 'dreamy softness') "
            "WHERE prompt_modifier LIKE '%cozy warmth and dreamy softness%'"
        )
    )


def downgrade() -> None:
    pass

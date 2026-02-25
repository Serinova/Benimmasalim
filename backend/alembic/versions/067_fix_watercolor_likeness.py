"""Fix watercolor and soft pastel likeness and proportion settings.

Revision ID: 067_fix_watercolor_likeness
Revises: 066_fix_soft_pastel_atmosphere
Create Date: 2026-02-22
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "067_fix_watercolor_likeness"
down_revision: str = "066_fix_soft_pastel_atmosphere"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Watercolor (sulu boya) likeness oranini arttir (%50 daha az benziyordu)
    op.execute(
        sa.text(
            "UPDATE visual_styles "
            "SET id_weight = 1.3 "
            "WHERE name ILIKE '%watercolor%' OR name ILIKE '%sulu boya%' OR name ILIKE '%suluboya%'"
        )
    )


def downgrade() -> None:
    op.execute(
        sa.text(
            "UPDATE visual_styles "
            "SET id_weight = 0.9 "
            "WHERE name ILIKE '%watercolor%' OR name ILIKE '%sulu boya%' OR name ILIKE '%suluboya%'"
        )
    )

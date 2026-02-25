"""Set visual_styles.id_weight = NULL for all seeded styles.

DB seeds set id_weight=0.90 uniformly, overriding per-style code weights
(watercolor 0.72, pastel 0.74, pixar 0.78 etc.). By NULLing the column,
the runtime falls back to STYLE_PULID_WEIGHTS in constants.py which has
correct per-style values.

Admins can still override via the admin panel (non-NULL value wins).

Revision ID: 048_fix_id_weight
Revises: 047_v3_story_pipeline
Create Date: 2026-02-17
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "048_fix_id_weight"
down_revision: str = "047_v3_story_pipeline"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1) Make column nullable
    op.alter_column(
        "visual_styles",
        "id_weight",
        existing_type=sa.Float(),
        nullable=True,
    )

    # 2) NULL out all rows so code fallback (STYLE_PULID_WEIGHTS) applies
    op.execute("UPDATE visual_styles SET id_weight = NULL")


def downgrade() -> None:
    # Restore 0.90 default for all rows, then make NOT NULL again
    op.execute("UPDATE visual_styles SET id_weight = 0.90 WHERE id_weight IS NULL")
    op.alter_column(
        "visual_styles",
        "id_weight",
        existing_type=sa.Float(),
        nullable=False,
    )

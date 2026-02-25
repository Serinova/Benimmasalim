"""Add num_inference_steps and guidance_scale to visual_styles.

Both nullable — NULL means use GenerationConfig defaults (28 / 3.5).
Admin can override per-style for quality/speed trade-offs.

Revision ID: 063_add_generation_params_to_visual_styles
Revises: 062_add_true_cfg_start_step_to_visual_styles
Create Date: 2026-02-21
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "063_add_generation_params_to_visual_styles"
down_revision: str = "062_add_true_cfg_start_step_to_visual_styles"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "visual_styles",
        sa.Column(
            "num_inference_steps",
            sa.Integer(),
            nullable=True,
            comment="FLUX num_inference_steps override (NULL = default 28)",
        ),
    )
    op.add_column(
        "visual_styles",
        sa.Column(
            "guidance_scale",
            sa.Float(),
            nullable=True,
            comment="FLUX guidance_scale override (NULL = default 3.5)",
        ),
    )


def downgrade() -> None:
    op.drop_column("visual_styles", "guidance_scale")
    op.drop_column("visual_styles", "num_inference_steps")

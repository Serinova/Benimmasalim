"""Add new visual fields to back_cover_configs table.

Revision ID: 117_back_cover_visual_fields
Revises: 116_seed_karsilama_templates
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "117_back_cover_visual_fields"
down_revision = "116_seed_karsilama_templates"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "back_cover_configs",
        sa.Column("background_gradient_end", sa.String(20), nullable=False, server_default="#EDE4F8"),
    )
    op.add_column(
        "back_cover_configs",
        sa.Column("accent_color", sa.String(20), nullable=False, server_default="#F59E0B"),
    )
    op.add_column(
        "back_cover_configs",
        sa.Column(
            "dedication_text",
            sa.Text(),
            nullable=False,
            server_default=(
                "Bu kitap, senin için; merakın, cesaretinle büyüyen "
                "ve hayal dünyasıyla sınırları zorlayan sen için..."
            ),
        ),
    )
    op.add_column(
        "back_cover_configs",
        sa.Column("show_decorative_lines", sa.Boolean(), nullable=False, server_default=sa.true()),
    )


def downgrade() -> None:
    op.drop_column("back_cover_configs", "show_decorative_lines")
    op.drop_column("back_cover_configs", "dedication_text")
    op.drop_column("back_cover_configs", "accent_color")
    op.drop_column("back_cover_configs", "background_gradient_end")

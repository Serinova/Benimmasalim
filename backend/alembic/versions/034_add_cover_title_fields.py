"""Add cover title WordArt fields to page_templates.

Kapak başlığı artık AI yerine page_composer tarafından WordArt tarzında çizilir.
Bu migration, kapak başlığının font, renk, kavis, gölge ve stroke ayarlarını ekler.

Revision ID: 034_cover_title
Revises: 033_text_bg_gradient
Create Date: 2026-02-11

"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "034_cover_title"
down_revision: str | None = "033_text_bg_gradient"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("page_templates", sa.Column("cover_title_enabled", sa.Boolean(), server_default="true", nullable=False))
    op.add_column("page_templates", sa.Column("cover_title_font_family", sa.String(100), server_default="Lobster", nullable=False))
    op.add_column("page_templates", sa.Column("cover_title_font_size_pt", sa.Integer(), server_default="48", nullable=False))
    op.add_column("page_templates", sa.Column("cover_title_font_color", sa.String(20), server_default="#FFD700", nullable=False))
    op.add_column("page_templates", sa.Column("cover_title_arc_intensity", sa.Integer(), server_default="35", nullable=False))
    op.add_column("page_templates", sa.Column("cover_title_shadow_enabled", sa.Boolean(), server_default="true", nullable=False))
    op.add_column("page_templates", sa.Column("cover_title_shadow_color", sa.String(20), server_default="#000000", nullable=False))
    op.add_column("page_templates", sa.Column("cover_title_shadow_offset", sa.Integer(), server_default="3", nullable=False))
    op.add_column("page_templates", sa.Column("cover_title_stroke_width", sa.Float(), server_default="2.0", nullable=False))
    op.add_column("page_templates", sa.Column("cover_title_stroke_color", sa.String(20), server_default="#8B6914", nullable=False))
    op.add_column("page_templates", sa.Column("cover_title_y_percent", sa.Float(), server_default="5.0", nullable=False))


def downgrade() -> None:
    op.drop_column("page_templates", "cover_title_y_percent")
    op.drop_column("page_templates", "cover_title_stroke_color")
    op.drop_column("page_templates", "cover_title_stroke_width")
    op.drop_column("page_templates", "cover_title_shadow_offset")
    op.drop_column("page_templates", "cover_title_shadow_color")
    op.drop_column("page_templates", "cover_title_shadow_enabled")
    op.drop_column("page_templates", "cover_title_arc_intensity")
    op.drop_column("page_templates", "cover_title_font_color")
    op.drop_column("page_templates", "cover_title_font_size_pt")
    op.drop_column("page_templates", "cover_title_font_family")
    op.drop_column("page_templates", "cover_title_enabled")

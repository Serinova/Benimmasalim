"""Add cloud extend/intensity fields to page_templates.

Allows admin to control cloud overlay width, height, and intensity
for better text readability control.

Revision ID: 105_cloud_extend
Revises: 104_white_cloud_bg
Create Date: 2026-02-28
"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "105_cloud_extend"
down_revision: str = "104_white_cloud_bg"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("page_templates", sa.Column("text_bg_extend_top", sa.Integer(), nullable=False, server_default="60"))
    op.add_column("page_templates", sa.Column("text_bg_extend_bottom", sa.Integer(), nullable=False, server_default="15"))
    op.add_column("page_templates", sa.Column("text_bg_extend_sides", sa.Integer(), nullable=False, server_default="6"))
    op.add_column("page_templates", sa.Column("text_bg_intensity", sa.Integer(), nullable=False, server_default="100"))


def downgrade() -> None:
    op.drop_column("page_templates", "text_bg_intensity")
    op.drop_column("page_templates", "text_bg_extend_sides")
    op.drop_column("page_templates", "text_bg_extend_bottom")
    op.drop_column("page_templates", "text_bg_extend_top")

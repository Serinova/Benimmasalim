"""Add back_cover_image_url to story_previews table.

Revision ID: 082_add_back_cover_image_url_to_story_previews
Revises: 081_add_is_back_cover_to_order_pages
Create Date: 2026-02-24
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "082_add_back_cover_image_url_to_story_previews"
down_revision: str = "081_add_is_back_cover_to_order_pages"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "story_previews",
        sa.Column("back_cover_image_url", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("story_previews", "back_cover_image_url")

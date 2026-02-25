"""Add child_photo_url to story_previews.

GCS URL for PuLID face reference; used by background task for remaining pages.

Revision ID: 020_child_photo_url
Revises: 019_id_weight
Create Date: 2026-02-05

"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "020_child_photo_url"
down_revision: str = "019_id_weight"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "story_previews",
        sa.Column("child_photo_url", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("story_previews", "child_photo_url")

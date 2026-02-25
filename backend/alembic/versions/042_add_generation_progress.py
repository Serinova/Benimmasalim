"""Add generation_progress JSONB column to story_previews.

Stores real-time progress info so the frontend can show
stage-based loading (e.g. "Sayfa 2/3 olusturuluyor...").

Revision ID: 042_generation_progress
Revises: 041_promo_story_preview
Create Date: 2026-02-13
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "042_generation_progress"
down_revision: str = "041_promo_story_preview"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "story_previews",
        sa.Column("generation_progress", postgresql.JSONB(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("story_previews", "generation_progress")

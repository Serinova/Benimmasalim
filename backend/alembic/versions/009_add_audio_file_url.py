"""Add audio_file_url to story_previews

Revision ID: 009_add_audio_file_url
Revises: 008_add_audio_to_story_preview
Create Date: 2026-01-31

"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '009_add_audio_file_url'
down_revision: str | None = '008_audio'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Add audio_file_url column for storing GCS URL of generated audio
    op.add_column('story_previews', sa.Column('audio_file_url', sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column('story_previews', 'audio_file_url')

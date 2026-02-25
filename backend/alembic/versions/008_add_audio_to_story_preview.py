"""Add audio fields to story_previews table.

Revision ID: 008_audio
Revises: 98504889b22f
Create Date: 2026-01-31
"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = '008_audio'
down_revision = '98504889b22f'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add audio book fields to story_previews
    op.add_column('story_previews', sa.Column('has_audio_book', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('story_previews', sa.Column('audio_type', sa.String(20), nullable=True))
    op.add_column('story_previews', sa.Column('audio_voice_id', sa.String(100), nullable=True))
    op.add_column('story_previews', sa.Column('voice_sample_url', sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column('story_previews', 'voice_sample_url')
    op.drop_column('story_previews', 'audio_voice_id')
    op.drop_column('story_previews', 'audio_type')
    op.drop_column('story_previews', 'has_audio_book')

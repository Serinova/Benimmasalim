"""Add marketing and conversion fields to scenarios

Revision ID: 010_add_scenario_marketing_fields
Revises: 009_add_audio_file_url
Create Date: 2026-02-01

This migration adds the following fields to the scenarios table:
- Media Assets: video_url, gallery_images (JSONB)
- Marketing & Urgency: promo_badge, promo_end_date, is_gift_wrapped
- Social Proof: rating, review_count, social_proof_text
- Content Features: feature_list (JSONB)

"""
from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '010_scenario_marketing'
down_revision: str | None = '009_add_audio_file_url'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # ============ MEDIA ASSETS ============
    # Video URL for trailer (YouTube/Vimeo)
    op.add_column('scenarios', sa.Column(
        'video_url',
        sa.Text(),
        nullable=True,
        comment='YouTube/Vimeo trailer video URL'
    ))

    # Gallery images for carousel (JSONB array)
    op.add_column('scenarios', sa.Column(
        'gallery_images',
        JSONB(),
        nullable=True,
        server_default='[]',
        comment='Array of image URLs for carousel gallery'
    ))

    # ============ MARKETING & URGENCY ============
    # Promo badge text
    op.add_column('scenarios', sa.Column(
        'promo_badge',
        sa.String(100),
        nullable=True,
        comment='Promotional badge text (e.g., "%20 İndirim")'
    ))

    # Promo end date for countdown
    op.add_column('scenarios', sa.Column(
        'promo_end_date',
        sa.DateTime(timezone=True),
        nullable=True,
        comment='Promotion end date for countdown timer'
    ))

    # Gift wrapped option
    op.add_column('scenarios', sa.Column(
        'is_gift_wrapped',
        sa.Boolean(),
        nullable=False,
        server_default='false',
        comment='Whether this scenario includes special gift packaging'
    ))

    # ============ SOCIAL PROOF ============
    # Rating score (0-5)
    op.add_column('scenarios', sa.Column(
        'rating',
        sa.Float(),
        nullable=True,
        server_default='0.0',
        comment='Rating score out of 5'
    ))

    # Review/order count
    op.add_column('scenarios', sa.Column(
        'review_count',
        sa.Integer(),
        nullable=False,
        server_default='0',
        comment='Number of reviews or orders'
    ))

    # Social proof display text
    op.add_column('scenarios', sa.Column(
        'social_proof_text',
        sa.String(255),
        nullable=True,
        comment='Social proof text (e.g., "500+ aile bayıldı!")'
    ))

    # ============ CONTENT FEATURES ============
    # Feature bullet points (JSONB array)
    op.add_column('scenarios', sa.Column(
        'feature_list',
        JSONB(),
        nullable=True,
        server_default='[]',
        comment='Array of feature bullet points'
    ))

    # ============ INDEXES ============
    # Index for active promos (for featured scenarios query)
    op.create_index(
        'idx_scenarios_promo_active',
        'scenarios',
        ['promo_end_date', 'is_active'],
        postgresql_where=sa.text('promo_end_date IS NOT NULL')
    )


def downgrade() -> None:
    # Drop index first
    op.drop_index('idx_scenarios_promo_active', table_name='scenarios')

    # Drop columns in reverse order
    op.drop_column('scenarios', 'feature_list')
    op.drop_column('scenarios', 'social_proof_text')
    op.drop_column('scenarios', 'review_count')
    op.drop_column('scenarios', 'rating')
    op.drop_column('scenarios', 'is_gift_wrapped')
    op.drop_column('scenarios', 'promo_end_date')
    op.drop_column('scenarios', 'promo_badge')
    op.drop_column('scenarios', 'gallery_images')
    op.drop_column('scenarios', 'video_url')

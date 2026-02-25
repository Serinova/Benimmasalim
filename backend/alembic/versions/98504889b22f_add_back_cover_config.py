"""add_back_cover_config

Revision ID: 98504889b22f
Revises: 007
Create Date: 2026-01-31

"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '98504889b22f'
down_revision: str | None = '007'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Create back_cover_configs table
    op.create_table('back_cover_configs',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('company_name', sa.String(length=200), nullable=False, server_default='Benim Masalım'),
        sa.Column('company_logo_url', sa.Text(), nullable=True),
        sa.Column('company_website', sa.String(length=200), nullable=False, server_default='www.benimmasalim.com'),
        sa.Column('company_email', sa.String(length=200), nullable=False, server_default='info@benimmasalim.com'),
        sa.Column('company_phone', sa.String(length=50), nullable=True),
        sa.Column('company_address', sa.Text(), nullable=True),
        sa.Column('background_color', sa.String(length=20), nullable=False, server_default='#F8F4F0'),
        sa.Column('primary_color', sa.String(length=20), nullable=False, server_default='#6B46C1'),
        sa.Column('text_color', sa.String(length=20), nullable=False, server_default='#333333'),
        sa.Column('qr_enabled', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('qr_size_mm', sa.Float(), nullable=False, server_default='30.0'),
        sa.Column('qr_position', sa.String(length=20), nullable=False, server_default='bottom_right'),
        sa.Column('qr_label', sa.String(length=100), nullable=False, server_default='Sesli Kitabı Dinle'),
        sa.Column('tips_title', sa.String(length=200), nullable=False, server_default='Ebeveynlere Öneriler'),
        sa.Column('tips_content', sa.Text(), nullable=False),
        sa.Column('tips_font_size', sa.Integer(), nullable=False, server_default='10'),
        sa.Column('tagline', sa.String(length=300), nullable=False, server_default='Her çocuk kendi masalının kahramanı!'),
        sa.Column('copyright_text', sa.String(length=300), nullable=False, server_default='© 2024 Benim Masalım. Tüm hakları saklıdır.'),
        sa.Column('show_stars', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('show_border', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('border_color', sa.String(length=20), nullable=False, server_default='#E0D4F7'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('is_default', sa.Boolean(), nullable=False, server_default='false'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )


def downgrade() -> None:
    op.drop_table('back_cover_configs')

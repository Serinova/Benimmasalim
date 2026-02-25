"""Add flipbook preview fields to products

Revision ID: 012_product_flipbook
Revises: 011_learning_outcome_assets
Create Date: 2026-02-01

This migration adds:
- sample_images: JSONB array for flipbook preview pages
- orientation: String for book orientation (portrait/landscape)

"""
from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '012_product_flipbook'
down_revision: str | None = '011_learning_outcome_assets'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Sample images for flipbook preview
    op.add_column('products', sa.Column(
        'sample_images',
        JSONB(),
        nullable=True,
        server_default='[]',
        comment='Sample page images for flipbook preview [cover, page1, page2, ...]'
    ))

    # Book orientation
    op.add_column('products', sa.Column(
        'orientation',
        sa.String(20),
        nullable=False,
        server_default='landscape',
        comment='Book orientation: portrait or landscape'
    ))


def downgrade() -> None:
    op.drop_column('products', 'orientation')
    op.drop_column('products', 'sample_images')

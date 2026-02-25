"""Move marketing fields from scenario to product

Revision ID: 4ed0b5e4ede9
Revises: 012_product_flipbook
Create Date: 2026-02-01 17:20:32.269439

"""
from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '4ed0b5e4ede9'
down_revision: str | None = '012_product_flipbook'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Add marketing columns to products table
    op.add_column('products', sa.Column('discounted_price', sa.Numeric(precision=10, scale=2), nullable=True, comment='Sale price if active promo'))
    op.add_column('products', sa.Column('video_url', sa.Text(), nullable=True, comment='Product promo/demo video (YouTube/Vimeo)'))
    op.add_column('products', sa.Column('promo_badge', sa.String(length=100), nullable=True))
    op.add_column('products', sa.Column('promo_end_date', sa.DateTime(timezone=True), nullable=True))
    op.add_column('products', sa.Column('is_gift_wrapped', sa.Boolean(), server_default='false', nullable=False))
    op.add_column('products', sa.Column('rating', sa.Float(), nullable=True))
    op.add_column('products', sa.Column('review_count', sa.Integer(), server_default='0', nullable=False))
    op.add_column('products', sa.Column('social_proof_text', sa.String(length=255), nullable=True))
    op.add_column('products', sa.Column('feature_list', postgresql.JSONB(astext_type=sa.Text()), nullable=True))

    # Add index for promo queries
    op.create_index('idx_products_promo_active', 'products', ['promo_end_date', 'is_active'], unique=False)

    # Remove marketing columns from scenarios table (if they exist)
    # Using batch_alter_table to handle potential column non-existence gracefully
    try:
        op.drop_index('idx_scenarios_promo_active', table_name='scenarios')
    except Exception:
        pass  # Index might not exist

    # Drop columns from scenarios (wrapped in try-except for safety)
    columns_to_drop = ['video_url', 'social_proof_text', 'review_count', 'is_gift_wrapped',
                       'promo_badge', 'feature_list', 'promo_end_date', 'rating']
    for col in columns_to_drop:
        try:
            op.drop_column('scenarios', col)
        except Exception:
            pass  # Column might not exist


def downgrade() -> None:
    # Add columns back to scenarios
    op.add_column('scenarios', sa.Column('rating', sa.DOUBLE_PRECISION(precision=53), server_default=sa.text("'0'::double precision"), nullable=True))
    op.add_column('scenarios', sa.Column('promo_end_date', postgresql.TIMESTAMP(timezone=True), nullable=True))
    op.add_column('scenarios', sa.Column('feature_list', postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'[]'::jsonb"), nullable=True))
    op.add_column('scenarios', sa.Column('promo_badge', sa.VARCHAR(length=100), nullable=True))
    op.add_column('scenarios', sa.Column('is_gift_wrapped', sa.BOOLEAN(), server_default=sa.text('false'), nullable=False))
    op.add_column('scenarios', sa.Column('review_count', sa.INTEGER(), server_default=sa.text('0'), nullable=False))
    op.add_column('scenarios', sa.Column('social_proof_text', sa.VARCHAR(length=255), nullable=True))
    op.add_column('scenarios', sa.Column('video_url', sa.TEXT(), nullable=True))

    # Recreate index
    op.create_index('idx_scenarios_promo_active', 'scenarios', ['promo_end_date', 'is_active'], unique=False)

    # Remove columns from products
    op.drop_index('idx_products_promo_active', table_name='products')
    op.drop_column('products', 'feature_list')
    op.drop_column('products', 'social_proof_text')
    op.drop_column('products', 'review_count')
    op.drop_column('products', 'rating')
    op.drop_column('products', 'is_gift_wrapped')
    op.drop_column('products', 'promo_end_date')
    op.drop_column('products', 'promo_badge')
    op.drop_column('products', 'video_url')
    op.drop_column('products', 'discounted_price')

"""add_product_type_and_type_specific_data_to_products

Revision ID: 091
Revises: 758718324cf7
Create Date: 2026-02-26 14:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


# revision identifiers, used by Alembic.
revision: str = '091'
down_revision: Union[str, None] = '758718324cf7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add product_type column to products table
    op.add_column('products',
        sa.Column('product_type', sa.String(50), nullable=False, server_default='story_book',
                  comment='Product type: story_book, coloring_book, audio_addon'))
    
    # Add type_specific_data JSONB column for flexible type-specific metadata
    op.add_column('products',
        sa.Column('type_specific_data', JSONB, nullable=True,
                  comment='Type-specific product data'))
    
    # Add index on product_type for filtering
    op.create_index('idx_products_type', 'products', ['product_type'])
    
    # Update all existing products to be story_book type (already defaulted by server_default)
    # This is just for explicit clarity
    op.execute("UPDATE products SET product_type = 'story_book' WHERE product_type IS NULL")


def downgrade() -> None:
    op.drop_index('idx_products_type', table_name='products')
    op.drop_column('products', 'type_specific_data')
    op.drop_column('products', 'product_type')

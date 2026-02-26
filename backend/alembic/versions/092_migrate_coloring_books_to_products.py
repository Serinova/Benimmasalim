"""migrate_coloring_books_to_products

Revision ID: 092
Revises: 091
Create Date: 2026-02-26 14:10:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB


# revision identifiers, used by Alembic.
revision: str = '092'
down_revision: Union[str, None] = '091'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Migrate data from coloring_book_products to products table.
    
    Strategy:
    1. Copy all coloring_book_products records to products
    2. Set product_type = 'coloring_book'
    3. Store line-art settings in type_specific_data JSONB
    4. Keep coloring_book_products table for backward compatibility (deprecated)
    """
    # Create temporary table to backup coloring book data (for rollback safety)
    op.execute("""
        CREATE TABLE IF NOT EXISTS coloring_book_products_backup AS 
        SELECT * FROM coloring_book_products
    """)
    
    # Migrate coloring_book_products to products table
    op.execute("""
        INSERT INTO products (
            id,
            name,
            slug,
            description,
            short_description,
            product_type,
            type_specific_data,
            base_price,
            discounted_price,
            extra_page_price,
            is_active,
            display_order,
            created_at,
            updated_at
        )
        SELECT 
            id,
            name,
            slug,
            description,
            NULL as short_description,
            'coloring_book' as product_type,
            jsonb_build_object(
                'line_art_method', COALESCE(line_art_method, 'canny'),
                'edge_threshold_low', COALESCE(edge_threshold_low, 80),
                'edge_threshold_high', COALESCE(edge_threshold_high, 200),
                'page_template_id', page_template_id::text
            ) as type_specific_data,
            base_price,
            discounted_price,
            0 as extra_page_price,
            active as is_active,
            0 as display_order,
            created_at,
            updated_at
        FROM coloring_book_products
        ON CONFLICT (id) DO NOTHING
    """)
    
    # Add comment to coloring_book_products table marking it as deprecated
    op.execute("""
        COMMENT ON TABLE coloring_book_products IS 
        'DEPRECATED: Use products table with product_type=coloring_book. Kept for backward compatibility.'
    """)


def downgrade() -> None:
    """
    Rollback: Remove migrated coloring books from products table.
    """
    # Delete coloring book products from products table
    op.execute("DELETE FROM products WHERE product_type = 'coloring_book'")
    
    # Drop backup table
    op.execute("DROP TABLE IF EXISTS coloring_book_products_backup")

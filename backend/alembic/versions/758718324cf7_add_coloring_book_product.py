"""add_coloring_book_product

Revision ID: 758718324cf7
Revises: 68f0daf6de81
Create Date: 2026-02-26 05:59:50.447413

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision: str = '758718324cf7'
down_revision: Union[str, None] = '68f0daf6de81'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create coloring_book_products table
    op.create_table(
        'coloring_book_products',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('slug', sa.String(255), unique=True, nullable=False),
        sa.Column('description', sa.Text),
        
        # Pricing
        sa.Column('base_price', sa.Numeric(10, 2), nullable=False),
        sa.Column('discounted_price', sa.Numeric(10, 2)),
        
        # Line-art conversion settings (optimized for simple, kid-friendly coloring)
        sa.Column('line_art_method', sa.String(50), server_default='canny'),
        sa.Column('edge_threshold_low', sa.Integer, server_default='80'),  # Higher = fewer details
        sa.Column('edge_threshold_high', sa.Integer, server_default='200'),  # Higher = simpler shapes
        
        # Page template reference
        sa.Column('page_template_id', UUID(as_uuid=True), sa.ForeignKey('page_templates.id', ondelete='SET NULL')),
        
        sa.Column('active', sa.Boolean, server_default='true'),
        sa.Column('created_at', sa.DateTime, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime, server_default=sa.text('now()'), onupdate=sa.text('now()')),
    )
    
    # Add coloring_book relationship to orders
    op.add_column('orders', 
        sa.Column('coloring_book_order_id', UUID(as_uuid=True),
                  sa.ForeignKey('orders.id', ondelete='SET NULL')))
    
    op.add_column('orders',
        sa.Column('is_coloring_book', sa.Boolean, server_default='false'))
    
    # Add coloring book flag to story_previews
    op.add_column('story_previews',
        sa.Column('has_coloring_book', sa.Boolean, server_default='false'))


def downgrade() -> None:
    op.drop_column('story_previews', 'has_coloring_book')
    op.drop_column('orders', 'is_coloring_book')
    op.drop_column('orders', 'coloring_book_order_id')
    op.drop_table('coloring_book_products')

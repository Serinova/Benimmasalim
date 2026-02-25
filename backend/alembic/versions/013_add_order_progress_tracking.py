"""Add progress tracking fields to orders.

Revision ID: 013_add_progress
Revises: f8ff49df653d
Create Date: 2024-02-03

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '013_add_progress'
down_revision = 'f8ff49df653d'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add progress tracking columns to orders table."""
    # Add completed_pages column
    op.add_column(
        'orders',
        sa.Column('completed_pages', sa.Integer(), nullable=False, server_default='0')
    )
    
    # Add total_pages column
    op.add_column(
        'orders',
        sa.Column('total_pages', sa.Integer(), nullable=False, server_default='16')
    )
    
    # Add generation_started_at column
    op.add_column(
        'orders',
        sa.Column('generation_started_at', sa.DateTime(timezone=True), nullable=True)
    )
    
    # Add generation_error column
    op.add_column(
        'orders',
        sa.Column('generation_error', sa.Text(), nullable=True)
    )
    
    # Add index for stuck order detection
    op.create_index(
        'idx_orders_stuck_processing',
        'orders',
        ['generation_started_at'],
        postgresql_where="status = 'PROCESSING' AND generation_started_at IS NOT NULL"
    )


def downgrade() -> None:
    """Remove progress tracking columns from orders table."""
    op.drop_index('idx_orders_stuck_processing', table_name='orders')
    op.drop_column('orders', 'generation_error')
    op.drop_column('orders', 'generation_started_at')
    op.drop_column('orders', 'total_pages')
    op.drop_column('orders', 'completed_pages')

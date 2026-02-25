"""Update order_pages for page-based preview system

Revision ID: 003
Revises: 002
Create Date: 2026-01-30

"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()

    # Check if table exists
    result = conn.execute(sa.text(
        "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'order_pages')"
    ))
    table_exists = result.scalar()

    if not table_exists:
        return

    # Get columns
    result = conn.execute(sa.text(
        "SELECT column_name FROM information_schema.columns WHERE table_name = 'order_pages'"
    ))
    columns = [row[0] for row in result]

    # Rename ai_prompt to image_prompt if it exists
    if 'ai_prompt' in columns and 'image_prompt' not in columns:
        op.alter_column('order_pages', 'ai_prompt', new_column_name='image_prompt', nullable=True)

    # Add preview_image_url column if not exists
    if 'preview_image_url' not in columns:
        op.add_column('order_pages', sa.Column('preview_image_url', sa.Text(), nullable=True))

    # Update status column
    if 'image_generation_status' in columns:
        op.drop_column('order_pages', 'image_generation_status')

    if 'status' not in columns:
        op.add_column('order_pages', sa.Column('status', sa.String(30), server_default='PENDING', nullable=False))

    # Handle indexes using raw SQL with IF EXISTS
    conn.execute(sa.text("DROP INDEX IF EXISTS idx_pages_status"))

    # Create new index
    conn.execute(sa.text(
        "CREATE INDEX IF NOT EXISTS idx_pages_status ON order_pages (status) WHERE status != 'FULL_GENERATED'"
    ))


def downgrade() -> None:
    conn = op.get_bind()

    # Check if table exists
    result = conn.execute(sa.text(
        "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'order_pages')"
    ))
    table_exists = result.scalar()

    if not table_exists:
        return

    # Get columns
    result = conn.execute(sa.text(
        "SELECT column_name FROM information_schema.columns WHERE table_name = 'order_pages'"
    ))
    columns = [row[0] for row in result]

    # Drop index
    conn.execute(sa.text("DROP INDEX IF EXISTS idx_pages_status"))

    # Revert status column
    if 'status' in columns:
        op.drop_column('order_pages', 'status')

    if 'image_generation_status' not in columns:
        op.add_column('order_pages', sa.Column('image_generation_status', sa.String(20), server_default='pending', nullable=False))

    # Create old index
    conn.execute(sa.text(
        "CREATE INDEX IF NOT EXISTS idx_pages_status ON order_pages (image_generation_status) WHERE image_generation_status != 'completed'"
    ))

    # Drop preview_image_url
    if 'preview_image_url' in columns:
        op.drop_column('order_pages', 'preview_image_url')

    # Rename image_prompt back to ai_prompt
    if 'image_prompt' in columns and 'ai_prompt' not in columns:
        op.alter_column('order_pages', 'image_prompt', new_column_name='ai_prompt', nullable=False)

"""Initial database schema

Revision ID: 001
Revises: 
Create Date: 2026-01-30

"""
from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Users table
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('email', sa.String(255), nullable=True),
        sa.Column('hashed_password', sa.String(255), nullable=True),
        sa.Column('full_name', sa.String(255), nullable=True),
        sa.Column('phone', sa.String(20), nullable=True),
        sa.Column('google_id', sa.String(255), nullable=True),
        sa.Column('avatar_url', sa.Text(), nullable=True),
        sa.Column('is_guest', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('role', sa.String(20), server_default='user', nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email'),
        sa.UniqueConstraint('google_id'),
    )
    op.create_index('idx_users_email', 'users', ['email'], postgresql_where=sa.text('email IS NOT NULL'))
    op.create_index('idx_users_google', 'users', ['google_id'], postgresql_where=sa.text('google_id IS NOT NULL'))

    # Products table
    op.create_table(
        'products',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('width_mm', sa.Float(), nullable=False),
        sa.Column('height_mm', sa.Float(), nullable=False),
        sa.Column('bleed_mm', sa.Float(), server_default='3.0', nullable=False),
        sa.Column('default_page_count', sa.Integer(), server_default='16', nullable=False),
        sa.Column('min_page_count', sa.Integer(), server_default='12', nullable=False),
        sa.Column('max_page_count', sa.Integer(), server_default='32', nullable=False),
        sa.Column('paper_type', sa.String(100), server_default="'Kuşe 170gr'", nullable=False),
        sa.Column('paper_finish', sa.String(50), server_default="'Mat'", nullable=False),
        sa.Column('cover_type', sa.String(50), server_default="'Sert Kapak'", nullable=False),
        sa.Column('lamination', sa.String(50), nullable=True),
        sa.Column('base_price', sa.Numeric(10, 2), nullable=False),
        sa.Column('production_cost', sa.Numeric(10, 2), nullable=True),
        sa.Column('ai_instructions', sa.Text(), nullable=True),
        sa.Column('print_specifications', postgresql.JSONB(), nullable=True),
        sa.Column('has_overlay', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('overlay_url', sa.Text(), nullable=True),
        sa.Column('overlay_position', sa.String(20), server_default="'center'", nullable=False),
        sa.Column('overlay_opacity', sa.Float(), server_default='1.0', nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('is_featured', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('display_order', sa.Integer(), server_default='0', nullable=False),
        sa.Column('stock_status', sa.String(20), server_default="'available'", nullable=False),
        sa.Column('thumbnail_url', sa.Text(), nullable=False),
        sa.Column('sample_pdf_url', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name'),
        sa.CheckConstraint('width_mm > 0', name='check_positive_width'),
        sa.CheckConstraint('height_mm > 0', name='check_positive_height'),
        sa.CheckConstraint('base_price > 0', name='check_positive_price'),
    )
    op.create_index('idx_products_active', 'products', ['is_active', 'display_order'])
    op.create_index('idx_products_featured', 'products', ['is_featured'], postgresql_where=sa.text('is_featured = true'))

    # Scenarios table
    op.create_table(
        'scenarios',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('thumbnail_url', sa.Text(), nullable=False),
        sa.Column('ai_prompt_template', sa.Text(), nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('display_order', sa.Integer(), server_default='0', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name'),
    )
    op.create_index('idx_scenarios_active_order', 'scenarios', ['is_active', 'display_order'])

    # Learning outcomes table
    op.create_table(
        'learning_outcomes',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('category', sa.String(50), nullable=False),
        sa.Column('age_group', sa.String(20), server_default="'5-10'", nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name'),
    )
    op.create_index('idx_outcomes_category', 'learning_outcomes', ['category', 'is_active'])

    # Visual styles table
    op.create_table(
        'visual_styles',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('thumbnail_url', sa.Text(), nullable=False),
        sa.Column('prompt_modifier', sa.Text(), nullable=False),
        sa.Column('cover_aspect_ratio', sa.String(10), server_default="'2:3'", nullable=False),
        sa.Column('page_aspect_ratio', sa.String(10), server_default="'1:1'", nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name'),
    )

    # Orders table
    op.create_table(
        'orders',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('product_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('scenario_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('visual_style_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('child_name', sa.String(255), nullable=False),
        sa.Column('child_age', sa.Integer(), nullable=False),
        sa.Column('child_gender', sa.String(10), nullable=True),
        sa.Column('selected_outcomes', postgresql.ARRAY(sa.String()), nullable=False),
        sa.Column('status', sa.String(50), server_default="'DRAFT'", nullable=False),
        sa.Column('payment_id', sa.String(100), nullable=True),
        sa.Column('payment_amount', sa.Numeric(10, 2), nullable=True),
        sa.Column('payment_status', sa.String(50), nullable=True),
        sa.Column('payment_provider', sa.String(50), server_default="'iyzico'", nullable=False),
        sa.Column('shipping_address', postgresql.JSONB(), nullable=True),
        sa.Column('tracking_number', sa.String(100), nullable=True),
        sa.Column('carrier', sa.String(50), nullable=True),
        sa.Column('child_photo_url', sa.Text(), nullable=True),
        sa.Column('face_embedding', postgresql.ARRAY(sa.Numeric()), nullable=True),
        sa.Column('final_pdf_url', sa.Text(), nullable=True),
        sa.Column('has_audio_book', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('audio_type', sa.String(20), nullable=True),
        sa.Column('audio_voice_id', sa.String(100), nullable=True),
        sa.Column('audio_file_url', sa.Text(), nullable=True),
        sa.Column('qr_code_url', sa.Text(), nullable=True),
        sa.Column('cover_regenerate_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('max_cover_regenerate', sa.Integer(), server_default='3', nullable=False),
        sa.Column('delivered_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('photo_deletion_scheduled_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['product_id'], ['products.id']),
        sa.ForeignKeyConstraint(['scenario_id'], ['scenarios.id']),
        sa.ForeignKeyConstraint(['visual_style_id'], ['visual_styles.id']),
        sa.UniqueConstraint('payment_id'),
        sa.CheckConstraint('child_age >= 5 AND child_age <= 10', name='valid_child_age'),
    )
    op.create_index('idx_orders_user', 'orders', ['user_id'])
    op.create_index('idx_orders_status', 'orders', ['status'])
    op.create_index('idx_orders_payment', 'orders', ['payment_id'], postgresql_where=sa.text('payment_id IS NOT NULL'))
    op.create_index('idx_orders_delivered', 'orders', ['delivered_at'], postgresql_where=sa.text('delivered_at IS NOT NULL'))
    op.create_index('idx_kvkk_cleanup', 'orders', ['photo_deletion_scheduled_at'], postgresql_where=sa.text('photo_deletion_scheduled_at IS NOT NULL'))

    # Order pages table
    op.create_table(
        'order_pages',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('order_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('page_number', sa.Integer(), nullable=False),
        sa.Column('text_content', sa.Text(), nullable=True),
        sa.Column('ai_prompt', sa.Text(), nullable=False),
        sa.Column('image_url', sa.Text(), nullable=True),
        sa.Column('image_generation_status', sa.String(20), server_default="'pending'", nullable=False),
        sa.Column('is_cover', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('is_regenerated', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('generation_attempt', sa.Integer(), server_default='1', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['order_id'], ['orders.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('order_id', 'page_number', name='unique_page_per_order'),
    )
    op.create_index('idx_pages_order', 'order_pages', ['order_id'])
    op.create_index('idx_pages_status', 'order_pages', ['image_generation_status'], postgresql_where=sa.text("image_generation_status != 'completed'"))

    # Audit logs table
    op.create_table(
        'audit_logs',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('action', sa.String(100), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('order_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('admin_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('details', postgresql.JSONB(), nullable=True),
        sa.Column('ip_address', postgresql.INET(), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['order_id'], ['orders.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['admin_id'], ['users.id'], ondelete='SET NULL'),
    )
    op.create_index('idx_logs_action', 'audit_logs', ['action', 'created_at'])
    op.create_index('idx_logs_order', 'audit_logs', ['order_id'], postgresql_where=sa.text('order_id IS NOT NULL'))
    op.create_index('idx_logs_created', 'audit_logs', ['created_at'])


def downgrade() -> None:
    op.drop_table('audit_logs')
    op.drop_table('order_pages')
    op.drop_table('orders')
    op.drop_table('visual_styles')
    op.drop_table('learning_outcomes')
    op.drop_table('scenarios')
    op.drop_table('products')
    op.drop_table('users')

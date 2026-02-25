"""Update products with template references

Revision ID: 006
Revises: 005
Create Date: 2025-01-30
"""
from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '006'
down_revision: str | None = '005'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Add new columns to products table (all nullable first)
    op.execute("ALTER TABLE products ADD COLUMN IF NOT EXISTS slug VARCHAR(255)")
    op.execute("ALTER TABLE products ADD COLUMN IF NOT EXISTS short_description VARCHAR(500)")
    op.execute("ALTER TABLE products ADD COLUMN IF NOT EXISTS cover_template_id UUID")
    op.execute("ALTER TABLE products ADD COLUMN IF NOT EXISTS inner_template_id UUID")
    op.execute("ALTER TABLE products ADD COLUMN IF NOT EXISTS back_template_id UUID")
    op.execute("ALTER TABLE products ADD COLUMN IF NOT EXISTS ai_config_id UUID")
    op.execute("ALTER TABLE products ADD COLUMN IF NOT EXISTS extra_page_price NUMERIC(10,2) DEFAULT 5.0")
    op.execute("ALTER TABLE products ADD COLUMN IF NOT EXISTS gallery_images JSONB")

    # Update existing products with slug from name
    op.execute("""
        UPDATE products 
        SET slug = LOWER(REPLACE(REPLACE(REPLACE(name, ' ', '-'), 'İ', 'i'), 'ı', 'i'))
        WHERE slug IS NULL OR slug = ''
    """)

    # Set default slug for any remaining null slugs
    op.execute("""
        UPDATE products 
        SET slug = CONCAT('product-', id::text)
        WHERE slug IS NULL OR slug = ''
    """)

    # Now make slug NOT NULL
    op.execute("ALTER TABLE products ALTER COLUMN slug SET NOT NULL")

    # Make thumbnail_url nullable
    op.execute("ALTER TABLE products ALTER COLUMN thumbnail_url DROP NOT NULL")

    # Add foreign key constraints
    op.execute("""
        DO $$ BEGIN
            ALTER TABLE products ADD CONSTRAINT fk_products_cover_template 
            FOREIGN KEY (cover_template_id) REFERENCES page_templates(id) ON DELETE SET NULL;
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$
    """)
    op.execute("""
        DO $$ BEGIN
            ALTER TABLE products ADD CONSTRAINT fk_products_inner_template 
            FOREIGN KEY (inner_template_id) REFERENCES page_templates(id) ON DELETE SET NULL;
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$
    """)
    op.execute("""
        DO $$ BEGIN
            ALTER TABLE products ADD CONSTRAINT fk_products_back_template 
            FOREIGN KEY (back_template_id) REFERENCES page_templates(id) ON DELETE SET NULL;
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$
    """)
    op.execute("""
        DO $$ BEGIN
            ALTER TABLE products ADD CONSTRAINT fk_products_ai_config 
            FOREIGN KEY (ai_config_id) REFERENCES ai_generation_configs(id) ON DELETE SET NULL;
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$
    """)

    # Create unique index on slug
    op.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_products_slug ON products(slug)")

    # Drop old columns that are now in page_templates (if they exist)
    op.execute("ALTER TABLE products DROP COLUMN IF EXISTS width_mm")
    op.execute("ALTER TABLE products DROP COLUMN IF EXISTS height_mm")
    op.execute("ALTER TABLE products DROP COLUMN IF EXISTS bleed_mm")
    op.execute("ALTER TABLE products DROP COLUMN IF EXISTS ai_instructions")
    op.execute("ALTER TABLE products DROP COLUMN IF EXISTS has_overlay")
    op.execute("ALTER TABLE products DROP COLUMN IF EXISTS overlay_url")
    op.execute("ALTER TABLE products DROP COLUMN IF EXISTS overlay_position")
    op.execute("ALTER TABLE products DROP COLUMN IF EXISTS overlay_opacity")
    op.execute("ALTER TABLE products DROP COLUMN IF EXISTS sample_pdf_url")

    # Drop old constraints (if they exist)
    op.execute("ALTER TABLE products DROP CONSTRAINT IF EXISTS check_positive_width")
    op.execute("ALTER TABLE products DROP CONSTRAINT IF EXISTS check_positive_height")


def downgrade() -> None:
    # Drop foreign key constraints
    op.execute("ALTER TABLE products DROP CONSTRAINT IF EXISTS fk_products_cover_template")
    op.execute("ALTER TABLE products DROP CONSTRAINT IF EXISTS fk_products_inner_template")
    op.execute("ALTER TABLE products DROP CONSTRAINT IF EXISTS fk_products_back_template")
    op.execute("ALTER TABLE products DROP CONSTRAINT IF EXISTS fk_products_ai_config")

    # Drop index
    op.execute("DROP INDEX IF EXISTS idx_products_slug")

    # Drop new columns
    op.execute("ALTER TABLE products DROP COLUMN IF EXISTS slug")
    op.execute("ALTER TABLE products DROP COLUMN IF EXISTS short_description")
    op.execute("ALTER TABLE products DROP COLUMN IF EXISTS cover_template_id")
    op.execute("ALTER TABLE products DROP COLUMN IF EXISTS inner_template_id")
    op.execute("ALTER TABLE products DROP COLUMN IF EXISTS back_template_id")
    op.execute("ALTER TABLE products DROP COLUMN IF EXISTS ai_config_id")
    op.execute("ALTER TABLE products DROP COLUMN IF EXISTS extra_page_price")
    op.execute("ALTER TABLE products DROP COLUMN IF EXISTS gallery_images")

    # Add back old columns
    op.execute("ALTER TABLE products ADD COLUMN IF NOT EXISTS width_mm FLOAT")
    op.execute("ALTER TABLE products ADD COLUMN IF NOT EXISTS height_mm FLOAT")
    op.execute("ALTER TABLE products ADD COLUMN IF NOT EXISTS bleed_mm FLOAT DEFAULT 3.0")

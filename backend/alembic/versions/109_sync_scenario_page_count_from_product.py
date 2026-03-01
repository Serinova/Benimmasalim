"""Sync scenario default_page_count and story_page_count from linked product.

Senaryolar ürün yönetiminde yatay A4'ye bağlı; sayfa sayısı şablondan (product) gelmeli.
linked_product_id'si olan tüm senaryolarda default_page_count ve story_page_count
ürünün default_page_count değerine çekiliyor; böylece hepsi tutarlı (örn. 22) görünür.

Revision ID: 109_sync_scenario_page_from_product
Revises: 108_fill_remaining_scenario_marketing
Create Date: 2026-03-01

"""
from alembic import op
import sqlalchemy as sa

revision = "109_sync_scenario_page_from_product"
down_revision = "108_fill_remaining_scenario_marketing"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    # linked_product_id'si olan senaryolarda default_page_count ve story_page_count'ı
    # ürünün default_page_count'ına eşitle (story_page_count null ise ürün değerini kullan)
    conn.execute(
        sa.text("""
            UPDATE scenarios s
            SET
                default_page_count = p.default_page_count,
                story_page_count = COALESCE(s.story_page_count, p.default_page_count)
            FROM products p
            WHERE s.linked_product_id = p.id
              AND p.default_page_count IS NOT NULL
              AND p.default_page_count >= 4
        """)
    )


def downgrade() -> None:
    # Geri alınamaz: hangi senaryonun eski değeri neydi bilinmiyor
    pass

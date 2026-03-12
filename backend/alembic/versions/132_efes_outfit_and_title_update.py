"""Efes Antik Kent: senaryo adı, kitap adı formatı, cinsiyete özel kıyafet güncellemesi.

- Senaryo adı: "Efes Antik Kent Macerası"
- Kitap adı: "[Çocuk adı]'ın Efes Antik Kent Macerası"
- Kız kıyafeti: Kaşif tarzı feminen — uzun pantolon, macera yeleği
- Erkek kıyafeti: Macera tarzı — cargo pantolon, düğmeli gömlek

Revision ID: 132_efes_outfit_title
Revises: 131_set_cover_title_source_gemini
Create Date: 2026-03-07
"""
from collections.abc import Sequence

from alembic import op
from sqlalchemy.sql import text

revision: str = "132_efes_outfit_title"
down_revision: str = "131_set_cover_title_source_gemini"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

NEW_NAME = "Efes Antik Kent Macerası"

# Kız: Kaşif tarzı ama feminen — antik kent macerası ruhu
# Mini etek / kısa short YOK — uzun kalem pantolon + kemerli macera yelek
OUTFIT_GIRL = (
    "terracotta orange adventure vest with golden compass embroidery over a cream cotton blouse, "
    "olive green slim cargo trousers with knee patch details, brown leather ankle boots with brass buckles, "
    "a woven straw sun hat with a terracotta ribbon, small tan leather explorer satchel across shoulder. "
    "EXACTLY the same outfit on every page — same orange vest, same cream blouse, same olive trousers, same brown boots, same straw hat."
)

# Erkek: Macera/kaşif tarzı — antik kent gezgini Indiana Jones ilham
OUTFIT_BOY = (
    "deep burgundy linen button-up shirt with rolled-up sleeves and a small golden key pendant necklace, "
    "khaki cargo trousers with leather belt and antique bronze buckle, dark brown leather lace-up boots, "
    "a sand-colored canvas messenger bag with brass clasp slung across chest, worn brown leather wristband. "
    "EXACTLY the same outfit on every page — same burgundy shirt, same khaki trousers, same brown boots, same canvas bag."
)

# Hikaye prompt'undaki başlık talimatını güncelle
TITLE_FIX_PATCH = """
- Kitap adı SADECE "[Çocuk adı]'ın Efes Antik Kent Macerası". Alt başlık ekleme.
""".strip()


def upgrade() -> None:
    conn = op.get_bind()
    conn.execute(
        text("""
            UPDATE scenarios
            SET name = :name,
                outfit_girl = :outfit_girl,
                outfit_boy = :outfit_boy
            WHERE theme_key = 'ephesus'
               OR theme_key = 'ephesus_ancient_city'
               OR name ILIKE '%Efes%'
        """),
        {
            "name": NEW_NAME,
            "outfit_girl": OUTFIT_GIRL,
            "outfit_boy": OUTFIT_BOY,
        },
    )
    # story_prompt_tr içindeki eski başlık talimatını güncelle
    conn.execute(
        text("""
            UPDATE scenarios
            SET story_prompt_tr = REPLACE(
                story_prompt_tr,
                '- Kitap adı SADECE "[Çocuk adı]''ın Efes Antik Kenti". Alt başlık ekleme.',
                :new_title_line
            )
            WHERE (theme_key = 'ephesus' OR name ILIKE '%Efes%')
              AND story_prompt_tr LIKE '%Efes Antik Kenti%'
        """),
        {"new_title_line": TITLE_FIX_PATCH},
    )
    # story_prompt_tr başlık satırlarını güncelle (farklı varyasyonlar)
    conn.execute(
        text("""
            UPDATE scenarios
            SET story_prompt_tr = REPLACE(
                story_prompt_tr,
                '"[Çocuk adı]''ın Efes Antik Kenti"',
                '"[Çocuk adı]''ın Efes Antik Kent Macerası"'
            )
            WHERE (theme_key = 'ephesus' OR name ILIKE '%Efes%')
              AND story_prompt_tr LIKE '%Efes Antik Kenti%'
        """),
    )


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(
        text("""
            UPDATE scenarios
            SET name = 'Efes Antik Kenti'
            WHERE theme_key = 'ephesus'
               OR name ILIKE '%Efes Antik Kent Macerası%'
        """),
    )

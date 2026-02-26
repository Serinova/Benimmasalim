"""add_audio_addon_products

Revision ID: 093
Revises: 092
Create Date: 2026-02-26 14:20:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID


# revision identifiers, used by Alembic.
revision: str = '093'
down_revision: Union[str, None] = '092'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Add audio addon products for system and cloned voice options.
    These replace hardcoded pricing in payments.py
    """
    # Insert System Voice Audio Addon
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
            is_featured,
            display_order,
            default_page_count,
            min_page_count,
            max_page_count
        ) VALUES (
            gen_random_uuid(),
            'Sesli Kitap - Sistem Sesi',
            'audio-addon-system-voice',
            'Hikayenizi profesyonel sistem sesiyle dinleyin. Kaliteli yapay zeka seslendirmesi ile kitabınız ses kazanıyor.',
            'Profesyonel sistem sesiyle sesli kitap',
            'audio_addon',
            '{"audio_type": "system", "voice_quality": "premium", "languages": ["tr"]}' ::jsonb,
            150.00,
            NULL,
            0,
            true,
            false,
            100,
            16,
            16,
            40
        )
        ON CONFLICT (slug) DO UPDATE SET
            base_price = EXCLUDED.base_price,
            is_active = EXCLUDED.is_active,
            updated_at = now()
    """)
    
    # Insert Cloned Voice Audio Addon
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
            is_featured,
            display_order,
            default_page_count,
            min_page_count,
            max_page_count
        ) VALUES (
            gen_random_uuid(),
            'Sesli Kitap - Klonlanmış Ses',
            'audio-addon-cloned-voice',
            'Kendi sesinizi veya sevdiklerinizin sesini klonlayarak hikayeyi seslendirin. Tamamen kişisel ve duygusal bir deneyim.',
            'Kendi sesinizle özel sesli kitap',
            'audio_addon',
            '{"audio_type": "cloned", "voice_quality": "ultra", "requires_sample": true, "languages": ["tr"]}' ::jsonb,
            300.00,
            NULL,
            0,
            true,
            true,
            101,
            16,
            16,
            40
        )
        ON CONFLICT (slug) DO UPDATE SET
            base_price = EXCLUDED.base_price,
            is_active = EXCLUDED.is_active,
            updated_at = now()
    """)


def downgrade() -> None:
    """Remove audio addon products"""
    op.execute("DELETE FROM products WHERE product_type = 'audio_addon'")

"""add_solar_system_adventure_scenario

Revision ID: 45d82b3c9171
Revises: 6ac798b22980
Create Date: 2026-02-25 21:35:03.809297

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '45d82b3c9171'
down_revision: Union[str, None] = '6ac798b22980'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add Güneş Sistemi Macerası: Gezegen Kaşifleri scenario."""
    from scripts.update_space_scenario import (
        SPACE_COVER_PROMPT,
        SPACE_PAGE_PROMPT,
        SPACE_STORY_PROMPT_TR,
        SPACE_CULTURAL_ELEMENTS,
        SPACE_CUSTOM_INPUTS,
        OUTFIT_GIRL,
        OUTFIT_BOY,
    )
    import json

    conn = op.get_bind()

    # Check if scenario already exists
    result = conn.execute(
        sa.text(
            "SELECT id FROM scenarios WHERE name ILIKE '%Güneş Sistemi%' "
            "OR theme_key = 'solar_system_space' LIMIT 1"
        )
    )
    existing = result.fetchone()

    marketing_features = json.dumps([
        "8 gezegeni keşfet",
        "Robot arkadaşla bilimsel veri toplama",
        "Mars'ta yürüyüş deneyimi",
        "Jüpiter fırtınasını görme",
        "Satürn halkalarında süzülme",
        "NASA tarzı bilimsel macera",
    ])

    if existing:
        # Update existing
        conn.execute(
            sa.text("""
                UPDATE scenarios SET
                    description = :description,
                    thumbnail_url = :thumbnail,
                    cover_prompt_template = :cover_prompt,
                    page_prompt_template = :page_prompt,
                    story_prompt_tr = :story_prompt,
                    location_en = :location_en,
                    theme_key = :theme_key,
                    cultural_elements = :cultural_elements,
                    custom_inputs_schema = :custom_inputs,
                    outfit_girl = :outfit_girl,
                    outfit_boy = :outfit_boy,
                    default_page_count = :page_count,
                    is_active = true,
                    display_order = :display_order,
                    marketing_badge = :marketing_badge,
                    age_range = :age_range,
                    tagline = :tagline,
                    marketing_features = :marketing_features,
                    estimated_duration = :estimated_duration,
                    marketing_price_label = :marketing_price_label,
                    rating = :rating
                WHERE name ILIKE '%Güneş Sistemi%' OR theme_key = 'solar_system_space'
            """),
            {
                "description": "Uzay istasyonundan Güneş Sistemi turuna çık! 8 gezegeni keşfet, AI robot arkadaşınla bilimsel veriler topla. Mars'ta yürü, Jüpiter fırtınasını gör, Satürn halkalarında süzül!",
                "thumbnail": "https://storage.googleapis.com/benimmasalim-generated-books/scenarios/solar-system-default.jpg",
                "cover_prompt": SPACE_COVER_PROMPT,
                "page_prompt": SPACE_PAGE_PROMPT,
                "story_prompt": SPACE_STORY_PROMPT_TR,
                "location_en": "Solar System",
                "theme_key": "solar_system_space",
                "cultural_elements": json.dumps(SPACE_CULTURAL_ELEMENTS),
                "custom_inputs": json.dumps(SPACE_CUSTOM_INPUTS),
                "outfit_girl": OUTFIT_GIRL,
                "outfit_boy": OUTFIT_BOY,
                "page_count": 22,
                "display_order": 15,
                "marketing_badge": "Bilimsel Keşif",
                "age_range": "6-10 yaş",
                "tagline": "Güneş Sistemi'nde 8 gezegeni keşfet! NASA tarzı bilimsel macera",
                "marketing_features": marketing_features,
                "estimated_duration": "20-25 dakika okuma",
                "marketing_price_label": "299 TL'den başlayan fiyatlarla",
                "rating": 5.0,
            }
        )
        print("OK: Gunes Sistemi Macerasi senaryosu guncellendi")
    else:
        # Create new
        product_result = conn.execute(
            sa.text("SELECT id FROM products WHERE name ILIKE '%A4%YATAY%32%' LIMIT 1")
        )
        product_row = product_result.fetchone()
        linked_product_id = product_row[0] if product_row else None

        conn.execute(
            sa.text("""
                INSERT INTO scenarios (
                    id, name, description, thumbnail_url,
                    cover_prompt_template, page_prompt_template, story_prompt_tr,
                    location_en, theme_key, cultural_elements, custom_inputs_schema,
                    outfit_girl, outfit_boy, default_page_count,
                    linked_product_id, is_active, display_order,
                    marketing_badge, age_range, tagline, marketing_features,
                    estimated_duration, marketing_price_label, rating,
                    created_at, updated_at
                ) VALUES (
                    gen_random_uuid(), :name, :description, :thumbnail,
                    :cover_prompt, :page_prompt, :story_prompt,
                    :location_en, :theme_key, :cultural_elements, :custom_inputs,
                    :outfit_girl, :outfit_boy, :page_count,
                    :linked_product_id, true, :display_order,
                    :marketing_badge, :age_range, :tagline, :marketing_features,
                    :estimated_duration, :marketing_price_label, :rating,
                    now(), now()
                )
            """),
            {
                "name": "Güneş Sistemi Macerası: Gezegen Kaşifleri",
                "description": "Uzay istasyonundan Güneş Sistemi turuna çık! 8 gezegeni keşfet, AI robot arkadaşınla bilimsel veriler topla. Mars'ta yürü, Jüpiter fırtınasını gör, Satürn halkalarında süzül!",
                "thumbnail": "https://storage.googleapis.com/benimmasalim-generated-books/scenarios/solar-system-default.jpg",
                "cover_prompt": SPACE_COVER_PROMPT,
                "page_prompt": SPACE_PAGE_PROMPT,
                "story_prompt": SPACE_STORY_PROMPT_TR,
                "location_en": "Solar System",
                "theme_key": "solar_system_space",
                "cultural_elements": json.dumps(SPACE_CULTURAL_ELEMENTS),
                "custom_inputs": json.dumps(SPACE_CUSTOM_INPUTS),
                "outfit_girl": OUTFIT_GIRL,
                "outfit_boy": OUTFIT_BOY,
                "page_count": 22,
                "linked_product_id": linked_product_id,
                "display_order": 15,
                "marketing_badge": "Bilimsel Keşif",
                "age_range": "6-10 yaş",
                "tagline": "Güneş Sistemi'nde 8 gezegeni keşfet! NASA tarzı bilimsel macera",
                "marketing_features": marketing_features,
                "estimated_duration": "20-25 dakika okuma",
                "marketing_price_label": "299 TL'den başlayan fiyatlarla",
                "rating": 5.0,
            }
        )
        print("OK: Gunes Sistemi Macerasi senaryosu olusturuldu")


def downgrade() -> None:
    """Remove Güneş Sistemi Macerası scenario."""
    conn = op.get_bind()
    conn.execute(
        sa.text(
            "DELETE FROM scenarios WHERE name ILIKE '%Güneş Sistemi%' "
            "OR theme_key = 'solar_system_space'"
        )
    )

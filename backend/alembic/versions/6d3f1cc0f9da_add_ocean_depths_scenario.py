"""add_ocean_depths_scenario

Revision ID: 6d3f1cc0f9da
Revises: 45d82b3c9171
Create Date: 2026-02-25 22:18:32.006276

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6d3f1cc0f9da'
down_revision: Union[str, None] = '45d82b3c9171'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add Okyanus Derinlikleri: Mavi Dev ile Macera scenario."""
    from scripts.update_ocean_adventure_scenario import (
        OCEAN_COVER_PROMPT,
        OCEAN_PAGE_PROMPT,
        OCEAN_STORY_PROMPT_TR,
        OCEAN_CULTURAL_ELEMENTS,
        OCEAN_CUSTOM_INPUTS,
        OUTFIT_GIRL,
        OUTFIT_BOY,
    )
    import json

    conn = op.get_bind()
    
    print("[DEBUG] Starting ocean depths scenario migration...")
    print(f"[DEBUG] OCEAN_CUSTOM_INPUTS type: {type(OCEAN_CUSTOM_INPUTS)}")
    print(f"[DEBUG] OCEAN_CUSTOM_INPUTS length: {len(OCEAN_CUSTOM_INPUTS)}")
    print(f"[DEBUG] OCEAN_CUSTOM_INPUTS value: {OCEAN_CUSTOM_INPUTS[:200] if len(str(OCEAN_CUSTOM_INPUTS)) > 200 else OCEAN_CUSTOM_INPUTS}")

    # Check if scenario already exists
    result = conn.execute(
        sa.text(
            "SELECT id FROM scenarios WHERE name ILIKE '%Okyanus%' "
            "OR theme_key = 'ocean_depths' LIMIT 1"
        )
    )
    existing = result.fetchone()
    
    print(f"[DEBUG] Existing scenario: {existing}")

    marketing_features = json.dumps([
        "Devasa mavi balina karşılaşması",
        "Yunus arkadaşla yüzme",
        "5 farklı derinlik seviyesi",
        "Fosforlu canlılar (biyolüminesans)",
        "Denizaltı + dalgıç deneyimi",
        "Okyanus bilimi ve çevre bilinci",
    ])
    
    custom_inputs_json = json.dumps(OCEAN_CUSTOM_INPUTS)
    print(f"[DEBUG] custom_inputs_json: {custom_inputs_json[:200]}")

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
                WHERE name ILIKE '%Okyanus%' OR theme_key = 'ocean_depths'
            """),
            {
                "description": "Okyanusun derinliklerine dal! Yunus arkadaşınla mercan bahçelerinden başla, fosforlu canlılarla tanış, 30 metrelik dev mavi balinaya bin. 5 farklı derinlik seviyesinde unutulmaz keşif!",
                "thumbnail": "https://storage.googleapis.com/benimmasalim-generated-books/scenarios/ocean-depths-default.jpg",
                "cover_prompt": OCEAN_COVER_PROMPT,
                "page_prompt": OCEAN_PAGE_PROMPT,
                "story_prompt": OCEAN_STORY_PROMPT_TR,
                "location_en": "Pacific Ocean",
                "theme_key": "ocean_depths",
                "cultural_elements": json.dumps(OCEAN_CULTURAL_ELEMENTS),
                "custom_inputs": custom_inputs_json,
                "outfit_girl": OUTFIT_GIRL,
                "outfit_boy": OUTFIT_BOY,
                "page_count": 22,
                "display_order": 16,
                "marketing_badge": "Okyanus Keşfi",
                "age_range": "5-10 yaş",
                "tagline": "Mavi balinadan okyanus dibine! Yunusla derin deniz macerası",
                "marketing_features": marketing_features,
                "estimated_duration": "20-25 dakika okuma",
                "marketing_price_label": "299 TL'den başlayan fiyatlarla",
                "rating": 5.0,
            }
        )
        print("[DEBUG] UPDATE executed")
        print("✓ Okyanus Derinlikleri senaryosu güncellendi")
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
                "name": "Okyanus Derinlikleri: Mavi Dev ile Macera",
                "description": "Okyanusun derinliklerine dal! Yunus arkadaşınla mercan bahçelerinden başla, fosforlu canlılarla tanış, 30 metrelik dev mavi balinaya bin. 5 farklı derinlik seviyesinde unutulmaz keşif!",
                "thumbnail": "https://storage.googleapis.com/benimmasalim-generated-books/scenarios/ocean-depths-default.jpg",
                "cover_prompt": OCEAN_COVER_PROMPT,
                "page_prompt": OCEAN_PAGE_PROMPT,
                "story_prompt": OCEAN_STORY_PROMPT_TR,
                "location_en": "Pacific Ocean",
                "theme_key": "ocean_depths",
                "cultural_elements": json.dumps(OCEAN_CULTURAL_ELEMENTS),
                "custom_inputs": custom_inputs_json,
                "outfit_girl": OUTFIT_GIRL,
                "outfit_boy": OUTFIT_BOY,
                "page_count": 22,
                "linked_product_id": linked_product_id,
                "display_order": 16,
                "marketing_badge": "Okyanus Keşfi",
                "age_range": "5-10 yaş",
                "tagline": "Mavi balinadan okyanus dibine! Yunusla derin deniz macerası",
                "marketing_features": marketing_features,
                "estimated_duration": "20-25 dakika okuma",
                "marketing_price_label": "299 TL'den başlayan fiyatlarla",
                "rating": 5.0,
            }
        )
        print("[DEBUG] INSERT executed")
        print("✓ Okyanus Derinlikleri senaryosu oluşturuldu")


def downgrade() -> None:
    """Remove Okyanus Derinlikleri scenario."""
    conn = op.get_bind()
    conn.execute(
        sa.text(
            "DELETE FROM scenarios WHERE name ILIKE '%Okyanus%' "
            "OR theme_key = 'ocean_depths'"
        )
    )

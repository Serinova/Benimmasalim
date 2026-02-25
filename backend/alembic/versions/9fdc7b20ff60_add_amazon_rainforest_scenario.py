"""add_amazon_rainforest_scenario

Revision ID: 9fdc7b20ff60
Revises: 090_seed_scenario_outfits
Create Date: 2026-02-25 18:19:59.616916

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision: str = '9fdc7b20ff60'
down_revision: Union[str, None] = '090_seed_scenario_outfits'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add Amazon Ormanları Keşfediyorum scenario."""
    from scripts.update_amazon_scenario import (
        AMAZON_COVER_PROMPT,
        AMAZON_PAGE_PROMPT,
        AMAZON_STORY_PROMPT_TR,
        AMAZON_CULTURAL_ELEMENTS,
        AMAZON_CUSTOM_INPUTS,
        OUTFIT_GIRL,
        OUTFIT_BOY,
    )
    import json
    
    conn = op.get_bind()
    
    # Check if scenario already exists
    result = conn.execute(
        sa.text("SELECT id FROM scenarios WHERE name ILIKE '%Amazon%Ormanlar%' LIMIT 1")
    )
    existing = result.fetchone()
    
    if existing:
        # Update existing
        conn.execute(
            sa.text("""
                UPDATE scenarios SET
                    description = :description,
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
                    display_order = 12
                WHERE name ILIKE '%Amazon%Ormanlar%'
            """),
            {
                "description": "Dünyanın en zengin ekosistemi Amazon yağmur ormanlarında büyülü bir keşif! Renkli papağanlar, pembe nehir yunusları, ağaç tembelleri ve dev kapok ağaçları arasında biyolojik çeşitliliği keşfet.",
                "cover_prompt": AMAZON_COVER_PROMPT,
                "page_prompt": AMAZON_PAGE_PROMPT,
                "story_prompt": AMAZON_STORY_PROMPT_TR,
                "location_en": "Amazon Rainforest",
                "theme_key": "amazon_rainforest",
                "cultural_elements": json.dumps(AMAZON_CULTURAL_ELEMENTS),
                "custom_inputs": json.dumps(AMAZON_CUSTOM_INPUTS),
                "outfit_girl": OUTFIT_GIRL,
                "outfit_boy": OUTFIT_BOY,
                "page_count": 22,
            }
        )
        print("✓ Amazon Ormanları senaryosu güncellendi")
    else:
        # Create new
        # First, get linked_product_id (A4 YATAY 32 sayfa)
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
                    created_at, updated_at
                ) VALUES (
                    gen_random_uuid(), :name, :description, :thumbnail,
                    :cover_prompt, :page_prompt, :story_prompt,
                    :location_en, :theme_key, :cultural_elements, :custom_inputs,
                    :outfit_girl, :outfit_boy, :page_count,
                    :linked_product_id, true, 12,
                    now(), now()
                )
            """),
            {
                "name": "Amazon Ormanları Keşfediyorum",
                "description": "Dünyanın en zengin ekosistemi Amazon yağmur ormanlarında büyülü bir keşif! Renkli papağanlar, pembe nehir yunusları, ağaç tembelleri ve dev kapok ağaçları arasında biyolojik çeşitliliği keşfet.",
                "thumbnail": "https://storage.googleapis.com/benimmasalim-generated-books/scenarios/amazon-rainforest-default.jpg",
                "cover_prompt": AMAZON_COVER_PROMPT,
                "page_prompt": AMAZON_PAGE_PROMPT,
                "story_prompt": AMAZON_STORY_PROMPT_TR,
                "location_en": "Amazon Rainforest",
                "theme_key": "amazon_rainforest",
                "cultural_elements": json.dumps(AMAZON_CULTURAL_ELEMENTS),
                "custom_inputs": json.dumps(AMAZON_CUSTOM_INPUTS),
                "outfit_girl": OUTFIT_GIRL,
                "outfit_boy": OUTFIT_BOY,
                "page_count": 22,
                "linked_product_id": linked_product_id,
            }
        )
        print("✓ Amazon Ormanları senaryosu oluşturuldu")


def downgrade() -> None:
    """Remove Amazon scenario."""
    conn = op.get_bind()
    conn.execute(
        sa.text("DELETE FROM scenarios WHERE name ILIKE '%Amazon%Ormanlar%'")
    )


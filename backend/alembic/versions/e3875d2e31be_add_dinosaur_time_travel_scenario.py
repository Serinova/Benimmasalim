"""add_dinosaur_time_travel_scenario

Revision ID: e3875d2e31be
Revises: 9fdc7b20ff60
Create Date: 2026-02-25 18:47:57.215186

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision: str = 'e3875d2e31be'
down_revision: Union[str, None] = '9fdc7b20ff60'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add Dinozorlar Macerası: Zaman Yolculuğu scenario."""
    from scripts.update_dinosaur_scenario import (
        DINOSAUR_COVER_PROMPT,
        DINOSAUR_PAGE_PROMPT,
        DINOSAUR_STORY_PROMPT_TR,
        DINOSAUR_CULTURAL_ELEMENTS,
        DINOSAUR_CUSTOM_INPUTS,
        OUTFIT_GIRL,
        OUTFIT_BOY,
    )
    import json
    
    conn = op.get_bind()
    
    # Check if scenario already exists
    result = conn.execute(
        sa.text("SELECT id FROM scenarios WHERE name ILIKE '%Dinozor%' LIMIT 1")
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
                    display_order = 13
                WHERE name ILIKE '%Dinozor%'
            """),
            {
                "description": "Zaman makinesi ile 65 milyon yıl öncesine gidip T-Rex, Triceratops, Brachiosaurus ve daha fazlasıyla tanış! Kayıp yavru dinozorun ailesini bul ve prehistorik dünyanın sırlarını keşfet. Aksiyon dolu bir macera!",
                "cover_prompt": DINOSAUR_COVER_PROMPT,
                "page_prompt": DINOSAUR_PAGE_PROMPT,
                "story_prompt": DINOSAUR_STORY_PROMPT_TR,
                "location_en": "Cretaceous Period",
                "theme_key": "dinosaur_time_travel",
                "cultural_elements": json.dumps(DINOSAUR_CULTURAL_ELEMENTS),
                "custom_inputs": json.dumps(DINOSAUR_CUSTOM_INPUTS),
                "outfit_girl": OUTFIT_GIRL,
                "outfit_boy": OUTFIT_BOY,
                "page_count": 22,
            }
        )
        print("✓ Dinozorlar Macerası senaryosu güncellendi")
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
                    :linked_product_id, true, 13,
                    now(), now()
                )
            """),
            {
                "name": "Dinozorlar Macerası: Zaman Yolculuğu",
                "description": "Zaman makinesi ile 65 milyon yıl öncesine gidip T-Rex, Triceratops, Brachiosaurus ve daha fazlasıyla tanış! Kayıp yavru dinozorun ailesini bul ve prehistorik dünyanın sırlarını keşfet. Aksiyon dolu bir macera!",
                "thumbnail": "https://storage.googleapis.com/benimmasalim-generated-books/scenarios/dinosaur-time-travel-default.jpg",
                "cover_prompt": DINOSAUR_COVER_PROMPT,
                "page_prompt": DINOSAUR_PAGE_PROMPT,
                "story_prompt": DINOSAUR_STORY_PROMPT_TR,
                "location_en": "Cretaceous Period",
                "theme_key": "dinosaur_time_travel",
                "cultural_elements": json.dumps(DINOSAUR_CULTURAL_ELEMENTS),
                "custom_inputs": json.dumps(DINOSAUR_CUSTOM_INPUTS),
                "outfit_girl": OUTFIT_GIRL,
                "outfit_boy": OUTFIT_BOY,
                "page_count": 22,
                "linked_product_id": linked_product_id,
            }
        )
        print("✓ Dinozorlar Macerası senaryosu oluşturuldu")


def downgrade() -> None:
    """Remove Dinozorlar Macerası scenario."""
    conn = op.get_bind()
    conn.execute(
        sa.text("DELETE FROM scenarios WHERE name ILIKE '%Dinozor%'")
    )

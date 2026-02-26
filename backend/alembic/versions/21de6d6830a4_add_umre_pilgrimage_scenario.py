"""add_umre_pilgrimage_scenario

Revision ID: 21de6d6830a4
Revises: 4d4290ef8d31
Create Date: 2026-02-25 19:23:43.092520

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '21de6d6830a4'
down_revision: Union[str, None] = '4d4290ef8d31'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add Umre Yolculuğu: Kutsal Topraklarda scenario."""
    from scripts.update_umre_scenario import (
        UMRE_COVER_PROMPT,
        UMRE_PAGE_PROMPT,
        UMRE_STORY_PROMPT_TR,
        UMRE_CULTURAL_ELEMENTS,
        UMRE_CUSTOM_INPUTS,
        OUTFIT_GIRL,
        OUTFIT_BOY,
    )
    import json
    
    conn = op.get_bind()
    
    # Check if scenario already exists
    result = conn.execute(
        sa.text("SELECT id FROM scenarios WHERE name ILIKE '%Umre%' LIMIT 1")
    )
    existing = result.fetchone()
    
    if existing:
        # Update existing
        marketing_features = json.dumps([
            "Kabe ve Mescid-i Haram ziyareti",
            "Safa-Marwa ve Zemzem suyu",
            "Medine ve yeşil kubbe",
            "Nur Dağı ve Arafat",
            "Saygı ve tevazu değerleri",
            "Ailece manevi bağ"
        ])
        
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
                    display_order = 14,
                    marketing_badge = :marketing_badge,
                    age_range = :age_range,
                    tagline = :tagline,
                    marketing_features = :marketing_features,
                    estimated_duration = :estimated_duration,
                    marketing_price_label = :marketing_price_label,
                    rating = :rating
                WHERE name ILIKE '%Umre%'
            """),
            {
                "description": "Ailesiyle birlikte Mekke ve Medine'ye manevi bir yolculuk! Kabe'yi görme, tavaf, Safa-Marwa, Zemzem, yeşil kubbe ve Nur Dağı. Saygı, tevazu ve şükür dolu bir deneyim.",
                "cover_prompt": UMRE_COVER_PROMPT,
                "page_prompt": UMRE_PAGE_PROMPT,
                "story_prompt": UMRE_STORY_PROMPT_TR,
                "location_en": "Mecca and Medina",
                "theme_key": "umre_pilgrimage",
                "cultural_elements": json.dumps(UMRE_CULTURAL_ELEMENTS),
                "custom_inputs": json.dumps(UMRE_CUSTOM_INPUTS),
                "outfit_girl": OUTFIT_GIRL,
                "outfit_boy": OUTFIT_BOY,
                "page_count": 22,
                "marketing_badge": "Manevi Yolculuk",
                "age_range": "7-10 yaş",
                "tagline": "Kutsal topraklarda unutulmaz bir manevi deneyim",
                "marketing_features": marketing_features,
                "estimated_duration": "20-25 dakika okuma",
                "marketing_price_label": "299 TL'den başlayan fiyatlarla",
                "rating": 5.0,
            }
        )
        print("OK: Umre Yolculugu senaryosu guncellendi")
    else:
        # Create new
        # First, get linked_product_id (A4 YATAY 32 sayfa)
        product_result = conn.execute(
            sa.text("SELECT id FROM products WHERE name ILIKE '%A4%YATAY%32%' LIMIT 1")
        )
        product_row = product_result.fetchone()
        linked_product_id = product_row[0] if product_row else None
        
        marketing_features = json.dumps([
            "Kabe ve Mescid-i Haram ziyareti",
            "Safa-Marwa ve Zemzem suyu",
            "Medine ve yeşil kubbe",
            "Nur Dağı ve Arafat",
            "Saygı ve tevazu değerleri",
            "Ailece manevi bağ"
        ])
        
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
                    :linked_product_id, true, 14,
                    :marketing_badge, :age_range, :tagline, :marketing_features,
                    :estimated_duration, :marketing_price_label, :rating,
                    now(), now()
                )
            """),
            {
                "name": "Umre Yolculuğu: Kutsal Topraklarda",
                "description": "Ailesiyle birlikte Mekke ve Medine'ye manevi bir yolculuk! Kabe'yi görme, tavaf, Safa-Marwa, Zemzem, yeşil kubbe ve Nur Dağı. Saygı, tevazu ve şükür dolu bir deneyim.",
                "thumbnail": "https://storage.googleapis.com/benimmasalim-generated-books/scenarios/umre-pilgrimage-default.jpg",
                "cover_prompt": UMRE_COVER_PROMPT,
                "page_prompt": UMRE_PAGE_PROMPT,
                "story_prompt": UMRE_STORY_PROMPT_TR,
                "location_en": "Mecca and Medina",
                "theme_key": "umre_pilgrimage",
                "cultural_elements": json.dumps(UMRE_CULTURAL_ELEMENTS),
                "custom_inputs": json.dumps(UMRE_CUSTOM_INPUTS),
                "outfit_girl": OUTFIT_GIRL,
                "outfit_boy": OUTFIT_BOY,
                "page_count": 22,
                "linked_product_id": linked_product_id,
                "marketing_badge": "Manevi Yolculuk",
                "age_range": "7-10 yaş",
                "tagline": "Kutsal topraklarda unutulmaz bir manevi deneyim",
                "marketing_features": marketing_features,
                "estimated_duration": "20-25 dakika okuma",
                "marketing_price_label": "299 TL'den başlayan fiyatlarla",
                "rating": 5.0,
            }
        )
        print("OK: Umre Yolculugu senaryosu olusturuldu")


def downgrade() -> None:
    """Remove Umre Yolculuğu scenario."""
    conn = op.get_bind()
    conn.execute(
        sa.text("DELETE FROM scenarios WHERE name ILIKE '%Umre%'")
    )

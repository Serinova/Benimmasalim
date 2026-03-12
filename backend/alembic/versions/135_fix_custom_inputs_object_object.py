"""Fix broken [object Object] in custom_inputs_schema options for 5 scenarios.

Revision ID: 135_fix_custom_inputs_object_object
Revises: 134_fix_dinosaur_pari_consistency
Create Date: 2026-03-12

Some scenarios have `options` arrays containing "[object Object]" strings
instead of proper {label, value} dicts. This is caused by a JS→JSON
serialization bug in the admin panel. This migration restores the correct
options based on each scenario's theme.
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text
import json

revision = "135_fix_custom_inputs_object_object"
down_revision = "d5e6f7a8b9c0"
branch_labels = None
depends_on = None


# Correct options for each broken scenario (theme_key → correct options list)
_FIXES: dict[str, list[dict]] = {
    "cappadocia": [
        {
            "key": "animal_friend",
            "type": "select",
            "label": "Yol Arkadaşı",
            "default": "Cesur Yılkı Atı",
            "options": [
                {"label": "Cesur Yılkı Atı", "value": "Cesur Yılkı Atı"},
                {"label": "Sevimli Kapadokya Tilkisi", "value": "Sevimli Kapadokya Tilkisi"},
            ],
        }
    ],
    "gobeklitepe": [
        {
            "key": "animal_friend",
            "type": "select",
            "label": "Step Dostu",
            "default": "Cesur Step Tilkisi",
            "options": [
                {"label": "Cesur Step Tilkisi", "value": "Cesur Step Tilkisi"},
                {"label": "Sevimli Step Tavşanı", "value": "Sevimli Step Tavşanı"},
            ],
        },
        {
            "key": "favorite_element",
            "type": "select",
            "label": "Favori Türk Öğesi",
            "default": "T-Pilleri",
            "options": [
                {"label": "T-Pilleri", "value": "T-Pilleri"},
                {"label": "Hayvan Rölyefleri", "value": "Hayvan Rölyefleri"},
            ],
        },
    ],
    "ephesus": [
        {
            "key": "animal_friend",
            "type": "select",
            "label": "Antik Dost",
            "default": "Antik Roma Kartalı",
            "options": [
                {"label": "Antik Roma Kartalı", "value": "Antik Roma Kartalı"},
                {"label": "Efes Kedisi", "value": "Efes Kedisi"},
            ],
        }
    ],
    "kudus": [
        {
            "key": "animal_friend",
            "type": "select",
            "label": "Kudüs Dostu",
            "default": "Güvercin Beyazı",
            "options": [
                {"label": "Kudüs Beyaz Güvercini", "value": "Güvercin Beyazı"},
                {"label": "Sevimli Zeytin Dalı Serçesi", "value": "Sevimli Zeytin Dalı Serçesi"},
            ],
        }
    ],
    "fairy_tale_world": [
        {
            "key": "animal_friend",
            "type": "select",
            "label": "Masal Dostu",
            "default": "Parıltılı Mini Ejderha",
            "options": [
                {"label": "Parıltılı Mini Ejderha", "value": "Parıltılı Mini Ejderha"},
                {"label": "Konuşan Masal Baykuşu", "value": "Konuşan Masal Baykuşu"},
            ],
        }
    ],
}


def upgrade() -> None:
    conn = op.get_bind()
    updated = 0

    for theme_key, correct_schema in _FIXES.items():
        result = conn.execute(
            text("UPDATE scenarios SET custom_inputs_schema = :schema WHERE theme_key = :tk"),
            {"schema": json.dumps(correct_schema, ensure_ascii=False), "tk": theme_key},
        )
        if result.rowcount > 0:
            updated += 1
            print(f"  ✅ Fixed custom_inputs_schema for {theme_key}")
        else:
            print(f"  ⚠️ No scenario found for theme_key={theme_key}")

    print(f"\nFixed custom_inputs_schema for {updated}/{len(_FIXES)} scenarios")


def downgrade() -> None:
    # Not reversible — the broken [object Object] data is not worth preserving
    pass

"""Fix custom_inputs_schema options from comma string to list format.

Revision ID: 113_fix_custom_inputs_options_format
Revises: 112_app_settings_and_product_vat
Create Date: 2026-03-01

Some scenarios were created with `options` stored as comma-separated strings
instead of JSON arrays. This migration normalizes them to proper arrays.
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text

revision = "113_fix_custom_inputs_options_format"
down_revision = "112_app_settings_and_product_vat"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    # Find all scenarios with custom_inputs_schema that have string options
    rows = conn.execute(
        text("SELECT id, custom_inputs_schema FROM scenarios WHERE custom_inputs_schema IS NOT NULL")
    ).fetchall()

    updated = 0
    for row in rows:
        scenario_id = row[0]
        schema = row[1]
        if not isinstance(schema, list):
            continue

        changed = False
        new_schema = []
        for field in schema:
            if not isinstance(field, dict):
                new_schema.append(field)
                continue
            options = field.get("options")
            if isinstance(options, str) and options:
                field = dict(field)
                field["options"] = [s.strip() for s in options.split(",") if s.strip()]
                changed = True
            new_schema.append(field)

        if changed:
            import json
            conn.execute(
                text("UPDATE scenarios SET custom_inputs_schema = :schema WHERE id = :id"),
                {"schema": json.dumps(new_schema, ensure_ascii=False), "id": scenario_id},
            )
            updated += 1

    print(f"Fixed options format in {updated} scenarios")


def downgrade() -> None:
    # Not reversible (string→list is safe; reverting list→string would lose data)
    pass

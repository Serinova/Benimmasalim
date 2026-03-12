"""Nullify registry-managed prompt columns for all 17 registered scenarios.

Revision ID: 136_nullify_registry_managed_columns
Revises: 135_fix_custom_inputs_object_object
Create Date: 2026-03-12

All scenario content (story_prompt_tr, outfits, companions, bible, etc.)
now lives in the Python code registry (`app/scenarios/`).  The admin API
reads from the registry when available (HYBRID mode).  This migration
clears the now-redundant DB copies to avoid confusion and save storage.

cover_prompt_template and page_prompt_template use '' (empty string)
instead of NULL because the column is NOT NULL with a server_default.
"""

from alembic import op
from sqlalchemy import text

revision = "136_nullify_registry_managed_columns"
down_revision = "135_fix_custom_inputs_object_object"
branch_labels = None
depends_on = None

# All 17 theme_keys that have a code-registry entry
_REGISTRY_KEYS = [
    "abusimbel",
    "amazon",
    "cappadocia",
    "catalhoyuk",
    "dinosaur",
    "ephesus",
    "fairy_tale_world",
    "galata",
    "gobeklitepe",
    "kudus",
    "ocean",
    "space",
    "sultanahmet",
    "sumela",
    "toy_world",
    "umre_pilgrimage",
    "yerebatan",
]


def upgrade() -> None:
    conn = op.get_bind()

    # Build a WHERE clause for all registry-managed scenarios
    placeholders = ", ".join(f":k{i}" for i in range(len(_REGISTRY_KEYS)))
    params = {f"k{i}": k for i, k in enumerate(_REGISTRY_KEYS)}

    result = conn.execute(
        text(f"""
            UPDATE scenarios
            SET story_prompt_tr      = NULL,
                cover_prompt_template = '',
                page_prompt_template  = '',
                outfit_girl           = NULL,
                outfit_boy            = NULL,
                custom_inputs_schema  = '[]'::jsonb,
                scenario_bible        = NULL,
                cultural_elements     = NULL,
                location_constraints  = NULL
            WHERE theme_key IN ({placeholders})
        """),
        params,
    )

    print(f"\n  ✅ Cleared registry-managed columns for {result.rowcount}/{len(_REGISTRY_KEYS)} scenarios\n")


def downgrade() -> None:
    # Content lives in app/scenarios/ Python code — no DB restore needed.
    pass

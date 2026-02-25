"""Update visual_styles display_name with user-friendly Turkish names.

Revision ID: vs_display_names_001
Revises: a1b2c3d4e5f6
Create Date: 2026-02-14
"""

from typing import Union
from alembic import op

revision: str = "vs_display_names_001"
down_revision: Union[str, None] = "a1b2c3d4e5f6"
branch_labels = None
depends_on = None

# Map: internal name (substring match) -> user-friendly display_name
DISPLAY_NAME_MAP = {
    "2D CHILDREN": "Klasik Hikaye Kitabı",
    "3D Pixar": "Sihirli Animasyon",
    "Adventure Digital": "Macera Dünyası",
    "Default Storybook": "Masal Kitabı",
    "Ghibli": "Rüya Bahçesi",
    "Watercolor": "Suluboya Masal",
    "Yumuşak Pastel": "Pastel Rüya",
}


def upgrade() -> None:
    for name_prefix, display_name in DISPLAY_NAME_MAP.items():
        op.execute(
            f"UPDATE visual_styles SET display_name = '{display_name}' "
            f"WHERE name LIKE '{name_prefix}%' AND (display_name IS NULL OR display_name = '')"
        )


def downgrade() -> None:
    for name_prefix in DISPLAY_NAME_MAP:
        op.execute(
            f"UPDATE visual_styles SET display_name = NULL "
            f"WHERE name LIKE '{name_prefix}%'"
        )

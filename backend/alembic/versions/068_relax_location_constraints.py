"""Relax location constraints text to prevent overcrowding in scenes.

Revision ID: 068_relax_location_constraints
Revises: 067_fix_watercolor_likeness
Create Date: 2026-02-23 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import table, column


# revision identifiers, used by Alembic.
revision = '068_relax_location_constraints'
down_revision = '067_fix_watercolor_likeness'
branch_labels = None
depends_on = None


def upgrade():
    # Define table structure for update
    scenarios = table('scenarios',
        column('id', sa.Integer),
        column('name', sa.String),
        column('location_constraints', sa.Text)
    )

    # Use raw SQL to REPLACE string in the column
    op.execute(
        "UPDATE scenarios SET location_constraints = REPLACE(location_constraints, 'required in every scene:', 'iconic elements (include 1-2 relevant details depending on the scene):') WHERE location_constraints LIKE '%required in every scene:%'"
    )


def downgrade():
    op.execute(
        "UPDATE scenarios SET location_constraints = REPLACE(location_constraints, 'iconic elements (include 1-2 relevant details depending on the scene):', 'required in every scene:') WHERE location_constraints LIKE '%iconic elements (include 1-2 relevant details depending on the scene):%'"
    )

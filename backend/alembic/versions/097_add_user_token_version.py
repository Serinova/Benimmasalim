"""Add token_version to users for JWT invalidation on account deletion.

Revision ID: 097_token_version
Revises: 096_notification_outbox
"""

from alembic import op
import sqlalchemy as sa


revision = "097_token_version"
down_revision = "096_notification_outbox"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("token_version", sa.Integer, server_default="0", nullable=False))


def downgrade() -> None:
    op.drop_column("users", "token_version")

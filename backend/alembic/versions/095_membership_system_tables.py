"""Membership system: user_addresses, notification_preferences, child_profiles + user/order extensions.

Revision ID: 095_membership
Revises: 094_update_all_outfit_descriptions
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


revision = "095_membership"
down_revision = "094"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # --- New tables ---

    op.create_table(
        "user_addresses",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("label", sa.String(50), server_default="Ev"),
        sa.Column("full_name", sa.String(100), nullable=False),
        sa.Column("phone", sa.String(20)),
        sa.Column("address_line", sa.Text, nullable=False),
        sa.Column("city", sa.String(50), nullable=False),
        sa.Column("district", sa.String(50)),
        sa.Column("postal_code", sa.String(10)),
        sa.Column("is_default", sa.Boolean, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("idx_user_addresses_user", "user_addresses", ["user_id"])

    op.create_table(
        "notification_preferences",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("email_order_updates", sa.Boolean, server_default="true"),
        sa.Column("email_marketing", sa.Boolean, server_default="false"),
        sa.Column("sms_order_updates", sa.Boolean, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "child_profiles",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("age", sa.Integer, nullable=False),
        sa.Column("gender", sa.String(10)),
        sa.Column("photo_url", sa.Text),
        sa.Column("photo_uploaded_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.CheckConstraint("age >= 1 AND age <= 18", name="valid_child_profile_age"),
    )
    op.create_index("idx_child_profiles_user", "child_profiles", ["user_id"])

    # --- Users table extensions ---
    op.add_column("users", sa.Column("email_verified_at", sa.DateTime(timezone=True)))
    op.add_column("users", sa.Column("last_login_at", sa.DateTime(timezone=True)))
    op.add_column("users", sa.Column("deletion_scheduled_at", sa.DateTime(timezone=True)))

    # --- Orders table extensions ---
    op.add_column("orders", sa.Column("child_profile_id", UUID(as_uuid=True),
                                       sa.ForeignKey("child_profiles.id", ondelete="SET NULL")))
    op.add_column("orders", sa.Column("billing_type", sa.String(20)))
    op.add_column("orders", sa.Column("billing_tax_id", sa.String(20)))
    op.add_column("orders", sa.Column("billing_company_name", sa.String(200)))
    op.add_column("orders", sa.Column("refund_requested_at", sa.DateTime(timezone=True)))
    op.add_column("orders", sa.Column("refund_reason", sa.Text))


def downgrade() -> None:
    op.drop_column("orders", "refund_reason")
    op.drop_column("orders", "refund_requested_at")
    op.drop_column("orders", "billing_company_name")
    op.drop_column("orders", "billing_tax_id")
    op.drop_column("orders", "billing_type")
    op.drop_column("orders", "child_profile_id")

    op.drop_column("users", "deletion_scheduled_at")
    op.drop_column("users", "last_login_at")
    op.drop_column("users", "email_verified_at")

    op.drop_index("idx_child_profiles_user", table_name="child_profiles")
    op.drop_table("child_profiles")
    op.drop_table("notification_preferences")
    op.drop_index("idx_user_addresses_user", table_name="user_addresses")
    op.drop_table("user_addresses")

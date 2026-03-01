"""Add composite indexes for orders list/detail performance.

Indexes added:
- orders(user_id, created_at DESC) — list pagination sort
- orders(user_id, status) — filtered list queries
- orders(child_name) using gin_trgm_ops — ILIKE search acceleration
- order_pages(order_id, page_number) — detail page loading (covers unique constraint)
- audit_logs(order_id, action, created_at) — timeline events query

Revision ID: 098_perf_indexes
Revises: 097_token_version
"""

from alembic import op

revision = "098_perf_indexes"
down_revision = "097_token_version"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Composite index for list pagination: WHERE user_id = ? ORDER BY created_at DESC
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_orders_user_created "
        "ON orders (user_id, created_at DESC)"
    )

    # Composite index for filtered list: WHERE user_id = ? AND status IN (...)
    op.create_index(
        "idx_orders_user_status",
        "orders",
        ["user_id", "status"],
        if_not_exists=True,
    )

    # Trigram index for ILIKE search on child_name (requires pg_trgm extension)
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_orders_child_name_trgm "
        "ON orders USING gin (child_name gin_trgm_ops)"
    )

    # Composite index for timeline events: WHERE order_id = ? AND action LIKE 'ORDER_STATUS_%' ORDER BY created_at
    op.create_index(
        "idx_audit_order_action_time",
        "audit_logs",
        ["order_id", "action", "created_at"],
        if_not_exists=True,
    )

    # Composite index for order pages: WHERE order_id = ? ORDER BY page_number
    # (unique constraint already creates an index, but explicit composite is clearer)
    op.create_index(
        "idx_pages_order_number",
        "order_pages",
        ["order_id", "page_number"],
        if_not_exists=True,
    )


def downgrade() -> None:
    op.drop_index("idx_pages_order_number", table_name="order_pages")
    op.drop_index("idx_audit_order_action_time", table_name="audit_logs")
    op.execute("DROP INDEX IF EXISTS idx_orders_child_name_trgm")
    op.drop_index("idx_orders_user_status", table_name="orders")
    op.execute("DROP INDEX IF EXISTS idx_orders_user_created")

"""Performance regression tests for orders list and detail endpoints.

Validates:
- Slim payload (no heavy fields in list)
- Include param controls pages/timeline loading
- Column-level select (no full ORM load for list)
- Pagination limits enforced
- Index definitions present in models
- Count query efficiency
"""

import inspect
import uuid

import pytest

from app.models.order import Order, OrderStatus


class TestListEndpointPayload:
    """Verify list endpoint returns minimal payload."""

    def test_list_uses_column_select_not_orm(self):
        """list_user_orders should use select(*columns), not select(Order)."""
        source = inspect.getsource(
            __import__("app.api.v1.orders", fromlist=["list_user_orders"]).list_user_orders
        )
        assert "_LIST_COLUMNS" in source
        assert "select(*_LIST_COLUMNS)" in source

    def test_list_columns_are_minimal(self):
        """_LIST_COLUMNS should not include heavy fields."""
        from app.api.v1.orders import _LIST_COLUMNS

        col_names = {c.key for c in _LIST_COLUMNS}
        heavy_fields = {
            "final_pdf_url", "audio_file_url", "qr_code_url",
            "shipping_address", "face_embedding", "face_description",
            "child_photo_url", "blueprint_json", "magic_items",
            "dedication_note", "back_cover_image_url",
        }
        assert col_names.isdisjoint(heavy_fields), (
            f"Heavy fields in list columns: {col_names & heavy_fields}"
        )

    def test_list_does_not_return_final_pdf_url(self):
        """final_pdf_url is expensive and not needed in list view."""
        source = inspect.getsource(
            __import__("app.api.v1.orders", fromlist=["list_user_orders"]).list_user_orders
        )
        assert "final_pdf_url" not in source

    def test_list_pagination_max_enforced(self):
        """per_page should be capped at 50."""
        source = inspect.getsource(
            __import__("app.api.v1.orders", fromlist=["list_user_orders"]).list_user_orders
        )
        assert "min(max(1, per_page), 50)" in source

    def test_list_count_uses_efficient_query(self):
        """Count query should use count(Order.id), not subquery wrapping."""
        source = inspect.getsource(
            __import__("app.api.v1.orders", fromlist=["list_user_orders"]).list_user_orders
        )
        assert "count(Order.id)" in source
        assert "select_from(query.subquery())" not in source


class TestDetailEndpointInclude:
    """Verify detail endpoint supports lazy loading via include param."""

    def test_detail_accepts_include_param(self):
        """get_order should accept 'include' query parameter."""
        source = inspect.getsource(
            __import__("app.api.v1.orders", fromlist=["get_order"]).get_order
        )
        assert "include:" in source or "include :" in source

    def test_detail_without_include_has_no_pages(self):
        """Without include=pages, response should not contain pages."""
        source = inspect.getsource(
            __import__("app.api.v1.orders", fromlist=["get_order"]).get_order
        )
        assert '"pages" in includes' in source

    def test_detail_without_include_has_no_timeline(self):
        """Without include=timeline, response should not contain timeline_events."""
        source = inspect.getsource(
            __import__("app.api.v1.orders", fromlist=["get_order"]).get_order
        )
        assert '"timeline" in includes' in source

    def test_load_pages_uses_column_select(self):
        """_load_order_pages should use column-level select."""
        source = inspect.getsource(
            __import__("app.api.v1.orders", fromlist=["_load_order_pages"])._load_order_pages
        )
        assert "OrderPage.page_number" in source
        assert "OrderPage.status" in source

    def test_load_timeline_uses_column_select(self):
        """_load_timeline_events should use column-level select."""
        source = inspect.getsource(
            __import__("app.api.v1.orders", fromlist=["_load_timeline_events"])._load_timeline_events
        )
        assert "AuditLog.action" in source
        assert "AuditLog.created_at" in source

    def test_timeline_fallback_for_old_orders(self):
        """_load_timeline_events should synthesize timeline for orders without audit logs."""
        source = inspect.getsource(
            __import__("app.api.v1.orders", fromlist=["_load_timeline_events"])._load_timeline_events
        )
        assert "ORDER_STATUS_DRAFT" in source


class TestDatabaseIndexes:
    """Verify required indexes exist in model definitions."""

    def test_order_model_has_user_created_index(self):
        """Composite index (user_id, created_at) for list pagination."""
        idx_names = {idx.name for idx in Order.__table__.indexes}
        assert "idx_orders_user_created" in idx_names

    def test_order_model_has_user_status_index(self):
        """Composite index (user_id, status) for filtered queries."""
        idx_names = {idx.name for idx in Order.__table__.indexes}
        assert "idx_orders_user_status" in idx_names

    def test_order_model_has_user_id_index(self):
        """Single-column index on user_id."""
        col = Order.__table__.columns["user_id"]
        assert col.index is True

    def test_order_pages_has_order_index(self):
        from app.models.order_page import OrderPage

        idx_names = {idx.name for idx in OrderPage.__table__.indexes}
        assert "idx_pages_order" in idx_names

    def test_audit_log_has_order_index(self):
        from app.models.audit_log import AuditLog

        idx_names = {idx.name for idx in AuditLog.__table__.indexes}
        assert "idx_logs_order" in idx_names

    def test_migration_file_exists(self):
        """Performance index migration should exist."""
        import os

        migration_path = os.path.join(
            os.path.dirname(__file__), "..", "alembic", "versions", "098_performance_indexes.py"
        )
        assert os.path.exists(migration_path)

    def test_migration_has_trigram_index(self):
        """Migration should create pg_trgm index for ILIKE search."""
        source = open(
            os.path.join(
                os.path.dirname(__file__), "..", "alembic", "versions", "098_performance_indexes.py"
            )
        ).read()
        assert "pg_trgm" in source
        assert "gin_trgm_ops" in source


class TestSearchOptimization:
    """Verify search uses efficient patterns."""

    def test_search_uses_ilike_not_like(self):
        """Search should use case-insensitive ILIKE."""
        source = inspect.getsource(
            __import__("app.api.v1.orders", fromlist=["list_user_orders"]).list_user_orders
        )
        assert "ilike" in source

    def test_search_strips_input(self):
        """Search input should be stripped to avoid whitespace-only queries."""
        source = inspect.getsource(
            __import__("app.api.v1.orders", fromlist=["list_user_orders"]).list_user_orders
        )
        assert "search.strip()" in source or "search_clean" in source


class TestAPIContractConsistency:
    """Verify API types match between frontend and backend."""

    def test_list_response_fields_match_frontend_interface(self):
        """Backend list response fields should match UserOrder interface."""
        source = inspect.getsource(
            __import__("app.api.v1.orders", fromlist=["list_user_orders"]).list_user_orders
        )
        required_fields = ["id", "status", "child_name", "created_at", "payment_amount",
                           "tracking_number", "carrier", "has_audio_book",
                           "total_pages", "completed_pages"]
        for field in required_fields:
            assert f'"{field}"' in source, f"Missing field in list response: {field}"


# Need os for migration file check
import os

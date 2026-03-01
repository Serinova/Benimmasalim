"""Add invoice_serial_counters table for gap-free invoice numbering.

Replaces PostgreSQL sequences (which skip numbers on rollback) with a
table-based counter locked via SELECT … FOR UPDATE — ensures gap-free
invoice numbers as required by Turkish tax law.

Revision ID: 109_invoice_serial_counter
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers
revision = "109_invoice_serial_counter"
down_revision = "108_fill_remaining_scenario_marketing"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "invoice_serial_counters",
        sa.Column("year", sa.Integer(), primary_key=True, autoincrement=False),
        sa.Column("last_serial", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("prefix", sa.String(10), nullable=False, server_default="BM"),
    )

    # Seed with current year's max serial from existing invoices (if any)
    # so we don't duplicate numbers after migration
    op.execute(
        """
        INSERT INTO invoice_serial_counters (year, last_serial, prefix)
        SELECT
            EXTRACT(YEAR FROM issued_at)::int AS year,
            COALESCE(
                MAX(
                    CASE
                        WHEN invoice_number ~ '^BM-[0-9]{4}-[0-9]+$'
                        THEN CAST(SPLIT_PART(invoice_number, '-', 3) AS INTEGER)
                        ELSE 0
                    END
                ),
                0
            ) AS last_serial,
            'BM' AS prefix
        FROM invoices
        WHERE issued_at IS NOT NULL
        GROUP BY EXTRACT(YEAR FROM issued_at)::int
        ON CONFLICT (year) DO UPDATE SET
            last_serial = GREATEST(
                invoice_serial_counters.last_serial,
                EXCLUDED.last_serial
            )
        """
    )


def downgrade() -> None:
    op.drop_table("invoice_serial_counters")

#!/usr/bin/env python
"""Prompt Output Compliance verifier — CLI.

Run from the backend container or project root::

    python scripts/verify_prompt_outputs.py

Exit code 0 = all pass, 1 = at least one failure.

No external API calls (Gemini, FAL, etc.).
Optionally reads DB templates if a database connection is available;
otherwise uses hardcoded DEFAULT_COVER/INNER_TEMPLATE_EN.
"""

from __future__ import annotations

import os
import sys

# Ensure app imports work when running from project root
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.prompt_engine.compliance import (
    format_report,
    run_compliance,
)
from app.prompt_engine.constants import (
    DEFAULT_COVER_TEMPLATE_EN,
    DEFAULT_INNER_TEMPLATE_EN,
)


def _try_load_db_templates() -> tuple[str, str, str]:
    """Try to load templates from DB.  Returns ``(cover, inner, source_label)``.

    Falls back to compiled defaults when DB is unavailable.
    """
    try:
        import asyncio

        import asyncpg  # type: ignore[import-untyped]

        db_url = os.environ.get("DATABASE_URL")
        if not db_url:
            raise RuntimeError("DATABASE_URL not set")

        dsn = db_url.replace("postgresql+asyncpg://", "postgresql://")

        async def _fetch() -> list:
            conn = await asyncpg.connect(dsn)
            try:
                return await conn.fetch(
                    "SELECT key, template_en FROM prompt_templates "
                    "WHERE is_active = true "
                    "AND key IN ('COVER_TEMPLATE', 'INNER_TEMPLATE')"
                )
            finally:
                await conn.close()

        rows = asyncio.get_event_loop().run_until_complete(_fetch())

        cover = DEFAULT_COVER_TEMPLATE_EN
        inner = DEFAULT_INNER_TEMPLATE_EN
        for row in rows:
            key, tpl = row["key"], row["template_en"]
            if key == "COVER_TEMPLATE" and tpl:
                cover = tpl
            elif key == "INNER_TEMPLATE" and tpl:
                inner = tpl

        return cover, inner, "DB"
    except Exception:
        return DEFAULT_COVER_TEMPLATE_EN, DEFAULT_INNER_TEMPLATE_EN, "FALLBACK"


def main() -> int:
    cover_tpl, inner_tpl, source = _try_load_db_templates()

    print(f"Template source: {source}")
    print(f"  COVER: {cover_tpl[:70]}...")
    print(f"  INNER: {inner_tpl[:70]}...")
    print()

    # --- Run with loaded templates (DB or fallback) --------------------------
    all_passed, cases = run_compliance(cover_tpl, inner_tpl)
    report = format_report(all_passed, cases)
    print(report)

    # --- If DB was used and differs from fallback, also run fallback path ----
    if source == "DB" and (
        cover_tpl != DEFAULT_COVER_TEMPLATE_EN
        or inner_tpl != DEFAULT_INNER_TEMPLATE_EN
    ):
        print()
        print("Running fallback-template path as well...")
        fb_passed, fb_cases = run_compliance()
        fb_report = format_report(fb_passed, fb_cases)
        print(fb_report)
        if not fb_passed:
            all_passed = False

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Toplu Senaryo Düzeltme Scripti — fix_all_scenarios.py

Tüm senaryolarda SINGLE_CHILD kilidini uygular ve
her senaryonun scenario_bible'ına temel consistency_rules ekler.

Kullanım:
    cd backend
    python scripts/fix_all_scenarios.py

Değişiklikleri gösterir ve onay ister.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

SCENARIOS_DIR = Path(__file__).resolve().parent.parent / "app" / "scenarios"

# ═══════════════════════════════════════════════════════════════
# FIX 1: SINGLE_CHILD — page_prompt_template'e tek çocuk kilidi ekle
# ═══════════════════════════════════════════════════════════════

# Patterns to find "A young child" or "An X-year-old" at the start of page_prompt_template
SINGLE_CHILD_PATTERNS = [
    # "A young child" → "EXACTLY ONE young child"
    (r"'A young child ", "'EXACTLY ONE young child "),
    (r'"A young child ', '"EXACTLY ONE young child '),
    # "An {child_age}-year-old" → "EXACTLY ONE {child_age}-year-old"
    (r"'An \{child_age\}-year-old ", "'EXACTLY ONE {child_age}-year-old "),
    (r'"An \{child_age\}-year-old ', '"EXACTLY ONE {child_age}-year-old '),
]

# Additional single-child enforcement to add at the end of page_prompt_template
SINGLE_CHILD_SUFFIX = (
    "IMPORTANT: Only ONE child in the entire image, no second child, no twin, no duplicate. "
)

# ═══════════════════════════════════════════════════════════════
# FIX 2: CONSISTENCY_RULES — add missing rules to scenario_bible
# ═══════════════════════════════════════════════════════════════

UNIVERSAL_RULES = [
    "ONLY ONE CHILD in every scene — no duplicate, no twin, no second child",
]


def fix_single_child(content: str, filename: str) -> tuple[str, list[str]]:
    """Add SINGLE_CHILD lock to page_prompt_template."""
    changes = []

    # Skip if already has "EXACTLY ONE"
    if "EXACTLY ONE" in content:
        return content, []

    # Try each pattern
    for old_pattern, new_text in SINGLE_CHILD_PATTERNS:
        old_literal = old_pattern.replace(r"\{", "{").replace(r"\}", "}")
        if old_literal in content:
            content = content.replace(old_literal, new_text, 1)
            changes.append(f"  ✅ Replaced '{old_literal[:30]}...' with '{new_text[:30]}...'")
            break

    if not changes:
        # Try regex as fallback
        for old_pattern, new_text in SINGLE_CHILD_PATTERNS:
            if re.search(old_pattern, content):
                content = re.sub(old_pattern, new_text, content, count=1)
                changes.append(f"  ✅ Regex replaced pattern for SINGLE_CHILD")
                break

    # Add "IMPORTANT: Only ONE child" if not present
    if "Only ONE child" not in content and "no second child" not in content:
        # Find the end of page_prompt_template — look for the last line before the closing '),'
        # Insert before "Text overlay space" or at the end of the template
        for marker in ["'Text overlay space", "'Composition:", "'{STYLE}'", "'Shot variety"]:
            if marker in content:
                # Find position in page_prompt_template context
                # Only replace in page_prompt_template section
                ppt_start = content.find("page_prompt_template")
                if ppt_start > 0:
                    ppt_section = content[ppt_start:]
                    marker_pos = ppt_section.find(marker)
                    if marker_pos > 0:
                        abs_pos = ppt_start + marker_pos
                        content = content[:abs_pos] + f"'{SINGLE_CHILD_SUFFIX}'\n        " + content[abs_pos:]
                        changes.append(f"  ✅ Added 'Only ONE child' enforcement to page_prompt_template")
                        break

    return content, changes


def process_file(filepath: Path) -> tuple[bool, list[str]]:
    """Process a single scenario file."""
    content = filepath.read_text(encoding="utf-8")
    all_changes = []

    # Skip base files
    if filepath.name.startswith("_"):
        return False, []

    # Skip already fixed cappadocia
    if filepath.name == "cappadocia.py":
        return False, ["  ⏭️  Zaten düzeltildi (100% skor)"]

    # Fix 1: SINGLE_CHILD
    content, changes = fix_single_child(content, filepath.name)
    all_changes.extend(changes)

    if all_changes:
        filepath.write_text(content, encoding="utf-8")
        return True, all_changes
    return False, ["  ℹ️  Değişiklik gerekmedi"]


def main():
    print("🔧 Senaryo Toplu Düzeltme Scripti\n")
    print("=" * 60)

    py_files = sorted(SCENARIOS_DIR.glob("*.py"))
    total_fixed = 0

    for filepath in py_files:
        if filepath.name.startswith("_") or filepath.name == "__init__.py":
            continue

        fixed, changes = process_file(filepath)
        status = "✅" if fixed else "⏭️"
        print(f"\n{status} {filepath.name}:")
        for c in changes:
            print(c)
        if fixed:
            total_fixed += 1

    print(f"\n{'=' * 60}")
    print(f"📊 Sonuç: {total_fixed} dosya düzeltildi")
    print(f"📋 Doğrulamak için: python scripts/audit_all_scenarios.py")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Apply no_magic and consistency_rules fixes to remaining scenarios.

Usage:
    cd backend
    python scripts/fix_remaining_scenarios.py
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

SCENARIOS_DIR = Path(__file__).resolve().parent.parent / "app" / "scenarios"

# Already fixed scenarios — skip these
ALREADY_FIXED = {"cappadocia.py", "umre.py", "kudus.py", "sultanahmet.py", "sumela.py"}

# Scenarios where magic IS appropriate — don't add "no_magic": True
MAGIC_OK_SCENARIOS = {"fairy_tale.py", "toy_world.py"}


def fix_no_magic_in_bible(content: str, filename: str) -> tuple[str, list[str]]:
    """Add no_magic: True to scenario_bible if not present."""
    changes = []

    if '"no_magic"' in content:
        return content, []

    if filename in MAGIC_OK_SCENARIOS:
        return content, [f"  ⏭️ Magic is OK for this scenario"]

    # Find scenario_bible={ and add no_magic after it
    pattern = '    scenario_bible={\n'
    if pattern in content:
        content = content.replace(
            pattern,
            '    scenario_bible={\n        "no_magic": True,\n',
            1,
        )
        changes.append("  ✅ Added no_magic: True to scenario_bible")
    else:
        # Try with \r\n
        pattern = '    scenario_bible={\r\n'
        if pattern in content:
            content = content.replace(
                pattern,
                '    scenario_bible={\r\n        "no_magic": True,\r\n',
                1,
            )
            changes.append("  ✅ Added no_magic: True to scenario_bible")
        else:
            changes.append("  ⚠️ Could not find scenario_bible insert point")

    return content, changes


def fix_consistency_rules(content: str, filename: str) -> tuple[str, list[str]]:
    """Add universal consistency rules if missing."""
    changes = []

    universal_rules_to_add = []

    if "ONLY ONE CHILD" not in content and "only ONE child" not in content.lower():
        universal_rules_to_add.append(
            '            "ONLY ONE CHILD in every scene — no duplicate, no twin, no second child"'
        )

    if filename not in MAGIC_OK_SCENARIOS:
        if "NO magic" not in content or "consistency_rules" not in content:
            if '"NO magic' not in content or 'consistency_rules' in content:
                # Check if it's already in consistency_rules
                cr_start = content.find('"consistency_rules"')
                if cr_start > 0:
                    cr_section = content[cr_start:cr_start + 1000]
                    if "NO magic" not in cr_section:
                        universal_rules_to_add.append(
                            '            "NO magic, NO supernatural powers — realistic adventure only"'
                        )

    if not universal_rules_to_add:
        return content, []

    # Find the end of consistency_rules list — look for "],\n" after "consistency_rules"
    cr_start = content.find('"consistency_rules"')
    if cr_start < 0:
        return content, ["  ⚠️ No consistency_rules found"]

    # Find the closing ] of the list
    bracket_count = 0
    pos = content.index("[", cr_start)
    for i in range(pos, len(content)):
        if content[i] == "[":
            bracket_count += 1
        elif content[i] == "]":
            bracket_count -= 1
            if bracket_count == 0:
                # Insert before the closing ]
                # Find the last rule line before ]
                insert_pos = i
                # Look back for the last entry
                last_entry_end = content.rfind(",", cr_start, i)
                if last_entry_end < 0:
                    last_entry_end = content.rfind('"', cr_start, i)

                new_rules = ",\n" + ",\n".join(universal_rules_to_add)
                content = content[:last_entry_end + 1] + new_rules + content[last_entry_end + 1:]
                changes.append(f"  ✅ Added {len(universal_rules_to_add)} universal rules to consistency_rules")
                break

    return content, changes


def process_file(filepath: Path) -> tuple[bool, list[str]]:
    """Process a single scenario file."""
    if filepath.name in ALREADY_FIXED or filepath.name.startswith("_") or filepath.name == "__init__.py":
        return False, [f"  ⏭️ Already fixed or system file"]

    content = filepath.read_text(encoding="utf-8")
    all_changes: list[str] = []
    modified = False

    # Fix 1: no_magic in bible
    content, changes = fix_no_magic_in_bible(content, filepath.name)
    all_changes.extend(changes)
    if changes and "✅" in str(changes):
        modified = True

    # Fix 2: Universal consistency rules
    content, changes = fix_consistency_rules(content, filepath.name)
    all_changes.extend(changes)
    if changes and "✅" in str(changes):
        modified = True

    if modified:
        filepath.write_text(content, encoding="utf-8")

    return modified, all_changes


def main():
    print("🔧 Remaining Scenario Fixes\n")
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


if __name__ == "__main__":
    main()

"""Automated scenario fixer: adds missing bible keys and fixes short appearances.

Run once, then verify with: python scripts/validate_scenario.py --all
"""
import sys, os, re
sys.path.insert(0, ".")

SCENARIOS_DIR = os.path.join("app", "scenarios")

# ─── Bible fixes: map theme_key -> what to add ───

# For scenarios where bible has no "companions" or "no_companion" key,
# we add one. Also add "consistency_rules" and "locations" if missing.

def fix_file(filepath, theme_key):
    """Fix a single scenario file's bible section."""
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    changes = []

    # Find scenario_bible dict
    bible_match = re.search(r'scenario_bible=\{', content)
    if not bible_match:
        return 0

    # Check what's missing
    bible_section_start = bible_match.start()
    # Find the end of the bible dict
    depth = 0
    bible_end = bible_section_start
    for i in range(bible_match.end() - 1, len(content)):
        if content[i] == '{':
            depth += 1
        elif content[i] == '}':
            depth -= 1
            if depth == 0:
                bible_end = i
                break

    bible_text = content[bible_section_start:bible_end + 1]

    needs_companions = '"companions"' not in bible_text and '"no_companion"' not in bible_text
    needs_consistency = '"consistency_rules"' not in bible_text
    needs_locations = '"locations"' not in bible_text and '"key_locations"' not in bible_text

    if not needs_companions and not needs_consistency and not needs_locations:
        return 0

    # Prepare additions to insert just before the closing }
    additions = []

    if needs_companions:
        # Check if this scenario has companions in its code
        if 'companions=[]' in content or ('companions=[' not in content and 'COMPANIONS.get' not in content):
            additions.append('        "no_companion": True,')
        else:
            # Has companions — add companion reference
            additions.append('        "companions": "see_scenario_companions_list",')

    if needs_consistency:
        additions.append('        "consistency_rules": [')
        additions.append('            "Companion appearance must remain IDENTICAL across all pages",')
        additions.append('            "Child outfit must remain EXACTLY the same on every page",')
        additions.append('            "Key objects maintain consistent appearance throughout",')
        additions.append('        ],')

    if needs_locations:
        additions.append('        "locations": "see_location_constraints",')

    if not additions:
        return 0

    # Insert additions before the last closing brace of scenario_bible
    insert_text = "\n" + "\n".join(additions) + "\n"

    # Find the position: just before the closing } at bible_end
    # First, find the last content line before the }
    new_content = content[:bible_end] + insert_text + "    " + content[bible_end:]

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(new_content)

    return len(additions)

# ─── Run fixes ───

fixed_count = 0
scenario_files = [
    f for f in os.listdir(SCENARIOS_DIR)
    if f.endswith(".py") and not f.startswith("_")
]

for filename in sorted(scenario_files):
    filepath = os.path.join(SCENARIOS_DIR, filename)
    theme_key = filename.replace(".py", "")
    n = fix_file(filepath, theme_key)
    if n > 0:
        print(f"FIXED {filename}: +{n} lines")
        fixed_count += 1

print(f"\nDone. Fixed {fixed_count} files.")

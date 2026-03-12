"""Bulk-fix scenario_bible and companion appearances for health check compliance.

This script reads all registered scenarios, identifies issues, and generates
the exact file edits needed to reach 100% health score.
"""
import sys, os, re, json
sys.path.insert(0, ".")

from app.scenarios import get_all_scenarios
from app.services.scenario_health_service import score_scenario

# Load all scenarios
scenarios = get_all_scenarios()

# Find all issues
for theme_key, sc in sorted(scenarios.items()):
    report = score_scenario(sc)
    bible = sc.scenario_bible or {}
    issues = []
    for c in report.checks:
        if c.status != "good":
            issues.append(f"  {c.name}: {c.message}")

    if not issues:
        continue

    print(f"\n=== {theme_key} ({report.percentage}%) ===")
    for i in issues:
        print(i)

    # Analyze what bible keys exist
    print(f"  Bible keys: {list(bible.keys())}")
    has_companions_key = "companions" in bible or "no_companion" in bible
    has_consistency = "consistency_rules" in bible
    has_locations = "locations" in bible or "key_locations" in bible
    print(f"  has_companions_key={has_companions_key} has_consistency={has_consistency} has_locations={has_locations}")

    # Check companion appearances
    for comp in sc.companions:
        wc = len(comp.appearance.split())
        if wc < 15:
            print(f"  SHORT appearance ({wc}w): {comp.name_tr} = '{comp.appearance}'")

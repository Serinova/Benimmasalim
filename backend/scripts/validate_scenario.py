#!/usr/bin/env python3
"""Scenario Validation CLI — static health check for all registered scenarios.

Usage:
    # Single scenario
    python scripts/validate_scenario.py --theme_key cappadocia

    # All scenarios (dashboard)
    python scripts/validate_scenario.py --all

    # JSON output
    python scripts/validate_scenario.py --all --json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Add backend to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


# ─────────────────────────────────────────────
# ANSI color helpers
# ─────────────────────────────────────────────

class _C:
    """ANSI color codes for terminal output."""
    RESET = "\033[0m"
    BOLD = "\033[1m"
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    GRAY = "\033[90m"


def _status_icon(status: str) -> str:
    if status == "good":
        return f"{_C.GREEN}✅{_C.RESET}"
    if status == "warning":
        return f"{_C.YELLOW}⚠️{_C.RESET}"
    return f"{_C.RED}❌{_C.RESET}"


def _grade_color(grade: str) -> str:
    colors = {"A": _C.GREEN, "B": _C.BLUE, "C": _C.YELLOW, "D": _C.RED, "F": _C.RED}
    color = colors.get(grade, _C.RESET)
    return f"{color}{_C.BOLD}{grade}{_C.RESET}"


# ─────────────────────────────────────────────
# Display functions
# ─────────────────────────────────────────────

def _print_single_report(report) -> None:
    """Print detailed report for a single scenario."""
    print()
    print(f"{_C.BOLD}{_C.CYAN}{'═' * 60}{_C.RESET}")
    print(f"{_C.BOLD}  📋 {report.name} ({report.theme_key}){_C.RESET}")
    print(f"{_C.BOLD}{_C.CYAN}{'═' * 60}{_C.RESET}")
    print()
    print(f"  {_C.BOLD}Not:{_C.RESET} {_grade_color(report.grade)}  "
          f"({report.total_score}/{report.max_score} = %{report.percentage})")
    print()

    for check in report.checks:
        icon = _status_icon(check.status)
        score_str = f"{check.score}/{check.max_score}"
        print(f"  {icon} {check.label:<25s}  {score_str:>6s}  {_C.GRAY}{check.message}{_C.RESET}")

    print()

    # Summary
    critical = [c for c in report.checks if c.status == "critical"]
    warnings = [c for c in report.checks if c.status == "warning"]

    if critical:
        print(f"  {_C.RED}{_C.BOLD}🔴 KRİTİK ({len(critical)}):{_C.RESET}")
        for c in critical:
            print(f"     • {c.label}: {c.message}")

    if warnings:
        print(f"  {_C.YELLOW}{_C.BOLD}🟡 UYARI ({len(warnings)}):{_C.RESET}")
        for c in warnings:
            print(f"     • {c.label}: {c.message}")

    if not critical and not warnings:
        print(f"  {_C.GREEN}{_C.BOLD}🟢 Tüm kontroller geçti!{_C.RESET}")

    print()


def _print_dashboard(reports: list) -> None:
    """Print all scenarios in a dashboard table."""
    print()
    print(f"{_C.BOLD}{_C.CYAN}{'═' * 80}{_C.RESET}")
    print(f"{_C.BOLD}  📊 SENARYO KALİTE TABLOSU — {len(reports)} senaryo{_C.RESET}")
    print(f"{_C.BOLD}{_C.CYAN}{'═' * 80}{_C.RESET}")
    print()

    # Header
    print(f"  {'Senaryo':<25s} {'Not':<5s} {'%':>4s}  {'✅':>3s} {'⚠️':>3s} {'❌':>3s}  {'Durum'}")
    print(f"  {'─' * 70}")

    # Sort by percentage (best first for dashboard)
    sorted_reports = sorted(reports, key=lambda r: r.percentage, reverse=True)

    for r in sorted_reports:
        good = sum(1 for c in r.checks if c.status == "good")
        warn = sum(1 for c in r.checks if c.status == "warning")
        crit = sum(1 for c in r.checks if c.status == "critical")

        # Status summary
        if crit > 0:
            status_msg = f"{_C.RED}Kritik sorun var{_C.RESET}"
        elif warn > 0:
            status_msg = f"{_C.YELLOW}İyileştirme önerilir{_C.RESET}"
        else:
            status_msg = f"{_C.GREEN}Mükemmel{_C.RESET}"

        name = r.name[:24]
        print(f"  {name:<25s} {_grade_color(r.grade):<14s} {r.percentage:>3d}%  "
              f"{good:>2d}  {warn:>2d}  {crit:>2d}   {status_msg}")

    print()

    # Summary stats
    avg_pct = sum(r.percentage for r in reports) / len(reports)
    a_count = sum(1 for r in reports if r.grade == "A")
    b_count = sum(1 for r in reports if r.grade == "B")
    c_count = sum(1 for r in reports if r.grade == "C")
    low_count = sum(1 for r in reports if r.grade in ("D", "F"))

    print(f"  {_C.BOLD}Ortalama:{_C.RESET} %{avg_pct:.0f}  |  "
          f"{_C.GREEN}A:{a_count}{_C.RESET}  "
          f"{_C.BLUE}B:{b_count}{_C.RESET}  "
          f"{_C.YELLOW}C:{c_count}{_C.RESET}  "
          f"{_C.RED}D/F:{low_count}{_C.RESET}")
    print()


def _output_json(reports: list) -> None:
    """Output all reports as JSON."""
    data = []
    for r in reports:
        data.append({
            "theme_key": r.theme_key,
            "name": r.name,
            "grade": r.grade,
            "percentage": r.percentage,
            "total_score": r.total_score,
            "max_score": r.max_score,
            "checks": [
                {
                    "name": c.name,
                    "label": c.label,
                    "status": c.status,
                    "score": c.score,
                    "max_score": c.max_score,
                    "message": c.message,
                }
                for c in r.checks
            ],
        })
    print(json.dumps(data, ensure_ascii=False, indent=2))


# ─────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Scenario health check — static validation for registered scenarios"
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--theme_key", help="Validate a single scenario by theme_key")
    group.add_argument("--all", action="store_true", help="Validate all scenarios (dashboard)")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    # Import here to trigger scenario registration
    from app.scenarios import get_all_scenarios, get_scenario_content
    from app.services.scenario_health_service import (
        get_all_scenario_health,
        score_scenario,
    )

    if args.theme_key:
        content = get_scenario_content(args.theme_key)
        if not content:
            available = ", ".join(sorted(get_all_scenarios().keys()))
            print(f"{_C.RED}Hata: '{args.theme_key}' bulunamadı.{_C.RESET}")
            print(f"Mevcut senaryolar: {available}")
            sys.exit(1)

        report = score_scenario(content)
        if args.json:
            _output_json([report])
        else:
            _print_single_report(report)

    elif args.all:
        reports = get_all_scenario_health()
        if args.json:
            _output_json(reports)
        else:
            _print_dashboard(reports)


if __name__ == "__main__":
    main()

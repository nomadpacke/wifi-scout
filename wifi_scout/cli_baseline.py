"""CLI subcommands for baseline capture and comparison."""
from __future__ import annotations

import argparse
import sys

from wifi_scout.baseline import build_baseline, compare, load_baseline, save_baseline
from wifi_scout.baseline_report import (
    export_comparison_json,
    format_comparison_text,
)
from wifi_scout.storage import load_samples


def cmd_baseline(args: argparse.Namespace) -> int:
    """Capture current DB samples as the new baseline."""
    try:
        samples = load_samples(args.db)
    except FileNotFoundError:
        print(f"Error: database not found: {args.db}", file=sys.stderr)
        return 1

    if not samples:
        print("No samples found in database — cannot create baseline.", file=sys.stderr)
        return 1

    entries = build_baseline(samples)
    save_baseline(entries, args.baseline_path)
    print(
        f"Baseline saved: {len(entries)} SSID(s), "
        f"{sum(e.sample_count for e in entries.values())} sample(s) → {args.baseline_path}"
    )
    return 0


def cmd_compare(args: argparse.Namespace) -> int:
    """Compare the latest DB samples against the stored baseline."""
    try:
        samples = load_samples(args.db)
    except FileNotFoundError:
        print(f"Error: database not found: {args.db}", file=sys.stderr)
        return 1

    baseline = load_baseline(args.baseline_path)
    if not baseline:
        print(
            f"No baseline found at {args.baseline_path}. "
            "Run 'wifi-scout baseline capture' first.",
            file=sys.stderr,
        )
        return 1

    comparisons = compare(samples, baseline)
    if not comparisons:
        print("No matching SSIDs between current samples and baseline.")
        return 0

    print(format_comparison_text(comparisons))

    if args.json_out:
        export_comparison_json(comparisons, args.json_out)
        print(f"\nJSON report written to {args.json_out}")

    return 0


def add_baseline_subparsers(subparsers: argparse._SubParsersAction, default_baseline: str) -> None:
    p = subparsers.add_parser("baseline", help="Baseline capture and comparison")
    bp = p.add_subparsers(dest="baseline_cmd", required=True)

    cap = bp.add_parser("capture", help="Save current DB as baseline")
    cap.add_argument("--db", required=True, help="Path to SQLite database")
    cap.add_argument("--baseline-path", default=default_baseline)
    cap.set_defaults(func=cmd_baseline)

    cmp = bp.add_parser("compare", help="Compare current DB against baseline")
    cmp.add_argument("--db", required=True, help="Path to SQLite database")
    cmp.add_argument("--baseline-path", default=default_baseline)
    cmp.add_argument("--json-out", default=None, help="Optional JSON export path")
    cmp.set_defaults(func=cmd_compare)

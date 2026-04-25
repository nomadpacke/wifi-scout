"""CLI subcommand: heatmap — build and export a signal heatmap."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from wifi_scout.heatmap import build_heatmap
from wifi_scout.heatmap_export import (
    export_heatmap_csv,
    export_heatmap_json,
    heatmap_text_summary,
)
from wifi_scout.location import list_locations
from wifi_scout.storage import load_samples


def cmd_heatmap(args: argparse.Namespace) -> int:
    """Build a heatmap from stored samples and export or print it."""
    db_path = Path(args.db)
    if not db_path.exists():
        print(f"Error: database not found: {db_path}", file=sys.stderr)
        return 1

    samples = load_samples(str(db_path), location=args.location or None)
    if not samples:
        print("No samples found in database.", file=sys.stderr)
        return 1

    locations = list_locations(args.location_store)
    if not locations:
        print("No locations defined. Add locations first with `wifi-scout location add`.",
              file=sys.stderr)
        return 1

    cells = build_heatmap(samples, locations)
    if not cells:
        print("No heatmap data: ensure samples have matching location names.", file=sys.stderr)
        return 1

    if args.format == "json":
        out = args.output or "heatmap.json"
        export_heatmap_json(cells, out)
        print(f"Heatmap exported to {out}")
    elif args.format == "csv":
        out = args.output or "heatmap.csv"
        export_heatmap_csv(cells, out)
        print(f"Heatmap exported to {out}")
    else:
        print(heatmap_text_summary(cells))

    return 0


def add_heatmap_subparser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser("heatmap", help="Build and export a WiFi signal heatmap")
    p.add_argument("--db", default="wifi_scout.db", help="Path to SQLite database")
    p.add_argument("--location-store", default="locations.json",
                   help="Path to locations JSON store")
    p.add_argument("--location", default="", help="Filter samples by location name")
    p.add_argument("--format", choices=["text", "json", "csv"], default="text",
                   help="Output format (default: text)")
    p.add_argument("--output", default="", help="Output file path (json/csv formats)")
    p.set_defaults(func=cmd_heatmap)

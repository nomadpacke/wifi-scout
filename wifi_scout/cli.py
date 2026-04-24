"""Command-line interface for wifi-scout."""

import argparse
import sys
from pathlib import Path

from wifi_scout.scanner import scan
from wifi_scout.storage import save_samples, load_samples
from wifi_scout.reporter import summarize, export_json, export_csv


DEFAULT_DB = Path.home() / ".wifi_scout" / "data.db"


def cmd_scan(args: argparse.Namespace) -> int:
    """Run a WiFi scan and persist the results."""
    db_path = Path(args.db)
    db_path.parent.mkdir(parents=True, exist_ok=True)

    samples = scan(location=args.location)
    if not samples:
        print("No WiFi networks found.", file=sys.stderr)
        return 1

    save_samples(db_path, samples)
    print(f"Saved {len(samples)} sample(s) from location '{args.location}'.")
    return 0


def cmd_report(args: argparse.Namespace) -> int:
    """Summarise stored samples and optionally export them."""
    db_path = Path(args.db)
    if not db_path.exists():
        print(f"Database not found: {db_path}", file=sys.stderr)
        return 1

    samples = load_samples(db_path, location=args.location or None)
    summary = summarize(samples)

    print(f"Networks : {summary['network_count']}")
    print(f"Samples  : {summary['sample_count']}")
    if summary["avg_signal_dbm"] is not None:
        print(f"Avg signal : {summary['avg_signal_dbm']:.1f} dBm  "
              f"(quality {summary['avg_quality']:.1f}%)")
        print(f"Best SSID  : {summary['best_ssid']} @ {summary['best_signal_dbm']} dBm")

    if args.json:
        export_json(samples, args.json)
        print(f"JSON exported → {args.json}")
    if args.csv:
        export_csv(samples, args.csv)
        print(f"CSV  exported → {args.csv}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="wifi-scout",
        description="Benchmark and log WiFi quality across locations.",
    )
    parser.add_argument("--db", default=str(DEFAULT_DB), metavar="PATH",
                        help="SQLite database path (default: %(default)s)")

    sub = parser.add_subparsers(dest="command", required=True)

    p_scan = sub.add_parser("scan", help="Scan nearby networks and save results.")
    p_scan.add_argument("--location", default="unknown",
                        help="Label for the current measurement location.")
    p_scan.set_defaults(func=cmd_scan)

    p_report = sub.add_parser("report", help="Display summary and export reports.")
    p_report.add_argument("--location", default="",
                          help="Filter by location label (empty = all).")
    p_report.add_argument("--json", metavar="FILE", default="",
                          help="Export samples to JSON file.")
    p_report.add_argument("--csv", metavar="FILE", default="",
                          help="Export samples to CSV file.")
    p_report.set_defaults(func=cmd_report)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    sys.exit(args.func(args))


if __name__ == "__main__":
    main()

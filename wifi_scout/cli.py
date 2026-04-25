"""CLI entry point for wifi-scout."""

import argparse
import sys
import logging

from wifi_scout.scanner import scan
from wifi_scout.storage import save_samples, load_samples
from wifi_scout.reporter import summarize, export_json, export_csv
from wifi_scout.scheduler import ScanScheduler

logger = logging.getLogger(__name__)


def cmd_scan(args) -> int:
    samples = scan(location=args.location)
    if not samples:
        print("No networks found.", file=sys.stderr)
        return 1
    save_samples(samples, db_path=args.db)
    print(f"Saved {len(samples)} network(s) from location '{args.location}'.")
    return 0


def cmd_report(args) -> int:
    import os
    if not os.path.exists(args.db):
        print(f"Database not found: {args.db}", file=sys.stderr)
        return 1
    samples = load_samples(db_path=args.db, location=args.location)
    summary = summarize(samples)
    if args.format == "json":
        print(export_json(summary))
    elif args.format == "csv":
        print(export_csv(summary))
    else:
        for row in summary:
            print(row)
    return 0


def cmd_watch(args) -> int:
    """Continuously scan at a fixed interval."""
    print(
        f"Starting scheduled scans every {args.interval}s "
        f"(location={args.location!r}, max_runs={args.max_runs})"
    )
    scheduler = ScanScheduler(
        scan_fn=scan,
        save_fn=lambda s: save_samples(s, db_path=args.db),
        interval=args.interval,
        location=args.location,
        max_runs=args.max_runs if args.max_runs > 0 else None,
    )
    try:
        scheduler.start()
    except KeyboardInterrupt:
        print(f"\nStopped after {scheduler.run_count} run(s).")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="wifi-scout",
        description="Benchmark and log WiFi quality across locations.",
    )
    parser.add_argument("--db", default="wifi_scout.db", help="SQLite database path")
    sub = parser.add_subparsers(dest="command")

    p_scan = sub.add_parser("scan", help="Run a one-shot WiFi scan")
    p_scan.add_argument("--location", default="unknown")

    p_report = sub.add_parser("report", help="Print a summary report")
    p_report.add_argument("--location", default=None)
    p_report.add_argument("--format", choices=["text", "json", "csv"], default="text")

    p_watch = sub.add_parser("watch", help="Continuously scan at an interval")
    p_watch.add_argument("--location", default="unknown")
    p_watch.add_argument("--interval", type=float, default=60.0, help="Seconds between scans")
    p_watch.add_argument("--max-runs", type=int, default=0, dest="max_runs",
                         help="Stop after N runs (0 = run forever)")

    return parser


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    parser = build_parser()
    args = parser.parse_args()
    dispatch = {"scan": cmd_scan, "report": cmd_report, "watch": cmd_watch}
    if args.command not in dispatch:
        parser.print_help()
        sys.exit(1)
    sys.exit(dispatch[args.command](args))


if __name__ == "__main__":
    main()

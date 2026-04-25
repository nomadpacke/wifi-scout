"""CLI subcommand for anomaly detection on stored WiFi samples."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from wifi_scout.anomaly import detect_anomalies, anomaly_summary_text
from wifi_scout.storage import load_samples


def cmd_anomaly(args: argparse.Namespace) -> int:
    """Run anomaly detection on samples from the database.

    Returns 0 on success, non-zero on error.
    """
    db = Path(args.db)
    if not db.exists():
        print(f"Error: database not found: {db}", file=sys.stderr)
        return 1

    samples = load_samples(str(db), ssid=args.ssid or None)
    if not samples:
        print("No samples found.", file=sys.stderr)
        return 1

    threshold = args.threshold
    fields = args.fields.split(",") if args.fields else None

    anomalies = detect_anomalies(samples, threshold=threshold, fields=fields)
    print(anomaly_summary_text(anomalies))

    if args.verbose and anomalies:
        print()
        for a in anomalies:
            ts = a.sample.timestamp
            print(
                f"  [{ts}] ssid={a.sample.ssid} "
                f"field={a.field} value={a.value} z={a.z_score}"
            )

    return 0


def add_anomaly_subparser(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    """Register the 'anomaly' subcommand."""
    p = subparsers.add_parser(
        "anomaly",
        help="Detect anomalous WiFi samples using z-score analysis.",
    )
    p.add_argument("--db", required=True, help="Path to SQLite database.")
    p.add_argument("--ssid", default=None, help="Filter samples by SSID.")
    p.add_argument(
        "--threshold",
        type=float,
        default=2.0,
        help="Z-score threshold for anomaly detection (default: 2.0).",
    )
    p.add_argument(
        "--fields",
        default=None,
        help="Comma-separated fields to analyze (default: signal_dbm,latency_ms).",
    )
    p.add_argument(
        "--verbose",
        action="store_true",
        help="Print per-anomaly details.",
    )
    p.set_defaults(func=cmd_anomaly)

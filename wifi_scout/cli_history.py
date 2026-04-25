"""CLI sub-command: `wifi-scout history` — show signal stability for stored samples."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from wifi_scout.signal_history import DROP_THRESHOLD, SignalHistory
from wifi_scout.storage import load_samples


def cmd_history(args: argparse.Namespace) -> int:
    """Print a stability report grouped by SSID."""
    db = Path(args.db)
    if not db.exists():
        print(f"[error] database not found: {db}", file=sys.stderr)
        return 1

    samples = load_samples(str(db), location=getattr(args, "location", None))
    if not samples:
        print("No samples found.", file=sys.stderr)
        return 1

    window: int = args.window
    drop_threshold: int = args.drop_threshold

    # Group samples by SSID preserving insertion order
    histories: dict[str, SignalHistory] = {}
    for s in samples:
        if s.ssid not in histories:
            histories[s.ssid] = SignalHistory(s.ssid, window=window)
        histories[s.ssid].add(s)

    printed = 0
    for ssid, hist in histories.items():
        report = hist.report(drop_threshold=drop_threshold)
        if report is None:
            print(f"{ssid}: insufficient data (<2 samples)")
            continue

        stability = "STABLE" if report.stable else "UNSTABLE"
        print(
            f"{ssid}: [{stability}] "
            f"n={report.sample_count} "
            f"mean={report.mean_signal:.1f} dBm "
            f"std={report.std_signal:.1f} "
            f"range=[{report.min_signal}, {report.max_signal}] "
            f"drops={report.drop_count}"
        )
        printed += 1

    if printed == 0:
        print("All SSIDs have insufficient data.")
        return 1

    return 0


def add_history_subparser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser(
        "history",
        help="Show rolling signal stability report per SSID.",
    )
    p.add_argument("--db", required=True, help="Path to SQLite database.")
    p.add_argument(
        "--location",
        default=None,
        help="Filter samples by location name.",
    )
    p.add_argument(
        "--window",
        type=int,
        default=20,
        help="Rolling window size (default: 20).",
    )
    p.add_argument(
        "--drop-threshold",
        dest="drop_threshold",
        type=int,
        default=DROP_THRESHOLD,
        help=f"Signal dBm below which a sample counts as a drop (default: {DROP_THRESHOLD}).",
    )
    p.set_defaults(func=cmd_history)

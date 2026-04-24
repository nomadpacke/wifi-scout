"""Generate exportable reports from WiFi scan samples."""

from __future__ import annotations

import csv
import io
import json
import statistics
from datetime import datetime
from typing import List, Optional

from wifi_scout.scanner import WiFiSample, signal_quality


def _sample_to_dict(sample: WiFiSample) -> dict:
    return {
        "timestamp": sample.timestamp.isoformat(),
        "location": sample.location,
        "ssid": sample.ssid,
        "bssid": sample.bssid,
        "signal_dbm": sample.signal_dbm,
        "frequency_mhz": sample.frequency_mhz,
        "quality_pct": signal_quality(sample.signal_dbm),
    }


def summarize(samples: List[WiFiSample]) -> dict:
    """Return aggregate statistics for a list of samples."""
    if not samples:
        return {}

    signals = [s.signal_dbm for s in samples]
    qualities = [signal_quality(s) for s in signals]
    locations = sorted({s.location for s in samples if s.location})
    ssids = sorted({s.ssid for s in samples})

    return {
        "sample_count": len(samples),
        "locations": locations,
        "ssids": ssids,
        "signal_dbm": {
            "min": min(signals),
            "max": max(signals),
            "mean": round(statistics.mean(signals), 2),
            "stdev": round(statistics.stdev(signals), 2) if len(signals) > 1 else 0.0,
        },
        "quality_pct": {
            "min": min(qualities),
            "max": max(qualities),
            "mean": round(statistics.mean(qualities), 2),
        },
        "period": {
            "start": min(s.timestamp for s in samples).isoformat(),
            "end": max(s.timestamp for s in samples).isoformat(),
        },
    }


def export_json(
    samples: List[WiFiSample],
    include_summary: bool = True,
) -> str:
    """Serialize samples (and optional summary) to a JSON string."""
    payload: dict = {"samples": [_sample_to_dict(s) for s in samples]}
    if include_summary:
        payload["summary"] = summarize(samples)
    return json.dumps(payload, indent=2)


def export_csv(samples: List[WiFiSample]) -> str:
    """Serialize samples to a CSV string."""
    fieldnames = [
        "timestamp",
        "location",
        "ssid",
        "bssid",
        "signal_dbm",
        "frequency_mhz",
        "quality_pct",
    ]
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=fieldnames, lineterminator="\n")
    writer.writeheader()
    for sample in samples:
        writer.writerow(_sample_to_dict(sample))
    return buf.getvalue()

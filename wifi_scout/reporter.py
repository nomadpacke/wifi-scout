"""Report generation: summarize, export JSON/CSV, and trend summaries."""
from __future__ import annotations

import csv
import json
from io import StringIO
from statistics import mean
from typing import Any, Dict, List, Optional

from wifi_scout.scanner import WiFiSample
from wifi_scout.trend import TrendReport, analyze


def _sample_to_dict(s: WiFiSample) -> Dict[str, Any]:
    return {
        "ssid": s.ssid,
        "bssid": s.bssid,
        "signal_dbm": s.signal_dbm,
        "quality": s.quality,
        "channel": s.channel,
        "latency_ms": s.latency_ms,
    }


def summarize(samples: List[WiFiSample]) -> Dict[str, Any]:
    """Return high-level statistics for a list of samples."""
    if not samples:
        return {"count": 0, "networks": []}

    by_ssid: Dict[str, List[WiFiSample]] = {}
    for s in samples:
        by_ssid.setdefault(s.ssid, []).append(s)

    networks = []
    for ssid, group in by_ssid.items():
        signals = [s.signal_dbm for s in group]
        latencies = [s.latency_ms for s in group if s.latency_ms is not None]
        networks.append(
            {
                "ssid": ssid,
                "samples": len(group),
                "avg_signal_dbm": round(mean(signals), 2),
                "min_signal_dbm": min(signals),
                "max_signal_dbm": max(signals),
                "avg_quality": round(mean(s.quality for s in group), 2),
                "avg_latency_ms": round(mean(latencies), 2) if latencies else None,
            }
        )

    return {"count": len(samples), "networks": networks}


def export_json(samples: List[WiFiSample], include_trends: bool = False) -> str:
    """Serialize samples (and optionally trends) to a JSON string."""
    payload: Dict[str, Any] = {"samples": [_sample_to_dict(s) for s in samples]}
    if include_trends:
        trends = analyze(samples)
        payload["trends"] = [
            {
                "ssid": t.ssid,
                "sample_count": t.sample_count,
                "avg_signal": t.avg_signal,
                "avg_quality": t.avg_quality,
                "signal_stdev": t.signal_stdev,
                "min_signal": t.min_signal,
                "max_signal": t.max_signal,
                "trend": t.trend,
                "avg_latency_ms": t.avg_latency_ms,
            }
            for t in trends
        ]
    return json.dumps(payload, indent=2)


def export_csv(samples: List[WiFiSample]) -> str:
    """Serialize samples to a CSV string."""
    output = StringIO()
    fieldnames = ["ssid", "bssid", "signal_dbm", "quality", "channel", "latency_ms"]
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    for s in samples:
        writer.writerow(_sample_to_dict(s))
    return output.getvalue()


def trend_summary_text(samples: List[WiFiSample]) -> str:
    """Return a human-readable trend summary string."""
    reports: List[TrendReport] = analyze(samples)
    if not reports:
        return "No trend data available."
    lines = []
    for r in reports:
        latency_str = f", avg latency {r.avg_latency_ms} ms" if r.avg_latency_ms is not None else ""
        lines.append(
            f"{r.ssid}: {r.trend} | avg signal {r.avg_signal} dBm"
            f" (±{r.signal_stdev}) | avg quality {r.avg_quality}%{latency_str}"
        )
    return "\n".join(lines)

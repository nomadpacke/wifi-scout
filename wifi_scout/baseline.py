"""Baseline comparison: compare current scan results against a stored baseline."""
from __future__ import annotations

import json
import os
from dataclasses import dataclass
from statistics import mean
from typing import Dict, List, Optional

from wifi_scout.scanner import WiFiSample

_DEFAULT_PATH = os.path.join(os.path.expanduser("~"), ".wifi_scout", "baseline.json")


@dataclass
class BaselineEntry:
    ssid: str
    avg_signal: float
    avg_quality: float
    avg_latency: float
    sample_count: int


@dataclass
class BaselineComparison:
    ssid: str
    signal_delta: float   # positive = better than baseline
    quality_delta: float
    latency_delta: float  # negative = better (lower latency)
    baseline: BaselineEntry


def build_baseline(samples: List[WiFiSample]) -> Dict[str, BaselineEntry]:
    """Aggregate samples by SSID into baseline entries."""
    grouped: Dict[str, List[WiFiSample]] = {}
    for s in samples:
        grouped.setdefault(s.ssid, []).append(s)

    result: Dict[str, BaselineEntry] = {}
    for ssid, group in grouped.items():
        result[ssid] = BaselineEntry(
            ssid=ssid,
            avg_signal=mean(s.signal_dbm for s in group),
            avg_quality=mean(s.quality for s in group),
            avg_latency=mean(s.latency_ms for s in group if s.latency_ms is not None)
            if any(s.latency_ms is not None for s in group)
            else 0.0,
            sample_count=len(group),
        )
    return result


def save_baseline(entries: Dict[str, BaselineEntry], path: str = _DEFAULT_PATH) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    data = [
        {
            "ssid": e.ssid,
            "avg_signal": e.avg_signal,
            "avg_quality": e.avg_quality,
            "avg_latency": e.avg_latency,
            "sample_count": e.sample_count,
        }
        for e in entries.values()
    ]
    with open(path, "w") as fh:
        json.dump(data, fh, indent=2)


def load_baseline(path: str = _DEFAULT_PATH) -> Dict[str, BaselineEntry]:
    if not os.path.exists(path):
        return {}
    with open(path) as fh:
        data = json.load(fh)
    return {
        d["ssid"]: BaselineEntry(
            ssid=d["ssid"],
            avg_signal=d["avg_signal"],
            avg_quality=d["avg_quality"],
            avg_latency=d["avg_latency"],
            sample_count=d["sample_count"],
        )
        for d in data
    }


def compare(
    current: List[WiFiSample],
    baseline: Dict[str, BaselineEntry],
) -> List[BaselineComparison]:
    """Return comparisons for SSIDs present in both current scan and baseline."""
    current_summary = build_baseline(current)
    comparisons: List[BaselineComparison] = []
    for ssid, entry in baseline.items():
        if ssid not in current_summary:
            continue
        cur = current_summary[ssid]
        comparisons.append(
            BaselineComparison(
                ssid=ssid,
                signal_delta=cur.avg_signal - entry.avg_signal,
                quality_delta=cur.avg_quality - entry.avg_quality,
                latency_delta=cur.avg_latency - entry.avg_latency,
                baseline=entry,
            )
        )
    return comparisons

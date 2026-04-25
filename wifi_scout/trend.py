"""Trend analysis for WiFi signal samples over time."""
from __future__ import annotations

from dataclasses import dataclass
from statistics import mean, stdev
from typing import List, Optional

from wifi_scout.scanner import WiFiSample


@dataclass
class TrendReport:
    ssid: str
    sample_count: int
    avg_signal: float
    avg_quality: float
    signal_stdev: float
    min_signal: int
    max_signal: int
    trend: str  # 'improving', 'degrading', 'stable'
    avg_latency_ms: Optional[float]


def _linear_slope(values: List[float]) -> float:
    """Return the slope of a simple linear regression over index-ordered values."""
    n = len(values)
    if n < 2:
        return 0.0
    xs = list(range(n))
    x_mean = mean(xs)
    y_mean = mean(values)
    numerator = sum((x - x_mean) * (y - y_mean) for x, y in zip(xs, values))
    denominator = sum((x - x_mean) ** 2 for x in xs)
    return numerator / denominator if denominator != 0 else 0.0


def _classify_trend(slope: float, threshold: float = 0.5) -> str:
    if slope > threshold:
        return "improving"
    if slope < -threshold:
        return "degrading"
    return "stable"


def analyze(samples: List[WiFiSample], ssid: Optional[str] = None) -> List[TrendReport]:
    """Analyze trends grouped by SSID (or filtered to a single SSID)."""
    if ssid:
        samples = [s for s in samples if s.ssid == ssid]

    groups: dict[str, List[WiFiSample]] = {}
    for s in samples:
        groups.setdefault(s.ssid, []).append(s)

    reports: List[TrendReport] = []
    for name, group in groups.items():
        signals = [s.signal_dbm for s in group]
        qualities = [s.quality for s in group]
        latencies = [s.latency_ms for s in group if s.latency_ms is not None]

        slope = _linear_slope([float(v) for v in signals])
        reports.append(
            TrendReport(
                ssid=name,
                sample_count=len(group),
                avg_signal=round(mean(signals), 2),
                avg_quality=round(mean(qualities), 2),
                signal_stdev=round(stdev(signals) if len(signals) > 1 else 0.0, 2),
                min_signal=min(signals),
                max_signal=max(signals),
                trend=_classify_trend(slope),
                avg_latency_ms=round(mean(latencies), 2) if latencies else None,
            )
        )
    return reports

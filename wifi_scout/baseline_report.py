"""Formatting helpers for baseline comparison results."""
from __future__ import annotations

import json
from typing import List

from wifi_scout.baseline import BaselineComparison


def _arrow(delta: float, higher_is_better: bool = True) -> str:
    if abs(delta) < 0.5:
        return "="
    if (delta > 0) == higher_is_better:
        return "▲"
    return "▼"


def format_comparison_text(comparisons: List[BaselineComparison]) -> str:
    if not comparisons:
        return "No baseline comparisons available."

    lines = ["Baseline Comparison", "=" * 50]
    for c in comparisons:
        sig_arrow = _arrow(c.signal_delta, higher_is_better=True)
        qual_arrow = _arrow(c.quality_delta, higher_is_better=True)
        lat_arrow = _arrow(c.latency_delta, higher_is_better=False)
        lines.append(f"SSID : {c.ssid}")
        lines.append(
            f"  Signal  : {c.signal_delta:+.1f} dBm {sig_arrow}  "
            f"(baseline {c.baseline.avg_signal:.1f} dBm)"
        )
        lines.append(
            f"  Quality : {c.quality_delta:+.1f}%   {qual_arrow}  "
            f"(baseline {c.baseline.avg_quality:.1f}%)"
        )
        lines.append(
            f"  Latency : {c.latency_delta:+.1f} ms  {lat_arrow}  "
            f"(baseline {c.baseline.avg_latency:.1f} ms)"
        )
        lines.append("")
    return "\n".join(lines).rstrip()


def comparisons_to_dicts(comparisons: List[BaselineComparison]) -> list:
    return [
        {
            "ssid": c.ssid,
            "signal_delta": round(c.signal_delta, 2),
            "quality_delta": round(c.quality_delta, 2),
            "latency_delta": round(c.latency_delta, 2),
            "baseline_avg_signal": round(c.baseline.avg_signal, 2),
            "baseline_avg_quality": round(c.baseline.avg_quality, 2),
            "baseline_avg_latency": round(c.baseline.avg_latency, 2),
            "baseline_sample_count": c.baseline.sample_count,
        }
        for c in comparisons
    ]


def export_comparison_json(comparisons: List[BaselineComparison], path: str) -> None:
    with open(path, "w") as fh:
        json.dump(comparisons_to_dicts(comparisons), fh, indent=2)

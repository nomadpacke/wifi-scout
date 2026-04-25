"""Anomaly detection for WiFi signal samples using z-score based outlier detection."""
from __future__ import annotations

import math
import statistics
from dataclasses import dataclass
from typing import List, Optional

from wifi_scout.scanner import WiFiSample


@dataclass
class Anomaly:
    sample: WiFiSample
    field: str
    value: float
    z_score: float
    description: str


def _z_scores(values: List[float]) -> List[float]:
    """Return z-scores for a list of values. Returns zeros if stdev is 0."""
    if len(values) < 2:
        return [0.0] * len(values)
    mean = statistics.mean(values)
    stdev = statistics.stdev(values)
    if stdev == 0:
        return [0.0] * len(values)
    return [(v - mean) / stdev for v in values]


def detect_anomalies(
    samples: List[WiFiSample],
    threshold: float = 2.0,
    fields: Optional[List[str]] = None,
) -> List[Anomaly]:
    """Detect anomalous samples by z-score on specified fields.

    Args:
        samples: List of WiFiSample objects to analyze.
        threshold: Absolute z-score above which a sample is flagged.
        fields: Fields to check. Defaults to ['signal_dbm', 'latency_ms'].

    Returns:
        List of Anomaly objects for each flagged (sample, field) pair.
    """
    if fields is None:
        fields = ["signal_dbm", "latency_ms"]

    anomalies: List[Anomaly] = []

    for field in fields:
        values = []
        valid_samples = []
        for s in samples:
            v = getattr(s, field, None)
            if v is not None:
                values.append(float(v))
                valid_samples.append(s)

        if len(values) < 3:
            continue

        zs = _z_scores(values)
        for sample, value, z in zip(valid_samples, values, zs):
            if abs(z) >= threshold:
                direction = "high" if z > 0 else "low"
                anomalies.append(
                    Anomaly(
                        sample=sample,
                        field=field,
                        value=value,
                        z_score=round(z, 3),
                        description=(
                            f"Anomalous {field} ({direction}): "
                            f"{value} (z={z:.2f}) on {sample.ssid}"
                        ),
                    )
                )

    return anomalies


def anomaly_summary_text(anomalies: List[Anomaly]) -> str:
    """Return a human-readable summary of detected anomalies."""
    if not anomalies:
        return "No anomalies detected."
    lines = [f"Detected {len(anomalies)} anomaly(ies):"]
    for a in anomalies:
        lines.append(f"  - {a.description}")
    return "\n".join(lines)

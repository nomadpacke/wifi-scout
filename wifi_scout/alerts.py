"""Alert system for WiFi quality thresholds."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from wifi_scout.scanner import WiFiSample, signal_quality


@dataclass
class AlertRule:
    """A threshold rule that triggers an alert."""
    name: str
    min_signal_dbm: Optional[int] = None   # e.g. -80
    min_quality_pct: Optional[float] = None  # 0-100
    max_latency_ms: Optional[float] = None


@dataclass
class Alert:
    """Fired when a sample violates a rule."""
    rule_name: str
    ssid: str
    message: str
    sample: WiFiSample


def evaluate(sample: WiFiSample, rules: List[AlertRule]) -> List[Alert]:
    """Return a list of alerts triggered by *sample* against *rules*."""
    alerts: List[Alert] = []
    quality = signal_quality(sample.signal_dbm)

    for rule in rules:
        if rule.min_signal_dbm is not None and sample.signal_dbm < rule.min_signal_dbm:
            alerts.append(Alert(
                rule_name=rule.name,
                ssid=sample.ssid,
                message=(
                    f"[{rule.name}] {sample.ssid}: signal {sample.signal_dbm} dBm "
                    f"below threshold {rule.min_signal_dbm} dBm"
                ),
                sample=sample,
            ))

        if rule.min_quality_pct is not None and quality < rule.min_quality_pct:
            alerts.append(Alert(
                rule_name=rule.name,
                ssid=sample.ssid,
                message=(
                    f"[{rule.name}] {sample.ssid}: quality {quality:.1f}% "
                    f"below threshold {rule.min_quality_pct:.1f}%"
                ),
                sample=sample,
            ))

        if (
            rule.max_latency_ms is not None
            and sample.latency_ms is not None
            and sample.latency_ms > rule.max_latency_ms
        ):
            alerts.append(Alert(
                rule_name=rule.name,
                ssid=sample.ssid,
                message=(
                    f"[{rule.name}] {sample.ssid}: latency {sample.latency_ms:.1f} ms "
                    f"exceeds threshold {rule.max_latency_ms:.1f} ms"
                ),
                sample=sample,
            ))

    return alerts


def format_alerts(alerts: List[Alert]) -> str:
    """Return a human-readable string for a list of alerts."""
    if not alerts:
        return "No alerts."
    return "\n".join(a.message for a in alerts)

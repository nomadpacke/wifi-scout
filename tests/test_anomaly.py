"""Tests for wifi_scout.anomaly module."""
from __future__ import annotations

import pytest
from datetime import datetime, timezone
from unittest.mock import patch

from wifi_scout.scanner import WiFiSample
from wifi_scout.anomaly import (
    Anomaly,
    _z_scores,
    detect_anomalies,
    anomaly_summary_text,
)


def _make_sample(signal_dbm: int = -60, latency_ms: float = 10.0, ssid: str = "TestNet") -> WiFiSample:
    return WiFiSample(
        ssid=ssid,
        bssid="AA:BB:CC:DD:EE:FF",
        signal_dbm=signal_dbm,
        frequency_mhz=2412,
        channel=6,
        latency_ms=latency_ms,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


def test_z_scores_basic():
    zs = _z_scores([10.0, 10.0, 10.0, 10.0])
    assert all(z == 0.0 for z in zs)


def test_z_scores_single_value():
    assert _z_scores([42.0]) == [0.0]


def test_z_scores_detects_outlier():
    values = [10.0, 10.0, 10.0, 10.0, 100.0]
    zs = _z_scores(values)
    assert zs[-1] > 2.0


def test_detect_anomalies_empty():
    result = detect_anomalies([])
    assert result == []


def test_detect_anomalies_too_few_samples():
    samples = [_make_sample() for _ in range(2)]
    result = detect_anomalies(samples)
    assert result == []


def test_detect_anomalies_no_outliers():
    samples = [_make_sample(signal_dbm=-60, latency_ms=10.0) for _ in range(10)]
    result = detect_anomalies(samples)
    assert result == []


def test_detect_anomalies_signal_outlier():
    samples = [_make_sample(signal_dbm=-60) for _ in range(9)]
    samples.append(_make_sample(signal_dbm=-10))  # unusually strong
    result = detect_anomalies(samples, threshold=2.0, fields=["signal_dbm"])
    assert len(result) == 1
    assert result[0].field == "signal_dbm"
    assert result[0].z_score > 2.0


def test_detect_anomalies_latency_outlier():
    samples = [_make_sample(latency_ms=10.0) for _ in range(9)]
    samples.append(_make_sample(latency_ms=500.0))  # spike
    result = detect_anomalies(samples, threshold=2.0, fields=["latency_ms"])
    assert len(result) == 1
    assert result[0].field == "latency_ms"
    assert "high" in result[0].description


def test_detect_anomalies_custom_threshold():
    samples = [_make_sample(signal_dbm=-60) for _ in range(9)]
    samples.append(_make_sample(signal_dbm=-10))
    # Very high threshold — nothing flagged
    result = detect_anomalies(samples, threshold=10.0, fields=["signal_dbm"])
    assert result == []


def test_anomaly_summary_text_no_anomalies():
    text = anomaly_summary_text([])
    assert "No anomalies" in text


def test_anomaly_summary_text_with_anomalies():
    samples = [_make_sample(signal_dbm=-60) for _ in range(9)]
    samples.append(_make_sample(signal_dbm=-10))
    anomalies = detect_anomalies(samples, fields=["signal_dbm"])
    text = anomaly_summary_text(anomalies)
    assert "Detected" in text
    assert "signal_dbm" in text

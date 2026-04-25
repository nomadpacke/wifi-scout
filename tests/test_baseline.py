"""Tests for wifi_scout.baseline and wifi_scout.baseline_report."""
from __future__ import annotations

import json
import os
from datetime import datetime

import pytest

from wifi_scout.baseline import (
    BaselineEntry,
    build_baseline,
    compare,
    load_baseline,
    save_baseline,
)
from wifi_scout.baseline_report import (
    comparisons_to_dicts,
    export_comparison_json,
    format_comparison_text,
)
from wifi_scout.scanner import WiFiSample


def _make_sample(ssid="HomeNet", signal=-55, quality=80.0, latency=10.0):
    return WiFiSample(
        ssid=ssid,
        bssid="AA:BB:CC:DD:EE:FF",
        signal_dbm=signal,
        quality=quality,
        channel=6,
        frequency_mhz=2437,
        latency_ms=latency,
        timestamp=datetime.utcnow(),
    )


def test_build_baseline_empty():
    assert build_baseline([]) == {}


def test_build_baseline_single():
    s = _make_sample(signal=-60, quality=70.0, latency=12.0)
    result = build_baseline([s])
    assert "HomeNet" in result
    entry = result["HomeNet"]
    assert entry.avg_signal == -60
    assert entry.avg_quality == 70.0
    assert entry.avg_latency == 12.0
    assert entry.sample_count == 1


def test_build_baseline_averages_multiple():
    samples = [
        _make_sample(signal=-60, quality=70.0, latency=10.0),
        _make_sample(signal=-40, quality=90.0, latency=20.0),
    ]
    result = build_baseline(samples)
    entry = result["HomeNet"]
    assert entry.avg_signal == pytest.approx(-50.0)
    assert entry.avg_quality == pytest.approx(80.0)
    assert entry.avg_latency == pytest.approx(15.0)
    assert entry.sample_count == 2


def test_build_baseline_multiple_ssids():
    samples = [
        _make_sample(ssid="A", signal=-50),
        _make_sample(ssid="B", signal=-70),
    ]
    result = build_baseline(samples)
    assert set(result.keys()) == {"A", "B"}


def test_save_and_load_baseline(tmp_path):
    path = str(tmp_path / "baseline.json")
    entries = build_baseline([_make_sample(signal=-55, quality=75.0, latency=8.0)])
    save_baseline(entries, path)
    loaded = load_baseline(path)
    assert "HomeNet" in loaded
    assert loaded["HomeNet"].avg_signal == pytest.approx(-55.0)


def test_load_baseline_missing_file(tmp_path):
    result = load_baseline(str(tmp_path / "nope.json"))
    assert result == {}


def test_compare_matching_ssid():
    baseline_entries = build_baseline([_make_sample(signal=-60, quality=70.0, latency=20.0)])
    current = [_make_sample(signal=-50, quality=80.0, latency=15.0)]
    comps = compare(current, baseline_entries)
    assert len(comps) == 1
    c = comps[0]
    assert c.ssid == "HomeNet"
    assert c.signal_delta == pytest.approx(10.0)
    assert c.quality_delta == pytest.approx(10.0)
    assert c.latency_delta == pytest.approx(-5.0)


def test_compare_no_matching_ssid():
    baseline_entries = build_baseline([_make_sample(ssid="Other")])
    current = [_make_sample(ssid="HomeNet")]
    comps = compare(current, baseline_entries)
    assert comps == []


def test_format_comparison_text_empty():
    text = format_comparison_text([])
    assert "No baseline" in text


def test_format_comparison_text_contains_ssid():
    baseline_entries = build_baseline([_make_sample(signal=-60, quality=70.0, latency=20.0)])
    current = [_make_sample(signal=-50, quality=80.0, latency=15.0)]
    comps = compare(current, baseline_entries)
    text = format_comparison_text(comps)
    assert "HomeNet" in text
    assert "+10.0" in text


def test_export_comparison_json(tmp_path):
    baseline_entries = build_baseline([_make_sample(signal=-60, quality=70.0, latency=20.0)])
    current = [_make_sample(signal=-50, quality=80.0, latency=15.0)]
    comps = compare(current, baseline_entries)
    out = str(tmp_path / "cmp.json")
    export_comparison_json(comps, out)
    with open(out) as fh:
        data = json.load(fh)
    assert len(data) == 1
    assert data[0]["ssid"] == "HomeNet"
    assert "signal_delta" in data[0]

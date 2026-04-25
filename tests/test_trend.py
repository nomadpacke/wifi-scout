"""Tests for wifi_scout.trend module."""
import pytest
from wifi_scout.scanner import WiFiSample
from wifi_scout.trend import TrendReport, analyze, _linear_slope, _classify_trend


def _make_sample(ssid="HomeNet", signal=-60, quality=70, latency=None):
    return WiFiSample(
        ssid=ssid,
        bssid="AA:BB:CC:DD:EE:FF",
        signal_dbm=signal,
        quality=quality,
        channel=6,
        latency_ms=latency,
    )


def test_linear_slope_increasing():
    assert _linear_slope([1.0, 2.0, 3.0, 4.0]) > 0


def test_linear_slope_decreasing():
    assert _linear_slope([4.0, 3.0, 2.0, 1.0]) < 0


def test_linear_slope_flat():
    assert _linear_slope([5.0, 5.0, 5.0]) == 0.0


def test_linear_slope_single_value():
    assert _linear_slope([42.0]) == 0.0


def test_classify_trend_stable():
    assert _classify_trend(0.1) == "stable"


def test_classify_trend_improving():
    assert _classify_trend(1.5) == "improving"


def test_classify_trend_degrading():
    assert _classify_trend(-2.0) == "degrading"


def test_analyze_empty_returns_empty():
    assert analyze([]) == []


def test_analyze_single_sample():
    reports = analyze([_make_sample(signal=-70, quality=50)])
    assert len(reports) == 1
    r = reports[0]
    assert r.ssid == "HomeNet"
    assert r.sample_count == 1
    assert r.avg_signal == -70.0
    assert r.signal_stdev == 0.0
    assert r.trend == "stable"
    assert r.avg_latency_ms is None


def test_analyze_improving_trend():
    samples = [_make_sample(signal=s) for s in [-80, -70, -60, -50]]
    reports = analyze(samples)
    assert reports[0].trend == "improving"


def test_analyze_degrading_trend():
    samples = [_make_sample(signal=s) for s in [-50, -60, -70, -80]]
    reports = analyze(samples)
    assert reports[0].trend == "degrading"


def test_analyze_multiple_ssids():
    samples = [
        _make_sample(ssid="Net1", signal=-60),
        _make_sample(ssid="Net2", signal=-80),
        _make_sample(ssid="Net1", signal=-55),
    ]
    reports = analyze(samples)
    ssids = {r.ssid for r in reports}
    assert ssids == {"Net1", "Net2"}


def test_analyze_ssid_filter():
    samples = [
        _make_sample(ssid="Net1", signal=-60),
        _make_sample(ssid="Net2", signal=-80),
    ]
    reports = analyze(samples, ssid="Net1")
    assert len(reports) == 1
    assert reports[0].ssid == "Net1"


def test_analyze_latency_averaged():
    samples = [
        _make_sample(latency=10.0),
        _make_sample(latency=20.0),
        _make_sample(latency=30.0),
    ]
    reports = analyze(samples)
    assert reports[0].avg_latency_ms == 20.0

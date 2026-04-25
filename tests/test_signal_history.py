"""Tests for wifi_scout.signal_history."""
from __future__ import annotations

import time
from typing import Optional

import pytest

from wifi_scout.scanner import WiFiSample
from wifi_scout.signal_history import (
    DEFAULT_WINDOW,
    DROP_THRESHOLD,
    STABILITY_THRESHOLD,
    SignalHistory,
    StabilityReport,
)


def _make_sample(ssid: str = "TestNet", signal: int = -60, channel: int = 6) -> WiFiSample:
    return WiFiSample(
        ssid=ssid,
        bssid="AA:BB:CC:DD:EE:FF",
        signal_dbm=signal,
        channel=channel,
        frequency_mhz=2437,
        timestamp=time.time(),
    )


# ---------------------------------------------------------------------------

def test_add_and_count():
    h = SignalHistory("TestNet")
    assert h.count == 0
    h.add(_make_sample())
    assert h.count == 1


def test_add_wrong_ssid_raises():
    h = SignalHistory("TestNet")
    with pytest.raises(ValueError, match="does not match"):
        h.add(_make_sample(ssid="OtherNet"))


def test_report_none_with_single_sample():
    h = SignalHistory("TestNet")
    h.add(_make_sample())
    assert h.report() is None


def test_report_basic_fields():
    h = SignalHistory("TestNet")
    for sig in [-60, -62, -61]:
        h.add(_make_sample(signal=sig))
    r = h.report()
    assert isinstance(r, StabilityReport)
    assert r.ssid == "TestNet"
    assert r.sample_count == 3
    assert r.min_signal == -62
    assert r.max_signal == -60


def test_stable_when_low_variance():
    h = SignalHistory("TestNet")
    for sig in [-60, -61, -60, -61, -60]:
        h.add(_make_sample(signal=sig))
    r = h.report()
    assert r is not None
    assert r.stable is True
    assert r.std_signal < STABILITY_THRESHOLD


def test_unstable_when_high_variance():
    h = SignalHistory("TestNet")
    for sig in [-40, -80, -40, -80, -40]:
        h.add(_make_sample(signal=sig))
    r = h.report()
    assert r is not None
    assert r.stable is False


def test_drop_count():
    h = SignalHistory("TestNet")
    signals = [-50, -76, -80, -60, -77]
    for sig in signals:
        h.add(_make_sample(signal=sig))
    r = h.report(drop_threshold=DROP_THRESHOLD)  # -75
    assert r is not None
    # -76, -80, -77 are below -75
    assert r.drop_count == 3


def test_window_limits_samples():
    window = 5
    h = SignalHistory("TestNet", window=window)
    for i in range(10):
        h.add(_make_sample(signal=-60 - i))
    assert h.count == window
    # Only last 5 samples kept
    signals = [s.signal_dbm for s in h.samples]
    assert signals == [-65, -66, -67, -68, -69]


def test_default_window_constant():
    h = SignalHistory("TestNet")
    assert h._window == DEFAULT_WINDOW

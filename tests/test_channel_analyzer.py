"""Tests for wifi_scout.channel_analyzer."""
from __future__ import annotations

import datetime
from typing import Optional

import pytest

from wifi_scout.channel_analyzer import (
    ChannelStats,
    analyze_channels,
    best_channel,
    channel_summary_text,
)
from wifi_scout.scanner import WiFiSample


def _make_sample(
    ssid: str = "TestNet",
    signal_dbm: int = -60,
    channel: Optional[int] = 6,
) -> WiFiSample:
    return WiFiSample(
        ssid=ssid,
        bssid="AA:BB:CC:DD:EE:FF",
        signal_dbm=signal_dbm,
        frequency_mhz=2437,
        channel=channel,
        timestamp=datetime.datetime(2024, 1, 1, 12, 0, 0),
        latency_ms=10.0,
    )


def test_analyze_channels_empty():
    assert analyze_channels([]) == {}


def test_analyze_channels_single_sample():
    sample = _make_sample(ssid="Home", signal_dbm=-55, channel=1)
    result = analyze_channels([sample])
    assert 1 in result
    stats = result[1]
    assert stats.channel == 1
    assert stats.network_count == 1
    assert stats.avg_signal_dbm == -55.0
    assert "Home" in stats.ssids
    assert stats.congested is False


def test_analyze_channels_congestion_detected():
    samples = [
        _make_sample(ssid="NetA", signal_dbm=-60, channel=6),
        _make_sample(ssid="NetB", signal_dbm=-70, channel=6),
        _make_sample(ssid="NetC", signal_dbm=-65, channel=6),
    ]
    result = analyze_channels(samples)
    assert result[6].congested is True
    assert result[6].network_count == 3


def test_analyze_channels_no_congestion_5ghz():
    """5 GHz channels should never be flagged as congested."""
    samples = [
        _make_sample(ssid="NetA", signal_dbm=-50, channel=36),
        _make_sample(ssid="NetB", signal_dbm=-55, channel=36),
        _make_sample(ssid="NetC", signal_dbm=-60, channel=36),
    ]
    result = analyze_channels(samples)
    assert result[36].congested is False


def test_analyze_channels_avg_signal():
    samples = [
        _make_sample(ssid="NetA", signal_dbm=-40, channel=11),
        _make_sample(ssid="NetA", signal_dbm=-60, channel=11),
    ]
    result = analyze_channels(samples)
    assert result[11].avg_signal_dbm == -50.0


def test_analyze_channels_skips_none_channel():
    sample = _make_sample(channel=None)
    result = analyze_channels([sample])
    assert result == {}


def test_best_channel_returns_least_congested():
    stats = {
        1: ChannelStats(1, 1, -55.0, ["A"], False),
        6: ChannelStats(6, 4, -60.0, ["B", "C", "D", "E"], True),
        11: ChannelStats(11, 2, -58.0, ["F", "G"], False),
    }
    assert best_channel(stats, band="2.4GHz") == 1


def test_best_channel_no_matching_band():
    stats = {
        36: ChannelStats(36, 2, -50.0, ["A", "B"], False),
    }
    assert best_channel(stats, band="2.4GHz") is None


def test_best_channel_empty_stats():
    assert best_channel({}) is None


def test_channel_summary_text_empty():
    text = channel_summary_text({})
    assert "No channel data" in text


def test_channel_summary_text_contains_channel():
    stats = {
        6: ChannelStats(6, 3, -62.0, ["A", "B", "C"], True),
    }
    text = channel_summary_text(stats)
    assert "Ch   6" in text
    assert "CONGESTED" in text
    assert "-62.0" in text

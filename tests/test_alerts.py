"""Tests for wifi_scout.alerts."""
import pytest
from wifi_scout.alerts import AlertRule, evaluate, format_alerts
from wifi_scout.scanner import WiFiSample
from datetime import datetime, timezone


def _make_sample(
    ssid="HomeNet",
    signal_dbm=-60,
    latency_ms=10.0,
):
    return WiFiSample(
        ssid=ssid,
        bssid="AA:BB:CC:DD:EE:FF",
        signal_dbm=signal_dbm,
        channel=6,
        timestamp=datetime.now(timezone.utc),
        latency_ms=latency_ms,
    )


def test_no_alerts_when_all_ok():
    sample = _make_sample(signal_dbm=-55, latency_ms=5.0)
    rule = AlertRule(name="strict", min_signal_dbm=-70, min_quality_pct=20.0, max_latency_ms=100.0)
    assert evaluate(sample, [rule]) == []


def test_alert_on_low_signal():
    sample = _make_sample(signal_dbm=-85)
    rule = AlertRule(name="signal", min_signal_dbm=-80)
    alerts = evaluate(sample, [rule])
    assert len(alerts) == 1
    assert alerts[0].rule_name == "signal"
    assert "-85" in alerts[0].message


def test_alert_on_low_quality():
    # signal_quality(-95) should be very low
    sample = _make_sample(signal_dbm=-95)
    rule = AlertRule(name="quality", min_quality_pct=30.0)
    alerts = evaluate(sample, [rule])
    assert len(alerts) == 1
    assert "quality" in alerts[0].message.lower()


def test_alert_on_high_latency():
    sample = _make_sample(latency_ms=250.0)
    rule = AlertRule(name="latency", max_latency_ms=100.0)
    alerts = evaluate(sample, [rule])
    assert len(alerts) == 1
    assert "250.0" in alerts[0].message


def test_multiple_violations_same_rule():
    sample = _make_sample(signal_dbm=-90, latency_ms=200.0)
    rule = AlertRule(name="combo", min_signal_dbm=-80, max_latency_ms=50.0)
    alerts = evaluate(sample, [rule])
    assert len(alerts) == 2


def test_no_latency_skips_latency_check():
    sample = _make_sample(latency_ms=None)
    rule = AlertRule(name="lat", max_latency_ms=10.0)
    alerts = evaluate(sample, [rule])
    assert alerts == []


def test_multiple_rules():
    sample = _make_sample(signal_dbm=-88, latency_ms=5.0)
    rules = [
        AlertRule(name="r1", min_signal_dbm=-80),
        AlertRule(name="r2", min_signal_dbm=-90),  # should not fire
    ]
    alerts = evaluate(sample, rules)
    assert len(alerts) == 1
    assert alerts[0].rule_name == "r1"


def test_format_alerts_empty():
    assert format_alerts([]) == "No alerts."


def test_format_alerts_multiple():
    sample = _make_sample(signal_dbm=-85, latency_ms=200.0)
    rule = AlertRule(name="all", min_signal_dbm=-80, max_latency_ms=50.0)
    alerts = evaluate(sample, [rule])
    output = format_alerts(alerts)
    lines = output.strip().splitlines()
    assert len(lines) == 2

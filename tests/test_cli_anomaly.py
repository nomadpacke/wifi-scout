"""Tests for wifi_scout.cli_anomaly module."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from wifi_scout.scanner import WiFiSample
from wifi_scout.cli_anomaly import cmd_anomaly, add_anomaly_subparser


def _make_sample(signal_dbm: int = -60, latency_ms: float = 10.0) -> WiFiSample:
    return WiFiSample(
        ssid="TestNet",
        bssid="AA:BB:CC:DD:EE:FF",
        signal_dbm=signal_dbm,
        frequency_mhz=2412,
        channel=6,
        latency_ms=latency_ms,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


def _make_args(**kwargs) -> argparse.Namespace:
    defaults = {
        "db": "/tmp/test_anomaly.db",
        "ssid": None,
        "threshold": 2.0,
        "fields": None,
        "verbose": False,
    }
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def test_cmd_anomaly_missing_db(tmp_path):
    args = _make_args(db=str(tmp_path / "missing.db"))
    result = cmd_anomaly(args)
    assert result == 1


def test_cmd_anomaly_no_samples(tmp_path):
    db = tmp_path / "scout.db"
    db.touch()
    args = _make_args(db=str(db))
    with patch("wifi_scout.cli_anomaly.load_samples", return_value=[]):
        result = cmd_anomaly(args)
    assert result == 1


def test_cmd_anomaly_no_anomalies(tmp_path, capsys):
    db = tmp_path / "scout.db"
    db.touch()
    samples = [_make_sample() for _ in range(5)]
    args = _make_args(db=str(db))
    with patch("wifi_scout.cli_anomaly.load_samples", return_value=samples), \
         patch("wifi_scout.cli_anomaly.detect_anomalies", return_value=[]):
        result = cmd_anomaly(args)
    assert result == 0
    out = capsys.readouterr().out
    assert "No anomalies" in out


def test_cmd_anomaly_with_anomalies(tmp_path, capsys):
    db = tmp_path / "scout.db"
    db.touch()
    samples = [_make_sample(signal_dbm=-60) for _ in range(9)]
    samples.append(_make_sample(signal_dbm=-10))
    args = _make_args(db=str(db))
    with patch("wifi_scout.cli_anomaly.load_samples", return_value=samples):
        result = cmd_anomaly(args)
    assert result == 0
    out = capsys.readouterr().out
    assert "Detected" in out or "anomal" in out.lower()


def test_cmd_anomaly_verbose(tmp_path, capsys):
    db = tmp_path / "scout.db"
    db.touch()
    samples = [_make_sample(signal_dbm=-60) for _ in range(9)]
    samples.append(_make_sample(signal_dbm=-10))
    args = _make_args(db=str(db), verbose=True)
    with patch("wifi_scout.cli_anomaly.load_samples", return_value=samples):
        result = cmd_anomaly(args)
    assert result == 0
    out = capsys.readouterr().out
    assert "signal_dbm" in out


def test_cmd_anomaly_custom_fields(tmp_path, capsys):
    db = tmp_path / "scout.db"
    db.touch()
    samples = [_make_sample() for _ in range(5)]
    args = _make_args(db=str(db), fields="signal_dbm")
    with patch("wifi_scout.cli_anomaly.load_samples", return_value=samples), \
         patch("wifi_scout.cli_anomaly.detect_anomalies", return_value=[]) as mock_detect:
        cmd_anomaly(args)
    mock_detect.assert_called_once()
    _, kwargs = mock_detect.call_args
    assert kwargs.get("fields") == ["signal_dbm"]


def test_add_anomaly_subparser():
    parser = argparse.ArgumentParser()
    subs = parser.add_subparsers()
    add_anomaly_subparser(subs)
    args = parser.parse_args(["anomaly", "--db", "foo.db"])
    assert args.db == "foo.db"
    assert args.threshold == 2.0
    assert args.verbose is False

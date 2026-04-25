"""Tests for wifi_scout.cli_baseline subcommands."""
from __future__ import annotations

import argparse
import json
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from wifi_scout.cli_baseline import cmd_baseline, cmd_compare
from wifi_scout.scanner import WiFiSample

_DEFAULT_BASELINE = "/tmp/test_baseline.json"


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


def _make_args(**kwargs) -> argparse.Namespace:
    defaults = {"db": "/tmp/fake.db", "baseline_path": _DEFAULT_BASELINE, "json_out": None}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def test_cmd_baseline_missing_db():
    args = _make_args(db="/nonexistent/path.db")
    with patch("wifi_scout.cli_baseline.load_samples", side_effect=FileNotFoundError):
        rc = cmd_baseline(args)
    assert rc == 1


def test_cmd_baseline_no_samples():
    args = _make_args()
    with patch("wifi_scout.cli_baseline.load_samples", return_value=[]):
        rc = cmd_baseline(args)
    assert rc == 1


def test_cmd_baseline_saves_and_returns_zero(tmp_path):
    args = _make_args(baseline_path=str(tmp_path / "bl.json"))
    samples = [_make_sample()]
    with patch("wifi_scout.cli_baseline.load_samples", return_value=samples):
        rc = cmd_baseline(args)
    assert rc == 0
    with open(args.baseline_path) as fh:
        data = json.load(fh)
    assert any(d["ssid"] == "HomeNet" for d in data)


def test_cmd_compare_missing_db():
    args = _make_args()
    with patch("wifi_scout.cli_baseline.load_samples", side_effect=FileNotFoundError):
        rc = cmd_compare(args)
    assert rc == 1


def test_cmd_compare_no_baseline(tmp_path):
    args = _make_args(baseline_path=str(tmp_path / "nope.json"))
    with patch("wifi_scout.cli_baseline.load_samples", return_value=[_make_sample()]):
        rc = cmd_compare(args)
    assert rc == 1


def test_cmd_compare_no_matching_ssids(tmp_path):
    bl_path = str(tmp_path / "bl.json")
    # build a baseline for a different SSID
    from wifi_scout.baseline import build_baseline, save_baseline
    save_baseline(build_baseline([_make_sample(ssid="Other")]), bl_path)
    args = _make_args(baseline_path=bl_path)
    with patch("wifi_scout.cli_baseline.load_samples", return_value=[_make_sample(ssid="HomeNet")]):
        rc = cmd_compare(args)
    assert rc == 0


def test_cmd_compare_with_json_out(tmp_path, capsys):
    bl_path = str(tmp_path / "bl.json")
    json_out = str(tmp_path / "out.json")
    from wifi_scout.baseline import build_baseline, save_baseline
    save_baseline(build_baseline([_make_sample(signal=-60)]), bl_path)
    args = _make_args(baseline_path=bl_path, json_out=json_out)
    with patch("wifi_scout.cli_baseline.load_samples", return_value=[_make_sample(signal=-50)]):
        rc = cmd_compare(args)
    assert rc == 0
    assert json_out
    with open(json_out) as fh:
        data = json.load(fh)
    assert data[0]["ssid"] == "HomeNet"

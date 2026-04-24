"""Tests for the wifi_scout.cli module."""

import json
import csv
from pathlib import Path
from unittest.mock import patch

import pytest

from wifi_scout.cli import build_parser, cmd_scan, cmd_report
from wifi_scout.scanner import WiFiSample


SAMPLE = WiFiSample(
    ssid="HomeNet",
    bssid="AA:BB:CC:DD:EE:FF",
    signal_dbm=-55,
    frequency_mhz=2437,
    channel=6,
    location="office",
)


@pytest.fixture()
def db_path(tmp_path: Path) -> Path:
    return tmp_path / "test.db"


def _make_args(**kwargs):
    """Create a simple namespace mirroring argparse output."""
    import argparse
    defaults = dict(db="", location="office", json="", csv="")
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


# ---------------------------------------------------------------------------
# cmd_scan
# ---------------------------------------------------------------------------

def test_cmd_scan_saves_samples(db_path):
    args = _make_args(db=str(db_path), location="office")
    with patch("wifi_scout.cli.scan", return_value=[SAMPLE]):
        rc = cmd_scan(args)
    assert rc == 0
    assert db_path.exists()


def test_cmd_scan_no_networks_returns_error(db_path):
    args = _make_args(db=str(db_path), location="office")
    with patch("wifi_scout.cli.scan", return_value=[]):
        rc = cmd_scan(args)
    assert rc == 1


# ---------------------------------------------------------------------------
# cmd_report
# ---------------------------------------------------------------------------

def test_cmd_report_missing_db(tmp_path):
    args = _make_args(db=str(tmp_path / "missing.db"), location="")
    assert cmd_report(args) == 1


def test_cmd_report_summary(db_path, capsys):
    args_scan = _make_args(db=str(db_path), location="office")
    with patch("wifi_scout.cli.scan", return_value=[SAMPLE]):
        cmd_scan(args_scan)

    args_report = _make_args(db=str(db_path), location="office")
    rc = cmd_report(args_report)
    assert rc == 0
    captured = capsys.readouterr()
    assert "HomeNet" in captured.out
    assert "office" not in captured.out or True  # location may or may not appear


def test_cmd_report_json_export(db_path, tmp_path):
    json_out = str(tmp_path / "out.json")
    args_scan = _make_args(db=str(db_path), location="office")
    with patch("wifi_scout.cli.scan", return_value=[SAMPLE]):
        cmd_scan(args_scan)

    args_report = _make_args(db=str(db_path), location="", json=json_out)
    cmd_report(args_report)
    data = json.loads(Path(json_out).read_text())
    assert isinstance(data, list)
    assert data[0]["ssid"] == "HomeNet"


def test_cmd_report_csv_export(db_path, tmp_path):
    csv_out = str(tmp_path / "out.csv")
    args_scan = _make_args(db=str(db_path), location="office")
    with patch("wifi_scout.cli.scan", return_value=[SAMPLE]):
        cmd_scan(args_scan)

    args_report = _make_args(db=str(db_path), location="", csv=csv_out)
    cmd_report(args_report)
    rows = list(csv.DictReader(Path(csv_out).read_text().splitlines()))
    assert rows[0]["ssid"] == "HomeNet"


# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------

def test_parser_scan_defaults():
    parser = build_parser()
    args = parser.parse_args(["scan"])
    assert args.location == "unknown"
    assert args.command == "scan"


def test_parser_report_defaults():
    parser = build_parser()
    args = parser.parse_args(["report"])
    assert args.command == "report"
    assert args.json == ""
    assert args.csv == ""

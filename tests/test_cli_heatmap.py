"""Tests for wifi_scout.cli_heatmap."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from wifi_scout.cli_heatmap import cmd_heatmap
from wifi_scout.heatmap import HeatmapCell
from wifi_scout.location import Location
from wifi_scout.scanner import WiFiSample


def _make_args(**kwargs) -> argparse.Namespace:
    defaults = {
        "db": "wifi_scout.db",
        "location_store": "locations.json",
        "location": "",
        "format": "text",
        "output": "",
    }
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def _make_sample(location: str = "home") -> WiFiSample:
    return WiFiSample(
        ssid="Net", bssid="AA:BB:CC:DD:EE:FF",
        signal_dbm=-60.0, quality=0.7,
        channel=6, frequency_mhz=2437, location=location,
    )


def _make_cell() -> HeatmapCell:
    return HeatmapCell("home", 51.5, -0.1, -60.0, 0.7, 2, ["Net"])


def test_cmd_heatmap_missing_db(tmp_path):
    args = _make_args(db=str(tmp_path / "missing.db"))
    assert cmd_heatmap(args) == 1


def test_cmd_heatmap_no_samples(tmp_path):
    db = tmp_path / "wifi.db"
    db.touch()
    with patch("wifi_scout.cli_heatmap.load_samples", return_value=[]):
        args = _make_args(db=str(db))
        assert cmd_heatmap(args) == 1


def test_cmd_heatmap_no_locations(tmp_path):
    db = tmp_path / "wifi.db"
    db.touch()
    with patch("wifi_scout.cli_heatmap.load_samples", return_value=[_make_sample()]), \
         patch("wifi_scout.cli_heatmap.list_locations", return_value=[]):
        args = _make_args(db=str(db))
        assert cmd_heatmap(args) == 1


def test_cmd_heatmap_no_matching_cells(tmp_path):
    db = tmp_path / "wifi.db"
    db.touch()
    loc = Location(name="office", latitude=51.6, longitude=-0.2)
    with patch("wifi_scout.cli_heatmap.load_samples", return_value=[_make_sample("home")]), \
         patch("wifi_scout.cli_heatmap.list_locations", return_value=[loc]), \
         patch("wifi_scout.cli_heatmap.build_heatmap", return_value=[]):
        args = _make_args(db=str(db))
        assert cmd_heatmap(args) == 1


def test_cmd_heatmap_text_output(tmp_path, capsys):
    db = tmp_path / "wifi.db"
    db.touch()
    cell = _make_cell()
    with patch("wifi_scout.cli_heatmap.load_samples", return_value=[_make_sample()]), \
         patch("wifi_scout.cli_heatmap.list_locations",
               return_value=[Location("home", 51.5, -0.1)]), \
         patch("wifi_scout.cli_heatmap.build_heatmap", return_value=[cell]):
        args = _make_args(db=str(db), format="text")
        rc = cmd_heatmap(args)
    assert rc == 0
    captured = capsys.readouterr()
    assert "home" in captured.out


def test_cmd_heatmap_json_export(tmp_path):
    db = tmp_path / "wifi.db"
    db.touch()
    out_path = str(tmp_path / "out.json")
    cell = _make_cell()
    with patch("wifi_scout.cli_heatmap.load_samples", return_value=[_make_sample()]), \
         patch("wifi_scout.cli_heatmap.list_locations",
               return_value=[Location("home", 51.5, -0.1)]), \
         patch("wifi_scout.cli_heatmap.build_heatmap", return_value=[cell]):
        args = _make_args(db=str(db), format="json", output=out_path)
        rc = cmd_heatmap(args)
    assert rc == 0
    with open(out_path) as fh:
        data = json.load(fh)
    assert data["total_locations"] == 1


def test_cmd_heatmap_csv_export(tmp_path):
    db = tmp_path / "wifi.db"
    db.touch()
    out_path = str(tmp_path / "out.csv")
    cell = _make_cell()
    with patch("wifi_scout.cli_heatmap.load_samples", return_value=[_make_sample()]), \
         patch("wifi_scout.cli_heatmap.list_locations",
               return_value=[Location("home", 51.5, -0.1)]), \
         patch("wifi_scout.cli_heatmap.build_heatmap", return_value=[cell]):
        args = _make_args(db=str(db), format="csv", output=out_path)
        rc = cmd_heatmap(args)
    assert rc == 0
    assert Path(out_path).exists()

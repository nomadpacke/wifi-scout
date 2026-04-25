"""Tests for wifi_scout.heatmap and wifi_scout.heatmap_export."""
from __future__ import annotations

import csv
import json
import os
from dataclasses import dataclass
from typing import Optional

import pytest

from wifi_scout.heatmap import HeatmapCell, build_heatmap, heatmap_to_dicts
from wifi_scout.heatmap_export import (
    export_heatmap_csv,
    export_heatmap_json,
    heatmap_text_summary,
)
from wifi_scout.location import Location
from wifi_scout.scanner import WiFiSample


def _make_sample(
    signal: float = -60.0,
    quality: float = 0.7,
    location: Optional[str] = "home",
    ssid: str = "TestNet",
) -> WiFiSample:
    return WiFiSample(
        ssid=ssid,
        bssid="AA:BB:CC:DD:EE:FF",
        signal_dbm=signal,
        quality=quality,
        channel=6,
        frequency_mhz=2437,
        location=location,
    )


def _make_location(name: str = "home", lat: float = 51.5, lon: float = -0.1) -> Location:
    return Location(name=name, latitude=lat, longitude=lon)


# --- build_heatmap ---

def test_build_heatmap_empty_samples():
    locs = [_make_location()]
    cells = build_heatmap([], locs)
    assert cells == []


def test_build_heatmap_empty_locations():
    samples = [_make_sample()]
    cells = build_heatmap(samples, [])
    assert cells == []


def test_build_heatmap_single_location():
    loc = _make_location("home", 51.5, -0.1)
    samples = [_make_sample(signal=-55.0, quality=0.8), _make_sample(signal=-65.0, quality=0.6)]
    cells = build_heatmap(samples, [loc])
    assert len(cells) == 1
    assert cells[0].location_name == "home"
    assert cells[0].avg_signal == pytest.approx(-60.0)
    assert cells[0].avg_quality == pytest.approx(0.7)
    assert cells[0].sample_count == 2


def test_build_heatmap_multiple_locations_sorted_by_signal():
    locs = [_make_location("office", 51.6, -0.2), _make_location("home", 51.5, -0.1)]
    samples = [
        _make_sample(signal=-80.0, location="office"),
        _make_sample(signal=-50.0, location="home"),
    ]
    cells = build_heatmap(samples, locs)
    assert cells[0].location_name == "home"
    assert cells[1].location_name == "office"


def test_build_heatmap_ignores_unknown_location():
    loc = _make_location("home")
    samples = [_make_sample(location="unknown_place")]
    cells = build_heatmap(samples, [loc])
    assert cells == []


def test_build_heatmap_ssids_deduplicated():
    loc = _make_location("home")
    samples = [
        _make_sample(ssid="NetA"),
        _make_sample(ssid="NetA"),
        _make_sample(ssid="NetB"),
    ]
    cells = build_heatmap(samples, [loc])
    assert cells[0].ssids == ["NetA", "NetB"]


# --- heatmap_to_dicts ---

def test_heatmap_to_dicts_keys():
    cell = HeatmapCell("home", 51.5, -0.1, -60.0, 0.7, 5, ["Net"])
    result = heatmap_to_dicts([cell])
    assert set(result[0].keys()) == {
        "location", "latitude", "longitude",
        "avg_signal_dbm", "avg_quality", "sample_count", "ssids",
    }


# --- export functions ---

def test_export_heatmap_json(tmp_path):
    cell = HeatmapCell("home", 51.5, -0.1, -60.0, 0.7, 3, ["Net"])
    out = str(tmp_path / "heatmap.json")
    export_heatmap_json([cell], out)
    with open(out) as fh:
        data = json.load(fh)
    assert data["total_locations"] == 1
    assert data["heatmap"][0]["location"] == "home"


def test_export_heatmap_csv(tmp_path):
    cell = HeatmapCell("home", 51.5, -0.1, -60.0, 0.7, 3, ["NetA", "NetB"])
    out = str(tmp_path / "heatmap.csv")
    export_heatmap_csv([cell], out)
    with open(out, newline="") as fh:
        rows = list(csv.DictReader(fh))
    assert len(rows) == 1
    assert rows[0]["location"] == "home"
    assert "NetA" in rows[0]["ssids"]


def test_heatmap_text_summary_empty():
    assert heatmap_text_summary([]) == "No heatmap data available."


def test_heatmap_text_summary_contains_location():
    cell = HeatmapCell("office", 51.6, -0.2, -70.0, 0.5, 10, [])
    text = heatmap_text_summary([cell])
    assert "office" in text
    assert "dBm" in text

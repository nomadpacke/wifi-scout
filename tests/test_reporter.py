"""Tests for wifi_scout.reporter."""

from __future__ import annotations

import csv
import io
import json
from datetime import datetime, timezone

import pytest

from wifi_scout.reporter import export_csv, export_json, summarize
from wifi_scout.scanner import WiFiSample


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_sample(
    signal_dbm: int = -60,
    ssid: str = "TestNet",
    location: str = "office",
    ts: datetime | None = None,
) -> WiFiSample:
    return WiFiSample(
        timestamp=ts or datetime(2024, 6, 1, 12, 0, 0, tzinfo=timezone.utc),
        ssid=ssid,
        bssid="AA:BB:CC:DD:EE:FF",
        signal_dbm=signal_dbm,
        frequency_mhz=2412,
        location=location,
    )


# ---------------------------------------------------------------------------
# summarize
# ---------------------------------------------------------------------------

def test_summarize_empty():
    assert summarize([]) == {}


def test_summarize_single_sample():
    sample = _make_sample(signal_dbm=-50)
    result = summarize([sample])
    assert result["sample_count"] == 1
    assert result["signal_dbm"]["mean"] == -50
    assert result["signal_dbm"]["stdev"] == 0.0
    assert result["locations"] == ["office"]
    assert result["ssids"] == ["TestNet"]


def test_summarize_multiple_samples():
    samples = [
        _make_sample(signal_dbm=-40, location="lobby"),
        _make_sample(signal_dbm=-80, location="basement"),
        _make_sample(signal_dbm=-60, location="office"),
    ]
    result = summarize(samples)
    assert result["sample_count"] == 3
    assert result["signal_dbm"]["min"] == -80
    assert result["signal_dbm"]["max"] == -40
    assert result["signal_dbm"]["stdev"] > 0
    assert sorted(result["locations"]) == ["basement", "lobby", "office"]


# ---------------------------------------------------------------------------
# export_json
# ---------------------------------------------------------------------------

def test_export_json_structure():
    samples = [_make_sample(), _make_sample(signal_dbm=-70, location="hall")]
    raw = export_json(samples)
    data = json.loads(raw)
    assert "samples" in data
    assert "summary" in data
    assert len(data["samples"]) == 2


def test_export_json_no_summary():
    raw = export_json([_make_sample()], include_summary=False)
    data = json.loads(raw)
    assert "summary" not in data


def test_export_json_sample_fields():
    sample = _make_sample(signal_dbm=-55)
    data = json.loads(export_json([sample], include_summary=False))
    row = data["samples"][0]
    assert row["signal_dbm"] == -55
    assert "quality_pct" in row
    assert "timestamp" in row


# ---------------------------------------------------------------------------
# export_csv
# ---------------------------------------------------------------------------

def test_export_csv_header_and_rows():
    samples = [_make_sample(-50), _make_sample(-70)]
    raw = export_csv(samples)
    reader = csv.DictReader(io.StringIO(raw))
    rows = list(reader)
    assert len(rows) == 2
    assert "signal_dbm" in rows[0]
    assert "quality_pct" in rows[0]


def test_export_csv_values():
    sample = _make_sample(signal_dbm=-65, location="rooftop")
    raw = export_csv([sample])
    reader = csv.DictReader(io.StringIO(raw))
    row = next(reader)
    assert int(row["signal_dbm"]) == -65
    assert row["location"] == "rooftop"

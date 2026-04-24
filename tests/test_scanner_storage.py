"""Tests for scanner data model and storage layer."""

import tempfile
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from wifi_scout.scanner import WiFiSample
from wifi_scout.storage import save_samples, load_samples


@pytest.fixture
def db_path(tmp_path: Path) -> Path:
    return tmp_path / "test_scans.db"


@pytest.fixture
def sample_factory():
    def _make(ssid="TestNet", signal_dbm=-65, location=None, offset_seconds=0):
        return WiFiSample(
            ssid=ssid,
            bssid="AA:BB:CC:DD:EE:FF",
            signal_dbm=signal_dbm,
            frequency_mhz=2412,
            channel=1,
            timestamp=datetime.utcnow() + timedelta(seconds=offset_seconds),
            location_label=location,
        )
    return _make


class TestWiFiSample:
    def test_signal_quality_perfect(self, sample_factory):
        s = sample_factory(signal_dbm=-50)
        assert s.signal_quality == 100

    def test_signal_quality_zero(self, sample_factory):
        s = sample_factory(signal_dbm=-100)
        assert s.signal_quality == 0

    def test_signal_quality_midpoint(self, sample_factory):
        s = sample_factory(signal_dbm=-75)
        assert s.signal_quality == 50

    def test_signal_quality_below_floor(self, sample_factory):
        s = sample_factory(signal_dbm=-110)
        assert s.signal_quality == 0


class TestStorage:
    def test_save_and_load_roundtrip(self, db_path, sample_factory):
        samples = [sample_factory(ssid="HomeNet", location="kitchen")]
        count = save_samples(samples, db_path=db_path)
        assert count == 1

        loaded = load_samples(db_path=db_path)
        assert len(loaded) == 1
        assert loaded[0].ssid == "HomeNet"
        assert loaded[0].location_label == "kitchen"

    def test_save_empty_list(self, db_path):
        assert save_samples([], db_path=db_path) == 0

    def test_filter_by_location(self, db_path, sample_factory):
        save_samples(
            [sample_factory(location="office"), sample_factory(location="home")],
            db_path=db_path,
        )
        results = load_samples(db_path=db_path, location="office")
        assert all(r.location_label == "office" for r in results)
        assert len(results) == 1

    def test_filter_by_since(self, db_path, sample_factory):
        old = sample_factory(offset_seconds=-3600)
        new = sample_factory(offset_seconds=0)
        save_samples([old, new], db_path=db_path)

        cutoff = datetime.utcnow() - timedelta(minutes=30)
        results = load_samples(db_path=db_path, since=cutoff)
        assert len(results) == 1

    def test_multiple_saves_accumulate(self, db_path, sample_factory):
        save_samples([sample_factory()], db_path=db_path)
        save_samples([sample_factory(), sample_factory()], db_path=db_path)
        assert len(load_samples(db_path=db_path)) == 3

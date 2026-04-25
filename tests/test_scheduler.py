"""Tests for wifi_scout.scheduler."""

import pytest
from unittest.mock import MagicMock, patch, call
from wifi_scout.scanner import WiFiSample
from wifi_scout.scheduler import ScanScheduler


def _make_sample(ssid="Home", location="desk"):
    return WiFiSample(
        ssid=ssid,
        bssid="AA:BB:CC:DD:EE:FF",
        signal_dbm=-55,
        quality=90,
        channel=6,
        frequency_ghz=2.4,
        location=location,
        timestamp="2024-01-01T00:00:00",
    )


@pytest.fixture
def mock_scan():
    return MagicMock(return_value=[_make_sample()])


@pytest.fixture
def mock_save():
    return MagicMock()


def test_run_once_calls_scan_and_save(mock_scan, mock_save):
    scheduler = ScanScheduler(mock_scan, mock_save, interval=5.0, location="desk")
    samples = scheduler.run_once()

    mock_scan.assert_called_once_with(location="desk")
    mock_save.assert_called_once_with(samples)
    assert len(samples) == 1
    assert scheduler.run_count == 1


def test_run_once_no_networks_skips_save(mock_save):
    scan_fn = MagicMock(return_value=[])
    scheduler = ScanScheduler(scan_fn, mock_save, location="desk")
    samples = scheduler.run_once()

    mock_save.assert_not_called()
    assert samples == []
    assert scheduler.run_count == 1


def test_max_runs_stops_loop(mock_scan, mock_save):
    with patch("wifi_scout.scheduler.time.sleep") as mock_sleep:
        scheduler = ScanScheduler(
            mock_scan, mock_save, interval=1.0, max_runs=3
        )
        scheduler.start()

    assert scheduler.run_count == 3
    assert mock_scan.call_count == 3
    assert mock_sleep.call_count == 2  # sleep between runs, not after last


def test_stop_flag_exits_loop(mock_scan, mock_save):
    call_count = 0

    def scan_and_stop(**kwargs):
        nonlocal call_count
        call_count += 1
        scheduler.stop()
        return [_make_sample()]

    scheduler = ScanScheduler(scan_and_stop, mock_save, interval=0.0)
    with patch("wifi_scout.scheduler.time.sleep"):
        scheduler.start()

    assert call_count == 1
    assert scheduler.run_count == 1


def test_run_count_increments_correctly(mock_scan, mock_save):
    scheduler = ScanScheduler(mock_scan, mock_save)
    assert scheduler.run_count == 0
    scheduler.run_once()
    scheduler.run_once()
    assert scheduler.run_count == 2

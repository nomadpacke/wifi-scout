"""Tests for wifi_scout.location."""

from __future__ import annotations

import json
import pytest
from pathlib import Path

from wifi_scout.location import (
    Location,
    save_location,
    load_location,
    list_locations,
    delete_location,
)


@pytest.fixture
def store_path(tmp_path: Path) -> Path:
    return tmp_path / "locations.json"


# ---------------------------------------------------------------------------
# Location dataclass validation
# ---------------------------------------------------------------------------

def test_location_valid():
    loc = Location(name="Home", description="Living room", latitude=51.5, longitude=-0.1)
    assert loc.name == "Home"


def test_location_invalid_name():
    with pytest.raises(ValueError, match="Location name"):
        Location(name="bad/name!")


def test_location_invalid_latitude():
    with pytest.raises(ValueError, match="Latitude"):
        Location(name="Bad", latitude=91.0)


def test_location_invalid_longitude():
    with pytest.raises(ValueError, match="Longitude"):
        Location(name="Bad", longitude=181.0)


# ---------------------------------------------------------------------------
# save / load round-trip
# ---------------------------------------------------------------------------

def test_save_and_load_location(store_path: Path):
    loc = Location(name="Office", description="Desk spot", latitude=48.8, longitude=2.3)
    save_location(loc, path=store_path)
    loaded = load_location("Office", path=store_path)
    assert loaded == loc


def test_load_missing_returns_none(store_path: Path):
    result = load_location("Nowhere", path=store_path)
    assert result is None


def test_save_overwrites_existing(store_path: Path):
    loc1 = Location(name="Cafe", description="First visit")
    loc2 = Location(name="Cafe", description="Second visit")
    save_location(loc1, path=store_path)
    save_location(loc2, path=store_path)
    loaded = load_location("Cafe", path=store_path)
    assert loaded.description == "Second visit"


# ---------------------------------------------------------------------------
# list_locations
# ---------------------------------------------------------------------------

def test_list_locations_empty(store_path: Path):
    assert list_locations(path=store_path) == []


def test_list_locations_sorted(store_path: Path):
    for name in ["Zebra", "Alpha", "Middle"]:
        save_location(Location(name=name), path=store_path)
    names = [loc.name for loc in list_locations(path=store_path)]
    assert names == ["Alpha", "Middle", "Zebra"]


# ---------------------------------------------------------------------------
# delete_location
# ---------------------------------------------------------------------------

def test_delete_existing_location(store_path: Path):
    save_location(Location(name="Temp"), path=store_path)
    removed = delete_location("Temp", path=store_path)
    assert removed is True
    assert load_location("Temp", path=store_path) is None


def test_delete_nonexistent_returns_false(store_path: Path):
    assert delete_location("Ghost", path=store_path) is False

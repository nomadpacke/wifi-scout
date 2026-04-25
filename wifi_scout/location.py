"""Location tagging for WiFi samples — attach human-readable labels to scan sessions."""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional

_DEFAULT_LOCATION_FILE = Path.home() / ".wifi_scout" / "locations.json"


@dataclass
class Location:
    name: str
    description: str = ""
    latitude: Optional[float] = None
    longitude: Optional[float] = None

    def __post_init__(self) -> None:
        if not re.match(r'^[\w\- ]{1,64}$', self.name):
            raise ValueError(
                f"Location name {self.name!r} must be 1-64 alphanumeric/dash/space chars."
            )
        if self.latitude is not None and not (-90.0 <= self.latitude <= 90.0):
            raise ValueError(f"Latitude {self.latitude} out of range [-90, 90].")
        if self.longitude is not None and not (-180.0 <= self.longitude <= 180.0):
            raise ValueError(f"Longitude {self.longitude} out of range [-180, 180].")


def _load_store(path: Path) -> dict:
    if path.exists():
        with path.open() as fh:
            return json.load(fh)
    return {}


def _save_store(path: Path, store: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as fh:
        json.dump(store, fh, indent=2)


def save_location(location: Location, path: Path = _DEFAULT_LOCATION_FILE) -> None:
    """Persist a Location to the JSON store."""
    store = _load_store(path)
    store[location.name] = asdict(location)
    _save_store(path, store)


def load_location(name: str, path: Path = _DEFAULT_LOCATION_FILE) -> Optional[Location]:
    """Return a Location by name, or None if not found."""
    store = _load_store(path)
    data = store.get(name)
    if data is None:
        return None
    return Location(**data)


def list_locations(path: Path = _DEFAULT_LOCATION_FILE) -> list[Location]:
    """Return all stored locations sorted by name."""
    store = _load_store(path)
    return [Location(**v) for v in sorted(store.values(), key=lambda d: d["name"])]


def delete_location(name: str, path: Path = _DEFAULT_LOCATION_FILE) -> bool:
    """Remove a location by name. Returns True if it existed."""
    store = _load_store(path)
    if name not in store:
        return False
    del store[name]
    _save_store(path, store)
    return True

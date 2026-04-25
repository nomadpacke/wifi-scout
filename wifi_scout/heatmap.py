"""Heatmap generation: aggregate signal strength by location."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Dict, Optional

from wifi_scout.scanner import WiFiSample
from wifi_scout.location import Location


@dataclass
class HeatmapCell:
    location_name: str
    latitude: float
    longitude: float
    avg_signal: float
    avg_quality: float
    sample_count: int
    ssids: List[str] = field(default_factory=list)


def _avg(values: List[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def build_heatmap(
    samples: List[WiFiSample],
    locations: List[Location],
) -> List[HeatmapCell]:
    """Aggregate samples per location into heatmap cells."""
    loc_map: Dict[str, Location] = {loc.name: loc for loc in locations}
    buckets: Dict[str, List[WiFiSample]] = {loc.name: [] for loc in locations}

    for sample in samples:
        if sample.location and sample.location in buckets:
            buckets[sample.location].append(sample)

    cells: List[HeatmapCell] = []
    for loc_name, loc_samples in buckets.items():
        if not loc_samples:
            continue
        loc = loc_map[loc_name]
        signals = [s.signal_dbm for s in loc_samples]
        qualities = [s.quality for s in loc_samples]
        ssids = list({s.ssid for s in loc_samples if s.ssid})
        cells.append(
            HeatmapCell(
                location_name=loc_name,
                latitude=loc.latitude,
                longitude=loc.longitude,
                avg_signal=round(_avg(signals), 2),
                avg_quality=round(_avg(qualities), 2),
                sample_count=len(loc_samples),
                ssids=sorted(ssids),
            )
        )
    cells.sort(key=lambda c: c.avg_signal, reverse=True)
    return cells


def heatmap_to_dicts(cells: List[HeatmapCell]) -> List[dict]:
    return [
        {
            "location": c.location_name,
            "latitude": c.latitude,
            "longitude": c.longitude,
            "avg_signal_dbm": c.avg_signal,
            "avg_quality": c.avg_quality,
            "sample_count": c.sample_count,
            "ssids": c.ssids,
        }
        for c in cells
    ]

"""Export heatmap data to JSON and CSV formats."""
from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import List

from wifi_scout.heatmap import HeatmapCell, heatmap_to_dicts


def export_heatmap_json(cells: List[HeatmapCell], path: str) -> None:
    """Write heatmap cells to a JSON file."""
    data = heatmap_to_dicts(cells)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump({"heatmap": data, "total_locations": len(data)}, fh, indent=2)


def export_heatmap_csv(cells: List[HeatmapCell], path: str) -> None:
    """Write heatmap cells to a CSV file."""
    fieldnames = [
        "location",
        "latitude",
        "longitude",
        "avg_signal_dbm",
        "avg_quality",
        "sample_count",
        "ssids",
    ]
    rows = heatmap_to_dicts(cells)
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            row["ssids"] = "|".join(row["ssids"])
            writer.writerow(row)


def heatmap_text_summary(cells: List[HeatmapCell]) -> str:
    """Return a human-readable heatmap summary."""
    if not cells:
        return "No heatmap data available."
    lines = ["WiFi Heatmap Summary", "=" * 40]
    for cell in cells:
        quality_pct = int(cell.avg_quality * 100)
        lines.append(
            f"  {cell.location_name:<20} "
            f"signal={cell.avg_signal:>7.1f} dBm  "
            f"quality={quality_pct:>3}%  "
            f"samples={cell.sample_count}"
        )
    return "\n".join(lines)

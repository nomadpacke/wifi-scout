"""Load AlertRule definitions from a JSON config file."""
from __future__ import annotations

import json
from pathlib import Path
from typing import List

from wifi_scout.alerts import AlertRule

_DEFAULT_RULES: List[dict] = [
    {
        "name": "weak-signal",
        "min_signal_dbm": -80,
        "min_quality_pct": 25.0,
    },
    {
        "name": "high-latency",
        "max_latency_ms": 150.0,
    },
]


def load_rules(config_path: str | Path | None = None) -> List[AlertRule]:
    """Load alert rules from *config_path* (JSON), or return built-in defaults.

    Expected JSON format::

        [
          {"name": "weak-signal", "min_signal_dbm": -80},
          {"name": "high-latency", "max_latency_ms": 150}
        ]
    """
    if config_path is None:
        return _rules_from_dicts(_DEFAULT_RULES)

    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"Alert config not found: {path}")

    with path.open() as fh:
        data = json.load(fh)

    if not isinstance(data, list):
        raise ValueError("Alert config must be a JSON array of rule objects.")

    return _rules_from_dicts(data)


def save_default_config(dest: str | Path) -> None:
    """Write the default rule set to *dest* as JSON (useful for --init)."""
    path = Path(dest)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as fh:
        json.dump(_DEFAULT_RULES, fh, indent=2)
        fh.write("\n")


def _rules_from_dicts(data: List[dict]) -> List[AlertRule]:
    rules = []
    for item in data:
        rules.append(
            AlertRule(
                name=item["name"],
                min_signal_dbm=item.get("min_signal_dbm"),
                min_quality_pct=item.get("min_quality_pct"),
                max_latency_ms=item.get("max_latency_ms"),
            )
        )
    return rules

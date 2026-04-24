"""Persistent storage for WiFi scan samples using SQLite."""

import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Optional

from wifi_scout.scanner import WiFiSample

DEFAULT_DB_PATH = Path.home() / ".wifi_scout" / "scans.db"

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS scans (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    ssid        TEXT NOT NULL,
    bssid       TEXT NOT NULL,
    signal_dbm  INTEGER NOT NULL,
    frequency_mhz INTEGER NOT NULL,
    channel     INTEGER NOT NULL,
    timestamp   TEXT NOT NULL,
    location    TEXT
);
"""


def _get_connection(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute(CREATE_TABLE_SQL)
    conn.commit()
    return conn


def save_samples(samples: list[WiFiSample], db_path: Path = DEFAULT_DB_PATH) -> int:
    """Persist a list of WiFiSample objects. Returns number of rows inserted."""
    if not samples:
        return 0
    conn = _get_connection(db_path)
    rows = [
        (
            s.ssid,
            s.bssid,
            s.signal_dbm,
            s.frequency_mhz,
            s.channel,
            s.timestamp.isoformat(),
            s.location_label,
        )
        for s in samples
    ]
    with conn:
        conn.executemany(
            "INSERT INTO scans (ssid, bssid, signal_dbm, frequency_mhz, channel, timestamp, location) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            rows,
        )
    conn.close()
    return len(rows)


def load_samples(
    db_path: Path = DEFAULT_DB_PATH,
    location: Optional[str] = None,
    since: Optional[datetime] = None,
) -> list[WiFiSample]:
    """Load stored samples with optional filters."""
    conn = _get_connection(db_path)
    query = "SELECT * FROM scans WHERE 1=1"
    params: list = []
    if location:
        query += " AND location = ?"
        params.append(location)
    if since:
        query += " AND timestamp >= ?"
        params.append(since.isoformat())
    query += " ORDER BY timestamp DESC"

    rows = conn.execute(query, params).fetchall()
    conn.close()

    return [
        WiFiSample(
            ssid=row["ssid"],
            bssid=row["bssid"],
            signal_dbm=row["signal_dbm"],
            frequency_mhz=row["frequency_mhz"],
            channel=row["channel"],
            timestamp=datetime.fromisoformat(row["timestamp"]),
            location_label=row["location"],
        )
        for row in rows
    ]

"""WiFi signal scanner module for wifi-scout."""

import subprocess
import platform
import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class WiFiSample:
    """Represents a single WiFi quality measurement."""

    ssid: str
    bssid: str
    signal_dbm: int
    frequency_mhz: int
    channel: int
    timestamp: datetime = field(default_factory=datetime.utcnow)
    location_label: Optional[str] = None

    @property
    def signal_quality(self) -> int:
        """Convert dBm to quality percentage (0-100)."""
        if self.signal_dbm <= -100:
            return 0
        if self.signal_dbm >= -50:
            return 100
        return 2 * (self.signal_dbm + 100)


def _scan_linux() -> list[WiFiSample]:
    """Scan WiFi networks on Linux using iwlist."""
    try:
        output = subprocess.check_output(
            ["iwlist", "scan"], stderr=subprocess.DEVNULL, text=True
        )
    except (subprocess.CalledProcessError, FileNotFoundError) as exc:
        raise RuntimeError(f"iwlist scan failed: {exc}") from exc

    samples: list[WiFiSample] = []
    current: dict = {}

    for line in output.splitlines():
        line = line.strip()
        if "ESSID:" in line:
            current["ssid"] = re.search(r'ESSID:"(.*)"', line).group(1) if re.search(r'ESSID:"(.*)"', line) else ""
        elif "Address:" in line:
            m = re.search(r"Address: ([0-9A-F:]{17})", line)
            current["bssid"] = m.group(1) if m else ""
        elif "Signal level=" in line:
            m = re.search(r"Signal level=(-\d+)", line)
            current["signal_dbm"] = int(m.group(1)) if m else -100
        elif "Frequency:" in line:
            m = re.search(r"Frequency:(\d+\.\d+)", line)
            freq_ghz = float(m.group(1)) if m else 2.4
            current["frequency_mhz"] = int(freq_ghz * 1000)
            m_ch = re.search(r"Channel (\d+)", line)
            current["channel"] = int(m_ch.group(1)) if m_ch else 0

        if len(current) >= 5:
            samples.append(
                WiFiSample(
                    ssid=current.get("ssid", ""),
                    bssid=current.get("bssid", ""),
                    signal_dbm=current.get("signal_dbm", -100),
                    frequency_mhz=current.get("frequency_mhz", 2400),
                    channel=current.get("channel", 0),
                )
            )
            current = {}

    return samples


def scan(location_label: Optional[str] = None) -> list[WiFiSample]:
    """Scan available WiFi networks and return samples."""
    system = platform.system()
    if system == "Linux":
        samples = _scan_linux()
    else:
        raise NotImplementedError(f"Scanning not supported on {system} yet.")

    for sample in samples:
        sample.location_label = location_label

    return samples

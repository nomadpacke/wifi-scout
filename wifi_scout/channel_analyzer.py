"""Analyze WiFi channel usage and detect congestion across samples."""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Dict, List, Optional

from wifi_scout.scanner import WiFiSample


@dataclass
class ChannelStats:
    channel: int
    network_count: int
    avg_signal_dbm: float
    ssids: List[str]
    congested: bool


# Channels that overlap heavily in 2.4 GHz band
_CONGESTION_THRESHOLD = 3  # networks sharing a channel


def _band(channel: int) -> str:
    """Return '2.4GHz' or '5GHz' based on channel number."""
    return "2.4GHz" if channel <= 14 else "5GHz"


def analyze_channels(samples: List[WiFiSample]) -> Dict[int, ChannelStats]:
    """Aggregate samples by channel and compute per-channel statistics.

    Args:
        samples: List of WiFiSample objects to analyze.

    Returns:
        Mapping of channel number to ChannelStats.
    """
    if not samples:
        return {}

    channel_data: Dict[int, List[WiFiSample]] = defaultdict(list)
    for s in samples:
        if s.channel is not None:
            channel_data[s.channel].append(s)

    result: Dict[int, ChannelStats] = {}
    for channel, ch_samples in channel_data.items():
        ssids = list({s.ssid for s in ch_samples if s.ssid})
        avg_signal = sum(s.signal_dbm for s in ch_samples) / len(ch_samples)
        network_count = len(ssids)
        congested = network_count >= _CONGESTION_THRESHOLD and _band(channel) == "2.4GHz"
        result[channel] = ChannelStats(
            channel=channel,
            network_count=network_count,
            avg_signal_dbm=round(avg_signal, 2),
            ssids=sorted(ssids),
            congested=congested,
        )
    return result


def best_channel(stats: Dict[int, ChannelStats], band: str = "2.4GHz") -> Optional[int]:
    """Suggest the least congested channel for the given band.

    Args:
        stats: Output from analyze_channels.
        band: '2.4GHz' or '5GHz'.

    Returns:
        Channel number with fewest networks, or None if no data.
    """
    candidates = {
        ch: s for ch, s in stats.items() if _band(ch) == band
    }
    if not candidates:
        return None
    return min(candidates, key=lambda ch: candidates[ch].network_count)


def channel_summary_text(stats: Dict[int, ChannelStats]) -> str:
    """Return a human-readable summary of channel usage."""
    if not stats:
        return "No channel data available."
    lines = ["Channel Usage Summary:", "-" * 36]
    for ch in sorted(stats):
        s = stats[ch]
        flag = " [CONGESTED]" if s.congested else ""
        lines.append(
            f"  Ch {ch:>3} ({_band(ch)}) | networks: {s.network_count} "
            f"| avg signal: {s.avg_signal_dbm} dBm{flag}"
        )
    return "\n".join(lines)

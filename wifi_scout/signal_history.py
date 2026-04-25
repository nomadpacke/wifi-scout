"""Sliding-window signal history and stability metrics."""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from statistics import mean, stdev
from typing import Deque, List, Optional

from wifi_scout.scanner import WiFiSample

DEFAULT_WINDOW = 20


@dataclass
class StabilityReport:
    ssid: str
    sample_count: int
    mean_signal: float
    std_signal: float
    min_signal: int
    max_signal: int
    stable: bool  # True when std_signal < STABILITY_THRESHOLD
    drop_count: int  # samples where signal < drop_threshold


STABILITY_THRESHOLD = 5.0   # dBm std-dev below which signal is "stable"
DROP_THRESHOLD = -75         # dBm — samples below this count as drops


class SignalHistory:
    """Maintains a fixed-size rolling window of WiFiSamples for one SSID."""

    def __init__(self, ssid: str, window: int = DEFAULT_WINDOW) -> None:
        self.ssid = ssid
        self._window = window
        self._samples: Deque[WiFiSample] = deque(maxlen=window)

    # ------------------------------------------------------------------
    def add(self, sample: WiFiSample) -> None:
        if sample.ssid != self.ssid:
            raise ValueError(
                f"Sample SSID '{sample.ssid}' does not match history SSID '{self.ssid}'"
            )
        self._samples.append(sample)

    # ------------------------------------------------------------------
    @property
    def samples(self) -> List[WiFiSample]:
        return list(self._samples)

    @property
    def count(self) -> int:
        return len(self._samples)

    # ------------------------------------------------------------------
    def report(self, drop_threshold: int = DROP_THRESHOLD) -> Optional[StabilityReport]:
        """Return a StabilityReport, or None if fewer than 2 samples."""
        if self.count < 2:
            return None

        signals = [s.signal_dbm for s in self._samples]
        mu = mean(signals)
        sigma = stdev(signals)
        drops = sum(1 for v in signals if v < drop_threshold)

        return StabilityReport(
            ssid=self.ssid,
            sample_count=self.count,
            mean_signal=round(mu, 2),
            std_signal=round(sigma, 2),
            min_signal=min(signals),
            max_signal=max(signals),
            stable=sigma < STABILITY_THRESHOLD,
            drop_count=drops,
        )

    # ------------------------------------------------------------------
    def __repr__(self) -> str:  # pragma: no cover
        return f"SignalHistory(ssid={self.ssid!r}, count={self.count}/{self._window})"

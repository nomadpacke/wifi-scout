"""Periodic scanning scheduler for wifi-scout."""

import time
import logging
from datetime import datetime
from typing import Callable, Optional

logger = logging.getLogger(__name__)


class ScanScheduler:
    """Runs WiFi scans at a fixed interval and persists results."""

    def __init__(
        self,
        scan_fn: Callable,
        save_fn: Callable,
        interval: float = 60.0,
        location: Optional[str] = None,
        max_runs: Optional[int] = None,
    ) -> None:
        self.scan_fn = scan_fn
        self.save_fn = save_fn
        self.interval = interval
        self.location = location
        self.max_runs = max_runs
        self._run_count = 0
        self._stop = False

    def stop(self) -> None:
        """Signal the scheduler to stop after the current run."""
        self._stop = True

    @property
    def run_count(self) -> int:
        return self._run_count

    def run_once(self) -> list:
        """Execute a single scan cycle and save results."""
        samples = self.scan_fn(location=self.location)
        if samples:
            self.save_fn(samples)
            logger.info(
                "[%s] Saved %d sample(s) for location=%r",
                datetime.utcnow().isoformat(),
                len(samples),
                self.location,
            )
        else:
            logger.warning("No networks found during scheduled scan.")
        self._run_count += 1
        return samples

    def start(self) -> None:
        """Block and run scans until stopped or max_runs reached."""
        logger.info(
            "Scheduler started: interval=%.1fs, max_runs=%s, location=%r",
            self.interval,
            self.max_runs,
            self.location,
        )
        while not self._stop:
            self.run_once()
            if self.max_runs is not None and self._run_count >= self.max_runs:
                logger.info("Reached max_runs=%d, stopping.", self.max_runs)
                break
            time.sleep(self.interval)

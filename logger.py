"""
logger.py
-----------
CSV event logger. Only logs on fatigue-state transitions (not every
frame) so the log stays readable and useful for post-drive analysis
rather than flooding with near-duplicate rows.
"""

import csv
import os
import time

import config


class EventLogger:
    """Writes fatigue state transitions to a CSV file."""

    def __init__(self, log_path: str = config.LOG_FILE_PATH) -> None:
        self._log_path = log_path
        self._previous_state: str = "NORMAL"
        os.makedirs(os.path.dirname(self._log_path), exist_ok=True)
        self._ensure_header()

    def _ensure_header(self) -> None:
        if not os.path.isfile(self._log_path):
            with open(self._log_path, mode="w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(
                    ["timestamp", "state", "reason", "ear", "mar", "pitch", "yaw", "roll"]
                )

    def log_if_state_changed(self, result) -> None:
        """Append a row only if the fatigue state differs from the last logged state."""
        if result.state == self._previous_state:
            return
        self._previous_state = result.state
        with open(self._log_path, mode="a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([
                time.strftime("%Y-%m-%d %H:%M:%S"),
                result.state,
                "; ".join(result.reasons),
                f"{result.ear:.3f}",
                f"{result.mar:.3f}",
                f"{result.pitch:.1f}",
                f"{result.yaw:.1f}",
                f"{result.roll:.1f}",
            ])

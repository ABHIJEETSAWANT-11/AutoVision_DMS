"""
fatigue_logic.py
------------------
Central fatigue decision engine. Owns all time-based state: PERCLOS
history, blink counting, yawn windowing, and sustained head-droop
tracking. Combines EAR, MAR, and head pitch signals into a single
FatigueResult using a configurable four-state machine:

    NORMAL  -> no meaningful fatigue signals
    ALERT   -> a single mild indicator (early warning, no alarm sound)
    WARNING -> one strong, confirmed fatigue signal (audio warning)
    DROWSY  -> two or more strong signals at once (audio alarm)

This module performs NO camera, display, or I/O -- it only processes
per-frame signals and returns a structured result for main.py to act on.
"""

from collections import deque
from dataclasses import dataclass
from typing import List, Optional

import config


@dataclass
class FatigueResult:
    state: str
    reasons: List[str]
    ear: float
    mar: float
    pitch: float
    yaw: float
    roll: float
    perclos: float
    total_blinks: int
    total_yawns: int
    face_detected: bool


class FatigueStateMachine:
    """Tracks driver state over time and produces a FatigueResult each frame."""

    def __init__(self) -> None:
        self._eye_closed_history: deque = deque()  # (timestamp, is_closed)
        self._yawn_timestamps: deque = deque()

        self._blink_counter = 0
        self._total_blinks = 0
        self._total_yawns = 0

        self._yawn_start_time: Optional[float] = None
        self._is_yawning = False

        self._pitch_droop_start: Optional[float] = None
        self._face_lost_since: Optional[float] = None

    # -- internal helpers ----------------------------------------------

    def _update_perclos(self, now: float, eyes_closed: bool) -> float:
        self._eye_closed_history.append((now, eyes_closed))
        while (
            self._eye_closed_history
            and now - self._eye_closed_history[0][0] > config.PERCLOS_WINDOW_SECONDS
        ):
            self._eye_closed_history.popleft()
        closed_frames = sum(1 for _, closed in self._eye_closed_history if closed)
        total_frames = len(self._eye_closed_history)
        return closed_frames / total_frames if total_frames else 0.0

    def _update_blinks(self, eyes_closed: bool) -> None:
        if eyes_closed:
            self._blink_counter += 1
        else:
            if self._blink_counter >= config.BLINK_CONSEC_FRAMES:
                self._total_blinks += 1
            self._blink_counter = 0

    def _update_yawns(self, now: float, mar: float) -> int:
        if mar > config.MAR_THRESHOLD:
            if self._yawn_start_time is None:
                self._yawn_start_time = now
            elif (
                (now - self._yawn_start_time) >= config.YAWN_MIN_DURATION_SECONDS
                and not self._is_yawning
            ):
                self._yawn_timestamps.append(now)
                self._total_yawns += 1
                self._is_yawning = True
        else:
            self._yawn_start_time = None
            self._is_yawning = False

        while (
            self._yawn_timestamps
            and now - self._yawn_timestamps[0] > config.YAWN_WINDOW_SECONDS
        ):
            self._yawn_timestamps.popleft()
        return len(self._yawn_timestamps)

    def _update_head_droop(self, now: float, pitch: float) -> bool:
        drooping = pitch < config.PITCH_DROOP_THRESHOLD_DEG
        if drooping:
            if self._pitch_droop_start is None:
                self._pitch_droop_start = now
        else:
            self._pitch_droop_start = None
        return (
            self._pitch_droop_start is not None
            and (now - self._pitch_droop_start) >= config.PITCH_DROOP_MIN_DURATION_SECONDS
        )

    # -- public API -------------------------------------------------------

    def update_no_face(self, now: float) -> FatigueResult:
        """Call once per frame when no face was detected."""
        if self._face_lost_since is None:
            self._face_lost_since = now
        lost_duration = now - self._face_lost_since

        state = "NORMAL"
        reasons: List[str] = []
        if lost_duration >= config.FACE_LOST_WARNING_SECONDS:
            state = "WARNING"
            reasons.append("Face not detected")

        return FatigueResult(
            state=state, reasons=reasons, ear=0.0, mar=0.0, pitch=0.0, yaw=0.0, roll=0.0,
            perclos=0.0, total_blinks=self._total_blinks, total_yawns=self._total_yawns,
            face_detected=False,
        )

    def update(
        self, now: float, ear: float, mar: float, pitch: float, yaw: float, roll: float
    ) -> FatigueResult:
        """Call once per frame when a face WAS detected."""
        self._face_lost_since = None

        eyes_closed = ear < config.EAR_THRESHOLD
        perclos = self._update_perclos(now, eyes_closed)
        self._update_blinks(eyes_closed)
        recent_yawn_count = self._update_yawns(now, mar)
        sustained_droop = self._update_head_droop(now, pitch)

        reasons: List[str] = []
        strong_signals = 0

        if perclos >= config.PERCLOS_WARNING_THRESHOLD:
            strong_signals += 1
            reasons.append("High eye closure (PERCLOS)")
        if recent_yawn_count >= config.YAWN_COUNT_WARNING:
            strong_signals += 1
            reasons.append("Frequent yawning")
        if sustained_droop:
            strong_signals += 1
            reasons.append("Sustained head droop")

        if strong_signals >= 2:
            state = "DROWSY"
        elif strong_signals == 1:
            state = "WARNING"
        elif perclos >= config.PERCLOS_ALERT_THRESHOLD or recent_yawn_count >= config.YAWN_COUNT_ALERT:
            state = "ALERT"
            if not reasons:
                reasons.append("Mild fatigue indicators")
        else:
            state = "NORMAL"

        return FatigueResult(
            state=state, reasons=reasons, ear=ear, mar=mar, pitch=pitch, yaw=yaw, roll=roll,
            perclos=perclos, total_blinks=self._total_blinks, total_yawns=self._total_yawns,
            face_detected=True,
        )

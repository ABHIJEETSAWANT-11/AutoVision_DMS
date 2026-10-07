"""
alarm.py
----------
Audio alert manager. Wraps pygame.mixer and plays state-appropriate
warning/drowsy tones with a cooldown so repeated triggers don't spam
the driver every frame.
"""

import pygame

import config

class AlarmManager:
    """Plays state-appropriate audio alerts with a cooldown between plays."""

    def __init__(self) -> None:
        pygame.mixer.init()
        self._warning_sound = pygame.mixer.Sound(config.WARNING_SOUND_PATH)
        self._drowsy_sound = pygame.mixer.Sound(config.DROWSY_SOUND_PATH)
        self._last_played: float = 0.0

    def trigger(self, state: str, now: float) -> None:
        """Play the appropriate sound for the given state, respecting the cooldown."""
        if state not in ("WARNING", "DROWSY"):
            return
        if (now - self._last_played) < config.SOUND_COOLDOWN_SECONDS:
            return

        if state == "WARNING":
            self._warning_sound.play()
        elif state == "DROWSY":
            self._drowsy_sound.play()
        self._last_played = now

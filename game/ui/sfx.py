"""Synthesized sound effects (no external audio assets required)."""

from __future__ import annotations

import math

import numpy as np
import pygame

SAMPLE_RATE = 22050


def _tone(
    frequency: float,
    duration: float,
    *,
    volume: float = 0.35,
    wave: str = "sine",
    decay: bool = True,
) -> pygame.mixer.Sound:
    count = max(1, int(SAMPLE_RATE * duration))
    t = np.linspace(0.0, duration, count, endpoint=False)
    if wave == "square":
        signal = np.sign(np.sin(2 * math.pi * frequency * t))
    elif wave == "noise":
        signal = np.random.default_rng(int(frequency)).uniform(-1.0, 1.0, count)
    else:
        signal = np.sin(2 * math.pi * frequency * t)
    if decay:
        envelope = np.linspace(1.0, 0.05, count)
        signal = signal * envelope
    signal = (signal * volume * 32767).astype(np.int16)
    stereo = np.column_stack((signal, signal))
    return pygame.sndarray.make_sound(stereo)


class SoundBank:
    """Lazy-built SFX bank."""

    def __init__(self) -> None:
        self.enabled = True
        self._sounds: dict[str, pygame.mixer.Sound] = {}
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=SAMPLE_RATE, size=-16, channels=2, buffer=512)
        except pygame.error:
            self.enabled = False

    def _get(self, name: str) -> pygame.mixer.Sound | None:
        if not self.enabled:
            return None
        if name not in self._sounds:
            builder = {
                "place": lambda: _tone(520, 0.08, wave="square", volume=0.25),
                "hit": lambda: _tone(180, 0.07, wave="square", volume=0.3),
                "level_up": lambda: _tone(660, 0.18, volume=0.3),
                "boss": lambda: _tone(90, 0.35, wave="square", volume=0.4),
                "victory": lambda: _tone(784, 0.28, volume=0.35),
                "death": lambda: _tone(110, 0.4, wave="noise", volume=0.25),
                "retreat": lambda: _tone(330, 0.12, volume=0.25),
                "build": lambda: _tone(440, 0.1, wave="square", volume=0.28),
                "equip": lambda: _tone(600, 0.06, volume=0.22),
                "click": lambda: _tone(400, 0.04, wave="square", volume=0.18),
            }.get(name)
            if builder is None:
                return None
            self._sounds[name] = builder()
        return self._sounds[name]

    def play(self, name: str) -> None:
        sound = self._get(name)
        if sound is not None:
            sound.play()

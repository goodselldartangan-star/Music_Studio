"""Stable shared contracts. Changes here should be rare and backwards-compatible."""
from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Literal

SR = 44100
TAIL_SECONDS = 3.0
STEM = 'Blue_Hour_Signal'
TITLE = 'Blue Hour Signal'

@dataclass(frozen=True)
class Settings:
    bpm: int = 118
    transpose: int = 0
    seed: int = 261111
    preview_bars: int | None = None

    def __post_init__(self):
        if not 90 <= self.bpm <= 145: raise ValueError('bpm out of range')
        if not -5 <= self.transpose <= 5: raise ValueError('transpose out of range')
        if self.preview_bars is not None and not 1 <= self.preview_bars <= 104:
            raise ValueError('preview bars out of range')

@dataclass(frozen=True)
class Note:
    part: str
    beat: float
    duration: float   # in beats, not seconds
    pitch: int        # MIDI number
    velocity: float   # 0-1.1
    pan: float = 0.0  # -1..1

@dataclass(frozen=True)
class Drum:
    kind: str
    beat: float
    velocity: float
    pan: float = 0.0

SECTIONS = [
    (0, 8, 'intro'), (8, 24, 'verse_a'), (24, 32, 'rise'),
    (32, 48, 'chorus_a'), (48, 56, 'instrumental'),
    (56, 72, 'verse_b'), (72, 80, 'bridge'),
    (80, 96, 'chorus_b'), (96, 104, 'outro'),
]
BARS = SECTIONS[-1][1]


def section_for(bar: int):
    return next((s,e,n) for s,e,n in SECTIONS if s <= bar < e)


def safe_note(part, beat, length, pitch, velocity, pan=0):
    if not (0 <= beat < BARS*4 and .02 <= length <= 8 and 20 <= pitch <= 108 and 0 < velocity <= 1.1 and -1 <= pan <= 1):
        raise ValueError(f'Invalid note: {part} {beat} {length} {pitch} {velocity} {pan}')
    return Note(part, round(beat,5), round(length,4), int(pitch), round(velocity,4),float(pan))

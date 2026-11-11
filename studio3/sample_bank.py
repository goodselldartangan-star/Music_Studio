"""Optional CC0 sample backend; never imports the songwriter or mixer.

Input: Note/Drum. Output: mono float32 audio at project sample rate.
SampleBank selects recorded notes by pitch, dynamic layer and stable round-robin.
A missing pack raises an actionable error rather than silently claiming sampling.
"""
from __future__ import annotations
from dataclasses import dataclass
from fractions import Fraction
from functools import lru_cache
from pathlib import Path
import hashlib
import math
import re

import numpy as np
import soundfile as sf
from scipy.signal import resample_poly

from .spec import SR, Note

# Meta Open Sound: CC0 instruments (see docs/real-instruments.md).
# Two interfaces, not a hard dependency: pluck -> steel guitar; keys -> piano.
SOURCE_FOR_PART = {'pluck': 'meta-steel-guitar', 'keys': 'meta-piano'}
NOTE_PATTERN = re.compile(r'_Vel0?(\d+)[^_]*_([A-G](?:s|b|#)?-?\d+)_\d+\.(?:wav|ogg|flac)$', re.I)
NOTE_PC = {'C': 0, 'D': 2, 'E': 4, 'F': 5, 'G': 7, 'A': 9, 'B': 11}


def midi_from_name(note: str) -> int:
    m = re.fullmatch(r'([A-G])([sb#]?)(-?\d+)', note, re.I)
    if not m:
        raise ValueError(f'Unsupported sample pitch: {note}')
    pc = NOTE_PC[m[1].upper()] + {'': 0, 's': 1, '#': 1, 'b': -1}[m[2].lower()]
    return (int(m[3]) + 1) * 12 + pc


@dataclass(frozen=True)
class Region:
    source: str
    path: Path
    midi: int
    layer: int


def _seed_index(*values: object) -> int:
    content = '|'.join(map(str, values)).encode('utf-8')
    return int.from_bytes(hashlib.sha256(content).digest()[:8], 'big')


@lru_cache(maxsize=48)
def _load(path: Path) -> tuple[np.ndarray, int]:
    audio, sr = sf.read(path, always_2d=True, dtype='float32')
    if not np.isfinite(audio).all():
        raise ValueError(f'Nonfinite sample: {path}')
    if sr < 8000 or sr > 192000 or not len(audio):
        raise ValueError(f'Invalid sample rate or empty sample: {path}')
    mono = audio.mean(axis=1)
    # Prevent multi-second unused tails inflating the cached backing bank.
    return mono[:round(8 * sr)].astype(np.float32), sr


@lru_cache(maxsize=80)
def _at_pitch(path: Path, base_midi: int, dest_midi: int) -> np.ndarray:
    audio, sr = _load(path)
    rate = 2 ** ((dest_midi - base_midi) / 12)
    fraction = Fraction((SR / sr) / rate).limit_denominator(4096)
    converted = resample_poly(audio, fraction.numerator, fraction.denominator)
    if not np.isfinite(converted).all():
        raise ValueError('Bad sample resampling')
    return np.ascontiguousarray(converted, dtype=np.float32)


class SampleBank:
    """Scans externally installed samples; no network calls at play time."""
    def __init__(self, root: str | Path):
        self.root = Path(root).expanduser().resolve()
        if not self.root.is_dir():
            raise FileNotFoundError(f'Sample folder not found: {self.root}')
        self.regions: dict[str, list[Region]] = {source: [] for source in SOURCE_FOR_PART.values()}
        for path in sorted(self.root.rglob('*')):
            if path.suffix.lower() not in ('.ogg', '.wav', '.flac'):
                continue
            if not path.is_file():
                continue
            # Detect the publisher's collection even with ZIP-internal wrappers.
            match = NOTE_PATTERN.search(path.name)
            if not match:
                continue
            source = next((name for name in self.regions if name in '/'.join(path.parts).lower()), None)
            if not source:
                continue
            self.regions[source].append(Region(source, path, midi_from_name(match[2]), int(match[1])))
        self.oneshots: dict[str, list[Path]] = {}
        for kind in ('kick', 'snare', 'hat', 'open_hat', 'clap', 'shaker', 'tom', 'rim'):
            folder = self.root / 'drums' / kind
            if folder.is_dir():
                found = sorted(p for p in folder.iterdir() if p.suffix.lower() in ('.wav', '.ogg', '.flac'))
                if found:
                    self.oneshots[kind] = found

    def has(self, part: str) -> bool:
        if part in SOURCE_FOR_PART:
            return bool(self.regions[SOURCE_FOR_PART[part]])
        return part in self.oneshots

    def inventory(self) -> dict[str, int]:
        return {**{kind: len(self.regions[source]) for kind, source in SOURCE_FOR_PART.items()},
                **{f'drum_{kind}': len(files) for kind, files in self.oneshots.items()}}

    def _select(self, note: Note, seed: int) -> Region:
        source = SOURCE_FOR_PART[note.part]
        choices = self.regions[source]
        if not choices:
            raise FileNotFoundError(f'No {source} samples found in {self.root}; run tools/install_cc0.py')
        max_layer = max(c.layer for c in choices)
        layer = max(1, min(max_layer, math.ceil(note.velocity * max_layer)))
        distance = min((abs(c.midi - note.pitch), abs(c.layer - layer)) for c in choices)
        # Prioritize notes as close as possible, then dynamic layer.
        selected = [c for c in choices if (abs(c.midi - note.pitch), abs(c.layer - layer)) == distance]
        if distance[0] > 4:
            raise ValueError(f'No suitable {source} pitch within 4 semitones of MIDI {note.pitch}')
        return selected[_seed_index(seed, note.part, note.pitch, note.beat) % len(selected)]

    def render_note(self, note: Note, bpm: int, seed: int) -> np.ndarray:
        if note.part not in SOURCE_FOR_PART:
            raise ValueError(f'Unsupported sampled part: {note.part}')
        region = self._select(note, seed)
        source = _at_pitch(region.path, region.midi, note.pitch)
        duration = note.duration * 60 / bpm
        release = 0.11 if note.part == 'pluck' else 0.17
        frames = max(1, round((duration + release) * SR))
        out = np.zeros(frames, dtype=np.float32)
        n = min(frames, len(source))
        if n:
            out[:n] = source[:n]
        # Natural sample attack is retained. MIDI note-off only shapes its release.
        start = min(frames, round(duration * SR))
        if start < frames:
            t = np.arange(frames - start, dtype=np.float32) / SR
            out[start:] *= np.exp(-t / (release * .22))
        if not np.isfinite(out).all():
            raise ValueError('Invalid sampled note waveform')
        # Samples have different original peak levels; fixed per-voice gain preserves dynamics.
        out *= (0.48 if note.part == 'pluck' else 0.39) * note.velocity
        return out

    def render_drum(self, kind: str, velocity: float, event_key: int) -> np.ndarray:
        variants = self.oneshots.get(kind)
        if not variants:
            raise FileNotFoundError(f'No recorded drum one-shot for {kind}')
        sample = variants[_seed_index(kind, event_key) % len(variants)]
        y, sr = _load(sample)
        if sr != SR:
            f = Fraction(SR, sr).limit_denominator(4096)
            y = resample_poly(y, f.numerator, f.denominator).astype(np.float32)
        y = y[:round(2 * SR)].copy()
        if len(y):
            fade = min(len(y), round(.014*SR))
            y[-fade:] *= np.linspace(1,0,fade,dtype=np.float32)
        return y * (0.55 * velocity)

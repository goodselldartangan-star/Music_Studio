"""P2 guitar technique only: score-in/score-out, no sampler or mixer changes."""
from __future__ import annotations
from copy import deepcopy
from collections import defaultdict


def shape_strums(score: dict) -> tuple[dict, dict]:
    """Refine previously staggered chord attacks; preserve block chords and tails.

    3–6 ascending/descending pitches within 0.18 beats represent one stroke.
    Notes already started keep their full duration, so later string attacks
    never steal the earlier strings' ringing voices.
    """
    bpm = score['bpm']
    if not 50 <= bpm <= 210:
        raise ValueError('Bad tempo for strum shaping')
    shaped = deepcopy(score)
    notes = shaped['notes']
    by_part: dict[str, list[int]] = defaultdict(list)
    for i, note in enumerate(notes):
        if note['instrument'] in ('acoustic', 'electric'):
            by_part[note['instrument']].append(i)
    groups = 0
    changed = 0
    max_shift_ms = 0.
    counts = {'down': 0, 'up': 0}
    for part, indices in by_part.items():
        indices.sort(key=lambda i: (notes[i]['beat'], notes[i]['pitch']))
        pos = 0
        while pos < len(indices):
            start = notes[indices[pos]]['beat']
            group = [indices[pos]]
            pos += 1
            while pos < len(indices) and notes[indices[pos]]['beat'] - start <= .18:
                group.append(indices[pos])
                pos += 1
            if not 3 <= len(group) <= 6 or any(notes[i].get('technique') == 'block' for i in group):
                continue
            notes_now = [notes[i] for i in group]
            pitches = [n['pitch'] for n in notes_now]
            rising = all(a < b for a, b in zip(pitches, pitches[1:]))
            falling = all(a > b for a, b in zip(pitches, pitches[1:]))
            if not (rising or falling) or notes_now[-1]['beat'] - start < .005:
                continue
            if max(pitches) - min(pitches) > 19:
                continue
            direction = 'down' if rising else 'up'
            step_seconds = .014 if rising else .011
            for j, i in enumerate(group):
                n = notes[i]
                original = n['beat']
                n['beat'] = round(start + step_seconds * j * bpm / 60., 4)
                accent = round(3 * (1 - 2*j/max(1, len(group)-1)))
                n['velocity'] = max(1, min(127, n['velocity'] + accent - (2 if not rising else 0)))
                delta_ms = abs(n['beat'] - original) * 60 / bpm * 1000
                max_shift_ms = max(max_shift_ms, delta_ms)
                changed += 1
            groups += 1
            counts[direction] += 1
    report = {'strum_groups':groups, 'changed_notes':changed,
              'downstrokes':counts['down'], 'upstrokes':counts['up'],
              'max_onset_shift_ms':round(max_shift_ms, 3),
              'other_parts_unchanged':True}
    return shaped, report

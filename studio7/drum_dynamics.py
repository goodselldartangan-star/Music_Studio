"""P3: deterministic velocity phrasing for existing drum hits.

Only velocities change; kick, backbeat, hats and fills retain their exact
positions and sample identities. No pseudo-random 'humanization'.
"""
from __future__ import annotations
from copy import deepcopy
import math


def shape_drum_dynamics(score: dict) -> tuple[dict, dict]:
    """Emphasize phrase and limb roles without moving hits (max nine MIDI units)."""
    bpm = score['bpm']
    if not isinstance(bpm, (float, int)) or not math.isfinite(bpm) or not 50 <= bpm <= 210:
        raise ValueError('Invalid tempo')
    output = deepcopy(score)
    drums = output['drums']
    report = {'hits': len(drums), 'changed': 0, 'by_kind': {},
              'max_velocity_delta': 0, 'all_onsets_and_kinds_preserved': True}
    snares = [d['beat'] for d in drums if d['kind'] == 'snare']
    for d in drums:
        at = float(d['beat']); old = d['velocity']; kind = d['kind']
        if not math.isfinite(at) or at < 0 or not 1 <= old <= 127:
            raise ValueError('Invalid drum hit')
        if d.get('technique') in ('fixed', 'ghost', 'flam'):
            continue
        bar = int(at // 4)
        phase = at % 4
        bar_end = (bar + 1) % 4 == 0
        change = 0
        if kind == 'kick':
            if phase < .22:
                change = 3 if bar_end else 2
            elif abs(phase - 2) < .26:
                change = -2
            else:
                change = -3
        elif kind == 'snare':
            change = (6 if bar_end and abs(phase - 3) < .22 else
                      2 if abs(phase - 3) < .22 else 0)
        elif kind == 'hat':
            half_index = round(phase * 2)
            strong_subdivision = half_index % 2 == 0
            clashes = any(abs(at - t) < .09 for t in snares)
            change = 2 if strong_subdivision and not clashes else -4 if clashes else -2
            if bar_end and phase >= 3.45 and not clashes:
                change += 2
        elif kind == 'open_hat':
            change = -3 if any(abs(at-t) < .08 for t in snares) else 2
        elif kind in ('tom', 'rim', 'crash'):
            change = 3 if bar_end else 0
        d['velocity'] = max(1, min(127, int(old + change)))
        actual = d['velocity'] - old
        if actual:
            report['changed'] += 1
            report['by_kind'][kind] = report['by_kind'].get(kind, 0) + 1
            report['max_velocity_delta'] = max(report['max_velocity_delta'], abs(actual))
    return output, report

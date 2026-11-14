"""Q4: optional piano sustain-pedal *note-off timing* (not pedal resonance).

MIDI CC64 defers key release while down. Apply only explicit windows and only
to copied piano notes. The sampler still uses its original recorded decay and
does not gain true damper, sympathetic-string or pedal-mechanism samples.
"""
from __future__ import annotations
from copy import deepcopy
import math


def apply_piano_pedal_windows(score:dict, windows:list[tuple[float,float]])->tuple[dict,dict]:
    """Delay key-up for a note released during a pedal-down interval.

    Windows use score beats and must not overlap. Never shorten note duration,
    steal an earlier repeated-pitch voice or move a note's attack. Every window
    must end before the score boundary, preventing a held/stuck pedal.
    """
    bar_end=int(score['bars'])*4
    pairs=[]
    previous_end=-1.
    for raw_start,raw_end in sorted(windows):
        start=float(raw_start);end=float(raw_end)
        if not math.isfinite(start) or not math.isfinite(end) or not 0<=start<end<bar_end:
            raise ValueError('Invalid or unterminated CC64 pedal interval')
        if start<previous_end:
            raise ValueError('Overlapping pedal windows')
        pairs.append((start,end))
        previous_end=end
    shaped=deepcopy(score)
    shifted=0
    max_extension=0.
    for n in shaped['notes']:
        if n['instrument']!='piano' or n.get('pedal')=='ignore':
            continue
        if n['beat']<0 or n['length']<=0:
            raise ValueError('Bad piano note event')
        key_up=n['beat']+n['length']
        for start,end in pairs:
            if start<=key_up<end:
                # The note may still be held when the pedal goes down. This
                # delay is measured from the *original* key-release time.
                extension=end-key_up
                if extension>0:
                    updated=n['length']+extension
                    if updated>7:
                        raise ValueError('Pedal extension exceeds score duration contract')
                    n['length']=round(updated,4)
                    shifted+=1
                    max_extension=max(max_extension,extension)
                break
    return shaped, {
        'pedal_down_windows_beats':[[a,b] for a,b in pairs],
        'piano_notes_held_past_key_release':shifted,
        'max_noteoff_extension_beats':round(max_extension,4),
        'attack_pitch_velocity_unchanged':True,
        'independent_replucks_preserved':True,
        'true_pedal_mechanism_or_string_resonance':False,
    }


def atmospheric_pedal_windows(score:dict)->list[tuple[float,float]]:
    """Conservative opt-in Silver build/chorus touch; dry intro remains intact.

    Re-pedal every bar: up briefly before the next chord change. This is a
    style-specific experiment, not a general algorithm for musical pedal art.
    """
    if score.get('style')!='silver' or score.get('bars')!=16:
        raise ValueError('The opt-in authored pedal pattern is Silver-only')
    return [(round(bar*4+.02,3),round(bar*4+3.88,3))
            for bar in range(8,16)]


def shape_silver_pedal_timing(score:dict)->tuple[dict,dict]:
    return apply_piano_pedal_windows(score,atmospheric_pedal_windows(score))

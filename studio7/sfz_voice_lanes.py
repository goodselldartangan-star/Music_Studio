"""Q4: plan separate offline SFZ *instances* for independent same-key releases.

SFZ note-off events identify MIDI note numbers, not note-voice identities.
The measured sfizz CLI output showed another MIDI channel alone does not
prevent an earlier same-pitch tail being released. These immutable plans
reserve a separate synth instance while the same pitch is still active,
including its release-guard interval. No audio backend is changed here.
"""
from __future__ import annotations
from copy import deepcopy
from math import isfinite


def assign_sfz_voice_lanes(notes:list[dict],bpm:float,*,release_guard_s:float=.5,
                           max_instances:int=8)->tuple[list[list[dict]],dict]:
    """Return score notes allocated to separate intended synth instances.

    Different pitches can play on the same synth instance. A repeated pitch
    gets another instance when its earlier voice still rings, including the
    release guard. A note after guard expiry reuses the earliest eligible
    instance. This planner does not rewrite scores or call sfizz_render.
    """
    if not isfinite(bpm) or bpm<=0:
        raise ValueError("Invalid tempo")
    if not isfinite(release_guard_s) or not 0<=release_guard_s<=5:
        raise ValueError("Invalid release-guard interval")
    if not isinstance(max_instances,int) or not 1<=max_instances<=32:
        raise ValueError("Expected a bounded pool of 1–32 synth instances")
    live:list[dict[int,float]]=[]
    groups:list[list[dict]]=[]
    assigned=[None]*len(notes)
    for index,n in sorted(enumerate(notes),key=lambda x:(x[1]['beat'],x[0])):
        beat=float(n["beat"]);duration=float(n["length"])
        pitch=int(n["pitch"]);velocity=int(n["velocity"])
        if (not isfinite(beat) or not isfinite(duration)
                or beat<0 or duration<=0 or not 0<=pitch<=127
                or not 1<=velocity<=127):
            raise ValueError("Invalid note event for SFZ voice isolation")
        at=beat*60/bpm
        release=(beat+duration)*60/bpm+release_guard_s
        slot=next((i for i,lane in enumerate(live)
                   if lane.get(pitch,float('-inf'))<=at),None)
        if slot is None:
            if len(live)==max_instances:
                raise ValueError(
                    "Exhausted SFZ instance pool: refusing to steal sounding notes")
            slot=len(live)
            live.append({})
            groups.append([])
        live[slot][pitch]=release
        copy=deepcopy(n)
        groups[slot].append(copy)
        assigned[index]=slot
    assert all(x is not None for x in assigned)
    return groups,{
        "instance_count":len(groups),
        "input_notes":len(notes),
        "lane_per_original_note":assigned,
        "release_guard_s":release_guard_s,
        "independent_same_pitch_noteoffs":True,
        "limitation":"Scheduling only; each lane must be rendered by an independent SFZ synth instance."
    }

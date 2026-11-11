"""P2 piano touch only: deterministic voicing, attack spacing and velocity.

No artificial sustain pedal is claimed: the current sampled-piano backend cannot
reproduce true damper resonance from MIDI CC64. Note durations and pitches stay
authored; only already rolled dyads/chords are slightly re-timed.
"""
from __future__ import annotations
from copy import deepcopy
import math


def shape_piano(score: dict) -> tuple[dict, dict]:
    bpm=score["bpm"]
    if not isinstance(bpm,(int,float)) or not math.isfinite(bpm) or not 50<=bpm<=210:
        raise ValueError("Invalid tempo")
    shaped=deepcopy(score)
    notes=shaped["notes"]
    ids=sorted((i for i,n in enumerate(notes) if n["instrument"]=="piano"),
               key=lambda i:(notes[i]["beat"],notes[i]["pitch"]))
    changed=0
    velocity_changes=0
    onset_changes=0
    max_shift_ms=0.
    groups=0
    j=0
    while j<len(ids):
        first=notes[ids[j]]
        if not 21<=first["pitch"]<=108 or first["beat"]<0 or first["length"]<=0:
            raise ValueError("Invalid piano note")
        start=first["beat"]
        group=[ids[j]]
        j+=1
        while j<len(ids) and notes[ids[j]]["beat"]-start<=.08:
            group.append(ids[j]);j+=1
        locked=any(notes[i].get("technique") in ("fixed","block","pedal") for i in group)
        rolled=(2<=len(group)<=5 and notes[group[-1]]["beat"]-start>=.003
                and len({notes[i]["pitch"] for i in group})==len(group))
        if rolled and not locked:
            groups+=1
            # A played chord can have ~10-15 ms spread without becoming an arpeggio.
            step_s=.012 if start//4<12 else .010
            for k,i in enumerate(group[1:],start=1):
                old=notes[i]["beat"]
                new=round(start + (step_s * k * bpm/60),4)
                # Only move a note within the original chord group; never move
                # backwards before the first stroke or beyond its old onset.
                if new<old:
                    notes[i]["beat"]=new
                    onset_changes+=1
                    max_shift_ms=max(max_shift_ms,(old-new)*60/bpm*1000)
        for i in group:
            n=notes[i]
            if n.get("technique") in ("fixed","block","pedal"):
                continue
            bar=int(n["beat"]//4)
            phase=n["beat"]%4
            accent=(-4 if bar<4 else 3 if bar>=12 else -2 if bar%4==3 else 0)
            accent+=2 if phase<.25 else -1
            if len(group)>1:
                # More weight in the lowest supporting voice; never transpose notes.
                accent+=2 if n["pitch"]==min(notes[t]["pitch"] for t in group) else -1
            old=n["velocity"]
            if not 1<=old<=127:raise ValueError("Invalid piano velocity")
            n["velocity"]=min(127,max(1,old+accent))
            velocity_changes+=int(n["velocity"]!=old)
            changed+=int(n["velocity"]!=old or n["beat"]!=score["notes"][i]["beat"])

    return shaped,{
        "piano_notes":len(ids),
        "changed_notes":changed,
        "velocity_changes":velocity_changes,
        "onset_changes":onset_changes,
        "rolled_chord_groups":groups,
        "max_onset_shift_ms":round(max_shift_ms,3),
        "pitch_and_length_unchanged":True,
        "sustain_pedal":False,
    }

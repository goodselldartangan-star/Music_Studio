"""Q2 opt-in physically coherent sampled guitar string assignment.

A recorded steel/nylon sample has a specific string zone encoded in its
filename. Independently randomizing that zone for every note can use the same
physical string for multiple different pitches in one ringing guitar chord.
This module selects source *recordings* only. It does not modify MIDI, damp
overlapping audio, or change older Studio versions' samplers.
"""
from __future__ import annotations
from dataclasses import dataclass
from hashlib import sha256
from itertools import product
from pathlib import Path
from typing import Sequence
import math
import re

STRINGS=("LowE","A","D","G","B","HighE")
OPEN_MIDI=(40,45,50,55,59,64)
ZONE=re.compile(r"_String(LowE|A|D|G|B|HighE)_",re.I)


@dataclass(frozen=True)
class Source:
    region: object
    path: Path
    pitch: int
    layer: int
    string_idx: int

    @property
    def fret(self)->int:
        return self.pitch-OPEN_MIDI[self.string_idx]


def _parse_region(region:object)->Source:
    if hasattr(region,"path"):
        path=Path(region.path)
        pitch=int(region.midi)
        layer=int(region.layer)
    else:
        path=Path(region[0])
        pitch=int(region[1])
        layer=int(region[2])
    m=ZONE.search(path.name)
    if m is None:
        raise ValueError(f"Recorded guitar sample lacks physical string zone: {path.name}")
    index=next(i for i,name in enumerate(STRINGS) if name.lower()==m[1].lower())
    return Source(region,path,pitch,layer,index)


def _relevant(notes:Sequence[dict],src:list[Source])->list[list[Source]]:
    largest=max(x.layer for x in src)
    pools=[]
    for note in notes:
        pitch=int(note["pitch"])
        velocity=int(note["velocity"])
        if not 0<=pitch<=127 or not 1<=velocity<=127:
            raise ValueError("Invalid pitch or velocity")
        layer=math.ceil(velocity/127*largest)
        distance=min((abs(s.pitch-pitch),abs(s.layer-layer)) for s in src)
        if distance[0]>4:
            raise ValueError(f"No recorded guitar source within 4 semitones of MIDI {pitch}")
        options=[s for s in src if (abs(s.pitch-pitch),abs(s.layer-layer))==distance]
        pools.append(sorted(options,key=lambda s:(s.string_idx,s.path.name)))
    return pools


def _stable_choice(options:list[Source],identity:int,pitch:int,layer:int)->Source:
    # Durations and start positions are deliberately NOT hashed. Note index
    # provides repeatable take variation across attacks of the same pitch.
    value=sha256(f"{identity}:{pitch}:{layer}".encode()).digest()
    return options[int.from_bytes(value[:8],"big")%len(options)]


def _chord_candidates(group:list[int],notes:Sequence[dict],pools:list[list[Source]])->list[Source]|None:
    if not 3<=len(group)<=6:
        return None
    pitches=[int(notes[i]["pitch"]) for i in group]
    # A strum has strictly rising or falling pitches in stroke order; block
    # chords and solo melodies are not silently re-voiced.
    if len(set(pitches))!=len(pitches):
        return None
    if not (all(a<b for a,b in zip(pitches,pitches[1:])) or
            all(a>b for a,b in zip(pitches,pitches[1:]))):
        return None
    if max(pitches)-min(pitches)>20:
        return None
    pitch_order=sorted(group,key=lambda i:notes[i]["pitch"])
    available=[[r for r in pools[i] if 0<=notes[i]["pitch"]-OPEN_MIDI[r.string_idx]<=20]
               for i in pitch_order]
    if any(not options for options in available):
        return None
    best=None;best_key=None
    for combo in product(*available):
        idx=[x.string_idx for x in combo]
        if any(a>=b for a,b in zip(idx,idx[1:])):
            continue
        frets=[notes[i]["pitch"]-OPEN_MIDI[r.string_idx] for i,r in zip(pitch_order,combo)]
        held=[f for f in frets if f>0]
        spread=max(held)-min(held) if held else 0
        # Low-fret voicings and compact non-open-fret reach are generally
        # easier to play. The ordering must still be physically possible.
        cost=(sum(f*.13+max(0,f-7)*1.5 for f in frets)
              +max(0,spread-5)*2.0 + spread*.18)
        key=(round(cost,5),tuple(idx),tuple(r.path.name for r in combo))
        if best_key is None or key<best_key:
            best_key=key
            best=dict(zip(pitch_order,combo))
    return [best[i] for i in group] if best is not None else None


def plan_guitar_samples(notes:Sequence[dict],regions:Sequence[object],*,seed_base:int=0)->tuple[list[object],dict]:
    """Return one original file region per note, with distinct strings in strums.

    Every note keeps the same pitch, velocity layer, attack time and duration.
    A live string model is deliberately NOT enforced across separated plucks:
    overlapping/retriggered voices must stay independent, as requested.
    """
    if not regions and notes:
        raise FileNotFoundError("Recorded guitar region bank is empty")
    if not notes:
        return [],{"strums":0,"mapped_distinct_strums":0,"unmapped_strums":0,
                   "remaining_intra_strum_string_conflicts":0}
    src=[_parse_region(r) for r in regions]
    pools=_relevant(notes,src)
    choices=[_stable_choice(options,seed_base+i,notes[i]["pitch"],options[0].layer)
             for i,options in enumerate(pools)]
    ordered=sorted(range(len(notes)),key=lambda i:(notes[i]["beat"],notes[i]["pitch"]))
    groups=[];pos=0
    while pos<len(ordered):
        start=notes[ordered[pos]]["beat"]
        group=[ordered[pos]]
        pos+=1
        while pos<len(ordered) and notes[ordered[pos]]["beat"]-start<=.18:
            group.append(ordered[pos]);pos+=1
        if 3<=len(group)<=6 and notes[group[-1]]["beat"]-start>.005:
            groups.append(group)
    distinct=0
    failed=0
    summaries=[]
    for group in groups:
        result=_chord_candidates(group,notes,pools)
        if result is None:
            failed+=1
        else:
            for i,choice in zip(group,result):
                choices[i]=choice
            distinct+=1
        strings=[STRINGS[choices[i].string_idx] for i in group]
        summaries.append({"beat":round(notes[group[0]]["beat"],3),
                          "pitches":[notes[i]["pitch"] for i in group],
                          "source_strings":strings,
                          "duplicate_string_occupancies":len(strings)-len(set(strings)),
                          "physically_mapped":result is not None})
    metrics={"strums":len(groups),"mapped_distinct_strums":distinct,
             "unmapped_strums":failed,
             "remaining_intra_strum_string_conflicts":
               sum(x["duplicate_string_occupancies"] for x in summaries),
             "assignments":summaries,
             "limitations":"Physical sample selection in each strum, not a full fretboard simulation; existing overlapping note tails are unchanged."}
    return [r.region for r in choices],metrics

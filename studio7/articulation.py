"""Independent note-lifecycle engine. No score, mixer or external AI dependencies.

Why this exists: a new note-on for the same pitch in FluidSynth releases a
previously playing voice on that channel. We allocate independent MIDI channels
for simultaneously sounding notes and preserve their soundfont release stages.
PCM instruments use an explicit smooth note-off envelope rather than the old
~30ms near-instant fade. This changes sound, not the authored score.
"""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence
import numpy as np
from studio6.soundfonts import FluidSynth, SR

CHANNELS = tuple(i for i in range(16) if i != 9)  # MIDI 10 is reserved for drums.

@dataclass(frozen=True)
class Articulation:
    attack_s: float
    release_s: float
    connect_gap_s: float = 0.0
    overlap_s: float = 0.0

PROFILES = {
    'acoustic': Articulation(.003, .24),
    'electric': Articulation(.005, .31, .095, .035),
    'lead': Articulation(.009, .34, .12, .04),
    'piano': Articulation(.004, .48),
    'bass': Articulation(.003, .12),
}


def smooth_release(source: np.ndarray, duration_s: float, *, part: str, sr: int=SR) -> np.ndarray:
    """Preserve source attack, let the released recorded note decay without a click.

    A sample that ends before the MIDI note naturally becomes silent: this
    function does NOT invent a false sustained waveform or time-stretch it.
    """
    if source.ndim != 1 or not np.isfinite(source).all():
        raise ValueError('Expected finite mono sample')
    if duration_s <= 0 or sr < 8000 or part not in PROFILES:
        raise ValueError('Invalid note release inputs')
    profile=PROFILES[part]
    hold=max(1,round(duration_s*sr));release=max(1,round(profile.release_s*sr))
    out=np.zeros(hold+release,dtype=np.float32)
    n=min(len(source),len(out));out[:n]=source[:n]
    attack=min(n,max(1,round(profile.attack_s*sr)))
    if attack>1:out[:attack]*=np.linspace(0,1,attack,dtype=np.float32)
    if n>hold:
        x=np.arange(n-hold,dtype=np.float32)/(release-1 if release>1 else 1)
        out[hold:n]*=(.5+.5*np.cos(np.pi*np.minimum(1,x))).astype(np.float32)
    return out


def planned_events(notes: Sequence[dict], bpm:int, *, part:str='electric') -> list[dict]:
    """Honor authored note lengths; connect only near-touching melodic phrases.

    Note-onsets never move. Explicit rests longer than connect_gap_s survive.
    Piano and chord parts are NOT automatically legato-extended.
    """
    if bpm<=0 or part not in PROFILES:raise ValueError('Bad tempo or part')
    profile=PROFILES[part]
    entries=[]
    for note in notes:
        st=note['beat']*60/bpm
        end=(note['beat']+note['length'])*60/bpm
        if st<0 or end<=st or not 0<note['velocity']<=127 or not 0<=note['pitch']<=127:
            raise ValueError('Invalid MIDI event')
        entries.append(dict(at=float(st),off=float(end),pitch=int(note['pitch']),velocity=int(note['velocity'])))
    entries.sort(key=lambda x:(x['at'],x['pitch']))
    if profile.overlap_s:
        for i,x in enumerate(entries[:-1]):
            nxt=entries[i+1]
            gap=nxt['at']-x['off']
            if -0.08 <= gap <= profile.connect_gap_s and nxt['at']>x['at']+0.08:
                x['off']=max(x['off'],nxt['at']+profile.overlap_s)
    return entries


def assign_voice_channels(events:Sequence[dict], *, release_guard_s:float=.22) -> list[dict]:
    """Assign different channels to notes whose sounding lifetimes overlap.

    Includes release tail in the reservation, so same-pitch retriggers don't
    unexpectedly steal a previous voice during its decay.
    """
    if not 0<=release_guard_s<=2:raise ValueError('Bad release guard')
    busy_until={c:-1e9 for c in CHANNELS}
    result=[]
    for e in sorted(events,key=lambda x:(x['at'],x['pitch'])):
        if e['off']<=e['at']:raise ValueError('note ends before note-on')
        available=[c for c in CHANNELS if busy_until[c]<=e['at']]
        if not available:
            raise ValueError('Too many simultaneous notes: split the stem or increase capacity')
        ch=min(available,key=lambda c:(busy_until[c],c))
        busy_until[ch]=e['off']+release_guard_s
        result.append({**e,'channel':ch})
    return result


def render_polyphonic(soundfont:Path,notes:list[dict],seconds:float,bpm:int,
                       *,part:str='electric',program:int=0)->np.ndarray:
    """Render melodic SF2 patches with isolated overlapping voices.

    Drums retain their original exclusive hi-hat groups and are not routed here.
    """
    if seconds<=0:raise ValueError('Bad duration')
    if part not in PROFILES:raise ValueError('Bad part')
    events=assign_voice_channels(planned_events(notes,bpm,part=part),release_guard_s=PROFILES[part].release_s)
    engine=FluidSynth(Path(soundfont),gain=.33,drum=False)
    try:
        for ch in {e['channel'] for e in events}:
            if engine.select(engine.synth,ch,engine.id,0,program)!=0:
                raise ValueError(f'SoundFont has no program {program}')
        timeline=[];frames=round(seconds*SR)
        for e in events:
            on=max(0,min(frames,round(e['at']*SR)))
            off=max(on+1,min(frames,round(e['off']*SR)))
            timeline.extend([(on,1,e['channel'],e['pitch'],e['velocity']),
                             (off,0,e['channel'],e['pitch'],0)])
        timeline.sort(key=lambda x:(x[0],x[1]))
        out=np.zeros((frames,2),np.float32);pos=0;k=0
        while pos<frames:
            boundary=timeline[k][0] if k<len(timeline) else frames
            if boundary>pos:
                size=boundary-pos
                left=np.empty(size,np.float32);right=np.empty(size,np.float32)
                engine.write(engine.synth,size,left.ctypes.data,0,1,right.ctypes.data,0,1)
                out[pos:boundary,0]=left;out[pos:boundary,1]=right;pos=boundary
            while k<len(timeline) and timeline[k][0]<=pos:
                _,on,ch,p,v=timeline[k]
                if on:engine.noteon(engine.synth,ch,p,v)
                else:engine.noteoff(engine.synth,ch,p)
                k+=1
        return out
    finally:
        engine.close()


def render_meta_note(bank, note, bpm:int, seed:int)->np.ndarray:
    """SampleBank compatible, but with independent musical release behavior.

    Keep the old shared SampleBank untouched for prior Music Studio versions.
    """
    from studio3.sample_bank import _at_pitch
    if note.part not in ('pluck','keys'):raise ValueError('Unsupported recorded note role')
    region=bank._select(note,seed)
    raw=_at_pitch(region.path,region.midi,note.pitch)
    part='acoustic' if note.part=='pluck' else 'piano'
    out=smooth_release(raw,note.duration*60/bpm,part=part)
    return out*(.48 if part=='acoustic' else .39)*note.velocity

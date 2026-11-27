"""Q4.2 opt-in *stopped-string* acoustic plucks, not invented mute samples.

The recorded pick/finger attack is untouched. A playable note can be
individually stopped by damping its own remaining sample tail. This is a
post-pluck stop, NOT a claim of a source-recorded palm-muted attack.
No piano, bass, DSP master, source assets or original score is rewritten.
"""
from __future__ import annotations

from copy import deepcopy
import math

import numpy as np

SR=44100
TECHNIQUE="stopped_string_release"


def damp_note_tail(wave:np.ndarray, *,start_ms:float,fade_ms:float=42,
                   sr:int=SR)->np.ndarray:
    """Smoothly stop this one pluck without touching its attack or other voices."""
    if (wave.ndim not in (1,2) or wave.size==0 or not np.isfinite(wave).all()
            or sr<8000 or not math.isfinite(start_ms)
            or not math.isfinite(fade_ms) or not 90<=start_ms<=1000
            or not 12<=fade_ms<=150):
        raise ValueError("Invalid independent pluck damping")
    st=round(start_ms*sr/1000)
    en=round((start_ms+fade_ms)*sr/1000)
    result=wave.copy()
    if st>=len(result):
        return result
    # Raised cosine reaches EXACT zero at fade end and cannot click.
    end=min(len(result),en)
    steps=np.arange(st,end,dtype=np.float64)
    gain=(.5+.5*np.cos(np.pi*(steps-st)/max(1,en-st))).astype(np.float32)
    if wave.ndim==1:
        result[st:end]*=gain
        result[end:]=0
    else:
        result[st:end]*=gain[:,None]
        result[end:]=0
    return result


def note_if_tagged(audio:np.ndarray,note:dict)->np.ndarray:
    if note.get("technique")!=TECHNIQUE:
        return audio
    return damp_note_tail(audio,
                          start_ms=float(note["damp_after_ms"]),
                          fade_ms=float(note.get("damp_fade_ms",42)))


def shape_harbor_stopped_upstrokes(score:dict)->tuple[dict,dict]:
    """Annotate *only* six Harbor upstroke groups; pitches/times/lengths intact.

    No automatic muting: an explicitly labelled optional score copy drives
    per-note acoustic damping. Preserve all earlier notes and their voices.
    """
    if score.get("style")!="harbor":
        return deepcopy(score),{"damped_strokes":0,"tagged_notes":0,
                                 "all_music_events_unchanged":True}
    out=deepcopy(score)
    chosen=(4,6,8,10,12,14)
    all_indices=[]
    for bar in chosen:
        target=bar*4+2.17
        # Harbor currently has four separate, already staggered string attacks.
        group=[i for i,n in enumerate(out["notes"])
               if n["instrument"]=="acoustic"
               and 0<=n["beat"]-target<=.12]
        if len(group)!=4 or any(out["notes"][i].get("technique") for i in group):
            raise ValueError(f"Source Harbor upstroke bar {bar} is not four free voices")
        all_indices.extend(group)
    for i in all_indices:
        out["notes"][i]["technique"]=TECHNIQUE
        out["notes"][i]["damp_after_ms"]=240
        out["notes"][i]["damp_fade_ms"]=42
    return out,{"damped_strokes":len(chosen),
                "tagged_notes":len(all_indices),
                "chosen_bars":list(chosen),
                "all_music_events_unchanged":True,
                "description":"Only release of specifically tagged original recorded guitar plucks changes; recorded attack and older independent voices remain."}

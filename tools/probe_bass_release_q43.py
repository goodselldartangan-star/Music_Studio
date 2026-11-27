"""Q4.3 genuine FreePats bass same-pitch release overlap diagnostic.

Compares the Music Studio 120-ms channel reservation to a source-informed
release guard. Nothing switches production bass until the A/B shows a
meaningful note-tail defect and all untouched notes remain unchanged.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import re

import numpy as np
import soundfile as sf

from studio7.articulation import planned_events,assign_voice_channels,render_polyphonic
from studio7.effects import SR
from tools.audit_articulation_q42 import sf2_inventory,sfz_regions


def rms(x:np.ndarray)->float:
    x=np.asarray(x,dtype=np.float64)
    return float(np.sqrt(np.mean(x*x)))


def source_release_s(text:str)->float:
    t=re.sub(r"(?m)//[^\n]*","",text)
    matches=re.findall(r"\bampeg_release\s*=\s*(\d+(?:\.\d+)?)",t)
    if len(matches)!=1:
        raise ValueError("Expected exactly one global original bass release setting")
    seconds=float(matches[0])
    if not 0.05<=seconds<=1.5:
        raise ValueError("Unreasonable original SFZ release time")
    return seconds


def _events()->list[dict]:
    # Note 35 (B1): mapped to genuine notes in both finger/picked bank.
    # First note ends at 0.26s; second pluck starts at 0.44s and ends
    # at 0.56s. The 180-ms gap is > Studio's 120-ms channel reservation
    # but < FreePats' documented 300–500ms release envelope.
    return [
        {"beat":0.0,"length":.52,"pitch":35,"velocity":100},
        {"beat":.88,"length":.24,"pitch":35,"velocity":90}]


def measure(sf2:Path,sfz:Path,*,out:Path,label:str)->dict:
    original=sfz.read_text()
    source=sfz_regions(original)
    if source["release_trigger_region_count"]!=0:
        raise ValueError("Unexpected explicit sample-release region")
    manifest=sf2_inventory(sf2)
    if not 10<=manifest["sample_header_count"]<=16:
        raise ValueError("Expected original compact bass soundfont")
    release=source_release_s(original)
    notes=_events()
    events=planned_events(notes,120,part="bass")
    old_channels=[n["channel"] for n in assign_voice_channels(events,release_guard_s=.12)]
    guarded_channels=[n["channel"] for n in assign_voice_channels(events,release_guard_s=release)]
    if old_channels!=[0,0] or guarded_channels!=[0,1]:
        raise AssertionError("Wrong exact same-pitch retrigger fixture routing")
    seconds=1.6
    old=render_polyphonic(sf2,notes[:1],seconds,120,part="bass")
    new=render_polyphonic(sf2,notes[1:],seconds,120,part="bass")
    reused=render_polyphonic(sf2,notes,seconds,120,part="bass",
                             release_guard_s=.12)
    isolated=render_polyphonic(sf2,notes,seconds,120,part="bass",
                               release_guard_s=release)
    for a in (old,new,reused,isolated):
        if a.shape!=(round(seconds*SR),2) or not np.isfinite(a).all():
            raise AssertionError("Unplayable FreePats SF2 bass output")
    if min(rms(old),rms(new))<1e-5:
        raise AssertionError("Missing real original bass sample audio")
    # FluidSynth's global reverb is not perfectly linear; a reference sum
    # is a diagnostic approximation, NOT ground truth voice extraction.
    expected=old+new
    window=slice(round(.58*SR),round(.71*SR))
    expected_tail_rms=rms(expected[window])
    error_reused=rms((reused-expected)[window])/max(expected_tail_rms,1e-10)
    error_isolated=rms((isolated-expected)[window])/max(expected_tail_rms,1e-10)
    diff=rms((isolated-reused)[window])
    if expected_tail_rms<=1e-7:
        raise AssertionError("No measurable tail during post-new-noteoff test window")
    out=Path(out)
    out.mkdir(parents=True,exist_ok=True)
    wave_path=out/f"Q43_{label}_bass_transition.wav"
    # A dry 1.6s diagnostic; no claim of mastered playback.
    sf.write(wave_path,isolated,SR,subtype="PCM_24")
    data={
        "source":f"FreePats {label} bass original CC0 SoundFont",
        "source_sfz_release_seconds":release,
        "studio_default_release_guard_seconds":.12,
        "source_sf2_sample_count":manifest["sample_header_count"],
        "fixture_pitch_midi":35,
        "first_noteoff_seconds":.26,
        "second_attack_seconds":.44,
        "second_noteoff_seconds":.56,
        "observed_channels_default":old_channels,
        "observed_channels_source_guard":guarded_channels,
        "old_note_only_window_rms":round(rms(old[window]),9),
        "new_note_only_window_rms":round(rms(new[window]),9),
        "reference_additive_window_rms":round(expected_tail_rms,9),
        "reused_channel_relative_window_error":round(error_reused,7),
        "isolated_channel_relative_window_error":round(error_isolated,7),
        "isolated_minus_reused_window_rms":round(diff,9),
        "change_is_measurable":bool(diff>1e-6),
        "guard_is_better_versus_additive_reference":bool(
            error_isolated+0.03<error_reused),
        "limitations":"Original SFZ release differs from actual SF2 envelope mapping. Reference uses a two-render sum and is approximate due to reverb; do not claim objective musical preference."
    }
    (out/f"Q43_{label}_bass_transition.json").write_text(json.dumps(data,indent=2))
    print(json.dumps(data,indent=2))
    return data


if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--source-root",type=Path,required=True)
    p.add_argument("--fonts",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    for kind in ("finger","picked"):
        measure(a.fonts/f"{kind}_bass.sf2",a.source_root/f"{kind}_bass.sfz",
                label=kind,out=a.out)

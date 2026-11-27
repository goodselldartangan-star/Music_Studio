"""Q4.3 follow-up: sweep every key of original FreePats finger/picked bass.

Each source key gets a same-pitch second attack 180 ms after previous noteoff.
Compare existing 120-ms voice guard against source-SFZ duration, without
altering scores, samples or the production backend. This measures whether a
new independent MIDI channel actually matters anywhere in the played range.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from studio7.articulation import render_polyphonic
from studio7.effects import SR
from studio7.score import make
from tools.probe_bass_release_q43 import source_release_s,rms
from tools.audit_articulation_q42 import sfz_regions,sf2_inventory


def original_bass_pitches()->list[int]:
    notes={int(n["pitch"])
           for style in ("harbor","after","silver")
           for n in make(style)["notes"] if n["instrument"]=="bass"}
    if not notes or min(notes)<26 or max(notes)>45:
        raise ValueError("Original bass range no longer fits available original SF2 bank")
    return sorted(notes)


def sweep(font:Path,definition:Path,*,label:str,out:Path)->dict:
    from studio7.articulation import PROFILES
    if PROFILES["bass"].release_s!=.12:
        raise ValueError("Existing baseline release profile changed")
    original=definition.read_text()
    source=sfz_regions(original)
    if source["release_trigger_region_count"]!=0:
        raise ValueError("Unexpected source release trigger added")
    envelope=source_release_s(original)
    sf=sf2_inventory(font)
    if not 10<=sf["sample_header_count"]<=16:
        raise ValueError("Unexpected original SF2 source zones")
    notes=original_bass_pitches()
    results=[]
    for pitch in notes:
        duo=[
            dict(beat=0.,length=.52,pitch=pitch,velocity=100),
            dict(beat=.88,length=.24,pitch=pitch,velocity=90)]
        default=render_polyphonic(font,duo,1.25,120,
                                 part="bass",release_guard_s=.12)
        isolated=render_polyphonic(font,duo,1.25,120,
                                  part="bass",release_guard_s=envelope)
        if default.shape!=(round(1.25*SR),2) or isolated.shape!=default.shape:
            raise AssertionError("Same-pitch sweep output shape mismatch")
        if not np.isfinite(default).all() or not np.isfinite(isolated).all():
            raise AssertionError("Bass rendered invalid sample data")
        # The entire 1.25s includes both attacks plus release, while the
        # 0.58–0.78s window checks post-short-noteoff retained tails.
        tail=slice(round(.58*SR),round(.78*SR))
        error=float(rms(default-isolated))
        tail_error=float(rms(default[tail]-isolated[tail]))
        results.append({
            "pitch":pitch,
            "default_rms":round(rms(default),9),
            "source_guard_rms":round(rms(isolated),9),
            "whole_note_difference_rms":round(error,9),
            "post_repluck_noteoff_difference_rms":round(tail_error,9),
            "relative_post_repluck_difference":
                round(tail_error/max(rms(isolated[tail]),1e-10),7)})
    report={
        "source":f"Original FreePats CC0 {label} bass",
        "score_names":["harbor","after","silver"],
        "source_release_seconds":envelope,
        "default_voice_guard_seconds":.12,
        "source_sample_headers":sf["sample_header_count"],
        "distinct_original_score_pitches_tested":len(notes),
        "max_whole_note_difference_rms":max(v["whole_note_difference_rms"] for v in results),
        "max_post_repluck_noteoff_difference_rms":max(v["post_repluck_noteoff_difference_rms"] for v in results),
        "pitches_with_difference_above_1e-6":[r["pitch"] for r in results
            if r["post_repluck_noteoff_difference_rms"]>1e-6],
        "per_pitch":results,
        "limitations":"True SF2 sample release behavior on the CI FluidSynth version; no claims for other SoundFonts or a sampled slide/legato sound."
    }
    out=Path(out)
    out.mkdir(parents=True,exist_ok=True)
    (out/f"Q43_{label}_bass_full_score_pitch_sweep.json").write_text(
        json.dumps(report,indent=2))
    print(json.dumps({k:v for k,v in report.items() if k!="per_pitch"},indent=2))
    return report


if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--source-root",type=Path,required=True)
    p.add_argument("--fonts",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    for label in ("finger","picked"):
        sweep(a.fonts/f"{label}_bass.sf2",a.source_root/f"{label}_bass.sfz",
              label=label,out=a.out)

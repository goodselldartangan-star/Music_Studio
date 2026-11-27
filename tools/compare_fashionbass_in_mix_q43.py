"""Q4.3 source-backed bass choice within identical full recorded-instrument Harbor.

A: existing CC0 FreePats finger bass SF2. B: full original CC0 Karoryfer
Fashionbass sfizz stem (285 pitched notes + recorded releases and noises).
Only the bass dry waveform is changed; preserve unchanged scores and
unaffected processed guitar/piano/drums/lead/electric. Match previews ONLY.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import subprocess

import numpy as np
import soundfile as sf

from studio7.score import make
from studio7.render import instrument_stems,process_stems
from studio7.effects import SR


def rms(x:np.ndarray)->float:
    x=np.asarray(x,dtype=np.float64)
    return float(np.sqrt(np.mean(x*x)))


def load_original_bass_stem(path:Path,score:dict)->np.ndarray:
    audio,sr=sf.read(path,dtype="float32",always_2d=True)
    frames=round(score["duration"]*SR)
    if (sr!=SR or audio.shape!=(frames,2) or not np.isfinite(audio).all()
            or rms(audio)<1e-7):
        raise ValueError("Full original Fashionbass source stem malformed or silent")
    return audio


def compare(*,assets:Path,fashionbass:Path,out:Path)->dict:
    score=make("harbor")
    raw=instrument_stems(score,assets=Path(assets))
    new_bass=load_original_bass_stem(Path(fashionbass),score)
    if raw["bass"].shape!=new_bass.shape:
        raise AssertionError("Two source basses have different score durations")
    old_dry=rms(raw["bass"])
    new_dry=rms(new_bass)
    if min(old_dry,new_dry)<1e-7:
        raise AssertionError("Missing original recorded bass")
    unchanged={**raw,"bass":new_bass}
    for role in raw:
        if role!="bass" and not np.array_equal(raw[role],unchanged[role]):
            raise AssertionError("Raw non-bass stem changed")
    old_mix,old_parts,old_diag=process_stems(score,raw,with_effects=True)
    new_mix,new_parts,new_diag=process_stems(score,unchanged,with_effects=True)
    for role in raw:
        if role!="bass" and not np.array_equal(old_parts[role],new_parts[role]):
            raise AssertionError("Processed non-bass stem changed")
    processed_bass_db=20*math.log10(
        max(rms(new_parts["bass"]),1e-10)/max(rms(old_parts["bass"]),1e-10))
    if abs(processed_bass_db)>1.:
        raise AssertionError("Full mix piano/bass level policy changed unexpectedly")
    difference=rms(old_mix-new_mix)
    if difference<=1e-5:
        raise AssertionError("Full source bass tone didn't change actual song")
    # Keep both 12s previews at the same overall RMS so volume is not
    # mistaken for a better tone. Never write this gain into production.
    st=round(18*SR)
    count=round(12*SR)
    old_clip=old_mix[st:st+count]
    new_clip=new_mix[st:st+count]
    if len(old_clip)!=count or len(new_clip)!=count:
        raise ValueError("Comparison exceeds scored song")
    gain_b=rms(old_clip)/max(rms(new_clip),1e-10)
    if not .4<=gain_b<=2.5:
        raise AssertionError("Unsafe comparison-only volume correction")
    global_gain=min(1.,.82/max(float(np.max(abs(old_clip))),
                                    float(np.max(abs(new_clip*gain_b))),1e-12))
    clips={
        "current_FreePats_finger_bass":(old_clip*global_gain).astype(np.float32),
        "optional_Karoryfer_Fashionbass":(new_clip*gain_b*global_gain).astype(np.float32)}
    out=Path(out)
    out.mkdir(parents=True,exist_ok=True)
    results={}
    for name,pcm in clips.items():
        peak=float(np.max(abs(pcm)))
        if peak>.8205 or not np.isfinite(pcm).all():
            raise AssertionError("Bass in context comparison clipped")
        mp3=out/f"Q43_Harbor_{name}.mp3"
        wav=out/f"Q43_Harbor_{name}.wav"
        sf.write(wav,pcm,SR,subtype="PCM_24")
        subprocess.run(["ffmpeg","-nostdin","-v","error","-y",
                        "-i",str(wav),"-c:a","libmp3lame","-b:a","224k",
                        str(mp3)],check=True)
        subprocess.run(["ffmpeg","-nostdin","-v","error","-xerror",
                        "-i",str(mp3),"-f","null","-"],check=True)
        wav.unlink()
        results[name]={"mp3":mp3.name,"peak":round(peak,6),
                        "rms_dbfs":round(20*math.log10(max(rms(pcm),1e-10)),3)}
    level_delta=abs(results["current_FreePats_finger_bass"]["rms_dbfs"]
                    -results["optional_Karoryfer_Fashionbass"]["rms_dbfs"])
    if level_delta>.05:
        raise AssertionError("Bass comparisons have unmatched listener volume")
    report={
        "style":"harbor",
        "original_bass_events":len([n for n in score["notes"] if n["instrument"]=="bass"]),
        "source_a":"FreePats Yamaha RBX CC0 finger bass SF2 (existing)",
        "source_b":"Karoryfer Fashionbass CC0 426-source original SFZ, independent sfizz instances (experimental)",
        "original_dry_bass_rms":round(old_dry,8),
        "new_dry_bass_rms":round(new_dry,8),
        "processed_bass_rms_difference_db":round(processed_bass_db,4),
        "unchanged_all_other_raw_stems":True,
        "unchanged_all_other_processed_stems":True,
        "same_original_note_pitch_timing_velocity_length":True,
        "full_song_waveform_difference_rms":round(difference,8),
        "comparison_only_fashionbass_gain":round(gain_b,6),
        "common_comparison_headroom_gain":round(global_gain,6),
        "full_mix_excerpt_level_difference_db":round(level_delta,3),
        "previews":results,
        "caveat":"This validates audio compatibility, not preference, genuine slides, or all SFZ semantics. No released music or default backend changed."
    }
    (out/"Q43_recorded_bass_in_full_Harbor_report.json").write_text(json.dumps(report,indent=2))
    print(json.dumps(report,indent=2))
    return report


if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--assets",type=Path,required=True)
    p.add_argument("--fashionbass",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    compare(assets=a.assets,fashionbass=a.fashionbass,out=a.out)

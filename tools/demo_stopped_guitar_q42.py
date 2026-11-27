"""Q4.2 genuine Meta-steel sample-backed, matched-level stopped-pluck A/B.

Two copies of the same optional string-mapped Harbor guitar arrangement.
One retains all original ringing notes; the other stops only 24 specifically
marked upstroke notes. Do not replace or publish any original music.
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
from studio7.render import _sample_meta
from studio7.string_mapping import shape_harbor_bm_guitar
from studio7.guitar_damping_q42 import shape_harbor_stopped_upstrokes,SR


def rms(x:np.ndarray)->float:
    return float(np.sqrt(np.mean(np.asarray(x,dtype=np.float64)**2)))


def demo(assets:Path,out:Path)->dict:
    score,voicings=shape_harbor_bm_guitar(make("harbor"))
    processed,stats=shape_harbor_stopped_upstrokes(score)
    if stats["tagged_notes"]!=24 or stats["damped_strokes"]!=6:
        raise AssertionError("Unexpected count of optional stopped guitar strings")
    # Both sources use the same recorded strings and original stereo/timing
    # rules; only the per-note tail envelope changes.
    original=_sample_meta(score,"acoustic",assets,string_aware=True)
    stopped=_sample_meta(processed,"acoustic",assets,string_aware=True)
    if original.shape!=stopped.shape or not np.isfinite(stopped).all():
        raise AssertionError("Invalid stopped guitar PCM")
    opening=round(8*SR)
    if not np.array_equal(original[:opening],stopped[:opening]):
        raise AssertionError("Untouched introduction changed")
    change=rms(original-stopped)
    if change<1e-5:
        raise AssertionError("Guitar stop was inaudibly identical in test fixture")
    begin=round(17.5*SR)
    count=round(12*SR)
    endings={"original_ringing":original[begin:begin+count],
             "selective_stopped_upstrokes":stopped[begin:begin+count]}
    if any(len(x)!=count for x in endings.values()):
        raise ValueError("Comparison section outside original score")
    target=rms(endings["original_ringing"])
    if target<1e-6:
        raise AssertionError("Original recorded guitar source failed to play")
    out=Path(out)
    out.mkdir(parents=True,exist_ok=True)
    output={}
    for name,source in endings.items():
        gain=1. if name=="original_ringing" else target/max(rms(source),1e-10)
        if not .25<gain<4.:
            raise AssertionError("Suspicious source loudness correction")
        clip=(source*gain).astype(np.float32)
        # These are matched listening excerpts, not final master automation.
        if not np.isfinite(clip).all() or np.max(np.abs(clip))>=.84:
            raise AssertionError("Clipping in stopped guitar excerpt")
        wav=out/f"Q42_Harbor_{name}.wav"
        mp3=out/f"Q42_Harbor_{name}.mp3"
        sf.write(wav,clip,SR,subtype="PCM_24")
        subprocess.run(["ffmpeg","-nostdin","-v","error","-y","-i",str(wav),
                        "-c:a","libmp3lame","-b:a","224k",str(mp3)],check=True)
        subprocess.run(["ffmpeg","-nostdin","-v","error","-xerror",
                        "-i",str(mp3),"-f","null","-"],check=True)
        wav.unlink()
        output[name]={"mp3":mp3.name,"excerpt_rms_dbfs":round(20*math.log10(rms(clip)),3),
                      "preview_only_gain":round(gain,6),
                      "peak_sample":round(float(np.max(np.abs(clip))),6)}
    err=abs(output["original_ringing"]["excerpt_rms_dbfs"]
            -output["selective_stopped_upstrokes"]["excerpt_rms_dbfs"])
    if err>.05:
        raise AssertionError("A/B sources not RMS matched")
    report={"instrument_source":"Original Meta Open Sound steel guitar, CC0-1.0",
            "arrangement":"Original Harbor, same Q2 physically distinct guitar string revoicing in both sources",
            "prior_source_string_voicing":voicings,
            "experimental_damping":stats,
            "original_intro_pcm_identical":True,
            "all_score_pitch_onset_velocity_length_identical":True,
            "non_guitar_parts_not_rendered":True,
            "single_note_voice_tail_damping_only":True,
            "full_duration_difference_rms":round(change,8),
            "excerpt_level_difference_db":round(err,3),
            "excerpt_start_s":17.5,"excerpt_duration_s":12.,
            "results":output,
            "limitation":"An existing recorded pluck stopped after 240ms, NOT a separately recorded palm-muted attack; listener preference untested."}
    (out/"Q42_stopped_guitar_comparison.json").write_text(json.dumps(report,indent=2))
    print(json.dumps(report,indent=2))
    return report


if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--assets",type=Path,required=True)
    p.add_argument("--out",type=Path,default=Path("q42-stopped-pluck"))
    a=p.parse_args()
    demo(a.assets,a.out)

"""Q4.2 actual licensed recorded-instrument Harbor mix stopped-guitar A/B.

Separately render *the same* original string-mapped score with and without
per-note acoustic damping. Verify every other source stem is byte-identical.
Only comparison excerpts are level matched; originals/releases unchanged.
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
from studio7.string_mapping import shape_harbor_bm_guitar
from studio7.guitar_damping_q42 import shape_harbor_stopped_upstrokes,SR


def rms(audio:np.ndarray)->float:
    return float(np.sqrt(np.mean(np.asarray(audio,dtype=np.float64)**2)))


def compare(assets:Path,out:Path)->dict:
    base,_=shape_harbor_bm_guitar(make("harbor"))
    stopped,selection=shape_harbor_stopped_upstrokes(base)
    if selection["tagged_notes"]!=24:
        raise AssertionError("Expected six isolated 4-string upstrokes")
    # This intentionally renders complete source backends twice to catch
    # unexpected score-tag bleed into bass, piano, electric, lead or drums.
    first=instrument_stems(base,assets=Path(assets),guitar_string_mapping=True)
    second=instrument_stems(stopped,assets=Path(assets),guitar_string_mapping=True)
    for part in first:
        if part!="acoustic" and not np.array_equal(first[part],second[part]):
            raise AssertionError(f"Unexpected raw {part} change")
    intro=round(8*SR)
    if not np.array_equal(first["acoustic"][:intro],second["acoustic"][:intro]):
        raise AssertionError("Recorded opening guitar attack/tails changed")
    source_delta=rms(first["acoustic"]-second["acoustic"])
    if source_delta<=1e-5:
        raise AssertionError("No audible-source difference after stopped string")
    a,processed_a,diag_a=process_stems(base,first,with_effects=True)
    b,processed_b,diag_b=process_stems(stopped,second,with_effects=True)
    for part in first:
        if part!="acoustic" and not np.array_equal(processed_a[part],processed_b[part]):
            raise AssertionError(f"Other processed {part} changed")
    if not np.isfinite(a).all() or not np.isfinite(b).all():
        raise AssertionError("Master mix has nonfinite audio")
    master_difference=rms(a-b)
    if master_difference<=1e-5:
        raise AssertionError("Stopped plucks made no change to full recorded mix")
    start=round(17.5*SR)
    length=round(12*SR)
    original=a[start:start+length]
    experimental=b[start:start+length]
    if len(original)!=length or len(experimental)!=length:
        raise ValueError("Preview exceeds original score")
    ratio=rms(original)/max(rms(experimental),1e-12)
    if not .5<=ratio<=2.0:
        raise AssertionError("Unexpectedly large comparison level correction")
    # Constrain the source level *equally* if either preview hits the ceiling.
    gain=min(1.,.82/max(float(np.max(abs(original))),
                            float(np.max(abs(experimental*ratio))),1e-12))
    pairs={"existing_ringing_guitar":original*gain,
           "stopped_upstrokes_only":experimental*ratio*gain}
    out=Path(out)
    out.mkdir(parents=True,exist_ok=True)
    previews={}
    for name,audio in pairs.items():
        pcm=np.asarray(audio,dtype=np.float32)
        peak=float(np.max(abs(pcm)))
        if peak>.8205 or not np.isfinite(pcm).all():
            raise AssertionError("Unsafe A/B preview level")
        wav=out/f"Q42_Harbor_fullmix_{name}.wav"
        mp3=out/f"Q42_Harbor_fullmix_{name}.mp3"
        sf.write(wav,pcm,SR,subtype="PCM_24")
        subprocess.run(["ffmpeg","-nostdin","-v","error","-y","-i",str(wav),
                        "-c:a","libmp3lame","-b:a","224k",str(mp3)],check=True)
        subprocess.run(["ffmpeg","-nostdin","-v","error","-xerror",
                        "-i",str(mp3),"-f","null","-"],check=True)
        wav.unlink()
        previews[name]={"file":mp3.name,"peak":round(peak,6),
                        "rms_dbfs":round(20*math.log10(max(rms(pcm),1e-12)),3)}
    difference=abs(previews["existing_ringing_guitar"]["rms_dbfs"]
                   -previews["stopped_upstrokes_only"]["rms_dbfs"])
    if difference>.05:
        raise AssertionError("Whole-song excerpt loudness mismatch")
    result={"style":"harbor","source":"Actual Meta Open Sound CC0 guitar/piano, FreePats CC0 bass/electric, MuldjordKit CC BY 4.0 drums",
            "guitar_upstroke_tags":selection,
            "only_guitar_raw_stem_changed":True,
            "only_guitar_processed_stem_changed":True,
            "original_intro_guitar_raw_pcm_identical":True,
            "source_guitar_difference_rms":round(source_delta,8),
            "full_mix_waveform_difference_rms":round(master_difference,8),
            "excerpt_level_difference_db":round(difference,3),
            "excerpt_shared_safety_gain":round(gain,5),
            "new_excerpt_relative_gain":round(ratio,5),
            "original_master_scale":diag_a["master_scale"],
            "stopped_master_scale":diag_b["master_scale"],
            "previews":previews,
            "limitation":"Sampled plucks with physically stopped sustain, not sampled palm-muted attacks; technical audio checks do not establish subjective preference."}
    (out/"Q42_stopped_guitar_fullmix_report.json").write_text(json.dumps(result,indent=2))
    print(json.dumps(result,indent=2))
    return result


if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--assets",type=Path,required=True)
    p.add_argument("--out",type=Path,default=Path("q42-fullmix"))
    args=p.parse_args()
    compare(args.assets,args.out)

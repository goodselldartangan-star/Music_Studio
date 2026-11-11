"""P3 identical-patch rhythm A/B: same drums and notes, only bass anchors move."""
from __future__ import annotations
import argparse,json,subprocess
from pathlib import Path
import numpy as np
import soundfile as sf
from studio7.score import make
from studio7.rhythm import shape_pocket
from tools.audit_rhythm_p3 import inspect_rhythm
from studio7.articulation import render_polyphonic
from studio7.render import _render_with_gm,DRUM_MAP
from studio6.soundfonts import SR


def run(gm:Path,out:Path)->dict:
    base=make("after")
    shaped,changes=shape_pocket(base)
    before_report=inspect_rhythm(base)
    after_report=inspect_rhythm(shaped)
    if not changes["bass_anchors_moved"] or not after_report["bass_anchor_offset_ms_median"]<before_report["bass_anchor_offset_ms_median"]:
        raise AssertionError("P3 pocket target was not reached")
    # Same source drum events, same velocities and pitches, two bass event timings.
    end_beat=32
    sec=end_beat*60/base["bpm"]+1.2
    hits=[{"beat":d["beat"],"length":.135,"pitch":DRUM_MAP[d["kind"]],"velocity":d["velocity"]}
          for d in base["drums"] if d["beat"]<end_beat]
    drums=_render_with_gm(gm,hits,sec,base["bpm"],"drums")
    audio={}
    for label,score in (("before",base),("after",shaped)):
        bass=[n for n in score["notes"] if n["instrument"]=="bass" and n["beat"]<end_beat]
        b=render_polyphonic(gm,bass,sec,base["bpm"],part="bass",program=33)
        audio[label]=drums*.70+b*.70
    scale=min(1.,.82/max(float(np.max(np.abs(y))) for y in audio.values()))
    output=Path(out);output.mkdir(parents=True,exist_ok=True)
    levels={}
    for key,value in audio.items():
        y=(value*scale).astype(np.float32)
        wav=output/f"P3_pocket_{key}.wav"
        mp3=output/f"P3_pocket_{key}.mp3"
        sf.write(wav,y,SR,subtype="PCM_24")
        subprocess.run(["ffmpeg","-nostdin","-hide_banner","-loglevel","error","-y",
                        "-i",str(wav),"-c:a","libmp3lame","-b:a","224k",str(mp3)],check=True)
        levels[key]={"rms_dbfs":round(20*np.log10(max(1e-10,float(np.sqrt(np.mean(y**2,dtype=np.float64))))),2),
                     "peak_dbfs":round(20*np.log10(max(1e-10,float(np.max(np.abs(y))))),2)}
    mse=float(np.mean((audio["before"]-audio["after"])**2,dtype=np.float64))
    if mse<1e-10:raise AssertionError("No audible-signal difference")
    report={"change":changes,"baseline":before_report,"candidate":after_report,"levels":levels,
            "waveform_mse":round(mse,8),
            "limitations":"Timing hypothesis only; pocket feel requires subjective confirmation before defaulting."}
    (output/"P3_pocket_report.json").write_text(json.dumps(report,indent=2))
    return report


if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--gm",type=Path,required=True)
    p.add_argument("--out",type=Path,default=Path("p3-pocket-preview"))
    a=p.parse_args()
    print(json.dumps(run(a.gm,a.out),indent=2))

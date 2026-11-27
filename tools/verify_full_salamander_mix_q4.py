"""Q4 non-production verification of original full Salamander piano.

Sum two independent sfizz voice program renders and exactly one pedal-only
sample instance. Report sample decoding, stereo, single-pedal routing and
peak headroom. Save a short derived MP3, never licensed original FLACs.
"""
from __future__ import annotations
import argparse
import json
import math
import subprocess
from pathlib import Path

import numpy as np
import soundfile as sf

SR=44100


def _decode(path:Path,expected:int)->np.ndarray:
    x,sr=sf.read(path,dtype="float32",always_2d=True)
    if sr!=SR or x.shape[1]!=2 or len(x)<expected-round(.4*SR):
        raise ValueError(f"Unexpected source format/length: {path}")
    if not np.isfinite(x).all():
        raise ValueError(f"Nonfinite sample in {path}")
    y=np.zeros((expected,2),np.float64)
    y[:min(expected,len(x))]=x[:min(expected,len(x))]
    return y


def _rms(a:np.ndarray)->float:
    return float(np.sqrt(np.mean(a*a,dtype=np.float64)))


def run(lanes:Path,*,out:Path,source_report:Path)->dict:
    lanes=Path(lanes)
    plan=json.loads((lanes/"Q4_lane_plan.json").read_text())
    route=json.loads((lanes/"Q4_pedal_route_plan.json").read_text())
    source=json.loads(Path(source_report).read_text())
    if source["blob_sha_verified_count"]!=641 or source["total_unique_original_flacs"]!=641:
        raise ValueError("Full official bank has not passed byte-for-byte verification")
    if (plan["lane_plan"]["input_notes"]!=64
            or len(plan["renders"])!=2
            or route["shared_mechanism_instances"]!=1
            or route["cc64_movement_count"]!=16):
        raise ValueError("Expected original Silver, 2 voice instances and one pedal mechanism")
    voice_program=(lanes/"voice_program"/"Q4_voice_only.sfz").read_text()
    if '#include "Data/pedal.txt"' in voice_program:
        raise ValueError("Note instrument still contains mechanical pedal regions")
    frames=round(plan["duration_s"]*SR)
    components={}
    for i in range(2):
        components[f"piano_{i}"]=_decode(
            lanes/f"with_pedal_lane_{i:02d}.wav",frames)
    components["shared_pedal"]=_decode(lanes/"shared_pedal.wav",frames)
    if min(_rms(components["piano_0"]),_rms(components["piano_1"]))<1e-7:
        raise AssertionError("One of the full original SFZ piano lanes is silent")
    if _rms(components["shared_pedal"])<1e-7:
        raise AssertionError("Full original pedal mechanism did not sound")
    sum_pcm=sum(components.values())
    peak=float(np.max(np.abs(sum_pcm)))
    if peak<=1e-7:
        raise AssertionError("No music produced by full source")
    # Never clip a verification file: retain the raw peak, apply a clearly
    # documented global gain to the derived listening-preview only.
    gain=min(1.0,.84/peak)
    preview=(sum_pcm*gain).astype(np.float32)
    out=Path(out)
    out.mkdir(parents=True,exist_ok=True)
    pcm=out/"Q4_Silver_full_original_Salamander_preview.wav"
    mp3=out/"Q4_Silver_full_original_Salamander_excerpt.mp3"
    sf.write(pcm,preview,SR,subtype="PCM_24")
    subprocess.run(["ffmpeg","-nostdin","-hide_banner","-v","error","-y",
                    "-i",str(pcm),"-t","12","-codec:a","libmp3lame",
                    "-b:a","224k",str(mp3)],check=True)
    subprocess.run(["ffmpeg","-v","error","-xerror",
                    "-i",str(mp3),"-f","null","-"],check=True)
    sample_peak=float(np.max(abs(preview)))
    if sample_peak>.8405:
        raise AssertionError("Derived MP3 preview PCM input has clipped")
    report={
        "source_revision":source["pinned_commit"],
        "source_original_flacs_verified":641,
        "source_bytes_verified":source["git_tree_total_bytes"],
        "source_license":source["license"],
        "score":"Silver original, 64 piano note events",
        "voice_instance_count":2,
        "physical_pedal_mechanism_instances":1,
        "cc64_pedal_movements":16,
        "sample_rate_hz":SR,
        "duration_seconds":round(frames/SR,3),
        "component_rms":{k:round(_rms(v),8) for k,v in components.items()},
        "unscaled_float_mix_peak":round(peak,6),
        "preview_gain":round(gain,6),
        "preview_pcm_peak":round(sample_peak,6),
        "preview_stereo_side_rms":round(_rms((preview[:,0]-preview[:,1])*.5),8),
        "original_music_files_changed":False,
        "limitations":"Experimental offline full bank; estimated CPU/RAM is measured separately, subjective sound quality not approved."
    }
    (out/"Q4_full_piano_audio_verification.json").write_text(json.dumps(report,indent=2))
    pcm.unlink()
    print(json.dumps(report,indent=2))
    return report


if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--lanes",type=Path,required=True)
    p.add_argument("--source-report",type=Path,required=True)
    p.add_argument("--out",type=Path,default=Path("q4-full-audio-preview"))
    a=p.parse_args()
    run(a.lanes,out=a.out,source_report=a.source_report)

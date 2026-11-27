"""Q4.3 experimental full original Fashionbass stem, isolated from defaults.

No replacements: derive deterministic MIDI lanes for the existing Harbor bass
notes; render each lane by its own external sfizz process, retaining
same-key release tails. Sum stereo PCM and generate a short technical excerpt.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import subprocess

import numpy as np
import soundfile as sf

from studio7.score import make
from studio7.effects import SR
from studio7.sfz_voice_lanes import assign_sfz_voice_lanes
from tools.render_sfz_lanes_q4 import _write_lane


def prepare(out:Path,*,style:str="harbor")->dict:
    if style not in ("harbor","after","silver"):
        raise ValueError("Only the three original songs may be tested")
    score=make(style)
    notes=[n for n in score["notes"] if n["instrument"]=="bass"]
    lanes,assignments=assign_sfz_voice_lanes(
        notes,score["bpm"],release_guard_s=.65,max_instances=8)
    out=Path(out)
    out.mkdir(parents=True,exist_ok=True)
    for i,lane in enumerate(lanes):
        _write_lane(out/f"bass_lane_{i:02d}.mid",lane,
                    score["bpm"],score["duration"])
    plan={
        "source_style":style,
        "original_score_bpm":score["bpm"],
        "original_score_duration_s":score["duration"],
        "notes_preserved":len(notes),
        "original_note_events_sha256":hashlib.sha256(
            json.dumps(notes,sort_keys=True).encode()).hexdigest(),
        "lane_plan":assignments,
        "render_files":[f"bass_lane_{i:02d}.wav" for i in range(len(lanes))],
        "publisher_license":"CC0 1.0 Karoryfer Fashionbass",
        "piano_guitar_drums_changed":False,
        "caveat":"Only bass stem, offline experiment. Voice process count and audio need verification."
    }
    (out/"Q43_Fashionbass_lane_plan.json").write_text(json.dumps(plan,indent=2))
    print(json.dumps(plan,indent=2))
    return plan


def mix(out:Path,*,preview_start_s:float=18.,preview_length_s:float=12.)->dict:
    root=Path(out)
    plan=json.loads((root/"Q43_Fashionbass_lane_plan.json").read_text())
    frames=round(plan["original_score_duration_s"]*SR)
    result=np.zeros((frames,2),dtype=np.float64)
    stem_stats=[]
    for fname in plan["render_files"]:
        path=root/fname
        y,sr=sf.read(path,dtype="float32",always_2d=True)
        if (sr!=SR or y.shape[1]!=2 or len(y)<frames-round(.2*SR)
                or not np.isfinite(y).all()):
            raise ValueError(f"Invalid full sampled bass lane: {fname}")
        if max(abs(y.min()),abs(y.max()))<=1e-6:
            raise AssertionError(f"Silent recorded bass lane: {fname}")
        end=min(frames,len(y))
        result[:end]+=y[:end]
        stem_stats.append({"lane":fname,
                           "rms":round(float(np.sqrt(np.mean(y*y))),8),
                           "original_frames":len(y)})
    peak=float(np.max(abs(result)))
    if not np.isfinite(peak) or peak<1e-6:
        raise AssertionError("Invalid original Fashionbass audio")
    output=root/"Q43_Fashionbass_full_stereo_bass.wav"
    sf.write(output,result.astype(np.float32),SR,subtype="PCM_24")
    st=round(preview_start_s*SR)
    ed=min(frames,st+round(preview_length_s*SR))
    if ed-st<round(8*SR):
        raise ValueError("Bass technical excerpt would be too short")
    audio=result[st:ed]
    # Do not permanently normalize source. Only the derived listening
    # excerpt gets conservative headroom and a clear numeric gain report.
    gain=min(1.,.82/max(float(np.max(abs(audio))),1e-10))
    excerpt=(audio*gain).astype(np.float32)
    wav=root/"Q43_Fashionbass_12s_excerpt.wav"
    mp3=root/"Q43_Fashionbass_12s_excerpt.mp3"
    sf.write(wav,excerpt,SR,subtype="PCM_24")
    subprocess.run(["ffmpeg","-nostdin","-hide_banner","-v","error","-y",
                    "-i",str(wav),"-c:a","libmp3lame","-b:a","224k",
                    str(mp3)],check=True)
    subprocess.run(["ffmpeg","-nostdin","-v","error","-xerror",
                    "-i",str(mp3),"-f","null","-"],check=True)
    wav.unlink()
    report={
        "score_style":plan["source_style"],
        "original_score_notes_preserved":plan["notes_preserved"],
        "full_stereo_source_duration_s":round(frames/SR,3),
        "independent_voice_instances":len(plan["render_files"]),
        "source_sample_rate_hz":SR,
        "source_mix_peak":round(peak,6),
        "source_mix_rms":round(float(np.sqrt(np.mean(result*result))),8),
        "stereo_side_rms":round(float(np.sqrt(np.mean(
            ((result[:,0]-result[:,1])*.5)**2))),8),
        "preview_only_gain":round(gain,6),
        "preview_pcm_peak":round(float(np.max(abs(excerpt))),6),
        "preview_mp3_file":mp3.name,
        "lane_stats":stem_stats,
        "original_other_stems_unchanged":True,
        "caveat":"Only bass stem and short technical MP3 tested; source bank does not claim slides. Main Music Studio renderer remains unchanged."
    }
    (root/"Q43_Fashionbass_full_audio_report.json").write_text(json.dumps(report,indent=2))
    print(json.dumps(report,indent=2))
    return report


if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("stage",choices=("prepare","mix"))
    p.add_argument("--out",type=Path,required=True)
    p.add_argument("--style",choices=("harbor","after","silver"),default="harbor")
    a=p.parse_args()
    if a.stage=="prepare":
        prepare(a.out,style=a.style)
    else:
        mix(a.out)

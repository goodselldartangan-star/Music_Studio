"""Q4 source-matched grand/upright piano test in the same unchanged mix.

Uses the already rendered original 641-sample Salamander grand piano and the
original CC0 Meta upright piano, with identical GM-fixture backing parts and
identical Music Studio mix processing. This is a technical comparison, not
a listening preference or a replacement piano.
"""
from __future__ import annotations
import argparse
import json
import math
import subprocess
from pathlib import Path

import numpy as np
import soundfile as sf

from studio7.score import make
from studio7.render import instrument_stems, _sample_meta, process_stems
from studio7.effects import SR
from tools.verify_full_salamander_mix_q4 import _decode


def rms(y:np.ndarray)->float:
    return float(np.sqrt(np.mean(np.asarray(y,dtype=np.float64)**2)))


def load_original_grand_lanes(folder:Path, *, frames:int)->np.ndarray:
    folder=Path(folder)
    plan=json.loads((folder/"Q4_lane_plan.json").read_text())
    route=json.loads((folder/"Q4_pedal_route_plan.json").read_text())
    if (plan["lane_plan"]["input_notes"]!=64
            or plan["lane_plan"]["instance_count"]!=2
            or route["shared_mechanism_instances"]!=1
            or route["cc64_movement_count"]!=16):
        raise ValueError("Expected exact original Silver lane/pedal configuration")
    components=[_decode(folder/f"with_pedal_lane_{i:02d}.wav",frames)
                for i in range(2)]
    components.append(_decode(folder/"shared_pedal.wav",frames))
    audio=sum(components).astype(np.float32)
    if not np.isfinite(audio).all() or rms(audio)<1e-7:
        raise AssertionError("Invalid or silent grand-piano source")
    return audio


def compare(*,meta_assets:Path, grand_lanes:Path,gm:Path,out:Path)->dict:
    score=make("silver")
    n=round(score["duration"]*SR)
    gm=Path(gm)
    if not gm.is_file():
        raise FileNotFoundError(gm)
    # Render identical fallback backing just once. Only the piano source
    # changes between A and B. The backline is an engineering fixture, not
    # the optional fully recorded electric/bass/kit reference arrangement.
    base=instrument_stems(score,gm=gm)
    upright=_sample_meta(score,"piano",Path(meta_assets))
    grand=load_original_grand_lanes(grand_lanes,frames=n)
    if upright.shape!=(n,2) or grand.shape!=(n,2):
        raise AssertionError("Piano stem clock/shape mismatch")
    before=rms(upright);after=rms(grand)
    if min(before,after)<1e-8:
        raise AssertionError("One real publisher piano source is silent")
    gain=before/after
    if not np.isfinite(gain) or not .05<gain<20:
        raise AssertionError("Suspicious dry-source level discrepancy")
    grand=(grand*gain).astype(np.float32)
    sources={"meta_upright":upright,"salamander_grand":grand}
    processed={}
    for name,piano in sources.items():
        raw={**base,"piano":piano}
        mixed,stems,diagnostics=process_stems(score,raw,with_effects=True)
        if not np.isfinite(mixed).all() or mixed.shape!=(n,2):
            raise AssertionError("Invalid full mix")
        processed[name]=(mixed,stems,diagnostics)
    before_piano=processed["meta_upright"][1]["piano"]
    after_piano=processed["salamander_grand"][1]["piano"]
    # Both dry samples are RMS matched and each receives the same role gain/EQ,
    # although different piano timbres may respond differently to that EQ.
    piano_level_diff=20*math.log10(max(rms(after_piano),1e-12)
                                  /max(rms(before_piano),1e-12))
    if abs(piano_level_diff)>1.:
        raise AssertionError("Piano parts no longer sufficiently level matched")
    for role in base:
        if role!="piano":
            if not np.array_equal(processed["meta_upright"][1][role],
                                  processed["salamander_grand"][1][role]):
                raise AssertionError("Non-piano role changed in the comparison")
    audio_delta=rms(processed["meta_upright"][0]
                    -processed["salamander_grand"][0])
    if audio_delta<1e-7:
        raise AssertionError("Piano replacement made no signal difference")
    out=Path(out)
    out.mkdir(parents=True,exist_ok=True)
    # Build section: actual piano, drums, bass and guitar all audible, but both
    # variants are from precisely the same authored Silver score and GM backline.
    start=round(19*SR)
    end=min(n,start+round(12*SR))
    outputs={}
    for name,(audio,_,diagnostics) in processed.items():
        clip=audio[start:end]
        peak=float(np.max(np.abs(clip)))
        if peak>.8401:
            raise AssertionError("Technical preview exceeds mix peak cap")
        wav=out/f"Q4_Silver_{name}_comparison.wav"
        mp3=out/f"Q4_Silver_{name}_comparison.mp3"
        sf.write(wav,clip,SR,subtype="PCM_24")
        subprocess.run(["ffmpeg","-nostdin","-v","error","-y",
                        "-i",str(wav),"-codec:a","libmp3lame","-b:a","224k",
                        str(mp3)],check=True)
        subprocess.run(["ffmpeg","-nostdin","-v","error","-xerror",
                        "-i",str(mp3),"-f","null","-"],check=True)
        wav.unlink()
        outputs[name]={"excerpt_peak":round(peak,6),
                       "excerpt_rms_dbfs":round(20*math.log10(max(rms(clip),1e-12)),3),
                       "master_scale":diagnostics["master_scale"],
                       "mp3_file":mp3.name}
    report={
        "style":"silver",
        "score_original_piano_notes":64,
        "comparison":"Original CC0 Meta upright vs CC BY 3.0 Salamander grand, same GM backing and Music Studio effects",
        "piano_dry_rms_match_gain":round(gain,5),
        "piano_processed_rms_difference_db":round(piano_level_diff,4),
        "full_mix_difference_rms":round(audio_delta,8),
        "original_nonpiano_parts_identical":True,
        "same_melody_and_timing":True,
        "excerpt_start_seconds":19.,
        "excerpt_duration_seconds":round((end-start)/SR,3),
        "results":outputs,
        "license_notice":"Salamander Grand Piano V3 by Alexander Holm, CC BY 3.0; reconstructed SFZ by kinwie, retuned by Markus Fiedler; Meta Open Sound upright CC0",
        "limitations":"The other parts use one fixed GM soundfont as a reproducible technical fixture; no listener preference or full real-instrument mix approved.",
    }
    (out/"Q4_piano_in_mix_comparison.json").write_text(json.dumps(report,indent=2))
    print(json.dumps(report,indent=2))
    return report


if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--meta-assets",required=True,type=Path)
    p.add_argument("--grand-lanes",required=True,type=Path)
    p.add_argument("--gm",required=True,type=Path)
    p.add_argument("--out",type=Path,default=Path("q4-inmix-preview"))
    a=p.parse_args()
    compare(meta_assets=a.meta_assets,grand_lanes=a.grand_lanes,gm=a.gm,out=a.out)

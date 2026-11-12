"""Q2 isolated actual-sample guitar A/B: source string mapping + playable Bm.

Both versions use the same licensed guitar sample collection, score tempo,
instrument mix/pan and source normalization. This is an engineering comparison,
not proof the new string voicing is preferred by a listener.
"""
from __future__ import annotations
import argparse,json,subprocess
from pathlib import Path
import numpy as np
import soundfile as sf

from studio7.score import make
from studio7.string_mapping import shape_harbor_bm_guitar
from studio7.render import _sample_meta
from studio6.soundfonts import SR


def run(assets:Path,out:Path,style:str="harbor")->dict:
    original=make(style)
    shaped,voicing=shape_harbor_bm_guitar(original)
    if style=="harbor" and voicing["chords_revoiced"]!=8:
        raise AssertionError("Harbor B-minor physical voicing not applied")
    # The exact same installed samples are used in both versions.
    old=_sample_meta(original,"acoustic",assets,string_aware=False)
    new=_sample_meta(shaped,"acoustic",assets,string_aware=True)
    if old.shape!=new.shape or not np.isfinite(old).all() or not np.isfinite(new).all():
        raise AssertionError("Q2 acoustic stems differ in dimensions or contain invalid samples")
    start_beat,end_beat=(8,24) if style=="harbor" else (48,64)
    t0=round(start_beat*60/original["bpm"]*SR)
    t1=round(end_beat*60/original["bpm"]*SR)
    clips={"before":old[t0:t1],"after":new[t0:t1]}
    if len(clips["before"])<4*SR:raise AssertionError("Not enough sample preview")
    target=float(np.sqrt(np.mean(clips["before"].astype(np.float64)**2)))
    root=Path(out);root.mkdir(parents=True,exist_ok=True)
    stats={}
    for key,wave in clips.items():
        rms=max(1e-12,float(np.sqrt(np.mean(wave.astype(np.float64)**2))))
        scale=min(1.2,max(.8,target/rms))
        peak=max(1e-12,float(np.max(np.abs(wave))))
        scale=min(scale,.85/peak)
        y=(wave*scale).astype(np.float32)
        wav=root/f"Q2_{style}_strings_{key}.wav"
        mp3=root/f"Q2_{style}_strings_{key}.mp3"
        sf.write(wav,y,SR,subtype="PCM_24")
        subprocess.run(["ffmpeg","-nostdin","-hide_banner","-v","error","-y",
                        "-i",str(wav),"-c:a","libmp3lame","-b:a","224k",str(mp3)],check=True)
        y_rms=max(1e-12,float(np.sqrt(np.mean(y.astype(np.float64)**2))))
        stats[key]={"rms_dbfs":round(20*np.log10(y_rms),2),
                    "peak_dbfs":round(20*np.log10(max(1e-12,float(np.max(np.abs(y))))),2),
                    "duration_s":round(len(y)/SR,3)}
    difference=float(np.sqrt(np.mean((clips["before"]-clips["after"])**2,dtype=np.float64)))
    if difference<1e-7:raise AssertionError("Different chord/string assignments produced identical audio")
    report={
        "style":style,
        "comparison":"Original recorded guitar vs optional independent physical string assignment",
        "guitar_voicing":voicing,
        "audio":stats,
        "source_difference_rms":round(difference,8),
        "limitations":"Not a professional guitar performance evaluation or musical preference verdict."
    }
    (root/f"Q2_{style}_strings_report.json").write_text(json.dumps(report,indent=2))
    return report


if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--assets",type=Path,required=True)
    p.add_argument("--out",type=Path,default=Path("q2-guitar-previews"))
    p.add_argument("--style",choices=("harbor","silver"),default="harbor")
    args=p.parse_args()
    print(json.dumps(run(args.assets,args.out,args.style),indent=2))

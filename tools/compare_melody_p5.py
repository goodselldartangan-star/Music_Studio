"""P5 same-lead-patch A/B of final four-bar phrase, only authored cadence differs."""
from __future__ import annotations
import argparse,json,subprocess
from pathlib import Path
import numpy as np
import soundfile as sf
from studio7.score import make
from studio7.melody import shape_final_answer,motif_report
from studio7.articulation import render_polyphonic
from studio6.soundfonts import SR


def run(gm:Path,out:Path,style:str='after')->dict:
    base=make(style);alternate,change=shape_final_answer(base)
    if not change['changed']:raise AssertionError('No final phrase variation')
    start,end=48,64
    seconds=(end-start)*60/base['bpm']+1.8
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    audio={}
    for label,score in [('before',base),('after',alternate)]:
        events=[dict(n,beat=n['beat']-start) for n in score['notes']
                if n['instrument'] in ('electric','lead') and start<=n['beat']<end]
        audio[label]=render_polyphonic(gm,events,seconds,score['bpm'],part='lead',program=26)
    peak=max(float(np.max(abs(v))) for v in audio.values())
    factor=min(1.,.84/max(peak,1e-9))
    report={}
    for label,wave in audio.items():
        wav=out/f'P5_melody_{label}.wav';mp3=out/f'P5_melody_{label}.mp3'
        y=(wave*factor).astype(np.float32)
        sf.write(wav,y,SR,subtype='PCM_24')
        subprocess.run(['ffmpeg','-nostdin','-hide_banner','-v','error','-y','-i',str(wav),
                        '-c:a','libmp3lame','-b:a','224k',str(mp3)],check=True)
        report[label]={'rms_dbfs':round(20*np.log10(max(1e-9,float(np.sqrt(np.mean(y*y))))),2),
                       'peak_dbfs':round(20*np.log10(max(1e-9,float(np.max(abs(y))))),2)}
    mse=float(np.mean((audio['before']-audio['after'])**2,dtype=np.float64))
    if mse<1e-10:raise AssertionError('No measurable change')
    result={'change':change,'level':report,'waveform_mse':round(mse,9),
            'unchanged_hook_count_before':motif_report(base)['same_pitch_onset_build_to_final'],
            'unchanged_hook_count_after':motif_report(alternate)['same_pitch_onset_build_to_final'],
            'limitations':'One authored cadence variant, not an aesthetic verdict or song quality score'}
    (out/'P5_melody_report.json').write_text(json.dumps(result,indent=2))
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--gm',type=Path,required=True)
    p.add_argument('--out',type=Path,default=Path('p5-melody-preview'))
    p.add_argument('--style',choices=['harbor','after','silver'],default='after')
    a=p.parse_args();print(json.dumps(run(a.gm,a.out,a.style),indent=2))

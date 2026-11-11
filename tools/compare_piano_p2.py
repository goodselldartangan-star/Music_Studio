"""P2 piano-touch A/B on the same GM sample patch and unchanged score notes."""
from __future__ import annotations
import argparse,json,subprocess
from pathlib import Path
import numpy as np
import soundfile as sf
from studio7.score import make
from studio7.piano_performance import shape_piano
from studio7.articulation import render_polyphonic
from studio6.soundfonts import SR


def run(gm:Path,output:Path)->dict:
    score=make('silver')
    revised,performance=shape_piano(score)
    if not performance['changed_notes'] or not performance['rolled_chord_groups']:
        raise AssertionError('Piano performance did not shape any notes')
    events={
        'before':[n for n in score['notes'] if n['instrument']=='piano' and n['beat']<16],
        'after':[n for n in revised['notes'] if n['instrument']=='piano' and n['beat']<16],
    }
    seconds=16*60/score['bpm']+2.
    x={label:render_polyphonic(gm,notes,seconds,score['bpm'],part='piano',program=0)
       for label,notes in events.items()}
    if not all(np.isfinite(arr).all() for arr in x.values()):
        raise AssertionError('Piano waveform invalid')
    out=Path(output);out.mkdir(parents=True,exist_ok=True)
    level=float(np.sqrt(np.mean(x['before']**2,dtype=np.float64)))
    report={}
    for name,data in x.items():
        rms=max(1e-10,float(np.sqrt(np.mean(data**2,dtype=np.float64))))
        scale=min(1.25,max(.8,level/rms))
        peak=max(1e-10,float(np.max(np.abs(data))))
        scale=min(scale,.85/peak)
        y=(data*scale).astype('float32')
        wav=out/f'P2_piano_{name}.wav'
        mp3=out/f'P2_piano_{name}.mp3'
        sf.write(wav,y,SR,subtype='PCM_24')
        subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-nostdin','-y',
                        '-i',str(wav),'-c:a','libmp3lame','-b:a','224k',str(mp3)],check=True)
        report[name]={'notes':len(events[name]),
                      'rms_dbfs':round(20*np.log10(max(1e-10,float(np.sqrt(np.mean(y**2,dtype=np.float64))))),2),
                      'peak_dbfs':round(20*np.log10(max(1e-10,float(np.max(abs(y))))),2)}
    mse=float(np.mean((x['before']-x['after'])**2,dtype=np.float64))
    if mse<1e-10:raise AssertionError('Piano performance A/B is identical')
    result={'test':'P2 piano touch and rolled chords',
            'score_change':performance,'audio':report,'waveform_mse':round(mse,9),
            'limitations':'Identical GM patch; only technical differences verified'}
    (out/'P2_piano_report.json').write_text(json.dumps(result,indent=2))
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--gm',type=Path,required=True)
    p.add_argument('--out',type=Path,default=Path('p2-piano-preview'))
    args=p.parse_args()
    print(json.dumps(run(args.gm,args.out),indent=2))

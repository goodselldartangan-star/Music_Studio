"""P3 drum hit-velocity A/B: same notes, MIDI timing and GM patch."""
from __future__ import annotations
import argparse,json,subprocess
from pathlib import Path
import numpy as np
import soundfile as sf
from studio7.score import make
from studio7.drum_dynamics import shape_drum_dynamics
from studio7.render import DRUM_MAP,_render_with_gm
from studio6.soundfonts import SR


def run(gm:Path,out:Path)->dict:
    score=make('after');shaped,changes=shape_drum_dynamics(score)
    stop=32
    seconds=stop*60/score['bpm']+1.2
    def events(s):
        return [dict(beat=d['beat'],pitch=DRUM_MAP[d['kind']],length=.135,velocity=d['velocity'])
                for d in s['drums'] if d['beat']<stop]
    if [(d['beat'],d['kind']) for d in score['drums']] != [(d['beat'],d['kind']) for d in shaped['drums']]:
        raise AssertionError('Drum pattern or timing changed')
    raw={name:_render_with_gm(gm,events(s),seconds,score['bpm'],'drums')
         for name,s in [('before',score),('after',shaped)]}
    target=float(np.sqrt(np.mean(raw['before']**2,dtype=np.float64)))
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    levels={}
    for name,x in raw.items():
        rms=float(np.sqrt(np.mean(x*x,dtype=np.float64)))
        scale=min(1.1,max(.9,target/max(1e-10,rms)))
        scale=min(scale,.85/max(1e-10,float(np.max(abs(x)))))
        y=(x*scale).astype('float32')
        wav=out/f'P3_drums_{name}.wav';mp3=out/f'P3_drums_{name}.mp3'
        sf.write(wav,y,SR,subtype='PCM_24')
        subprocess.run(['ffmpeg','-y','-v','error','-nostdin','-i',str(wav),'-c:a','libmp3lame','-b:a','224k',str(mp3)],check=True)
        levels[name]={'rms_dbfs':round(20*np.log10(max(1e-9,float(np.sqrt(np.mean(y*y,dtype=np.float64))))),2),
                      'peak_dbfs':round(20*np.log10(max(1e-9,float(np.max(abs(y))))),2)}
    mse=float(np.mean((raw['before']-raw['after'])**2,dtype=np.float64))
    if mse<1e-10:raise AssertionError('Drum performance is identical')
    report={'change':changes,'levels':levels,'waveform_mse':round(mse,9),
            'scope':'Drum hit velocity only, same patch, unchanged hit positions and sounds',
            'limitations':'Technical test, not groove preference'}
    (out/'P3_drums_report.json').write_text(json.dumps(report,indent=2))
    return report


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--gm',type=Path,required=True)
    p.add_argument('--out',type=Path,default=Path('p3-drum-preview'))
    a=p.parse_args();print(json.dumps(run(a.gm,a.out),indent=2))

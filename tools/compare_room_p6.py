"""P6 room test: identical dry piano, change only wet reflection pre-delay."""
from __future__ import annotations
import argparse,json,subprocess
from pathlib import Path
import numpy as np
import soundfile as sf
from studio7.effects import room_send,SR
from studio7.articulation import render_polyphonic


def run(gm:Path,out:Path)->dict:
    notes=[{'beat':.25,'length':1.1,'pitch':60,'velocity':84},
           {'beat':1.05,'length':.9,'pitch':64,'velocity':66},
           {'beat':2.,'length':1.3,'pitch':67,'velocity':91}]
    dry=render_polyphonic(gm,notes,5.0,120,part='piano',program=0)
    versions={}
    for name,pd in (('before',0.),('after',32.)):
        wet=room_send(dry,wet=.18,predelay_ms=pd)
        versions[name]=dry+wet
    delta=float(np.sqrt(np.mean((versions['before']-versions['after'])**2,dtype=np.float64)))
    if not np.isfinite(delta) or delta<1e-5:raise AssertionError('P6 pre-delay difference not measurable')
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    target=float(np.sqrt(np.mean(versions['before']**2,dtype=np.float64)))
    report={}
    for name,mix in versions.items():
        rms=max(1e-9,float(np.sqrt(np.mean(mix**2,dtype=np.float64))))
        factor=min(1.12,max(.88,target/rms))
        factor=min(factor,.82/max(1e-9,float(np.max(abs(mix)))))
        y=(mix*factor).astype(np.float32)
        wav=out/f'P6_room_{name}.wav';mp3=out/f'P6_room_{name}.mp3'
        sf.write(wav,y,SR,subtype='PCM_24')
        subprocess.run(['ffmpeg','-nostdin','-hide_banner','-v','error','-y','-i',str(wav),
                        '-c:a','libmp3lame','-b:a','224k',str(mp3)],check=True)
        report[name]={'rms_dbfs':round(20*np.log10(max(1e-9,float(np.sqrt(np.mean(y**2,dtype=np.float64))))),2),
                      'peak_dbfs':round(20*np.log10(max(1e-9,float(np.max(abs(y))))),2)}
    result={'comparison':'Identical dry GM piano; wet room pre-delay 0 vs 32 ms',
            'difference_rms':round(delta,7),
            'levels':report,'limitations':'Timing and signal integrity verified; spatial preference untested'}
    (out/'P6_room_report.json').write_text(json.dumps(result,indent=2))
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--gm',type=Path,required=True)
    p.add_argument('--out',type=Path,default=Path('p6-room-preview'))
    a=p.parse_args();print(json.dumps(run(a.gm,a.out),indent=2))

"""P4 matched 4-bar piano+lead A/B: only piano octave placement differs."""
from __future__ import annotations
import argparse,json,subprocess
from pathlib import Path
import numpy as np
import soundfile as sf
from studio7.score import make
from studio7.registers import audit_registers,separate_lead_piano
from studio7.articulation import render_polyphonic
from studio6.soundfonts import SR


def run(font:Path,folder:Path)->dict:
    original=make('silver');modified,report=separate_lead_piano(original)
    if not report['unisons_after']<report['unisons_before']:
        raise AssertionError('No improved foreground register separation')
    start,stop=16,32
    sec=(stop-start)*60/original['bpm']+1.5
    folder=Path(folder);folder.mkdir(parents=True,exist_ok=True)
    audio={}
    for version,score in [('before',original),('after',modified)]:
        stems=[]
        for part,program in [('piano',0),('electric',27)]:
            events=[dict(n,beat=n['beat']-start)
                    for n in score['notes'] if n['instrument']==part and start<=n['beat']<stop]
            stems.append(render_polyphonic(font,events,sec,score['bpm'],part=part,program=program))
        audio[version]=stems[0]*.7+stems[1]*.7
    peak=max(float(np.max(np.abs(a))) for a in audio.values())
    scale=min(1.,.84/max(peak,1e-9))
    results={}
    for name,raw in audio.items():
        y=(raw*scale).astype(np.float32)
        wav=folder/f'P4_register_{name}.wav';mp3=folder/f'P4_register_{name}.mp3'
        sf.write(wav,y,SR,subtype='PCM_24')
        subprocess.run(['ffmpeg','-nostdin','-hide_banner','-v','error','-y','-i',str(wav),
                        '-c:a','libmp3lame','-b:a','224k',str(mp3)],check=True)
        results[name]={'rms_dbfs':round(20*np.log10(max(1e-9,float(np.sqrt(np.mean(y*y))))),2),
                       'peak_dbfs':round(20*np.log10(max(1e-9,float(np.max(abs(y))))),2)}
    difference=float(np.mean((audio['before']-audio['after'])**2,dtype=np.float64))
    if difference<1e-10:raise AssertionError('Identical AB')
    output={'change':report,'audio':results,'waveform_mse':round(difference,9),
            'scope':'piano pitch octaves only; original melody and chord pitch classes retained',
            'limitations':'No measured preference or evidence of human-style listening quality'}
    (folder/'P4_register_report.json').write_text(json.dumps(output,indent=2))
    return output


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--gm',type=Path,required=True)
    p.add_argument('--out',type=Path,default=Path('p4-register-preview'))
    a=p.parse_args();print(json.dumps(run(a.gm,a.out),indent=2))

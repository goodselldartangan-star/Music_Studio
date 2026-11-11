"""P2 bass A/B on identical SoundFont: only note velocity/duration differs."""
from __future__ import annotations
import argparse,json,subprocess
from pathlib import Path
import numpy as np
import soundfile as sf
from studio7.score import make
from studio7.bass_performance import shape_bass
from studio7.articulation import render_polyphonic
from studio6.soundfonts import SR


def run(gm: Path, output: Path) -> dict:
    score=make('after')
    shaped,report=shape_bass(score)
    if report['changed_notes']<1:
        raise AssertionError('No bass expression change')
    sources={
        'before':[n for n in score['notes'] if n['instrument']=='bass' and n['beat']<16],
        'after':[n for n in shaped['notes'] if n['instrument']=='bass' and n['beat']<16]
    }
    seconds=16*60/score['bpm']+1.5
    raw={label:render_polyphonic(gm,notes,seconds,score['bpm'],part='bass',program=33)
         for label,notes in sources.items()}
    out=Path(output);out.mkdir(parents=True,exist_ok=True)
    target=float(np.sqrt(np.mean(raw['before']**2,dtype=np.float64)))
    report_audio={}
    for label,audio in raw.items():
        level=float(np.sqrt(np.mean(audio**2,dtype=np.float64)))
        scale=min(1.25,max(.8,target/max(1e-10,level)))
        peak=max(1e-10,float(np.max(np.abs(audio))))
        scale=min(scale,.85/peak)
        audio=(audio*scale).astype('float32')
        file=out/f'P2_bass_{label}.mp3'
        wav=out/f'P2_bass_{label}.wav'
        sf.write(wav,audio,SR,subtype='PCM_24')
        subprocess.run(['ffmpeg','-nostdin','-hide_banner','-loglevel','error','-y',
                        '-i',str(wav),'-c:a','libmp3lame','-b:a','224k',str(file)],check=True)
        report_audio[label]={'rms_dbfs':round(20*np.log10(max(1e-10,float(np.sqrt(np.mean(audio**2,dtype=np.float64))))),2),
                             'peak_dbfs':round(20*np.log10(max(1e-10,float(np.max(np.abs(audio))))),2),
                             'note_count':len(sources[label])}
    difference=float(np.mean((raw['before']-raw['after'])**2,dtype=np.float64))
    if difference<1e-10:raise AssertionError('Bass A/B failed to change audio')
    info={'test':'Bass articulation P2 (no other stems or effects changed)',
          'score_change':report,'audio':report_audio,
          'waveform_difference_mse':round(difference,9),
          'limitations':'GM test patch only; sound or playing preference unverified'}
    (out/'P2_bass_report.json').write_text(json.dumps(info,indent=2))
    return info


if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--gm',type=Path,required=True)
    p.add_argument('--out',type=Path,default=Path('p2-bass-preview'))
    a=p.parse_args()
    print(json.dumps(run(a.gm,a.out),indent=2))

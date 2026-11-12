"""P8 controlled 16-bar transition comparison with unchanged patches."""
from __future__ import annotations
import argparse,json,subprocess
from pathlib import Path
import numpy as np
import soundfile as sf
from studio7.score import make
from studio7.sections import shape_transition_breath
from studio7.render import instrument_stems
from studio7.effects import SR


def run(gm:Path,out:Path)->dict:
    score=make('after')
    alternate,change=shape_transition_breath(score)
    raws={}
    for name,s in (('before',score),('after',alternate)):
        stems=instrument_stems(s,gm=gm)
        raws[name]=(stems['bass']*.7+stems['drums']*.7).astype(np.float32)
    transition_at=47.35*60/score['bpm']
    start=round(transition_at*SR)
    before,after=raws['before'],raws['after']
    early_diff=float(np.sqrt(np.mean((before[:start]-after[:start])**2,dtype=np.float64)))
    tail_diff=float(np.sqrt(np.mean((before[start:]-after[start:])**2,dtype=np.float64)))
    if not np.isfinite(tail_diff) or tail_diff<1e-6:
        raise AssertionError('Arrangement edit produced no audible-signal difference')
    # No pre-transition score content was changed. Allow tiny synthesizer render
    # noise but reject any large perturbation before the intended break.
    if early_diff>max(.001,tail_diff*.3):
        raise AssertionError('Earlier groove was unexpectedly changed')
    target=max(float(np.max(abs(w))) for w in raws.values())
    gain=min(1.,.83/max(1e-9,target))
    output=Path(out);output.mkdir(parents=True,exist_ok=True)
    for name,w in raws.items():
        pcm=(w*gain).astype(np.float32)
        wav=output/f'P8_transition_{name}.wav'
        mp3=output/f'P8_transition_{name}.mp3'
        sf.write(wav,pcm,SR,subtype='PCM_24')
        subprocess.run(['ffmpeg','-nostdin','-hide_banner','-v','error','-y',
                        '-i',str(wav),'-c:a','libmp3lame','-b:a','224k',str(mp3)],check=True)
    report={'change':change,'early_difference_rms':round(early_diff,8),
            'transition_and_later_difference_rms':round(tail_diff,8),
            'limitations':'A structural rest is not necessarily preferable; only timing/silence mechanics are tested.'}
    (output/'P8_transition_report.json').write_text(json.dumps(report,indent=2))
    return report


if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--gm',type=Path,required=True)
    p.add_argument('--out',type=Path,default=Path('p8-transition-preview'))
    a=p.parse_args()
    print(json.dumps(run(a.gm,a.out),indent=2))

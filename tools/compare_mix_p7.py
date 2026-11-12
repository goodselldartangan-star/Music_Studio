"""P7 controlled full-arrangement technical mix comparison (same score + effects)."""
from __future__ import annotations
import argparse,json,subprocess
from pathlib import Path
import numpy as np
import soundfile as sf
from studio7.score import make
from studio7.render import instrument_stems,process_stems
from studio7.mix_translation import mix_translation_metrics
from studio7.effects import SR


def run(gm:Path,out:Path)->dict:
    score=make('after')
    raw=instrument_stems(score,gm=gm)
    mixed={}
    for name,precise in (('before',False),('after',True)):
        audio,_,_=process_stems(score,raw,with_effects=True,precise_low_mono=precise)
        if not np.isfinite(audio).all():raise AssertionError('Nonfinite mixed audio')
        mixed[name]=audio
    start,end=round(4*SR),round(20*SR)
    stats={key:mix_translation_metrics(wave[start:end]) for key,wave in mixed.items()}
    if stats['after']['low_side_fraction']>stats['before']['low_side_fraction']+.005:
        raise AssertionError('Precise mono worsened side energy below 150Hz')
    if stats['after']['estimated_true_peak_dbfs']>0:
        raise AssertionError('True peak would exceed digital full scale')
    root=Path(out);root.mkdir(parents=True,exist_ok=True)
    files={}
    for key,wave in mixed.items():
        wav=root/f'P7_mono_{key}.wav';mp3=root/f'P7_mono_{key}.mp3'
        sf.write(wav,wave,SR,subtype='PCM_24')
        subprocess.run(['ffmpeg','-nostdin','-hide_banner','-v','error','-y','-i',str(wav),
                        '-c:a','libmp3lame','-b:a','256k',str(mp3)],check=True)
        files[key]=str(mp3)
    change=float(np.sqrt(np.mean((mixed['after']-mixed['before'])**2,dtype=np.float64)))
    if change<1e-7:raise AssertionError('No measurable mix change')
    report={'comparison':'Identical score, samples, mixing and FX: legacy vs optional low-side filter',
            'first_16_seconds_after_intro':stats,'difference_rms':round(change,8),
            'files':files,
            'limitations':'Side leakage and true-peak technical checks; no mixing preference inferred.'}
    (root/'P7_mono_report.json').write_text(json.dumps(report,indent=2))
    return report


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--gm',type=Path,required=True)
    p.add_argument('--out',type=Path,default=Path('p7-mix-preview'))
    a=p.parse_args();print(json.dumps(run(a.gm,a.out),indent=2))

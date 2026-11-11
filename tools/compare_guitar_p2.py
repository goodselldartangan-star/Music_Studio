"""P2 short A/B: identical guitar timbre and notes; only strum performance differs.

This is an engineering comparison, not a preference test or finished song.
"""
from __future__ import annotations
import argparse,json,subprocess
from pathlib import Path
import numpy as np
import soundfile as sf
from studio7.score import make
from studio7.playing import shape_strums
from studio7.articulation import render_polyphonic
from studio6.soundfonts import SR


def run(font: Path,out: Path)->dict:
    score=make('harbor')
    changed,per=shape_strums(score)
    if not per['strum_groups']:raise AssertionError('No strums shaped')
    seconds=16*60/score['bpm']+1.2
    original=[n for n in score['notes'] if n['instrument']=='acoustic' and n['beat']<16]
    modified=[n for n in changed['notes'] if n['instrument']=='acoustic' and n['beat']<16]
    assert len(original)==len(modified)
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    arrays=[];reports={}
    for label,notes in [('before',original),('after',modified)]:
        y=render_polyphonic(font,notes,seconds,score['bpm'],part='acoustic',program=25)
        if not np.isfinite(y).all():raise AssertionError('Invalid recording samples')
        arrays.append(y)
    target_rms=np.sqrt(np.mean(arrays[0]**2,dtype=np.float64))
    for label,y in zip(('before','after'),arrays):
        rms=np.sqrt(np.mean(y*y,dtype=np.float64))
        y=y * min(1.15,max(.85,target_rms/max(rms,1e-9)))
        y=y * min(1.,.83/max(float(np.max(np.abs(y))),1e-6))
        wav=out/f'P2_guitar_{label}.wav';mp3=out/f'P2_guitar_{label}.mp3'
        sf.write(wav,y,SR,subtype='PCM_24')
        subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-nostdin','-y',
                        '-i',str(wav),'-codec:a','libmp3lame','-b:a','224k',str(mp3)],check=True)
        reports[label]={'rms_dbfs':round(20*np.log10(np.sqrt(np.mean(y*y))+1e-12),2),
                        'peak_dbfs':round(20*np.log10(max(float(np.max(abs(y))),1e-12)),2),
                        'notes':len(notes),'duration_s':round(len(y)/SR,2)}
    delta=np.mean((arrays[0]-arrays[1])**2,dtype=np.float64)
    if delta<=1e-9:raise AssertionError('No measurable change in performance audio')
    report={'test':'P2 isolated guitar strumming','performance':per,'versions':reports,
            'waveform_mse':round(float(delta),8),
            'limitations':'Same GM guitar patch, notes and instrument mixer; no human listening claim.'}
    (out/'P2_guitar_report.json').write_text(json.dumps(report,indent=2))
    return report


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--gm',type=Path,required=True)
    p.add_argument('--out',type=Path,default=Path('p2_guitar_preview'))
    a=p.parse_args();print(json.dumps(run(a.gm,a.out),indent=2))

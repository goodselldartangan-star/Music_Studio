"""Q4 opt-in piano CC64-style note-off deferral: same source and score notes.

The comparison measures note-off/PCM behavior; it does not simulate sampled
pedal noise, sympathetic resonance or approve a musical preference.
"""
from __future__ import annotations
import argparse
import json
import math
import subprocess
from pathlib import Path

import numpy as np
import soundfile as sf

from studio7.score import make
from studio7.pedal_timing import shape_silver_pedal_timing
from studio7.articulation import render_polyphonic
from studio7.effects import SR


def _rms(a):
    return float(np.sqrt(np.mean(a.astype(np.float64)**2)))


def run(gm:Path|None,out:Path,*,assets:Path|None=None)->dict:
    if (gm is None)==(assets is None):
        raise ValueError('Select exactly one piano test backend')
    base=make('silver')
    candidate,performance=shape_silver_pedal_timing(base)
    if not performance['piano_notes_held_past_key_release']:
        raise AssertionError('No notes extended by the authored pedal windows')
    seconds=base['duration']
    audio={}
    for name,score in (('before',base),('after',candidate)):
        notes=[n for n in score['notes'] if n['instrument']=='piano']
        if assets is None:
            audio[name]=render_polyphonic(gm,notes,seconds,base['bpm'],part='piano',program=0)
        else:
            from studio7.render import _sample_meta
            audio[name]=_sample_meta(score,'piano',assets)
        if not np.isfinite(audio[name]).all():
            raise AssertionError('Invalid piano waveform')
    onset=round(32*60/base['bpm']*SR)
    earlier=_rms(audio['before'][:onset]-audio['after'][:onset])
    full_change=_rms(audio['before']-audio['after'])
    if earlier>1e-6 or full_change<1e-6:
        raise AssertionError('Pedal timing affected intro or created no later waveform difference')
    duration=12
    start=round((32*60/base['bpm']-.4)*SR)
    stop=min(len(audio['before']),start+round(duration*SR))
    old=audio['before'][start:stop]
    new=audio['after'][start:stop]
    reference=_rms(old)
    out=Path(out)
    out.mkdir(parents=True,exist_ok=True)
    stats={}
    for label,y in (('before',old),('after',new)):
        gain=min(1.12,max(.88,reference/max(_rms(y),1e-12)))
        gain=min(gain,.83/max(float(np.max(abs(y))),1e-12))
        leveled=(y*gain).astype('float32')
        wav=out/f'Q4_pedal_{label}.wav'
        mp3=out/f'Q4_pedal_{label}.mp3'
        sf.write(wav,leveled,SR,subtype='PCM_24')
        subprocess.run(['ffmpeg','-nostdin','-hide_banner','-loglevel','error','-y',
                        '-i',str(wav),'-c:a','libmp3lame','-b:a','224k',str(mp3)],check=True)
        wav.unlink()
        stats[label]={'rms_dbfs':round(20*math.log10(max(_rms(leveled),1e-12)),2),
                      'peak_dbfs':round(20*math.log10(max(float(np.max(abs(leveled))),1e-12)),2)}
    matched=stats['after']['rms_dbfs']-stats['before']['rms_dbfs']
    if abs(matched)>.6:
        raise AssertionError('Preview is not loudness matched')
    report={'experiment':'Q4 limited CC64-style note-off deferral, no physical pedal resonance',
            'backend':'publisher Meta Piano OGG' if assets is not None else 'GM SoundFont fixture',
            'piano_performance':performance,
            'initial_audio_difference_rms':round(earlier,9),
            'entire_audio_difference_rms':round(full_change,8),
            'level_matched_piano_excerpt':stats,
            'excerpt_rms_difference_db':round(matched,2),
            'limitations':'Only note-off timing; true damper, sympathetic resonance and pedal mechanisms remain unmodeled.'}
    (out/'Q4_pedal_timing_report.json').write_text(json.dumps(report,indent=2))
    print(json.dumps(report,indent=2))
    return report


if __name__=='__main__':
    p=argparse.ArgumentParser()
    back=p.add_mutually_exclusive_group(required=True)
    back.add_argument('--gm',type=Path)
    back.add_argument('--piano-assets',type=Path)
    p.add_argument('--out',type=Path,default=Path('q4-pedal-preview'))
    args=p.parse_args()
    run(args.gm,args.out,assets=args.piano_assets)

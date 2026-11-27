"""Q4 offline experiment: one sfizz_render *instance* per safe MIDI lane.

Prepare MIDI lanes with no overlapping same-pitch voices on any one sampler.
Each lane must then be rendered by an independent sfizz_render process. The
mix stage sums only rendered WAVs, never steals, cuts or normalizes notes.
Do NOT enable this experiment as the Studio's default piano backend.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path

import mido
import numpy as np
import soundfile as sf

from studio7.sfz_voice_lanes import assign_sfz_voice_lanes

SR=44100
TICKS_PER_SECOND=960  # MIDI 480 ticks/beat at 120 bpm


def _write_lane(path:Path,notes:list[dict],bpm:float,duration_s:float)->None:
    midi=mido.MidiFile(ticks_per_beat=480)
    track=mido.MidiTrack()
    midi.tracks.append(track)
    track.append(mido.MetaMessage('set_tempo',tempo=500000,time=0))
    events=[]
    for n in notes:
        at=n['beat']*60/bpm
        off=(n['beat']+n['length'])*60/bpm
        events.extend([(round(at*TICKS_PER_SECOND),1,int(n['pitch']),int(n['velocity'])),
                       (round(off*TICKS_PER_SECOND),0,int(n['pitch']),0)])
    # A key outside acoustic piano range forces sfizz_render to keep recording
    # release tails, even when it would otherwise stop at the last note-off.
    events.extend([(round((duration_s-.2)*TICKS_PER_SECOND),1,1,1),
                   (round((duration_s-.05)*TICKS_PER_SECOND),0,1,0)])
    events.sort(key=lambda x:(x[0],x[1]))
    prev=0
    for tick,on,pitch,velocity in events:
        if tick<prev or tick<0 or tick>=round(duration_s*TICKS_PER_SECOND):
            raise ValueError('Out-of-bounds SFZ lane event')
        track.append(mido.Message('note_on' if on else 'note_off',
                     note=pitch,velocity=velocity,time=tick-prev,channel=0))
        prev=tick
    track.append(mido.MetaMessage('end_of_track',
                 time=round(duration_s*TICKS_PER_SECOND)-prev))
    midi.save(path)


def prepare(out:Path,notes:list[dict],bpm:float,duration_s:float,
            *,release_guard_s:float=.5,max_instances:int=8)->dict:
    out=Path(out)
    if not 1<=duration_s<=200 or not np.isfinite(duration_s):
        raise ValueError('Invalid render duration')
    if any(n.get('instrument')!='piano' for n in notes):
        raise ValueError('This Q4 sampler experiment accepts piano notes only')
    if any((n['beat']+n['length'])*60/bpm>=duration_s-.25 for n in notes):
        raise ValueError('Score notes must leave room for their release tails')
    lanes,report=assign_sfz_voice_lanes(
        notes,bpm,release_guard_s=release_guard_s,max_instances=max_instances)
    out.mkdir(parents=True,exist_ok=True)
    for i,lane in enumerate(lanes):
        _write_lane(out/f'lane_{i:02d}.mid',lane,bpm,duration_s)
    manifest={'bpm':bpm,'duration_s':duration_s,
              'lane_plan':report,
              'renders':[{'midi':f'lane_{i:02d}.mid',
                          'wav':f'lane_{i:02d}.wav'} for i in range(len(lanes))],
              'source_notes_sha256':hashlib.sha256(
                  json.dumps(notes,sort_keys=True).encode()).hexdigest(),
              'scope':'Q4 standalone test of isolated sfizz processes, NOT Music Studio default'}
    (out/'Q4_lane_plan.json').write_text(json.dumps(manifest,indent=2))
    return manifest


def combine(out:Path)->dict:
    out=Path(out)
    m=json.loads((out/'Q4_lane_plan.json').read_text())
    frames=round(m['duration_s']*SR)
    mixed=np.zeros((frames,2),np.float64)
    for entry in m['renders']:
        path=out/entry['wav']
        x,sample_rate=sf.read(path,dtype='float32',always_2d=True)
        if (sample_rate!=SR or x.shape[1]!=2 or len(x)<frames-round(.2*SR)
                or not np.isfinite(x).all()):
            raise ValueError(f'Bad or truncated SFZ lane: {path.name}')
        count=min(frames,len(x))
        mixed[:count]+=x[:count]
    peak=float(np.max(np.abs(mixed)))
    if peak>=.999:
        raise ValueError('Unmixed sfizz lanes exceed PCM full-scale; no silent normalization')
    path=out/'Q4_isolated_lane_mix.wav'
    sf.write(path,mixed.astype(np.float32),SR,subtype='PCM_24')
    report={'rendered_instances':len(m['renders']),
            'input_notes':m['lane_plan']['input_notes'],
            'peak_sample':round(peak,6),
            'releases_not_stolen_by_shared_midi_noteoff':True,
            'audio_path':path.name,
            'limitation':'Independent process render test only; no actual full Salamander production integration.'}
    (out/'Q4_lane_audio_report.json').write_text(json.dumps(report,indent=2))
    return report


FIXTURE=[{'instrument':'piano','pitch':60,'beat':.4,'length':4.4,'velocity':80},
         {'instrument':'piano','pitch':60,'beat':1.8,'length':.5,'velocity':110}]


if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('command',choices=('prepare','mix'))
    p.add_argument('--out',type=Path,default=Path('q4-sfizz-probe/lanes'))
    p.add_argument('--score',type=Path)
    args=p.parse_args()
    if args.command=='prepare':
        if args.score:
            score=json.loads(args.score.read_text())
            notes=[n for n in score['notes'] if n['instrument']=='piano']
            result=prepare(args.out,notes,score['bpm'],score['duration'])
        else:
            result=prepare(args.out,FIXTURE,120.,4.)
    else:
        result=combine(args.out)
    print(json.dumps(result,indent=2))

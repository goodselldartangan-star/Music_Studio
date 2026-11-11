"""P1: inspect downloaded recorded-instrument maps without rendering a new song.

Run after tools/install_cc0.py and tools/install_optional_v7.py. Deliberately
checks pitches/layers, not subjective sound quality or audio mixing.
"""
from __future__ import annotations
import argparse
import json
import math
from collections import Counter
from pathlib import Path
import soundfile as sf
from studio3.sample_bank import SampleBank, SOURCE_FOR_PART
from studio3.spec import Note
from studio7.samples import Collection
from studio7.score import SONGS, make


def audit_assets(root: Path) -> dict:
    bank=SampleBank(root)
    nylon=Collection(root,'meta-nylon-guitar')
    sources={}
    for part,source in SOURCE_FOR_PART.items():
        regions=bank.regions[source]
        if not regions:raise AssertionError(f'No samples for {part}')
        sources[part]={'recordings':len(regions),'min_midi':min(r.midi for r in regions),
                       'max_midi':max(r.midi for r in regions),
                       'layers':sorted({r.layer for r in regions})}
    sources['nylon']={'recordings':len(nylon.regions),'min_midi':min(r[1] for r in nylon.regions),
                      'max_midi':max(r[1] for r in nylon.regions),
                      'layers':sorted({r[2] for r in nylon.regions})}
    # Probe soft/medium/strong recording layers on the same exact pitch.
    velocity_probes={}
    for name,records in {
        'pluck':[(r.path,r.midi,r.layer) for r in bank.regions[SOURCE_FOR_PART['pluck']]],
        'keys':[(r.path,r.midi,r.layer) for r in bank.regions[SOURCE_FOR_PART['keys']]],
        'nylon':nylon.regions,
    }.items():
        maxlayer=max(r[2] for r in records)
        pitches=sorted({r[1] for r in records})
        full=[p for p in pitches if len({r[2] for r in records if r[1]==p})>=3]
        if not full:raise AssertionError(f'{name}: no pitch has soft/medium/hard samples')
        target=full[len(full)//2]
        selected=[]
        for velocity in (24,70,115):
            goal=math.ceil(velocity/127*maxlayer)
            choice=min(records,key=lambda r:(abs(r[1]-target),abs(r[2]-goal),str(r[0])))
            info=sf.info(choice[0])
            if choice[1]!=target or info.frames < .1*info.samplerate:
                raise AssertionError(f'{name}: invalid recorded velocity probe at MIDI {target}')
            selected.append(choice[2])
        if len(set(selected))!=3:
            raise AssertionError(f'{name}: soft/medium/hard did not select different recordings')
        velocity_probes[name]={'midi_pitch':target,'layers_at_velocity_24_70_115':selected}
    used={}
    for style in SONGS:
        score=make(style)
        deltas=[];layers=Counter();sampled=0
        for n in score['notes']:
            part=n['instrument']
            if part not in ('acoustic','piano'):continue
            if part=='acoustic' and style=='silver':
                # Independent nylon-guitar collection. Check its *actual* pitch+layer map.
                maxlayer=max(v[2] for v in nylon.regions)
                goal=math.ceil(n['velocity']/127*maxlayer)
                nearest=min(nylon.regions,key=lambda r:(abs(r[1]-n['pitch']),abs(r[2]-goal)))
                original=nearest[1];layer=nearest[2]
            else:
                voice=Note('pluck' if part=='acoustic' else 'keys',n['beat'],n['length'],
                           n['pitch'],n['velocity']/127,0)
                region=bank._select(voice,seed=123)
                original=region.midi;layer=region.layer
            change=abs(n['pitch']-original)
            if change>4:raise AssertionError(f'{style}/{part}: excessive sample pitch shift {change}')
            deltas.append(change);layers[f'{part}:{layer}']+=1;sampled+=1
        used[style]={'sampled_notes':sampled,'exact_pitch_hits':deltas.count(0),
                     'max_transpose_semitones':max(deltas,default=0),
                     'sample_layer_usage':dict(sorted(layers.items()))}
        if not sampled:raise AssertionError(f'No recorded notes in {style}')
    return {'sources':sources,'velocity_probes':velocity_probes,'scores':used,
            'limitations':'Mapping and provenance checks, not an acoustic realism or listener preference score.'}


def main():
    p=argparse.ArgumentParser();p.add_argument('--assets',type=Path,required=True)
    p.add_argument('--out',type=Path,default=Path('sample_coverage_p1.json'))
    a=p.parse_args();report=audit_assets(a.assets)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(report,indent=2,sort_keys=True))
    print(json.dumps(report,indent=2))


if __name__=='__main__':main()

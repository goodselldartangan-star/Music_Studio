"""Compact, instrument-agnostic musical score. All timing in quarter-note beats."""
from dataclasses import dataclass, asdict
import math, random

@dataclass(frozen=True)
class Note:
    instrument: str
    pitch: int
    beat: float
    length: float
    velocity: int

@dataclass(frozen=True)
class Hit:
    kind: str
    beat: float
    velocity: int

STYLES = {
 'porch': {'title': 'Porch Radio', 'bpm': 106, 'bars': 12,
           'chords': [(55,59,62,67),(52,55,59,64),(48,52,55,59),(50,54,57,62)],
           'bass_roots':[31,28,36,38], 'key':'G major / E minor'},
 'city': {'title': 'Street Corner', 'bpm': 122, 'bars': 12,
          'chords':[(57,60,64,69),(53,57,60,65),(48,52,55,60),(55,59,62,67)],
          'bass_roots':[33,29,36,31], 'key':'A minor'},
 'night': {'title': 'Last Window', 'bpm': 98, 'bars': 12,
           'chords':[(50,53,57,62),(46,50,53,58),(53,57,60,65),(48,52,55,60)],
           'bass_roots':[38,34,29,36], 'key':'D minor / F major'},
}

def make(name: str) -> dict:
    """Three distinct, authored arrangements; never re-times one source score."""
    if name not in STYLES: raise ValueError(f'Unknown demo: {name}')
    style=STYLES[name]; rng=random.Random({'porch':202,'city':307,'night':419}[name]);
    notes=[]; drums=[]; bars=style['bars']
    def add(inst,pitch,beat,length,velocity):
        if 0<=beat<bars*4:
            assert 20<=pitch<=100 and length>0
            notes.append(asdict(Note(inst,pitch,round(beat,4),round(length,4),int(velocity))))
    def hit(kind,beat,v):
        if 0<=beat<bars*4:drums.append(asdict(Hit(kind,round(beat,4),int(v))))
    for b in range(bars):
        pos=b*4; phase=b%4; chord=style['chords'][phase]; root=style['bass_roots'][phase];
        chorus=b>=8
        if name=='porch':
            # Finger-strummed guitar: staggered chord strokes and a quieter answer, not a sequencer arpeggio.
            for beat,scale in ((.10,1),(2.11,.78)):
                for i,p in enumerate(chord):
                    add('acoustic',p,pos+beat+i*.045+rng.uniform(-.006,.006),1.35,round((74 if chorus else 66)*scale-i*2))
            if b%2==1:
                for i,p in enumerate((chord[1],chord[2],chord[3])):
                    add('acoustic',p+12,pos+3.00+i*.20,.38,45+i*4)
            for i,(off,dur) in enumerate(((0,1.25),(2.03,.78),(3.50,.36))):
                add('bass',root+(12 if i==2 else 0),pos+off,dur,82 if i==0 else 68)
            if b in (3,7,11):
                add('piano',chord[1]+12,pos+3.0,.93,52)
            if b>=2:
                for k in (0,2):hit('kick',pos+k,78 if k==0 else 64)
                hit('snare',pos+1.025,65);hit('snare',pos+3.025,73)
                for j in range(8):hit('hat',pos+j*.5+(j%2)*.026,36+(j%2)*14)
            hook={0:[(0.48,.76,74),(1.50,.87,71),(2.85,.92,69)],1:[(.21,.62,71),(1.21,1.10,74),(3.04,.7,76)],2:[(.50,.72,74),(1.48,.65,71),(2.64,1.14,67)],3:[(.24,.59,69),(1.0,.72,71),(2.25,1.46,67)]}[phase]
            if b>=4:
                for off,dur,p in hook: add('electric',p-12,pos+off,dur,76 if chorus else 64)
        elif name=='city':
            # Punchy and intentional: electric chord backbeats, syncopated bass; a lead guitar hook with held notes.
            for offset in (.52,1.54,2.54,3.48):
                for i,p in enumerate(chord[1:]):
                    add('electric',p+12 if i==2 else p,pos+offset+i*.020,.28 if not chorus else .39,72 if chorus else 59)
            if b%2==0:
                for i,p in enumerate(chord[1:3]):add('piano',p+12,pos+2.05+i*.023,.64,47)
            basspat=[(0,.76,0,89),(.99,.42,0,65),(1.75,.47,12,71),(2.52,.70,0,88),(3.48,.38,0,68)]
            for off,dur,octave,vel in basspat:add('bass',root+octave,pos+off,dur,vel)
            for off,vel in ((0,93),(1.73,68),(2.48,74),(3.55,62)):
                hit('kick',pos+off,vel)
            for off in (1,3):hit('snare',pos+off+.01,92 if chorus else 79)
            for j in range(8):hit('hat',pos+j*.5+(j%2)*.035,44+(16 if j%2 else 0))
            if b%4==3:hit('open_hat',pos+3.48,58)
            hook={0:[(.1,.65,81),(1.0,.54,79),(1.88,.64,76),(2.96,.92,74)],1:[(.22,.75,76),(1.47,.56,79),(2.29,1.37,81)],2:[(.14,.72,79),(1.10,.63,76),(2.23,1.22,72)],3:[(.13,.61,74),(1.0,.61,76),(2.12,1.54,69)]}[phase]
            for off,dur,p in hook:
                add('electric',p,pos+off,dur,83 if chorus else 74)
        else:
            # Piano and silence first; guitar phrases are an answer, not simultaneous notes everywhere.
            for offset,mel in ((.02,(chord[0]+12,chord[1]+12)),(2.17,(chord[2]+12,chord[3]+12))):
                for i,p in enumerate(mel):add('piano',p,pos+offset+i*.048,2.45 if offset<1 else 1.42,59+i*2+(7 if chorus else 0))
            if b>=2:
                add('bass',root,pos+.04,1.62,74)
                add('bass',root+7,pos+2.74,.69,51)
            if b>=4:
                hit('kick',pos+.02,75);hit('snare',pos+2.04,64)
                for j in range(4):hit('hat',pos+j+.47,39+(7 if j%2 else 0))
            if b>=8:
                hit('kick',pos+2.72,50);hit('open_hat',pos+3.5,47)
            for i,(off,length,pitch) in enumerate({0:[(.42,1.3,69),(2.63,1.08,65)],1:[(.27,.81,67),(1.53,1.68,65)],2:[(.38,.96,69),(1.74,1.74,72)],3:[(.28,.63,67),(1.12,2.0,65)]}[phase]):
                if b>=2: add('acoustic',pitch,pos+off,length,64+(5 if chorus else 0))
    return {'title':style['title'],'style':name,'bpm':style['bpm'],'bars':bars,'key':style['key'],
            'seconds':bars*4*60/style['bpm']+2.0,'notes':notes,'drums':drums,
            'credits':'Recorded acoustic guitar/piano: Meta Open Sound (CC0); electric guitar/bass: FreePats (CC0); acoustic drums: MuldjordKit / DrumGizmo.org (CC BY 4.0).'}

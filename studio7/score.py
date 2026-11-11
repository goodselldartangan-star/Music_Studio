"""Original 16-bar sketches; note roles remain independent of SF2, DSP and effects.

A chord tone in an upper voice is not a free pass to play more notes. We intentionally
leave answers and rests around the lead, and place bass entrances after kick attacks.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
import random

@dataclass(frozen=True)
class Note:
    instrument: str
    pitch: int
    beat: float
    length: float
    velocity: int

@dataclass(frozen=True)
class Drum:
    kind: str
    beat: float
    velocity: int

# Every chord includes only actual pitch classes, and each instrument has its own register.
SONGS = {
 'harbor': dict(title='The Harbor Light',tempo=108,key='D major',theme='organic',
                roots=(38,33,35,31),harmonies=('D','A','Bm','G'),
                voicings=((50,54,57,62),(49,52,57,61),(47,50,54,59),(43,47,50,55))),
 'after': dict(title='After the Signal',tempo=122,key='E minor',theme='punch',
               roots=(40,36,31,38),harmonies=('Em','C','G','D'),
               voicings=((52,55,59,64),(48,52,55,60),(43,47,50,55),(50,54,57,62))),
 'silver': dict(title='Silver Rain',tempo=102,key='D minor',theme='dream',
                roots=(38,34,41,36),harmonies=('Dm','Bb','F','C'),
                voicings=((50,53,57,62),(46,50,53,58),(53,57,60,65),(48,52,55,60))),
}

# 4-bar phrases. Longer anchor notes and explicit rests are not accidental omissions.
LEADS={
 'harbor': [((.35,.86,69),(1.65,.52,71),(2.71,1.02,74)),
            ((.22,.55,73),(1.15,.92,71),(2.75,.92,69)),
            ((.53,.89,71),(2.02,1.44,74)),
            ((.32,.64,69),(1.34,.55,67),(2.26,1.24,66))],
 'after': [((.20,.56,71),(1.13,.62,74),(2.37,1.24,76)),
           ((.39,.66,76),(1.42,.47,74),(2.58,.87,72)),
           ((.18,.67,74),(1.34,.88,79),(2.77,.78,76)),
           ((.34,.55,74),(1.42,1.40,71))],
 'silver': [((.56,.90,69),(2.17,1.41,65)),
            ((.28,.70,67),(1.40,1.67,65)),
            ((.52,1.14,72),(2.29,1.22,69)),
            ((.33,.82,67),(1.70,1.79,64))]
}
# Some pitches above are melodic non-chord tones (passing / suspensions), checked as key tones.
SCALE={
 'harbor':{1,2,4,6,7,9,11},
 'after':{0,2,4,6,7,9,11},
 'silver':{0,2,4,5,7,9,10},
}

def make(style: str)->dict:
    if style not in SONGS: raise ValueError(f'Unknown style: {style}')
    cfg=SONGS[style];rng=random.Random({'harbor':811,'after':209,'silver':310}[style]);
    notes=[];drums=[];bars=16
    def add(part,pitch,at,length,velocity):
        if not 0<=at<bars*4 or not 0.045<=length<=7:raise ValueError('invalid note placement')
        if not 21<=pitch<=100 or not 1<=velocity<=127:raise ValueError('note range/velocity')
        notes.append(asdict(Note(part,pitch,round(at,4),round(length,3),round(velocity))))
    def hit(kind,at,velocity):
        if not 0<=at<bars*4:raise ValueError('hit outside score')
        drums.append(asdict(Drum(kind,round(at,4),round(velocity))))
    for b in range(bars):
        p=b%4; at=b*4; chord=cfg['voicings'][p]; root=cfg['roots'][p]
        intro=b<4; expansion=b>=8; chorus=b>=12
        # General rule: intro = one anchor, verse = groove + restrained melody,
        # build = thinner instrument instead of louder everything, chorus = hook + bass and drums.
        if style=='harbor':
            # Guitar main rhythm at the low/mid register; downstroke and upstroke are genuinely staggered.
            for offset,speed,velocity,decay in ((.08,.037,71,1.11),(2.17,-.029,59,.70)):
                selected=chord if speed>0 else tuple(reversed(chord))
                for j,pitch in enumerate(selected):
                    add('acoustic',pitch,at+offset+abs(speed)*j,decay if j<2 else decay*.9,
                        velocity-int(j*2)+rng.randint(-3,3)+(6 if chorus else 0))
            # Piano is a non-overlapping answer / fill, only where the guitar has left air.
            if p in (1,3) and b>=4:add('piano',chord[2]+12,at+3.15,.57,50+(8 if chorus else 0))
            if not intro:
                for off,du,oct,vel in ((.11,1.10,0,82),(2.29,.57,0,70),(3.58,.35,12,56)):
                    add('bass',root+(7 if oct and root+7<=45 else 0),at+off,du,vel)
                for off,v in ((0,91),(2.0,68)):hit('kick',at+off,v)
                for off in (1,3):hit('snare',at+off+.018,77)
                for j in range(8):hit('hat',at+.5*j+.024*(j%2),43+15*(j%2))
            else:
                if b>=2: hit('hat',at+1.49,40);hit('hat',at+3.49,43)
            if b>=4:
                for off,dur,pitch in LEADS[style][p]:
                    # Guitar lead only on stronger phrases, less accompaniment in verses.
                    if b in (4,5,6,7) and off>2.5: continue
                    add('electric',pitch,at+off,dur,72+(8 if chorus else 0))
        elif style=='after':
            # This guitar is a rhythmic accent, not a continuous sustained pad.
            if not intro or b>=2:
                for off in (.53,2.50):
                    for j,pitch in enumerate(((64,67,71),(60,64,67),(62,67,71),(62,66,69))[p]):
                        add('electric',pitch,at+off+.024*j,.32,64+(9 if chorus else 0)-2*j)
            # Piano does not play through every guitar strike, only spare offbeats.
            if p in (0,2) or intro:
                add('piano',chord[2]+12,at+.11,.67 if intro else .35,46 if intro else 42)
            for off,du,oct,v in ((.13,.7,0,81),(1.65,.37,0,65),(2.30,.66,0,75),(3.52,.31,12,55)):
                if intro and off>2.4:continue
                add('bass',root+(0 if oct and root+7>45 else (7 if oct else 0)),at+off,du,v if not intro else int(v*.67))
            if not intro:
                for off,v in ((0,92),(1.77,59),(2.51,80)):hit('kick',at+off,v)
                for off in (1,3):hit('snare',at+off+.013,80+(9 if chorus else 0))
                for j in range(8):hit('hat',at+j*.5+.030*(j%2),40+15*(j%2))
                if p==3:hit('open_hat',at+3.5,52)
            else:
                hit('kick',at,.52*100)
                for j in (1,3,5,7):hit('hat',at+j*.5,38)
            if b>=4:
                # Lead hook uses a different instrument role than rhythm guitar in the final recording.
                for off,dur,pitch in LEADS[style][p]:
                    if b<8 and p==2 and off>2.5:continue
                    add('lead',pitch,at+off,dur,73+(8 if chorus else 0))
        else:
            # Piano-forward atmospheric arrangement, guitar only responds to gaps.
            for off,du,inv in ((.08,2.50,0),(2.72,1.11,1)):
                tones=(chord[1]+12,chord[2]+12) if inv==0 else (chord[2]+12,chord[3]+12)
                for j,tone in enumerate(tones):add('piano',tone,at+off+j*.041,du,60+(9 if chorus else 0)-2*j)
            if b>=4:
                add('bass',root,at+.16,1.55,73)
                add('bass',root+(7 if root+7<=45 else 0),at+2.76,.75,49)
            if b>=8:
                hit('kick',at,69 if not chorus else 85)
                hit('snare',at+2.025,68 if not chorus else 78)
                for j in range(4):hit('hat',at+j+.49,38+6*(j%2))
            if b>=4:
                for off,dur,pitch in LEADS[style][p]:
                    add('electric',pitch,at+off,dur,67+(10 if chorus else 0))
            if chorus:
                for j,pitch in enumerate((chord[1],chord[2],chord[3])):
                    add('acoustic',pitch,at+3.15+.04*j,.52,57+3*j)
                hit('open_hat',at+3.50,41)
    # Returning hook is developed, not replaced. Last four bars have new articulation.
    for n in notes:
        if n['instrument'] in ('electric','lead') and n['beat']>=48:
            n['velocity']=min(114,n['velocity']+4)
            if n['beat']%4<1.1:n['length']=round(n['length']*1.12,3)
    return {'title':cfg['title'],'style':style,'key':cfg['key'],'bpm':cfg['tempo'],
            'bars':bars,'duration':bars*4*60/cfg['tempo']+3.,'chords':cfg['harmonies']*4,
            'notes':notes,'drums':drums,'provenance':'Original GPT-authored composition; no other generative AI.'}


def validate(score:dict)->dict:
    """Proof obligations that are readable without audio or an ML model."""
    style=score['style'];allowed=SCALE[style]
    lead=[n for n in score['notes'] if n['instrument'] in ('lead','electric') and n['length']>.5]
    offkey=[n for n in lead if n['pitch']%12 not in allowed]
    if offkey: raise ValueError(f'Lead pitches outside key: {offkey[:5]}')
    for n in score['notes']:
        if n['beat']<0 or n['beat']>=score['bars']*4 or n['length']<=0:raise ValueError('note invalid')
    # Bass must be pitched no higher than the guitar and must avoid piling attacks onto kick.
    bass=[n for n in score['notes'] if n['instrument']=='bass']
    if bass and max(n['pitch'] for n in bass)>45:raise ValueError('bass above recorded FingerBassYR source range')
    return {'validated':True,'lead_count':len(lead),'bass_count':len(bass),'drum_hits':len(score['drums'])}

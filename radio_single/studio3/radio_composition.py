"""Original, self-contained pop instrumental songbook.

The songbook controls ALL musical decisions. It emits the same portable JSON
score schema consumed by the v3 MIDI and instrument layers. No AI/API needed.
"""
from dataclasses import asdict
import numpy as np
from .spec import Note, Drum, safe_note, SR, TAIL_SECONDS

TITLE='Headlights on the Water'
STEM='Headlights_on_the_Water'
BPM=118
BARS=96
SECTIONS=[
  (0,4,'intro'),(4,16,'verse_a'),(16,24,'pre_a'),(24,36,'chorus_a'),
  (36,40,'post'),(40,52,'verse_b'),(52,60,'pre_b'),(60,72,'chorus_b'),
  (72,80,'bridge'),(80,92,'final_chorus'),(92,96,'outro')]

# Pitch classes agree with the chord labels and notes. F# natural minor/A major.
CHORDS={
 'F#m7': ((54,57,61,64),30),
 'Dmaj9': ((50,54,57,61,64),38),
 'Aadd9': ((57,61,64,71),33),
 'E6/9': ((52,56,59,61,66),40),
 'Bm7': ((59,62,66,69),35),
 'C#m7': ((49,52,56,59),37),
}
KEY_PCS={1,2,4,6,8,9,11}
PROGRESSIONS={
 'intro': ['Aadd9','E6/9','F#m7','Dmaj9'],
 'verse_a':['F#m7','Dmaj9','Aadd9','E6/9'],
 'pre_a':['Bm7','Dmaj9','E6/9','E6/9'],
 'chorus_a':['Aadd9','E6/9','F#m7','Dmaj9'],
 'post':['Aadd9','E6/9','F#m7','Dmaj9'],
 'verse_b':['F#m7','Dmaj9','Aadd9','E6/9'],
 'pre_b':['Bm7','Dmaj9','E6/9','E6/9'],
 'chorus_b':['Aadd9','E6/9','F#m7','Dmaj9'],
 'bridge':['Dmaj9','E6/9','C#m7','F#m7','Dmaj9','E6/9','Bm7','E6/9'],
 'final_chorus':['Aadd9','E6/9','F#m7','Dmaj9'],
 'outro':['F#m7','Dmaj9','E6/9','Aadd9'],
}
# The chorus carries a vocal-shaped, intentionally memorable 8-bar hook.
# Fields: position in bar (beats), duration (beats), MIDI note pitch.
HOOK=[
 [(0.13,.51,76),(.92,.47,78),(1.70,.97,81),(3.08,.52,80)],
 [(0.18,.79,80),(1.35,.48,78),(2.14,1.24,76)],
 [(0.13,.54,73),(1.04,.55,76),(1.88,.72,78),(3.03,.57,81)],
 [(0.12,.93,81),(1.44,.52,78),(2.24,1.26,76)],
 [(0.12,.49,76),(.85,.51,78),(1.76,1.04,81),(3.15,.58,83)],
 [(0.18,.72,80),(1.29,.53,78),(2.18,1.14,76)],
 [(0.16,.58,73),(1.16,.54,76),(2.06,.59,78),(3.15,.50,76)],
 [(0.17,.59,78),(.98,.49,76),(1.86,1.59,74)],
]
VERSE=[
 [(0.43,.56,69),(1.54,.55,73),(2.61,.71,71)],
 [(0.26,.79,69),(1.56,.51,71),(2.63,.80,73)],
 [(0.46,.50,73),(1.36,.69,76),(2.62,.72,73)],
 [(0.38,.71,71),(1.62,.45,69),(2.63,.68,68)],
]
PRE=[
 [(0.35,.62,71),(1.38,.48,73),(2.24,.60,74),(3.12,.52,76)],
 [(0.22,.54,73),(1.23,.53,76),(2.28,.56,78),(3.19,.48,81)],
 [(0.22,.54,76),(1.31,.53,78),(2.34,.58,80),(3.31,.40,81)],
 [(0.22,.49,80),(1.08,.53,78),(2.04,.48,76),(2.98,.79,83)],
]

def section_at(bar):
    return next((x for x in SECTIONS if x[0]<=bar<x[1]),None)

def scale_shift(pitch,steps):
    if not steps:return pitch
    choices=[n for n in range(60,91) if n%12 in KEY_PCS]
    k=min(range(len(choices)),key=lambda i:abs(choices[i]-pitch))
    return choices[max(0,min(len(choices)-1,k+steps))]

def compose(bpm=BPM, seed=113026, bars=None):
    """Compose a completely original, deterministic 96-bar instrumental radio form."""
    if not 98<=bpm<=135:raise ValueError('tempo outside 98–135 BPM')
    if bars is not None and not 1<=bars<=BARS:raise ValueError('invalid preview length')
    bars=bars or BARS
    rng=np.random.default_rng(seed)
    notes=[]; drums=[]; chords=[]
    def add(part,beat,dur,pitch,vel,pan=0):
        if 0<=beat<bars*4:
            notes.append(asdict(safe_note(part,beat,dur,pitch,vel,pan)))
    def hit(kind,beat,vel,pan=0):
        if 0<=beat<bars*4:
            drums.append(asdict(Drum(kind,round(beat,5),round(vel,4),round(pan,3))))
    for bar in range(bars):
        s,e,name=section_at(bar);local=bar-s;pos=bar*4
        chorus='chorus' in name
        pre='pre_' in name
        quiet=name in ('intro','bridge','outro')
        chord=PROGRESSIONS[name][local%len(PROGRESSIONS[name])]
        chords.append({'bar':bar,'chord':chord})
        tones,root=CHORDS[chord]
        # Pads are supporting context, not a full stack of dominant chords.
        pad_vel=.12 if name in ('intro','bridge','outro') else .13 if not chorus else .18
        for j,pitch in enumerate(tones):
            if j==0 and name!='bridge':continue
            add('pad',pos+.03,3.68,pitch+ (12 if j==0 and name=='bridge' else 0),pad_vel*(1-.055*j),-.44 if j%2 else .44)
        # Organic keyboard stabs, humanized by section-specific accents.
        if chorus:
            key_pattern=[(.10,.59,.37),(1.52,.43,.27),(2.54,.54,.35)]
        elif pre:
            key_pattern=[(.09,.78,.32),(2.01,.72,.28)]
        elif quiet:
            key_pattern=[(.10,1.18,.29),(2.56,.85,.24)]
        else:
            key_pattern=[(.12,.81,.28),(1.72,.42,.20),(2.71,.82,.29)]
        for k,(offset,dur,vel) in enumerate(key_pattern):
            t1=tones[(k+1)%len(tones)]
            t2=tones[(k+3)%len(tones)]
            add('keys',pos+offset,dur,t1+(12 if name=='intro' and k==0 else 0),vel,-.31)
            add('keys',pos+offset+.025,dur*.96,t2,vel*.64,.32)
        # Bouncy guitar-like plucks on the offbeats, varied on the fourth bar.
        if name=='intro':guitar=[(.09,.39,.67),(.77,.34,.40),(1.56,.51,.67),(2.73,.38,.48)]
        elif quiet:guitar=[(.12,.52,.47),(1.59,.45,.35),(2.88,.41,.39)]
        elif chorus or name=='post':guitar=[(.08,.31,.76),(.76,.31,.46),(1.48,.43,.71),(2.48,.39,.76),(3.35,.36,.53)]
        else:guitar=[(.08,.32,.67),(.83,.26,.41),(1.60,.37,.63),(2.57,.35,.67),(3.42,.25,.41)]
        for i,(off,dur,vel) in enumerate(guitar):
            posj=max(.03,off+float(np.clip(rng.normal(0,.011),-.024,.024)))
            amp=vel*float(rng.uniform(.95,1.05))
            p=tones[(i*2+1)%len(tones)]+(12 if (i==4 and chorus) else 0)
            add('pluck',pos+posj,dur,p,amp, -.45 if i%2 else .43)
            if chorus and i in (0,2):
                add('pluck',pos+posj+.028,dur*.80,p-12,amp*.24,.39 if i%2 else -.39)
        # Bass connects with the kick, leaving spaces before chord changes.
        if name=='intro':bp=[(0,1.0,.43)] if local>=2 else []
        elif name=='bridge':bp=[(0,1.53,.54),(2.45,.73,.33)]
        elif name=='outro':bp=[(0,1.36,.45),(2.08,1.1,.33)] if local<3 else [(0,2.3,.40)]
        elif chorus:bp=[(0,.72,.87),(.88,.38,.51),(1.54,.52,.66),(2.19,.62,.83),(3.41,.37,.63)]
        elif pre:bp=[(0,.85,.62),(1.52,.50,.45),(2.05,.69,.67),(3.58,.31,.48)]
        else:bp=[(0,.84,.72),(1.53,.37,.42),(2.08,.77,.68),(3.48,.40,.49)]
        for i,(off,dur,amp) in enumerate(bp):
            octave=12 if i==1 and not quiet else 0
            add('bass',pos+off,dur,root+octave,amp)
        # Arpeggiator varies density in response to song form.
        if name=='bridge':steps=[0,2,4]
        elif name in ('intro','outro'):steps=[0,3,6]
        elif chorus:steps=[0,2,3,5,6,7]
        elif pre:steps=list(range(8))
        else:steps=[0,1,3,4,6,7]
        for step in steps:
            p=tones[[2,3,1,4 if len(tones)>4 else 0][(step+local)%4]]+12
            add('arp',pos+.065+.5*step,.26,p,.22 if chorus else .18 if quiet else .20,(-.56 if step%2 else .56))
        # Deliberate melody / vocal phrasing.
        if name in ('verse_a','verse_b'):
            for j,(off,dur,pitch) in enumerate(VERSE[local%4]):
                pitch+=0
                if name=='verse_b':
                    # New melodic reply rather than copying verse A.
                    if local%4 in (1,3) and j==2:pitch=scale_shift(pitch,2 if local<6 else -1)
                    if local in (3,7) and j==0:continue # breath
                    if local>=8 and j==1:pitch=scale_shift(pitch,1)
                    off+= .07 if j==2 else 0
                if name=='verse_a' and local<4 and j==2 and local%2==1:continue
                add('lead',pos+off,dur,pitch,.43 if name=='verse_a' else .53,.11)
        elif pre:
            for j,(off,dur,pitch) in enumerate(PRE[local%4]):
                if name=='pre_b' and j==3 and local%4 in (1,3):pitch=scale_shift(pitch,1)
                add('lead',pos+off,dur,pitch,(.50+.13*local/8) if name=='pre_a' else (.58+.13*local/8),.10)
        elif chorus:
            for j,(off,dur,pitch) in enumerate(HOOK[local%8]):
                if name=='chorus_b' and local%8 in (3,5,6) and j==len(HOOK[local%8])-1:
                    pitch=scale_shift(pitch,1 if local%8==5 else -1)
                    off+=.06
                if name=='final_chorus':
                    if local%8 in (2,3,5,6) and j==len(HOOK[local%8])-1:
                        pitch=scale_shift(pitch,1 if local%8 in (2,5) else -1)
                    if local>=8 and j==1:dur*=1.20
                add('lead',pos+off,dur,pitch,.72 if name=='chorus_a' else .75 if name=='chorus_b' else .80,.07)
                if name=='final_chorus' and j==0 and local%4 in (1,3):
                    add('counter',pos+off+.20,dur*.82,pitch-12,.25,-.36)
        elif name=='intro':
            # Tease the hook immediately; no meandering atmospheric prelude.
            for j,(off,dur,pitch) in enumerate(HOOK[local%8][:2]):
                add('bell',pos+off,dur*1.0,pitch,.22 if local<2 else .29,.16)
        elif name=='post':
            for j,(off,dur,pitch) in enumerate(HOOK[(local+4)%8][:3]):
                add('bell',pos+off,dur*.9,pitch,.34,.24)
        elif name=='bridge':
            base=[[(.4,.91,73),(2.3,.67,71)],[(.4,.9,69),(2.5,.82,68)],[(.3,1.16,73),(2.6,.70,76)],[(.2,1.1,78),(2.6,.71,76)]][local%4]
            for off,dur,pitch in base:add('lead',pos+off,dur,pitch,.45 if local<4 else .56,.17)
        elif name=='outro':
            for off,dur,pitch in HOOK[(local+4)%8][:2]:
                add('bell',pos+off,dur*1.3,pitch,.20,.13)
        # Drums: balanced indie-pop snare and crisp electronic hats.
        if name=='intro':
            for i in range(4):hit('shaker',pos+i+.5,.12 if i%2 else .16,-.18 if i%2 else .18)
            if local>=2:hit('kick',pos,.39)
            if local>=3:hit('rim',pos+2,.22)
            continue
        if name=='outro':
            hit('kick',pos,.56 if local<2 else .36)
            if local<2:hit('rim',pos+2,.24)
            for i in (1,3):hit('shaker',pos+i+.5,.14,.19)
            continue
        if name=='bridge':
            hit('kick',pos,.57 if local>=4 else .45)
            hit('snare',pos+2.012,.40)
            for step in range(4):hit('hat',pos+step+.52,.13 if step%2 else .18,-.3 if step%2 else .3)
            if local>=4:hit('shaker',pos+3.65,.16)
        else:
            if chorus or name=='post':
                kicks=[(0,1.00),(1,.64),(2,.85),(2.75,.60),(3.51,.65)]
            elif pre:kicks=[(0,.91),(1.52,.51),(2,.76),(3.53,.61)]
            else:kicks=[(0,.95),(1.55,.50),(2.03,.83),(3.52,.55)]
            for off,amp in kicks:hit('kick',pos+off,amp*(.80 if chorus else .68))
            for back in (1,3):
                hit('snare',pos+back+.014,.85 if chorus else .68)
                if chorus:hit('clap',pos+back+.029,.21)
                elif local%4:hit('ghost',pos+back-.22,.14)
            for step in range(8):
                timing=float(np.clip(rng.normal(0,.005),-.011,.011))
                swing=.04 if step%2 else 0
                hvel=(.31 if step%2 else .21)*float(rng.uniform(.94,1.08))
                hit('hat',pos+max(.01,step*.5+swing+timing),hvel,-.3 if step%2 else .3)
            if chorus:
                for i in (3,7):hit('open_hat',pos+i*.5+.036,.20,.39)
            if pre and local>=4:
                for i in (1,3,5,7):hit('shaker',pos+i*.5,.17,-.19)
        if local%4==3 and name not in ('bridge','outro'):
            for k in range(4):hit('tom',pos+3.03+k*.225,.22+.049*k,-.25+.14*k)
    # Drum transition accents (new sections only).
    for s,e,name in SECTIONS[1:]:
        if s>=bars:continue
        if name in ('chorus_a','chorus_b','final_chorus'):
            hit('impact',s*4,.61)
        else:hit('impact',s*4,.31)
    notes.sort(key=lambda x:(x['beat'],x['part'],x['pitch']))
    drums.sort(key=lambda x:(x['beat'],x['kind']))
    return {'title':TITLE,'stem':STEM,'bpm':bpm,'seed':seed,'sample_rate':SR,
            'bars':bars,'duration_seconds':bars*4*60/bpm+TAIL_SECONDS,
            'sections':[{'start':s,'end':min(e,bars),'name':n} for s,e,n in SECTIONS if s<bars],
            'chords':chords,'notes':notes,'drums':drums,
            'composition':{'key':'F# minor / A major','meter':'4/4','style':'rhythmic indie/electronic radio-pop instrumental','hook_bars':8},
            'mix':{'stereo_width':2.80}}

"""Readable songbook: all original melodic material and arrangement decisions."""
from dataclasses import asdict
import numpy as np
from .spec import Settings, Note, Drum, SECTIONS, BARS, SR, STEM, TITLE, TAIL_SECONDS, section_for, safe_note

# Voicings selected to keep the inner voices moving smoothly.
CHORDS = {
    'Bm9': ((59,62,66,69,73),35), 'Gmaj7': ((55,59,62,66,69),31),
    'Dadd9': ((57,62,64,66,69),38), 'A6sus': ((57,61,64,66,71),33),
    'Em9': ((52,59,62,66,67),40), 'F#7sus': ((54,59,61,64,70),30),
}
PROGRESSIONS = {
    'intro': ('Bm9','Gmaj7','Dadd9','A6sus'),
    'verse_a': ('Bm9','Gmaj7','Dadd9','A6sus'),
    'rise': ('Em9','Gmaj7','A6sus','F#7sus'),
    'chorus_a': ('Gmaj7','Dadd9','A6sus','Bm9'),
    'instrumental': ('Bm9','Em9','Gmaj7','A6sus'),
    'verse_b': ('Bm9','Gmaj7','Dadd9','A6sus'),
    'bridge': ('Em9','Bm9','Gmaj7','F#7sus'),
    'chorus_b': ('Gmaj7','Dadd9','A6sus','Bm9'),
    'outro': ('Em9','Gmaj7','F#7sus','Bm9'),
}
# A memorable, singable instrumental chorus; phrasing leaves space for breath.
HOOK = [
    [(0.18,.47,74),(.90,.47,78),(1.72,.69,81),(2.92,.84,83)],
    [(.16,.77,81),(1.45,.50,78),(2.26,.68,76),(3.32,.48,74)],
    [(.17,.49,73),(.93,.55,76),(1.90,.62,78),(3.03,.77,81)],
    [(.16,.73,78),(1.45,.47,74),(2.25,1.17,71)],
    [(.14,.44,74),(.83,.50,78),(1.71,.84,81),(2.97,.77,85)],
    [(.16,.68,83),(1.26,.44,81),(2.12,.64,78),(3.16,.56,76)],
    [(.16,.58,73),(1.09,.48,76),(1.97,.74,78),(3.13,.57,81)],
    [(.16,.70,78),(1.30,.52,74),(2.29,1.26,71)],
]
VERSE = [
    [(0.52,.54,66),(1.45,.55,69),(2.50,.78,71)],
    [(0.27,.83,74),(1.61,.48,71),(2.36,.83,69)],
    [(0.39,.42,66),(1.18,.59,69),(2.31,.68,74),(3.37,.31,76)],
    [(0.26,.67,73),(1.50,.54,69),(2.42,.82,66)],
]
RISE = [
    [(.36,.55,67),(1.31,.51,71),(2.28,.56,74),(3.22,.43,76)],
    [(.16,.60,69),(1.19,.45,74),(2.12,.54,78),(3.14,.54,81)],
    [(.25,.57,73),(1.26,.55,76),(2.32,.55,78),(3.21,.48,81)],
    [(.23,.55,70),(1.23,.54,73),(2.24,.62,78),(3.20,.49,82)],
]


def create_score(settings: Settings=Settings()):
    """A score is ordinary JSON; the synthesizer never needs to inspect the songbook."""
    bars=settings.preview_bars or BARS
    rng=np.random.default_rng(settings.seed)
    notes: list[Note]=[]; drums: list[Drum]=[]
    def add(part,beat,length,pitch,vel,pan=0):
        if 0<=beat<bars*4:
            notes.append(safe_note(part, beat, length, pitch+settings.transpose,vel,pan))
    def hit(kind,beat,vel,pan=0):
        if 0<=beat<bars*4:drums.append(Drum(kind,round(beat,5),round(vel,4),pan))
    chordlist=[]
    for bar in range(bars):
        start,end,section=section_for(bar);phrase=bar-start;pos=bar*4
        chord=PROGRESSIONS[section][phrase%4]; chordlist.append({'bar':bar,'chord':chord})
        tones,bass=CHORDS[chord]
        chorus=section.startswith('chorus');quiet=section in ('intro','instrumental','bridge','outro')
        # String and pad parts are independent, so they can be replaced without score edits.
        for i,p in enumerate(tones):
            add('pad',pos+.035,3.73,p,(.15 if section=='intro' else .11) if quiet else (.20 if chorus else .145),-.42 if i%2 else .42)
        if section=='outro':positions=[(.12,2.8,.35)]
        elif quiet:positions=[(.14,1.40,.27),(2.53,.95,.24)]
        else:positions=[(.10,.88,.32),(1.55,.53,.28),(2.85,.73,.32)]
        for k,(off,length,vel) in enumerate(positions):
            if section=='intro':vel*=1.32
            for j,p in enumerate((tones[1],tones[3])):
                add('keys',pos+off+j*.037,length,p+(12 if j and section=='intro' else 0),vel*(1-.04*j),-.2 if j==0 else .23)
        # Clean picked guitar: narrow timing and velocity deviations, doubled in choruses.
        guitar=[(.08,.27,.72),(.81,.27,.36),(1.52,.38,.62),(2.54,.36,.65),(3.40,.32,.46)]
        if quiet:guitar=[(.07,.55,.61),(1.43,.34,.42),(2.66,.43,.48)]
        if section=='outro':guitar=[(.08,.53,.45),(2.47,.52,.33)]
        for i,(off,length,vel) in enumerate(guitar):
            if section=='intro':vel*=1.24
            micro=float(np.clip(rng.normal(0,.012),-.026,.026))
            dynamics=float(rng.uniform(.92,1.07))
            pitch=tones[(i*2+1)%len(tones)]+(12 if i==4 and chorus else 0)
            add('pluck',pos+max(.03,off+micro),length,pitch,vel*dynamics,-.40 if i%2 else .4)
            if chorus and i in (0,2,4):
                add('pluck',pos+max(.03,off+micro+.024),length*.85,pitch-12,vel*.28,.50 if i%2 else -.50)
        if section not in ('intro','outro'):
            basspat=[(0,.86,0,.72),(1.54,.35,12,.41),(2.09,.67,0,.65),(3.51,.35,0,.57)]
            if chorus:basspat=[(0,.87,0,.86),(.91,.45,0,.43),(1.55,.48,12,.64),(2.11,.60,0,.74),(3.39,.40,0,.65)]
            if section=='bridge':basspat=[(0,1.62,0,.58),(2.59,.75,0,.40)]
            if section=='instrumental':basspat=[(0,.91,0,.66),(1.52,.40,12,.43),(2.5,1.04,0,.61)]
            for off,dur,octave,vel in basspat:add('bass',pos+off,dur,bass+octave,vel)
            if chorus and phrase%4==3: add('bass',pos+3.79,.17,bass+2,.44)
        # Sparkling arpeggiator stays behind the vocal-like lead.
        arpsteps=[0,3,5] if quiet else [0,1,3,4,6,7] if not chorus else list(range(8))
        for step in arpsteps:
            p=tones[[2,4,1,3][(step+phrase)%4]]+12
            add('arp',pos+.05+step*.5,.29,p,(.23 if section=='intro' else .18) if quiet else .26 if chorus else .22,-.55 if step%2 else .55)
        # Sections and instrumentation are explicitly structured; no random melody generator.
        if section in ('verse_a','verse_b'):
            for off,dur,p in VERSE[phrase%4]:
                if section=='verse_a' and phrase<4 and off>2.8:continue
                add('lead',pos+off,dur,p+(12 if section=='verse_b' and phrase in (7,15) else 0)
                    +(-2 if section=='verse_b' and phrase>=8 and phrase%4==2 and off>2 else 0),
                    .46 if section=='verse_a' else .54,.10)
        elif section=='rise':
            for off,dur,p in RISE[phrase%4]:add('lead',pos+off,dur,p,.51+.11*phrase/8,.08)
        elif chorus:
            for off,dur,p in HOOK[phrase%8]:
                # Same opening hook, more elaborate tail in the final chorus.
                variation=(-2 if section=='chorus_b' and phrase%8 in (3,7) and off>2 else 0)
                add('lead',pos+off,dur,p+variation,.69 if section=='chorus_a' else .77,.06)
                if section=='chorus_b' and phrase%4==2 and dur>.5:
                    add('counter',pos+off+.08,dur*.87,p-12,.22,-.37)
        elif section=='instrumental':
            for off,dur,p in HOOK[phrase%8][:3]:add('bell',pos+off,dur*1.22,p,.36,.24)
        elif section=='bridge':
            for off,dur,p in VERSE[phrase%4][:2]:add('keys',pos+off,dur*1.45,p,.35,-.2)
            if phrase>=4:add('lead',pos+.48,1.69,69+phrase,.42,.13)
        elif section=='outro':
            for off,dur,p in VERSE[phrase%4][:2]: add('bell',pos+off,dur*1.40,p,.23,.12)
        # Groove: backbeat anchor plus variation, no wholesale jitter on every event.
        if section=='intro':
            if phrase>=2:
                for n in range(4):hit('shaker',pos+n+.5,.15 if n%2 else .11,-.2 if n%2 else .2)
                if phrase>=4:
                    hit('rim',pos+2,.25)
                    add('bass',pos+.03,1.42,bass,.36)
                if phrase>=6:hit('kick',pos,.31)
            continue
        if section=='outro':
            if phrase<4:
                hit('kick',pos,.49 if phrase<2 else .30)
                hit('shaker',pos+2.5,.18,.25)
            continue
        if section=='bridge':
            hit('kick',pos,.54); hit('snare',pos+2.008,.45)
            for step in range(4):hit('hat',pos+step+.49,.16+.02*(step%2),.21 if step%2 else -.21)
        else:
            kick=[(0,1),(.98,.65),(2,.78),(2.76,.55),(3.5,.59)]
            if section=='instrumental':kick=[(0,1),(1.51,.43),(2.01,.8),(3.52,.53)]
            for off,vel in kick:hit('kick',pos+off,vel*(.79 if chorus else .62))
            for off in (1,3):
                hit('snare',pos+off+.009,.78 if chorus else .63)
                if chorus:hit('clap',pos+off+.028,.21)
                elif phrase%4!=0:hit('ghost',pos+off-.22,.17)
            for step in range(8):
                if section=='instrumental' and step%2:continue
                micro=float(np.clip(rng.normal(0,.006),-.012,.012))
                swing=.046 if step%2 else 0
                hvel=(.29 if step%2 else .20)*float(rng.uniform(.92,1.09))
                hit('hat',pos+max(.02,step*.5+swing+micro),hvel,-.29 if step%2 else .29)
            if chorus:
                for k in (3,7):hit('open_hat',pos+k*.5+.035,.17,.41)
                if phrase%4 in (1,3):hit('shaker',pos+3.72,.16,-.24)
        if phrase%8==7 and section not in ('instrumental','bridge'):
            for k in range(4):hit('tom',pos+3.02+k*.22,.24+.054*k,-.22+.14*k)
    for bar in (8,24,32,48,56,72,80,96):
        if bar<bars:hit('impact',bar*4,.43 if bar not in (32,80) else .60)
    return {'title':TITLE,'stem':STEM,'sample_rate':SR,'bpm':settings.bpm,
            'bars':bars,'transpose':settings.transpose,'seed':settings.seed,
            'duration_seconds':bars*4*60/settings.bpm+TAIL_SECONDS,
            'sections':[{'start':s,'end':min(e,bars),'name':n} for s,e,n in SECTIONS if s<bars],
            'chords':chordlist,
            'notes':[asdict(n) for n in notes], 'drums':[asdict(d) for d in drums]}

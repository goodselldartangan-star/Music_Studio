#!/usr/bin/env python3
"""Music Studio: original, offline, non-AI instrumental composer and synthesizer.

No cloud services, model APIs, soundfonts, samples, or keys. Made for the user.

Usage:
    python offline_song.py --out output
    python offline_song.py --out output --score-only
    python offline_song.py --out output --no-mp3

Needs numpy, scipy, soundfile, mido and ffmpeg to produce the MP3.
"""
from __future__ import annotations
import argparse
import json
import math
import subprocess
from dataclasses import dataclass, asdict
from pathlib import Path
from functools import lru_cache
import numpy as np
import soundfile as sf
from scipy.signal import butter, sosfilt, fftconvolve
import mido

NAME = 'Streetlight Letters'
STEM = 'Streetlight_Letters'
BPM = 116
SR = 44100
BEATS = 4
BARS = 100
TAIL = 4.0
SPB = 60/BPM
SEED = 426117
SEC = [(0,8,'opening'),(8,24,'verse_one'),(24,32,'rise'),
       (32,48,'chorus_one'),(48,56,'instrumental_break'),
       (56,72,'verse_two'),(72,80,'bridge'),(80,96,'last_chorus'),
       (96,100,'ending')]
# Chord pitch classes, but voice-led in the middle register with colorful extensions.
CHORDS = {
 'Em9': ([55,59,62,66,71],40), 'Cmaj9': ([55,59,62,64,67],36),
 'Gadd9': ([55,59,62,69,74],43), 'Dadd9': ([54,57,62,64,69],38),
 'D/F#': ([54,57,62,66,69],42), 'Am9': ([55,57,60,64,71],33),
 'B7sus4': ([57,59,64,66,69],35), 'Em/G': ([55,59,62,66,71],43),
 'G6/9': ([55,59,64,69,74],43)
}
PROGS = {
 'opening':['Em9','Cmaj9','Gadd9','Dadd9'],
 'verse_one':['Em9','Cmaj9','Gadd9','Dadd9'],
 'rise':['Am9','Cmaj9','Dadd9','B7sus4'],
 'chorus_one':['Cmaj9','Gadd9','D/F#','Em9'],
 'instrumental_break':['Em9','Am9','Gadd9','Dadd9'],
 'verse_two':['Em9','Cmaj9','Gadd9','Dadd9'],
 'bridge':['Am9','Em/G','Cmaj9','Dadd9'],
 'last_chorus':['Cmaj9','Gadd9','D/F#','Em9'],
 'ending':['Cmaj9','Dadd9','Em9','G6/9']
}
# Writing exact melodic phrases (not random melodies) is key to a listenable result.
VERSE = [
 [(0.55,.55,67),(1.25,.40,71),(2.12,.75,74),(3.22,.48,71)],
 [(0.2,.73,69),(1.18,.70,67),(2.12,.45,64),(2.88,.75,67)],
 [(0.5,.62,71),(1.36,.60,74),(2.15,.70,76),(3.17,.48,74)],
 [(0.1,.80,69),(1.14,.55,66),(2.15,1.35,64)]
]
# Eight-bar chorus lead melody: ascending question, more space in the answer.
HOOK = [
 [(0.20,.38,67),(.72,.47,71),(1.45,.69,74),(2.40,.43,76),(3.05,.78,79)],
 [(0.08,.71,79),(1.05,.52,74),(1.88,.55,71),(2.80,.48,69),(3.40,.43,71)],
 [(0.17,.44,69),(.83,.60,74),(1.66,.80,78),(2.75,.42,76),(3.36,.46,74)],
 [(0.15,.46,71),(.88,.52,74),(1.65,.76,76),(2.70,.61,79),(3.45,.43,76)],
 [(0.18,.41,74),(.77,.42,76),(1.45,.94,79),(2.68,.53,81),(3.37,.41,79)],
 [(0.11,.62,76),(1.00,.41,74),(1.65,.70,71),(2.65,.60,69),(3.42,.39,71)],
 [(0.10,.45,69),(.83,.50,74),(1.52,.73,78),(2.55,.43,81),(3.26,.55,78)],
 [(0.10,.60,79),(.93,.42,76),(1.65,.73,74),(2.65,1.12,71)]
]
PRE = [
 [(0.50,.43,69),(1.14,.45,71),(1.79,.55,72),(2.75,.72,76)],
 [(0.08,.60,71),(1.03,.63,74),(2.06,.45,76),(2.75,.75,79)],
 [(0.09,.73,74),(.96,.45,76),(1.65,.55,78),(2.55,.65,81)],
 [(0.16,.56,76),(.98,.47,78),(1.75,.51,81),(2.60,.88,83)]
]
COUNTER = [
 [(0.55,.95,64),(2.24,.50,67),(3.06,.64,71)],
 [(0.20,1.23,62),(1.90,.77,67),(3.03,.61,69)],
 [(0.50,.90,66),(2.03,.68,69),(3.00,.72,74)],
 [(0.32,1.20,67),(2.13,.85,71),(3.15,.55,74)]
]
@dataclass
class Note:
    voice: str
    beat: float
    beats: float
    pitch: int
    vel: float
    pan: float = 0.0

@dataclass
class Hit:
    kind: str
    beat: float
    vel: float
    pan: float = 0.0

notes: list[Note] = []
hits: list[Hit] = []

def note(voice, beat, length, pitch, vel=.65, pan=0):
    assert 0 <= beat <= BARS*BEATS and 0 < length <= 8 and 25 <= pitch <= 108
    notes.append(Note(voice,round(float(beat),4),round(float(length),4),int(pitch),float(vel),float(pan)))

def hit(kind, beat, vel=.8, pan=0):
    hits.append(Hit(kind,round(float(beat),4),float(vel),float(pan)))

def section(b):
    return next(name for s,e,name in SEC if s<=b<e)

def chord(b):
    sec=section(b)
    return PROGS[sec][(b-(next(s for s,e,n in SEC if n==sec)))%4]

def arrange():
    notes.clear();hits.clear()
    rng=np.random.default_rng(SEED)
    for b in range(BARS):
        s=section(b)
        cname=chord(b)
        voicing,root=CHORDS[cname]
        pos=b*4.0
        opening=s=='opening'; verse=s in ('verse_one','verse_two')
        chorus=s in ('chorus_one','last_chorus')
        introish=s in ('opening','instrumental_break','bridge','ending')
        full=s in ('chorus_one','last_chorus')
        # Wide pad with rich chord tones. Bass stays centered and mostly unaffected by reverb.
        padvol={'opening':.21,'verse_one':.22,'rise':.25,'chorus_one':.31,
                'instrumental_break':.21,'verse_two':.23,'bridge':.26,
                'last_chorus':.36,'ending':.22}[s]
        for j,p in enumerate(voicing):
            note('pad',pos+.025,3.81,p,padvol*(1+.02*(j%2)),(-.56 if j%2==0 else .56))
        # Muted, guitar-like rhythmic plucking gives the song its indie-pop motion.
        if s!='ending':
            if opening: rhythm=[(.05,.32,.42),(1.45,.32,.37),(2.54,.36,.45)]
            elif s=='instrumental_break': rhythm=[(.06,.45,.48),(1.60,.44,.45),(3.13,.43,.48)]
            elif s=='bridge': rhythm=[(.06,.33,.38),(2.07,.39,.44)]
            else: rhythm=[(.08,.29,.57),(.73,.22,.40),(1.53,.36,.56),(2.51,.29,.52),(3.40,.25,.37)]
            for j,(t,l,v) in enumerate(rhythm):
                p=voicing[(j*2+1)%len(voicing)] + (12 if j==4 and chorus else 0)
                note('pluck',pos+t,l,p,v*(1.14 if chorus else 1),(-.3 if j%2 else .3))
                if full and j in (0,2):
                    note('pluck',pos+t+.026,l,voicing[0]+12,v*.35, .26 if j==0 else -.3)
        # Distinct offbeat clav-key harmonies, contrasted with exposed bridge.
        if s in ('opening','instrumental_break','bridge','ending'):
            times=[(.11,1.55,.40),(2.45,.84,.32)] if s!='ending' else [(.08,3.45,.39)]
        else:
            times=[(.08,.72,.29),(1.54,.54,.29),(2.75,.70,.35)]
        for j,(off,length,vol) in enumerate(times):
            for k,p in enumerate(voicing[1::2]):
                note('keys',pos+off+k*.032,length,p+12 if opening and k==1 else p,
                     vol*(.87 if j else 1.),(-.28 if k==0 else .28))
        # Syncopated synth bass with anticipations, small melodic approach notes.
        if s not in ('opening','ending'):
            if s=='bridge':
                basspat=[(0,1.6,0,.68),(2.5,.8,0,.49)]
            elif s=='instrumental_break':
                basspat=[(0,.78,0,.68),(1.45,.48,0,.54),(2.4,.58,12,.61),(3.26,.43,0,.54)]
            else:
                basspat=[(0,.80,0,.83),(.91,.39,0,.48),(1.51,.42,12,.72),(2.04,.62,0,.69),(3.22,.58,0,.71)]
            for off,dur,octa,vel in basspat:
                note('bass',pos+off,dur,root+octa,vel*(1.08 if full else 1),0)
            if chorus and b%4==3:
                # Step-up transition into each four-bar phrase
                note('bass',pos+3.74,.22,root+2,.53)
        # Electronic dotted pulse / arpeggio maintains identity across sections.
        arp_notes=[voicing[2]+12,voicing[-1]+12,voicing[1]+12,voicing[3]+12]
        if s=='opening': ap=[0,3,5]
        elif s=='bridge': ap=[1,3,5]
        elif s=='ending': ap=[0,2,4]
        else: ap=list(range(8)) if s in ('rise','last_chorus') else [0,1,3,4,5,7]
        for k in ap:
            t=k*.5+.075
            p=arp_notes[(k+(b%4))%len(arp_notes)]
            vol=.24 if opening else .29 if verse else .33 if s=='rise' else .36 if full else .27
            note('arp',pos+t,.36,p,vol,(-.53 if k%2==0 else .53))
        # Melody: restraint in verses, an identifiable instrumental hook in choruses.
        if s=='opening' and b>=4:
            for off,l,p in VERSE[b%4][:2]: note('keys',pos+off,l,p,.25,.1)
        if verse:
            for off,l,p in VERSE[b%4]:
                if s=='verse_one' and b<12 and off>2.5: continue
                note('lead',pos+off,l,p,.39 if s=='verse_one' else .47,.06)
        if s=='rise':
            for off,l,p in PRE[(b-24)%4]: note('lead',pos+off,l,p,.48+.10*(b-24)/8,.04)
        if chorus:
            pat=HOOK[(b-(32 if s=='chorus_one' else 80))%8]
            for off,l,p in pat:
                note('lead',pos+off,l,p,.73 if s=='chorus_one' else .82,.04)
                if s=='last_chorus' and b>=88 and l>.55:
                    note('glow',pos+off+.028,l,p-12,.20,-.18)
            if s=='last_chorus':
                for off,l,p in COUNTER[(b-80)%4]:
                    note('counter',pos+off,l,p,.24, -.39)
        if s=='instrumental_break':
            for off,l,p in VERSE[b%4]: note('keys',pos+off,l*1.5,p+12,.44,.10)
        if s=='bridge':
            pat=VERSE[(b-72)%4]
            for off,l,p in pat[:3]:note('glow',pos+off,l*1.5,p,.35,-.2)
            if b>=76: note('lead',pos+.64,2.1,74+(b-76),.33,.1)
        if s=='ending':
            for off,l,p in VERSE[b%4][:2]: note('keys',pos+off,l*1.5,p,.35,.12)
            if b==99:
                for p in [55,59,64,69,74]: note('keys',pos+.20,2.6,p,.31, -.12 if p%2 else .13)
        # Percussion from silence to full chorus, with organic accents/fills.
        if opening:
            if b>=4:
                for k in range(4): hit('closed_hat',pos+k+.48,.20+.05*(k%2), (-.24 if k%2 else .24))
                hit('rim',pos+2,.24)
            continue
        if s=='ending':
            if b==96: hit('kick',pos,.52)
            if b in [96,97]:hit('closed_hat',pos+2.45,.19,-.23)
            continue
        if s=='bridge':
            hit('kick',pos,.57)
            hit('snare',pos+2,.42)
            for k in range(4):hit('closed_hat',pos+k+.5,.26,(-.20 if k%2==0 else .20))
        else:
            for off,v in [(0,1.0),(.98,.75),(2.0,.87),(2.78,.52),(3.51,.68)]:
                if s=='instrumental_break' and off in (.98,2.78):continue
                hit('kick',pos+off, (.82 if chorus else .69 if verse else .77)*v)
            for off in [1,3]:
                hit('snare',pos+off,(.83 if chorus else .70 if verse else .76))
                if chorus:hit('clap',pos+off+.015,.26)
                if verse:hit('ghost',pos+off-.22,.19)
            for k in range(8):
                if s=='instrumental_break' and k%2:continue
                swing=.032 if k%2 else 0
                v=(.24 if k%2==0 else .35)*(1.1 if chorus else 1)
                hit('closed_hat',pos+.5*k+swing,v,(-.33 if k%2 else .27))
            if chorus:
                for k in [3,7]:hit('open_hat',pos+.5*k+.03,.19,.43)
            if s=='rise' and b>=28:
                for k in range(8):hit('ghost',pos+2+k*.25,.08+.028*k)
        if (b+1)%8==0 and s not in ('instrumental_break','bridge'):
            for k in range(4):hit('tom',pos+3.05+k*.20,.23+.07*k,-.26+.16*k)
        if b%4==3 and chorus:
            hit('open_hat',pos+3.76,.28,.4)
    for b in [8,24,32,48,56,72,80,96]:
        hit('impact',b*4,.34 if b in (8,56) else .58)


def freq(m):return 440*2**((m-69)/12)

def sine(phase):return np.sin(phase)

def envelope(t, dur, attack=.006, release=.16):
    attack_env=1-np.exp(-t/max(attack,0.0002))
    release_env=np.clip((dur+release-t)/max(release,0.001),0,1)**1.3
    return (attack_env*release_env).astype(np.float32)

def synth(n:Note):
    f=freq(n.pitch);dur=n.beats*SPB
    release={'pad':.52,'bass':.15,'pluck':.25,'keys':.40,'arp':.22,
             'lead':.38,'counter':.28,'glow':.62}[n.voice]
    size=max(1,int((dur+release)*SR))
    t=np.arange(size,dtype=np.float32)/SR
    ph=2*np.pi*f*t
    if n.voice=='bass':
        ph=2*np.pi*(f*t+f*.0020*(1-np.exp(-t/.035)))
        a=envelope(t,dur,.006,.12)*(.82+.18*np.exp(-t/.22))
        y=.84*np.sin(ph)+.24*np.sin(2*ph+.32)+.12*np.sin(3*ph)*np.exp(-t/.27)
        y=np.tanh(y*1.25)*a*.40
    elif n.voice=='pluck':
        # Bright, short, muted string with partial-dependent decay and pick transient.
        a=envelope(t,dur,.0025,.17)*np.exp(-t/.36)
        y=(.55*np.sin(ph)+.34*np.sin(2.003*ph+.13)*np.exp(-t/.20)
           +.21*np.sin(3.001*ph+.4)*np.exp(-t/.11)
           +.11*np.sin(4.003*ph+.7)*np.exp(-t/.07)
           +.055*np.sin(5.01*ph+.9)*np.exp(-t/.045))
        y+=.037*np.sin(2*np.pi*2174*t)*np.exp(-t/.009)
        y=a*y*.64
    elif n.voice=='keys':
        a=envelope(t,dur,.004,.35)*np.exp(-t/(1.25+.15*dur))
        y=(.67*np.sin(ph)+.21*np.sin(2.0017*ph+.3)*np.exp(-t/.75)
           +.10*np.sin(3.002*ph+.25)*np.exp(-t/.30)+.04*np.sin(5.06*ph)*np.exp(-t/.14))
        y*=a*.57
    elif n.voice=='pad':
        a=envelope(t,dur,.24,.51)
        ph2=2*np.pi*f*(1.004*t)
        y=(.47*np.sin(ph)+.30*np.sin(ph2+.55)+.19*np.sin(2*ph+.3)
          +.11*np.sin(3*ph+.6))
        y*=a*.23
    elif n.voice=='arp':
        a=envelope(t,dur,.004,.17)*np.exp(-t/.23)
        mod=.43*np.exp(-t/.18)*np.sin(2*np.pi*f*2.001*t)
        y=(.64*np.sin(ph+mod)+.23*np.sin(2*ph+.24)+.12*np.sin(3*ph+.45))
        y*=a*.62
    elif n.voice in ('lead','counter','glow'):
        a=envelope(t,dur,.025 if n.voice=='lead' else .052,.31)
        vibr=.0027*np.sin(2*np.pi*5.0*np.maximum(t-.16,0))*(1-np.exp(-np.maximum(t-.16,0)/.16))
        lph=2*np.pi*f*(t+vibr/(2*np.pi*5.0))
        brightness=.73 if n.voice=='lead' else .38
        y=(.64*np.sin(lph)+.23*np.sin(2*lph+.12)*brightness+.14*np.sin(3*lph+.55)*brightness
           +.08*np.sin(lph*1.0032+.73))
        # a tiny pitch drop on attack adds movement
        y*=a*(.63 if n.voice=='lead' else .39)
    else:raise ValueError(n.voice)
    return y.astype(np.float32)*n.vel

@lru_cache(maxsize=1000)
def drum_wave(kind, vclass):
    tlen={'kick':.52,'snare':.31,'clap':.26,'closed_hat':.17,
          'open_hat':.34,'rim':.15,'tom':.36,'ghost':.18,'impact':1.35}[kind]
    t=np.arange(max(1,int(tlen*SR)),dtype=np.float32)/SR
    rr=np.random.default_rng(SEED + sum(ord(c) for c in kind)*51+vclass)
    noise=rr.standard_normal(len(t)).astype(np.float32)
    if kind=='kick':
        frequency=49+116*np.exp(-t/.023)
        phase=2*np.pi*np.cumsum(frequency)/SR
        y=(.84*np.sin(phase)*np.exp(-t/.105)
           +.11*noise*np.exp(-t/.004))
    elif kind in ('snare','ghost','clap','rim'):
        n=sosfilt(butter(2,[1150 if kind!='rim' else 2300,10000],btype='bandpass',fs=SR,output='sos'),noise)
        if kind=='clap':
            pulse=(np.exp(-((t-.015)/.009)**2)+.70*np.exp(-((t-.041)/.010)**2)
                   +.57*np.exp(-((t-.067)/.012)**2))
            y=n*(pulse*.18 + np.exp(-t/.07)*.10)
        elif kind=='rim':y=n*np.exp(-t/.019)*.13+np.sin(2*np.pi*900*t)*np.exp(-t/.012)*.13
        elif kind=='ghost':y=n*np.exp(-t/.052)*.17+np.sin(2*np.pi*184*t)*np.exp(-t/.039)*.11
        else:y=n*np.exp(-t/.095)*.40+np.sin(2*np.pi*183*t)*np.exp(-t/.084)*.19
    elif kind in ('closed_hat','open_hat'):
        n=sosfilt(butter(3,6200,btype='highpass',fs=SR,output='sos'),noise)
        tail=.034 if kind=='closed_hat' else .12
        y=n*np.exp(-t/tail)*(.31 if kind=='closed_hat' else .26)
    elif kind=='tom':
        fq=120+55*np.exp(-t/.037)
        y=np.sin(2*np.pi*np.cumsum(fq)/SR)*np.exp(-t/.11)*.38
    else:
        n=sosfilt(butter(2,[160,9000],btype='bandpass',fs=SR,output='sos'),noise)
        y=n*np.exp(-t/.32)*.20+np.sin(2*np.pi*66*t)*np.exp(-t/.35)*.35
    return y.astype(np.float32)


def as_midi(path):
    m=mido.MidiFile(ticks_per_beat=480)
    meta=mido.MidiTrack();m.tracks.append(meta)
    meta.append(mido.MetaMessage('track_name',name=NAME,time=0))
    meta.append(mido.MetaMessage('set_tempo',tempo=mido.bpm2tempo(BPM),time=0))
    meta.append(mido.MetaMessage('time_signature',numerator=4,denominator=4,time=0))
    chan={'keys':(0,2),'pad':(1,89),'bass':(2,39),'pluck':(3,27),'arp':(4,81),
          'lead':(5,81),'counter':(6,80),'glow':(7,88)}
    for voice,(ch,program) in chan.items():
        track=mido.MidiTrack();m.tracks.append(track)
        track.append(mido.MetaMessage('track_name',name=voice,time=0))
        track.append(mido.Message('program_change',channel=ch,program=program,time=0))
        ev=[]
        for n in notes:
            if n.voice==voice:
                ev.extend([(round(n.beat*480),1,n.pitch,round(n.vel*112)),
                           (round((n.beat+n.beats)*480),0,n.pitch,0)])
        tick=0
        for t,on,p,v in sorted(ev,key=lambda e:(e[0],e[1])):
            track.append(mido.Message('note_on' if on else 'note_off',channel=ch,note=p,
                                      velocity=v,time=t-tick));tick=t
    d=mido.MidiTrack();m.tracks.append(d);d.append(mido.MetaMessage('track_name',name='drums',time=0))
    mapping={'kick':36,'snare':38,'ghost':37,'clap':39,'closed_hat':42,'open_hat':46,
             'rim':37,'tom':45,'impact':49}
    ev=[]
    for h in hits:
        p=mapping[h.kind]
        ev.extend([(round(h.beat*480),1,p,round(h.vel*108)),(round((h.beat+.12)*480),0,p,0)])
    tick=0
    for t,on,p,v in sorted(ev,key=lambda e:(e[0],e[1])):
        d.append(mido.Message('note_on' if on else 'note_off',channel=9,note=p,velocity=v,time=t-tick));tick=t
    m.save(path)


def add_mono(bus, wave, st, pan):
    if st>=len(bus) or st<0:return
    end=min(st+len(wave),len(bus))
    p=max(-.99,min(.99,pan))
    bus[st:end,0]+=wave[:end-st]*math.sqrt((1-p)/2)
    bus[st:end,1]+=wave[:end-st]*math.sqrt((1+p)/2)


def fx_delay(buf, delay_sec=.36, fb=.29):
    out=np.zeros_like(buf)
    for i in range(1,4):
        d=round(delay_sec*i*SR)
        if d<len(buf):out[d:]+=buf[:-d]*(fb**i)
    return out


def room_ir(seed):
    rng=np.random.default_rng(seed)
    ir=np.zeros(int(1.8*SR),np.float32)
    for i in range(180):
        t=.016+1.54*rng.random()**.83
        idx=min(len(ir)-1,int(t*SR))
        ir[idx]+=rng.normal()*math.exp(-t/.43)*.075
    for tm,amp in [(0.027,.24),(.055,.18),(.101,.11),(.167,.08)]:
        ir[round(tm*SR)]+=amp
    return ir


def render(out):
    total=int((BARS*4*SPB+TAIL)*SR)
    rhythm=np.zeros((total,2),np.float32)
    harmony=np.zeros_like(rhythm)
    melodies=np.zeros_like(rhythm)
    sub=np.zeros_like(rhythm)
    for n in notes:
        wave=synth(n)
        dst=(sub if n.voice=='bass' else harmony if n.voice in ('pad','pluck','keys')
             else melodies)
        add_mono(dst,wave,int(n.beat*SPB*SR),n.pan)
    for i,h in enumerate(hits):
        y=drum_wave(h.kind,i%4)*h.vel
        add_mono(rhythm,y,int(h.beat*SPB*SR),h.pan)
    # Short four-on-the-floor volume dip is reserved for supporting instruments.
    side=np.ones(total,dtype=np.float32)
    for h in hits:
        if h.kind!='kick':continue
        st=int(h.beat*SPB*SR)
        duration=int(.205*SR)
        en=min(total,st+duration)
        t=np.arange(en-st,dtype=np.float32)/SR
        side[st:en]=np.minimum(side[st:en],1-.20*np.exp(-t/.080))
    harmony *= side[:,None]
    melodies *= (0.94+.06*side)[:,None]
    sub *= (0.90+.10*side)[:,None]
    # Wide but controlled echoes and synthetic room (no downloaded impulse responses).
    master=rhythm+sub+harmony+melodies
    for ch in range(2):
        master[:,ch]+=fx_delay(melodies[:,ch],.375 if ch==0 else .5625,.35)*.36
        wet=fftconvolve((.23*harmony[:,ch]+.28*melodies[:,ch]),room_ir(100+ch),mode='full')[:total]
        master[:,ch]+=wet*.22
    # Stereo image: mono fundamentals, stereo overtones and spatial cues.
    mid=.5*(master[:,0]+master[:,1])
    side=.5*(master[:,0]-master[:,1])
    side=sosfilt(butter(2,160,btype='highpass',fs=SR,output='sos'),side)
    master[:,0]=mid+side*1.50
    master[:,1]=mid-side*1.50
    # Gentle bus presence: brightens the plucked strings and the lead without harsh clipping.
    presence=sosfilt(butter(2,[780,6500],btype='bandpass',fs=SR,output='sos'),master,axis=0)
    air=sosfilt(butter(2,5500,btype='highpass',fs=SR,output='sos'),master,axis=0)
    master += .95*presence + .55*air
    master=sosfilt(butter(2,27,btype='highpass',fs=SR,output='sos'),master,axis=0).astype(np.float32)
    # Smooth occasional sum-bus peaks without hard digital clipping.
    master=np.tanh(master*.98).astype(np.float32)
    peak=float(np.max(np.abs(master)))
    master *= (.89/max(peak,1e-8))
    # Short fade-in, natural ending tail.
    fi=int(.05*SR)
    master[:fi]*=np.linspace(0,1,fi,dtype=np.float32)[:,None]
    fo=int(2*SR)
    master[-fo:]*=np.linspace(1,0,fo,dtype=np.float32)[:,None]
    out.mkdir(parents=True,exist_ok=True)
    path=out/(STEM+'.wav')
    sf.write(path,master,SR,subtype='PCM_24')
    rms=float(np.sqrt(np.mean(master**2)))
    return {'wav':str(path),'duration_seconds':len(master)/SR,'sample_rate':SR,
            'sample_peak_dBFS':20*math.log10(float(np.max(np.abs(master)))),
            'rms_dBFS':20*math.log10(rms)}


def main():
    arg=argparse.ArgumentParser()
    arg.add_argument('--out',type=Path,default=Path('output'))
    arg.add_argument('--score-only',action='store_true')
    arg.add_argument('--no-mp3',action='store_true')
    a=arg.parse_args();a.out.mkdir(parents=True,exist_ok=True)
    arrange()
    score={'name':NAME,'bpm':BPM,'bars':BARS,'beats_per_bar':BEATS,
        'duration_seconds':BARS*BEATS*SPB+TAIL,
        'sections':[{'start_bar':s,'end_bar':e,'name':n} for s,e,n in SEC],
        'chords':[{'bar':b,'name':chord(b)} for b in range(BARS)],
        'notes':[asdict(n) for n in notes], 'drums':[asdict(h) for h in hits]}
    (a.out/(STEM+'.score.json')).write_text(json.dumps(score,indent=2))
    as_midi(a.out/(STEM+'.mid'))
    result={'name':NAME,'notes':len(notes),'drum_hits':len(hits),'score_only':a.score_only}
    if not a.score_only:
        result.update(render(a.out))
        if not a.no_mp3:
            mp3=a.out/(STEM+'.mp3')
            subprocess.run(['ffmpeg','-hide_banner','-nostdin','-y','-loglevel','error',
              '-i',str(a.out/(STEM+'.wav')),'-metadata',f'title={NAME}',
              '-metadata','artist=Music Studio', '-codec:a','libmp3lame',
              '-b:a','320k',str(mp3)],check=True)
            result['mp3']=str(mp3)
    print(json.dumps(result,indent=2))

if __name__=='__main__':main()

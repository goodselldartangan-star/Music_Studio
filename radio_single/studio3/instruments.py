"""Independent sound generation. Input: note/drum. Output: mono float32 samples.

No external sounds, sample packs, AI APIs, or network access.
"""
from functools import lru_cache
import math
import numpy as np
from scipy.signal import butter, sosfilt
from .spec import Note, SR


def hz(midi): return 440.0 * 2 ** ((midi-69)/12)


def plucked_string(pitch, seconds, velocity, seed, brightness=1.0):
    """Fractional-delay Karplus–Strong pluck; string noise and simple body resonance."""
    rate=SR; freq=hz(pitch); period=rate/freq
    d=int(period); frac=period-d
    if d<3 or seconds<=0:raise ValueError('invalid string frequency/duration')
    count=max(d+4,int(seconds*rate));rng=np.random.default_rng(seed)
    excitation=rng.normal(size=d+2).astype(np.float32)
    excitation=np.convolve(excitation,[.12,.23,.30,.23,.12],mode='same')
    excitation-=.36*np.roll(excitation,max(1,int(d*.22)))
    excitation-=excitation.mean()
    excitation*=.75/max(1e-6,np.max(np.abs(excitation)))
    y=np.zeros(count,np.float32);y[:d+2]=excitation
    # Damped feedback keeps the tone naturally pitch-stable and finite.
    gain=math.exp(-6.9*d/(rate*(.95+.7*velocity)))
    for st in range(d+2,count,d):
        en=min(count,st+d)
        y[st:en]=gain*((1-frac)*y[st-d:en-d]+frac*y[st-d-1:en-d-1])
    # Mild body coloration; no soundfont is loaded.
    y=sosfilt(butter(2,min(10400,4300*brightness+2700),btype='lowpass',fs=SR,output='sos'),y)
    t=np.arange(count,dtype=np.float32)/SR
    envelope=(1-np.exp(-t/.0025))*np.clip((seconds-t)/.11,0,1)**1.15
    return (y*envelope).astype(np.float32)


def note_wave(note:Note,bpm:int,seed:int):
    f=hz(note.pitch);dur=note.duration*60/bpm
    rel={'pluck':.17,'bass':.14,'keys':.22,'pad':.55,'arp':.14,
         'lead':.22,'counter':.22,'bell':.60}[note.part]
    if note.part=='pluck':
        return .32*note.velocity*plucked_string(note.pitch,dur+rel,note.velocity,
                                               seed+note.pitch*17+int(note.beat*100),brightness=1.24)
    n=max(2,int(SR*(dur+rel)));t=np.arange(n,dtype=np.float64)/SR
    attack={'bass':.008,'keys':.011,'pad':.18,'arp':.005,'lead':.028,'counter':.025,'bell':.004}[note.part]
    envelope=(1-np.exp(-t/attack))*np.minimum(1,np.maximum(0,(dur+rel-t)/rel))**1.3
    if note.part=='bass':
        # Tiny downward pitch gesture and independent harmonic envelope.
        pitchbend=1+0.012*np.exp(-t/.045)
        ph=2*np.pi*f*np.cumsum(pitchbend)/SR
        y=(.71*np.sin(ph)+.28*np.sin(2*ph+.16)+.13*np.sin(3*ph+.2))
        y*=.7+.3*np.exp(-t/.16)
        envelope*=.61
    elif note.part=='pad':
        ph=2*np.pi*f*t
        y=.51*np.sin(ph)+.29*np.sin(ph*1.0021+.43)+.19*np.sin(2*ph+.24)
        y*=.94+.06*np.sin(2*np.pi*.42*t)
        envelope*=.26
    elif note.part=='keys':
        ph=2*np.pi*f*t
        y=(.66*np.sin(ph)+.29*np.sin(2.003*ph+.16)*np.exp(-t/.4)
          +.09*np.sin(3.992*ph+.6)*np.exp(-t/.15))
        envelope*=.60*np.exp(-t/1.0)
    elif note.part=='arp':
        ph=2*np.pi*f*t
        index=1.7*np.exp(-t/.08)
        y=(.74*np.sin(ph+index*np.sin(2*ph))+.21*np.sin(2*ph+.35))
        envelope*=.46*np.exp(-t/.23)
    elif note.part=='bell':
        ph=2*np.pi*f*t
        y=.84*np.sin(ph+1.6*np.exp(-t/.27)*np.sin(2.39*ph))+.16*np.sin(3.01*ph)
        envelope*=.32*np.exp(-t/.82)
    else:
        # A breath-shaped instrumental melody: scoop, delayed vibrato and variable brightness.
        vib=0.0033*np.sin(2*np.pi*5.0*np.maximum(0,t-.16))*(1-np.exp(-np.maximum(0,t-.16)/.12))
        pitchbend=1-.012*np.exp(-t/.035)+vib
        ph=2*np.pi*f*np.cumsum(pitchbend)/SR
        y=.67*np.sin(ph)+.25*np.sin(2*ph+.20)+.11*np.sin(3*ph+.34)
        # Natural decay, without a choppy gate between notes.
        envelope*=.54 if note.part=='lead' else .29
    return (y*envelope*note.velocity).astype(np.float32)


@lru_cache(maxsize=128)
def drum_wave(kind:str,variant:int=0):
    """Synthesized percussion; parameter variation prevents identical repeated hits."""
    length={'kick':.46,'snare':.31,'ghost':.21,'clap':.23,'hat':.15,
            'open_hat':.32,'shaker':.19,'rim':.13,'tom':.32,'impact':1.15}[kind]
    t=np.arange(max(3,int(length*SR)),dtype=np.float32)/SR
    rng=np.random.default_rng(182031+variant%7*941+sum(map(ord,kind))*13)
    noise=rng.normal(size=len(t)).astype(np.float32)
    if kind=='kick':
        f=47+140*np.exp(-t/.025)
        y=.95*np.sin(2*np.pi*np.cumsum(f)/SR)*np.exp(-t/.11)+.034*noise*np.exp(-t/.003)
    elif kind in ('hat','open_hat','shaker'):
        cutoff=5700 if kind!='shaker' else 3100
        hiss=sosfilt(butter(3,cutoff,fs=SR,btype='highpass',output='sos'),noise)
        tau=.031 if kind=='hat' else .102 if kind=='open_hat' else .066
        y=.44*hiss*np.exp(-t/tau)
        if kind=='shaker':y*=.68+.32*np.sin(2*np.pi*150*t)
    elif kind in ('snare','ghost','rim','clap'):
        hiss=sosfilt(butter(2,[1500,10000],fs=SR,btype='bandpass',output='sos'),noise)
        if kind=='clap':
            pulse=np.exp(-((t-.014)/.008)**2)+.78*np.exp(-((t-.046)/.010)**2)+.44*np.exp(-((t-.075)/.012)**2)
            y=.31*hiss*pulse
        else:
            amp={'snare':.36,'ghost':.13,'rim':.10}[kind]
            y=amp*hiss*np.exp(-t/(.078 if kind=='snare' else .040))
            y+=.14*np.sin(2*np.pi*(180 if kind!='rim' else 920)*t)*np.exp(-t/.047)
    elif kind=='tom':
        y=.34*np.sin(2*np.pi*np.cumsum((103+variant%7*.65)+90*np.exp(-t/.025))/SR)*np.exp(-t/.12)
    else:
        y=(.15*noise+.26*np.sin(2*np.pi*60*t))*np.exp(-t/.27)
    return y.astype(np.float32)

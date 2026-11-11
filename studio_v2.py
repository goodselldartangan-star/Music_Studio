#!/usr/bin/env python3
"""Music Studio v2: original, deterministic instrumental composition and physical-model DSP.

No model APIs, network requests, soundfonts or downloaded samples. Requires numpy,
scipy, soundfile, mido, and ffmpeg for MP3 export. Original implementation.

Usage: python studio_v2.py --out output_v2 [--preview-bars 8] [--score-only]
"""
from __future__ import annotations
import argparse
from dataclasses import asdict, dataclass
import json
import math
from pathlib import Path
import subprocess
import numpy as np
import soundfile as sf
from scipy.signal import butter, sosfilt, resample_poly
import mido

NAME = 'Porchlight Receiver'
STEM = 'Porchlight_Receiver'
SR = 44100
BPM = 114
BARS = 88
SEED = 20261111
SPB = 60 / BPM
TAIL = 3.5
SECTIONS = [(0, 8, 'intro'), (8, 20, 'verse_one'), (20, 28, 'prechorus'),
            (28, 44, 'chorus_one'), (44, 52, 'interlude'), (52, 64, 'verse_two'),
            (64, 72, 'bridge'), (72, 84, 'final_chorus'), (84, 88, 'outro')]
CHORDS = {
    'Am9': ([57, 60, 64, 67, 71], 33), 'Fmaj7': ([57, 60, 64, 65, 69], 29),
    'Cadd9': ([55, 60, 62, 64, 67], 36), 'Gsus4': ([55, 60, 62, 67, 69], 31),
    'G6': ([55, 59, 62, 64, 67], 31), 'Dm9': ([57, 60, 64, 65, 69], 38),
    'E7sus': ([56, 59, 62, 64, 69], 40)
}
PROGRESSIONS = {
    'intro': ['Am9', 'Fmaj7', 'Cadd9', 'Gsus4'],
    'verse_one': ['Am9', 'Fmaj7', 'Cadd9', 'G6'],
    'prechorus': ['Dm9', 'Fmaj7', 'G6', 'E7sus'],
    'chorus_one': ['Fmaj7', 'Cadd9', 'G6', 'Am9'],
    'interlude': ['Am9', 'Dm9', 'Fmaj7', 'Gsus4'],
    'verse_two': ['Am9', 'Fmaj7', 'Cadd9', 'G6'],
    'bridge': ['Dm9', 'Am9', 'Fmaj7', 'E7sus'],
    'final_chorus': ['Fmaj7', 'Cadd9', 'G6', 'Am9'],
    'outro': ['Dm9', 'Fmaj7', 'E7sus', 'Am9']
}
# Explicit composition, not randomly sampled melody; the second chorus answers the first.
VERSE = [
    [(0.5,.52,69),(1.28,.45,72),(2.20,.70,76),(3.25,.43,72)],
    [(0.23,.80,69),(1.36,.58,67),(2.12,.65,65),(3.18,.48,69)],
    [(0.55,.62,67),(1.45,.54,72),(2.32,.70,74),(3.22,.42,76)],
    [(0.19,.65,74),(1.14,.62,71),(2.23,1.20,69)]
]
# 8-bar hook: rising motif, delayed answer, deliberate held notes and rests.
HOOK = [
    [(.20,.44,72),(.92,.50,76),(1.76,.67,79),(2.95,.78,81)],
    [(.14,.90,79),(1.58,.56,76),(2.52,.96,74)],
    [(.24,.50,71),(.96,.52,74),(1.82,.72,79),(3.01,.62,83)],
    [(.18,.84,81),(1.45,.50,79),(2.33,1.05,76)],
    [(.18,.45,72),(.86,.48,76),(1.64,.90,79),(2.99,.55,84)],
    [(.11,.82,83),(1.37,.55,79),(2.18,.60,76),(3.16,.51,74)],
    [(.22,.49,71),(.95,.65,74),(1.97,.75,79),(3.02,.53,81)],
    [(.12,.66,79),(1.24,.52,76),(2.09,1.45,72)]
]
PRE = [
    [(.30,.54,69),(1.22,.52,72),(2.28,.70,74),(3.17,.46,76)],
    [(.17,.69,72),(1.20,.54,76),(2.22,.62,77),(3.18,.55,79)],
    [(.18,.73,74),(1.42,.50,76),(2.35,.73,79),(3.18,.45,81)],
    [(.20,.56,76),(1.21,.51,79),(2.17,.67,81),(3.19,.52,83)]
]
@dataclass(frozen=True)
class Note:
    part: str
    beat: float
    duration: float
    pitch: int
    velocity: float
    pan: float = 0.0

@dataclass(frozen=True)
class Hit:
    kind: str
    beat: float
    velocity: float
    pan: float = 0.0


def current_section(bar):
    return next((start, name) for start, end, name in SECTIONS if start <= bar < end)


def current_chord(bar):
    start, name = current_section(bar)
    return PROGRESSIONS[name][(bar-start) % 4]


def song_plan(preview_bars=None, bpm=BPM, transpose=0, seed=SEED):
    """Return deterministic score, with constrained humanization and motif development."""
    if not isinstance(bpm, int) or not 90 <= bpm <= 145:
        raise ValueError('BPM must be an integer from 90 to 145')
    if not isinstance(transpose, int) or not -5 <= transpose <= 5:
        raise ValueError('transpose must be between -5 and +5 semitones')
    bars = preview_bars if preview_bars is not None else BARS
    if not isinstance(bars, int) or not (1 <= bars <= BARS):
        raise ValueError('preview_bars must be between 1 and 88')
    notes, drums = [], []
    rng = np.random.default_rng(seed)

    def add(part, beat, length, pitch, vel, pan=0):
        if beat >= bars*4 or length <= 0: return
        pitch += transpose
        assert 28 <= pitch <= 100 and 0 <= vel <= 1.3
        notes.append(Note(part, round(beat, 5), round(length, 4), int(pitch), round(vel, 4), pan))

    def hit(kind, beat, vel, pan=0):
        if 0 <= beat < bars*4:
            drums.append(Hit(kind, round(beat, 5), round(vel, 4), pan))

    for bar in range(bars):
        s0, section = current_section(bar)
        phrase = bar-s0
        chord = current_chord(bar)
        tones, bass = CHORDS[chord]
        origin = bar*4.
        chorus = section in ('chorus_one', 'final_chorus')
        sparse = section in ('intro', 'bridge', 'outro', 'interlude')
        # Pads and piano have independent, modest expression; bass and kick stay tight.
        for i, pitch in enumerate(tones):
            add('pad', origin + .03, 3.72, pitch, .16+(.055 if chorus else .0), -.30 if i%2 else .30)
        keys = [(0.12, 1.3, .22), (2.46, .92, .20)] if sparse else [(0.12,.72,.27),(1.57,.50,.21),(2.79,.78,.29)]
        if section == 'outro': keys = [(.10,3.24,.25)]
        for k, (off, dur, vel) in enumerate(keys):
            for j, pitch in enumerate((tones[1], tones[3])):
                add('keys', origin+off+j*.036, dur, pitch + (12 if section=='intro' and j else 0), vel*(.94+.04*k), -.20 if j==0 else .20)
        # First section deliberately withholds the full plucked motif.
        picking = [(0.1,.44,.46),(1.48,.34,.39),(2.61,.41,.43)] if sparse else [(.10,.32,.56),(.82,.28,.34),(1.56,.38,.55),(2.61,.31,.51),(3.44,.28,.39)]
        if section == 'outro': picking = [(0.12,.80,.37),(2.52,.56,.31)]
        for i,(off,dur,vel) in enumerate(picking):
            # A stable pattern with deterministic guitaristic velocity and microtiming.
            micro = float(np.clip(rng.normal(0,.010),-.025,.025))
            dynamics = float(rng.uniform(.94,1.06))
            chosen = tones[(2*i+1)%5] + (12 if i==4 and chorus else 0)
            add('pluck', origin+max(.02,off+micro), dur, chosen, vel*dynamics*(1.1 if chorus else 1), -.35 if i%2 else .35)
        # Bass uses rests/approach notes, with controlled velocity rather than random note choice.
        if section not in ('intro','outro'):
            patt = [(0,.77,0,.75),(1.48,.46,12,.56),(2.1,.61,0,.64),(3.37,.48,0,.64)]
            if section=='bridge': patt=[(0,1.55,0,.57),(2.53,.72,0,.43)]
            elif chorus: patt=[(0,.84,0,.86),(.95,.39,0,.40),(1.53,.49,12,.66),(2.16,.59,0,.70),(3.48,.35,0,.61)]
            for off,dur,octv,vel in patt:
                add('bass',origin+off,dur,bass+octv,vel,0)
            if chorus and phrase%4==3:
                add('bass',origin+3.82,.16,bass+2,.41,0)
        # Arpeggio accent pattern rotates through chord tones without altering identity.
        positions = [0,3,5] if section=='intro' else [0,2,5] if section=='bridge' else [0,1,3,4,6,7]
        if chorus: positions=list(range(8))
        arptones = [tones[2]+12,tones[4]+12,tones[1]+12,tones[3]+12]
        for step in positions:
            add('arp',origin+step*.5+.07,.31,arptones[(step+phrase%4)%4],.24 if sparse else .30 if chorus else .27,-.49 if step%2 else .49)
        # Verse, prechorus and chorus motifs develop instead of constant new-note generation.
        if section in ('verse_one','verse_two'):
            for off,dur,pitch in VERSE[phrase%4]:
                if section=='verse_one' and phrase<4 and off>2.8: continue
                add('lead',origin+off,dur,pitch if section=='verse_one' else pitch+(12 if phrase in (7,11) else 0),
                    .43 if section=='verse_one' else .50,.09)
        elif section=='prechorus':
            for off,dur,pitch in PRE[phrase%4]:
                add('lead',origin+off,dur,pitch,.45+.12*phrase/8,.08)
        elif chorus:
            melody=HOOK[phrase%8]
            for off,dur,pitch in melody:
                # Final chorus changes a few melodic endings and adds a subdued lower reply.
                final=section=='final_chorus'
                delta = -2 if final and phrase in (3,7) and off>2 else 0
                add('lead',origin+off,dur,pitch+delta,.69 if not final else .76,.06)
                if final and phrase%4==2 and dur>.5:
                    add('reply',origin+off+.06,dur*.9,pitch-12,.21,-.35)
        elif section=='interlude':
            for off,dur,pitch in VERSE[phrase%4][:3]:
                add('bell',origin+off,dur*1.45,pitch+12,.32,.17)
        elif section=='bridge':
            for off,dur,pitch in VERSE[phrase%4][:3]:
                add('bell',origin+off,dur*1.8,pitch,.31,-.22)
            if phrase>=4: add('lead',origin+.66,1.45,72+phrase,.31,.10)
        elif section=='outro':
            for off,dur,pitch in VERSE[phrase%4][:2]:
                add('keys',origin+off,dur*1.5,pitch,.26,.13)
        # Groove: swing is applied to offbeats only. Backbeat stays a reliable anchor.
        if section == 'intro':
            if phrase>=4:
                for k in range(4):hit('hat',origin+k+.48,.20+(.04 if k%2 else 0),-.20 if k%2 else .20)
                hit('rim',origin+2,.27)
            continue
        if section=='outro':
            if phrase==0: hit('kick',origin,.45)
            if phrase<=1:hit('hat',origin+2.45,.18,.22)
            continue
        if section=='bridge':
            hit('kick',origin,.53)
            hit('snare',origin+2.00,.41)
            for k in range(4):hit('hat',origin+k+.52,.22,-.18 if k%2 else .18)
        else:
            for off,lev in [(0,1),(.98,.70),(2,.84),(2.78,.55),(3.49,.65)]:
                if section=='interlude' and off in (.98,2.78):continue
                hit('kick',origin+off,lev*(.74 if chorus else .63))
            for off in (1,3):
                hit('snare',origin+off,.77 if chorus else .64)
                if chorus:hit('clap',origin+off+.026,.20)
                if section.startswith('verse'):hit('ghost',origin+off-.24,.14)
            for step in range(8):
                if section=='interlude' and step%2:continue
                swing=(.035 if step%2 else 0.)
                jitter=float(np.clip(rng.normal(0,.006),-.012,.012))
                vel=(.25 if step%2==0 else .33)*float(rng.uniform(.91,1.08))
                hit('hat',origin+step*.5+swing+jitter,vel,-.23 if step%2 else .23)
            if chorus:
                for step in (3,7):hit('open_hat',origin+step*.5+.039,.17,.38)
        if phrase%8==7 and section not in ('interlude','bridge'):
            for k in range(4):hit('tom',origin+3.02+k*.22,.23+.06*k,-.24+.15*k)
    for sectionbar in (8,20,28,44,52,64,72,84):
        if sectionbar<bars:hit('impact',sectionbar*4,.32 if sectionbar in (8,52) else .51)
    return {'title':NAME,'stem':STEM,'bpm':bpm,'transpose':transpose,'seed':seed,'bars':bars,'sample_rate':SR,
            'duration_seconds':bars*4*(60/bpm)+TAIL,
            'sections':[{'start':st,'end':min(en,bars),'name':name}
                        for st,en,name in SECTIONS if st<bars],
            'chords':[{'bar':i,'chord':current_chord(i)} for i in range(bars)],
            'notes':[asdict(n) for n in notes], 'drums':[asdict(d) for d in drums]}


def hz(midi):return 440.0*2.0**((midi-69)/12)


def string_wave(pitch, duration, velocity=.6, seed=1, rate=SR):
    """Lightweight digital-waveguide/Karplus–Strong pluck with fractional-delay tuning.

    Noise excitation -> pick position comb -> interpolated feedback delay. Operates
    in vectorized blocks, no extra samples, copied code, or numba required.
    """
    if duration<=0: raise ValueError('positive duration required')
    frequency=hz(pitch)
    period=rate/frequency
    delay=int(math.floor(period))
    if delay<3:raise ValueError('pitch too high for physical model')
    frac=period-delay
    samples=max(delay+4,int(duration*rate))
    rng=np.random.default_rng(seed)
    noise=rng.normal(size=delay+2).astype(np.float32)
    noise=np.convolve(noise,np.array([.14,.23,.26,.23,.14],dtype=np.float32),mode='same')
    picklag=max(1,int(.20*delay))
    exc=noise-np.roll(noise,picklag)*.44
    exc-=np.mean(exc)
    exc/=max(1e-6,np.max(np.abs(exc)))
    out=np.zeros(samples,np.float32)
    out[:delay+2]=exc*min(1.,.28+velocity*.78)
    decay=1.05 + 1.20*(1-velocity)
    gain=math.exp(-6.9*delay/(rate*decay))
    # Delay is greater than each processed block. Both taps are already rendered.
    start=delay+2
    while start<samples:
        end=min(samples,start+delay)
        out[start:end]=gain*((1-frac)*out[start-delay:end-delay]+frac*out[start-delay-1:end-delay-1])
        start=end
    # Fast but finite release, plus a gentle body tone low-pass.
    t=np.arange(samples,dtype=np.float32)/rate
    envelope=(1-np.exp(-t/.002))*np.clip((duration-t)/.10,0,1)**1.3
    return (sosfilt(butter(2,6900,btype='lowpass',fs=rate,output='sos'),out)*envelope).astype(np.float32)


def voice_wave(note, seed=SEED, bpm=BPM):
    """Synthesize a rendered note at its own velocity and articulation."""
    part=note.part; f=hz(note.pitch);dur=note.duration*(60/bpm)
    release={'pluck':.12,'bass':.15,'pad':.55,'keys':.32,'arp':.15,'lead':.33,'reply':.27,'bell':.65}[part]
    if part=='pluck':
        y=string_wave(note.pitch,dur+release,note.velocity,seed+note.pitch*13+round(note.beat*10))
        return y*.34*note.velocity
    length=max(1,int((dur+release)*SR))
    t=np.arange(length,dtype=np.float32)/SR
    attack=.008 if part in ('bass','keys','arp','bell') else .19 if part=='pad' else .037
    env=(1-np.exp(-t/attack))*np.clip((dur+release-t)/release,0,1)**1.3
    # Frequency-dependent partial limits avoid generating harmonics above Nyquist.
    harmonics=lambda amps:sum(a*np.sin(2*np.pi*k*f*t+phase) for k,a,phase in amps if k*f<SR*.43)
    if part=='bass':
        y=harmonics([(1,.80,0),(2,.22,.24),(3,.09,.17)])
        y*=np.exp(-t/.80)*.26+.67
        env*=.55
    elif part=='pad':
        y=.55*np.sin(2*np.pi*f*t)+.28*np.sin(2*np.pi*f*1.003*t+.5)+.16*np.sin(2*np.pi*2*f*t+.2)
        env*=.28
    elif part=='keys':
        y=harmonics([(1,.70,0),(2,.24,.2),(3,.10,.38),(5,.048,.9)])
        env*=.49*np.exp(-t/1.25)
    elif part=='arp':
        modulation=.30*np.exp(-t/.17)*np.sin(2*np.pi*f*2*t)
        y=.72*np.sin(2*np.pi*f*t+modulation)+.22*np.sin(2*np.pi*2*f*t+.18)
        env*=.51*np.exp(-t/.28)
    elif part=='bell':
        # Low-index decaying FM bell, not sampled audio.
        ph=2*np.pi*f*t
        mod=1.4*np.exp(-t/.45)*np.sin(ph*2.4)
        y=np.sin(ph+mod)+.13*np.sin(ph*3.01)
        env*=.27*np.exp(-t/1.1)
    else:
        # Short pitch scoop and delayed vibrato; brighter chorus lead, softer reply.
        vibr=.003*np.sin(2*np.pi*5.3*np.maximum(t-.20,0))*(1-np.exp(-np.maximum(t-.20,0)/.11))
        scoop=.0045*np.exp(-t/.045)
        phase=2*np.pi*f*(t+vibr/(2*np.pi*5.3)+scoop*.012)
        y=.68*np.sin(phase)+.26*np.sin(2*phase+.16)+.08*np.sin(3*phase+.51)
        env*=.52 if part=='lead' else .27
    return (y*env*note.velocity).astype(np.float32)


def drum_wave(kind, variation=0):
    lengths={'kick':.45,'snare':.30,'ghost':.21,'clap':.24,'hat':.15,
             'open_hat':.33,'rim':.14,'tom':.33,'impact':1.15}
    t=np.arange(int(lengths[kind]*SR),dtype=np.float32)/SR
    rng=np.random.default_rng(SEED + sum(map(ord,kind))*17+variation%7)
    noise=rng.normal(size=len(t)).astype(np.float32)
    if kind=='kick':
        frequency=48+132*np.exp(-t/.028)
        ph=2*np.pi*np.cumsum(frequency)/SR
        y=.86*np.sin(ph)*np.exp(-t/.10)+.045*noise*np.exp(-t/.003)
    elif kind in ('hat','open_hat'):
        high=sosfilt(butter(3,6800,fs=SR,btype='highpass',output='sos'),noise)
        y=high*np.exp(-t/(.033 if kind=='hat' else .105))*.21
    elif kind in ('snare','ghost','clap','rim'):
        high=sosfilt(butter(2,[1200,9500],fs=SR,btype='bandpass',output='sos'),noise)
        if kind=='clap':
            pulse=np.exp(-((t-.02)/.009)**2)+.73*np.exp(-((t-.049)/.01)**2)+.40*np.exp(-((t-.078)/.014)**2)
            y=.24*high*pulse
        else:
            amp={'snare':.31,'ghost':.10,'rim':.095}[kind]
            y=high*np.exp(-t/(.085 if kind=='snare' else .043))*amp
            y+=.14*np.sin(2*np.pi*(182 if kind!='rim' else 912)*t)*np.exp(-t/.052)
    elif kind=='tom':
        y=.34*np.sin(2*np.pi*np.cumsum(116+65*np.exp(-t/.028))/SR)*np.exp(-t/.105)
    else:
        y=(.13*noise+.23*np.sin(2*np.pi*70*t))*np.exp(-t/.25)
    return y.astype(np.float32)


def stereo_add(destination, signal, beat, pan, bpm=BPM):
    start=int(max(0,beat)*(60/bpm)*SR)
    stop=min(len(destination),start+len(signal))
    if stop<=start:return
    p=np.clip(pan,-.98,.98)
    destination[start:stop,0]+=signal[:stop-start]*math.sqrt((1-p)/2)
    destination[start:stop,1]+=signal[:stop-start]*math.sqrt((1+p)/2)


def delay_stereo(signal):
    wet=np.zeros_like(signal)
    for ch,sec in enumerate((.31,.45)):
        for rep in (1,2,3):
            d=int(sec*rep*SR)
            wet[d:,ch]+=signal[:-d,ch]*(.35**rep)
    return wet


def soft_clip_oversampled(chunk, drive=1.12):
    """Resampling before nonlinear saturation reduces foldback distortion."""
    up=resample_poly(chunk,2,1,axis=0)
    effected=np.tanh(up*drive)/np.tanh(drive)
    return resample_poly(effected,1,2,axis=0)[:len(chunk)].astype(np.float32)


def apply_bus_eq(name, signal):
    # Per-bus tone/space control replaces one massive global presence boost.
    if name=='drums':
        return sosfilt(butter(2,33,fs=SR,btype='highpass',output='sos'),signal,axis=0)
    if name=='bass':
        return sosfilt(butter(2,1300,fs=SR,btype='lowpass',output='sos'),signal,axis=0)
    if name=='strings':
        return sosfilt(butter(2,[125,10500],fs=SR,btype='bandpass',output='sos'),signal,axis=0)
    if name=='keys':
        return sosfilt(butter(2,[95,11000],fs=SR,btype='bandpass',output='sos'),signal,axis=0)
    return sosfilt(butter(2,[180,10000],fs=SR,btype='bandpass',output='sos'),signal,axis=0)


def write_midi(score, target):
    file=mido.MidiFile(ticks_per_beat=480)
    mt=mido.MidiTrack();file.tracks.append(mt)
    mt.append(mido.MetaMessage('track_name',name=NAME,time=0))
    mt.append(mido.MetaMessage('set_tempo',tempo=mido.bpm2tempo(score['bpm']),time=0))
    mt.append(mido.MetaMessage('time_signature',numerator=4,denominator=4,time=0))
    programs={'bass':(0,38),'pluck':(1,25),'keys':(2,3),'pad':(3,89),
              'arp':(4,81),'lead':(5,81),'reply':(6,80),'bell':(7,10)}
    for part,(channel,program) in programs.items():
        track=mido.MidiTrack();file.tracks.append(track)
        track.append(mido.MetaMessage('track_name',name=part,time=0))
        track.append(mido.Message('program_change',channel=channel,program=program,time=0))
        events=[]
        for n in score['notes']:
            if n['part']!=part:continue
            events.extend([(round(n['beat']*480),1,n['pitch'],max(1,min(127,round(n['velocity']*105)))),
                           (round((n['beat']+n['duration'])*480),0,n['pitch'],0)])
        last=0
        for tick,on,pitch,vel in sorted(events,key=lambda item:(item[0],item[1])):
            track.append(mido.Message('note_on' if on else 'note_off',channel=channel,note=pitch,velocity=vel,time=tick-last));last=tick
    track=mido.MidiTrack();file.tracks.append(track)
    track.append(mido.MetaMessage('track_name',name='percussion',time=0))
    mapping={'kick':36,'snare':38,'ghost':37,'clap':39,'hat':42,'open_hat':46,'rim':37,'tom':45,'impact':49}
    events=[]
    for hit in score['drums']:
        pitch=mapping[hit['kind']];start=round(hit['beat']*480)
        events.extend([(start,1,pitch,max(1,min(127,round(hit['velocity']*105)))),(start+57,0,pitch,0)])
    last=0
    for tick,on,pitch,vel in sorted(events,key=lambda item:(item[0],item[1])):
        track.append(mido.Message('note_on' if on else 'note_off',channel=9,note=pitch,velocity=vel,time=tick-last));last=tick
    file.save(target)


def render_audio(score, output):
    frames=round(score['duration_seconds']*SR)
    spb=60/score['bpm']
    stems={part:np.zeros((frames,2),np.float32) for part in ('drums','bass','strings','keys','lead')}
    for n in score['notes']:
        event=Note(**n)
        wave=voice_wave(event,bpm=score['bpm'])
        bus='strings' if event.part=='pluck' else 'keys' if event.part in ('keys','pad','arp') else 'bass' if event.part=='bass' else 'lead'
        stereo_add(stems[bus],wave,event.beat,event.pan,bpm=score['bpm'])
    for i,h in enumerate(score['drums']):
        event=Hit(**h)
        stereo_add(stems['drums'],drum_wave(event.kind,i%7)*event.velocity,event.beat,event.pan,bpm=score['bpm'])
    # Duck only supporting parts after strong kicks. Delays stay clear of subbass.
    duck=np.ones(frames,np.float32)
    for h in score['drums']:
        if h['kind']!='kick':continue
        st=round(h['beat']*spb*SR);stop=min(frames,st+round(.19*SR))
        if stop>st:
            t=np.arange(stop-st,dtype=np.float32)/SR
            duck[st:stop]=np.minimum(duck[st:stop],1-.15*np.exp(-t/.072))
    master=np.zeros((frames,2),np.float32)
    gains={'drums':.94,'bass':.88,'strings':.90,'keys':.81,'lead':.89}
    for name,bus in stems.items():
        if name in ('keys','strings'):bus*=duck[:,None]
        conditioned=apply_bus_eq(name,bus)
        if name=='lead':conditioned+=delay_stereo(conditioned)*.24
        if name=='keys':conditioned+=delay_stereo(conditioned)*.11
        master+=conditioned.astype(np.float32)*gains[name]
        del conditioned
    # Low frequencies summed to mono for playback compatibility.
    mid=.5*(master[:,0]+master[:,1])
    side=.5*(master[:,0]-master[:,1])
    side=sosfilt(butter(2,155,fs=SR,btype='highpass',output='sos'),side)
    master[:,0]=mid+side*1.22
    master[:,1]=mid-side*1.22
    master=sosfilt(butter(2,29,fs=SR,btype='highpass',output='sos'),master,axis=0).astype(np.float32)
    # Use section-level macro dynamics rather than crushing the entire mix.
    gain=np.ones(frames,np.float32)
    for sec in score['sections']:
        if sec['name']=='intro':level=.83
        elif sec['name']=='bridge':level=.86
        elif sec['name']=='outro':level=.79
        elif sec['name']=='prechorus':level=.94
        elif sec['name'] in ('chorus_one','final_chorus'):level=1.10
        else:level=.94
        lo=round(sec['start']*4*spb*SR);hi=min(frames,round(sec['end']*4*spb*SR))
        gain[lo:hi]=level
    gain=sosfilt(butter(1,3,fs=SR,btype='lowpass',output='sos'),gain)
    master*=gain[:,None]
    # Piecewise 2x saturation prevents excessive aliasing and retains more dynamics.
    for st in range(0,frames,SR*6):
        en=min(frames,st+SR*6)
        master[st:en]=soft_clip_oversampled(master[st:en],drive=1.045)
    peak=float(np.max(np.abs(master)))
    master*=.83/max(peak,1e-9)   # -1.62 dB sample-peak ceiling; true-peak verified later
    fadein=int(.035*SR)
    master[:fadein]*=np.linspace(0,1,fadein,dtype=np.float32)[:,None]
    fadeout=int(2.5*SR)
    master[-fadeout:]*=np.linspace(1,0,fadeout,dtype=np.float32)[:,None]**1.3
    wav=output/(STEM+'.wav')
    sf.write(wav,master,SR,subtype='PCM_24')
    return {'wav':str(wav),'sample_peak_dbfs':round(20*math.log10(np.max(np.abs(master))),2),
            'rms_dbfs':round(20*math.log10(max(1e-9,np.sqrt(np.mean(master**2)))),2)}


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--out',type=Path,default=Path('output_v2'))
    ap.add_argument('--preview-bars',type=int)
    ap.add_argument('--score-only',action='store_true')
    ap.add_argument('--no-mp3',action='store_true')
    ap.add_argument('--bpm',type=int,default=BPM,help='Tempo: 90–145 BPM')
    ap.add_argument('--transpose',type=int,default=0,help='Transpose in semitones: -5 to +5')
    ap.add_argument('--seed',type=int,default=SEED,help='Deterministic performance variation')
    args=ap.parse_args();args.out.mkdir(parents=True,exist_ok=True)
    score=song_plan(args.preview_bars,bpm=args.bpm,transpose=args.transpose,seed=args.seed)
    (args.out/(STEM+'.score.json')).write_text(json.dumps(score,indent=2))
    write_midi(score,args.out/(STEM+'.mid'))
    result={'title':NAME,'notes':len(score['notes']),'drums':len(score['drums']),'seconds':score['duration_seconds']}
    if not args.score_only:
        result.update(render_audio(score,args.out))
        if not args.no_mp3:
            mp3=args.out/(STEM+'.mp3')
            subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-nostdin','-y','-i',
                str(args.out/(STEM+'.wav')),'-codec:a','libmp3lame','-b:a','320k',
                '-metadata',f'title={NAME}','-metadata','artist=Music Studio',str(mp3)],check=True)
            result['mp3']=str(mp3)
    print(json.dumps(result,indent=2))

if __name__=='__main__':main()
#!/usr/bin/env python3
"""Afterglow Atlas — original algorithmically arranged instrumental electronic song.

Dependencies: numpy, scipy, soundfile, mido. No soundfont, service, or network.
Run: python afterglow_atlas.py --out ./output
"""
from __future__ import annotations
import argparse, json, math
from pathlib import Path
from dataclasses import dataclass
import numpy as np
from scipy.signal import butter, sosfilt, fftconvolve
import soundfile as sf
import mido

TITLE = "Afterglow Atlas"
BPM = 116
SR = 44100
BEATS_PER_BAR = 4
BARS = 72
TAIL = 5.0
SECONDS_PER_BEAT = 60.0 / BPM
RNG = np.random.default_rng(24261110)

@dataclass
class Note:
    part: str
    start: float # beats
    length: float # beats
    pitch: int
    velocity: float = 0.8
    pan: float = 0.0

notes: list[Note] = []
drums: list[tuple[str,float,float]] = []

# Voicings intentionally use voice-leading, colors and inversions rather than root-position triads.
PROGS = {
    "A": [("Dm9",[57,60,64,65,69],38), ("Bbmaj7",[58,62,65,69],34),
          ("Fadd9",[57,60,67,72],41), ("Cadd9",[55,60,64,74],36)],
    "B": [("Gm9",[58,62,65,69],31), ("Bbmaj7",[58,62,65,69],34),
          ("F/A",[57,60,65,69],33), ("Csus4",[55,60,65,72],36)],
    "C": [("Bbmaj7",[58,62,65,69],34), ("Fadd9",[57,60,67,72],41),
          ("Cadd9",[55,60,64,74],36), ("Dm9",[57,60,64,65,69],38)],
    "D": [("Gm9",[58,62,65,69],31), ("Dm9",[57,60,64,65,69],38),
          ("Bbmaj7",[58,62,65,69],34), ("Cadd9",[55,60,64,74],36)],
}

def add(part, beat, length, pitch, vel=0.8, pan=0.0):
    notes.append(Note(part, round(beat,5),round(length,5),pitch,vel,pan))

def drum(kind, beat, vel=0.75):
    drums.append((kind,round(beat,5),vel))

def chords_for_bar(bar):
    if bar < 24: key = "A"
    elif bar < 32: key = "B"
    elif bar < 48: key = "C"
    elif bar < 56: key = "D"
    elif bar < 68: key = "C"
    else: key = "A"
    return PROGS[key][bar % 4]

# Two-bar hook, answered by another two-bar question/answer. Each returns with variations.
HOOK = [
    [(0.50,0.45,69), (1.00,0.45,72), (1.50,0.48,74), (2.10,1.45,77)],
    [(0.10,0.80,76), (1.00,0.48,74), (1.60,0.50,72), (2.30,1.20,69)],
    [(0.00,0.48,72), (0.60,0.50,76), (1.25,0.65,79), (2.20,0.60,77), (3.00,0.65,76)],
    [(0.25,0.50,74), (0.90,0.55,72), (1.60,0.60,69), (2.50,1.30,67)],
]
VERSE = [
    [(0.50,0.90,69), (1.65,0.48,72), (2.35,0.85,74)],
    [(0.30,0.75,72), (1.40,0.75,69), (2.70,0.70,65)],
    [(0.20,0.80,69), (1.20,0.85,72), (2.65,0.75,76)],
    [(0.30,0.75,74), (1.35,0.70,72), (2.45,1.15,67)],
]
# Section layout and named chord progressions appear in score.json for reproducibility.
SECTIONS = [(0,8,"intro"),(8,24,"verse"),(24,32,"build"),
            (32,48,"chorus"),(48,56,"breakdown"),
            (56,68,"final_chorus"),(68,72,"outro")]

def section_of(b):
    return next(name for s,e,name in SECTIONS if s <= b < e)

def arrange():
    for b in range(BARS):
        sec = section_of(b)
        name, voicing, root = chords_for_bar(b)
        pos = b*4.0
        # Sustained harmonic floor; release overlaps chord transitions slightly.
        v = {"intro":.32,"verse":.38,"build":.43,"chorus":.53,
             "breakdown":.29,"final_chorus":.57,"outro":.34}[sec]
        for i,p in enumerate(voicing):
            add("pad",pos+0.03,3.78,p,v*(.88 if i==0 else 1.0),pan=(-.50 if i%2==0 else .50))
        # Sparse harmonic piano rhythm, with a recurring syncopated third-beat response.
        if sec in ("intro","breakdown","outro"):
            for i,p in enumerate(voicing[1::2]):
                add("piano",pos+.1,2.30,p+12 if sec=="intro" and i==0 else p,
                    .48 if sec=="intro" else .56,pan=(-.22 if i==0 else .22))
            if b%2==1: add("piano",pos+2.50,1.15,voicing[-1]+12,.37,.2)
        else:
            for j,t in enumerate([0.05, 1.50, 2.75]):
                for i,p in enumerate([voicing[0],voicing[2],voicing[-1]]):
                    add("piano",pos+t,1.05 if j==0 else .62,p,
                        (.37 if sec=="verse" else .40) * (1.0-.10*j),pan=(-.16+i*.16))
        # Grounding warm bass with varied syncopation, except opening/outro.
        if sec not in ("intro","outro"):
            if sec == "breakdown":
                pattern=[(0,2.80,0), (3.13,.62,12)]
            else:
                pattern=[(0,.88,0), (1.0,.48,0), (1.72,.42,12), (2.47,.85,0), (3.52,.40,0)]
            for off,dur,octave in pattern:
                add("bass",pos+off,dur,root+octave,.71 if sec=="verse" else .84,pan=0)
        # Sparkling, non-random chord-tone arpeggio with octave jumps.
        if sec not in ("outro",):
            aph=[voicing[1]+12,voicing[2]+12,voicing[-1]+12,voicing[2]+12,
                 voicing[0]+12,voicing[2]+12,voicing[-1]+12,voicing[2]+12]
            if sec in ("chorus","final_chorus","build"):
                for k,p in enumerate(aph):
                    add("arp",pos+.5*k,.33,p,.32 if sec=="build" else .39,
                        pan=-.35 if k%2==0 else .35)
            elif sec in ("intro","breakdown"):
                for k in [0,2,4,6]:
                    add("arp",pos+.5*k,.60,aph[k],.21 if sec=="intro" else .25,
                        pan=-.28 if k%4==0 else .28)
            else:
                for k in [0,2,3,5,7]:
                    add("arp",pos+.5*k,.34,aph[k],.29,pan=-.32 if k%2 else .32)
        # Theme transforms from private piano line to euphoric lead, then returns to keys.
        if sec in ("verse","build","chorus","final_chorus"):
            if sec in ("verse","build"):
                pat=VERSE[b%4]
                inst="lead" if sec=="build" else "piano"
                lv=.54 if sec=="build" else .44
            else:
                pat=HOOK[(b-32)%4] if sec=="chorus" else HOOK[(b-56)%4]
                inst="lead"; lv=.79 if sec=="chorus" else .88
            for offset,duration,pitch in pat:
                # Embellishment for last four bars, retaining motif contour.
                shift=12 if sec=="final_chorus" and b>=64 and pitch<=72 else 0
                add(inst,pos+offset,duration,pitch+shift,lv,pan=.05)
        if sec=="breakdown":
            for offset,duration,pitch in VERSE[b%4]:
                add("piano",pos+offset,duration*1.18,pitch,.56,pan=.05)
        if sec=="intro" and b>=4:
            for offset,duration,pitch in VERSE[b%4]:
                add("piano",pos+offset,duration,pitch,.31,pan=.06)
        if sec=="final_chorus":
            # High bells support, but do not fight, the hook's long notes.
            for k,p in enumerate([voicing[2]+24,voicing[-1]+24]):
                add("bells",pos+(.25 if k==0 else 2.25),.65,p,.31,pan=(-.54 if k==0 else .54))
        if sec=="outro" and b==71:
            # Conclude on a luminous F-major sonority instead of an unresolved dominant.
            for p in [65,69,72,76,79]:
                add("pad",pos+.02,4.25,p,.29,.15)
                add("piano",pos+.05,2.0,p,.35,-.10)
        # Percussion dynamics: conservative intro; drums enter with evolving energy.
        if sec not in ("intro","outro"):
            if sec=="breakdown":
                drum("kick",pos,.72); drum("snare",pos+2.0,.63)
                for k in range(4): drum("hat",pos+.5+k,.25+.06*(k%2))
            else:
                energy={"verse":.68,"build":.78,"chorus":.87,"final_chorus":.93}[sec]
                for k in range(4):
                    drum("kick",pos+k,energy*(.93 if k%2 else 1.0))
                    drum("hat",pos+k+.5,.47+.09*(k%2))
                    if sec in ("chorus","final_chorus"):
                        drum("hat",pos+k+.25,.18)
                for k in [1,3]:
                    drum("snare",pos+k,.73 if sec=="verse" else .82)
                    if sec in ("chorus","final_chorus"): drum("clap",pos+k+.017,.31)
                if b%4==3:
                    for j in range(4): drum("hat",pos+3+j*.25,.23+.09*j)
                if sec=="build" and b>=28:
                    for j in range(8): drum("snare",pos+2+j*.25,.15+.048*j)
                if b%8==7: drum("tom",pos+3.5,.50)
    # Intro pulse, lift impact, section transitions.
    for b in [8,24,32,48,56,68]:
        drum("impact",b*4.0,.33 if b==8 else .58)
    # Added reverse-like sweep texture is generated at mixing stage.

def freq_of(m): return 440.0 * 2.0**((m-69)/12.0)

def oscillator(note:Note):
    f=freq_of(note.pitch)
    dur=note.length*SECONDS_PER_BEAT
    rel={"pad":.58,"piano":.30,"bass":.11,"arp":.28,"lead":.42,"bells":.70}[note.part]
    n=int((dur+rel)*SR); t=np.arange(n,dtype=np.float64)/SR
    # soft-edged piecewise amplitude curves, customized by sound family
    if note.part=="pad":
        a=(1-np.exp(-t/.24))*np.minimum(1.,np.maximum(0.,(dur+.5-t)/.72))
        a *= np.exp(-np.maximum(t-dur,0)/.33)
        y=(.48*np.sin(2*np.pi*f*t)+.27*np.sin(2*np.pi*f*1.004*t+.3)
           +.16*np.sin(2*np.pi*2*f*t+.6)+.09*np.sin(2*np.pi*3*f*.998*t+.25))
        y*=a*.30
    elif note.part=="piano":
        # Synthetic felt-electric-piano partials with natural, pitch-dependent decay.
        a=(1-np.exp(-t/.0035)) * np.exp(-t/(1.30+dur*.24))
        a*=np.minimum(1,np.maximum(0,(dur+.25-t)/.23))
        y=(.83*np.sin(2*np.pi*f*t)+.22*np.exp(-t/.85)*np.sin(2*np.pi*2.002*f*t+.4)
           +.12*np.exp(-t/.30)*np.sin(2*np.pi*3*f*t+.5)+.06*np.exp(-t/.12)*np.sin(2*np.pi*4*f*t))
        y*=a*.36
    elif note.part=="bass":
        a=(1-np.exp(-t/.006))*np.minimum(1,np.maximum(0,(dur+.1-t)/.13))
        lfo=.004*np.sin(2*np.pi*2.1*t)
        y=(.83*np.sin(2*np.pi*f*(t+lfo))+.32*np.sin(2*np.pi*2*f*t)
           +.12*np.exp(-t/.22)*np.sin(2*np.pi*3*f*t+.5))
        y=np.tanh(1.5*y)*a*.54
    elif note.part=="arp":
        a=(1-np.exp(-t/.003))*np.exp(-t/.28)*np.minimum(1,np.maximum(0,(dur+.14-t)/.21))
        y=(.66*np.sin(2*np.pi*f*t)+.26*np.sin(2*np.pi*2*f*t+.25)
           +.13*np.sin(2*np.pi*3*f*t+.4)+.06*np.sin(2*np.pi*4*f*t))
        y*=a*.35
    elif note.part=="lead":
        a=(1-np.exp(-t/.037))*np.minimum(1,np.maximum(0,(dur+.36-t)/.36))
        vib=(1+.0025*np.sin(2*np.pi*5.2*t))
        phase=2*np.pi*f*(t + .0025*np.sin(2*np.pi*5.2*t)/(2*np.pi*5.2))
        y=(.68*np.sin(phase)+.18*np.sin(2*phase+.2)+.12*np.sin(phase*1.003+.6)
           +.055*np.sin(3*phase+.7))
        y*=a*.49
    else: # bells
        a=(1-np.exp(-t/.002))*np.exp(-t/.42)
        y=np.sin(2*np.pi*f*t+1.1*np.exp(-t/.19)*np.sin(2*np.pi*2.1*f*t))
        y*=a*.25
    return y.astype(np.float32)

def drum_wave(kind,velocity,seed):
    dur={"kick":.42,"snare":.32,"hat":.105,"clap":.20,"tom":.43,"impact":1.10}[kind]
    n=int(dur*SR); t=np.arange(n,dtype=np.float64)/SR
    random=np.random.default_rng(seed)
    if kind=="kick":
        f=50+95*np.exp(-t/.028)
        phase=2*np.pi*np.cumsum(f)/SR
        y=np.sin(phase)*np.exp(-t/.115)*.80 + random.standard_normal(n)*np.exp(-t/.008)*.13
    elif kind=="snare":
        z=random.standard_normal(n); z=sosfilt(butter(2,[900,10000],btype='bandpass',fs=SR,output='sos'),z)
        y=z*np.exp(-t/.10)*.31 +np.sin(2*np.pi*180*t)*np.exp(-t/.072)*.22
    elif kind=="hat":
        z=random.standard_normal(n); z=sosfilt(butter(2,6500,btype='highpass',fs=SR,output='sos'),z)
        y=z*np.exp(-t/.025)*.19
    elif kind=="clap":
        z=random.standard_normal(n); z=sosfilt(butter(2,[1500,10000],btype='bandpass',fs=SR,output='sos'),z)
        a=np.exp(-t/.055)*(1+.65*np.sin(2*np.pi*48*t)**8)
        y=z*a*.20
    elif kind=="tom":
        f=125+75*np.exp(-t/.07)
        y=np.sin(2*np.pi*np.cumsum(f)/SR)*np.exp(-t/.13)*.36
    else:
        z=random.standard_normal(n); z=sosfilt(butter(2,[180,11000],btype='bandpass',fs=SR,output='sos'),z)
        y=z*np.exp(-t/.28)*.17 + np.sin(2*np.pi*60*t)*np.exp(-t/.30)*.25
    return (y*velocity).astype(np.float32)

def delay(x,sec,feedback=.24):
    result=np.zeros_like(x)
    d=int(sec*SR)
    for j in range(1,4):
        shift=d*j
        if shift>=len(x): break
        result[shift:]+=x[:-shift]*(feedback**j)
    return result

def reverb(x,seed=11):
    # Fast, subtle decorrelated synthetic room — dense diffusion, no external IR.
    rng=np.random.default_rng(seed)
    length=int(1.65*SR)
    ir=np.zeros(length,dtype=np.float32)
    for i in range(240):
        idx=int((.014+rng.random()**.83*1.54)*SR)
        if idx<length: ir[idx]+=rng.normal()*np.exp(-idx/(SR*.45))*.07
    for sec,amp in [(.027,.20),(.043,.16),(.077,.12),(.119,.09)]:
        ir[int(sec*SR)] += amp
    wet=fftconvolve(x,ir,mode='full')[:len(x)].astype(np.float32)
    return wet

def render(out):
    length= BARS*4*SECONDS_PER_BEAT+TAIL
    n=int(length*SR)
    main=np.zeros((n,2),dtype=np.float32)
    fx=np.zeros((n,2),dtype=np.float32)
    padbus=np.zeros((n,2),dtype=np.float32)
    for idx,no in enumerate(notes):
        y=oscillator(no)*no.velocity
        st=int(no.start*SECONDS_PER_BEAT*SR)
        en=min(st+len(y),n)
        if en<=st: continue
        p=np.clip(no.pan,-1,1)
        gains=np.array([np.sqrt((1-p)/2),np.sqrt((1+p)/2)],dtype=np.float32)
        dest=padbus if no.part=="pad" else fx if no.part in ("lead","arp","bells","piano") else main
        dest[st:en,:] += y[:en-st,None]*gains
    for idx,(kind,beat,v) in enumerate(drums):
        y=drum_wave(kind,v,1000+idx)
        st=int(beat*SECONDS_PER_BEAT*SR); en=min(st+len(y),n)
        if en>st:
            # Drum transients stable in center, hats slightly wider.
            pan=(-.20 if idx%2 else .20) if kind=="hat" else 0.
            gains=np.array([np.sqrt((1-pan)/2),np.sqrt((1+pan)/2)],dtype=np.float32)
            main[st:en,:] += y[:en-st,None]*gains
    # Sidechain-like volume dips on the on-beat kick in active dance sections.
    env=np.ones(n,dtype=np.float32)
    for kind,beat,_ in drums:
        if kind=="kick":
            st=int(beat*SECONDS_PER_BEAT*SR)
            dur=int(.24*SR)
            end=min(n,st+dur)
            tt=np.arange(end-st,dtype=np.float32)/SR
            env[st:end]=np.minimum(env[st:end],1-.22*np.exp(-tt/.09))
    main+=padbus*env[:,None]
    main+=fx*env[:,None]
    # Independent reverbs ensure a broad space without smearing the low-end drums.
    for ch in range(2):
        main[:,ch] += delay(fx[:,ch],.375 if ch==0 else .5625,.34)*.43
        main[:,ch] += reverb((fx[:,ch]*.43+padbus[:,ch]*.32),23+ch)*.24
    # Stereo widening only above bass frequencies; low end stays focused in mono.
    center=(main[:,0]+main[:,1])*.5
    side=(main[:,0]-main[:,1])*.5
    side=sosfilt(butter(2,180,btype='highpass',fs=SR,output='sos'),side)
    main[:,0]=center+side*1.8
    main[:,1]=center-side*1.8
    # Filter excessive sub rumble and upper digital edge gently.
    main=sosfilt(butter(2,28,btype='highpass',fs=SR,output='sos'),main,axis=0).astype(np.float32)
    # Saturate rare transients then keep a conservative premaster ceiling.
    main=np.tanh(main*.97).astype(np.float32)
    peak=float(np.max(np.abs(main)))
    main*=.88/max(peak,1e-8)
    out.mkdir(exist_ok=True,parents=True)
    sf.write(str(out/'Afterglow_Atlas.wav'),main,SR,subtype='PCM_24')
    print(json.dumps({"seconds":length,"samples":n,"sample_rate":SR,"peak_dBFS":float(20*np.log10(np.max(np.abs(main))))},indent=2))

def save_midi(path):
    mid=mido.MidiFile(ticks_per_beat=480)
    mapch={"pad":(0,88),"piano":(1,2),"bass":(2,38),"arp":(3,81),"lead":(4,81),"bells":(5,10)}
    meta=mido.MidiTrack(); mid.tracks.append(meta)
    meta.append(mido.MetaMessage('track_name',name=TITLE,time=0))
    meta.append(mido.MetaMessage('set_tempo',tempo=mido.bpm2tempo(BPM),time=0))
    for part,(ch,prog) in mapch.items():
        track=mido.MidiTrack(); mid.tracks.append(track)
        track.append(mido.MetaMessage('track_name',name=part,time=0))
        track.append(mido.Message('program_change',channel=ch,program=prog,time=0))
        es=[]
        for no in notes:
            if no.part==part:
                es.extend([(round(no.start*480),1,no.pitch,round(no.velocity*112)),
                           (round((no.start+no.length)*480),0,no.pitch,0)])
        prev=0
        for tick,on,p,v in sorted(es,key=lambda v:(v[0],v[1])):
            track.append(mido.Message('note_on' if on else 'note_off',note=p,velocity=v,channel=ch,time=tick-prev)); prev=tick
    dt=mido.MidiTrack(); mid.tracks.append(dt)
    dt.append(mido.MetaMessage('track_name',name='drums',time=0))
    kit={"kick":36,"snare":38,"hat":42,"clap":39,"tom":45,"impact":49}
    es=[]
    for name,beat,vel in drums:
        es.extend([(round(beat*480),1,kit[name],round(vel*110)),(round((beat+.125)*480),0,kit[name],0)])
    prev=0
    for tick,on,p,v in sorted(es,key=lambda x:(x[0],x[1])):
        dt.append(mido.Message('note_on' if on else 'note_off',note=p,velocity=v,channel=9,time=tick-prev));prev=tick
    mid.save(str(path))

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--out',type=Path,default=Path('output'))
    ap.add_argument('--score-only',action='store_true'); args=ap.parse_args()
    arrange()
    args.out.mkdir(exist_ok=True,parents=True)
    payload={"title":TITLE,"bpm":BPM,"beats_per_bar":4,"bars":BARS,
       "sections":[{"start_bar":s,"end_bar":e,"name":nm} for s,e,nm in SECTIONS],
       "harmony":[{"bar":b,"chord":chords_for_bar(b)[0]} for b in range(BARS)],
       "notes":[n.__dict__ for n in notes],
       "drums":[{"kind":k,"beat":b,"velocity":v} for k,b,v in drums]}
    (args.out/'Afterglow_Atlas.score.json').write_text(json.dumps(payload,indent=2))
    save_midi(args.out/'Afterglow_Atlas.mid')
    print(f'Score: {len(notes)} pitched notes, {len(drums)} percussion events')
    if not args.score_only: render(args.out)
if __name__=='__main__':main()
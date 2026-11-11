"""One-directional signal flow: score -> audio notes -> isolated buses -> master.
Instrument modules cannot import the mixer, so swaps do not require rewriting DSP.
"""
import math
from pathlib import Path
import numpy as np
import soundfile as sf
from scipy.signal import butter, sosfilt, resample_poly
from .spec import Note,SR,STEM
from .radio_instruments import note_wave,drum_wave

BUS={'bass':'bass','pluck':'guitar','keys':'keys','pad':'keys','arp':'keys',
     'lead':'lead','counter':'lead','bell':'lead'}
GAIN={'drums':1.05,'bass':.67,'guitar':1.07,'keys':.82,'lead':1.19}


def insert(dest,mono,beat,pan,bpm):
    st=round(max(0,beat)*SR*60/bpm);en=min(len(dest),st+len(mono))
    if en<=st:return
    pan=float(np.clip(pan,-.99,.99))
    dest[st:en,0]+=mono[:en-st]*math.sqrt((1-pan)/2)
    dest[st:en,1]+=mono[:en-st]*math.sqrt((1+pan)/2)


def filter_bus(name,bus):
    filters={
        'drums':('highpass',30), 'bass':('lowpass',1900),
        'guitar':('bandpass',[150,12500]), 'keys':('bandpass',[100,12000]),
        'lead':('bandpass',[190,11600])}
    typ,fc=filters[name]
    return sosfilt(butter(2,fc,fs=SR,btype=typ,output='sos'),bus,axis=0).astype(np.float32)


def stereo_echo(x,delay_a=.27,delay_b=.41):
    wet=np.zeros_like(x)
    for ch,delay in enumerate((delay_a,delay_b)):
        for rep in range(1,4):
            d=int(delay*rep*SR)
            if d<len(x):wet[d:,ch]+=x[:-d,ch]*(.32**rep)
    return wet


def reverb(x):
    """Cheap early room reflections, high-pass filtered to protect the kick and bass."""
    wet=np.zeros_like(x)
    for dsec,amount,left in [(0.061,.18,0),(0.107,.18,1),(.179,.13,0),
                              (.229,.12,1),(.313,.08,0),(.401,.07,1)]:
        n=int(dsec*SR)
        wet[n:,left]+=x[:-n,1-left]*amount
    return filter_bus('lead',wet)


def oversampled_saturation(audio,drive=1.07):
    # 2x oversampling controls nonlinear aliasing from master bus saturation.
    up=resample_poly(audio,2,1,axis=0)
    wet=np.tanh(up*drive)/np.tanh(drive)
    return resample_poly(wet,1,2,axis=0)[:len(audio)].astype(np.float32)


def mix_score(score:dict,out:Path):
    frames=round(score['duration_seconds']*SR);bpm=score['bpm']
    buses={name:np.zeros((frames,2),np.float32) for name in GAIN}
    for n in score['notes']:
        voice=Note(**n)
        insert(buses[BUS[voice.part]],note_wave(voice,bpm,score['seed']),voice.beat,voice.pan,bpm)
    for i,h in enumerate(score['drums']):
        insert(buses['drums'],drum_wave(h['kind'],i%7)*h['velocity'],h['beat'],h['pan'],bpm)
    # 120ms supporting-part duck; never duck the lead.
    duck=np.ones(frames,dtype=np.float32)
    for h in score['drums']:
        if h['kind']!='kick':continue
        st=round(h['beat']*SR*60/bpm);en=min(frames,st+round(.16*SR))
        if en>st:
            t=np.arange(en-st,dtype=np.float32)/SR
            duck[st:en]=np.minimum(duck[st:en],1-.16*np.exp(-t/.065))
    master=np.zeros((frames,2),np.float32)
    for name,bus in buses.items():
        if name in ('guitar','keys'):bus*=duck[:,None]
        conditioned=filter_bus(name,bus)
        if name=='lead':conditioned+=.21*stereo_echo(conditioned)+.14*reverb(conditioned)
        elif name=='keys':conditioned+=.11*stereo_echo(conditioned,.24,.38)
        master+=conditioned*GAIN[name]
        del conditioned
    del buses
    # Stereo width is an independent mix parameter, not baked into the sound engine.
    width=float(score.get('mix',{}).get('stereo_width',1.95))
    if not .75<=width<=3.10:
        raise ValueError('stereo_width must be in [0.75, 3.10]')
    # Low frequency mono and stereo above 145 Hz only.
    mid=(master[:,0]+master[:,1])*.5;side=(master[:,0]-master[:,1])*.5
    side=sosfilt(butter(2,145,fs=SR,btype='highpass',output='sos'),side).astype(np.float32)
    master[:,0]=mid+side*width;master[:,1]=mid-side*width
    master=sosfilt(butter(2,29,fs=SR,btype='highpass',output='sos'),master,axis=0).astype(np.float32)
    # Musical macro-automation with smoothed edges, not global brickwall compression.
    shape=np.ones(frames,dtype=np.float32)
    level={'intro':.98,'verse_a':.88,'pre_a':.99,'chorus_a':1.09,'post':1.00,
           'verse_b':.94,'pre_b':1.01,'chorus_b':1.13,'bridge':.77,'final_chorus':1.18,'outro':.77}
    for sec in score['sections']:
        st=round(sec['start']*4*SR*60/bpm);en=min(frames,round(sec['end']*4*SR*60/bpm))
        shape[st:en]=level[sec['name']]
    shape=sosfilt(butter(1,2.8,fs=SR,btype='lowpass',output='sos'),shape)
    master*=shape[:,None]
    for st in range(0,frames,5*SR):
        en=min(frames,st+5*SR)
        master[st:en]=oversampled_saturation(master[st:en])
    # Master peak ceiling before MP3 encoding; test decoded MP3 separately.
    peak=float(np.max(np.abs(master)))
    master*=.79/max(peak,1e-10)
    fadein=min(round(.025*SR),frames)
    master[:fadein]*=np.linspace(0,1,fadein,dtype=np.float32)[:,None]
    fadeout=min(round(2.65*SR),frames)
    master[-fadeout:]*=np.linspace(1,0,fadeout,dtype=np.float32)[:,None]**1.4
    path=out/(score['stem']+'.wav')
    sf.write(path,master,SR,subtype='PCM_24')
    return {'wav':str(path),'sample_peak_dbfs':round(20*math.log10(max(np.max(np.abs(master)),1e-10)),2)}

"""Small, fully deterministic DSP library. Stereo arrays of float32 at 44.1 kHz.

Effects should solve a musical problem: separation, depth, motion or continuity.
No component modifies the MIDI score or depends on another generative model.
"""
from __future__ import annotations
import numpy as np
from scipy.signal import butter,sosfilt,fftconvolve, resample_poly

SR=44100

def _filter(x,kind,freq,order=2):
    if x.size==0:return x.copy()
    return sosfilt(butter(order,freq,btype=kind,fs=SR,output='sos'),x,axis=0).astype(np.float32)

def highpass(x,freq):return _filter(x,'highpass',freq)
def lowpass(x,freq):return _filter(x,'lowpass',freq)

def sidechain_envelope(frames:int,kick_frames:list[int],depth=.24,release=.18):
    """Soft attenuation only near kick onsets; base gain is 1.0."""
    env=np.ones(frames,dtype=np.float32)
    a=max(1,round(.012*SR));length=max(a+1,round(release*SR))
    t=np.arange(length)
    # onset tapers into a brief gentle duck, then recovers with an exponential.
    curve=1.0-depth*(1-np.exp(-t/max(1,a/3)))*np.exp(-t/(length*.37))
    for onset in kick_frames:
        lo=max(0,onset);hi=min(frames,lo+length)
        if hi>lo: env[lo:hi]=np.minimum(env[lo:hi],curve[:hi-lo])
    return env

def tap_delay(x:np.ndarray,bpm:int,beat_fraction=.75,feedback=.29,wet=.16,stereo=True):
    """Tempo-locked, high-passed, low-passed repeats; no hidden input changes."""
    n=x.shape[0];out=x.copy()
    shift=round(SR*60/bpm*beat_fraction)
    if not 0<shift<n:return out
    filtered=lowpass(highpass(x,270),5200)
    for rep in range(1,5):
        d=shift*rep
        if d>=n:break
        mag=wet*feedback**(rep-1)
        if stereo:
            out[d:,rep%2]+=filtered[:-d,0 if rep%2 else 1]*mag
        else: out[d:]+=filtered[:-d]*mag
    return out.astype(np.float32)

def subtle_chorus(x:np.ndarray,bpm:int,wet=.13,depth_ms=3.2,rate_hz=.32):
    """Slow modulated microdelay, not wholesale fake-wide stereo duplication."""
    n=len(x)
    if not n:return x
    grid=np.arange(n,dtype=np.float64)
    y=x.copy()
    for ch in range(2):
        phase=.5*np.pi*ch
        delay_samples=SR*(.012+depth_ms*.001*np.sin(2*np.pi*rate_hz*grid/SR+phase))
        source=np.maximum(0.,grid-delay_samples)
        y[:,ch]+=(wet*np.interp(source,grid,x[:,ch])).astype(np.float32)
    return y

def tremolo(x:np.ndarray,bpm:int,depth=.16,divisions=2):
    n=len(x);t=np.arange(n,dtype=np.float64)/SR
    phase=2*np.pi*bpm*divisions/60*t
    return (x*(1-depth*(.5-.5*np.cos(phase)))[:,None]).astype(np.float32)

def _room_ir(seed=27,seconds=1.13):
    """Fixed diffuse room IR + early reflections with band-limited tails."""
    n=int(seconds*SR);rng=np.random.default_rng(seed)
    noise=rng.normal(0,1,n).astype(np.float32)
    noise=lowpass(highpass(noise,420),7800)
    t=np.arange(n)/SR
    envelope=np.exp(-t*5.5)*np.maximum(0,np.minimum(1,(t-.022)/.06))
    ir=noise*envelope*.0027
    for at,val in ((.029,.30),(.054,.20),(.077,.16),(.107,.13),(.163,.10)):
        ir[round(at*SR)]+=val
    return ir

def room_send(x:np.ndarray,wet=.11,ir_seconds=1.13):
    """Stereo shared 'room' instead of unrelated reverbs glued onto each patch."""
    if wet==0:return np.zeros_like(x)
    ir_l=_room_ir(43,ir_seconds);ir_r=_room_ir(101,ir_seconds)
    send=lowpass(highpass(x,220),6600)
    y=np.empty_like(x)
    y[:,0]=fftconvolve(send[:,0],ir_l,mode='full')[:len(x)]
    y[:,1]=fftconvolve(send[:,1],ir_r,mode='full')[:len(x)]
    return (wet*y).astype(np.float32)

def saturate(x:np.ndarray,drive=1.11,wet=.18):
    """2x oversampled gentle saturation, deliberately not used on all stems."""
    higher=resample_poly(x,2,1,axis=0)
    nonlinear=np.tanh(higher*drive)/np.tanh(drive)
    shaped=resample_poly(nonlinear,1,2,axis=0)[:len(x)]
    return (x*(1-wet)+shaped*wet).astype(np.float32)

def mono_below(x:np.ndarray,cutoff=135):
    low=lowpass(x,cutoff);high=x-low
    center=low.mean(axis=1,keepdims=True)
    return (high+center).astype(np.float32)

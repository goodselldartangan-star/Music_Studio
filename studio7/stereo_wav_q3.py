"""Q3 optional source-quality 24-bit stereo WAV note renderer.

Isolated from old mono sample banks. Preserve original stereo channels, authored
note timing, velocity, smooth independent note-off, and source pitch/attack.
Only official-style 48 kHz / 24-bit / stereo WAV is accepted; no hidden fallback.
"""
from __future__ import annotations
from fractions import Fraction
from functools import lru_cache
from pathlib import Path

import numpy as np
import soundfile as sf
from scipy.signal import resample_poly
from studio3.spec import SR
from .articulation import smooth_release

GAINS = {'steel': (.48,'acoustic'), 'nylon': (.43,'acoustic'), 'piano': (.39,'piano')}


@lru_cache(maxsize=48)
def _stereo_at_pitch(path:Path,base:int,pitch:int)->np.ndarray:
    """Decode and resample a *stereo* source; never sum channels to mono."""
    path=Path(path)
    with sf.SoundFile(path) as f:
        if (f.format!='WAV' or f.subtype!='PCM_24' or
                f.channels!=2 or f.samplerate!=48000 or len(f)==0):
            raise ValueError(f'Expected original stereo 24-bit/48k WAV: {path.name}')
        samples=f.read(frames=min(len(f),8*f.samplerate),dtype='float32',always_2d=True)
        source_rate=f.samplerate
    if not np.isfinite(samples).all():
        raise ValueError('Nonfinite recorded WAV sample')
    if not 0<=base<=127 or not 0<=pitch<=127 or abs(base-pitch)>4:
        raise ValueError('Requested note is too far from recorded source pitch')
    ratio=Fraction((SR/source_rate)/(2**((pitch-base)/12))).limit_denominator(4096)
    y=resample_poly(samples,ratio.numerator,ratio.denominator,axis=0)
    return np.ascontiguousarray(y,dtype=np.float32)


def render_stereo_wav_note(path:Path,base:int,pitch:int,velocity:int,
                            length:float,bpm:int,*,kind:str)->np.ndarray:
    if kind not in GAINS:
        raise ValueError('Unknown sampled instrument')
    if not 1<=velocity<=127 or length<=0 or bpm<=0:
        raise ValueError('Invalid note parameters')
    gain,part=GAINS[kind]
    source=_stereo_at_pitch(Path(path),base,pitch)
    duration=length*60/bpm
    # Each sample remains independent; this does not reuse/steal sounding voices.
    channels=[smooth_release(source[:,i],duration,part=part,sr=SR) for i in range(2)]
    return np.column_stack(channels).astype(np.float32)*(gain*velocity/127)

"""Small sampler for one externally installed CC0 collection.

Does not change global SampleBank assumptions used by prior Music Studio versions.
"""
from pathlib import Path
from functools import lru_cache
from fractions import Fraction
import math,hashlib
import numpy as np
import soundfile as sf
from scipy.signal import resample_poly
from studio3.sample_bank import NOTE_PATTERN,midi_from_name
from studio3.spec import SR
from .articulation import smooth_release

class Collection:
    def __init__(self,root:Path,name:str):
        self.name=name
        files=sorted((root/name).rglob('*')) if (root/name).exists() else []
        self.regions=[]
        for p in files:
            if not p.is_file() or p.suffix.lower() not in ('.wav','.ogg','.flac'):continue
            match=NOTE_PATTERN.search(p.name)
            if match:self.regions.append((p,midi_from_name(match[2]),int(match[1])))
        if not self.regions:raise FileNotFoundError(f'No {name} recorded samples under {root/name}')
    def render(self,pitch:int,velocity:int,length:float,bpm:int,seed:int,*,region=None):
        if not 0<velocity<128 or length<=0:raise ValueError('Invalid MIDI note')
        maxlayer=max(x[2] for x in self.regions)
        goal=math.ceil(velocity/127*maxlayer)
        d=min((abs(p-pitch),abs(layer-goal)) for _,p,layer in self.regions)
        candidates=[x for x in self.regions if (abs(x[1]-pitch),abs(x[2]-goal))==d]
        if d[0]>4:raise ValueError(f'{self.name}: pitch {pitch} is outside sampled range')
        # Take identity is independent of duration, so articulation A/B keeps the same recording.
        if region is not None:
            if region not in candidates:
                raise ValueError("Requested recorded string is not a valid pitch/velocity-layer candidate")
            path,base,_=region
        else:
            ix=int(hashlib.sha256(f'{seed}:{pitch}:{goal}'.encode()).hexdigest()[:8],16)%len(candidates)
            path,base,_=candidates[ix]
        sample=_resampled(path,base,pitch)
        duration=length*60/bpm
        out=smooth_release(sample,duration,part='acoustic',sr=SR)
        return out*(.43*velocity/127)

@lru_cache(maxsize=80)
def _resampled(path:Path,base:int,pitch:int)->np.ndarray:
    a,sr=sf.read(path,dtype='float32',always_2d=True)
    if not np.isfinite(a).all() or sr<8000:raise ValueError(f'Bad sample {path}')
    mono=a.mean(axis=1)
    rate=2**((pitch-base)/12)
    ratio=Fraction((SR/sr)/rate).limit_denominator(4096)
    return np.ascontiguousarray(resample_poly(mono[:sr*8],ratio.numerator,ratio.denominator),dtype=np.float32)

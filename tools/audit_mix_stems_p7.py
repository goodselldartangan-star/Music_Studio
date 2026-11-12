"""P7 read-only spectral inventory of processed stems (no mix scoring).

Use the actual offline renderer. Band energy ratios describe occupied spectrum,
not psychoacoustic masking or preferred relative loudness.
"""
from __future__ import annotations
import argparse,json,math
from pathlib import Path
import numpy as np
from scipy.signal import welch
from studio7.score import make
from studio7.render import instrument_stems,process_stems
from studio7.effects import SR

BANDS={'sub_bass_35_160':(35,160),'low_mid_160_500':(160,500),
       'mid_500_2000':(500,2000),'presence_2000_8000':(2000,8000)}


def describe_stem(x:np.ndarray)->dict:
    if x.ndim!=2 or x.shape[1]!=2 or not np.isfinite(x).all():
        raise ValueError('Expected finite stereo stem')
    rms=float(np.sqrt(np.mean(x.astype(np.float64)**2))) if len(x) else 0.
    if rms<1e-10:return {'rms_dbfs':-120.,'band_fraction':{b:0. for b in BANDS}}
    m=x.mean(axis=1).astype(np.float64)
    f,P=welch(m,SR,nperseg=min(16384,len(x)))
    valid=(f>=35)&(f<=8000)
    total=max(1e-20,float(np.trapezoid(P[valid],f[valid])))
    fractions={}
    for band,(lo,hi) in BANDS.items():
        indices=(f>=lo)&(f<hi)
        power=float(np.trapezoid(P[indices],f[indices])) if indices.sum()>=2 else 0.
        fractions[band]=round(power/total,5)
    return {'rms_dbfs':round(20*math.log10(rms),2),'band_fraction':fractions}


def inspect_score(score:dict,gm:Path)->dict:
    raw=instrument_stems(score,gm=gm)
    _,processed,_=process_stems(score,raw,with_effects=True)
    report={k:describe_stem(x) for k,x in processed.items()}
    return {'style':score['style'],'stems':report,
            'limitations':'Stem energy inventory only; not a masking or aesthetic rating.'}


def main():
    p=argparse.ArgumentParser();p.add_argument('--gm',type=Path,required=True)
    p.add_argument('--style',default='after',choices=['after','harbor','silver'])
    p.add_argument('--out',type=Path,default=Path('p7_stem_inventory.json'))
    a=p.parse_args()
    report=inspect_score(make(a.style),a.gm)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(report,indent=2))
    print(json.dumps(report,indent=2))


if __name__=='__main__':main()

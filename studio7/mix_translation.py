"""P7 offline mix translation: optional zero-phase side-only low-end mono.

Keep mid (L+R)/2 untouched; filter only side (L-R)/2. Default v7 mixer is
unchanged unless the explicit translation option is selected.
No claim of ideal bass EQ, loudness, or listener preference.
"""
from __future__ import annotations
import math
import numpy as np
from scipy.signal import butter, sosfiltfilt, welch, resample_poly
from studio7.effects import SR


def precise_mono_below(x:np.ndarray,cutoff:float=135)->np.ndarray:
    if x.ndim!=2 or x.shape[1]!=2 or len(x)<32 or not np.isfinite(x).all():
        raise ValueError("Expected finite stereo audio with at least 32 frames")
    if not math.isfinite(cutoff) or not 25<=cutoff<=400:
        raise ValueError("Invalid low-mono crossover")
    mid=(x[:,0].astype(np.float64)+x[:,1].astype(np.float64))*.5
    side=(x[:,0].astype(np.float64)-x[:,1].astype(np.float64))*.5
    sos=butter(4,cutoff,btype='highpass',fs=SR,output='sos')
    filtered=sosfiltfilt(sos,side)
    y=np.stack((mid+filtered,mid-filtered),axis=1)
    return y.astype(np.float32)


def _band_side_metrics(x:np.ndarray,cutoff:float)->tuple[float,float]:
    mid=(x[:,0].astype(np.float64)+x[:,1].astype(np.float64))*.5
    side=(x[:,0].astype(np.float64)-x[:,1].astype(np.float64))*.5
    length=min(len(x),32768)
    f,pm=welch(mid,SR,nperseg=length)
    _,ps=welch(side,SR,nperseg=length)
    mask=f<=cutoff
    if np.count_nonzero(mask)<2:return 0.,-240.
    pm_low=float(np.trapezoid(pm[mask],f[mask]))
    ps_low=float(np.trapezoid(ps[mask],f[mask]))
    # The fraction alone is misleading when mid energy is zero (anti-phase).
    # Record absolute side energy as RMS dBFS too.
    fraction=float(ps_low/max(1e-20,ps_low+pm_low))
    side_dbfs=10*math.log10(max(ps_low,1e-24))
    return fraction,side_dbfs


def mix_translation_metrics(x:np.ndarray,*,cutoff:float=150.,true_peak_rate:int=4)->dict:
    """Return signal-engineering measurements, not a grading score.

    True peak estimated at 4x by polyphase interpolation. Exact codec
    reconstructed true peak can differ; tests use uncompressed PCM fixtures.
    """
    if x.ndim!=2 or x.shape[1]!=2 or len(x)<32 or not np.isfinite(x).all():
        raise ValueError("Expected finite stereo audio")
    if not 25<=cutoff<=400 or true_peak_rate not in (2,4,8):
        raise ValueError("Unsupported mix audit settings")
    # Bound memory on multi-minute material; small chunk overlaps are included
    # to avoid missing intersample peaks at boundaries.
    best=0.
    step=SR
    for at in range(0,len(x),step):
        region=x[max(0,at-64):min(len(x),at+step+64)]
        hi=resample_poly(region,true_peak_rate,1,axis=0)
        best=max(best,float(np.max(abs(hi))))
    sample_peak=float(np.max(abs(x)))
    rms_l=float(np.sqrt(np.mean(x[:,0].astype(np.float64)**2)))
    rms_r=float(np.sqrt(np.mean(x[:,1].astype(np.float64)**2)))
    mid=(x[:,0].astype(np.float64)+x[:,1].astype(np.float64))*.5
    mono_rms=float(np.sqrt(np.mean(mid**2)))
    full_rms=float(np.sqrt(np.mean(x.astype(np.float64)**2)))
    fraction,side_dbfs=_band_side_metrics(x,cutoff)
    return {
        'sample_peak_dbfs':round(20*math.log10(max(sample_peak,1e-12)),3),
        'estimated_true_peak_dbfs':round(20*math.log10(max(best,1e-12)),3),
        'rms_dbfs':round(20*math.log10(max(full_rms,1e-12)),3),
        'balance_db':round(20*math.log10(max(rms_l,1e-12)/max(rms_r,1e-12)),3),
        'mono_rms_delta_db':round(20*math.log10(max(mono_rms,1e-12)/max(full_rms,1e-12)),3),
        'low_side_fraction':round(fraction,6),
        'low_side_rms_dbfs':round(side_dbfs,3),
        'low_side_cutoff_hz':cutoff,
        'limitations':'Technical peaks and band energy do not determine mix quality.'
    }

"""Objective A/B evidence; measurements do not establish musical preference."""
import argparse
import json
from pathlib import Path
import math
import numpy as np
import soundfile as sf
from scipy.signal import welch


def stats(x, sr):
    rms = np.sqrt(np.mean(x*x))
    peak = np.max(np.abs(x))
    xmono = np.mean(x, axis=1)
    hz, spec = welch(xmono, sr, nperseg=min(8192, len(xmono)))
    return {'rms_dbfs': round(20*math.log10(max(rms, 1e-12)), 2),
            'sample_peak_dbfs': round(20*math.log10(max(peak, 1e-12)), 2),
            'spectral_centroid_hz': round(float(np.sum(hz*spec)/max(1e-20,np.sum(spec))), 1)}


def analyze(a, b, out):
    x, sr = sf.read(a, always_2d=True, dtype='float32')
    y, sr2 = sf.read(b, always_2d=True, dtype='float32')
    if sr != sr2 or x.shape != y.shape:
        raise ValueError('A/B format mismatch')
    if x.shape[1] != 2 or not np.isfinite(x).all() or not np.isfinite(y).all():
        raise ValueError('Invalid stereo audio')
    difference = float(np.sqrt(np.mean((x-y)**2)))
    if difference < 1e-4:
        raise AssertionError('Sampled render matches original synthesis too closely: expected timbre change')
    ainfo, binfo = stats(x, sr), stats(y, sr)
    # Normalize segment RMS for listener comparison; preserve source originals.
    rms_a = float(np.sqrt(np.mean(x*x)))
    rms_b = float(np.sqrt(np.mean(y*y)))
    peak_a = float(np.max(np.abs(x)))
    peak_b = float(np.max(np.abs(y)))
    # Choose one common RMS that fits BOTH excerpts below the peak ceiling.
    # Normalizing independently then clipping can leave a misleading level gap.
    target_rms = min(.18, .90 * rms_a / max(peak_a, 1e-9),
                     .90 * rms_b / max(peak_b, 1e-9))
    x = x * (target_rms / max(rms_a, 1e-9))
    y = y * (target_rms / max(rms_b, 1e-9))
    gap = np.zeros((int(sr*.9), 2),dtype=np.float32)
    sf.write(out, np.concatenate([x,gap,y], axis=0),sr,subtype='PCM_24')
    report = {'passed': True, 'format': 'synth first, sampled second, 0.9 sec gap',
              'synth': ainfo, 'sampled':binfo,
              'difference_rms': round(difference,6),
              'ab_common_rms_dbfs': round(20 * math.log10(max(target_rms, 1e-10)), 2),
              'limitation': 'Numbers only show differences, not which timbre listeners prefer.'}
    return report


def main():
    p=argparse.ArgumentParser()
    p.add_argument('synth',type=Path)
    p.add_argument('sampled',type=Path)
    p.add_argument('--out',type=Path,default=Path('previews/AB_synth_then_samples.wav'))
    args=p.parse_args()
    args.out.parent.mkdir(parents=True,exist_ok=True)
    report=analyze(args.synth,args.sampled,args.out)
    (args.out.parent/'comparison.json').write_text(json.dumps(report,indent=2))
    print(json.dumps(report,indent=2))


if __name__=='__main__':main()

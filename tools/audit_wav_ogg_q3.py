"""Q3: verify OGG-preview and WAV-master provenance and matched takes.

Pure research/read-only. ZIPs are supplied explicitly, never fetched at runtime.
Pairs use the complete exact basename, not just MIDI pitch, to preserve physical
string, velocity, round-robin identity. Not a perceptual quality verdict.
"""
from __future__ import annotations
import argparse
import io
import json
import math
from pathlib import Path, PurePosixPath
from zipfile import ZipFile

import numpy as np
import soundfile as sf
from scipy.signal import correlate, correlation_lags


def _manifest(archive: ZipFile, suffix: str) -> dict[str, object]:
    found: dict[str, object] = {}
    for entry in archive.infolist():
        name = PurePosixPath(entry.filename)
        if entry.is_dir() or name.suffix.casefold() != suffix:
            continue
        if name.is_absolute() or '..' in name.parts or entry.file_size > 35_000_000:
            raise ValueError('Unexpected or unsafe sample inside publisher archive')
        key = name.stem.casefold()
        if key in found:
            raise ValueError(f'Conflicting sample identity inside archive: {key}')
        found[key] = entry
    if not found:
        raise ValueError(f'No {suffix} recordings in provided archive')
    return found


def _scan(z: ZipFile, entry: object, seconds: float = 1.4) -> tuple[dict, np.ndarray]:
    data = z.read(entry)
    with sf.SoundFile(io.BytesIO(data)) as audio:
        meta = {'channels': int(audio.channels), 'sample_rate': int(audio.samplerate),
                'subtype': audio.subtype, 'format': audio.format,
                'duration_s': round(len(audio) / audio.samplerate, 4)}
        samples = audio.read(frames=min(len(audio), round(audio.samplerate * seconds)),
                             dtype='float32', always_2d=True)
    if not np.isfinite(samples).all() or not len(samples):
        raise ValueError('Nonfinite or empty publisher audio')
    return meta, samples


def _rms_db(a: np.ndarray) -> float:
    return round(20 * math.log10(max(1e-12, float(np.sqrt(np.mean(a.astype(np.float64)**2))))), 3)


def _match_similarity(wav: np.ndarray, ogg: np.ndarray, sr: int) -> dict:
    """Best raw waveform correlation across +/-60ms in a 1.2s sample prefix.

    High correlation after finding a small time lag indicates a candidate for
    the same performance, not forensic evidence of exact identity.
    """
    n = min(len(wav), len(ogg), round(sr * 1.2))
    if n < round(sr * .2):
        raise ValueError('Insufficient source audio to compare')
    a = wav[:n].mean(axis=1).astype(np.float64)
    b = ogg[:n].mean(axis=1).astype(np.float64)
    a -= a.mean()
    b -= b.mean()
    norm = float(np.linalg.norm(a) * np.linalg.norm(b))
    if norm < 1e-9:
        return {'correlation': 0., 'estimated_offset_ms': 0., 'usable_audio': False}
    xc = correlate(a, b, mode='full', method='fft')
    lags = correlation_lags(n,n,mode='full')
    keep = np.flatnonzero(abs(lags) <= round(.060 * sr))
    arg = keep[int(np.argmax(xc[keep]))]
    return {'correlation': round(float(xc[arg] / norm),5),
            'estimated_offset_ms': round(float(lags[arg] * 1000 / sr),2),
            'usable_audio': True}


def _channel_info(pcm: np.ndarray) -> dict:
    mid = pcm.mean(axis=1).astype(np.float64)
    if pcm.shape[1] == 1:
        side = np.zeros_like(mid)
    else:
        side = ((pcm[:,0].astype(np.float64) - pcm[:,1].astype(np.float64)) * .5)
    ratio = float(np.sqrt(np.mean(side*side)) / max(1e-12, np.sqrt(np.mean(mid*mid))))
    return {'mid_rms_dbfs': _rms_db(mid), 'side_to_mid_rms': round(ratio,5)}


def inspect_pair(ogg_zip: ZipFile, ogg_entry: object, wav_zip: ZipFile, wav_entry: object) -> dict:
    wav_info, w = _scan(wav_zip,wav_entry)
    ogg_info, o = _scan(ogg_zip,ogg_entry)
    out = {'identity': PurePosixPath(wav_entry.filename).stem,
           'wav': {**wav_info, **_channel_info(w)},
           'ogg': {**ogg_info, **_channel_info(o)}}
    if wav_info['sample_rate'] != ogg_info['sample_rate']:
        out['comparison'] = {'status': 'sample_rate_mismatch'}
        return out
    sim = _match_similarity(w,o,wav_info['sample_rate'])
    length_diff = abs(wav_info['duration_s'] - ogg_info['duration_s'])
    out['comparison'] = {**sim, 'duration_difference_s': round(length_diff,4),
        'candidate_same_take': (sim['usable_audio'] and sim['correlation']>=.68
                                and length_diff <= .12)}
    return out


def compare_archives(ogg_path: Path, wav_path: Path, *, max_pairs: int = 12) -> dict:
    if not 2 <= max_pairs <= 30:
        raise ValueError('Select between 2 and 30 study recordings')
    with ZipFile(ogg_path) as ogg_zip, ZipFile(wav_path) as wav_zip:
        oggs = _manifest(ogg_zip, '.ogg')
        wavs = _manifest(wav_zip, '.wav')
        matched = sorted(set(oggs) & set(wavs))
        if not matched:
            raise ValueError('No exact file-basename matches between publisher archives')
        chosen = [matched[i] for i in np.linspace(0,len(matched)-1,
                                                  min(max_pairs,len(matched)),dtype=int)]
        results = [inspect_pair(ogg_zip,oggs[k],wav_zip,wavs[k]) for k in chosen]
        same = sum(bool(x['comparison'].get('candidate_same_take')) for x in results)
        return {
            'ogg_archive': ogg_path.name, 'wav_archive': wav_path.name,
            'ogg_bytes': ogg_path.stat().st_size, 'wav_bytes': wav_path.stat().st_size,
            'ogg_file_count': len(oggs), 'wav_file_count': len(wavs),
            'same_filename_pairs': len(matched),
            'unpaired_ogg_examples': sorted(set(oggs)-set(wavs))[:8],
            'unpaired_wav_examples': sorted(set(wavs)-set(oggs))[:8],
            'tested_pairs': results,
            'candidate_same_take_count': same,
            'checked_pair_count': len(results),
            'wav_channel_counts': {str(c):sum(r['wav']['channels']==c for r in results)
                                   for c in sorted({r['wav']['channels'] for r in results})},
            'ogg_channel_counts': {str(c):sum(r['ogg']['channels']==c for r in results)
                                   for c in sorted({r['ogg']['channels'] for r in results})},
            'conclusion_limit': ('Exact basenames plus waveform similarity are evidence for same-take identity, '
                                 'not a blind listening verdict. No audio is changed.')}


def main() -> None:
    p=argparse.ArgumentParser()
    p.add_argument('--ogg',type=Path,required=True)
    p.add_argument('--wav',type=Path,required=True)
    p.add_argument('--max-pairs',type=int,default=12)
    p.add_argument('--out',type=Path,default=Path('q3_source_comparison.json'))
    args=p.parse_args()
    result=compare_archives(args.ogg,args.wav,max_pairs=args.max_pairs)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,indent=2))
    compact={k:v for k,v in result.items() if k!='tested_pairs'}
    compact['pairs']=[{'identity':x['identity'], 'wav_channels':x['wav']['channels'],
                       'wav_format':x['wav']['subtype'],
                       'correlation':x['comparison'].get('correlation'),
                       'estimated_offset_ms':x['comparison'].get('estimated_offset_ms'),
                       'same_take_candidate':x['comparison'].get('candidate_same_take')}
                      for x in result['tested_pairs']]
    print(json.dumps(compact,indent=2))


if __name__=='__main__':
    main()

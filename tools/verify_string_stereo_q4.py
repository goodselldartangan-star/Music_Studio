"""Q4: combine Q2 physically mapped strings and Q3 original stereo sources.

Use real published score notes and exact matching OGG/WAV performed takes.
This is an isolated recorded-instrument integration, not a finished mix.
"""
from __future__ import annotations
import argparse
import json
import math
import subprocess
from pathlib import Path

import numpy as np
import soundfile as sf

from studio3.sample_bank import SampleBank
from studio7.effects import SR
from studio7.samples import Collection
from studio7.score import make
from studio7.render import _sample_meta
from studio7.string_mapping import plan_guitar_samples, shape_harbor_bm_guitar


def _recorded_regions(root: Path, style: str):
    if style == 'silver':
        return Collection(root, 'meta-nylon-guitar').regions
    return SampleBank(root).regions['meta-steel-guitar']


def _identity(region):
    """Identity independent of codec extension and install directory."""
    if hasattr(region, 'path'):
        return (region.path.stem, int(region.midi), int(region.layer))
    return (Path(region[0]).stem, int(region[1]), int(region[2]))


def _rms(y):
    return float(np.sqrt(np.mean(y.astype(np.float64)**2)))


def compare(ogg: Path, wav: Path, out: Path) -> dict:
    out=Path(out)
    out.mkdir(parents=True,exist_ok=True)
    reports={}
    for style in ('harbor','silver'):
        original=make(style)
        score, voicing=shape_harbor_bm_guitar(original)
        assert original['drums']==score['drums']
        assert all(a==b for a,b in zip(
            (n for n in original['notes'] if n['instrument'] != 'acoustic'),
            (n for n in score['notes'] if n['instrument'] != 'acoustic')))
        guitar=[n for n in score['notes'] if n['instrument']=='acoustic']
        regions_ogg=_recorded_regions(ogg,style)
        regions_wav=_recorded_regions(wav,style)
        chosen_ogg, mapping_ogg=plan_guitar_samples(guitar,regions_ogg,
                                                    seed_base=score['bars']*43)
        chosen_wav, mapping_wav=plan_guitar_samples(guitar,regions_wav,
                                                    seed_base=score['bars']*43)
        ogg_ids=[_identity(x) for x in chosen_ogg]
        wav_ids=[_identity(x) for x in chosen_wav]
        if len(ogg_ids)!=len(guitar) or ogg_ids != wav_ids:
            mismatch=next(((i,a,b) for i,(a,b) in enumerate(zip(ogg_ids,wav_ids))
                           if a!=b),None)
            raise AssertionError(f'{style}: mono/stereo guitar took different performed takes: {mismatch}')
        if mapping_ogg['remaining_intra_strum_string_conflicts']!=0:
            raise AssertionError(f'{style}: conflicting physical strings in OGG plan')
        if mapping_wav['remaining_intra_strum_string_conflicts']!=0:
            raise AssertionError(f'{style}: conflicting physical strings in WAV plan')
        if (mapping_ogg['mapped_distinct_strums'] != mapping_wav['mapped_distinct_strums']
                or mapping_wav['unmapped_strums'] != 0):
            raise AssertionError(f'{style}: string plan differs or is incomplete')
        if mapping_wav['mapped_distinct_strums']!= (32 if style=='harbor' else 4):
            raise AssertionError(f'{style}: unexpected strum inventory')

        mono=_sample_meta(score,'acoustic',ogg,string_aware=True)
        stereo=_sample_meta(score,'acoustic',wav,string_aware=True,stereo_wav=True)
        if mono.shape!=stereo.shape or not np.isfinite(stereo).all():
            raise AssertionError(f'{style}: malformed stereo guitar stem')
        if float(np.max(abs(mono[:,0]-mono[:,1])))>1e-7:
            raise AssertionError(f'{style}: historical mono recording changed')
        side=_rms((stereo[:,0]-stereo[:,1])*.5)
        if side<=1e-7:
            raise AssertionError(f'{style}: no original stereo information retained')
        if _rms(stereo)<1e-7 or _rms(mono)<1e-7:
            raise AssertionError('Unexpected silent guitar')
        # Check real piano is independent of Q2 guitar mapping, even with WAV.
        piano_original=_sample_meta(original,'piano',wav,stereo_wav=True)
        piano_revoiced=_sample_meta(score,'piano',wav,stereo_wav=True)
        if not np.array_equal(piano_original,piano_revoiced):
            raise AssertionError(f'{style}: guitar string mapping altered piano samples')
        # An excerpt containing recorded strums, not an arbitrary silent segment.
        start_sec=48*60/score['bpm'] if style=='silver' else 0.
        start=round(start_sec*SR)
        length=round(11*SR)
        before=mono[start:start+length]
        after=stereo[start:start+length]
        target=_rms(before)
        if target<1e-6:
            raise AssertionError(f'{style}: quiet comparison excerpt')
        gained={}
        for label,source in (('ogg',before),('wav',after)):
            factor=min(1.4,max(.7,target/max(_rms(source),1e-10)))
            factor=min(factor,.82/max(float(np.max(np.abs(source))),1e-10))
            gained[label]=(source*factor).astype(np.float32)
        matched_db=20*math.log10(max(_rms(gained['wav']),1e-12)
                                / max(_rms(gained['ogg']),1e-12))
        if abs(matched_db)>.5:
            raise AssertionError(f'{style}: excerpt volume not matched: {matched_db:.2f}dB')
        for label,audio in gained.items():
            dest=out/f'Q4_{style}_{label}.mp3'
            wav_tmp=out/f'Q4_{style}_{label}.wav'
            sf.write(wav_tmp,audio,SR,subtype='PCM_24')
            subprocess.run(['ffmpeg','-nostdin','-hide_banner','-loglevel','error','-y',
                            '-i',str(wav_tmp),'-c:a','libmp3lame','-b:a','224k',str(dest)],
                           check=True)
            wav_tmp.unlink()
        reports[style]={
            'guitar_note_count':len(guitar),
            'string_mapped_strums':mapping_wav['mapped_distinct_strums'],
            'unmapped_strums':mapping_wav['unmapped_strums'],
            'string_conflicts':mapping_wav['remaining_intra_strum_string_conflicts'],
            'wav_and_ogg_exact_take_matches':len(guitar),
            'guitar_voicing':voicing,
            'wav_stereo_side_rms_dbfs':round(20*math.log10(max(side,1e-12)),2),
            'excerpt_start_s':round(start_sec,3),
            'excerpt_duration_s':round(len(before)/SR,2),
            'excerpt_rms_difference_db':round(matched_db,3),
            'piano_preserved_by_string_mapping':True,
            'original_score_untouched':True,
        }
    result={'scores':reports,'source_edit':'None', 'original_release_edit':'None',
            'limitations':'Source mapping and PCM/MP3 decoding measured, no human sound-quality preference asserted.'}
    (out/'Q4_combined_source_report.json').write_text(json.dumps(result,indent=2))
    print(json.dumps(result,indent=2))
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--ogg-assets',type=Path,required=True)
    parser.add_argument('--wav-assets',type=Path,required=True)
    parser.add_argument('--out',type=Path,default=Path('q4-combined-preview'))
    args=parser.parse_args()
    compare(args.ogg_assets,args.wav_assets,args.out)

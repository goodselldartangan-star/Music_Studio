"""Q3 short, level-matched mono OGG vs original stereo WAV sampled-note A/B.

Only acoustic/nylon/piano notes are rendered. No full-song remix or release.
The exact published note identities and score are selected by the same sampler.
"""
from __future__ import annotations
import argparse,json,math,subprocess
from pathlib import Path
import numpy as np
import soundfile as sf
from studio7.effects import SR
from studio7.render import _sample_meta

PHRASES={
 'steel':('harbor','acoustic',[(50,.35,2.2,81),(54,.39,1.6,71),(57,.43,1.5,74),(62,.47,1.35,67),(50,1.1,.22,65)]),
 'piano':('after','piano',[(60,.2,2.1,72),(64,.21,1.7,77),(67,.23,1.4,85),(60,1.0,.30,62)]),
 'nylon':('silver','acoustic',[(52,.35,1.9,65),(55,.39,1.45,72),(59,.43,1.3,70),(64,.47,1.25,69),(52,1.15,.21,58)]),
}


def _rms(x):return float(np.sqrt(np.mean(x.astype(np.float64)**2)))


def run(ogg_root:Path,wav_root:Path,out:Path):
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    report={}
    for label,(style,part,notes) in PHRASES.items():
        score={'style':style,'bars':16,'bpm':110,'duration':7.5,
               'notes':[dict(instrument=part,pitch=p,beat=b,length=l,velocity=v)
                        for p,b,l,v in notes]}
        old=_sample_meta(score,part,ogg_root,string_aware=(label!='piano'))
        new=_sample_meta(score,part,wav_root,string_aware=(label!='piano'),stereo_wav=True)
        if old.shape!=new.shape or not np.isfinite(new).all():
            raise AssertionError('Unequal or invalid instrument stems')
        old_side=_rms((old[:,0]-old[:,1])*.5)
        new_side=_rms((new[:,0]-new[:,1])*.5)
        if new_side<old_side+1e-8:
            raise AssertionError(f'{label}: expected stereo source detail not present')
        if old_side>1e-8:
            raise AssertionError(f'{label}: old mono OGG unexpectedly had a stereo side')
        target=_rms(old)
        mixes={}
        for version,payload in (('ogg',old),('wav',new)):
            r=_rms(payload)
            if r<1e-7:raise AssertionError('Silent instrument recording')
            gain=min(1.4,max(.7,target/r))
            gain=min(gain,.86/max(1e-9,float(np.max(np.abs(payload)))))
            y=(payload*gain).astype(np.float32)
            mixes[version]=y
            dest=out/f'Q3_{label}_{version}.wav'
            mp3=out/f'Q3_{label}_{version}.mp3'
            sf.write(dest,y,SR,subtype='PCM_24')
            subprocess.run(['ffmpeg','-nostdin','-hide_banner','-v','error','-y',
                            '-i',str(dest),'-c:a','libmp3lame','-b:a','224k',str(mp3)],check=True)
        report[label]={
            'notes':len(notes),'duration_s':len(old)/SR,
            'ogg_side_rms_dbfs':round(20*math.log10(max(1e-12,old_side)),2),
            'wav_side_rms_dbfs':round(20*math.log10(max(1e-12,new_side)),2),
            'matched_rms_diff_db':round(20*math.log10(_rms(mixes['wav'])/_rms(mixes['ogg'])),3),
            'wav_mid_vs_ogg_mid_correlation':round(float(np.corrcoef(old.mean(axis=1),new.mean(axis=1))[0,1]),5)
        }
        if abs(report[label]['matched_rms_diff_db'])>.4:
            raise AssertionError(f'{label}: A/B not matched in loudness')
    result={'matched_sampled_instrument_phrases':report,
            'note':'Technical A/B, original mono OGG and original stereo WAV source; no musical taste asserted.'}
    (out/'Q3_short_comparison.json').write_text(json.dumps(result,indent=2))
    print(json.dumps(result,indent=2))
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--ogg-assets',type=Path,required=True)
    p.add_argument('--wav-assets',type=Path,required=True)
    p.add_argument('--out',type=Path,default=Path('q3-stereo-ab'))
    a=p.parse_args();run(a.ogg_assets,a.wav_assets,a.out)

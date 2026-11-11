"""Strict but modest engineering checks; never claims listeners like a song."""
from __future__ import annotations
import argparse,json,subprocess,math
from pathlib import Path
import numpy as np
import soundfile as sf
from studio3.performance import PROFILES


def verify(root:Path,expect_samples=False)->list[dict]:
    rows=[];waveforms=[]
    metrics_path=root/'results.json'
    if not metrics_path.exists():raise FileNotFoundError(metrics_path)
    byname={x['profile']:x for x in json.loads(metrics_path.read_text())}
    for name in PROFILES:
        report=byname[name]
        stem=f'Music_Studio_Example_{name.title()}'
        wav=root/name/(stem+'.wav');mp3=root/name/(stem+'.mp3')
        if not wav.is_file() or not mp3.is_file():raise AssertionError(f'Missing master for {name}')
        y,sr=sf.read(wav,dtype='float32',always_2d=True)
        duration=len(y)/sr
        expected=report['duration_seconds']
        assert sr==44100 and y.shape[1]==2 and np.isfinite(y).all(), name
        assert abs(duration-expected)<.025, name
        peak=float(np.max(np.abs(y)))
        assert 0.02<peak<.9, name
        rms=float(np.sqrt(np.mean(y*y)))
        assert .008<rms<.3, name
        left=np.sqrt(np.mean(y[:,0]**2));right=np.sqrt(np.mean(y[:,1]**2))
        balance=20*math.log10(left/max(right,1e-12))
        assert abs(balance)<3.5, (name,balance)
        # Decode every MP3 rather than simply trusting the file extension.
        subprocess.run(['ffmpeg','-nostdin','-v','error','-xerror','-i',str(mp3),'-f','null','-'],check=True,capture_output=True)
        if expect_samples:
            assert report['sampled_drums']>=20, (name,report['sampled_drums'])
            assert report['sampled_notes']>=20, (name,report['sampled_notes'])
        rows.append({'example':name,'seconds':round(duration,2),'peak_dbfs':round(20*math.log10(peak),2),
                     'rms_dbfs':round(20*math.log10(rms),2),'balance_db':round(balance,2),
                     'sampled_notes':report['sampled_notes'],'sampled_drums':report['sampled_drums']})
        # Use a stereo averaged excerpt to test that each music example differs materially.
        mono=y[::6].mean(axis=1).astype(np.float32)
        waveforms.append(mono)
    for i in range(len(waveforms)):
        for j in range(i+1,len(waveforms)):
            n=min(len(waveforms[i]),len(waveforms[j]))
            corr=float(np.corrcoef(waveforms[i][:n:8],waveforms[j][:n:8])[0,1])
            assert abs(corr)<.95,(rows[i]['example'],rows[j]['example'],corr)
    return rows


def main():
    p=argparse.ArgumentParser();p.add_argument('root',type=Path)
    p.add_argument('--require-samples',action='store_true')
    a=p.parse_args()
    result=verify(a.root,a.require_samples)
    (a.root/'verification.json').write_text(json.dumps(result,indent=2))
    print(json.dumps(result,indent=2))

if __name__=='__main__':main()

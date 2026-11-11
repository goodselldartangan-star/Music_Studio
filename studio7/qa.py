"""Objective, independent audio QA. Does NOT pretend to grade human musical taste."""
from __future__ import annotations
from pathlib import Path
import subprocess,json,math
import numpy as np
import soundfile as sf
from scipy.signal import welch

def inspect(path:Path)->dict:
    path=Path(path)
    data=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_entries',
        'stream=sample_rate,channels:format=duration','-of','json',str(path)],text=True))
    channels=data['streams'][0]['channels']
    sr=int(data['streams'][0]['sample_rate'])
    duration=float(data['format']['duration'])
    assert sr==44100 and channels==2 and 28<duration<47, f'Unexpected MP3 properties: {sr} {channels} {duration}'
    pipe=subprocess.run(['ffmpeg','-nostdin','-hide_banner','-v','error','-xerror',
       '-i',str(path),'-f','f32le','-acodec','pcm_f32le','-ac','2','-ar','44100','pipe:1'],
       capture_output=True,check=True)
    x=np.frombuffer(pipe.stdout,'<f4').reshape(-1,2)
    assert np.isfinite(x).all() and len(x)>28*44100
    pk=float(np.max(np.abs(x)));rms=float(np.sqrt(np.mean(x*x)))
    balance=float(20*np.log10(max(1e-9,np.sqrt(np.mean(x[:,0]**2)))/max(1e-9,np.sqrt(np.mean(x[:,1]**2)))))
    corr=float(np.corrcoef(x[::256,:].T)[0,1])
    assert 0.001<rms<.4 and pk<.995 and abs(balance)<3 and corr>-.15, (rms,pk,balance,corr)
    # Gross spectral hazards, not a preferred commercial spectral curve.
    f,P=welch(x[::2,0],22050,nperseg=8192)
    total=max(1e-12,np.trapezoid(P,f))
    sub=float(np.trapezoid(P[f<25],f[f<25])/total)
    assert sub<.08, f'Rumble: {sub}'
    return dict(filename=path.name,duration_s=round(duration,2),rms_dbfs=round(20*math.log10(rms),2),
                sample_peak_dbfs=round(20*math.log10(pk),2),balance_db=round(balance,2),
                stereo_correlation=round(corr,3),subsonic_fraction=round(sub,4),passed=True,
                limitations='This is technical QA; no perceptual listening claim.')

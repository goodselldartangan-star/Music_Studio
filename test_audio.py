"""Objective engineering QA for Afterglow Atlas (not a substitute for human audition)."""
import json, math
from pathlib import Path
import numpy as np
import soundfile as sf
from scipy.signal import welch
import mido
root=Path(__file__).parent/'output'
sig,sr=sf.read(root/'Afterglow_Atlas.wav',dtype='float32',always_2d=True)
score=json.loads((root/'Afterglow_Atlas.score.json').read_text())
assert sr==44100 and sig.shape[1]==2 and np.isfinite(sig).all()
assert 153 < len(sig)/sr < 155
assert len(score['notes'])>1000 and len(score['drums'])>500
assert max(abs(sig.min()),abs(sig.max())) <= .9
assert np.mean(np.abs(sig)>0.997)<1e-8
assert any(x['name']=='final_chorus' for x in score['sections'])
assert set(x['chord'] for x in score['harmony']) >= {'Dm9','Bbmaj7','Fadd9','Cadd9'}
mid=mido.MidiFile(root/'Afterglow_Atlas.mid')
assert len(mid.tracks)==8
# Approximate per-section RMS, channel balance, correlation, digital-silence checks.
spb=60/score['bpm']; sections=[]
for s in score['sections']:
    x=sig[int(s['start_bar']*4*spb*sr):int(s['end_bar']*4*spb*sr)]
    rms=float(np.sqrt(np.mean(x*x)))
    sections.append({'section':s['name'],'seconds':round(len(x)/sr,2),'rms_dbfs':round(20*math.log10(max(rms,1e-10)),2)})
assert -35 < sections[0]['rms_dbfs'] < -10
assert sections[3]['rms_dbfs'] > sections[1]['rms_dbfs']
assert sections[5]['rms_dbfs'] > sections[4]['rms_dbfs']
ch_rms=np.sqrt(np.mean(sig*sig,axis=0)); balance=20*np.log10(ch_rms[0]/ch_rms[1]); assert abs(balance)<2.0
corr=np.corrcoef(sig[::32,0],sig[::32,1])[0,1]
assert -.5<corr<.999
# Check subsonic energy fraction and high frequencies are bounded.
from scipy.signal import welch
f,P=welch(sig[:,0],sr,nperseg=16384)
tot=np.trapezoid(P,f)
sub=np.trapezoid(P[f<30],f[f<30])/tot
hi=np.trapezoid(P[f>12000],f[f>12000])/tot
assert sub<.015 and hi<.12
print(json.dumps({'passed':True,'duration_sec':round(len(sig)/sr,3),'true_sample_peak_dBFS':round(float(20*np.log10(np.max(np.abs(sig)))),2),
  'channel_balance_dB':round(float(balance),3),'stereo_correlation':round(float(corr),3),
  'energy_below_30Hz_fraction':round(float(sub),4),'energy_above_12kHz_fraction':round(float(hi),4),
  'sections':sections},indent=2))
"""Strict mechanical QA, not an opinion about musical quality."""
from __future__ import annotations
import math,subprocess
from pathlib import Path
import numpy as np
import soundfile as sf


def inspect(wav:Path,mp3:Path,expected:float)->dict:
    if not wav.is_file() or not mp3.is_file():raise FileNotFoundError('Master missing')
    y,sr=sf.read(wav,dtype='float32',always_2d=True)
    if sr!=44100 or y.shape[1]!=2 or abs(len(y)/sr-expected)>.04:raise AssertionError('Wrong sample rate/channels/duration')
    if not np.isfinite(y).all():raise AssertionError('Corrupt audio')
    peak=float(np.max(np.abs(y)));rms=float(np.sqrt(np.mean(y*y)))
    if not .06<=peak<=.92 or not .002<=rms<=.24:raise AssertionError(f'Invalid level: peak {peak}, rms {rms}')
    ch=np.sqrt(np.mean(y*y,axis=0)); balance=20*math.log10(ch[0]/max(ch[1],1e-10))
    if abs(balance)>=4.0:raise AssertionError('Channel imbalance')
    p=subprocess.run(['ffmpeg','-nostdin','-loglevel','error','-xerror','-i',str(mp3),'-f','null','-'],capture_output=True)
    if p.returncode:raise AssertionError(f'MP3 decode error: {p.stderr[:400]}')
    return {'duration':len(y)/sr,'peak_dbfs':20*math.log10(peak),'rms_dbfs':20*math.log10(rms),
            'channel_balance_db':balance,'decoded_mp3':True,'passed':True}

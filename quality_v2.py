#!/usr/bin/env python3
"""Objective song delivery gates for Music Studio v2; no subjective quality claim."""
import argparse
import json
import math
from pathlib import Path
import re
import subprocess
import numpy as np
import soundfile as sf
from scipy.signal import welch
import mido

STEM='Porchlight_Receiver'


def loudness_statistics(wav):
    result=subprocess.run(['ffmpeg','-hide_banner','-nostdin','-loglevel','info',
        '-i',str(wav),'-af','ebur128=peak=true','-f','null','-'],
        check=True,capture_output=True,text=True)
    report=result.stderr.rsplit('Summary:',1)[-1]
    measures={}
    patterns={'integrated_lufs':r'Integrated loudness:\s*I:\s*([-+\d.]+)\s*LUFS',
              'loudness_range_lu':r'Loudness range:\s*LRA:\s*([-+\d.]+)\s*LU',
              'true_peak_dbtp':r'True peak:\s*Peak:\s*([-+\d.]+)\s*dBFS'}
    for key,pattern in patterns.items():
        m=re.search(pattern,report)
        if not m:raise ValueError(f'Could not parse FFmpeg {key}')
        measures[key]=float(m.group(1))
    return measures


def validate(out, *, require_full=True):
    score=json.loads((out/(STEM+'.score.json')).read_text())
    wav=out/(STEM+'.wav');mp3=out/(STEM+'.mp3');midi=out/(STEM+'.mid')
    assert wav.is_file() and mp3.is_file() and midi.is_file(), 'Missing final delivery file'
    assert score['bars']==88 if require_full else 1 <=score['bars']<=88
    sections=score['sections']
    assert sections[0]['start']==0 and sections[-1]['end']==score['bars']
    assert all(x['end']==y['start'] for x,y in zip(sections,sections[1:])), 'Section timeline broken'
    if require_full:
        assert set(s['name'] for s in sections)>={'verse_one','chorus_one','bridge','final_chorus'}
        assert len(score['notes'])>2000 and len(score['drums'])>1000
    assert len(score['chords'])==score['bars']
    assert all(0 <= n['beat'] < score['bars']*4 for n in score['notes'])
    mid=mido.MidiFile(midi)
    assert len(mid.tracks)==10, 'Missing MIDI instruments'
    with sf.SoundFile(wav) as f:
        assert f.channels==2 and f.samplerate==44100
        assert f.subtype=='PCM_24'
        assert abs(len(f)/f.samplerate-score['duration_seconds']) < .03
        sr=f.samplerate
        channels=[0.,0.];count=0;peak=0.;last=None;pieces=[]
        # Whole-track reading is fine at 44.1k and <4min, but chunking is safer.
        for block in f.blocks(blocksize=44100,dtype='float32',always_2d=True):
            assert np.isfinite(block).all(), 'NaN/Inf audio'
            peak=max(peak,float(np.max(np.abs(block))))
            channels[0]+=float(np.sum(block[:,0]**2));channels[1]+=float(np.sum(block[:,1]**2))
            count+=len(block)
            if len(pieces)*sr < 30*sr:pieces.append(block[:min(len(block),sr)].copy())
            last=block
    assert .45<peak<.96, f'Unreasonable peak {peak:.3f}'
    balance=10*math.log10(channels[0]/channels[1])
    assert abs(balance)<1.5, f'Stereo imbalance {balance:.2f} dB'
    rms=math.sqrt(sum(channels)/(2*count))
    rmsdb=20*math.log10(max(rms,1e-9))
    assert -24<rmsdb<-10, f'RMS level {rmsdb:.1f}'
    assert last is not None and float(np.sqrt(np.mean(last[-min(8000,len(last)):]**2)))<.005,'End tail is too loud'
    excerpt=np.concatenate(pieces)
    corr=np.corrcoef(excerpt[::16,0],excerpt[::16,1])[0,1]
    assert .05 < corr < .9999, f'Stereo phase {corr:.3f}'
    f,p=welch(excerpt[:,0],sr,nperseg=16384)
    total=np.trapezoid(p,f)
    def fraction(low,hi):
        mask=(f>=low)&(f<hi)
        return float(np.trapezoid(p[mask],f[mask])/total)
    sub=fraction(0,30);bass=fraction(30,120);presence=fraction(1000,6000);air=fraction(6000,19000)
    assert sub<.03, f'Subsonic rumble {sub:.3f}'
    if require_full:
        assert .08<bass<.80, f'Bass energy {bass:.3f}'
        assert .01<presence<.50, f'Presence energy {presence:.3f}'
    assert air<.35, f'Harsh high-frequency energy {air:.3f}'
    # Decode entire MP3; reject any decode warnings treated as errors.
    subprocess.run(['ffmpeg','-hide_banner','-nostdin','-v','error','-xerror',
                    '-i',str(mp3),'-f','null','-'],check=True,capture_output=True)
    info=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration',
            '-of','json',str(mp3)],text=True))
    assert abs(float(info['format']['duration'])-count/sr)<.20
    loud=loudness_statistics(wav)
    if require_full:
        assert -19.5<loud['integrated_lufs']<-10.5, f'Loudness out of range: {loud}'
    assert loud['true_peak_dbtp'] < -1.0, f'True peak too high: {loud}'
    if require_full:
        assert 3.0 < loud['loudness_range_lu'] < 18.0, f'Dynamics outside reasonable limits: {loud}'
    # Full song per-section RMS. These verify form, not human enjoyment.
    levels={}
    with sf.SoundFile(wav) as f:
        for section in sections:
            start=round(section['start']*4*60/score['bpm']*sr)
            stop=round(section['end']*4*60/score['bpm']*sr)
            f.seek(start)
            part=f.read(stop-start,dtype='float32')
            levels[section['name']]=round(20*math.log10(max(1e-9,np.sqrt(np.mean(part**2)))),2)
    if require_full:
        assert levels['chorus_one'] > levels['verse_one']+1.5, 'Chorus did not lift'
        assert levels['final_chorus'] > levels['bridge']+2.5, 'Final chorus did not lift'
    return {'passed':True,'title':score['title'],'duration_seconds':round(count/sr,3),
            'notes':len(score['notes']),'drum_hits':len(score['drums']),'sample_peak_dbfs':round(20*math.log10(peak),2),
            'rms_dbfs':round(rmsdb,2),'stereo_balance_db':round(balance,2),
            'stereo_correlation_30s':round(float(corr),3),
            'sub_0_30':round(sub,4),'bass_30_120':round(bass,4),
            'presence_1k_6k':round(presence,4),'air_6k_19k':round(air,4),
            'section_rms_dbfs':levels,'ffmpeg_loudness':loud,
            'note':'Objective file and audio-engineering checks. No subjective listening or musical-quality guarantee.'}


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('out',type=Path,nargs='?',default=Path('output_v2'))
    ap.add_argument('--preview',action='store_true')
    args=ap.parse_args()
    result=validate(args.out,require_full=not args.preview)
    (args.out/'quality_v2.json').write_text(json.dumps(result,indent=2))
    print(json.dumps(result,indent=2))

if __name__=='__main__':main()
#!/usr/bin/env python3
"""Offline, reproducible checks for Music Studio's original synthesized song.

Audio engineering acceptance checks are NOT a human listening test.
"""
import argparse
import json
import math
import subprocess
from pathlib import Path
import numpy as np
import soundfile as sf
from scipy.signal import welch
import mido

STEM='Streetlight_Letters'

def check(out: Path):
    score=json.loads((out/f'{STEM}.score.json').read_text())
    wav=out/f'{STEM}.wav'; mp3=out/f'{STEM}.mp3'; midi=out/f'{STEM}.mid'
    assert wav.exists() and mp3.exists() and midi.exists(), 'A deliverable is missing'
    assert score['bpm']==116 and score['bars']==100
    sections=score['sections']
    assert sections[0]['start_bar']==0 and sections[-1]['end_bar']==100
    assert all(a['end_bar']==b['start_bar'] for a,b in zip(sections,sections[1:]))
    assert set(s['name'] for s in sections)>={'verse_one','verse_two','chorus_one','last_chorus','bridge'}
    assert len(score['notes'])>2000 and len(score['drums'])>1200
    assert all(n['pitch']>=25 and n['pitch']<=108 for n in score['notes'])
    assert len(score['chords'])==score['bars']
    midi_data=mido.MidiFile(midi)
    assert len(midi_data.tracks)==10 and len(midi_data.tracks[5])>20
    signal,rate=sf.read(wav,dtype='float32',always_2d=True)
    assert rate==44100 and signal.shape[1]==2
    duration=len(signal)/rate
    assert abs(duration-score['duration_seconds'])<.02 and 205<duration<215
    assert np.isfinite(signal).all(), 'NaN or infinity'
    peak=float(np.max(np.abs(signal)))
    assert .7<peak<=.91, 'Failed peak ceiling'
    assert not np.any(np.abs(signal)>.997), 'Digital clipping'
    overall_rms=np.sqrt(np.mean(signal*signal))
    db=20*math.log10(overall_rms)
    assert -23<db<-10, 'Unacceptable sound level'
    channels=np.sqrt(np.mean(signal*signal,axis=0))
    balance=float(20*np.log10(channels[0]/channels[1]))
    assert abs(balance)<1.8, 'Stereo imbalance'
    corr=float(np.corrcoef(signal[::50,0],signal[::50,1])[0,1])
    assert .25<corr<.999, 'Stereo phase / mono compatibility risk'
    section_levels={}
    for s in sections:
        st=int((s['start_bar']*4*60/score['bpm'])*rate)
        en=int((s['end_bar']*4*60/score['bpm'])*rate)
        w=signal[st:en]
        val=float(20*np.log10(max(1e-10,np.sqrt(np.mean(w*w)))))
        section_levels[s['name']]=round(val,2)
    assert section_levels['chorus_one'] > section_levels['verse_one']+1.0
    assert section_levels['last_chorus'] > section_levels['verse_two']+1.0
    assert section_levels['last_chorus'] > section_levels['bridge']+2.0
    assert section_levels['opening'] < section_levels['chorus_one']-4.0
    # Frequency weighting: avoid both weak bass and muddy high-frequency absence.
    freq,power=welch(signal[:,0],rate,nperseg=16384)
    total=np.trapezoid(power,freq)
    def band(a,b):
        valid=(freq>=a)&(freq<b)
        return float(np.trapezoid(power[valid],freq[valid])/total)
    low=band(30,120); presence=band(1000,6000); air=band(6000,20000)
    assert .16<low<.70, f'Bass energy out of range: {low}'
    assert .04<presence<.45, f'Presence energy out of range: {presence}'
    assert air<.20, 'Excessively harsh treble'
    assert band(0,30)<.018, 'Subsonic rumble'
    tail=signal[-int(.3*rate):]
    tail_db=20*math.log10(max(1e-10,np.sqrt(np.mean(tail*tail))))
    assert tail_db<-42, 'Abrupt or overly loud ending'
    duration_probe=subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration',
        '-of','default=noprint_wrappers=1:nokey=1',str(mp3)],text=True)
    mp3_duration=float(duration_probe.strip())
    assert abs(duration-mp3_duration)<.20, 'MP3 differs from the render'
    subprocess.run(['ffmpeg','-nostdin','-v','error','-xerror','-i',str(mp3),
        '-f','null','-'],check=True,capture_output=True)
    return {
        'passed':True,'name':score['name'],'seconds':round(duration,3),
        'song_sections':len(sections),'notes':len(score['notes']),'drum_hits':len(score['drums']),
        'WAV_peak_dBFS':round(20*math.log10(peak),2),
        'WAV_RMS_dBFS':round(float(db),2),
        'stereo_balance_dB':round(balance,2),'stereo_correlation':round(corr,3),
        'bass_energy_fraction':round(low,3),'presence_energy_fraction':round(presence,3),
        'upper_frequency_energy_fraction':round(air,3),
        'tail_RMS_dBFS':round(tail_db,2),
        'MP3_seconds':round(mp3_duration,3),
        'section_RMS_dBFS':section_levels,
        'notes_on_validation':'Checks technical integrity and arrangement, not subjective musical taste.'
    }

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('out',type=Path,nargs='?',default=Path('output'))
    a=p.parse_args()
    result=check(a.out)
    (a.out/'audio_quality.json').write_text(json.dumps(result,indent=2))
    print(json.dumps(result,indent=2))

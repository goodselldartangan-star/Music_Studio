"""Independent acceptance gate: detects damaged media and mix engineering faults.
A green result does NOT mean that an algorithm evaluated musical taste.
"""
import json,math,re,subprocess
from pathlib import Path
import numpy as np
import soundfile as sf
import mido
from scipy.signal import welch
from .spec import STEM,SR,BARS


def _loudness(path):
    r=subprocess.run(['ffmpeg','-hide_banner','-nostdin','-loglevel','info','-i',str(path),
                      '-af','ebur128=peak=true','-f','null','-'],capture_output=True,text=True,check=True)
    s=r.stderr.rsplit('Summary:',1)[-1]
    pat={'integrated_lufs':r'Integrated loudness:\s*I:\s*([-+\d.]+)\s*LUFS',
         'loudness_range_lu':r'Loudness range:\s*LRA:\s*([-+\d.]+)\s*LU',
         'true_peak_dbtp':r'True peak:\s*Peak:\s*([-+\d.]+)\s*dBFS'}
    values={}
    for k,p in pat.items():
        m=re.search(p,s)
        if not m:raise AssertionError('Missing ffmpeg loudness summary '+k)
        values[k]=float(m.group(1))
    return values


def validate(out:Path,full=True):
    score=json.loads((out/(STEM+'.score.json')).read_text())
    wav=out/(STEM+'.wav');mp3=out/(STEM+'.mp3');midi=out/(STEM+'.mid')
    for f in (wav,mp3,midi):assert f.is_file() and f.stat().st_size>0,f'Missing {f}'
    if full:assert score['bars']==BARS
    else:assert 1<=score['bars']<=BARS
    sections=score['sections']
    assert sections[0]['start']==0 and sections[-1]['end']==score['bars']
    assert all(a['end']==b['start'] for a,b in zip(sections,sections[1:])), 'Noncontiguous section boundaries'
    assert len(score['chords'])==score['bars']
    if full:
        assert {'chorus_a','verse_a','bridge','chorus_b'}<=set(s['name'] for s in sections)
        assert len(score['notes'])>2300 and len(score['drums'])>900
    assert all(0<=n['beat']<score['bars']*4 for n in score['notes'])
    mf=mido.MidiFile(midi);assert len(mf.tracks)==10
    with sf.SoundFile(wav) as f:
        assert f.samplerate==SR and f.channels==2 and f.subtype=='PCM_24'
        seconds=len(f)/SR
        assert abs(seconds-score['duration_seconds'])<.02
        peak=0;energies=np.zeros(2);samples=0;head=[];last=None
        for block in f.blocks(blocksize=SR,dtype='float32',always_2d=True):
            assert np.isfinite(block).all(), 'NaN/Inf samples'
            peak=max(peak,float(np.max(np.abs(block))))
            energies+=np.sum(block.astype(np.float64)**2,axis=0)
            samples+=len(block)
            if len(head)<28:head.append(block.copy())
            last=block
    assert .30<peak<.96, f'Extreme sample peak: {peak}'
    balance=10*math.log10(energies[0]/energies[1]);assert abs(balance)<1.4
    rmsdb=10*math.log10(np.sum(energies)/(samples*2))
    assert -27<rmsdb<-8,f'RMS out of range {rmsdb}'
    assert np.sqrt(np.mean(last[-min(8000,len(last)):]**2))<.008,'Tail does not decay'
    excerpt=np.concatenate(head)
    corr=np.corrcoef(excerpt[::16,0],excerpt[::16,1])[0,1]
    assert -.1<corr<.9999,f'Stereo correlation: {corr}'
    f,p=welch(excerpt[:,0],SR,nperseg=16384)
    total=np.trapezoid(p,f)
    def ratio(a,b):
        sel=(f>=a)&(f<b)
        return float(np.trapezoid(p[sel],f[sel])/total)
    low=ratio(35,150);high=ratio(3000,10000);sub=ratio(0,30)
    assert sub<.035,'Subsonic rumble'
    assert high<.40,'Excessive treble'
    subprocess.run(['ffmpeg','-nostdin','-v','error','-xerror','-i',str(mp3),'-f','null','-'],check=True,capture_output=True)
    dat=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration','-of','json',str(mp3)],text=True))
    assert abs(float(dat['format']['duration'])-seconds)<.15
    loud=_loudness(wav)
    assert loud['true_peak_dbtp'] < -1.0,'Inter-sample clipping risk'
    if full:
        assert -19.5<loud['integrated_lufs']<-10.0,'Out-of-range loudness'
        assert 2<loud['loudness_range_lu']<19,'Unreasonable dynamics'
    levels={}
    with sf.SoundFile(wav) as f:
        for s in sections:
            lo=round(s['start']*4*60/score['bpm']*SR);hi=round(s['end']*4*60/score['bpm']*SR)
            f.seek(lo);chunk=f.read(hi-lo,dtype='float32')
            levels[s['name']]=round(20*math.log10(max(1e-10,np.sqrt(np.mean(chunk**2)))),2)
    if full:
        assert levels['chorus_a']>levels['verse_a']+1,'Chorus does not lift above verse'
        assert levels['chorus_b']>levels['bridge']+2,'Final chorus does not lift above bridge'
    return {'passed':True,'title':score['title'],'seconds':round(seconds,3),
            'notes':len(score['notes']),'drum_hits':len(score['drums']),
            'sample_peak_dbfs':round(20*math.log10(peak),2),
            'rms_dbfs':round(rmsdb,2),'stereo_balance_db':round(balance,3),
            'stereo_correlation_first_28s':round(float(corr),3),
            'low_35_150':round(low,4),'high_3000_10000':round(high,4),
            'section_rms_dbfs':levels,'loudness':loud,
            'limits':'Objective QC only. Does not establish subjective musical quality.'}

"""Tests symbolic composition first, then measured signal and media integrity.
Passing tests isn't a claim of human listening or commercial success.
"""
import json,math,subprocess,re
from pathlib import Path
import numpy as np
import soundfile as sf
from scipy.signal import welch
import mido
from .spec import SR
def _loudness(path):
    proc=subprocess.run(['ffmpeg','-hide_banner','-nostdin','-v','info','-i',str(path),
                         '-af','ebur128=peak=true','-f','null','-'],capture_output=True,text=True,check=True)
    summary=proc.stderr.rsplit('Summary:',1)[-1]
    patterns={'integrated_lufs':r'Integrated loudness:\s*I:\s*([-+\d.]+)\s*LUFS',
              'loudness_range_lu':r'Loudness range:\s*LRA:\s*([-+\d.]+)\s*LU',
              'true_peak_dbtp':r'True peak:\s*Peak:\s*([-+\d.]+)\s*dBFS'}
    result={}
    for key,pat in patterns.items():
        match=re.search(pat,summary)
        if match is None:raise AssertionError('missing loudness metric: '+key)
        result[key]=float(match.group(1))
    return result
from .radio_composition import CHORDS,KEY_PCS,BARS,SECTIONS

def signature(score,bar):
    return tuple((round(n['beat']-bar*4,2),n['pitch'],round(n['duration'],2))
                 for n in score['notes'] if n['part']=='lead' and bar*4<=n['beat']<(bar+1)*4)

def audit_score(score):
    assert score['bars']<=BARS and score['bars']>0
    assert all(c['chord'] in CHORDS for c in score['chords'])
    assert len(score['chords'])==score['bars']
    assert all(n['pitch']%12 in KEY_PCS for n in score['notes'] if n['part']=='lead'), 'lead out of key'
    assert all(0<=n['beat']<score['bars']*4 for n in score['notes'])
    assert all(0<=d['beat']<score['bars']*4 for d in score['drums'])
    if score['bars']>=92:
        # Recognizable chorus downbeat, but purposeful development in later repetitions.
        assert signature(score,24)==signature(score,60)==signature(score,80)
        comparisons={}
        for x,y,start in [(4,40,'verses'),(24,60,'choruses'),(24,80,'final_hook')]:
            matches=sum(signature(score,x+i)==signature(score,y+i) for i in range(12))
            comparisons[start]={'identical_bars':matches,'total':12}
            assert matches<=9, f'{start} too repetitive ({matches}/12)'
    else:comparisons={}
    assert len(score['sections'])>0 and score['sections'][0]['start']==0
    assert score['sections'][-1]['end']==score['bars']
    assert all(a['end']==b['start'] for a,b in zip(score['sections'],score['sections'][1:]))
    return {'passed':True,'song':score['title'],'bars':score['bars'],'notes':len(score['notes']),
            'drums':len(score['drums']),'phrase_variations':comparisons}

def check_audio(folder,score,full=True):
    folder=Path(folder);stem=score['stem']
    wav=folder/(stem+'.wav');mp3=folder/(stem+'.mp3');midi=folder/(stem+'.mid')
    for f in (wav,mp3,midi):assert f.is_file() and f.stat().st_size>300, f'Missing {f}'
    m=mido.MidiFile(midi);assert len(m.tracks)==10
    with sf.SoundFile(wav) as f:
        assert f.samplerate==SR and f.channels==2 and f.subtype=='PCM_24'
        assert abs(len(f)/SR-score['duration_seconds'])<.03
        peak=0;energy=np.zeros(2);head=[];last=None
        for block in f.blocks(blocksize=SR,dtype='float32',always_2d=True):
            assert np.isfinite(block).all()
            peak=max(peak,float(np.max(np.abs(block))))
            energy+=np.sum(block.astype(np.float64)**2,axis=0)
            if len(head)<25:head.append(block.copy())
            last=block
    assert .20<peak<.95
    balance=10*math.log10(energy[0]/energy[1]);assert abs(balance)<1.6
    assert np.sqrt(np.mean(last[-min(7000,len(last)):]**2))<.015
    excerpt=np.concatenate(head)
    corr=float(np.corrcoef(excerpt[::16,0],excerpt[::16,1])[0,1]);assert -.1<corr<.9999
    freqs,p=welch(excerpt[:,0],SR,nperseg=16384)
    total=np.trapezoid(p,freqs)
    def band(a,b):
        i=(freqs>=a)&(freqs<b)
        return float(np.trapezoid(p[i],freqs[i])/total)
    assert band(0,30)<.035
    subprocess.run(['ffmpeg','-nostdin','-v','error','-xerror','-i',str(mp3),'-f','null','-'],check=True,capture_output=True)
    info=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration','-of','json',str(mp3)],text=True))
    assert abs(float(info['format']['duration'])-score['duration_seconds'])<.15
    loud=_loudness(wav)
    mp3_loud=_loudness(mp3)
    assert loud['true_peak_dbtp']<-1.0, loud
    assert mp3_loud['true_peak_dbtp']<-.5, mp3_loud
    if full:
        assert -20<loud['integrated_lufs']<-10, loud
        assert 3<loud['loudness_range_lu']<19,loud
    levels={}
    with sf.SoundFile(wav) as f:
        for sec in score['sections']:
            lo=round(sec['start']*4*SR*60/score['bpm']);hi=round(sec['end']*4*SR*60/score['bpm'])
            f.seek(lo);data=f.read(hi-lo,dtype='float32',always_2d=True)
            levels[sec['name']]=round(20*math.log10(max(1e-9,np.sqrt(np.mean(data*data)))),2)
    if full:
        assert levels['chorus_a']>levels['verse_a']+1.0, levels
        assert levels['final_chorus']>levels['bridge']+2.0, levels
    return {'passed':True,'duration_sec':round(score['duration_seconds'],2),
      'sample_peak_dbfs':round(20*math.log10(peak),2),'balance_dB':round(balance,2),
      'stereo_correlation_first25':round(corr,3),'subsonic_fraction':round(band(0,30),5),
      'loudness':loud,'mp3_loudness':mp3_loud,'section_rms_dBFS':levels,
      'limitation':'objective tests, not a human listening evaluation'}

"""Render recorded performers to separate stems and mix conservatively."""
from __future__ import annotations
import argparse,json,math,subprocess
from pathlib import Path
import numpy as np
import soundfile as sf
from scipy.signal import butter,sosfilt
from .score import make,STYLES
from .soundfonts import render_sf2,SR

DRUM_PITCH={'kick':36,'snare':38,'hat':42,'open_hat':46,'tom':45,'rim':37,'crash':49}


def sample_meta(score,kind:str,root:Path):
    """Reuse v5 Meta SampleBank contract without cloning that code."""
    from studio3.sample_bank import SampleBank
    from studio3.spec import Note
    bank=SampleBank(root)
    part={'acoustic':'pluck','piano':'keys'}[kind]
    if not bank.has(part):raise FileNotFoundError(f'{kind} samples missing at {root}')
    frames=round(score['seconds']*SR)
    out=np.zeros((frames,2),dtype=np.float32)
    for i,n in enumerate(x for x in score['notes'] if x['instrument']==kind):
        event=Note(part,n['beat'],n['length'],n['pitch'],n['velocity']/127,.0)
        sample=bank.render_note(event,score['bpm'],score['bars']*997+i)
        st=round(n['beat']*60/score['bpm']*SR)
        en=min(frames,st+len(sample))
        if en<=st:continue
        # Recorded mono guitar and piano spaced naturally, without hard artificial widening.
        pan=(.23 if kind=='acoustic' else -.12)
        out[st:en,0]+=sample[:en-st]*math.sqrt((1-pan)/2)
        out[st:en,1]+=sample[:en-st]*math.sqrt((1+pan)/2)
    return out


def render(score,assets:Path,out:Path,strict:bool=True):
    frames=round(score['seconds']*SR);out.mkdir(parents=True,exist_ok=True)
    fonts={p:assets/'sf2'/f'{p}.sf2' for p in ('electric','bass','drums')}
    for name,path in fonts.items():
        if not path.is_file():raise FileNotFoundError(f'Missing recorded {name}: {path}')
    stems={}
    for name in ('electric','bass'):
        stems[name]=render_sf2(fonts[name],[n for n in score['notes'] if n['instrument']==name],score['seconds'],score['bpm'])
    hits=[{'beat':h['beat'],'length':.13,'pitch':DRUM_PITCH[h['kind']],'velocity':h['velocity']} for h in score['drums']]
    stems['drums']=render_sf2(fonts['drums'],hits,score['seconds'],score['bpm'],drum=True)
    for name in ('acoustic','piano'):
        stems[name]=sample_meta(score,name,assets)
    # Five stems available separately for diagnostics and future edits.
    for name,signal in stems.items():
        if name in ('bass','drums') and np.sqrt(np.mean(signal*signal)) < .00015:
            raise AssertionError(f'Recorded {name} instrument rendered silence; inspect its soundfont bank/preset')
    volumes={
       'porch': {'acoustic':1.08,'piano':.54,'electric':.67,'bass':.88,'drums':.80},
       'city':  {'acoustic':.06,'piano':.38,'electric':1.0,'bass':.89,'drums':.98},
       'night': {'acoustic':.70,'piano':1.06,'electric':.03,'bass':.62,'drums':.66},
    }[score['style']]
    # Trim low end where inappropriate. Keep actual recorded attack and stereo stereo ambience.
    for name,signal in stems.items():
        cutoff=30 if name in ('bass','drums') else 85 if name in ('acoustic','electric') else 50
        stems[name]=sosfilt(butter(2,cutoff,fs=SR,btype='highpass',output='sos'),signal,axis=0).astype(np.float32)
        # Export each stem for inspecting actual instrument isolation.
        sf.write(out/f'{score["style"]}-{name}.wav',stems[name],SR,subtype='PCM_16')
    mixed=sum(stems[n]*volumes[n] for n in stems)
    # Gentle envelope instead of global sound-changing compression.
    attack=min(frames,round(.18*SR));tail=min(frames,round(1.4*SR))
    mixed[:attack]*=np.linspace(0,1,attack,dtype=np.float32)[:,None]
    mixed[-tail:]*=np.linspace(1,0,tail,dtype=np.float32)[:,None]
    peak=float(np.max(abs(mixed)))
    assert peak>0.001 and np.isfinite(mixed).all(), 'Silent or invalid master'
    mixed *= .79/peak
    wav=out/f'{score["style"]}-real.wav'
    mp3=out/f'{score["style"]}-real.mp3'
    sf.write(wav,mixed,SR,subtype='PCM_24')
    subprocess.run(['ffmpeg','-nostdin','-hide_banner','-v','error','-y','-i',str(wav),'-c:a','libmp3lame','-b:a','256k',str(mp3)],check=True)
    return {'style':score['style'],'title':score['title'],'wav':str(wav),'mp3':str(mp3), 'duration':score['seconds'],
            'notes':len(score['notes']),'drums':len(score['drums']), 'peak_dbfs':20*math.log10(float(np.max(abs(mixed))))}


def main():
    p=argparse.ArgumentParser(description='Offline recorded-band previews (not another AI)')
    p.add_argument('--assets',type=Path,default=Path('assets/v6'))
    p.add_argument('--out',type=Path,default=Path('v6-demos'))
    p.add_argument('--style',choices=STYLES,default=None)
    a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
    outputs=[]
    for kind in [a.style] if a.style else STYLES:
        score=make(kind)
        (a.out/f'{kind}.score.json').write_text(json.dumps(score,indent=2))
        report=render(score,a.assets,a.out)
        outputs.append(report)
    (a.out/'render_report.json').write_text(json.dumps(outputs,indent=2))
    print(json.dumps(outputs,indent=2))

if __name__=='__main__':main()

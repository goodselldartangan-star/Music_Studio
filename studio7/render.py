"""Arrange instrument stems with intentional roles, then process them independently.

Sample selection is backend-specific. All production, EQ and effects work on isolated
stereo stems and can be changed without editing scores or shared data formats.
"""
from __future__ import annotations
from pathlib import Path
import math,subprocess,json
import numpy as np
import soundfile as sf
from .score import make,validate,SONGS
from .effects import highpass,lowpass,room_send,tap_delay,subtle_chorus,tremolo,sidechain_envelope,saturate,mono_below,SR
from studio6.soundfonts import FluidSynth,render_sf2
from .articulation import render_polyphonic,render_meta_note
from .samples import Collection
from .playing import shape_strums
from .bass_performance import shape_bass
from .piano_performance import shape_piano
from .rhythm import shape_pocket
from .drum_dynamics import shape_drum_dynamics
from .registers import separate_lead_piano
from .melody import shape_final_answer
from .mix_translation import precise_mono_below

DRUM_MAP={'kick':36,'snare':38,'hat':42,'open_hat':46,'tom':45,'rim':37,'crash':49}
GM_PROGRAM={'acoustic':25,'electric':27,'piano':0,'bass':33,'lead':26,'drums':0}
REAL_PARTS={'electric','bass','drums','acoustic','piano'}

# Gains in RMS dBFS across the full duration, not indiscriminate peak normalization.
# Different instruments will intentionally sit at different depths in each style.
DB_TARGET={
 'harbor':{'acoustic':-23.5,'electric':-25.0,'piano':-32.5,'bass':-25.0,'drums':-25.5,'lead':-24.0},
 'after':{'acoustic':-40.0,'electric':-27.7,'piano':-29.5,'bass':-24.2,'drums':-23.8,'lead':-23.0},
 'silver':{'acoustic':-34.0,'electric':-27.8,'piano':-24.0,'bass':-28.0,'drums':-30.0,'lead':-25.0},
}


def _render_with_gm(path:Path,notes:list[dict],seconds:float,bpm:int,part:str):
    if part!='drums':
        return render_polyphonic(path,notes,seconds,bpm,part=part,program=GM_PROGRAM[part])
    # Percussion groups such as open/closed hats deliberately retain drum choking.
    fs=FluidSynth(path,gain=.33,drum=True)
    try:
        evt=[{'at':n['beat']*60/bpm,'off':(n['beat']+n['length'])*60/bpm,
              'pitch':n['pitch'],'velocity':n['velocity']} for n in notes]
        return fs.render(evt,round(seconds*SR))
    finally: fs.close()


def _sample_meta(score:dict,part:str,assets:Path):
    # Reuse the existing CC0 Meta sampler; that module owns sample parsing.
    from studio3.sample_bank import SampleBank
    from studio3.spec import Note
    bank=SampleBank(assets)
    if part=='acoustic' and score['style']=='silver':
        collection=Collection(assets,'meta-nylon-guitar')
        frames=round(score['duration']*SR);dest=np.zeros((frames,2),dtype=np.float32)
        for i,n in enumerate(x for x in score['notes'] if x['instrument']==part):
            raw=collection.render(n['pitch'],n['velocity'],n['length'],score['bpm'],i+int(n['beat']*100))
            st=round(n['beat']*60/score['bpm']*SR);en=min(frames,st+len(raw))
            if en>st:dest[st:en]+=raw[:en-st,None]*.7071
        return dest
    key={'acoustic':'pluck','piano':'keys'}[part]
    if not bank.has(key):raise FileNotFoundError(f'Missing CC0 {key} samples in {assets}')
    frames=round(score['duration']*SR);dest=np.zeros((frames,2),dtype=np.float32)
    for i,n in enumerate(x for x in score['notes'] if x['instrument']==part):
        voice=Note(key,n['beat'],n['length'],n['pitch'],n['velocity']/127,0)
        raw=render_meta_note(bank,voice,score['bpm'],score['bars']*43+i)
        start=round(n['beat']*60/score['bpm']*SR)
        end=min(frames,start+len(raw))
        if end>start:
            dest[start:end,:]+=raw[:end-start,None]*.7071
    return dest


def instrument_stems(score:dict,assets:Path|None=None,gm:Path|None=None)->dict:
    """Real backend: v6 downloaded CC0/CC-BY soundfonts + Meta samples.
    Portable offline fallback: system GM SoundFont only, explicitly labeled.
    """
    if assets is None and gm is None:raise ValueError('Choose real sampled assets or local GM fallback')
    if assets is not None and gm is not None:raise ValueError('Do not mix backends implicitly')
    out={}
    notes=score['notes'];dur=score['duration'];bpm=score['bpm']
    for name in ('bass','acoustic','electric','piano','lead'):
        active=[n for n in notes if n['instrument']==name]
        if not active:
            out[name]=np.zeros((round(dur*SR),2),np.float32)
            continue
        if gm:
            out[name]=_render_with_gm(gm,active,dur,bpm,name)
        elif name in ('acoustic','piano'):
            out[name]=_sample_meta(score,name,assets)
        else:
            font=assets/'sf2'/('bass_picked.sf2' if name=='bass' and score['style']=='after' else f'{"electric" if name=="lead" else name}.sf2')
            out[name]=render_polyphonic(font,active,dur,bpm,part=name,program=0)
    hits=[{'beat':h['beat'],'length':.135,'pitch':DRUM_MAP[h['kind']],'velocity':h['velocity']} for h in score['drums']]
    if hits:
        out['drums']=_render_with_gm(gm,hits,dur,bpm,'drums') if gm else render_sf2(assets/'sf2/drums.sf2',hits,dur,bpm,drum=True)
    else:
        out['drums']=np.zeros((round(dur*SR),2),np.float32)
    for name,a in out.items():
        if not np.isfinite(a).all():raise AssertionError(f'Invalid samples in {name}')
        if a.shape!=(round(dur*SR),2):raise AssertionError('stem shape mismatch')
    return out


def _target_gain(x:np.ndarray,db:float):
    rms=float(np.sqrt(np.mean(np.square(x,dtype=np.float64))))
    if rms<2e-7:return x.copy(),0.0
    gain=float(10**(db/20)/rms)
    gain=min(gain,17.)  # refuse to amplify unexpectedly quiet or mis-mapped soundfont indefinitely
    return (x*gain).astype(np.float32),gain


def process_stems(score:dict,raw:dict,with_effects=True,room_predelay_ms=0.,precise_low_mono=False)->tuple[np.ndarray,dict,dict]:
    style=score['style'];bpm=score['bpm']
    frames=round(score['duration']*SR)
    kick_frames=[round(h['beat']*60/bpm*SR) for h in score['drums'] if h['kind']=='kick']
    duck=sidechain_envelope(frames,kick_frames,depth=.24 if style=='after' else .14,release=.19)
    out={};gain_report={}
    for name in ('drums','bass','acoustic','electric','piano','lead'):
        s=raw.get(name,np.zeros((frames,2),np.float32)).copy()
        # Transparent per-role filtering; do not use the same 'full spectrum' for every sound.
        if name=='bass': s=lowpass(highpass(s,37),2500)
        elif name=='drums':s=highpass(s,30)
        elif name=='acoustic':s=lowpass(highpass(s,135),11800)
        elif name=='electric':s=lowpass(highpass(s,168),7900)
        elif name=='lead':s=lowpass(highpass(s,200),8800)
        else:s=lowpass(highpass(s,95),11400)
        s,g=_target_gain(s,DB_TARGET[style][name]);gain_report[name]=round(g,3)
        if name=='bass':
            s*=duck[:,None]
            s=precise_mono_below(s,160) if precise_low_mono else mono_below(s,160)
        if name=='electric': s=saturate(s,drive=1.08,wet=.12)
        if with_effects:
            if style=='harbor' and name=='electric':
                s=tap_delay(s,bpm,beat_fraction=.75,wet=.105,feedback=.30)
            if style=='after' and name=='lead':
                s=tap_delay(s,bpm,beat_fraction=.75,wet=.21,feedback=.33)
                s=subtle_chorus(s,bpm,wet=.08)
            if style=='after' and name=='electric':s=tremolo(s,bpm,depth=.13,divisions=2)
            if style=='silver' and name=='electric':
                s=tap_delay(s,bpm,beat_fraction=1.,wet=.21,feedback=.37)
                s=subtle_chorus(s,bpm,wet=.15)
        # Place instruments, but never remove the center bass/lead completely.
        side={'acoustic':-.31 if style!='silver' else -.38,'piano':.17,
              'electric':.29 if style!='silver' else .21,'lead':-.14,'drums':0.,'bass':0.}[name]
        # Gentle balance shift, preserve recorded stereo texture.
        if side>0:s[:,1]*=(1+side*.55);s[:,0]*=(1-side*.55)
        if side<0:s[:,0]*=(1-side*.55);s[:,1]*=(1+side*.55)
        out[name]=s
    dry=sum(out.values())
    if with_effects:
        reverb_send=sum(out[n]*weight for n,weight in {
            'acoustic':.42,'electric':.65,'piano':.63,'lead':.70,'drums':.22,'bass':.04}.items())
        wet=room_send(reverb_send,wet={'harbor':.16,'after':.13,'silver':.27}[style],predelay_ms=room_predelay_ms)
        mixed=dry+wet
    else: mixed=dry
    # Maintain sub-bass focus; mono at low frequencies, with stereo musical details.
    mixed=precise_mono_below(mixed,115) if precise_low_mono else mono_below(mixed,115)
    # Gentle 45ms fade-in and 1.5sec fade-out; does not prematurely choke final phrase.
    fade_in=min(frames,round(.045*SR));fade_out=min(frames,round(1.55*SR))
    mixed[:fade_in]*=np.linspace(0,1,fade_in)[:,None]
    mixed[-fade_out:]*=np.linspace(1,0,fade_out)[:,None]
    p=float(np.max(abs(mixed)))
    if p<.003 or not np.isfinite(p):raise AssertionError('Silent/invalid master')
    # Consistent gain between examples, conservative peak cap; no continuous hard limiter.
    scale=min(1.,.84/p)
    mixed=(mixed*scale).astype(np.float32)
    return mixed,out,{'gain_used':gain_report,'peak_pre_gain':round(p,4),'master_scale':round(scale,4)}


def render(style:str,out:Path,assets:Path|None=None,gm:Path|None=None,
           with_effects=True,guitar_performance=False,bass_performance=False,piano_performance=False,
           rhythm_pocket=False,drum_dynamics=False,register_separation=False,melody_answer=False,
           room_predelay_ms=0.,precise_low_mono=False):
    if not math.isfinite(room_predelay_ms) or not 0<=room_predelay_ms<=160:
        raise ValueError('Room predelay must be 0–160 milliseconds')
    score=make(style);validate(score)
    performance_report=None
    if guitar_performance:
        score,performance_report=shape_strums(score)
        validate(score)
    bass_report=None
    if bass_performance:
        score,bass_report=shape_bass(score)
        validate(score)
    piano_report=None
    if piano_performance:
        score,piano_report=shape_piano(score)
        validate(score)
    rhythm_report=None
    if rhythm_pocket:
        score,rhythm_report=shape_pocket(score)
        validate(score)
    drum_report=None
    if drum_dynamics:
        score,drum_report=shape_drum_dynamics(score)
        validate(score)
    melody_report=None
    if melody_answer:
        score,melody_report=shape_final_answer(score)
        validate(score)
    register_report=None
    if register_separation:
        score,register_report=separate_lead_piano(score)
        validate(score)
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    raw=instrument_stems(score,assets=assets,gm=gm)
    mix,stems,diagnostics=process_stems(score,raw,with_effects=with_effects,
                                          room_predelay_ms=room_predelay_ms,
                                          precise_low_mono=precise_low_mono)
    stem=f'{style}-v7' + ('-p2-guitar' if guitar_performance else '') + ('-p2-bass' if bass_performance else '') + ('-p2-piano' if piano_performance else '') + ('-p3-pocket' if rhythm_pocket else '') + ('-p3-drums' if drum_dynamics else '') + ('-p4-register' if register_separation else '') + ('-p5-answer' if melody_answer else '') + (f'-p6-room{int(room_predelay_ms)}ms' if room_predelay_ms else '') + ('-p7-mono' if precise_low_mono else '')
    wav=out/(stem+'.wav');mp3=out/(stem+'.mp3')
    sf.write(wav,mix,SR,subtype='PCM_24')
    subprocess.run(['ffmpeg','-nostdin','-hide_banner','-v','error','-y','-i',str(wav),
                    '-c:a','libmp3lame','-b:a','256k',
                    '-metadata',f'title={score["title"]}',
                    '-metadata','artist=Music Studio (original instrumental)',str(mp3)],check=True)
    meta={'title':score['title'],'style':style,'backend':'GM preview (fallback)' if gm else 'recorded instruments',
          'duration_seconds':score['duration'],'score_notes':len(score['notes']),
          'drum_hits':len(score['drums']), 'effects_enabled':with_effects,
          'guitar_performance':performance_report,
          'bass_performance':bass_report,
          'piano_performance':piano_report,
          'rhythm_pocket':rhythm_report,
          'drum_dynamics':drum_report,
          'register_separation':register_report,
          'melody_answer':melody_report,
          'room_predelay_ms':room_predelay_ms,
          'precise_low_mono':precise_low_mono,**diagnostics}
    (out/(stem+'.score.json')).write_text(json.dumps(score,indent=2))
    (out/(stem+'.metadata.json')).write_text(json.dumps(meta,indent=2))
    return mp3,meta

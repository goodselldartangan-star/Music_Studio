"""A/B diagnostics for one engine subsystem: note lifetimes and legato.

Each MP3: BEFORE (legacy note stopping) | short pause | AFTER (new voice/release).
Uses local 5.7 MB General MIDI font only as a neutral, reproducible test.
No artist recordings, AI-generation APIs, or hidden downloaded sound assets.
"""
from __future__ import annotations
from pathlib import Path
import json, subprocess
import numpy as np
import soundfile as sf
from studio6.soundfonts import FluidSynth, SR
from studio7.articulation import render_polyphonic,planned_events,smooth_release

SOUNDFONT=Path('/usr/share/sounds/sf2/TimGM6mb.sf2')


def legacy_sf2(notes,seconds,bpm,program):
    synth=FluidSynth(SOUNDFONT,gain=.33)
    try:
        assert synth.select(synth.synth,0,synth.id,0,program)==0
        return synth.render([{'at':n['beat']*60/bpm,
                              'off':(n['beat']+n['length'])*60/bpm,
                              'pitch':n['pitch'],'velocity':n['velocity']}
                            for n in notes],round(seconds*SR))
    finally:synth.close()


def wave_rms(x):return float(np.sqrt(np.mean(np.square(x,dtype=np.float64))))


def legacy_pcm_release(raw,duration,release=.17):
    n=round((duration+release)*SR);out=np.zeros(n,np.float32)
    out[:min(n,len(raw))]=raw[:min(n,len(raw))]
    hold=round(duration*SR)
    if hold<n:out[hold:]*=np.exp(-np.arange(n-hold)/SR/(release*.22))
    return out


def piano_sustain_examples():
    bpm=116;seconds=9.0
    # Acoustic piano recorded from the same MIDI source at each pitch. Holding the
    # source longer than the notation allows the RELEASE, not sample truncation,
    # to control the note ending.
    score=[(0.,60,.70,77),(.0,64,.70,71),(.0,67,.70,73),
           (1.0,64,.65,65),(1.85,67,.68,70),(2.85,69,.88,80),
           (4.05,65,.76,69),(4.05,69,.76,68),(4.05,72,.76,71),
           (5.25,71,.80,74),(6.34,72,1.02,77)]
    output=[]
    for improved in (False,True):
        mix=np.zeros((round(seconds*SR),2),np.float32)
        for i,(beat,pitch,length,vel) in enumerate(score):
            start=round(beat*60/bpm*SR);dur=length*60/bpm
            # One held source note, the same for both renderers.
            raw=legacy_sf2([{'beat':0,'length':4.4,'pitch':pitch,'velocity':vel}],2.5,bpm,program=0)
            mono=raw.mean(axis=1)
            voice=smooth_release(mono,dur,part='piano') if improved else legacy_pcm_release(mono,dur)
            end=min(len(mix),start+len(voice))
            if end>start:
                mix[start:end,0]+=voice[:end-start]*.75
                mix[start:end,1]+=voice[:end-start]*.75
        output.append(mix)
    return output


def render_demo(name,before,after,out:Path,description):
    out.mkdir(parents=True,exist_ok=True)
    gap=np.zeros((round(.8*SR),2),np.float32)
    joined=[];measure=[]
    for x in (before,after):
        x=x.copy();rms=wave_rms(x)
        if rms<1e-5:raise ValueError('Silent demo')
        x*=min(24.,(10**(-20/20))/rms)
        peak=float(np.max(np.abs(x)))
        if peak>.78:x*=.78/peak
        k=min(500,len(x)//2)
        x[:k]*=np.linspace(0,1,k)[:,None]
        x[-k:]*=np.linspace(1,0,k)[:,None]
        measure.append({'rms_dbfs':round(20*np.log10(wave_rms(x)),2),
                        'peak_dbfs':round(float(20*np.log10(max(1e-8,float(np.max(np.abs(x)))))),2)})
        joined.append(x)
    audio=np.concatenate([joined[0],gap,joined[1]],axis=0)
    wav=out/f'{name}.wav';mp3=out/f'{name}.mp3'
    sf.write(wav,audio,SR,subtype='PCM_24')
    subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-nostdin','-y','-i',str(wav),
                    '-c:a','libmp3lame','-b:a','256k',str(mp3)],check=True)
    subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-nostdin','-xerror',
                    '-i',str(mp3),'-f','null','-'],check=True)
    return {'file':mp3.name,'seconds':round(len(audio)/SR,2),
            'before_after':measure,'description':description,
            'difference_rms':round(wave_rms(joined[0]-joined[1]),5)}


def main():
    if not SOUNDFONT.exists():raise RuntimeError('Test SF2 missing')
    out=Path('articulation_previews');out.mkdir(exist_ok=True)
    result=[]
    bpm=112;seconds=8.4
    guitar_notes=[
        {'beat':a,'length':1.55 if i%3!=1 else 1.25,'pitch':p,'velocity':82+(i%3)*5}
        for i,(a,p) in enumerate([(0,64),(1,64),(2,67),(3,67),(4,69),(5,69),
                                   (6,67),(7,67),(8,64),(9,64),(10,62),(11,64)])]
    before=legacy_sf2(guitar_notes,seconds,bpm,27)
    after=render_polyphonic(SOUNDFONT,guitar_notes,seconds,bpm,part='electric',program=27)
    result.append(render_demo('01_repeated_guitar_before_after',before,after,out,
         'A repeated clean-guitar note should ring into its retrigger, not be killed by an older note-off.'))
    before,after=piano_sustain_examples()
    result.append(render_demo('02_piano_releases_before_after',before,after,out,
         'Piano chord releases should linger naturally; the next notes arrive without a hard gated cut.'))
    bpm=110;seconds=9.5
    lead_notes=[{'beat':a,'length':l,'pitch':p,'velocity':82+(i%2)*4}
                for i,(a,l,p) in enumerate([
                    (0,.89,67),(1,.89,69),(2,.90,71),(3,1.38,74),
                    (5,.87,72),(6,.87,71),(7,.88,69),(8,1.6,67),
                    (11,.89,69),(12,.88,72),(13,1.55,74)])]
    before=legacy_sf2(lead_notes,seconds,bpm,73)
    after=render_polyphonic(SOUNDFONT,lead_notes,seconds,bpm,part='lead',program=73)
    result.append(render_demo('03_melody_connections_before_after',before,after,out,
        'Only near-touching melody notes join gently; the larger intended rests remain audible.'))
    report={'purpose':'articulation only; same notes and patch in each pair','samples':'General MIDI test SoundFont, not final studio instruments',
            'order':'legacy first, 0.8-second pause, improved second',
            'qa_note':'Technical difference and valid decode are verified; preferred sound requires listener feedback.',
            'clips':result}
    (out/'report.json').write_text(json.dumps(report,indent=2))
    print(json.dumps(report,indent=2))

if __name__=='__main__':main()

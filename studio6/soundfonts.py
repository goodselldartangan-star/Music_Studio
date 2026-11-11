"""Minimal offline FluidSynth SF2 render adapter. Only event lists in, mono/stereo samples out.
Uses system libfluidsynth; no model, remote service, or model inference.
"""
from __future__ import annotations
import ctypes as C
import ctypes.util
from pathlib import Path
import numpy as np

SR=44100

class FluidSynth:
    def __init__(self, soundfont:Path, gain:float=.34, drum:bool=False):
        if not Path(soundfont).is_file():raise FileNotFoundError(soundfont)
        libname=C.util.find_library('fluidsynth')
        if not libname:raise RuntimeError('libfluidsynth not installed')
        self.lib=C.CDLL(libname)
        def bind(name,return_type,types):
            func=getattr(self.lib,name);func.argtypes=types;func.restype=return_type;return func
        P=C.c_void_p;I=C.c_int;F=C.c_float;S=C.c_char_p
        self.mk_settings=bind('new_fluid_settings',P,[])
        self.setnum=bind('fluid_settings_setnum',I,[P,S,C.c_double])
        self.setint=bind('fluid_settings_setint',I,[P,S,I])
        self.mk_synth=bind('new_fluid_synth',P,[P])
        self.sfload=bind('fluid_synth_sfload',I,[P,S,I])
        self.select=bind('fluid_synth_program_select',I,[P,I,I,I,I])
        self.noteon=bind('fluid_synth_noteon',I,[P,I,I,I])
        self.noteoff=bind('fluid_synth_noteoff',I,[P,I,I])
        self.write=bind('fluid_synth_write_float',I,[P,I,P,I,I,P,I,I])
        self.cleanup=bind('delete_fluid_synth',None,[P])
        self.cleanup_settings=bind('delete_fluid_settings',None,[P])
        self.settings=self.mk_settings()
        self.setnum(self.settings,b'synth.sample-rate',SR)
        self.setnum(self.settings,b'synth.gain',gain)
        self.setnum(self.settings,b'synth.reverb.room-size',.25)
        self.setnum(self.settings,b'synth.reverb.level',.10)
        self.setint(self.settings,b'synth.chorus.active',0)
        self.synth=self.mk_synth(self.settings)
        self.id=self.sfload(self.synth,str(soundfont).encode(),1)
        if self.id<0:raise ValueError(f'FluidSynth failed to load: {soundfont}')
        self.channel=9 if drum else 0
        banks=[128,0] if drum else [0,128]
        if not any(self.select(self.synth,self.channel,self.id,bank,0)==0 for bank in banks):
            raise ValueError(f'SF2 has no expected preset: {soundfont} (banks {banks})')

    def render(self,notes:list[dict],frames:int)->np.ndarray:
        """Events: {beat,pitch,length,velocity}, where beat is pre-converted to seconds via 'bpm' upstream.
        Here callers must supply 'at' and 'off' in seconds.
        """
        if frames<0:raise ValueError('bad audio length')
        events=[]
        for n in notes:
            start=max(0,min(frames,int(round(n['at']*SR))))
            end=max(start+1,min(frames,int(round(n['off']*SR))))
            events.append((start,1,int(n['pitch']),int(n['velocity'])))
            events.append((end,0,int(n['pitch']),0))
        events.sort(key=lambda x:(x[0],x[1]))
        out=np.zeros((frames,2),dtype=np.float32)
        k=0;pos=0
        while pos<frames:
            nextframe=events[k][0] if k<len(events) else frames
            if nextframe>pos:
                step=nextframe-pos
                left=np.empty(step,dtype=np.float32);right=np.empty(step,dtype=np.float32)
                self.write(self.synth,step,left.ctypes.data,0,1,right.ctypes.data,0,1)
                out[pos:nextframe,0]=left;out[pos:nextframe,1]=right
                pos=nextframe
            while k<len(events) and events[k][0]<=pos:
                _,on,p,v=events[k]
                if on:self.noteon(self.synth,self.channel,p,min(127,max(1,v)))
                else:self.noteoff(self.synth,self.channel,p)
                k+=1
        return out
    def close(self):
        if getattr(self,'synth',None):self.cleanup(self.synth);self.synth=None
        if getattr(self,'settings',None):self.cleanup_settings(self.settings);self.settings=None


def render_sf2(path:Path,notes:list[dict],duration:float,bpm:int,drum:bool=False)->np.ndarray:
    events=[]
    for n in notes:
        st=n['beat']*60/bpm
        length=n.get('length',.18)*60/bpm
        events.append({'at':st,'off':st+length,'pitch':n['pitch'], 'velocity':n['velocity']})
    player=FluidSynth(Path(path),drum=drum)
    try:return player.render(events,round(duration*SR))
    finally:player.close()

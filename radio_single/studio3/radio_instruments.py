"""Drop-in improved instruments; contract: mono float32 samples for each note.
Preserves the physical-model plucks from v3, introduces expressive bright lead.
"""
import numpy as np
from .spec import Note, SR
from .instruments import hz, note_wave as _base_note_wave, drum_wave as _base_drum_wave

def note_wave(note:Note,bpm:int,seed:int):
    if note.part not in ('lead','counter'):
        return _base_note_wave(note,bpm,seed)
    # A short formant-like, harmonically shaped synth line that can carry a hook.
    seconds=note.duration*60/bpm
    release=.23
    t=np.arange(max(2,int((seconds+release)*SR)),dtype=np.float64)/SR
    f=hz(note.pitch)
    bend=1-.009*np.exp(-t/.036)
    vib=.0028*(1-np.exp(-np.maximum(0,t-.14)/.1))*np.sin(2*np.pi*5.3*np.maximum(0,t-.14))
    ph=2*np.pi*f*np.cumsum(bend+vib)/SR
    body=(.62*np.sin(ph)+.30*np.sin(2*ph+.19)+.16*np.sin(3*ph+.30)
          +.065*np.sin(4*ph+.23)+.035*np.sin(5*ph+.12))
    breath=(.022*np.sin(2*np.pi*9*t)*np.exp(-t/.34))
    attack=(1-np.exp(-t/.021))
    gate=np.minimum(1,np.maximum(0,(seconds+release-t)/release))**1.35
    contour=(.93+.07*np.sin(2*np.pi*.9*t))*attack*gate
    amp=.42 if note.part=='lead' else .23
    return np.asarray((body+breath)*contour*amp*note.velocity,dtype=np.float32)

def drum_wave(kind:str,variant:int=0):
    return _base_drum_wave(kind,variant)

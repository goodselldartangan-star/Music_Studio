"""P4: audit chord spelling and foreground/accompaniment pitch overlap.

Optional register separation shifts an existing piano dyad/chord by an octave;
no notes, chords, rhythms, velocity or effects are added or deleted.
"""
from __future__ import annotations
from copy import deepcopy
import re

_PC={'C':0,'D':2,'E':4,'F':5,'G':7,'A':9,'B':11}


def _parse_triad(name:str)->tuple[int,set[int]]:
    m=re.fullmatch(r'([A-G])([#b]?)(m?)',name)
    if not m:raise ValueError(f'Unsupported triad name: {name}')
    root=(_PC[m[1]]+(1 if m[2]=='#' else -1 if m[2]=='b' else 0))%12
    return root,{root,(root+(3 if m[3] else 4))%12,(root+7)%12}


def _overlap(a:dict,b:dict)->float:
    return min(a['beat']+a['length'], b['beat']+b['length'])-max(a['beat'],b['beat'])


def audit_registers(score:dict)->dict:
    from studio7.score import SONGS
    style=score.get('style')
    if style not in SONGS:raise ValueError('Unknown score/style')
    cfg=SONGS[style]
    if not (len(cfg['harmonies'])==len(cfg['voicings'])==len(cfg['roots'])==4):
        raise ValueError('Incomplete harmonic sequence')
    chords=[]
    for label,voicing,bass in zip(cfg['harmonies'],cfg['voicings'],cfg['roots']):
        root_pc,expected=_parse_triad(label)
        played={p%12 for p in voicing}
        if played!=expected or bass%12!=root_pc:
            raise ValueError(f'{style}: {label} has wrong voicing or bass')
        chords.append({'name':label,'pitch_classes':sorted(expected),
                       'voicing_span_semitones':max(voicing)-min(voicing)})
    leads=[n for n in score['notes'] if n['instrument'] in ('lead','electric') and n['length']>.5]
    piano=[n for n in score['notes'] if n['instrument']=='piano']
    unisons=[];semitones=[]
    for n in piano:
        for l in leads:
            o=_overlap(n,l)
            if o>=.24 and abs(n['pitch']-l['pitch'])<=1:
                hit={'beat':round(max(n['beat'],l['beat']),3),'piano_pitch':n['pitch'],
                     'lead_pitch':l['pitch'],'overlap_beats':round(o,3)}
                (unisons if n['pitch']==l['pitch'] else semitones).append(hit)
    return {'style':style,'chords':chords,'foreground_piano_unisons':len(unisons),
            'foreground_piano_semitones':len(semitones),
            'unison_examples':unisons[:6],'semitone_examples':semitones[:6],
            'note':'Unisons can be deliberate doubling; counts measure role overlap, not musical error.'}


def separate_lead_piano(score:dict)->tuple[dict,dict]:
    """Opt-in: lower whole piano chords only when doing so removes foreground unisons.

    Limit piano support voices to MIDI 48..84. Avoid splitting dyads/chords and
    keep every original piano pitch class; explicit fixed-register notes win.
    """
    before=audit_registers(score)
    revised=deepcopy(score)
    notes=revised['notes']
    piano_ids=sorted((i for i,n in enumerate(notes) if n['instrument']=='piano'),
                     key=lambda i:notes[i]['beat'])
    groups=[];i=0
    while i<len(piano_ids):
        start=notes[piano_ids[i]]['beat'];group=[piano_ids[i]];i+=1
        while i<len(piano_ids) and notes[piano_ids[i]]['beat']-start<=.09:
            group.append(piano_ids[i]);i+=1
        groups.append(group)
    shifted_groups=0;shifted_notes=0
    for group in groups:
        if any(notes[j].get('register')=='fixed' for j in group):continue
        pitches=[notes[j]['pitch'] for j in group]
        if min(pitches)-12<48 or max(pitches)-12>84:continue
        trial=deepcopy(revised)
        for j in group:trial['notes'][j]['pitch']-=12
        now=audit_registers(revised)
        cand=audit_registers(trial)
        if (cand['foreground_piano_unisons']<now['foreground_piano_unisons']
            and cand['foreground_piano_semitones']<=now['foreground_piano_semitones']):
            revised=trial;notes=revised['notes']
            shifted_groups+=1;shifted_notes+=len(group)
    after=audit_registers(revised)
    return revised,{'piano_chord_groups_revoiced':shifted_groups,
                    'piano_notes_revoiced':shifted_notes,
                    'unisons_before':before['foreground_piano_unisons'],
                    'unisons_after':after['foreground_piano_unisons'],
                    'semitones_before':before['foreground_piano_semitones'],
                    'semitones_after':after['foreground_piano_semitones'],
                    'pitches_only_octave_shifted':True}

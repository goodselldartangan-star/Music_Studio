"""P8 arrangement sections: score-only inventory and optional final-section breath.

No quantization, new harmony or sound selection. A quiet transition can be
useful or not, depending on style; tests verify the edit, not listener taste.
"""
from __future__ import annotations
from collections import Counter
from copy import deepcopy


SECTIONS=('intro','verse','build','final')


def section_inventory(score:dict)->dict:
    bars=int(score['bars'])
    if bars!=16:raise ValueError("P8 study currently expects a 16-bar score")
    parts={}
    for i,name in enumerate(SECTIONS):
        start=i*16;end=start+16
        notes=[n for n in score['notes'] if start<=n['beat']<end]
        drums=[d for d in score['drums'] if start<=d['beat']<end]
        parts[name]={'notes':len(notes),'drum_hits':len(drums),
                     'instrument_onsets':dict(sorted(Counter(n['instrument'] for n in notes).items())),
                     'drum_types':dict(sorted(Counter(d['kind'] for d in drums).items()))}
    return {'style':score['style'],'sections':parts,
            'note_onsets_total':sum(x['notes'] for x in parts.values()),
            'drum_onsets_total':sum(x['drum_hits'] for x in parts.values()),
            'limitations':'Event counts describe texture density, not musical quality.'}


def shape_transition_breath(score:dict)->tuple[dict,dict]:
    """Make a small backing-instrument gap before final return at beat 48.

    Drop the final closed-hat attack and at most one short late bass pickup in
    the previous bar. Preserve open hat if used as a transition lift. No
    sounding notes have their note-off changed; foreground phrasing stays put.
    """
    if score.get('bars')!=16:raise ValueError("Expected 16-bar score")
    original=deepcopy(score)
    start,end=47.35,48.
    dropped_notes=[];dropped_drums=[]
    kept=[]
    for note in original['notes']:
        is_pickup=(note['instrument']=='bass' and start<=note['beat']<end
                   and note['length']<=.5 and note.get('technique')!='fixed')
        if is_pickup and not dropped_notes:
            dropped_notes.append((note['beat'],note['pitch']))
        else:
            kept.append(note)
    original['notes']=kept
    kept=[]
    for hit in original['drums']:
        is_hat=(hit['kind']=='hat' and start<=hit['beat']<end
                and hit.get('technique')!='fixed')
        if is_hat:
            dropped_drums.append(hit['beat'])
        else:
            kept.append(hit)
    original['drums']=kept
    if not dropped_drums:raise ValueError("No late closed-hat attack exists for controlled transition")
    return original,{
        'before':section_inventory(score),
        'after':section_inventory(original),
        'dropped_short_bass_pickups':dropped_notes,
        'dropped_closed_hats':dropped_drums,
        'unchanged_foreground_harmony_and_note_tails':True,
    }

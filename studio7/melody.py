"""P5: authored final-answer cadences while preserving the recurring hook.

No random note mutations. Optional score transformation, not a taste metric.
"""
from __future__ import annotations
from copy import deepcopy
from studio7.score import SCALE

# (closing note, duration in beats). All are chord tones of the last bar.
FINAL_ANSWERS={
    'harbor':(67,1.58), # G4, G-major root
    'after':(69,1.98),  # A4, D-major fifth
    'silver':(64,2.08), # E4, C-major third
}


def motif_report(score:dict)->dict:
    """Describe motif repetition and phrase end without judging appeal."""
    leads=[n for n in score['notes'] if n['instrument'] in ('lead','electric') and n['length']>.5]
    def phrase(start):
        return [(n['pitch'],round(n['beat']-start,3),round(n['length'],3))
                for n in leads if start<=n['beat']<start+16]
    earlier,build,final=(phrase(t) for t in (16,32,48))
    shared=len(set((p,b) for p,b,_ in build)&set((p,b) for p,b,_ in final))
    ending=sorted((n for n in leads if 60<=n['beat']<64),key=lambda n:n['beat'])
    last=ending[-1] if ending else None
    return {'style':score['style'],'verse_notes':len(earlier),'build_notes':len(build),
            'last_refrain_notes':len(final),
            'same_pitch_onset_build_to_final':shared,
            'last_note_pitch':last['pitch'] if last else None,
            'last_note_duration':last['length'] if last else None,
            'last_note_ends_at':round(last['beat']+last['length'],3) if last else None,
            'note':'Motif repetition/variation is descriptive, not a catchiness score.'}


def shape_final_answer(score:dict)->tuple[dict,dict]:
    style=score.get('style')
    if style not in FINAL_ANSWERS:raise ValueError('Missing authored cadence')
    revised=deepcopy(score)
    ids=[i for i,n in enumerate(revised['notes'])
         if n['instrument'] in ('lead','electric') and n['length']>.5 and 60<=n['beat']<64]
    if not ids:raise ValueError('No closing foreground phrase')
    idx=max(ids,key=lambda i:revised['notes'][i]['beat'])
    old=revised['notes'][idx]
    if old.get('technique')=='fixed':
        return revised,{'changed':False,'reason':'fixed phrase'}
    pitch,duration=FINAL_ANSWERS[style]
    if pitch%12 not in SCALE[style]:raise ValueError('Cadence out of key')
    if old['beat']+duration>63.97:raise ValueError('Cadence overruns bar')
    before=motif_report(score)
    revised['notes'][idx]['pitch']=pitch
    revised['notes'][idx]['length']=duration
    return revised,{'changed':True,'from':(old['pitch'],old['length']),
                    'to':(pitch,duration),'earlier_hook_unchanged':True,
                    'final_phrase':motif_report(revised),'previous_final_phrase':before}

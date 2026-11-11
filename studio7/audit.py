"""Music-theory and arrangement guardrails, intentionally not an aesthetic judge."""
from collections import Counter
from .score import validate


def review(score:dict)->dict:
    validate(score)
    notes=score['notes'];errors=[]
    bass=[n for n in notes if n['instrument']=='bass']
    if any(n['pitch']>45 for n in bass):errors.append('Recorded bass out of native range')
    # Flag extended seconds/minor seconds between emphasized lead and sounding piano.
    leads=[n for n in notes if n['instrument'] in ('lead','electric') and n['length']>.5]
    keyboard=[n for n in notes if n['instrument']=='piano']
    for n in leads:
        for k in keyboard:
            overlap=min(n['beat']+n['length'],k['beat']+k['length'])-max(n['beat'],k['beat'])
            if overlap>.22 and abs(n['pitch']-k['pitch']) in (1,11,13):
                errors.append(f'Strong semitone lead/piano overlap at beat {n["beat"]:.2f}')
    # Detect implausibly spread simultaneous rhythm-guitar triads (same onset family).
    if score['style']=='after':
        chordstrikes={}
        for n in notes:
            if n['instrument']=='electric' and n['length']<.5:
                anchor=round(n['beat']*2)/2
                chordstrikes.setdefault(anchor,[]).append(n['pitch'])
        for t,pitches in chordstrikes.items():
            if max(pitches)-min(pitches)>14:errors.append(f'Overwide guitar voicing at beat {t}')
    melodic_density=round(len(leads)/(score['bars']*4),2)
    return {'passed':not errors,'issues':errors,'melody_notes_per_beat':melodic_density,
            'parts':dict(Counter(n['instrument'] for n in notes)),
            'principle':'Checks playable registers and obvious collisions, not listener preference.'}

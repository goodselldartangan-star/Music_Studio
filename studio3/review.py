"""Readable pre-render composition audit for GPT-assisted iteration.

Deterministic warnings are a checklist, not a simulated human listener.
"""
from collections import defaultdict
from .theory import KEY_CLASSES, verify_chords


def bar_signature(notes: list[dict], bar: int, part: str='lead') -> tuple:
    selected = (n for n in notes if n['part']==part and bar*4 <= n['beat'] < (bar+1)*4)
    return tuple(sorted((round(n['beat']-bar*4, 2), n['pitch'], round(n['duration'],2))
                        for n in selected))


def section_similarity(score:dict, first: tuple[int,int], second:tuple[int,int]) -> dict:
    n=min(first[1]-first[0],second[1]-second[0]); notes=score['notes']
    matches=sum(bar_signature(notes, first[0]+i)==bar_signature(notes,second[0]+i) for i in range(n))
    return {'matches':matches,'total':n,'fraction':round(matches/max(n,1),3)}


def audit_score(score:dict, chord_voicings:dict|None=None, strict:bool=False) -> dict:
    if chord_voicings is not None:
        verify_chords(chord_voicings)
    bars=score['bars']; notes=score['notes']; keys=KEY_CLASSES
    lead=[n for n in notes if n['part']=='lead']
    out_of_key=[(n['beat'],n['pitch']) for n in lead if (n['pitch']-score.get('transpose',0))%12 not in keys]
    large_leaps=[]
    for a,b in zip(lead,lead[1:]):
        if abs(b['pitch']-a['pitch'])>12 and b['beat']-a['beat']<3.5:
            large_leaps.append((a['beat'],b['beat'],b['pitch']-a['pitch']))
    sections={x['name']:(x['start'],x['end']) for x in score['sections']}
    comparisons={}
    for k, a,b in [('verse_reply','verse_a','verse_b'),('chorus_development','chorus_a','chorus_b')]:
        if a in sections and b in sections:
            comparisons[k]=section_similarity(score,sections[a],sections[b])
    chord_label_bad=[entry for entry in score['chords'] if chord_voicings is not None
                     and entry['chord'] not in chord_voicings]
    warnings=[]
    if len(out_of_key)>0: warnings.append(f'{len(out_of_key)} lead notes outside key vocabulary; check intentional chromatic notes')
    if len(large_leaps)>12: warnings.append(f'{len(large_leaps)} large melodic leaps: inspect transitions')
    for name,data in comparisons.items():
        if data['fraction'] >= .70:
            warnings.append(f'{name}: {data["matches"]}/{data["total"]} bars identical; develop the phrase')
    if chord_label_bad: warnings.append('Unknown chord names in score')
    report={'bars':bars,'lead_note_count':len(lead),'pitch_range':[min((n['pitch'] for n in lead),default=None),
                  max((n['pitch'] for n in lead),default=None)],
            'out_of_key_count':len(out_of_key),'large_leap_count':len(large_leaps),
            'phrase_comparisons':comparisons,'warnings':warnings,
            'limitations':'Symbolic constraints only; listening and musical taste are not measured'}
    if strict and warnings:
        raise ValueError('Composition preflight: '+ '; '.join(warnings))
    return report

"""Phrase-level development as a pure score transform.

Keep the first hook intact. Change later answers and endings so repeats are
recognizable without being carbon copies. Works on the portable score JSON
and never needs to import the sound engine or the mixer.
"""
from copy import deepcopy
from .theory import diatonic_step, KEY_CLASSES


def develop_score(score: dict) -> dict:
    """Make an independently editable variation without changing the score schema."""
    result = deepcopy(score)
    by_bar: dict[int, list[dict]] = {}
    for note in result['notes']:
        if note['part'] == 'lead':
            by_bar.setdefault(int(note['beat'] // 4), []).append(note)
    changed = 0
    for bar, notes in by_bar.items():
        notes.sort(key=lambda n: n['beat'])
        if not notes:
            continue
        # Verse 1: retain the first eight-bar identity, add a two-bar answer.
        if 16 <= bar < 24 and bar % 4 in (0, 1, 3):
            target = notes[-1]
            target['pitch'] = diatonic_step(target['pitch'], 1 if bar % 4 != 1 else -1)
            target['beat'] = round(target['beat'] + 0.075, 5)
            target['duration'] = round(target['duration'] * .88, 4)
            changed += 1
        # Verse 2: new answers and rests rather than an identical 4-bar cycle.
        if 56 <= bar < 72:
            phrase = bar - 56
            if len(notes) > 1:
                target = notes[-1]
                direction = (1, -1, 2, -1)[phrase % 4]
                target['pitch'] = diatonic_step(target['pitch'], direction)
                target['beat'] = round(target['beat'] + (.09 if phrase % 2 else -.06), 5)
                target['duration'] = round(target['duration'] * (1.12 if phrase % 3 == 1 else .81), 4)
                changed += 1
            if phrase in (4, 12) and len(notes) > 2:
                result['notes'].remove(notes[0])  # intentional, clearly audible rest
                changed += 1
        # Last chorus: original downbeat hook preserved at bars 80 and 88;
        # other bars change their endings, keeping the cadence on B.
        if 80 <= bar < 96 and (bar - 80) % 8 not in (0, 7):
            phrase = (bar - 80) % 8
            target = notes[-1]
            direction = (0, 1, -1, 1, 0, -1, 1, 0)[phrase]
            if direction:
                target['pitch'] = diatonic_step(target['pitch'], direction)
                target['beat'] = round(target['beat'] + (.07 if phrase % 2 == 0 else -.035), 5)
                target['duration'] = round(target['duration'] * (1.16 if phrase in (1, 5) else .92), 4)
                changed += 1
    # Normalize accidental off-key notes inherited from the old fixed score,
    # using at most a semitone of correction. Record the edit for inspection.
    transpose=score.get('transpose',0)
    for note in result['notes']:
        if note['part'] != 'lead':
            continue
        local=note['pitch']-transpose
        if local%12 not in KEY_CLASSES:
            candidates=(local-1,local+1)
            choice=next((p for p in candidates if p%12 in KEY_CLASSES),None)
            if choice is not None:
                note['pitch'] += choice-local
                changed += 1
    result['notes'].sort(key=lambda n: (n['beat'], n['part'], n['pitch']))
    result['development'] = {'version': 1, 'edited_events': changed,
                             'preserved_hook_bars': [32, 40, 80, 88]}
    return result

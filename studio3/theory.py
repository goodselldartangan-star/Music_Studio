"""Small, auditable music-theory contract. Standard library only.

Chord names here describe the actual pitch classes, not a guessed harmonic label.
Passing these checks doesn't prove that the progression sounds beautiful.
"""

CHORD_CLASSES = {
    'Bm9': frozenset((11, 2, 6, 9, 1)),
    'Gmaj9': frozenset((7, 11, 2, 6, 9)),
    'Dadd9': frozenset((2, 6, 9, 4)),
    'A6/9': frozenset((9, 1, 4, 6, 11)),
    'Em9': frozenset((4, 7, 11, 2, 6)),
    'F#7sus4': frozenset((6, 11, 1, 4)),
}
# B natural minor with A# added for the dominant's leading tone.
KEY_CLASSES = frozenset((11, 1, 2, 4, 6, 7, 9, 10))


def diatonic_step(pitch: int, steps: int) -> int:
    """Shift a MIDI note through allowable scale tones while preserving register."""
    if not steps:
        return pitch
    candidates = [p for p in range(24, 109) if p % 12 in KEY_CLASSES]
    # Source pitches from the lead are members of this scale.
    index = min(range(len(candidates)), key=lambda idx: abs(candidates[idx] - pitch))
    return candidates[max(0, min(len(candidates)-1, index+steps))]


def verify_chords(chord_voicings: dict) -> None:
    """Raise on misleading chord names or out-of-contract voicings."""
    if set(chord_voicings) != set(CHORD_CLASSES):
        raise ValueError('Chord labels and harmony theory contract disagree')
    for name, (notes, bass) in chord_voicings.items():
        actual = {n % 12 for n in notes} | {bass % 12}
        if actual != CHORD_CLASSES[name]:
            raise ValueError(f'{name}: got pitch classes {actual}, expected {CHORD_CLASSES[name]}')

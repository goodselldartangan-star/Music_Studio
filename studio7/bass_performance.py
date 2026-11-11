"""P2 bass technique: non-destructive note emphasis and bounded releases.

Only bass velocity and duration may change. No onset, pitch, chord, drum, mix,
instrument-bank or effects edits. Deliberate overlaps and tagged notes survive.
"""
from __future__ import annotations
from copy import deepcopy
import math


def shape_bass(score: dict) -> tuple[dict, dict]:
    """Return a new score with more intentional, restrained bass articulation.

    The downbeat supports the chord; offbeat passing notes are less emphatic.
    Short plucks release slightly earlier; long anchors can use a fraction of
    their *existing* rest. Every note attack stays exactly at its authored beat.
    """
    bpm = score["bpm"]
    if not isinstance(bpm, (int, float)) or not math.isfinite(bpm) or not 50 <= bpm <= 210:
        raise ValueError("Invalid tempo")
    result = deepcopy(score)
    notes = result["notes"]
    ids = sorted((i for i,n in enumerate(notes) if n["instrument"] == "bass"),
                 key=lambda i: notes[i]["beat"])
    changes = 0
    velocity_changes = 0
    length_changes = 0
    max_delta = 0.
    preserved_overlaps = 0
    for j, i in enumerate(ids):
        note = notes[i]
        if not 21 <= note["pitch"] <= 45 or not 1 <= note["velocity"] <= 127:
            raise ValueError("Invalid recorded bass pitch/velocity")
        if note["length"] <= 0 or note["beat"] < 0:
            raise ValueError("Invalid bass event")
        if note.get("technique") in ("fixed", "hold", "legato", "overlap"):
            continue
        pos = note["beat"] % 4
        if pos < .38:
            # Root / main phrase anchor. Strong but not a random hit.
            dv = 5
        elif pos >= 3.25:
            # Pickup into the following phrase.
            dv = -4
        elif pos < 2:
            dv = -3
        else:
            dv = 1
        new_v = max(1, min(127, note["velocity"] + dv))
        if new_v != note["velocity"]:
            note["velocity"] = new_v
            velocity_changes += 1

        length = float(note["length"])
        next_at = notes[ids[j+1]]["beat"] if j+1 < len(ids) else None
        end = note["beat"] + length
        if next_at is not None and next_at < end:
            # An overlapping previous note must not be cut short.
            preserved_overlaps += 1
        elif length <= .48:
            # A controlled light pluck, not an artificial note kill.
            note["length"] = round(max(.11, length - min(.045,length*.085)),4)
        elif length >= .88 and next_at is not None and next_at > end + .10:
            # Take <=35% of the old rest; never occupy the next attack.
            rest = next_at-end
            note["length"] = round(length + min(.07,rest*.35),4)

        delta = abs(float(note["length"]) - length)
        if delta > 1e-5:
            length_changes += 1
            max_delta = max(delta,max_delta)
        if note["velocity"] != new_v:
            raise AssertionError("Velocity assignment failed")
        if new_v != max(1,min(127,new_v)):
            raise AssertionError("Invalid velocity")
        if new_v != score["notes"][i]["velocity"] or delta > 1e-5:
            changes += 1

    return result, {
        "bass_notes": len(ids),
        "changed_notes": changes,
        "velocity_changes": velocity_changes,
        "length_changes": length_changes,
        "max_duration_change_beats": round(max_delta,4),
        "preserved_overlaps": preserved_overlaps,
        "onsets_and_pitches_unchanged": True,
    }

"""Q4 experimental SFZ piano pedal event routing, separate from actual voices.

Note lanes receive CC64 so samples can sustain, but CC22=0 mutes their
individual pedal-mechanism regions. A dedicated single effects instance
receives CC22=64 and the same CC64 edges; it emits pedal noises once per
gesture. Do not send these controllers to existing Music Studio renderers.
"""
from __future__ import annotations
import math


def pedal_controllers(windows:list[tuple[float,float]], *,
                      duration_beats:float,lanes:int)->dict:
    if not 1<=lanes<=32:
        raise ValueError("Expected a bounded set of SFZ voice instances")
    if not math.isfinite(duration_beats) or duration_beats<=0:
        raise ValueError("Bad score duration")
    sorted_windows=sorted((float(a),float(b)) for a,b in windows)
    old_end=0.
    edges=[]
    for start,end in sorted_windows:
        if (not math.isfinite(start) or not math.isfinite(end)
                or start<0 or start>=end or end>=duration_beats
                or start<old_end):
            raise ValueError("Bad, overlapping or unterminated sustain windows")
        edges.extend(((start,64,127),(end,64,0)))
        old_end=end
    # CC22 zero must precede any CC64 movement on each note lane.
    # CC22=64 approximates the official SFZ default HDCC22=0.5.
    voices=[[(0.,22,0),*edges] for _ in range(lanes)]
    mechanism=[(0.,22,64),*edges]
    return {
        "note_lane_events":voices,
        "single_mechanism_events":mechanism,
        "pedal_movement_count":len(edges),
        "mechanism_instances":1,
        "suppressed_in_note_lanes":True,
        "caveat":"SFZ engine must be tested to honor the CC22 gate in the complete Salamander instrument."
    }

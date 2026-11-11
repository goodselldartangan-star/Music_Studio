"""P3 optional bass/kick pocket. Only already-associated bass anchor *onsets* move.

A behind-kick bass note can be intentional. Defaults are mild style-specific
targets, not universal groove standards. No quantizing pickups, snares or hats.
"""
from __future__ import annotations
from copy import deepcopy
import math

TARGET_LAG_MS={"harbor":23.,"after":17.,"silver":38.}


def shape_pocket(score:dict, *, target_lag_ms:float|None=None)->tuple[dict,dict]:
    bpm=score["bpm"]
    if not isinstance(bpm,(int,float)) or not math.isfinite(bpm) or not 50<=bpm<=210:
        raise ValueError("Invalid BPM")
    target=TARGET_LAG_MS.get(score.get("style",""),25.) if target_lag_ms is None else target_lag_ms
    if not math.isfinite(target) or not 0<=target<=100:
        raise ValueError("Invalid target lag")
    beat_ms=60000/bpm
    out=deepcopy(score)
    kicks=sorted(h["beat"] for h in score["drums"] if h["kind"]=="kick")
    bass_ids=sorted((i for i,n in enumerate(score["notes"]) if n["instrument"]=="bass"),
                    key=lambda i:score["notes"][i]["beat"])
    moved=0;skipped_overlap=0;unpaired=0;pickup=0
    offsets_before=[];offsets_after=[]
    for pos,idx in enumerate(bass_ids):
        old=score["notes"][idx]
        if old.get("timing") in ("fixed","pickup"):
            continue
        if old["beat"]%4>=.38:
            pickup+=1
            continue
        candidates=[k for k in kicks if abs(old["beat"]-k)<=.38]
        if not candidates:
            unpaired+=1
            continue
        kick=min(candidates,key=lambda k:abs(k-old["beat"]))
        before_ms=(old["beat"]-kick)*beat_ms
        offsets_before.append(before_ms)
        new_at=kick+target/beat_ms
        # Only tighten genuinely late anchors. Never move an earlier/leading note
        # into an unrelated role or make it arrive before the kick.
        if before_ms<=target+12 or new_at>=old["beat"]:
            offsets_after.append(before_ms)
            continue
        if pos:
            prior=score["notes"][bass_ids[pos-1]]
            if prior["beat"]+prior["length"]>new_at-.02:
                skipped_overlap+=1
                offsets_after.append(before_ms)
                continue
        if old["beat"]-new_at>.12:
            new_at=old["beat"]-.12
        if new_at<0:
            raise AssertionError("Negative bass onset")
        out["notes"][idx]["beat"]=round(new_at,4)
        offsets_after.append((out["notes"][idx]["beat"]-kick)*beat_ms)
        moved+=1
    return out, {
        "matched_downbeat_bass":len(offsets_before),
        "bass_anchors_moved":moved,
        "unpaired_anchors":unpaired,
        "unmodified_pickups":pickup,
        "skipped_to_preserve_rest_or_overlap":skipped_overlap,
        "median_lag_before_ms":round(sorted(offsets_before)[len(offsets_before)//2],2) if offsets_before else None,
        "median_lag_after_ms":round(sorted(offsets_after)[len(offsets_after)//2],2) if offsets_after else None,
        "target_lag_ms":target,
        "other_instruments_drums_notes_and_velocities_unchanged":True,
    }

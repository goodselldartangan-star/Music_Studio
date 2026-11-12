"""Q2: evaluate physically tagged guitar string usage in existing scores.

This is a read-only audit of the exact sample files chosen by the current
recorded backend. It distinguishes simultaneous distinct-string chord attacks
from legitimate independent repeated-note sample voices.
"""
from __future__ import annotations
import argparse, hashlib, json, math, re
from pathlib import Path

from studio3.sample_bank import SampleBank
from studio3.spec import Note
from studio7.samples import Collection
from studio7.score import make

STRING_ORDER = ("LowE", "A", "D", "G", "B", "HighE")
STRING_PATTERN = re.compile(r"_String(LowE|A|D|G|B|HighE)_", re.I)


def string_of(path: Path) -> str:
    m=STRING_PATTERN.search(Path(path).name)
    if not m:
        raise ValueError(f"Recording missing physical string identity: {path}")
    return next(z for z in STRING_ORDER if z.lower()==m[1].lower())


def strum_groups(notes: list[dict]) -> list[list[tuple[int,dict]]]:
    acoustic=[(i,n) for i,n in enumerate(notes) if n["instrument"]=="acoustic"]
    acoustic.sort(key=lambda x:(x[1]["beat"],x[1]["pitch"]))
    groups=[];i=0
    while i<len(acoustic):
        first=acoustic[i][1]["beat"]
        group=[acoustic[i]];i+=1
        while i<len(acoustic) and acoustic[i][1]["beat"]-first<=.18:
            group.append(acoustic[i]);i+=1
        if 3<=len(group)<=6:
            groups.append(group)
    return groups


def _nylon_take(bank:Collection,n:dict,seed:int) ->Path:
    choices=bank.regions
    maxlayer=max(layer for _,_,layer in choices)
    goal=math.ceil(n["velocity"]/127*maxlayer)
    distance=min((abs(p-n["pitch"]),abs(layer-goal)) for _,p,layer in choices)
    best=[x for x in choices if (abs(x[1]-n["pitch"]),abs(x[2]-goal))==distance]
    index=int(hashlib.sha256(f'{seed}:{n["pitch"]}:{goal}'.encode()).hexdigest()[:8],16)%len(best)
    return best[index][0]


def audit_score(score:dict,assets:Path)->dict:
    style=score["style"]
    bank=SampleBank(assets) if style!="silver" else None
    nylon=Collection(assets,"meta-nylon-guitar") if style=="silver" else None
    guitars=[n for n in score["notes"] if n["instrument"]=="acoustic"]
    original_indices={id(n):i for i,n in enumerate(guitars)}
    groups=strum_groups(score["notes"])
    results=[]
    for group in groups:
        string_choices=[]
        for _,n in group:
            i=original_indices[id(n)]
            if nylon is not None:
                filename=_nylon_take(nylon,n,i+int(n["beat"]*100))
            else:
                note=Note("pluck",n["beat"],n["length"],n["pitch"],n["velocity"]/127,0)
                filename=bank._select(note,score["bars"]*43+i).path
            string_choices.append(string_of(filename))
        collisions=len(string_choices)-len(set(string_choices))
        results.append({"beat":round(group[0][1]["beat"],3),
                        "pitches":[n["pitch"] for _,n in group],
                        "source_strings":string_choices,
                        "same_string_collisions":collisions})
    return {
        "style":style,"gestures":len(results),
        "gestures_with_duplicate_strings":sum(x["same_string_collisions"]>0 for x in results),
        "excess_string_occupancies":sum(x["same_string_collisions"] for x in results),
        "colliding_examples":[x for x in results if x["same_string_collisions"]][:12],
        "limitations":"A per-note sample zone does not imply a physical voice model. The old renderer sums all note tails independently."
    }


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--assets",type=Path,required=True)
    p.add_argument("--out",type=Path,default=Path("q2_string_selection.json"))
    a=p.parse_args()
    report={style:audit_score(make(style),a.assets) for style in ("harbor","silver")}
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(report,indent=2))
    print(json.dumps(report,indent=2))


if __name__=="__main__":
    main()

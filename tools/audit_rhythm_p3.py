"""P3 baseline groove audit: report, do not quantize or alter any note.

Measure the authored kick/bass relationship and independent snare/hat placement.
Music production references treat ahead/behind timing as expressive, not a defect.
"""
from __future__ import annotations
import argparse, json, statistics
from pathlib import Path
from studio7.score import make, SONGS


def inspect_rhythm(score:dict)->dict:
    bpm=score["bpm"]
    if bpm<=0:raise ValueError("Invalid BPM")
    kicks=sorted(h["beat"] for h in score["drums"] if h["kind"]=="kick")
    snares=sorted(h["beat"] for h in score["drums"] if h["kind"]=="snare")
    hats=sorted(h["beat"] for h in score["drums"] if h["kind"] in ("hat","open_hat"))
    bass=sorted((n for n in score["notes"] if n["instrument"]=="bass"),key=lambda n:n["beat"])
    beat_ms=60000/bpm
    anchors=[];unpaired=[];pickup=0
    for n in bass:
        pos=n["beat"]%4
        if pos >= .38:
            pickup+=1
            continue
        matching=[k for k in kicks if abs(k-n["beat"])<=.38]
        if not matching:
            unpaired.append(round(n["beat"],3))
            continue
        k=min(matching,key=lambda k:abs(k-n["beat"]))
        anchors.append({"bass_beat":n["beat"],"kick_beat":k,
                        "offset_ms":round((n["beat"]-k)*beat_ms,2)})
    snare_offsets=[round((beat-round(beat))*beat_ms,2) for beat in snares]
    hat_offsets=[round((beat-round(beat*2)/2)*beat_ms,2) for beat in hats]
    late=[a for a in anchors if a["offset_ms"]>40]
    result={
      "style":score["style"],"bpm":bpm,"kick_hits":len(kicks),
      "snare_hits":len(snares),"hat_hits":len(hats),"bass_notes":len(bass),
      "downbeat_bass_kick_pairs":len(anchors),
      "unpaired_downbeat_bass":unpaired,
      "other_bass_notes":pickup,
      "bass_anchor_offset_ms_median":round(statistics.median([a["offset_ms"] for a in anchors]),2) if anchors else None,
      "anchor_offsets_ms":[a["offset_ms"] for a in anchors],
      "late_anchor_over_40ms_count":len(late),
      "snare_grid_offset_ms_median":round(statistics.median(snare_offsets),2) if snare_offsets else None,
      "hat_halfbeat_offset_ms_median":round(statistics.median(hat_offsets),2) if hat_offsets else None,
      "review_note":"40ms is a diagnostic threshold, not a universal musical error. Intro bass without kick is intentional. No MIDI events are modified.",
    }
    return result


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--out",type=Path,default=Path("p3_rhythm_baseline.json"))
    args=parser.parse_args()
    reports={style:inspect_rhythm(make(style)) for style in SONGS}
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(reports,indent=2))
    print(json.dumps(reports,indent=2))


if __name__=="__main__":main()

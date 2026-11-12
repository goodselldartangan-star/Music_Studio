"""P5 score-only phrase audit; metrics describe structure, not musical appeal.

Reports rests, note-duration variation, and recurring pitch/onset motifs.
Avoid replacing listener judgment with a numeric 'catchiness' score.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from studio7.score import make, SONGS
from studio7.melody import motif_report, shape_final_answer


def phrase_metrics(score:dict)->dict:
    if score['bpm'] <= 0: raise ValueError("Invalid tempo")
    leads=sorted((n for n in score['notes'] if n['instrument'] in ('lead','electric')
                  and n['length']>.5 and 16<=n['beat']<64),
                 key=lambda n:(n['beat'],n['pitch']))
    if not leads: raise ValueError("No expressive lead phrases")
    passages={}
    for start in (16,32,48):
        notes=[n for n in leads if start<=n['beat']<start+16]
        rests=[]
        for prior,nxt in zip(notes,notes[1:]):
            gap=nxt['beat']-(prior['beat']+prior['length'])
            if gap>0:rests.append(round(gap,3))
        long=[n for n in notes if n['length']>=1]
        passages[str(start)]={
            'notes':len(notes), 'pitches':len({n['pitch'] for n in notes}),
            'rests_count':len(rests), 'longest_rest_beats':max(rests,default=0),
            'notes_at_least_1_beat':len(long),
            'longest_note_beats':round(max((n['length'] for n in notes),default=0),3)
        }
    return {'style':score['style'],'passages':passages,'motif':motif_report(score),
            'limitations':'Structure-only; neither perceived hook quality nor human emotion is measured.'}


def audit_all()->dict:
    out={}
    for style in SONGS:
        original=make(style)
        revised,change=shape_final_answer(original)
        old=phrase_metrics(original);new=phrase_metrics(revised)
        # Only one last phrase note is changed: earlier hook and rests stay intact.
        assert old['passages']['16']==new['passages']['16']
        assert old['passages']['32']==new['passages']['32']
        assert new['passages']['48']['notes']==old['passages']['48']['notes']
        assert change['changed']
        out[style]={'original':old,'optional_final_answer':new,'change':change}
    return out


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--out',type=Path,default=Path('p5_phrase_report.json'))
    args=p.parse_args()
    r=audit_all()
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(r,indent=2,sort_keys=True))
    print(json.dumps({style:{'phrase_counts':[x['notes'] for x in data['original']['passages'].values()],
                             'rests':[x['rests_count'] for x in data['original']['passages'].values()],
                             'long_notes':[x['notes_at_least_1_beat'] for x in data['original']['passages'].values()]}
                      for style,data in r.items()},indent=2))


if __name__=='__main__':main()

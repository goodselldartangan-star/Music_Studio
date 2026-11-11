"""Render three concise music sketches for direct user feedback.

Each comparison begins from the same score contract. Independent performance
and mix profiles vary the feel, not the source melody or downloaded recordings.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import subprocess
from studio3 import create_score, Settings
from studio3.development import develop_score
from studio3.performance import PROFILES,make_excerpt
from studio3.mix import mix_score
from studio3.midi import write_midi


def render_one(out:Path,profile:str,bank:Path|None=None,require_drums:bool=False):
    score=make_excerpt(develop_score(create_score(Settings())),profile)
    out.mkdir(parents=True,exist_ok=True)
    (out/(score['stem']+'.score.json')).write_text(json.dumps(score,indent=2))
    write_midi(score,out/(score['stem']+'.mid'))
    report=mix_score(score,out,sample_root=bank,require_drums=require_drums)
    wav=Path(report['wav']);mp3=out/(score['stem']+'.mp3')
    subprocess.run(['ffmpeg','-nostdin','-v','error','-y','-i',str(wav),'-codec:a','libmp3lame','-b:a','256k',str(mp3)],check=True)
    report.update({'profile':profile,'description':score['description'],'mp3':str(mp3),'duration_seconds':score['duration_seconds']})
    return report


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--out',type=Path,default=Path('feedback-examples'))
    p.add_argument('--sample-root',type=Path)
    p.add_argument('--require-drums',action='store_true')
    p.add_argument('--only',choices=list(PROFILES))
    a=p.parse_args()
    results=[]
    for profile in ([a.only] if a.only else PROFILES):
        results.append(render_one(a.out/profile,profile,bank=a.sample_root,require_drums=a.require_drums))
    (a.out/'results.json').write_text(json.dumps(results,indent=2))
    print(json.dumps(results,indent=2))

if __name__=='__main__':main()

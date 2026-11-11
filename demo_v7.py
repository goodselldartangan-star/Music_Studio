"""Render three short, original instrument arrangements, no other AI service."""
import argparse,json
from pathlib import Path
from studio7.score import SONGS
from studio7.render import render
from studio7.qa import inspect

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--out',type=Path,default=Path('output_v7'))
    backend=p.add_mutually_exclusive_group(required=True)
    backend.add_argument('--assets',type=Path)
    backend.add_argument('--gm',type=Path)
    p.add_argument('--style',choices=list(SONGS))
    p.add_argument('--guitar-performance',action='store_true',help='P2 optional strum gestures')
    p.add_argument('--bass-performance',action='store_true',help='P2 optional bass articulation')
    p.add_argument('--piano-performance',action='store_true',help='P2 optional piano touch and rolled chords')
    a=p.parse_args();results=[]
    for style in ([a.style] if a.style else SONGS):
        mp3,meta=render(style,a.out,assets=a.assets,gm=a.gm,guitar_performance=a.guitar_performance,
                        bass_performance=a.bass_performance,
                        piano_performance=a.piano_performance)
        report=inspect(mp3)
        results.append({'metadata':meta,'audio_qa':report})
    (a.out/'verification_v7.json').write_text(json.dumps(results,indent=2))
    print(json.dumps(results,indent=2))
if __name__=='__main__':main()

"""CLI: inspect a symbolic score before running expensive synthesis."""
import argparse
import json
from pathlib import Path
from studio3.composition import CHORDS
from studio3.review import audit_score


def main():
    parser=argparse.ArgumentParser(description='Deterministic music-theory and repetition review')
    parser.add_argument('score',type=Path)
    parser.add_argument('--strict',action='store_true',help='Reject severe unresolved warnings')
    args=parser.parse_args()
    result=audit_score(json.loads(args.score.read_text()),CHORDS,strict=args.strict)
    print(json.dumps(result,indent=2))

if __name__=='__main__':main()

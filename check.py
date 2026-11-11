"""Thin quality-check CLI, separable from the music renderer."""
import argparse,json
from pathlib import Path
from studio3.quality import validate

def main():
    p=argparse.ArgumentParser();p.add_argument('output',nargs='?',type=Path,default=Path('output'))
    p.add_argument('--preview',action='store_true')
    a=p.parse_args();r=validate(a.output,full=not a.preview)
    (a.output/'qa_report.json').write_text(json.dumps(r,indent=2))
    print(json.dumps(r,indent=2))

if __name__=='__main__':main()

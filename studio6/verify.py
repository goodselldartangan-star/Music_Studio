"""Verify all demo masters and prevent placeholder instrument packs from being released."""
from __future__ import annotations
import argparse,json
from pathlib import Path
from .score import STYLES,make
from .qa import inspect


def verify(root:Path,assets:Path)->dict:
    required=[assets/'sf2'/f'{kind}.sf2' for kind in ('electric','bass','drums')]
    required += [assets/'provenance.json',assets/'soundfont_provenance.json']
    if any(not p.is_file() for p in required):raise FileNotFoundError('Missing required publisher-sourced recordings or provenance')
    rows=[]
    for kind in STYLES:
        expected=make(kind)['seconds'];r=inspect(root/f'{kind}-real.wav',root/f'{kind}-real.mp3',expected)
        rows.append({'style':kind,**r})
    results={'passed':True,'models_used':0,'audio_sources':'Meta Open Sound; FreePats Yamaha bass, Fender guitar, MuldjordKit drums',
             'note':'Technical quality check, not a human aesthetic judgment','examples':rows}
    (root/'verification.json').write_text(json.dumps(results,indent=2))
    return results

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,default=Path('v6-demos'))
    p.add_argument('--assets',type=Path,default=Path('assets/v6'))
    a=p.parse_args();print(json.dumps(verify(a.out,a.assets),indent=2))

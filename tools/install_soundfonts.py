"""Safely unpack CC0/CC BY SoundFont releases acquired from their original publishers.
Requires py7zr only during installation; never needs cloud inference or an API key.
"""
from __future__ import annotations
import argparse,hashlib,json,shutil
from pathlib import Path, PurePosixPath

PACKS={
 'electric': ('freepats/electric-guitar-FSBS-clean','2026-08-07','EGuitarFSBS-clean-bridge-small-SF2-20260807.7z','CC0-1.0'),
 'bass': ('freepats/electric-bass-YR','2019-09-30','FingerBassYR-SF2-20190930.7z','CC0-1.0'),
 'drums': ('freepats/muldjordkit','2020-10-18','MuldjordKit-SF2-20201018.7z','CC-BY-4.0'),
}

def install(archives:Path,destination:Path)->dict:
    import py7zr
    manifest={}
    destination.mkdir(parents=True,exist_ok=True)
    for name,(repo,tag,filename,license) in PACKS.items():
        archive=archives/filename
        if not archive.is_file():raise FileNotFoundError(f'Missing {archive}; use gh release download from {repo} tag {tag}')
        with py7zr.SevenZipFile(archive,mode='r') as z:
            names=z.getnames()
            if any(PurePosixPath(x).is_absolute() or '..' in PurePosixPath(x).parts for x in names):
                raise ValueError('7z path traversal detected')
            if not any(x.lower().endswith('.sf2') for x in names):
                raise ValueError(f'{filename} has no soundfont')
            temporary=destination/f'.extract-{name}'
            if temporary.exists():shutil.rmtree(temporary)
            temporary.mkdir()
            try:
                z.extractall(path=temporary)
                choices=list(temporary.rglob('*.sf2'))
                if len(choices)!=1:raise ValueError(f'Expected one SF2 in {filename}: {choices}')
                target=destination/'sf2'/f'{name}.sf2';target.parent.mkdir(parents=True,exist_ok=True)
                shutil.copyfile(choices[0],target)
            finally:shutil.rmtree(temporary,ignore_errors=True)
        manifest[name]={'publisher':repo,'tag':tag,'filename':filename,'license':license,
                        'download_sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),
                        'sample_bytes':target.stat().st_size}
    (destination/'soundfont_provenance.json').write_text(json.dumps(manifest,indent=2))
    return manifest

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--archives',type=Path,required=True)
    p.add_argument('--out',type=Path,default=Path('assets/v6'))
    args=p.parse_args();print(json.dumps(install(args.archives,args.out),indent=2))

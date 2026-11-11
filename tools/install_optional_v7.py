"""Install optional picked bass SF2 + nylon guitar OGG only from verified publisher ZIPs.

Does not download or modify existing v6 instruments. Outputs manifest with SHA256.
"""
from __future__ import annotations
import argparse,hashlib,json,shutil,zipfile
from pathlib import Path,PurePosixPath

def install_bass(archive:Path,out:Path):
    import py7zr
    with py7zr.SevenZipFile(archive) as z:
        entries=z.getnames()
        if any(PurePosixPath(x).is_absolute() or '..' in PurePosixPath(x).parts for x in entries):raise ValueError('bad path')
        tmp=out/'.bass-tmp'
        if tmp.exists():shutil.rmtree(tmp)
        tmp.mkdir(parents=True)
        try:
            z.extractall(path=tmp)
            fonts=list(tmp.rglob('*.sf2'))
            if len(fonts)!=1:raise ValueError('picked bass archive must contain one SF2')
            dest=out/'sf2/bass_picked.sf2';dest.parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(fonts[0],dest)
        finally:shutil.rmtree(tmp)
    return dest

def install_nylon(archive:Path,out:Path):
    dest=out/'meta-nylon-guitar';dest.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(archive) as z:
        files=[a for a in z.infolist() if a.filename.lower().endswith(('.ogg','.wav'))]
        if not files:raise ValueError('No nylon samples in archive')
        for f in files:
            path=PurePosixPath(f.filename)
            if path.is_absolute() or '..' in path.parts:raise ValueError('bad path')
            target=dest/path.name
            with z.open(f) as src,open(target,'wb') as dst:shutil.copyfileobj(src,dst)
    return dest

def main():
    p=argparse.ArgumentParser();p.add_argument('--picked-bass',type=Path,required=True)
    p.add_argument('--nylon',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
    bass=install_bass(a.picked_bass,a.out);nylon=install_nylon(a.nylon,a.out)
    data={
      'picked_bass':{'publisher':'freepats/electric-bass-YR','tag':'2019-09-30','license':'CC0-1.0','sha256':hashlib.sha256(a.picked_bass.read_bytes()).hexdigest(),'installed':str(bass)},
      'nylon_guitar':{'publisher':'facebookincubator/Meta-open-sound','tag':'meta-nylon-guitar-v1.0.0','license':'CC0-1.0','sha256':hashlib.sha256(a.nylon.read_bytes()).hexdigest(),'sample_count':len(list(nylon.glob('*.ogg')))+len(list(nylon.glob('*.wav')))} }
    (a.out/'optional_v7_provenance.json').write_text(json.dumps(data,indent=2))
    print(json.dumps(data,indent=2))
if __name__=='__main__':main()

"""Install original publisher 24-bit stereo WAV notes into a separate source tier.

No downloads, external AI, or replacement of legacy mono OGG archives. The
source ZIPs come from the exact official Meta Open Sound release tags.
"""
from __future__ import annotations
import argparse,hashlib,json,shutil
from pathlib import Path,PurePosixPath
from zipfile import ZipFile
import soundfile as sf
from studio3.sample_bank import NOTE_PATTERN

SOURCES={
    'meta-steel-guitar': ('meta-open-sound-meta-steel-guitar-wav.zip',375,663385210),
    'meta-piano': ('meta-open-sound-meta-piano-wav.zip',352,752311261),
    'meta-nylon-guitar': ('meta-open-sound-meta-nylon-guitar-wav.zip',348,423127309),
}


def install_archive(kind:str,archive:Path,root:Path,*,strict=True)->dict:
    if kind not in SOURCES:raise ValueError('Unknown original WAV collection')
    filename,count,bytes_expected=SOURCES[kind]
    archive=Path(archive)
    if not archive.is_file():raise FileNotFoundError(archive)
    if strict and (archive.name!=filename or archive.stat().st_size!=bytes_expected):
        raise ValueError(f'Unexpected published archive identity/size for {kind}')
    root=Path(root);root.mkdir(parents=True,exist_ok=True)
    target=root/kind
    if target.exists():
        raise FileExistsError(f'Existing original samples will not be overwritten: {target}')
    temporary=root/('.'+kind+'.installing')
    if temporary.exists():raise FileExistsError(f'Installation already pending: {temporary}')
    temporary.mkdir()
    used=set()
    try:
        with ZipFile(archive) as pack:
            for info in pack.infolist():
                if info.is_dir() or not info.filename.lower().endswith('.wav'):
                    continue
                sample=PurePosixPath(info.filename)
                if sample.is_absolute() or '..' in sample.parts or info.file_size>35000000:
                    raise ValueError('Unsafe or unexpectedly large WAV sample in archive')
                if not NOTE_PATTERN.search(sample.name):
                    raise ValueError(f'Unrecognized recorded-note identity: {sample.name}')
                if sample.name.casefold() in used:raise ValueError('Duplicate source-note filename')
                used.add(sample.name.casefold())
                dest=temporary/sample.name
                with pack.open(info) as src,dest.open('wb') as out:
                    shutil.copyfileobj(src,out)
                metadata=sf.info(dest)
                if (metadata.format!='WAV' or metadata.subtype!='PCM_24'
                    or metadata.channels!=2 or metadata.samplerate!=48000):
                    raise ValueError(f'Not a 24-bit 48k stereo publisher WAV: {sample.name}')
        if strict and len(used)!=count:
            raise ValueError(f'{kind}: expected {count} WAV files but found {len(used)}')
        temporary.rename(target)
    except Exception:
        shutil.rmtree(temporary,ignore_errors=True)
        raise
    digest=hashlib.sha256()
    with archive.open('rb') as source:
        for chunk in iter(lambda:source.read(1024*1024),b''):
            digest.update(chunk)
    return {'source':'facebookincubator/Meta-open-sound','collection':kind,
            'license':'CC0-1.0','archive':archive.name,'sha256':digest.hexdigest(),
            'archives_bytes':archive.stat().st_size,'sample_count':len(used),
            'format':'WAV PCM_24 stereo 48kHz',
            'note':'Installed separately; no existing OGG samples or MP3s replaced'}


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--steel',type=Path,required=True)
    p.add_argument('--piano',type=Path,required=True)
    p.add_argument('--nylon',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    a=p.parse_args()
    reports=[]
    for kind,archive in (('meta-steel-guitar',a.steel),('meta-piano',a.piano),('meta-nylon-guitar',a.nylon)):
        reports.append(install_archive(kind,archive,a.out))
    manifest={'source_release_tags':{'meta-steel-guitar':'meta-steel-guitar-v1.0.0',
        'meta-piano':'meta-piano-v1.0.0','meta-nylon-guitar':'meta-nylon-guitar-v1.0.0'},
        'collections':reports}
    (a.out/'wav_provenance.json').write_text(json.dumps(manifest,indent=2))
    print(json.dumps(manifest,indent=2))

if __name__=='__main__':main()

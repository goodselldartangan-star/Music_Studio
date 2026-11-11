"""Fetch/extract verified-source CC0 OGG instrument packs without an AI service.

Download assets from Meta's tagged releases or pass existing ZIPs.
No user account is needed; samples stay out of source control.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import shutil
import urllib.request
from zipfile import ZipFile

RELEASE = 'https://github.com/facebookincubator/Meta-open-sound/releases/download/'
PACKS = {
    'meta-steel-guitar': ('meta-steel-guitar-v1.0.0', 'meta-open-sound-meta-steel-guitar-ogg.zip', 35_000_000),
    'meta-piano': ('meta-piano-v1.0.0', 'meta-open-sound-meta-piano-ogg.zip', 60_000_000),
}
# SHA256 observed from the publisher's unmodified release ZIPs during the first
# successful authenticated-public GitHub Actions retrieval on 2026-11-11.
PINNED_SHA256 = {
    'meta-steel-guitar': 'a06baf193497ba36f20ccb67018e9f106155ad5e4f81d8a672530498038f68ed',
    'meta-piano': '4ba8095f5c2a70396d14f3b9c563f6c9010a093893159bad50e83145e1c35d40',
}


def download_pack(kind: str, cache: Path) -> Path:
    tag, filename, limit = PACKS[kind]
    cache.mkdir(parents=True, exist_ok=True)
    dest = cache / filename
    if dest.exists() and 1000 < dest.stat().st_size < limit:
        return dest
    url = f'{RELEASE}{tag}/{filename}'
    request = urllib.request.Request(url, headers={'User-Agent': 'MusicStudio-CC0-SampleInstaller/1.0'})
    partial = dest.with_suffix('.zip.part')
    total = 0
    try:
        with urllib.request.urlopen(request, timeout=90) as src, partial.open('wb') as out:
            while chunk := src.read(1024 * 512):
                total += len(chunk)
                if total > limit:
                    raise ValueError(f'Archive unexpectedly large: {kind}')
                out.write(chunk)
        if total < 1000:
            raise ValueError('Archive unexpectedly small')
        partial.replace(dest)
    finally:
        partial.unlink(missing_ok=True)
    return dest


def install_pack(kind: str, archive: Path, dest: Path) -> dict:
    if kind not in PACKS:
        raise ValueError(f'Unknown collection: {kind}')
    tag, filename, max_bytes = PACKS[kind]
    if archive.stat().st_size > max_bytes:
        raise ValueError('Archive size outside publisher bounds')
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    if archive.name == filename and digest != PINNED_SHA256[kind]:
        raise ValueError(f'Publisher archive checksum changed for {kind}; inspect source before using')
    target = dest / kind
    target.mkdir(parents=True, exist_ok=True)
    count = 0
    with ZipFile(archive) as z:
        for info in z.infolist():
            if info.is_dir() or not info.filename.lower().endswith('.ogg'):
                continue
            srcname = PurePosixPath(info.filename)
            if srcname.is_absolute() or '..' in srcname.parts:
                raise ValueError('Unsafe ZIP path')
            if info.file_size > 12_000_000:
                raise ValueError('Unexpectedly large sample')
            # Store OGG by basename. Publisher naming includes pitch and layer.
            sample = target / srcname.name
            if not sample.exists() or sample.stat().st_size != info.file_size:
                with z.open(info) as source, sample.open('wb') as sink:
                    shutil.copyfileobj(source, sink)
            count += 1
    if count < 1:
        raise ValueError(f'No OGG sample files in {archive}')
    return {'collection': kind, 'license': 'CC0-1.0', 'release_tag': tag,
            'asset': filename, 'files': count,
            'download_sha256': digest}


def main():
    p = argparse.ArgumentParser(description='Install Meta Open Sound CC0 piano + guitar libraries')
    p.add_argument('--out', type=Path, default=Path('assets/cc0-samples'))
    p.add_argument('--cache', type=Path, default=Path('.download-cache'))
    p.add_argument('--no-download', action='store_true', help='Use existing ZIPs only')
    p.add_argument('--guitar-zip', type=Path)
    p.add_argument('--piano-zip', type=Path)
    args = p.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    summaries = []
    for kind, zip_arg in (('meta-steel-guitar', args.guitar_zip), ('meta-piano', args.piano_zip)):
        if zip_arg:
            path = zip_arg
        elif args.no_download:
            raise ValueError(f'Missing --{ "guitar" if kind == "meta-steel-guitar" else "piano" }-zip')
        else:
            path = download_pack(kind, args.cache)
        summaries.append(install_pack(kind, path, args.out))
    provenance = {'source': 'https://github.com/facebookincubator/Meta-open-sound', 'packs': summaries,
                  'note': 'Samples licensed CC0 by publisher; these archives are not required in git.'}
    (args.out / 'provenance.json').write_text(json.dumps(provenance, indent=2))
    print(json.dumps(provenance, indent=2))


if __name__ == '__main__':
    main()

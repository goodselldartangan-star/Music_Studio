"""Install a small, pinned CC0 808 kit from a public GitHub repository.

No third-party AI, account, or token. SHA1 is the Git blob hash including header,
so GitHub's source integrity can be verified independently of transport.
Only exact allowlisted source paths are retrieved.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import urllib.request

SOURCE = 'Boochi44/free-drum-samples'
REV = '77ba31428a079dd8f17c8e144c1e649ea0a198b3'  # upstream tree, not a branch alias
FILES = [
    ('kick','02-bounce/kicks/bounce-kick-01.wav','cf595b2b384ec776f7d49a534f4e99b2aabc6905'),
    ('kick','02-bounce/kicks/bounce-kick-02.wav','8dc3eff1916bfc4399a44b333e2f76515293ef53'),
    ('snare','02-bounce/snares/bounce-snare-01.wav','dcc8ea387b3b729697c866406b633dd00f2e6081'),
    ('snare','02-bounce/snares/bounce-snare-02.wav','9b76b1de87476ac6244dc4a5941ceca603044127'),
    ('hat','02-bounce/hi-hats/hi-hat-closed-01.wav','ffc5951ddfc3801f947579f7994bcab2ca42edf1'),
    ('hat','03-soulful-vintage/hi-hats/hi-hat-closed-01.wav','24a61ae3229dafa5f432fc7ecace6d6b5f034d1c'),
    ('open_hat','02-bounce/open-hats/open-hat-01.wav','09bef0beb015be23963b968e37696fc788d5ef98'),
    ('clap','03-soulful-vintage/claps/vintage-clap-01.wav','2a17dc297a59b672bfc55f902e92fae40258f37c'),
    ('tom','03-soulful-vintage/percs/perc-low-tom.wav','1b9dc88728f104c551d572dea2ea589e561e2df3'),
    ('rim','01-hard-trap/percs/perc-rimshot.wav','c5a54c77a27ed9776b74890b4ffe1016b1202e13'),
    ('shaker','03-soulful-vintage/percs/perc-maraca.wav','16bb6a4a1f7a0b7aeb55efe68682321832a2a032'),
]


def git_blob_sha(data:bytes)->str:
    return hashlib.sha1(f'blob {len(data)}\0'.encode()+data).hexdigest()


def install(dest:Path, fetch=None)->dict:
    """Downloader is injectable so tests exercise validation without networking."""
    if fetch is None:
        def fetch(path):
            url=f'https://raw.githubusercontent.com/{SOURCE}/main/drum-samples/{path}'
            req=urllib.request.Request(url,headers={'User-Agent':'MusicStudio-CC0Drums/1.0'})
            with urllib.request.urlopen(req,timeout=40) as response:
                return response.read(2_000_001)
    manifest=[]
    for kind,rel,sha in FILES:
        out=dest/'drums'/kind/(rel.split('/')[0]+'-'+Path(rel).name)
        if out.exists() and git_blob_sha(out.read_bytes())==sha:
            data=out.read_bytes()
        else:
            data=fetch(rel)
            if len(data)>2_000_000 or not data.startswith(b'RIFF') or b'WAVE' not in data[:16]:
                raise ValueError(f'Not a WAV file: {rel}')
            if git_blob_sha(data)!=sha:
                raise ValueError(f'Source checksum mismatch: {rel}')
            out.parent.mkdir(parents=True,exist_ok=True)
            partial=out.with_suffix('.partial')
            partial.write_bytes(data)
            partial.replace(out)
        manifest.append({'kind':kind,'upstream':rel,'local':str(out.relative_to(dest)),'git_blob_sha1':sha,'bytes':len(data)})
    result={'source':f'https://github.com/{SOURCE}','license':'CC0-1.0','files':manifest}
    dest.mkdir(parents=True,exist_ok=True)
    (dest/'drum_provenance.json').write_text(json.dumps(result,indent=2))
    return result


def main():
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,default=Path('assets/cc0-samples'))
    args=p.parse_args();r=install(args.out)
    print(json.dumps({'source':r['source'],'count':len(r['files']),'kinds':sorted(set(x['kind'] for x in r['files']))},indent=2))

if __name__=='__main__':main()

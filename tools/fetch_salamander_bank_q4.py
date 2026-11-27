"""Q4 optional full-bank source installer, exact pinned publisher Git objects.

Downloads public CC BY 3.0 FLAC originals to a temporary CI directory. Each
stream is checked against the pinned official Git blob SHA1 and size before
atomic installation. Nothing is committed, republished, or changed in the
existing Music Studio instrument folders.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
import time
from concurrent.futures import ThreadPoolExecutor,as_completed
from pathlib import Path
from urllib.parse import quote
from urllib.request import Request,urlopen

from tools.audit_salamander_full_q4 import COMMIT,REQUIRED_FILES,UPSTREAM,original_blob_sha


def _read_url(relative:str, *,timeout:int=90)->bytes:
    url=f"https://raw.githubusercontent.com/{UPSTREAM}/{COMMIT}/{quote(relative,safe='/')}"
    req=Request(url,headers={"User-Agent":"Music-Studio-Q4-offline-recording-audit"})
    with urlopen(req,timeout=timeout) as response:
        return response.read()


def install_one(path:Path,rel:str,sha:str,size:int,*,retries:int=4)->str:
    if "/" in rel or "\\" in rel or rel in ("",".",".."):
        raise ValueError("Invalid original sample path")
    dest=path/"Samples"/rel
    dest.parent.mkdir(parents=True,exist_ok=True)
    if dest.is_file() and dest.stat().st_size==size and original_blob_sha(dest)==sha:
        return "reused"
    tmp=dest.with_suffix(dest.suffix+".part")
    for attempt in range(retries):
        try:
            blob=_read_url("Samples/"+rel)
            if len(blob)!=size:
                raise ValueError(f"Wrong byte count for {rel}")
            got=hashlib.sha1(b"blob "+str(len(blob)).encode()+b"\x00"+blob).hexdigest()
            if got!=sha:
                raise ValueError(f"Publisher Git blob digest mismatch: {rel}")
            tmp.write_bytes(blob)
            os.replace(tmp,dest)
            return "downloaded"
        except Exception:
            tmp.unlink(missing_ok=True)
            if attempt==retries-1:
                raise
            time.sleep(min(2**attempt,12))
    raise AssertionError("Unreachable downloader state")


def download(root:Path,manifest:Path,*,workers:int=4,limit:int|None=None)->dict:
    if not 1<=workers<=8:
        raise ValueError("Bound external download concurrency")
    data=json.loads(Path(manifest).read_text())
    if data.get("source_revision")!=COMMIT:
        raise ValueError("Pinned original Git revision mismatch")
    originals={}
    for item in data["tree"]:
        if item["type"]!="blob" or not item["path"].startswith("Samples/"):
            raise ValueError("Unexpected source manifest entry")
        originals[item["path"][len("Samples/"):]]=(item["sha"],item["size"])
    if len(originals)!=641:
        raise ValueError("Expected the complete original 641-file piano")
    source=Path(root)
    source.mkdir(parents=True,exist_ok=True)
    # Definitions are small and always fetched from the same official commit.
    for rel in (*REQUIRED_FILES,"README.md"):
        dest=source/rel
        dest.parent.mkdir(parents=True,exist_ok=True)
        if not dest.exists():
            dest.write_bytes(_read_url(rel))
    all_files=sorted(originals.items())
    if limit is not None:
        if limit<1:raise ValueError("File limit must be positive")
        all_files=all_files[:limit]
    result={"downloaded":0,"reused":0}
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures={pool.submit(install_one,source,name,sha,size):name
                 for name,(sha,size) in all_files}
        for idx,future in enumerate(as_completed(futures),1):
            status=future.result()
            result[status]+=1
            if idx%40==0 or idx==len(all_files):
                print(f"Q4 pinned FLAC integrity: {idx}/{len(all_files)} verified")
    return {"original_source":f"https://github.com/{UPSTREAM}",
            "commit":COMMIT,
            "cc_by_3_0_attribution":"Salamander Grand Piano V3 by Alexander Holm",
            "requested_flac_count":len(all_files),
            **result,
            "verify_all_required":limit is None}


if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--out",type=Path,required=True)
    p.add_argument("--manifest",type=Path,default=Path("tests/fixtures/q4_salamander_pinned_tree.json"))
    p.add_argument("--workers",type=int,default=4)
    p.add_argument("--limit",type=int)
    a=p.parse_args()
    print(json.dumps(download(a.out,a.manifest,workers=a.workers,limit=a.limit),indent=2))

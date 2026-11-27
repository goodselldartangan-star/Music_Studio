"""Q4 full original Salamander SFZ sample closure / optional file integrity audit.

Read the exact publisher SFZ includes and pinned Git tree; resolve 16 velocity
layers, key releases, resonances and pedal samples without copying them into
Music Studio. When given an installed bank, stream-verify every Git blob SHA1
and its FLAC header. No sound generation, source modification or licensing
claims beyond those grounded in upstream text and commit.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
from collections import Counter
from pathlib import Path

import soundfile as sf

UPSTREAM="sfzinstruments/SalamanderGrandPiano"
COMMIT="3382bf9496bba2486f5ab0de55a264d1dfc38404"
COUNTS={"note":480,"release":88,"resonance":69,"pedal":4}
REQUIRED_FILES=("Salamander Grand Piano V3.sfz",
                "Data/notes.txt","Data/hammer.txt","Data/str_res.txt",
                "Data/pedal.txt",*tuple(f"Data/vel_{v:02d}.txt" for v in range(1,17)))
SAMPLE_REGEX=re.compile(r"\bsample=([^\s]+)")


def _refs(text:str)->list[str]:
    return SAMPLE_REGEX.findall(re.sub(r"//[^\n]*","",text))


def resolve_source_refs(root:Path)->dict[str,list[str]]:
    root=Path(root)
    for relative in REQUIRED_FILES:
        if not (root/relative).is_file():
            raise FileNotFoundError(f"Missing pinned SFZ definition: {relative}")
    main=(root/REQUIRED_FILES[0]).read_text()
    for name in ("Data/notes.txt","Data/hammer.txt","Data/str_res.txt",
                 "Data/pedal.txt"):
        if f'#include "{name}"' not in main:
            raise ValueError(f"Main SFZ does not include {name}")
    notes=(root/"Data/notes.txt").read_text()
    note_regions=_refs(notes)
    if len(note_regions)!=30 or not all("$VEL" in t and "$EXT" in t
                                       for t in note_regions):
        raise ValueError("Expected 30 original pitch zones expanded by 16 velocities")
    result={"note":[],"release":[],"resonance":[],"pedal":[]}
    for v in range(1,17):
        text=(root/f"Data/vel_{v:02d}.txt").read_text()
        token=re.search(r"(?m)^\s*#define\s+\$VEL\s+(v\d+)\s*$",text)
        if not token or token.group(1)!=f"v{v}":
            raise ValueError(f"Invalid velocity zone {v}")
        for name in note_regions:
            result["note"].append(name.replace("$VEL",token.group(1))
                                      .replace("$EXT","flac"))
    for group,src in (("release","Data/hammer.txt"),
                      ("resonance","Data/str_res.txt"),("pedal","Data/pedal.txt")):
        values=_refs((root/src).read_text())
        result[group]=[x.replace("$EXT","flac") for x in values]
        if any("$" in x for x in result[group]):
            raise ValueError(f"Unsupported unexpanded sample token: {group}")
    # Check semantic MIDI pitch mapping before counts/duplicate detection.
    # This gives an actionable error when one release region is misrouted.
    release=(root/"Data/hammer.txt").read_text()
    if not re.search(r"\bkey=60\s+sample=rel40\.\$EXT",release):
        raise ValueError("Original MIDI-60 hammer release mapping changed")
    for group,expected in COUNTS.items():
        if len(result[group])!=expected or len(set(result[group]))!=expected:
            raise ValueError(f"Unexpected number of {group} sample regions")
    all_names=[x for names in result.values() for x in names]
    if len(all_names)!=641 or len(set(all_names))!=641:
        raise ValueError("Duplicate or missing sample declarations across groups")
    return result


def original_blob_sha(path:Path)->str:
    size=path.stat().st_size
    h=hashlib.sha1(b"blob "+str(size).encode()+b"\x00")
    with path.open("rb") as stream:
        for block in iter(lambda:stream.read(4*1024*1024),b""):
            h.update(block)
    return h.hexdigest()


def audit(root:Path,tree_json:Path,*,verify_sample_bytes:bool=False)->dict:
    refs=resolve_source_refs(root)
    data=json.loads(Path(tree_json).read_text())
    if data.get("truncated") or not isinstance(data.get("tree"),list):
        raise ValueError("Git source tree truncated or invalid")
    manifest={}
    for file in data["tree"]:
        path=file.get("path","")
        if path.startswith("Samples/") and path.endswith(".flac"):
            filename=path[len("Samples/"):]
            if filename in manifest:
                raise ValueError("Duplicate source sample in Git tree")
            if file.get("type")!="blob" or file.get("size",0)<=0:
                raise ValueError(f"Malformed Git sample: {path}")
            manifest[filename]={"git_blob_sha1":file["sha"],"bytes":file["size"]}
    all_refs={name for names in refs.values() for name in names}
    if set(manifest)!=all_refs:
        raise ValueError(
            f"SFZ/Git source mismatch: missing={sorted(all_refs-set(manifest))[:8]}, "
            f"unused={sorted(set(manifest)-all_refs)[:8]}")
    if len(manifest)!=641:
        raise ValueError("Unexpected full piano size")
    verified={}
    if verify_sample_bytes:
        for name,expected in sorted(manifest.items()):
            sample=Path(root)/"Samples"/name
            if not sample.is_file() or sample.stat().st_size!=expected["bytes"]:
                raise FileNotFoundError(f"Missing or wrong-size publisher FLAC: {name}")
            if original_blob_sha(sample)!=expected["git_blob_sha1"]:
                raise ValueError(f"Git blob SHA mismatch for original recording: {name}")
            info=sf.info(sample)
            if (info.format!="FLAC" or info.samplerate!=48000
                    or info.channels not in (1,2) or info.frames<=1000):
                raise ValueError(f"Unexpected FLAC sample format: {name}")
            verified[name]={"channels":info.channels,"seconds":round(info.duration,2)}
    return {
        "source":f"https://github.com/{UPSTREAM}",
        "pinned_commit":COMMIT,
        "license":"CC BY 3.0 — Alexander Holm; keep original attribution",
        "source_regions_by_group":{k:len(v) for k,v in refs.items()},
        "total_unique_original_flacs":len(manifest),
        "git_tree_total_bytes":sum(x["bytes"] for x in manifest.values()),
        "midi60_release_sample":"rel40.flac",
        "blob_sha_verified_count":len(verified),
        "flac_channel_histogram":dict(Counter(str(x["channels"]) for x in verified.values())),
        "sample_names_to_hashes":manifest,
        "caveat":"Static SFZ closure and source integrity, not ARIA opcode compatibility, speed or listener quality."
    }


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--sfz-root",type=Path,required=True)
    p.add_argument("--source-tree-json",type=Path,required=True)
    p.add_argument("--verify-sample-bytes",action="store_true")
    p.add_argument("--out",type=Path,default=Path("q4-full-source-report.json"))
    a=p.parse_args()
    result=audit(a.sfz_root,a.source_tree_json,
                 verify_sample_bytes=a.verify_sample_bytes)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(result,indent=2))
    print(json.dumps({k:v for k,v in result.items() if k!="sample_names_to_hashes"},indent=2))


if __name__=="__main__":
    main()

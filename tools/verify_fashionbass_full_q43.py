"""Q4.3 full original Karoryfer Fashionbass bank and optional bass render.

The source and published Music Studio assets never change. The 426 original
CC0 WAVs are all read/hashes against a pinned Git-tree fixture. The original
SFZ's Windows slashes are made portable only in a disposable derived map.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import soundfile as sf

from tools.audit_salamander_full_q4 import original_blob_sha
from tools.probe_fashionbass_q43 import validate_source


def verify_bank(source:Path,manifest_path:Path,*,out:Path)->dict:
    source=Path(source)
    manifest=json.loads(manifest_path.read_text())
    audit=validate_source(
        (source/"fashionbass.sfz").read_text(),
        (source/"fashionbass_clean.sfz").read_text(),manifest)
    counts={}
    durations=[]
    formats={}
    for entry in manifest["samples"]:
        rel=entry["path"]
        path=source/rel
        if not path.is_file() or path.stat().st_size!=entry["size"]:
            raise FileNotFoundError(f"Missing or wrong size original WAV: {rel}")
        if original_blob_sha(path)!=entry["sha"]:
            raise ValueError(f"Original publisher WAV was modified: {rel}")
        info=sf.info(path)
        if (info.format!="WAV" or info.samplerate not in (44100,48000)
                or info.channels not in (1,2) or info.frames<100):
            raise ValueError(f"Unexpected original WAV audio format: {rel}")
        k=rel.split("/",1)[0]
        counts[k]=counts.get(k,0)+1
        durations.append(info.duration)
        formats[f"{info.samplerate}/{info.channels}"]=formats.get(f"{info.samplerate}/{info.channels}",0)+1
    if counts!={"notes":285,"release":76,"noises":65}:
        raise ValueError("Original WAV groups changed after byte-level validation")
    # Derived map references the exact same original WAVs. Normalize only
    # Windows separators; the publisher SFZ remains unchanged and hashable.
    derived=source/"Q43_derived_full_recorded_bass.sfz"
    original=(source/"fashionbass.sfz").read_text()
    if original.count("\\")<300:
        raise ValueError("Unexpected source SFZ separator layout")
    derived.write_text(original.replace("\\","/"))
    audit.update({
        "source_repository":"https://github.com/sfzinstruments/karoryfer.fashionbass",
        "license":"CC0 1.0, Karoryfer Lecolds",
        "original_wavs_hash_and_audio_verified":426,
        "verified_recording_groups":counts,
        "recording_formats":formats,
        "original_seconds_min":round(min(durations),4),
        "original_seconds_max":round(max(durations),4),
        "derived_sfz":"Q43_derived_full_recorded_bass.sfz",
        "source_original_wavs_unchanged":True,
        "caveat":"Full original source integrity; musical quality, full SFZ opcode compatibility and audio still need separate tests."
    })
    out=Path(out)
    out.mkdir(parents=True,exist_ok=True)
    (out/"Q43_complete_original_bass_bank_report.json").write_text(json.dumps(audit,indent=2))
    print(json.dumps(audit,indent=2))
    return audit


if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--source",type=Path,required=True)
    p.add_argument("--manifest",type=Path,default=Path("tests/fixtures/q43_fashionbass_original_tree.json"))
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    verify_bank(a.source,a.manifest,out=a.out)

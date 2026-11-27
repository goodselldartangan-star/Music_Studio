"""Q4.3 CC0 Fashionbass complete source-map audit and 2-WAV release trigger.

Never invent a bass slide. Verify all 426 pinned original recordings' mapped
file names; stage only 2 Git-SHA-verified real WAVs for a controlled note-on
versus note-off release-layer render. The full 345 MB source remains optional.
"""
from __future__ import annotations
import json
import re
from pathlib import Path

import numpy as np
import soundfile as sf
import mido

from studio7.score import make
from studio7.effects import SR

REVISION="0703973b300a6bacb837602be9b588ab64732a72"
SOURCES={
    "notes/d2_mf_rr1.wav":"da8333b8e74c532d406d4e263c74378c074158ee",
    "release/d2_release_rr1.wav":"3e5a9f8ef67a4870d1ec81b0085ad6f19b37b197",
}


def _groups(text:str)->list[str]:
    return re.split(r"<group>",re.sub(r"(?m)//[^\n]*","",text))[1:]


def refs(text:str)->set[str]:
    names=re.findall(r"\bsample=([^\s<>]+)",text)
    if len(names)!=len(set(names)):
        raise ValueError("Duplicate recording region name")
    names=[name.replace("\\","/") for name in names]
    if any(name.startswith("/") or ".." in Path(name).parts
           for name in names):
        raise ValueError("Unsafe SFZ source sample path")
    return set(names)


def validate_source(full:str,clean:str,manifest:dict)->dict:
    if manifest.get("pinned_commit")!=REVISION or manifest.get("truncated"):
        raise ValueError("Wrong original publisher revision or incomplete Git tree")
    files={entry["path"]:entry for entry in manifest.get("samples",[])}
    if len(files)!=426 or any(not x.get("sha") or x.get("size",0)<=0
                               for x in files.values()):
        raise ValueError("Unexpected original sample-source manifest")
    all_refs=refs(full)
    clean_refs=refs(clean)
    if all_refs!=set(files):
        raise ValueError("Official SFZ and 426 source recordings do not match")
    if clean_refs != {p for p in all_refs if not p.startswith("release/")}:
        raise ValueError("Clean SFZ differs beyond original trigger-release sample exclusions")
    groups=_groups(full)
    release_groups=[g for g in groups if "trigger=release" in g]
    if len(release_groups)!=19:
        raise ValueError("Expected 19 original key-release pitch zones")
    if any(not re.search(r"\bsample=release",g) for g in release_groups):
        raise ValueError("Key-release region is not recorded release sample")
    playable=set()
    for group in groups:
        if "sample=notes" not in group:
            continue
        lo=re.search(r"\blokey=(\d+)",group)
        hi=re.search(r"\bhikey=(\d+)",group)
        if lo is None or hi is None:
            raise ValueError("Unbounded recorded note group")
        playable.update(range(int(lo[1]),int(hi[1])+1))
    scored={n["pitch"] for style in ("harbor","after","silver")
            for n in make(style)["notes"] if n["instrument"]=="bass"}
    if not scored.issubset(playable):
        raise ValueError("Original music contains bass pitches absent from Fashionbass")
    by_kind={k:sum(p.startswith(k+"/") for p in all_refs)
             for k in ("notes","release","noises")}
    if by_kind!={"notes":285,"release":76,"noises":65}:
        raise ValueError("Unexpected original recorded sample categories")
    if any(name not in files or files[name]["sha"]!=sha
           for name,sha in SOURCES.items()):
        raise ValueError("Pinned original release-note test WAV identity changed")
    return {
        "pinned_git_revision":REVISION,
        "source_original_records":426,
        "source_original_wav_bytes":sum(x["size"] for x in files.values()),
        "source_regions_by_category":by_kind,
        "release_key_groups":len(release_groups),
        "original_three_scores_bass_pitches":sorted(scored),
        "all_original_bass_pitches_covered":True,
        "two_sound_probe_original_sha":SOURCES,
        "caveat":"File-index completeness only. Full-bank bytes and original full SFZ opcode behavior still require independent verification."
    }


def prepare_minimal_original(root:Path)->None:
    root=Path(root)
    samples=root/"Samples"
    for name in SOURCES:
        if not (samples/name).is_file():
            raise FileNotFoundError(f"Missing original pinned source WAV {name}")
    # The two SFZ variants use the SAME untouched original real note.
    # Only the sample-recorded key-release is toggled; no synthetic noise.
    base=(
        "<group>\nkey=38\npitch_keycenter=38\n"
        "ampeg_release=0.050\n"
        "<region> sample=Samples/notes/d2_mf_rr1.wav\n")
    rel=(
        "<group>\nkey=38\ntrigger=release\npitch_keycenter=38\n"
        "volume=-8\nrt_decay=5\n"
        "<region> sample=Samples/release/d2_release_rr1.wav\n")
    (root/"Q43_note_only.sfz").write_text(base)
    (root/"Q43_original_release.sfz").write_text(base+"\n"+rel)
    # Both render identical MIDI (fixed 120 BPM = 960 ticks/second).
    # 0.10s NOTE ON, 0.70s NOTE OFF; sentinel out-of-range ensures tail.
    ticks=[(96,mido.Message("note_on",note=38,velocity=84,channel=0)),
           (672,mido.Message("note_off",note=38,velocity=0,channel=0)),
           (1920,mido.Message("note_on",note=1,velocity=1,channel=9)),
           (2112,mido.Message("note_off",note=1,velocity=0,channel=9))]
    midi=mido.MidiFile(ticks_per_beat=480)
    track=mido.MidiTrack()
    track.append(mido.MetaMessage("set_tempo",tempo=500000,time=0))
    prev=0
    for tick,msg in ticks:
        track.append(msg.copy(time=tick-prev))
        prev=tick
    track.append(mido.MetaMessage("end_of_track",time=2400-prev))
    midi.tracks.append(track)
    midi.save(root/"Q43_original_release.mid")


def _read(path:Path)->np.ndarray:
    audio,sr=sf.read(path,dtype="float32",always_2d=True)
    if sr!=SR or audio.shape[1]!=2 or not np.isfinite(audio).all():
        raise ValueError("Invalid authentic source playback")
    return audio


def inspect_minimal_original(root:Path)->dict:
    root=Path(root)
    plain=_read(root/"Q43_note_only.wav")
    with_release=_read(root/"Q43_original_release.wav")
    n=min(len(plain),len(with_release))
    if n<round(1.35*SR):
        raise ValueError("Rendered sample cut off early")
    plain=plain[:n]
    with_release=with_release[:n]
    def rms(x):
        return float(np.sqrt(np.mean(np.asarray(x,np.float64)**2)))
    before=slice(round(.2*SR),round(.65*SR))
    after=slice(round(.72*SR),round(1.07*SR))
    attack_difference=rms(plain[before]-with_release[before])
    release_difference=rms(plain[after]-with_release[after])
    if rms(plain[before])<=1e-6 or not np.isfinite(release_difference):
        raise AssertionError("Original recorded bass note did not sound")
    # A release sample should make NO change before the actual note-off.
    if attack_difference>1e-6:
        raise AssertionError("Release-only variant changed the original source attack")
    if release_difference<=1e-6:
        raise AssertionError("Actual original release recording did not trigger")
    if max(float(np.max(abs(plain))),float(np.max(abs(with_release))))>=.99:
        raise AssertionError("Authentic sample signal clipped")
    report={
        "source":"Karoryfer Fashionbass original CC0 recorded WAV",
        "single_original_note":"notes/d2_mf_rr1.wav",
        "single_original_release":"release/d2_release_rr1.wav",
        "release_trigger":"SFZ trigger=release, not synthesized transient",
        "note_on_seconds":.1,
        "note_off_seconds":.7,
        "original_note_before_off_rms":round(rms(plain[before]),8),
        "pre_noteoff_variant_difference_rms":round(attack_difference,9),
        "post_noteoff_recorded_release_difference_rms":round(release_difference,9),
        "original_note_peak":round(float(np.max(abs(plain))),6),
        "original_with_release_peak":round(float(np.max(abs(with_release))),6),
        "real_recorded_release_trigger_verified":True,
        "limitations":"Two exact original WAVs only. Complete 426-file compatibility and musical taste not yet accepted."
    }
    (root/"Q43_Fashionbass_2WAV_release_report.json").write_text(json.dumps(report,indent=2))
    print(json.dumps(report,indent=2))
    return report


if __name__=="__main__":
    import argparse
    p=argparse.ArgumentParser()
    p.add_argument("stage",choices=("audit","prepare","inspect"))
    p.add_argument("--root",required=True,type=Path)
    p.add_argument("--manifest",type=Path,default=Path("tests/fixtures/q43_fashionbass_original_tree.json"))
    a=p.parse_args()
    a.root.mkdir(parents=True,exist_ok=True)
    if a.stage=="audit":
        report=validate_source(
            (a.root/"fashionbass.sfz").read_text(),
            (a.root/"fashionbass_clean.sfz").read_text(),
            json.loads(a.manifest.read_text()))
        (a.root/"Q43_Fashionbass_source_audit.json").write_text(json.dumps(report,indent=2))
        print(json.dumps(report,indent=2))
    elif a.stage=="prepare":
        prepare_minimal_original(a.root)
    else:
        inspect_minimal_original(a.root)

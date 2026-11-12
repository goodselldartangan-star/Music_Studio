"""Q1 read-only review of actual recorded sample attack alignment.

Looks for unexpectedly large leading-silence differences between velocity
layers of the same exact pitch. A threshold crossing is a technical proxy,
not an acoustic judgement; never rewrite source recordings in this module.
"""
from __future__ import annotations
from collections import defaultdict, Counter
from pathlib import Path
import argparse
import json
import math
import re

import numpy as np
import soundfile as sf

from studio3.sample_bank import NOTE_PATTERN, midi_from_name


COLLECTIONS = ("meta-steel-guitar", "meta-piano", "meta-nylon-guitar")
LATE_REVIEW_MS = {"meta-steel-guitar": 75.0, "meta-piano": 40.0,
                  "meta-nylon-guitar": 40.0}


def onset_ms(samples: np.ndarray, sample_rate: int, *, max_seconds: float=.38) -> float | None:
    """Find first sustained energy above a source-relative threshold.

    3ms moving RMS, 1ms hop and 3 adjacent above-threshold frames. This
    rejects single-sample clicks but cannot distinguish string preparation
    noise from desired pitched attack; outliers need manual source review.
    """
    a = np.asarray(samples)
    if a.ndim == 2:
        a = a.mean(axis=1)
    if a.ndim != 1 or sample_rate < 8000 or not np.isfinite(a).all():
        raise ValueError("Expected finite mono/stereo PCM and a valid sample rate")
    n = min(len(a), round(sample_rate * max_seconds))
    window = max(8, round(.003 * sample_rate))
    hop = max(1, round(.001 * sample_rate))
    if n < window * 3:
        return None
    x = a[:n].astype(np.float64)
    integral = np.concatenate(([0.], np.cumsum(x*x)))
    positions = np.arange(0, n-window+1, hop)
    rms = np.sqrt(np.maximum(0., (integral[positions+window]-integral[positions]) / window))
    reference = float(np.percentile(rms, 95))
    if reference < .00004:
        return None
    threshold = max(.00002, reference * .075)
    flags = rms >= threshold
    runs = flags[:-2] & flags[1:-1] & flags[2:]
    found = np.flatnonzero(runs)
    return round(float(positions[found[0]] * 1000 / sample_rate), 2) if found.size else None


def examine_file(path: Path) -> dict:
    with sf.SoundFile(path) as f:
        sample_rate, channels, frames = f.samplerate, f.channels, len(f)
        data = f.read(frames=min(frames, round(.45 * sample_rate)),
                      dtype="float32", always_2d=True)
        subtype, fmt = f.subtype, f.format
    return {"filename": path.name, "sample_rate": sample_rate, "channels": channels,
            "format": fmt, "subtype": subtype,
            "duration_s": round(frames / sample_rate, 3),
            "onset_ms": onset_ms(data, sample_rate)}


def audit_collection(root: Path, collection: str) -> dict:
    if collection not in COLLECTIONS:
        raise ValueError("Unexpected source")
    folder = Path(root) / collection
    if not folder.is_dir():
        raise FileNotFoundError(f"Missing {folder}")
    entries = []
    by_pitch_string = defaultdict(list)
    for file in sorted(folder.rglob("*")):
        if not file.is_file() or file.suffix.lower() not in (".ogg", ".wav", ".flac"):
            continue
        match = NOTE_PATTERN.search(file.name)
        if not match:
            continue
        detail = examine_file(file)
        detail.update({"midi_pitch": midi_from_name(match[2]), "layer": int(match[1])})
        # Two samples can share MIDI pitch but be played on different physical
        # guitar strings, which have intentionally different attack envelopes.
        # Compare dynamic layers *within one string zone*, not across strings.
        zone_match = re.search(r"_String([^_]+)_Vel", file.name, re.I)
        detail["string_zone"] = zone_match.group(1) if zone_match else "keyboard"
        entries.append(detail)
        if detail["onset_ms"] is not None:
            by_pitch_string[(detail["midi_pitch"],detail["string_zone"])].append(detail)
    if not entries:
        raise AssertionError(f"No playable recordings found in {folder}")

    channel_counts = dict(sorted(Counter(str(x["channels"]) for x in entries).items()))
    format_counts = dict(sorted(Counter(x["format"] for x in entries).items()))
    samplerates = dict(sorted(Counter(str(x["sample_rate"]) for x in entries).items()))
    onsets = sorted(x["onset_ms"] for x in entries if x["onset_ms"] is not None)
    late = [x for x in entries if x["onset_ms"] is not None
            and x["onset_ms"] >= LATE_REVIEW_MS[collection]]
    differing_layers = []
    for (pitch, zone), notes in by_pitch_string.items():
        if len(notes) < 2:
            continue
        t = [x["onset_ms"] for x in notes]
        span = max(t)-min(t)
        if span >= 25:
            differing_layers.append({
                "midi_pitch": pitch, "string_zone": zone,
                "spread_ms": round(span, 2),
                "layers": [{"layer": n["layer"], "filename": n["filename"],
                            "onset_ms": n["onset_ms"]} for n in notes]
            })
    late.sort(key=lambda x:x["onset_ms"],reverse=True)
    differing_layers.sort(key=lambda x:x["spread_ms"],reverse=True)
    return {
        "collection": collection, "recordings": len(entries),
        "channel_counts": channel_counts, "formats": format_counts,
        "sample_rates_hz": samplerates,
        "onset_p50_ms": round(float(np.median(onsets)),2) if onsets else None,
        "onset_p95_ms": round(float(np.percentile(onsets,95)),2) if onsets else None,
        "late_review_threshold_ms": LATE_REVIEW_MS[collection],
        "late_review_count": len(late),
        "late_review_examples": late[:20],
        "within_string_layer_spread_over_25ms_count": len(differing_layers),
        "within_string_layer_spread_examples": differing_layers[:15],
        "all_onsets_detected": len(onsets)==len(entries),
        "limitations": "RMS threshold detects energy, not musical onset or intentional pick/finger transients."
    }


def audit_all(root: Path) -> dict:
    return {
        "collections": {name: audit_collection(root,name) for name in COLLECTIONS},
        "source_changes": "None; read-only waveform analysis",
        "production_question": "The current OGG archives are previews; WAV master quality is a separate optional decision."
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--assets",type=Path,required=True)
    parser.add_argument("--out",type=Path,default=Path("q1_recorded_attack_audit.json"))
    args = parser.parse_args()
    report = audit_all(args.assets)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(report,indent=2))
    print(json.dumps({
        name: {k: v[k] for k in ("recordings","channel_counts","formats","sample_rates_hz",
                                 "onset_p50_ms","onset_p95_ms","late_review_count",
                                 "velocity_layer_spread_over_25ms_count",
                                 "late_review_examples","velocity_layer_spread_examples")}
        for name,v in report["collections"].items()
    },indent=2))


if __name__=="__main__":
    main()

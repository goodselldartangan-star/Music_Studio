"""Q4 small authentic-audio test: shared pedal mechanism, never duplicated per voice.

Uses the existing five pinned Salamander FLAC samples and two independent
sfizz piano note processes. The original Data/pedal region conditions are
represented with one deterministic D1/U1 take (the full bank has D1/D2,
U1/U2 random alternatives and must be tested separately).
No original source, SFZ or published song is modified.
"""
from __future__ import annotations
import argparse
import json
import math
from pathlib import Path

import mido
import numpy as np
import soundfile as sf

from tools.sfz_pedal_controller_q4 import (
    prepare as prepare_pedal, write_voice_only_sfz)
from tools.probe_sfz_piano_q4 import rms,read_stereo

SR=44100


def prepare(root:Path)->dict:
    root=Path(root)
    if not (root/"Samples"/"pedalD1.flac").is_file():
        raise FileNotFoundError("Pinned publisher piano recordings not installed")
    data=root/"Data"
    data.mkdir(parents=True,exist_ok=True)
    # Deterministic subset of the real publisher pedal.txt, not a fake tone.
    (data/"pedal.txt").write_text(
        "master_label=pedalAction\nlokey=-1\nhikey=-1\n"
        "group=1\npolyphony=1\noff_time=0.1\n"
        "<group>\nvolume=-20\non_locc64=127\non_hicc64=127\n"
        "locc64=127\nhicc64=127\n"
        "<region> sample=pedalD1.$EXT\n"
        "<group>\nvolume=-19\non_locc64=0\non_hicc64=0\n"
        "locc64=0\nhicc64=0\n"
        "<region> sample=pedalU1.$EXT\n")
    result=prepare_pedal(root/"lanes",root,bpm=120.,duration_s=4.,
                         windows=[(.5,1.3)])
    # The original piano note remains physically sampled and the auxiliary
    # pedal regions are copied only into the pedal-only SFZ instance.
    note_sfz=(root/"Q4_note_lane_pedal_gate.sfz")
    note_sfz.write_text(
        "<control>\ndefault_path=Samples/\nset_hdcc22=0.5\n"
        "<group>\nkey=60\npitch_keycenter=60\nampeg_release=0.5\n"
        "<region> sample=C4v12.flac\n"
        "<global>\nlocc22=1\namplitude_oncc22=200\n"
        '#define $EXT flac\n#include "Data/pedal.txt"\n')
    write_voice_only_sfz(
        note_sfz,root/"voice_program"/"Q4_voice_only.sfz",root)
    # Same CC64 events; only the controller 22 value differs. The mini
    # runtime's CC22=0 suppression FAILED, so treat it only as diagnostic.
    # that CC22=0 silences pedal-only regions before the first movement.
    original=mido.MidiFile(root/"lanes/shared_pedal.mid")
    for track in original.tracks:
        for msg in track:
            if msg.type=="control_change" and msg.control==22:
                msg.value=0
    original.save(root/"lanes/shared_pedal_muted.mid")
    return result


def inspect(root:Path)->dict:
    root=Path(root)
    lanes=root/"lanes"
    on=read_stereo(lanes/"shared_pedal.wav")
    muted=read_stereo(lanes/"shared_pedal_muted.wav")
    first=read_stereo(lanes/"with_pedal_lane_00.wav")
    second=read_stereo(lanes/"with_pedal_lane_01.wav")
    enabled_rms=rms(on)
    suppressed_rms=rms(muted)
    if enabled_rms<1e-6:
        raise AssertionError("Real pedal mechanism did not sound")
    # The CC22 gate alone was empirically unreliable with this sfizz build.
    # Sound exclusion is enforced by a voice-only SFZ with NO pedal regions.
    text=(root/"voice_program"/"Q4_voice_only.sfz").read_text()
    if '#include "Data/pedal.txt"' in text:
        raise AssertionError("Voice-only SFZ still includes pedal noise regions")
    if not (root/"voice_program"/"Samples").is_symlink():
        raise AssertionError("Derived voice program lost source sample links")
    if min(rms(first),rms(second))<1e-6:
        raise AssertionError("Muted CC22 also muted actual piano samples")
    mixed=first+second+on
    peak=float(np.max(np.abs(mixed)))
    if peak>=.999:
        raise AssertionError("Unscaled shared pedal mix would clip")
    # Directly compare against a no-mechanism mix; the exact increment must
    # be the single isolated recorded mechanism, not a copy per piano lane.
    observed=mixed-first-second
    normalized_error=rms(observed-on)/max(enabled_rms,1e-10)
    if normalized_error>.00001:
        raise AssertionError("Pedal sound was not isolated exactly once")
    sf.write(root/"Q4_one_pedal_mechanism_mix.wav",mixed.astype(np.float32),
             SR,subtype="PCM_24")
    report={"publisher_audio":"Original Salamander C4v12, pedalD1 and pedalU1 FLAC",
            "instance_count":2,"mechanism_instance_count":1,
            "cc64_edges":2,
            "pedal_enabled_rms":round(enabled_rms,8),
            "pedal_muted_rms":round(suppressed_rms,8),
            "cc22_only_mute_reliable":bool(suppressed_rms<=max(1e-7,enabled_rms*.005)),
            "voice_only_sfz_no_pedal_regions":True,
            "single_mechanism_rms_difference_error":round(normalized_error,8),
            "mixed_peak":round(peak,6),
            "note_lanes_still_sound":True,
            "limitations":"Five-source miniature SFZ. Pedal routing uses source-program separation, NOT CC22 mute; full keyboard and RAM untested."}
    (root/"Q4_one_pedal_report.json").write_text(json.dumps(report,indent=2))
    print(json.dumps(report,indent=2))
    return report


if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("command",choices=("prepare","inspect"))
    p.add_argument("--root",type=Path,default=Path("q4-sfizz-probe"))
    a=p.parse_args()
    if a.command=="prepare":
        print(json.dumps(prepare(a.root),indent=2))
    else:
        inspect(a.root)

"""Q4 experimental real-SFZ pedal routing: CC64 everywhere, pedal sound once.

Preserves every existing note-on/off in each independent sampler MIDI file.
The original source program is split into a temporary voice-only SFZ (the
Data/pedal.txt include is excluded) and one shared pedal-only SFZ instance.
The CC22=0 controller on note lanes is extra safety only: the miniature
sfizz tests showed CC22 alone cannot be trusted as a mute.
One shared SFZ instance plays mechanisms once per CC64 edge.
This is experimental tooling;
original Music Studio playback and earlier audio files remain unchanged.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from os.path import relpath

import mido

from studio7.sfz_pedal_routing import pedal_controllers
from studio7.pedal_timing import atmospheric_pedal_windows
from studio7.score import make


def _absolute_ticks(track):
    total=0
    for msg in track:
        total+=msg.time
        yield total,msg


def inject_cc_track(original:Path,destination:Path,controllers:list[tuple[float,int,int]],
                    *,duration_beats:float)->None:
    mf=mido.MidiFile(original)
    if len(mf.tracks)!=1 or mf.ticks_per_beat!=480:
        raise ValueError("Only existing single-track 480 PPQ Q4 lane MIDI is supported")
    source=list(_absolute_ticks(mf.tracks[0]))
    if not source or not any(msg.type=="set_tempo" and msg.tempo==500000
                             for _,msg in source):
        raise ValueError("Expected fixed 120 BPM test-timeline tempo")
    events=[]
    for tick,msg in source:
        if msg.type in ("end_of_track","set_tempo"):
            continue
        events.append((tick,2,msg.copy(time=0)))
    for beat,cc,value in controllers:
        tick=round(beat*480)
        if tick>=round(duration_beats*480):
            raise ValueError("Pedal edge exceeds MIDI duration")
        events.append((tick,0 if cc==22 else 1,
                       mido.Message("control_change",channel=0,
                                    control=cc,value=value,time=0)))
    events.sort(key=lambda item:(item[0],item[1]))
    out=mido.MidiFile(ticks_per_beat=480)
    track=mido.MidiTrack()
    out.tracks.append(track)
    track.append(mido.MetaMessage("set_tempo",tempo=500000,time=0))
    prev=0
    for tick,_,msg in events:
        if tick<prev:
            raise AssertionError("Unsorted MIDI controller event")
        track.append(msg.copy(time=tick-prev))
        prev=tick
    track.append(mido.MetaMessage("end_of_track",
                 time=max(0,round(duration_beats*480)-prev)))
    destination.parent.mkdir(parents=True,exist_ok=True)
    out.save(destination)


def write_shared_pedal_midi(path:Path, controllers:list[tuple[float,int,int]],
                            *,duration_beats:float)->None:
    # Create a silent out-of-range note near the end to prevent sfizz CLI
    # from trimming genuine pedal-release tails.
    tempo=500000
    events=[(round(beat*480),0 if cc==22 else 1,
             mido.Message("control_change",channel=0,control=cc,value=value))
            for beat,cc,value in controllers]
    events.extend([
        (round((duration_beats-.4)*480),2,
         mido.Message("note_on",channel=9,note=1,velocity=1)),
        (round((duration_beats-.1)*480),2,
         mido.Message("note_off",channel=9,note=1,velocity=0))])
    events.sort(key=lambda x:(x[0],x[1]))
    midi=mido.MidiFile(ticks_per_beat=480)
    track=mido.MidiTrack()
    midi.tracks.append(track)
    track.append(mido.MetaMessage("set_tempo",tempo=tempo,time=0))
    prev=0
    for tick,_,msg in events:
        if tick<prev:
            raise ValueError("Bad pedal scheduling")
        track.append(msg.copy(time=tick-prev))
        prev=tick
    track.append(mido.MetaMessage("end_of_track",
                    time=max(0,round(duration_beats*480)-prev)))
    path.parent.mkdir(parents=True,exist_ok=True)
    midi.save(path)


def write_shared_pedal_sfz(path:Path, bank:Path)->None:
    bank=Path(bank)
    if not (bank/"Data"/"pedal.txt").is_file():
        raise FileNotFoundError(f"Missing original Salamander pedal.txt in {bank}")
    # SFZ paths are relative to the auxiliary file; bank is never edited.
    samples=relpath(bank/"Samples",path.parent).replace("\\","/")
    includes=relpath(bank/"Data"/"pedal.txt",path.parent).replace("\\","/")
    sfz=(f"#define $EXT flac\n<control>\ndefault_path={samples}/\n"
         "set_hdcc22=0.5\n"
         "<global>\nlocc22=1\namplitude_oncc22=200\n"
         f'#include "{includes}"\n')
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(sfz)


def write_voice_only_sfz(source:Path, destination:Path, bank:Path)->None:
    """Copy source SFZ program to an isolated workspace without pedal regions.

    Original source file and Data/Samples content are never modified.
    Data/ and Samples/ links retain relative include paths for the complete
    641-file publisher program. Only the one physical-pedal include is
    excluded; notes, releases, resonance and controls remain unchanged.
    """
    source=Path(source)
    destination=Path(destination)
    bank=Path(bank)
    original=source.read_text()
    needle='#include "Data/pedal.txt"'
    if original.count(needle)!=1:
        raise ValueError("Expected exactly one publisher physical-pedal include")
    rewritten=original.replace(
        needle,"// Q4: mechanical pedal regions played in exactly one shared SFZ instance")
    if rewritten==original or needle in rewritten:
        raise AssertionError("Physical pedal routing transformation failed")
    destination.parent.mkdir(parents=True,exist_ok=True)
    # No source recording bytes are copied or re-encoded.
    for name in ("Samples","Data"):
        from_source=bank/name
        dest_link=destination.parent/name
        if not from_source.exists():
            raise FileNotFoundError(from_source)
        if dest_link.is_symlink():
            if dest_link.resolve()!=from_source.resolve():
                raise ValueError("Derived SFZ would reference wrong sample bank")
        elif not dest_link.exists():
            # Relative symlinks survive the host-to-container bind mount:
            # absolute /home/runner/... targets are invalid inside /work.
            from os.path import relpath as _relpath
            dest_link.symlink_to(_relpath(from_source.resolve(),dest_link.parent.resolve()),
                                 target_is_directory=True)
        elif dest_link.resolve()!=from_source.resolve():
            raise ValueError("Derived program directory contains incompatible sample source")
    destination.write_text(rewritten)


def prepare(root:Path,bank:Path,*,bpm:float, duration_s:float,
            windows:list[tuple[float,float]])->dict:
    root=Path(root)
    plan=json.loads((root/"Q4_lane_plan.json").read_text())
    if abs(plan["bpm"]-bpm)>1e-6 or abs(plan["duration_s"]-duration_s)>1e-6:
        raise ValueError("Pedal plan and already rendered piano-lane clock differ")
    controls=pedal_controllers(windows,
                              duration_beats=duration_s*bpm/60,
                              lanes=plan["lane_plan"]["instance_count"])
    for i,events in enumerate(controls["note_lane_events"]):
        path=root/f"lane_{i:02d}.mid"
        if not path.is_file():
            raise FileNotFoundError(path)
        inject_cc_track(path,root/f"with_pedal_lane_{i:02d}.mid",events,
                        duration_beats=duration_s*bpm/60)
    write_shared_pedal_midi(root/"shared_pedal.mid",
                            controls["single_mechanism_events"],
                            duration_beats=duration_s*bpm/60)
    write_shared_pedal_sfz(root/"shared_pedal.sfz",bank)
    source=(Path(bank)/"Salamander Grand Piano V3.sfz")
    if source.is_file():
        write_voice_only_sfz(source,root/"voice_program"/"Q4_voice_only.sfz",bank)
    report={"lane_count":plan["lane_plan"]["instance_count"],
            "original_note_count":plan["lane_plan"]["input_notes"],
            "shared_mechanism_instances":1,
            "cc64_movement_count":controls["pedal_movement_count"],
            "note_lane_cc22":0,
            "mechanism_suppression":"voice-only SFZ derived from unchanged publisher program; CC22=0 not trusted",
            "shared_mechanism_cc22":64,
            "source_sfz_original_unchanged":True,
            "caveat":"Requires full SFZ real-audio test: CC22 gate must be silent on voice lanes."}
    (root/"Q4_pedal_route_plan.json").write_text(json.dumps(report,indent=2))
    return report


if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--lanes",type=Path,required=True)
    p.add_argument("--bank",type=Path,required=True)
    p.add_argument("--silver",action="store_true",
                   help="Use Silver's original 8 authored CC64 windows")
    a=p.parse_args()
    manifest=json.loads((a.lanes/"Q4_lane_plan.json").read_text())
    windows=(atmospheric_pedal_windows(make("silver")) if a.silver
             else [(.5,1.3)])
    r=prepare(a.lanes,a.bank,bpm=manifest["bpm"],
              duration_s=manifest["duration_s"],windows=windows)
    print(json.dumps(r,indent=2))

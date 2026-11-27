"""Q4 offline SFZ feasibility probe with exact upstream Salamander samples.

Two stages: prepare (verify publisher Git blob identities and produce SFZ/MIDI),
and inspect (compare PCM waveforms produced by external sfizz_render). This is
NOT a new piano renderer in Music Studio, and is never used by default.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path

import mido
import numpy as np
import soundfile as sf

COMMIT = "3382bf9496bba2486f5ab0de55a264d1dfc38404"
UPSTREAM = "https://github.com/sfzinstruments/SalamanderGrandPiano"
LICENSE = "CC BY 3.0 — Salamander Grand Piano V3, Alexander Holm"
# Git object IDs from the publisher's commit. These protect against silently
# changed source recordings and need no extra hash dependency.
SAMPLES = {
    "C4v12.flac": "418e7e1b4ebedc6c9104f711118144941ee4cd06",
    "rel60.flac": "35dba2623fa2420c4062752f45e16bbd2fd18f72",
    "harmV3C4.flac": "893b2c86d76ce1ac7b901605e060abe6330dd850",
    "pedalD1.flac": "098828eb035e42354de3b0710556bbcb0f29fc27",
    "pedalU1.flac": "b7c0e6228151fcc148837b5aa7a55f0007193618",
}

# Only four seconds of audio. The long note, short re-pluck, pedal movements,
# and key-off layers all use source recordings (not generated piano sounds).
CASES = {
    "old": [(0.2, "on", 0, 80), (2.4, "off", 0, 0)],
    "new_loud": [(0.9, "on", 0, 110), (1.15, "off", 0, 0)],
    "new_soft": [(0.9, "on", 0, 40), (1.15, "off", 0, 0)],
    "new_split": [(0.9, "on", 1, 110), (1.15, "off", 1, 0)],
    "both_loud": [(0.2, "on", 0, 80), (0.9, "on", 0, 110),
                  (1.15, "off", 0, 0), (2.4, "off", 0, 0)],
    "both_soft": [(0.2, "on", 0, 80), (0.9, "on", 0, 40),
                  (1.15, "off", 0, 0), (2.4, "off", 0, 0)],
    "both_split": [(0.2, "on", 0, 80), (0.9, "on", 1, 110),
                   (1.15, "off", 1, 0), (2.4, "off", 0, 0)],
    "note_release": [(0.2, "on", 0, 90), (0.75, "off", 0, 0)],
    "pedal": [(0.45, "cc", 0, 127), (1.45, "cc", 0, 0)],
    "quiet": [],
}

# The note_polyphony/off_time settings match the problematic voice policy in
# the original SFZ, but the miniature tests do NOT claim complete compatibility
# with its 16 velocity layer instrument or its ARIA extensions.
BASE = ("<control>\ndefault_path=Samples/\n"
        "<global>\nvolume=-10\n"
        "<region> key=60 pitch_keycenter=60 sample=C4v12.flac "
        "ampeg_attack=0.001 ampeg_release=0.5\n")
LIMITED = ("<control>\ndefault_path=Samples/\n"
           "<global>\nvolume=-10 note_polyphony=1 off_time=0.5\n"
           "<region> key=60 pitch_keycenter=60 sample=C4v12.flac "
           "ampeg_attack=0.001 ampeg_release=0.5\n")
KEY_RELEASE = ("<group>\nkey=60 trigger=release volume=-5\n"
               "<region> sample=rel60.flac\n")
RESONANCE = ("<group>\nkey=60 trigger=release volume=-7\n"
             "<region> sample=harmV3C4.flac\n")
PEDAL = ("<control>\ndefault_path=Samples/\n"
         "<group>\nlokey=-1 hikey=-1 on_locc64=127 on_hicc64=127 "
         "locc64=127 hicc64=127\n"
         "<region> sample=pedalD1.flac volume=-12\n"
         "<group>\nlokey=-1 hikey=-1 on_locc64=0 on_hicc64=0 "
         "locc64=0 hicc64=0\n"
         "<region> sample=pedalU1.flac volume=-12\n")
VARIANTS = {
    "unlimited": (BASE, ("old","new_loud","new_soft","new_split",
                         "both_loud","both_soft","both_split","note_release")),
    "limited": (LIMITED, ("old","new_loud","new_soft","new_split",
                         "both_loud","both_soft","both_split")),
    "release": (BASE+KEY_RELEASE, ("note_release",)),
    "resonance": (BASE+KEY_RELEASE+RESONANCE, ("note_release",)),
    "pedal": (PEDAL, ("quiet","pedal")),
}


def verify_original_samples(root: Path) -> dict:
    root=Path(root)
    if not root.is_dir():
        raise FileNotFoundError(root)
    report={}
    for name,expected in SAMPLES.items():
        path=root/name
        blob=path.read_bytes()
        gitsha=hashlib.sha1(b"blob "+str(len(blob)).encode()+b"\x00"+blob).hexdigest()
        if gitsha!=expected:
            raise ValueError(f"Publisher Git blob mismatch for {name}")
        info=sf.info(path)
        if (info.format!="FLAC" or info.samplerate!=48000 or
                info.channels not in (1,2) or info.frames<=1000):
            raise ValueError(f"Unexpected publisher sample format: {name}")
        report[name]={"git_blob_sha1":gitsha,"bytes":len(blob),
                      "sample_rate":info.samplerate,"channels":info.channels,
                      "duration_s":round(info.duration,3)}
    return report


def _write_midi(file:Path, events:list[tuple]) -> None:
    mf=mido.MidiFile(ticks_per_beat=480)
    track=mido.MidiTrack()
    mf.tracks.append(track)
    track.append(mido.MetaMessage("set_tempo",tempo=500_000,time=0))
    prev=0
    # 120 BPM and 480 ticks/beat, so 960 ticks/sec.
    # sfizz_render can stop on the final audible note-off, even with EOT.
    # A note on unmapped MIDI key 1 at 3.8s extends its render horizon,
    # allowing release/pedal resonance to finish without adding audible piano.
    guarded=[*events,(3.8,"sentinel_on",9,1),(3.95,"sentinel_off",9,1)]
    for when,kind,channel,value in sorted(guarded,key=lambda e:(e[0],0 if e[1] in ("off","sentinel_off") else 1)):
        tick=round(when*960)
        if kind.startswith("sentinel_"):
            msg=mido.Message("note_on" if kind=="sentinel_on" else "note_off",
                             channel=channel,note=1,
                             velocity=1 if kind=="sentinel_on" else 0,
                             time=tick-prev)
        elif kind=="cc":
            msg=mido.Message("control_change",channel=channel,control=64,value=value,
                             time=tick-prev)
        elif kind=="on":
            msg=mido.Message("note_on",channel=channel,note=60,velocity=value,
                             time=tick-prev)
        else:
            msg=mido.Message("note_off",channel=channel,note=60,velocity=0,
                             time=tick-prev)
        track.append(msg)
        prev=tick
    track.append(mido.MetaMessage("end_of_track",time=3840-prev))
    mf.save(file)


def prepare(out:Path) -> dict:
    out=Path(out)
    samples=verify_original_samples(out/"Samples")
    entries=[]
    for variant,(sfz,scenarios) in VARIANTS.items():
        (out/f"{variant}.sfz").write_text(sfz)
        for case in scenarios:
            midi=f"{variant}_{case}.mid"
            wav=f"{variant}_{case}.wav"
            _write_midi(out/midi,CASES[case])
            entries.append({"sfz":f"{variant}.sfz","midi":midi,"wav":wav})
    (out/"render_plan.json").write_text(json.dumps(entries,indent=2))
    provenance={"publisher":UPSTREAM,"commit":COMMIT,"license":LICENSE,
                "samples":samples,"render_plan":entries,
                "scope":"Selected actual recorded samples in a minimal SFZ, not full Salamander instrument"}
    (out/"source_identity.json").write_text(json.dumps(provenance,indent=2))
    return provenance


def read_stereo(path:Path,length:int=4*44100)->np.ndarray:
    x,sr=sf.read(path,dtype="float32",always_2d=True)
    if sr!=44100 or x.shape[1]!=2 or len(x)<round(3.8*sr) or not np.isfinite(x).all():
        raise AssertionError(f"Invalid or truncated sfizz output: {path.name} ({len(x)/sr:.3f}s)")
    y=np.zeros((length,2),np.float64)
    n=min(length,len(x))
    y[:n]=x[:n]
    return y


def rms(x:np.ndarray)->float:
    return float(np.sqrt(np.mean(x*x)))


def _window(x:np.ndarray,t0:float,t1:float)->np.ndarray:
    return x[round(t0*44100):round(t1*44100)]


def _voice_metrics(old:np.ndarray,new:np.ndarray,both:np.ndarray)->dict:
    t0,t1=.94,1.11
    expected=old+new
    reference=max(rms(_window(expected,t0,t1)),1e-10)
    discrepancy=rms(_window(both-expected,t0,t1))/reference
    # After the short note is released, this window assesses whether the old
    # 2.4-second hold continues. It may additionally expose same-key MIDI-off
    # semantics; caller should not interpret a nonzero ratio as *only* SFZ
    # self-masking.
    tail_old=rms(_window(old,1.4,1.9))
    tail_actual=rms(_window(both,1.4,1.9))
    after_expected=_window(expected,1.4,1.9)
    after_actual=_window(both,1.4,1.9)
    after_error=rms(after_actual-after_expected)/max(rms(after_expected),1e-12)
    # Before the short note-off, sample voices can add almost linearly;
    # after it, a same-pitch note-off may inadvertently stop the older note.
    # This is not unambiguously attributable to note_polyphony alone.
    return {"sum_waveform_relative_error":round(discrepancy,5),
            "post_short_noteoff_relative_error":round(after_error,5),
            "old_tail_rms":round(tail_old,7),
            "combined_post_repluck_rms":round(tail_actual,7),
            "tail_ratio":round(tail_actual/max(tail_old,1e-12),5),
            "nearly_linear_sum_before_noteoff":bool(discrepancy<.08),
            "independent_post_noteoff_tails":bool(after_error<.12)}


def inspect(root:Path)->dict:
    root=Path(root)
    identity=json.loads((root/"source_identity.json").read_text())
    result={"source":identity["publisher"],"source_commit":identity["commit"],
            "source_license":identity["license"],"reference":"real publisher PCM in miniature SFZ",
            "voice_tests":{},"release_samples":{},"pedal_noise":{}}
    for variant in ("unlimited","limited"):
        old=read_stereo(root/f"{variant}_old.wav")
        if rms(_window(old,.25,.75))<1e-5:
            raise AssertionError(f"{variant}: no audible real piano sample")
        new=read_stereo(root/f"{variant}_new_loud.wav")
        new_soft=read_stereo(root/f"{variant}_new_soft.wav")
        new_split=read_stereo(root/f"{variant}_new_split.wav")
        result["voice_tests"][variant]={
            "louder_same_channel":_voice_metrics(
                old,new,read_stereo(root/f"{variant}_both_loud.wav")),
            "softer_same_channel":_voice_metrics(
                old,new_soft,read_stereo(root/f"{variant}_both_soft.wav")),
            "louder_separate_channel":_voice_metrics(
                old,new_split,read_stereo(root/f"{variant}_both_split.wav")),
            "second_channel_audible":bool(rms(_window(new_split,.95,1.1))>1e-5),
        }
    baseline=read_stereo(root/"unlimited_note_release.wav")
    key_release=read_stereo(root/"release_note_release.wav")
    resonance=read_stereo(root/"resonance_note_release.wav")
    window=(.75,1.2)
    rel_level=rms(_window(key_release-baseline,*window))
    resonant_level=rms(_window(resonance-key_release,*window))
    # A production-safe reference: render the two physical note voices in
    # separate offline sampler processes and sum their PCM. This is a
    # feasibility reference only; it is NOT enabled in Music Studio.
    independent=read_stereo(root/"unlimited_old.wav")+read_stereo(root/"unlimited_new_loud.wav")
    combined=read_stereo(root/"unlimited_both_loud.wav")
    sf.write(root/"Q4_independent_voice_reference.wav",independent,44100,subtype="PCM_24")
    result["voice_isolation_reference"]={
        "single_process_post_noteoff_error":result["voice_tests"]["unlimited"]["louder_same_channel"]["post_short_noteoff_relative_error"],
        "independent_pcm_sum_old_tail_preserved":True,
        "purpose":"Reference waveform only. Production would require a real independent-instance SFZ voice pool."
    }
    result["release_samples"]={
        "key_release_extra_rms":round(rel_level,8),
        "string_resonance_extra_rms":round(resonant_level,8),
        "key_release_layer_detected":bool(rel_level>1e-6),
        "string_resonance_layer_detected":bool(resonant_level>1e-6),
    }
    quiet=read_stereo(root/"pedal_quiet.wav")
    pedal=read_stereo(root/"pedal_pedal.wav")
    signal=rms(_window(pedal-quiet,.45,1.75))
    result["pedal_noise"]={
        "pedal_cc64_extra_rms":round(signal,8),
        "pedal_mechanism_layer_detected":bool(signal>1e-6),
    }
    result["limitations"]=(
        "Miniature real-sample SFZ, not the full ARIA Salamander program. "
        "The same-pitch note-off interaction includes channel handling and "
        "possible SFZ self-masking, not just one opcode. The post-noteoff tail "
        "must be measured; a nearly linear pre-release sum is insufficient. "
        "No production integration or artistic preference.")
    (root/"Q4_sfizz_feasibility_report.json").write_text(json.dumps(result,indent=2))
    print(json.dumps(result,indent=2))
    return result


if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("command",choices=("prepare","inspect"))
    parser.add_argument("--out",type=Path,default=Path("q4-sfizz-probe"))
    args=parser.parse_args()
    if args.command=="prepare":
        summary=prepare(args.out)
        print("Verified",len(summary["samples"]),"pinned publisher FLACs,",
              len(summary["render_plan"]),"render fixtures")
    else:
        inspect(args.out)

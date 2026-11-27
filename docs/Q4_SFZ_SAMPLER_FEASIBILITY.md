# Q4 — Offline SFZ piano: verified recorded layers and independent voice blocker

**Scope:** a minimal real-sample technical probe of an alternate piano sampler. The shipped Music Studio piano, audio assets, and release files were not changed. This is **not** a complete Salamander Grand Piano implementation or a subjective claim of better piano sound.

## Why this test exists

The current Meta upright piano collection supplies recorded note-on velocity layers but not distinct sampled hammer/key release, pedal noises or sympathetic string resonance. The optional Q4 CC64-inspired note-off transform is already verified, but ordinary note duration extension cannot reproduce real pedal mechanism sounds.

The [Salamander Grand Piano V3](https://github.com/sfzinstruments/SalamanderGrandPiano) by Alexander Holm is a **CC BY 3.0** recorded piano with 16 note velocity layers, key-release recordings, string-resonance releases and pedal-up/down noises. Its full SFZ program includes ARIA extensions and `note_polyphony=1`. The original collection contains **641 FLAC files**, roughly **748,397,030 bytes** of sample blobs at the pinned repository revision. Those figures are from the official Git tree, not the installed Music Studio backend.

The [sfizz 1.2.3 package](https://pkgs.alpinelinux.org/package/edge/testing/x86_64/sfizz), BSD 2-Clause, includes a headless offline `sfizz_render` executable. This makes a reproducible source-rendering trial possible without another AI service or requiring input from the user.

## Reproducible experiment

[Passing clean real-source sfizz and lane-planner workflow](https://github.com/goodselldartangan-star/Music_Studio/actions/runs/45920743367) downloaded only **five authentic publisher FLACs** at exact upstream commit `3382bf9496bba2486f5ab0de55a264d1dfc38404`. Each is checked against its official Git *blob* SHA before any SFZ is rendered:

- `C4v12.flac` — sampled C4 note
- `rel60.flac` — actual key/hammer-release sample
- `harmV3C4.flac` — separately recorded C4 resonance
- `pedalD1.flac` and `pedalU1.flac` — mechanism movement recordings

An isolated Alpine Linux container installed `sfizz` v1.2.3 and rendered **19 short MIDI/SFZ cases**. The Python harness passed **10** independent tests of MIDI pedal/same-pitch scheduling, source authenticity, and old-voice preservation metrics. It did not require the full ~748 MB sample library, alter any prior Music Studio note, or redistribute the original audio samples in GitHub artifacts.

In the inspected *miniature* instrument, actual recorded layers triggered:

| Layer addition | RMS of difference versus control |
|---|---:|
| Key release sample at note-off | **0.00978723** |
| String-resonance release sample | **0.00002231** |
| Pedal-down/up mechanism via CC64 | **0.00142991** |

These are waveform differences, not direct perceived loudness or proof of faithful whole-piano pedaling. The actual full Salamander SFZ includes additional conditions, group controls and velocity regions not represented by this test.

## Critical same-pitch lifecycle finding

With the same C4 note held past a new, shorter C4 attack, the old note's later tail was reduced **even when the miniature SFZ's `note_polyphony=1` constraint was omitted**. The following measurements come from the real recorded C4 audio, not generated sine waves.

| Mode | Pre-short-note-off superposition error | Old note tail after short note-off (relative RMS) |
|---|---:|---:|
| No `note_polyphony` limit | 0.00260 (louder re-pluck) | ~0.118 |
| `note_polyphony=1`, `off_time=0.5` | 0.07527 (louder re-pluck) | ~0.118 |
| Same source but new note on a different MIDI channel | 0.00260 or 0.07527, according to preset | ~0.118 |

The problem is **not established to be caused solely by `note_polyphony` or the louder note**. The SFZ renderer's handling of a later same-pitch note-off can also release the earlier same-pitch sound. A note-on sum can look correct before that event while the tail is still lost afterward. This is exactly the failure mode the user's piano/strum overlap requirement rejects. The original Music Studio Meta piano sample renderer has independent per-voice envelopes and is unaffected.

## More precise after-note-off measurements

The later test now records the **relative waveform error after the short note has been released**. For the louder C4 re-pluck, the error was **0.97848** in the no-limit SFZ and **0.97984** with `note_polyphony=1`. The independent old-note baseline at 1.4–1.9 seconds had RMS **0.0002828**, but the combined single-synth output was only **0.0000334** (no limit) or **0.0000333** (limited). This is **not** a normal volume match or acceptable isolated old-tail preservation.

A second recorded-note channel did not resolve the issue in `sfizz_render`. The cause is broader than the `note_polyphony` setting: individual MIDI same-pitch note-off semantics and sampler voice handling must be isolated. Do not mistake the nearly linear *before*-new-note-off waveform sum for success.

## New isolated-instance scheduling contract

`studio7/sfz_voice_lanes.py::assign_sfz_voice_lanes` is a separate, **pure planner**, not a player. It assigns a different sampler instance when a previous note of the same pitch is still ringing, with a bounded release guard, while different pitches of a chord can share one instance. It refuses to steal notes when an instance limit is exceeded, and preserves all original score events. The [10-test clean Q4 job](https://github.com/goodselldartangan-star/Music_Studio/actions/runs/45920743367) passed this planner against synthetic same-note fixtures and Silver's scored piano with and without pedal timing.

As a **technical reference only**, the probe also exported a short PCM sum of independently rendered old and new piano notes. This avoids a shared same-key note-off event, demonstrating the desired signal behavior; it does **not** establish a CPU/RAM-efficient full production sampler. The GitHub artifact contains this derived comparison MP3 and the source/license manifest, but not the original publisher sample files.

## First actual independent-instance audio renderer — passed

A second, deliberately isolated module, `tools/render_sfz_lanes_q4.py`, now creates one MIDI stream per instance lane, renders each via its **own sfizz process**, and sums the resulting **stereo PCM** without stealing notes, shortening releases, or hiding clipped output through automatic normalization.

The [successful 14-test combined audio run](https://github.com/goodselldartangan-star/Music_Studio/actions/runs/45921081092) validated independent-lane MIDI creation, bounded pool capacity, full Silver score note preservation, clean stereo mixing and **actual publisher FLAC-based** note playback. It confirmed:

- **2 independent SFZ sampler instances** for the controlled C4 long note + short re-pluck
- **0.0 relative waveform error** versus the true separately rendered old+new PCM reference
- The older C4 note's post-new-note-off RMS ratio measured **1.02056**, versus **0.11793** on the original single-instance output
- All 14 unit tests passed; actual key-release, string-resonance and CC64 pedal recordings remained audible in the independent feature probe
- A separate, derived short MP3 and compact test report are saved in the CI artifacts; **original publisher source files were not republished**

The [final clean Q4 run with actual Silver sizing](https://github.com/goodselldartangan-star/Music_Studio/actions/runs/45921258338) also measured **64 piano notes** in the existing full 16-bar Silver arrangement. They require **2 separate SFZ instances** both before and after the authored pedal note-off extension, with a **0.5-second release guard**. This is a score-derived concurrency budget, **not** a measured CPU/memory requirement: a complete licensed sample library would still need loading, performance profiling, and source license/attribution verification. The same run passed all 14 tests, real release/noise audio checks, and separate-instance PCM reconstruction.

The **new method preserves this repeatable sample-level overlap case**, but it is a *standalone engineering prototype*. It has not been wired into the default Studio, and it has not yet played the complete 641-file Salamander SFZ program. Realistic pedal mechanics still require routing the CC64 noise only once rather than redundantly per instance, and benchmarking RAM/disk/CPU before attempting a full song.

## Engineering decision

**Do not switch the Music Studio production piano to sfizz/SFZ yet.** Separate sampler-instance rendering now preserves the one verified repeated C4 fixture, but it still needs the full program's 16 velocity layers, release/pedal routing, audio quality, memory budget and no-stolen-notes tests on real Silver before integration. Routing a note to another MIDI channel did **not** solve it in this isolated offline test.

The diagnostic script `tools/probe_sfz_piano_q4.py` creates a repeatable, nonproduction reference by summing two notes rendered in separate isolated sampler processes. This preserves the old note mathematically but **is not yet a practical high-polyphony sampler backend**. The production solution must be efficient, licensed and regression tested.

## Exact status

- **Verified:** offline sfizz executable, pinned publisher provenance, sampled pedal and release triggers, measured single-instance note-lifecycle blocker, independent-instance planning and an actual two-instance stereo PCM reference render (14 tests).
- **Not verified or implemented:** complete Salamander source program with all ARIA semantics, production-efficient SFZ instance pooling and mechanical-noise routing, full-song playback, realistic acoustic pedal preference, all 16 velocity layers, user listening approval.
- **Preserved:** original OGG/WAV sample backends, score, note tails, published MP3s and optional earlier Q4 note-off timing mode.

No user files are required at this stage.

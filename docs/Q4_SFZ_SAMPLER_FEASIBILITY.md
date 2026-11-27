# Q4 — Offline SFZ piano: verified recorded layers and independent voice blocker

**Scope:** a minimal real-sample technical probe of an alternate piano sampler. The shipped Music Studio piano, audio assets, and release files were not changed. This is **not** a complete Salamander Grand Piano implementation or a subjective claim of better piano sound.

## Why this test exists

The current Meta upright piano collection supplies recorded note-on velocity layers but not distinct sampled hammer/key release, pedal noises or sympathetic string resonance. The optional Q4 CC64-inspired note-off transform is already verified, but ordinary note duration extension cannot reproduce real pedal mechanism sounds.

The [Salamander Grand Piano V3](https://github.com/sfzinstruments/SalamanderGrandPiano) by Alexander Holm is a **CC BY 3.0** recorded piano with 16 note velocity layers, key-release recordings, string-resonance releases and pedal-up/down noises. Its full SFZ program includes ARIA extensions and `note_polyphony=1`. The original collection contains **641 FLAC files**, roughly **748,397,030 bytes** of sample blobs at the pinned repository revision. Those figures are from the official Git tree, not the installed Music Studio backend.

The [sfizz 1.2.3 package](https://pkgs.alpinelinux.org/package/edge/testing/x86_64/sfizz), BSD 2-Clause, includes a headless offline `sfizz_render` executable. This makes a reproducible source-rendering trial possible without another AI service or requiring input from the user.

## Reproducible experiment

[Passing clean real-source sfizz workflow](https://github.com/goodselldartangan-star/Music_Studio/actions/runs/45920391940) downloaded only **five authentic publisher FLACs** at exact upstream commit `3382bf9496bba2486f5ab0de55a264d1dfc38404`. Each is checked against its official Git *blob* SHA before any SFZ is rendered:

- `C4v12.flac` — sampled C4 note
- `rel60.flac` — actual key/hammer-release sample
- `harmV3C4.flac` — separately recorded C4 resonance
- `pedalD1.flac` and `pedalU1.flac` — mechanism movement recordings

An isolated Alpine Linux container installed `sfizz` v1.2.3 and rendered **19 short MIDI/SFZ cases**. The Python harness passed five independent tests of MIDI pedal/same-pitch scheduling, source authenticity, and old-voice preservation metrics. It did not require the full ~748 MB sample library, alter any prior Music Studio note, or redistribute the original audio samples in GitHub artifacts.

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

## Engineering decision

**Do not switch the Music Studio production piano to sfizz/SFZ yet.** The next narrowly scoped test must use independent sampler instances or truly separate voice-identity handling, verify that an old held C4 continues after the newer C4 is released, and check mechanical/release layers with the full source program before considering integration. Routing a note to another MIDI channel did **not** solve it in this isolated offline test.

The diagnostic script `tools/probe_sfz_piano_q4.py` creates a repeatable, nonproduction reference: add the two notes rendered in separate isolated audio instances. This preserves the old note mathematically but **is not yet a practical high-polyphony sampler backend**. The production solution must be efficient, licensed and regression tested.

## Exact status

- **Verified:** offline sfizz executable, publisher provenance, real sampled pedal and release trigger paths, and measured note-lifecycle blocker.
- **Not verified or implemented:** complete Salamander source program with all ARIA semantics, dedicated sampler instance pooling, full-song playback, realistic acoustic pedal preference, all 16 velocity layers, user listening approval.
- **Preserved:** original OGG/WAV sample backends, score, note tails, published MP3s and optional earlier Q4 note-off timing mode.

No user files are required at this stage.

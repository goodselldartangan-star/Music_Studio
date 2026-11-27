# Q4 — Complete licensed grand-piano source and 16-bar Silver test

**Status: full-bank experimental engineering gate passed, November 26, 2026.** [Successful clean 20-test GitHub run](https://github.com/goodselldartangan-star/Music_Studio/actions/runs/45923699850).

**Production status:** NOT enabled by default or integrated into the original Music Studio piano backend. The independent recorded-piano renderer is a tested, reproducible offline experiment, not yet a listener-approved replacement.

## What was verified

- The actual [Salamander Grand Piano V3](https://github.com/sfzinstruments/SalamanderGrandPiano) files at **commit `3382bf9496bba2486f5ab0de55a264d1dfc38404`** were downloaded from the public official repository, and every original **641 FLAC** was checked against its pinned Git blob SHA and size. Together the original compressed recordings occupy **748,397,030 bytes** (~714 MiB).
- Sample groups: **480 note-on recordings** (30 sampled pitch zones × 16 velocity layers), **88 chromatic key/hammer releases**, **69 separately sampled resonances**, and **4 pedal-up/down mechanical recordings**. The main SFZ additionally includes `Data/tune_nat.txt` and `Data/tune_ret.txt`; missing either caused parser errors in an earlier test and is now guarded.
- All releases mapped to their real MIDI pitches: source `rel40.flac` is assigned MIDI key **60**; `rel60.flac` corresponds to **MIDI 80**, not C4. Unlike the earlier miniature sample trigger, the full original SFZ uses the correct mapping.
- The original 16-bar **Silver Rain** score was rendered with **64 unchanged piano note events** through two independent `sfizz_render` 1.2.3 processes and **one** separately rendered physical pedal mechanism instance (16 CC64 down/up edges).
- The voice-only SFZ is an **uncommitted, transient derivation** of the original program with the mechanical `Data/pedal.txt` include excluded, preserving the full note-on, key-release, resonance, velocity and tuning definitions. Original bank files, Music Studio defaults and released MP3s remain unmodified.
- The controller events are scheduled at the original score's **102 BPM**, but written into `sfizz_render`'s fixed-120-BPM MIDI timeline using real seconds. Earlier tests found and fixed a tempo-scaling bug that truncated the pedal-only recording.
- A 40.647-second stereo piano+one-pedal render was non-silent and finite. Its **unscaled sample peak was 0.077332**, so no preview gain reduction was required, and its 12-second MP3 excerpt decoded successfully.

## Actual source-sample audio and resource data

| Component | PCM RMS | Render time | Peak process RSS |
|---|---:|---:|---:|
| Original grand piano, instance 0 | 0.00699842 | **1.07 s** | **162,428 KiB** |
| Original grand piano, instance 1 | 0.00412740 | **0.72 s** | **125,808 KiB** |
| Shared recorded pedal mechanism | 0.00021327 | **0.22 s** | **17,968 KiB** |

Each of these was rendered **sequentially**, not simultaneously. RSS cannot be summed to claim actual concurrent process memory consumption, and performance depends on CI hardware, sample cache and playback configuration. The recorded stereo-side RMS in the combined PCM was **0.00551524**, so stereo content survived.

The derived preview includes a 12-second encoded excerpt in the GitHub Actions artifact. The artifact contains source manifests, technical reports and derived audio—not the original publisher FLAC files.

## Important defects fixed during this gate

1. **Source closure:** the official `Data/notes.txt` includes `Data/region.txt`, which holds the 30 pitch-region declarations. The audit now resolves both layers, all 16 velocity definitions, natural/retuned tuning maps and all 88 MIDI release-sample placements.
2. **Moving between host and container:** absolute symlinks to samples failed inside the isolated Alpine container. A disposable derived-SFZ workspace now uses portable relative symlinks.
3. **Pedal mechanism double-trigger:** CC22=0 alone did not reliably mute physical pedal regions in sfizz. The original program's mechanical-pedal include is instead excluded from note instances, and a separate shared SFZ fires those sounds once per CC64 movement.
4. **Wrong pedal clock:** the Silver score is 102 BPM, not the MIDI file's fixed 120 BPM. The experiment now converts musical beats to absolute seconds before encoding controller event timestamps.

## Boundaries and next steps

This validates a complete publisher sample bank with no missing-source parser errors in the final clean run, real note/release/resonance and pedal sound paths, independent same-pitch voice handling via separate processes, a 2-instance budget for Silver, and measured audio/RAM/CPU evidence. It does **not** mean all of the original SFZ's ARIA-specific controls have been perceptually verified, that the grand piano is a better fit for the pop arrangement, or that pedal realism is identical to a physical instrument. A successful load can ignore noncritical opcodes silently.

The next focused stage is a **proper level-matched instrument-in-context A/B** of the recorded Meta upright piano and the recorded Salamander grand piano in the same unchanged Silver score, with no doubled pedal sounds, clipping, or note interruptions. An optional integration adapter should stay isolated from scores, effect DSP and existing sample selection. Any recorded-source distribution must carry **CC BY 3.0 attribution to Alexander Holm**, along with relevant SFZ-map credit to kinwie and retuning credit to Markus Fiedler.

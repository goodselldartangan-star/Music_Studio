# Music Studio — prioritized improvement backlog

**Operating rule:** Work on exactly **one major audio subsystem at a time**. Preserve v7 and earlier releases, make a matched baseline versus candidate comparison, run automated tests and inspect stems, then integrate only when the stated gate passes. GPT is the only AI; offline sample libraries and ordinary DSP are allowed. Do not claim that test metrics prove something sounds good.

**Listening policy:** Default to autonomous testing. Ask for listener feedback only when two or more technically valid choices differ in musical *feel*, timbre, groove or taste and those differences cannot be resolved by objective checks. When asking, provide a short level-matched A/B with one change, what to listen for, and no unrelated choices. Never require input to run automated tests.

**Current focus: P1.** P0 is completed with local and GitHub CI evidence. Only P1 may be actively changed now. Tasks can be reordered if evidence justifies it; record the reason.

| Order | Major subsystem | Status | Work to do | Completion gate (automatic unless marked *) |
|---|---|---|---|---|
| **P0** | **Note lifecycle / articulation** | **DONE — 29 local tests + GitHub CI succeeded** | Confirm overlapping same-pitch notes, soundfont voice allocation, recorded-sample tails, intentional rests and releases; run real instrument fixtures | 25 v7/v8 tests pass; clean GitHub job succeeds; no stolen-note or stuck-note regression; compare fixed-phrase waveforms and note boundaries. *Ask listener only if natural decay vs muddy overlap remains ambiguous.* |
| **P1** | **Recorded-instrument playback** | **ACTIVE — sample mapping audit** | Audit SF2/SFZ mappings, pitch transposition limits, velocity layers, sample attack and natural tails, timbre/round robin; remove any fake-sounding presets only after replacement passes | Correct instrument range and sample provenance; repeatable note tests at soft/mid/hard velocities; no unlicensed assets; recorded and fallback backend remain interchangeable. *Timbre preference may need listening.* |
| P2 | Instrument playing technique | QUEUED | Per-part guitar strum order and duration, bass note placement and slides, piano pedaling/voicings, ghost notes, dynamic accents | Instrument-specific MIDI patterns in playable ranges; realistic attack scheduling; no accidental all-notes-on-one-beat; deterministic score fixtures. |
| P3 | Rhythm-section connection | QUEUED | Align kick/bass intent and drum pocket; validate hats, snares, fills, round-robin and groove; avoid over-quantization | Drum/bass stem onset and timing tests; no unplanned kick/bass collisions; stable intentional swing; bounded velocity and timing changes. *Groove feel may need listening.* |
| P4 | Harmony and register coordination | QUEUED | Chord spelling, inversions, voice leading, bass/register separation, suspensions and intentionally resolved dissonances | Theory audit and overlapping-note checks catch errors; cadence notes and bass roots verified; preserve intentional tensions rather than banning every dissonance. |
| P5 | Memorable lead phrasing | QUEUED | Write hooks with longer held notes, breath spaces, motivic responses, contour variation; reduce busy accompaniments | Melodic phrase and rest coverage; recurrence with meaningful variation; repeated-hook identity; no unsupported claims about catchiness. *Only listener can validate emotional appeal.* |
| P6 | Effects and sonic depth | QUEUED | Deliberate shared room, predelay, stereo delay, modulation, distortion and automation; evaluate per-instrument wet/dry | Stereo/mono, decay, unwanted resonance, clipping and phase tests; bypass comparison has one processing change; don't mask lead transients. *Spatial preference may need listening.* |
| P7 | Mix balance / masking | QUEUED | Per-stem gain staging, frequency overlap, transient separation, kick/bass hierarchy, translation to mono and headphones | Peak/true peak/LUFS/dynamic range/phase/stem tests; consistent matched-loudness comparisons. *Final balance taste may need listening.* |
| P8 | Section arrangement / transitions | QUEUED | Contrasting verses/choruses, rests and fills, dynamics, return of signature motif; no rigid four-bar repeat template | Section metrics, structural audit, variation across repeats, clean transition tails and fade; end-to-end score reproducibility. |
| P9 | Production acceptance and maintainability | QUEUED | Consolidate integration tests, enable CI gates, remove unused duplicate workflow triggers only with proof, keep docs GPT-readable | Tests run on clean environment, documented asset licenses, reproducible previews/masters; modules remain isolated; no regression across old releases. |

## Repeatable task protocol

1. **Inspect:** identify exact code path, audible symptom and a small reproducible score/fixture.
2. **Baseline:** render raw isolated stems and a no-change comparison before modifying the subsystem.
3. **Change one owner:** e.g. P0 edits `studio7/articulation.py` and its focused tests, not score, instruments and mastering at once.
4. **Test:** unit/contract tests -> synthetic fixtures -> recorded samples -> short preview -> MP3 decode/QA -> clean GitHub runner.
5. **Compare:** preserve gain-matched baseline and candidate; inspect onsets, releases, peak, RMS, phase and notes. Auto-accept only objective fixes; otherwise mark *needs listening* and ask one focused question.
6. **Record:** update this file with evidence, commit, close current task, start the next. Never silently publish a song as "good" solely because tests passed.

## P0 evidence available now

- v8 source: `studio7/articulation.py`, `tests/test_articulation.py`, `docs/note-lifecycles-v8.md`.
- Local verification on **2026-11-11**: `python -m unittest tests.test_studio7 tests.test_articulation -v` → **29 tests passed**, including four new polyphony and channel-reuse regressions.
- Earlier GitHub run 43096670027 remained queued, but the new [successful focused workflow 43102402291](https://github.com/goodselldartangan-star/Music_Studio/actions/runs/43102402291) and [successful broad QA 43102402221](https://github.com/goodselldartangan-star/Music_Studio/actions/runs/43102402221) both passed on commit 413e70b. See [P0 results](P0_NOTE_LIFECYCLE_RESULTS.md).
- The old sampler lacked instrument-appropriate release and FluidSynth could interrupt repeated same-pitch notes sharing a channel; v8 addresses both. No further user audition is needed just to confirm these code-level fixes.

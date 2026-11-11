# P2 — Natural playing technique: engineering stage complete

**Date:** 2026-11-11. **Scope:** guitar stroke order, bass emphasis and controlled releases, piano touch and rolled chord timing. Original v7 scores, real sample libraries, backing drums, harmony, mixing and effects were preserved. The three score transforms are opt-in; earlier renders and releases remain unchanged.

## What changed

| Module | Independent adjustment | What it deliberately does not do |
|---|---|---|
| `studio7/playing.py` | Slightly retime pre-existing down/up guitar strums, with bounded accents | No altered pitches, note durations, chords, solo lines, drums or mix |
| `studio7/bass_performance.py` | Phrase-position velocity and small length refinements while preserving pre-existing overlap and rests | Never shifts bass onsets or pitches; no synthetic slide or new rhythm hits |
| `studio7/piano_performance.py` | Phrase/voice-dependent touch and 10–12 ms spacing of *already staggered* chords | No harmonic changes, note truncation, new notes or false sustain-pedal modeling |
| `studio7/render.py` / `demo_v7.py` | Optional `--guitar-performance --bass-performance --piano-performance`; file suffixes prevent overwriting old masters | Default render and sample banks unchanged |

## Tests performed

1. [Guitar isolated clean-runner verification](https://github.com/goodselldartangan-star/Music_Studio/actions/runs/43110129074): **34 tests** passed. Harbor: 32 strum groups, 128 notes changed, maximum onset shift 19.667 ms; score and note lengths preserved.
2. [Bass isolated clean-runner verification](https://github.com/goodselldartangan-star/Music_Studio/actions/runs/43116698788): **39 tests** passed, a matched bass A/B MP3, and a full After arrangement. 60 bass notes adjusted, maximum duration change 0.0314 beat; no onset/pitch change and existing overlaps remain.
3. [Piano + combined clean-runner verification](https://github.com/goodselldartangan-star/Music_Studio/actions/runs/43117496622): **46 tests** passed, matched piano A/B MP3, full Silver arrangement, and all three modules together. 32 rolled piano chord groups and 60 piano notes adjusted, maximum onset shift 14.118 ms. Explicit block chords and original pitch/duration intact. Transform order independence is tested.
4. [Actual recorded-instrument CI](https://github.com/goodselldartangan-star/Music_Studio/actions/runs/43117771303): downloaded original licensed guitar/piano/bass/drum libraries, passed the existing sample coverage checks, rendered the original three v7 examples unchanged, then rendered **Harbor** and **Silver** with *all three* P2 transforms enabled; both are labeled `recorded instruments` and passed MP3 QA.

Regression tests also ensure a chord can play at once, and a short same-pitch pluck can enter while the earlier note sustains without forcing it to stop.

## What is still NOT claimed

The quality gates verify finite audio, boundaries, decode, real sample usage, note correctness, and isolated code changes. They **do not prove** the guitar, bass or piano sound convincingly human, or that one rendering is more enjoyable than another.

**True piano sustain pedal** was intentionally deferred. Real pedal resonance, sympathetic vibration and damper response require instrument/library support; extending all MIDI note lengths is not equivalent. The current CC0 piano is rendered as independent samples with note-off envelopes. Investigate the asset backend and actual pedal-related samples before adding CC64 or simulated pedal tone.

Useful reading:
- [MusicRadar: piano performance dynamics, timing and MIDI sustain](https://www.musicradar.com/tuition/tech/how-to-make-a-programmed-piano-part-sound-more-realistic-632299)
- [Waves: programmed bass note articulation and legato](https://www.waves.com/how-to-make-programmed-bass-tracks-realistic)

## Decision

P2 **engineering gate passed**. Maintain these modules as optional until later musical-arrangement or user preference reviews. Proceed to **P3 Rhythm-section connection**, starting with *measurement* of kick/bass onset relationships and groove patterns before editing them. Do not request another listening demo solely for these technical checks.

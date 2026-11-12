# Music Studio — prioritized improvement backlog

**Operating rule:** Work on exactly **one major audio subsystem at a time**. Preserve v7 and earlier releases, make a matched baseline versus candidate comparison, run automated tests and inspect stems, then integrate only when the stated gate passes. GPT is the only AI; offline sample libraries and ordinary DSP are allowed. Do not claim that test metrics prove something sounds good.

**Listening policy:** Default to autonomous testing. Ask for listener feedback only when two or more technically valid choices differ in musical *feel*, timbre, groove or taste and those differences cannot be resolved by objective checks. When asking, provide a short level-matched A/B with one change, what to listen for, and no unrelated choices. Never require input to run automated tests.

**Checklist status: P0–P9 scoped engineering gates completed.** All technical acceptance checks passed. **Musical taste, full professional production quality, and optional setting preferences remain unvalidated**; future work should use one short, level-matched preference comparison only when justified, not a new long demo by default.

| Order | Major subsystem | Status | Work to do | Completion gate (automatic unless marked *) |
|---|---|---|---|---|
| **P0** | **Note lifecycle / articulation** | **DONE — 29 local tests + GitHub CI succeeded** | Confirm overlapping same-pitch notes, soundfont voice allocation, recorded-sample tails, intentional rests and releases; run real instrument fixtures | 25 v7/v8 tests pass; clean GitHub job succeeds; no stolen-note or stuck-note regression; compare fixed-phrase waveforms and note boundaries. *Ask listener only if natural decay vs muddy overlap remains ambiguous.* |
| **P1** | **Recorded-instrument playback** | **DONE — real-asset pitch/layer QA and GitHub CI passed** | Audit SF2/SFZ mappings, pitch transposition limits, velocity layers, sample attack and natural tails, timbre/round robin; remove any fake-sounding presets only after replacement passes | Correct instrument range and sample provenance; repeatable note tests at soft/mid/hard velocities; no unlicensed assets; recorded and fallback backend remain interchangeable. *Timbre preference may need listening.* |
| **P2** | **Instrument playing technique** | **DONE — guitar/bass/piano tested on GM and real samples** | Per-part guitar strum order and duration, bass note placement and slides, piano pedaling/voicings, ghost notes, dynamic accents | Instrument-specific MIDI patterns in playable ranges; realistic attack scheduling; no accidental all-notes-on-one-beat; deterministic score fixtures. |
| **P3** | **Rhythm-section connection** | **DONE — pocket & drum dynamics independently tested; real-sample QA passed** | Align kick/bass intent and drum pocket; validate hats, snares, fills, round-robin and groove; avoid over-quantization | Drum/bass stem onset and timing tests; no unplanned kick/bass collisions; stable intentional swing; bounded velocity and timing changes. *Groove feel may need listening.* |
| **P4** | **Harmony and register coordination** | **DONE — chord review and optional piano revoicing passed real audio QA** | Chord spelling, inversions, voice leading, bass/register separation, suspensions and intentionally resolved dissonances | Theory audit and overlapping-note checks catch errors; cadence notes and bass roots verified; preserve intentional tensions rather than banning every dissonance. |
| **P5** | **Memorable lead phrasing** | **DONE — motif structure and optional chord-tone cadence verified; artistic preference untested** | Write hooks with longer held notes, breath spaces, motivic responses, contour variation; reduce busy accompaniments | Melodic phrase and rest coverage; recurrence with meaningful variation; repeated-hook identity; no unsupported claims about catchiness. *Only listener can validate emotional appeal.* |
| **P6** | **Effects and sonic depth** | **DONE — room predelay/bypass, stereo and recorded-asset QA passed** | Deliberate shared room, predelay, stereo delay, modulation, distortion and automation; evaluate per-instrument wet/dry | Stereo/mono, decay, unwanted resonance, clipping and phase tests; bypass comparison has one processing change; don't mask lead transients. *Spatial preference may need listening.* |
| **P7** | **Mix balance / masking** | **DONE — stereo side, true-peak and stem spectrum QA passed real samples** | Per-stem gain staging, frequency overlap, transient separation, kick/bass hierarchy, translation to mono and headphones | Peak/true peak/LUFS/dynamic range/phase/stem tests; consistent matched-loudness comparisons. *Final balance taste may need listening.* |
| **P8** | **Section arrangement / transitions** | **DONE — controlled backing break and recorded-sample QA passed** | Contrasting verses/choruses, rests and fills, dynamics, return of signature motif; no rigid four-bar repeat template | Section metrics, structural audit, variation across repeats, clean transition tails and fade; end-to-end score reproducibility. |
| **P9** | **Production acceptance and maintainability** | **DONE — 189-test clean runner, real samples and no-clobber release safety** | Consolidate integration tests, enable CI gates, remove unused duplicate workflow triggers only with proof, keep docs GPT-readable | Tests run on clean environment, documented asset licenses, reproducible previews/masters; modules remain isolated; no regression across old releases. |

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

## P1 acceptance evidence (2026-11-11)

- [P1 recorded-sample report](P1_RECORDED_SAMPLE_RESULTS.md): **1,075** recordings, **220/220 exact pitch** sample-backed notes, and three distinct velocity selections for steel guitar, piano and nylon guitar.
- 32 local tests and [successful P1 focused GitHub QA](https://github.com/goodselldartangan-star/Music_Studio/actions/runs/43103480466).
- [Successful full recorded-instrument GitHub run](https://github.com/goodselldartangan-star/Music_Studio/actions/runs/43105376460) downloaded licensed sample archives, audited and rendered all demos; no subjective quality claim.
- Next P2 owns **how** instruments are performed (strum attacks, expressive dynamics, piano pedaling, bass articulation), not their sample-selection backend. No user listening needed until a taste judgment remains.

## Simultaneous notes / retriggers — verified capability (2026-11-11)

User asked whether the same instrument can play a chord and re-pluck a pitch while the older voice rings. **Yes:** distinct chord pitches share an instrument/channel, and overlapping same-pitch retriggers are mapped to separate MIDI channels by `studio7/articulation.py`. Recorded sample notes are independently summed in `studio7/render.py`; neither an old sample's duration nor a new attack must cancel the other. P0 already solved this, so **do not create a duplicate priority**. Two regressions in `tests/test_articulation.py` now explicitly protect a three-note chord plus same-pitch retrigger, and a long sample tail plus shorter pluck.

**P2 guitar substage:** `studio7/playing.py` is an optional, deterministic score-to-score transformation that adjusts only already-staggered guitar strums. It preserves pitches, durations, note counts, explicit block chords, instrument types and all non-guitar parts. CLI flag: `demo_v7.py --guitar-performance`. Existing demos still render with the old settings unless the flag is passed. Local: 34 focused tests passed and full 38.58s harbor preview passed technical MP3 QA. P2 remains active for bass/piano expression and recorded-instrument acceptance.

## P2 playing technique acceptance evidence (2026-11-11)

- [Full P2 report](P2_PLAYING_TECHNIQUE_RESULTS.md): independent guitar strokes, bass emphasis and controlled note lengths, and piano chord touch.
- 34 guitar tests / 39 bass tests / **46 piano + combined tests** passed on [focused clean runners](https://github.com/goodselldartangan-star/Music_Studio/actions/runs/43117496622).
- [Real recorded-instrument CI](https://github.com/goodselldartangan-star/Music_Studio/actions/runs/43117771303) tested original demos and both Harbor and Silver with all three P2 modules enabled. Both MP3 quality checks passed.
- The original scores/patches/effects are unchanged unless flags opt in. A true physical piano sustain pedal is **not simulated**; it needs instrument support and remains a later research item.
- **Next P3:** analyze kick/bass attacks, hat/snare groove and intentional timing, without conflating it with instrument performance techniques.

## P3 initial timing audit (2026-11-11)

- [P3 baseline and optional bass/kick pocket report](P3_RHYTHM_BASELINE.md). Median downbeat bass lag behind kick: Harbor 61.11ms, After 63.93ms, Silver 94.12ms; these are *not* universal errors.
- [Score-only baseline CI](https://github.com/goodselldartangan-star/Music_Studio/actions/runs/43118680421) and [optional timing experiment CI](https://github.com/goodselldartangan-star/Music_Studio/actions/runs/43119195729) passed 36 focused tests, matched kick/bass A/B and integrated MP3 decode.
- [Full real sampled-instrument CI](https://github.com/goodselldartangan-star/Music_Studio/actions/runs/43119410960) confirmed optional After P3 render along with all previous instrument checks.
- **After** opt-in downbeat bass anchors change median lag from 63.93ms to 17.02ms. Snare, hats and offbeat bass pickups are unchanged; the new pocket remains an **opt-in hypothesis**, not a declared superior groove. **P3 stays active** for drum/bass dynamics and groove interactions.

## P3 completion (2026-11-11)

- [P3 engineering completion report](P3_RHYTHM_RESULTS.md) — optional kick/bass anchor timing and deterministic drum dynamics; no pattern changes or new hits.
- [P3 drum-dynamics workflow](https://github.com/goodselldartangan-star/Music_Studio/actions/runs/43123081945) passed 13 focused tests and full MP3.
- [Real recorded-instrument acceptance](https://github.com/goodselldartangan-star/Music_Studio/actions/runs/43123279343) passed with both P3 options enabled. Subjective groove preference remains unknown; defaults unchanged.
- **Next:** P4 instrument register and harmony coordination. Maintain an explicit distinction between intentional doubling and accidental pitch clashes.

## P4 completed (2026-11-11)

- [P4 register/harmony acceptance report](P4_REGISTER_RESULTS.md): correct chord spellings/roots; Silver showed 24 overlapping piano/lead unisons. Optional whole-chord octave revoicing changed 30 piano notes, removing all 24 counted overlaps without changing pitches modulo 12, melody, event times, dynamics or drums.
- [33-test P4 CI](https://github.com/goodselldartangan-star/Music_Studio/actions/runs/43124657339) and [full recorded-instrument CI](https://github.com/goodselldartangan-star/Music_Studio/actions/runs/43124861612) passed.
- Revoicing remains optional because intentional unison doubling may be musically desirable. Next P5: motif contrast, rest space and final-phrase cadences.

## P5 engineering acceptance (2026-11-11)

- [P5 report](P5_PHRASE_RESULTS.md): tests of note/rest/hold structure and a one-note optional closing cadence aligned with each final chord; earlier melody remains unmodified.
- [31-test P5 clean runner](https://github.com/goodselldartangan-star/Music_Studio/actions/runs/43149596445) and [real recorded-instrument run](https://github.com/goodselldartangan-star/Music_Studio/actions/runs/43149618708) **both passed**.
- The ending choice and melody memorability are subjective, therefore default versions remain unchanged. P6 will improve technical spatial/effect behavior without adding arbitrary processing or changing scores.

## P6 engineering completion (2026-11-11)

- [P6 spatial DSP report](P6_EFFECTS_RESULTS.md): optional wet-only room pre-delay, validation of IR duration, dry bypass, tempo delay and stereo behavior.
- [P6 focused CI](https://github.com/goodselldartangan-star/Music_Studio/actions/runs/43150536348) passed 25 tests, matched piano room A/B and integrated MP3 QA.
- [Full licensed recorded-instrument CI](https://github.com/goodselldartangan-star/Music_Studio/actions/runs/43150661031) succeeded with the optional Harbor room pre-delay; default audio unchanged.
- **Next P7:** measure low-end side energy and true-peak / channel translation explicitly. Do not use a one-number proxy for musical mixing decisions.

## P7 technical acceptance (2026-11-11)

- [P7 mix-translation report](P7_MIX_TRANSLATION_RESULTS.md) contains the measured low-side and true-peak data, plus per-stem spectral roles; no claim of preferred EQ.
- [33-test expanded mix CI](https://github.com/goodselldartangan-star/Music_Studio/actions/runs/43151836846) and [full real-sample CI](https://github.com/goodselldartangan-star/Music_Studio/actions/runs/43151867062) passed.
- Optional zero-phase low-side filter reduced measured side power by ~6.65 dB in the controlled fixture while leaving the center waveform untouched. Earlier masters remain the default. **Next P8:** evaluate section progression and intentional transitions, no new song yet.

## P8 engineering acceptance (2026-11-11)

- [P8 section transition report](P8_ARRANGEMENT_RESULTS.md): optional brief backing gap at beats ~47.5 to 48, with all foreground melodies/notes and sustaining tails preserved.
- [P8 26-test clean runner](https://github.com/goodselldartangan-star/Music_Studio/actions/runs/43152580420) verified zero audio difference before the intended break and full optional MP3 export.
- [P8 recorded-instrument acceptance](https://github.com/goodselldartangan-star/Music_Studio/actions/runs/43152723681) passed all previous publisher-sample checks plus the optional After transition.
- The quiet break is not made default; whether it helps the musical build remains a listening question. **Next P9:** protect previous GitHub release assets and consolidate acceptance evidence.

## P9 engineering completion and next gate (2026-11-11)

- [P9 final technical acceptance report](P9_PRODUCTION_ACCEPTANCE.md) and [dedicated 4-test release safety workflow](https://github.com/goodselldartangan-star/Music_Studio/actions/runs/43153356836) passed.
- [Full clean recorded-instrument workflow](https://github.com/goodselldartangan-star/Music_Studio/actions/runs/43153298828) passed **189 unit tests** and all demo MP3 integrity checks; existing release recordings and verification asset were **explicitly preserved** in its logs (no overwritten assets).
- Completed P0–P9 means the *engineering tasks and their testable contracts* are done, **not** that instrumentation, groove, melody, mix or emotional impact sound professionally convincing. Piano pedal resonance and subjective decisions remain intentionally deferred.
- All P2–P8 treatments remain optional and default original scores/FX/published demos preserved. Next phase: only consider a **single isolated, short A/B for a specific musical preference** when automated checks cannot decide. Do not use aggregate quality metrics as a surrogate for listening.

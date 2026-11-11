# P0 — Note lifecycle and voice allocation: completed (2026-11-11)

**Scope:** note on/off, overlapping same-pitch voices, sample release envelopes. No changes to score, instrumental timbres, harmony, effects or mix.

## Problem and root cause

- FluidSynth note-on for an already sounding **same pitch on the same channel** releases the prior voice. MIDI note-off is addressed by channel and pitch; it cannot name an individual overlapping voice. See [FluidSynth MIDI API](https://www.fluidsynth.org/api/group__midi__messages.html).
- V8 protected against same-pitch overlap by reserving one whole MIDI channel for every sounding **note**, including unrelated pitches. With only 15 melodic channels, an ordinary 16-note chord falsely failed as "too many simultaneous notes".
- Some old direct sample notes had extremely short release tapers (~30–40 ms); V8 already introduced per-instrument envelope profiles, covered by regression tests. SFZ's [envelope guidance](https://sfzformat.com/tutorials/envelope_generators/) supports preserving natural sampled attacks and choosing an explicit release.

## Focused change

- `studio7/articulation.py::assign_voice_channels`: track the next safe time **per pitch, per MIDI channel**. Distinct pitches can share channel 0; repeated same pitches are sent to channels 1, 2, ... until their note-off plus release guard expires. Reuse channels deterministically after release.
- Fail explicitly only when more than 15 simultaneous **same-pitch** notes require isolated channels; validate pitch, velocity and event boundaries.
- `tests/test_articulation.py`: four new regression tests verify a 40-note distinct-pitch chord, five-note chord retriggers, guard/reuse ordering, and actual SoundFont playback of a 20-note piano chord. Existing stuck/cut note tests retained; capacity test correctly checks 16 simultaneous **same-pitch** notes.

## Verified results

- Local: `python -m unittest tests.test_studio7 tests.test_articulation -v` → **29/29 passed** (25 original + 4 new).
- Local: `python demo_v7.py --gm /usr/share/sounds/sf2/TimGM6mb.sf2 --style harbor --out <dir>` and `studio7.qa.inspect()` → 38.58s MP3, RMS -21.85 dBFS, peak -1.53 dBFS, channel balance 0.26dB, stereo correlation 0.959, all QA passed.
- Channel allocation in current 16-bar scores: all guitar/electric voices use 1 channel; bass typically 1–2, piano 1–2, including polyphonic chords. Same-pitch retriggers remain separated.
- **Clean GitHub runner:** [focused articulation workflow success](https://github.com/goodselldartangan-star/Music_Studio/actions/runs/43102402291) at commit `413e70b4bd02cdd86d1bec07e5418f45eafafa18`. Steps include 29 unit tests, before/after render and QA, and artifact retention.
- [Broader score-to-audio QA success](https://github.com/goodselldartangan-star/Music_Studio/actions/runs/43102402221) at the same commit.

**Limitations:** The clean-runner demonstration uses a GM SoundFont, not the external recorded asset library; it verifies voice management, not realistic sampled-instrument tone. More sophisticated same-pitch polyphony or pedal behavior remains a distinct future feature if required. No subjective listening preference is claimed.

**Decision:** P0 engineering acceptance gate met. Advance **one** subsystem to P1 (recorded-instrument playback). Keep v7/v8 demos and source for regression comparisons.

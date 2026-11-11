# Music Studio — note transitions (single-subsystem upgrade)

## Why this upgrade exists

A listener reported notes seeming to end when the next note arrived. We found two credible mechanical causes in the v7 engine:

1. FluidSynth's `fluid_synth_noteon` automatically releases an earlier same-key note on the *same channel*. When two MIDI notes of the same pitch overlap and note-on/off events share a channel, later note-offs can interfere with the new attack. Documentation: https://www.fluidsynth.org/api/group__midi__messages.html
2. Recorded Meta sample playback used forced exponential gain after note-off with decay time `release * .24` (nylon; 0.14s * .24 = **0.034 s**) and `release * .22` (steel/piano). This can sound gated. Proper sample instruments define their own release behavior. Sources: https://sfzformat.com/opcodes/ampeg_release/ and https://sfzlab.github.io/sfz-website/documentation/tutorials/legato/

This is a **code-level** diagnosis, not proof that every clipped-sounding note in v7 had that cause.

## What changed (and what did not)

- `studio7/articulation.py` is the sole owner of musical note-lifecycle policies. It adds per-instrument attack and release timings, optional connected-phrase overlap, separate MIDI channels for notes whose tails overlap, and a smooth raised-cosine release for sample playback. Explicit rests longer than a small connection window are preserved.
- `studio7/render.py` now calls that independent voice renderer for melodic SoundFonts; drum hi-hat choke groups retain their original behavior. Meta sampled guitar/piano uses the new release adapter while leaving `studio3/sample_bank.py` unchanged for older versions.
- `studio7/samples.py` uses the same envelope for optional nylon guitar. No score format, chord, drum style, effects bus or mastering behavior was rewritten.
- The note planner refuses more concurrent voices than the available MIDI channels instead of silently stealing notes. This is a deliberate bounded fallback; future instruments with huge polyphony may need a separate strategy.

## How to compare

```bash
python -m unittest tests.test_studio7 tests.test_articulation -v
python compare_note_endings.py
```

Each MP3 under `articulation_previews/` contains the exact same source phrase rendered **old first**, 0.8-second silence, **revised second**. Original GM test SoundFont is used for controlled, portable comparison (on Ubuntu `timgm6mb-soundfont`). These are *articulation demos*, not claims that this GM bank is realistic enough for a finished song.

- `01_repeated_guitar_before_after.mp3`: repeated pitches that previously competed on one channel; should ring through retriggers without the older note-off killing the newer attack.
- `02_piano_releases_before_after.mp3`: original abrupt `.17 * .22` exponential release vs `.48` second shaped decay. Should have lingering but controlled piano note-offs.
- `03_melody_connections_before_after.mp3`: near-adjacent legato lead notes vs unmodified note-offs; intentional larger rests remain.

All samples are original MIDI phrases. No other generative AI, external credentials or copyrighted song samples.

## Objective acceptance checks

- 18 original v7 unit tests + 7 additional articulation unit tests.
- Integrated v7 `harbor` GM render also passed its full MP3 decode and channel/peak QA tests (38.58s).
- Three 256kbps MP3 A/B pairs passed FFmpeg decode. They differ numerically as expected; that **does not establish listener preference**.
- No accidental note-on relocation; sample attack is preserved with only millisecond-scale smoothing. Existing intentional drum choke behavior retained.

## Deferred changes — NOT part of this stage

Instrument/sample quality, chord voicing, acoustic room modeling, songwriting complexity, vocal expression, MIDI score changes and EQ remain open. Do **not** update these simultaneously while judging note endings. The next priority should be picked after listening feedback.

# P6 — Effects depth / spatial DSP: scoped technical verification

**2026-11-11**. This document records the **mechanical** effects behavior, not whether a listener prefers a more distant or wider sound.

## What was changed

- `studio7/effects.py::room_send` now rejects invalid room duration (previously could index beyond the impulse buffer), out-of-range wet mix and nonfinite input, with clear errors.
- Added an optional **0–160 ms wet-only pre-delay**. Its default is **0 ms**; previously released mixes keep the same impulse timing, parameters and output contract. The dry instrument notes are never delayed.
- `studio7/render.py` and `demo_v7.py --room-predelay-ms 32` expose it as an optional control. File suffix `-p6-room32ms` prevents overwriting earlier masters; metadata records the choice.
- No new musical notes, sample bank, score timing, chord, instrument, or EQ settings were changed.

## Tests and limits

- [Focused P6 GitHub Actions succeeded](https://github.com/goodselldartangan-star/Music_Studio/actions/runs/43150536348): **25 tests**, including 7 new spatial assertions and existing v7 contract tests; matched-dry-piano A/B, decoder checks, and full Harbor GM MP3 QA.
- A test impulse verifies that changing only the pre-delay shifts the **wet** reflections and retains the original dry onset. The two deterministic stereo room impulse responses are independent.
- A half-beat tempo delay was tested at 120 vs 240 BPM, and wet=0 produced exact silence in the wet-only room send. Full mix default (0 ms) is preserved.
- Isolated comparison: before/after RMS was level-matched (both approximately -46.11 dBFS); waveform difference RMS was 0.0006707. This establishes a change, not a musical preference.
- Full Harbor GM optional render passed QA at approximately -21.85 dBFS RMS.
- The existing `mono_below` crossover reduces low-frequency side energy but is not a brickwall cancellation filter. An earlier P6 test incorrectly required >50% output-RMS suppression; the corrected test reflects the existing filter. **Precise bass mono and phase translation remain a P7 mix task**, rather than silently changing the crossover during P6.

## Recorded instruments

[Recorded-instrument GitHub run 43150661031](https://github.com/goodselldartangan-star/Music_Studio/actions/runs/43150661031) was started after the corrected spatial tests; its real-library Harbor P6 export is **pending verification**, not a passed gate until the workflow completes successfully.

## Acceptance caveat

Automated tests cannot decide the ideal ambience or how wide/distant an instrument *should* feel. The new effect remains optional until a listening-based preference is relevant. Do not call more reverb intrinsically better.

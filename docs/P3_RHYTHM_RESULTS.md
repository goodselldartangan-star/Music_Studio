# P3 — Rhythm-section engineering: completed 2026-11-11

**Decision:** P3 engineering gate passed. Acoustic *groove preference* remains unverified and the new transforms remain optional; do not make them default on the strength of unit tests.

## Baseline and controlled changes

The read-only [rhythm timing audit](P3_RHYTHM_BASELINE.md) found median downbeat bass delays behind kick of 61.11ms (Harbor), 63.93ms (After), 94.12ms (Silver). These may be deliberate pocket choices, not errors.

- `studio7/rhythm.py::shape_pocket`: optional phrase/style-aware bass anchor onset correction. Keeps every drum event, bass pitch, bass velocity, note length, pickup and explicit overlap intact. In the After score, 16 anchors shifted; median downbeat bass lag 63.93 → 17.02ms. Does **not** quantize the entire rhythm section.
- `studio7/drum_dynamics.py::shape_drum_dynamics`: deterministic kick/snare/hat velocity hierarchy by phrase position. No new hits, no changed onsets, no random timing, and explicit ghost/fixed hits unchanged. On the After test passage, 163/179 existing hits changed velocity; maximum change 6 MIDI velocity units. The separate transforms commute and leave melodic score data untouched.
- Both are **opt-in** CLI flags: `--rhythm-pocket`, `--drum-dynamics`. Earlier default renders and previously published files are preserved.

## Verified acceptance

- [Read-only timing baseline CI](https://github.com/goodselldartangan-star/Music_Studio/actions/runs/43118680421) succeeded.
- [P3 isolated kick/bass CI](https://github.com/goodselldartangan-star/Music_Studio/actions/runs/43119195729) succeeded: 36 focused tests, matched A/B, full MP3.
- [P3 drum dynamics CI](https://github.com/goodselldartangan-star/Music_Studio/actions/runs/43123081945) succeeded: 13 focused tests, matched drum-only A/B, decoded MP3, full integrated After arrangement with both options enabled.
- [Full recorded instrument workflow](https://github.com/goodselldartangan-star/Music_Studio/actions/runs/43123279343) succeeded: complete licensed recorded-sample install, all default demos plus optional P3 rhythm-pocket/drum-dynamics After render, passed its audio QA.

Tests prove deterministic event edits, compatibility, robust rendering and decoding. They do not prove tighter timing or accented drums sound better. For a future musical preference decision, compare short loudness-matched grooves when the arrangement context warrants it.

## Next

P4 — harmony and register coordination, beginning with an objective audit of overlapping lead/piano pitches and chord label/voicing consistency. Avoid blanket bans on intentional dissonance. Keep any revoicing option behind its own flag and acceptance gate.

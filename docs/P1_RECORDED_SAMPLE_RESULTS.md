# P1 — Recorded-instrument playback verification (2026-11-11)

**Decision:** P1 *engineering* gate complete. Advance one subsystem to P2 (instrument playing technique). No claim of listener preference, musical realism, or production approval is made.

## Focused fix

`studio7/samples.py` chose its round-robin sample take using `seed:pitch:length`, so merely editing a note's duration could silently change the original recording. The key is now `seed:pitch:velocity_layer`. The same note and seed retain the same attack/timbre through length-only changes. Its release envelope still changes as intended.

`tests/test_sample_take_identity.py` verifies identical early waveforms across changed lengths for 20 seeds and two distinct takes. The old synthesized instruments and score format are untouched.

## Actual publisher recordings (GitHub clean runner)

The `tools.audit_sample_coverage` check runs **after** the official sample archives are downloaded and unpacked, **before** any songs are rendered. Data below is from [successful real-asset workflow 43105376460](https://github.com/goodselldartangan-star/Music_Studio/actions/runs/43105376460):

| Sample collection | Recordings | Sampled MIDI range | Velocity layers |
|---|---:|---:|---|
| Meta Open Sound steel guitar (CC0) | 375 | 40–84 | 1, 2, 3 |
| Meta Open Sound piano (CC0) | 352 | 21–108 | 1, 2, 3, 4 |
| Meta Open Sound nylon guitar (CC0) | 348 | 40–83 | 1, 2, 3 |
| **Total** | **1,075** | | |

Across all three pre-existing demos: **220/220 sample-backed guitar and piano notes are exactly recorded at their requested pitch** (zero semitone transposition). Breakdown: harbor 134/134, after 10/10, silver 76/76. Original song notes and mix were not changed.

Recorded soft/mid/strong layers were checked at one pitch per instrument with MIDI velocities 24/70/115; all selected different real audio files of at least 0.1 seconds:
- Steel guitar pitch 62 → layers **1 / 2 / 3**
- Piano pitch 65 → layers **1 / 3 / 4**
- Nylon guitar pitch 62 → layers **1 / 2 / 3**

The existing scores mainly request middle layers (harbor: acoustic layer 2, piano layer 2; after: piano layer 2; silver: acoustic layer 2, piano layers 2–3). **P2 will address authored performance dynamics**; modifying the scores was intentionally out of P1 scope.

## Tests and limits

- 32 local unit tests passed, including same-take length invariance and exact-score pitch coverage fixtures.
- [Dedicated P1 clean-runner test 43103480466](https://github.com/goodselldartangan-star/Music_Studio/actions/runs/43103480466) passed.
- [Full real-library instrument-download / audit / three-demo render and QA 43105376460](https://github.com/goodselldartangan-star/Music_Studio/actions/runs/43105376460) passed.
- Existing FreePats electric bass/guitar SoundFonts and MuldjordKit drums are still installed and tested in the full render path, but the pitch-by-pitch report above is specific to the three Meta recorded instruments, not those SoundFonts. MuldjordKit requires CC BY attribution (DrumGizmo.org), per `docs/engine_audit_v7.md`.

**Limits:** Correct file mapping, real velocity layers, and clean decoding do not prove instruments sound natural or are played idiomatically. Dynamic phrasing, strum articulation, pedaling, drum groove, melodic development, mixing, and subjective sound preference remain separate roadmap stages. No listening sample was required to verify these engineering properties.

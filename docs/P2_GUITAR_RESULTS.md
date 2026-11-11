# P2 guitar playing technique — first substage complete (2026-11-11)

**Scope:** one musical subsystem: guitar chord attack order, stroke spacing and bounded expression. This does **not** close the entire P2 issue; bass and piano technique remain.

## New baseline-protected capability

- `studio7/playing.py::shape_strums(score)` produces a new score without touching the original. It adjusts only already-staggered groups of 3–6 ascending (downstroke) or descending (upstroke) guitar pitches. Simultaneous block chords, solo melodies, rests, drum events and non-guitar instruments are unchanged.
- Each group is limited to 14 ms per downstroke string or 11 ms per upstroke string; the originally authored first attack stays fixed. Velocity changes are at most 5 MIDI units. Every original pitch, note duration and note count is retained; struck strings may keep ringing into later attacks.
- `demo_v7.py --guitar-performance` opts in; default render behavior is unchanged. Enabled output uses `-p2-guitar` suffix to avoid overwriting previous audio.
- `tests/test_articulation.py` explicitly protects a multi-pitch chord plus second same-pitch attack, and a long, ringing PCM note overlapped with a shorter pluck. The existing independent voice allocator supports both; no new voice engine was needed.

## Objective tests and render

- 34 local tests passed: existing v7 and note lifecycle suites plus new P2 tests.
- Isolated 4-bar GM SoundFont A/B: **32 guitar strum groups**, **128 notes**, 16 downstrokes, 16 upstrokes changed in the full 16-bar source arrangement, maximum onset shift **19.667 ms**. Sample patch, note durations and pitches identical. A/B is RMS-matched at -41.77 dBFS. No acoustic quality preference is claimed.
- Full optional guitar-performance Harbor preview: **38.58-second MP3**; technical QA passed (RMS -21.93 dBFS, sample peak -1.49 dBFS, channel balance 0.27 dB, correlation 0.959).
- [**GitHub Actions guitar P2 verification succeeded**](https://github.com/goodselldartangan-star/Music_Studio/actions/runs/43110129074), including the focused tests, matched A/B audio render, and 39-second full integration. The A/B files and reports are saved as run artifacts.

## Limits and next step

This verifies non-destructive strumming and note overlap, **not** that programmed guitars sound natural to a listener. The test SoundFont is intentionally a consistent, portable playback fixture, not a replacement for our downloaded sampled instruments. P2 remains active to address bass-playing articulation and piano chord/pedal technique, separately, with the same isolated test protocol. Avoid requesting listener feedback until subjective instrument realism is the remaining question.

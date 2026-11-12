# P8 — Section arrangement and returning-section transition

**Engineering scope:** analyze density of existing intro/verse/build/final sections and create one **optional** quiet backing gesture before the final return, without altering the original composition.

## What changed

`studio7/sections.py::section_inventory` counts note and drum entrances across four 4-bar sections. This establishes texture density, **not** arrangement excellence.

`shape_transition_breath` removes the final closed hi-hat attack shortly before beat 48 and at most one short late bass pickup, preserving all other notes and their lengths. Open hi-hat accents that lead into the return remain. Nothing already sustaining is forcibly stopped, and the foreground melody, piano, guitar, harmony, note timing and sample patches are unchanged.

The optional flag is `demo_v7.py --transition-breath`; it generates separate `-p8-breath` files. The original released demos remain unchanged.

## Test results

- [Focused P8 GitHub workflow 43152580420](https://github.com/goodselldartangan-star/Music_Studio/actions/runs/43152580420) passed **26 tests**, matched original/alternate GM-backed drum+bass recordings, full optional After arrangement and MP3 QA.
- In the After controlled comparison, **one bass pickup at beat 47.52 (MIDI 45)** and **one closed hat at beat 47.53** were omitted.
- **Pre-transition waveform difference RMS = 0.0**, verifying the earlier score is not inadvertently affected; transition-and-after difference RMS ≈ **0.00069496** in the technical fixture.
- Tests preserve all lead and nonbass notes, unchanged drum attacks outside the narrow transition window, original bass note lengths, and explicit tail/overlap compatibility.
- [Real recorded-instrument acceptance workflow 43152723681](https://github.com/goodselldartangan-star/Music_Studio/actions/runs/43152723681) **passed**, including all original rendered examples and the optional After transition with recorded instruments and decoded MP3 QA.

## Limits

A late break may create contrast, but is not automatically musically superior. The original score already distinguishes introduction, verse, build and final section; adding a break only makes one potential structural option. Listen only when choosing the artistic direction of the song, not to approve a deterministic event deletion.

No finished song, new note composition or claim of production-level structure has been made.

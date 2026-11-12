# P4 — Harmony and register coordination: engineering gate complete

**Date:** 2026-11-11. **Decision:** P4's engineering acceptance passed. The optional register-separated mix is *not* declared aesthetically superior or made default.

## Verified findings

- All three existing scores have correctly spelled four-chord triad sequences, complete chord voicings and matching bass roots under `studio7/registers.py::audit_registers`.
- An exact same-register, sustained lead/piano overlap is not necessarily a wrong note. However, the atmospheric Silver score has **24** foreground/piano overlapping unisons at ≥0.24 beat, versus **2** in Harbor and **3** in After. There were no overlapping piano/lead semitone conflicts under this measurement.
- A tested optional `studio7/registers.py::separate_lead_piano` shifts an *entire* existing piano chord group down one octave only when it reduces a lead unison without introducing an additional measured semitone conflict. It keeps the full piano harmony, pitched note count, timing, length, velocity and original lead unchanged; fixed-register groups are skipped. This is frequency/register separation, **not** an EQ or compression change.
- Result: **Silver: 30 piano notes revoiced, counted unisons 24 → 0, semitone conflicts remain 0**. Harbor: 2 → 0; After: 3 → 0. The new piano notes remain in the recorded sample's MIDI range. Source compositions remain untouched.
- CLI flag: `--register-separation`; default audio remains unchanged and outputs carry the distinct `-p4-register` suffix.

## Evidence

- Five isolated P4 tests passed locally, including triad root/quality consistency and preservation of melody, pitch classes and original score.
- [Clean P4 GitHub Actions run 43124657339](https://github.com/goodselldartangan-star/Music_Studio/actions/runs/43124657339) passed **33 focused tests**, a matched four-bar piano+lead A/B and full Silver MP3 QA. The A/B is an engineering comparison, not a listener approval.
- [Full original publisher recordings integration 43124861612](https://github.com/goodselldartangan-star/Music_Studio/actions/runs/43124861612) passed installation, original demo QA and **Silver with optional P4 register spacing on recorded piano and guitar patches**.
- Uses existing [Berklee voice-leading principles](https://online.berklee.edu/takenote/voice-leading-paradigms-for-harmony-in-music-composition/) as research context. The transform only makes octave placements, not melodic voice-leading predictions.

## Limits / next

Moving piano an octave may alter intimacy, fullness, masking and perceived musical balance; metrics do not guarantee improvement, and some exact doublings are intentional. Keep opt-in until a contextual listening comparison is warranted.

P5 should focus on **melody and motifs**, especially phrase structure, rests, repeated hooks and meaningful cadences; don't treat more note changes as inherently better.

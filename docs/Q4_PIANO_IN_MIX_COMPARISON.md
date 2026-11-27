# Q4 — Upright versus grand piano, matched in the same Silver arrangement

**November 26, 2026. Engineering in-context A/B gate passed; listener preference not yet decided.**

[Verified full-bank and in-context GitHub Actions run](https://github.com/goodselldartangan-star/Music_Studio/actions/runs/45924512479) passed **22 focused tests**, verified 641 original Salamander FLACs against the pinned publisher Git objects, rendered the complete 64-note grand piano part using two independent sfizz processes and one shared physical-pedal instance, and generated two independent **12-second audio comparisons** with otherwise identical Silver arrangement.

## Sources and non-piano invariants

- **A:** Original Meta Open Sound **CC0 upright piano** (publisher-verified `meta-piano-v1.0.0` OGG asset, publisher-updated 2026-11-12 archive revision).
- **B:** Salamander Grand Piano V3 **CC BY 3.0**, Alexander Holm (SFZ by kinwie, retuned by Markus Fiedler), original pinned 641 FLACs, one shared pedal-noise instance.
- **All other recorded-instrument voices identical:** the project’s existing CC0 nylon guitar, electric-guitar SF2, finger-bass SF2, MuldjordKit recorded drums and existing lead/effects modules. Bass, guitar, kit, lead notes, volume, EQ, panning, room, and all score events are unchanged.
- Both use the same 16-bar original Silver Rain score (**64 piano note events**) and the existing `studio7/render.py::process_stems` effects path. No other AI used.

## Measurements

| Controlled measurement | GM technical fixture | Actual licensed recorded-instrument backing |
|---|---:|---:|
| Processed piano RMS grand versus upright | +0.3096 dB | +0.3096 dB |
| Full-mix waveform difference RMS | 0.07321631 | 0.08440492 |
| Original upright excerpt RMS | −21.940 dBFS | −22.400 dBFS |
| Grand excerpt RMS **after comparison-only matching** | −21.940 dBFS | −22.400 dBFS |
| Excerpt RMS mismatch | 0.000 dB | 0.000 dB |
| Upright excerpt sample peak | 0.767611 | 0.840000 |
| Grand excerpt sample peak after RMS match | 0.716875 | 0.619676 |
| Other processed stems identical | Yes | Yes |
| MP3 decoder and PCM peak gate | Passed | Passed |

The real-backline grand needed **0.737709** comparison-only gain to match the upright’s overall 19–31-second excerpt RMS. This is not a new mastering setting or claim that the grand's dynamics should be compressed. The full mixes before this A/B-only gain had different loudness because piano attacks, stereo and release/pedal signals differ. Both exported preview excerpts have equal RMS, not equal instantaneous peaks or identical loudness perception.

## Reproducible files

- `tools/compare_pianos_in_mix_q4.py` renders the same original score once through the recorded backing, swaps only the piano source, processes both identically, checks unchanged non-piano processed stems, measures dry/processed piano levels and excerpt loudness, writes separate 224k MP3s and a JSON provenance report.
- `tests/test_compare_pianos_in_mix_q4.py` validates stereo lane/pedal decoding, source clock and exact two-instance signature.
- `.github/workflows/q4-salamander-full-bank.yml` now includes both the earlier small GM technical fixture and the **actual publisher-backed Silver** mix. It downloads and validates source recordings only within clean CI; artifacts include short derived MP3s and text reports, **not** source FLAC libraries or overwritten historical songs.
- GitHub run `45924512479` → artifact `Q4-Full641-Licensed-Piano-Technical-Evidence`; in particular, `real-backing-comparison/Q4_Silver_meta_upright_comparison.mp3` and `real-backing-comparison/Q4_Silver_salamander_grand_comparison.mp3`.

## Engineering conclusion and outstanding creative decision

**Pass:** Full source integrity, deterministic same-score instrument swapping, independent repeated-note tails, 16 pedal CC64 events with one physical-pedal sound instance, unchanged non-piano stems, stereo playback, MP3 decoding, no peak clipping, and matched-level comparison excerpts.

**Not established:** That a sampled grand is *better* for this pop/electronic Silver arrangement than the original CC0 upright. A different piano can change intimacy and song texture even when technically complete. No subjective human listening test or high-grade acoustic ear assessment is claimed. A source backend should not become the default until a short, truly level-matched musical-context listening choice is warranted. Keep earlier Meta renders and GitHub release assets intact.

Next optional step should focus on evaluating whether the new piano fits the **full musical palette** with alternate arrangements, not additional sample-library changes. If the user prefers fewer listening requests, keep the selection deferred and continue with isolated guitar/bass expression once Q4 is explicitly treated as technically complete.

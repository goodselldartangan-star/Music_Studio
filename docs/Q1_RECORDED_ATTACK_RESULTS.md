# Q1 — Recorded sample attack and source-format audit

**Scope:** Post-P9 musical-quality research; read-only inspection of all licensed publisher samples. No score, sampler, sample files or original MP3s were modified. **Result: audit completed, do not enable automatic global trimming.**

## Measured source characteristics

[Successful clean real-library workflow](https://github.com/goodselldartangan-star/Music_Studio/actions/runs/43156295047) downloaded and verified the same original Meta CC0 1.0.0 OGG archives as Music Studio v7 and audited all 1,075 sound recordings. It also passed six attack-detector/test fixtures (five original and one distinct-physical-string guard).

| Source | Samples | Format / channels / original rate | Detected attack median | 95th percentile | Above severe review threshold | Within-string or same-key velocity groups with >25 ms spread |
|---|---:|---|---:|---:|---:|---:|
| Steel acoustic guitar | 375 | mono OGG, 48 kHz | 17 ms | 35 ms | 0 at ≥75 ms | 26 |
| Upright piano | 352 | mono OGG, 48 kHz | 4 ms | 10 ms | 0 at ≥40 ms | 0 |
| Nylon guitar | 348 | mono OGG, 48 kHz | 5 ms | 21 ms | 0 at ≥40 ms | 1 |

The detector measures first sustained energy in a 3ms RMS window with a 1ms hop and source-relative threshold; it does **not** claim to locate the exact musical pitched attack. An attack delay can be musical string/finger noise or natural variation, not just leading digital silence. The archive's piano did not reproduce the source project's documented extreme late starts under this detector.

### Important methodological correction

Initial guitar reports wrongly pooled samples of the **same MIDI pitch across different physical strings**. Since the string itself affects attack and timbre, that exaggerates supposed *velocity-layer* variation. Q1 now groups by **MIDI pitch and guitar string zone** before comparing velocity layers. Synthetic tests explicitly catch this confound.

Some legitimate within-string variations remain: steel guitar 26 groups and nylon 1 group have detected layer spreads above 25ms; for example steel D-string F♯4 is measured at 6/20/42ms for layers 1/2/3. This is a targeted research lead, **not proof of a recording error**.

## Source fidelity and future work

The publisher's official [Meta Open Sound agent guide](https://github.com/facebookincubator/Meta-open-sound/blob/main/AGENTS.md) says the OGG previews are mono and the separate recording masters are 24-bit / 48kHz WAV. Current Music Studio rendering uses the OGG release archives and resamples to the engine's 44.1kHz rate. A later optional high-fidelity asset path could be investigated, with complete provenance and a controlled comparison, without replacing original licenses/MP3s.

The publisher's [changelog](https://github.com/facebookincubator/Meta-open-sound/blob/main/CHANGELOG.md) discusses sample-attack fixes, but the current pinned archives show **no severe late-energy examples by this Q1 threshold**. We will not strip pick/finger transients or globally slide MIDI notes to manufacture aligned attacks.

## Decision

**Q1 measurement gate complete. No sonic alteration warranted from the current evidence.** Next focused investigation: whether the sampler's deterministic random choice across different **guitar physical strings** produces unnatural string assignment in simultaneous chords. Prove it with a score/source-map audit before editing playback. Human preference decisions can be deferred until one specific before/after difference cannot be resolved objectively.

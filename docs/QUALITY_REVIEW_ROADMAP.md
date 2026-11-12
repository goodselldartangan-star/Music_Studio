# Music Studio — post-checklist sound-quality roadmap

**Operating rule:** Exactly one major sound/quality subsystem at a time. Begin with a reproducible defect or controlled hypothesis, verify using source recordings and offline tests, render one short isolated A/B only if needed, and keep all previously released audio intact. GPT is the only AI; sampled instruments and ordinary DSP are not AI systems. Never confuse automated pass/fail with subjective musical approval.

| Item | Status | Focus and evidence | Next technical/creative gate |
|---|---|---|---|
| **Q1 — Source recorded-note attack audit** | **DONE — no blanket trim justified** | [Q1 report](Q1_RECORDED_ATTACK_RESULTS.md): 1,075 source OGG files inspected, instrument/velocity attack timing documented, cross-string confound corrected | Preserve original pick/finger noise; targeted new issue only if a source-level defect is reproducible |
| **Q2 — Guitar physical-string sample selection** | **DONE — optional mapping and guitar chord voicing passed** | [Q2 report](Q2_GUITAR_STRING_RESULTS.md): 24/32 Harbor and 2/4 Silver strums conflicted before; 36/36 strums map to distinct physical strings with option enabled. Full source recordings and CI verified | Optional `--guitar-string-mapping`; subjective guitar feel not automatically approved |
| **Q3 — Production-quality source recording tier** | **NEXT — research only** | Compare publisher's 24-bit WAV masters against current mono OGG previews of *the same* pitches/layers; report stereo channels, sample rates, licensing, attack and fidelity metrics | Only propose optional production asset tier after verified source/provenance and a short same-note, loudness-matched comparison; never pretend lossless means automatically preferred |
| **Q4 — Expressive continuous instruments** | QUEUED | Genuine piano damper/sustain-resonance support, guitar string muting, bass slides and connected articulation: test physical/asset feasibility before coding | Isolated reference-backed instrument behaviors with no stolen voices or stuck releases |
| **Q5 — Combined musical decisions** | DEFERRED | Controlled pairwise combinations of approved optional changes only when context warrants | A single short, level-matched listener A/B only when a genuine musical-feel preference remains |

The [original P0–P9 engineering checklist](IMPROVEMENT_ROADMAP.md) remains completed. It does **not** certify a professionally produced or emotionally satisfying musical performance. Preserve old master files and use explicit opt-in switches for experimental treatments.

# Music Studio — post-checklist sound-quality roadmap

**Operating rule:** Exactly one major sound/quality subsystem at a time. Begin with a reproducible defect or controlled hypothesis, verify using source recordings and offline tests, render one short isolated A/B only if needed, and keep all previously released audio intact. GPT is the only AI; sampled instruments and ordinary DSP are not AI systems. Never confuse automated pass/fail with subjective musical approval.

| Item | Status | Focus and evidence | Next technical/creative gate |
|---|---|---|---|
| **Q1 — Source recorded-note attack audit** | **DONE — no blanket trim justified** | [Q1 report](Q1_RECORDED_ATTACK_RESULTS.md): 1,075 source OGG files inspected, instrument/velocity attack timing documented, cross-string confound corrected | Preserve original pick/finger noise; targeted new issue only if a source-level defect is reproducible |
| **Q2 — Guitar physical-string sample selection** | **DONE — optional mapping and guitar chord voicing passed** | [Q2 report](Q2_GUITAR_STRING_RESULTS.md): 24/32 Harbor and 2/4 Silver strums conflicted before; 36/36 strums map to distinct physical strings with option enabled. Full source recordings and CI verified | Optional `--guitar-string-mapping`; subjective guitar feel not automatically approved |
| **Q3 — Production-quality source recording tier** | **DONE — stereo WAV playback and source identity verified** | [Q3 results](Q3_SOURCE_FIDELITY_RESULTS.md): all 1,075 OGG/WAV sources paired; 33 tests and clean real-source stereo A/B passed | Optional original 24-bit WAV backend stays opt-in; larger files and subjective preferences unapproved |
| **Q3.1 — Joint guitar string + stereo source verification** | **DONE — full guitar takes matched** | [Q3.1 report](Q3_COMBINED_GUITAR_STEREO_RESULTS.md): all 140 guitar notes matched exact OGG/WAV takes, 36 distinct strums, 37 CI tests, no piano/voice interference | No default changes; compatibility gate passed, guitar stereo width preference unjudged |
| **Q4 — Expressive continuous instruments** | **ACTIVE — examine real pedal/resonance libraries before code** | Research genuine piano damper/pedal noise and string resonance sample support, plus guitar muting and bass connected articulation | Test publisher sample licenses, engine capability and short fixtures. No fake pedal resonance or voice truncation |
| **Q5 — Combined musical decisions** | DEFERRED | Controlled pairwise combinations of approved optional changes only when context warrants | A single short, level-matched listener A/B only when a genuine musical-feel preference remains |

The [original P0–P9 engineering checklist](IMPROVEMENT_ROADMAP.md) remains completed. It does **not** certify a professionally produced or emotionally satisfying musical performance. Preserve old master files and use explicit opt-in switches for experimental treatments.

## Q3 and Q3.1 accepted (November 13, 2026)

- [Q3 stereo-source clean CI](https://github.com/goodselldartangan-star/Music_Studio/actions/runs/43532042435) passed all 33 tests and publisher original OGG/stereo WAV matched source A/Bs; original mono default preserved.
- [Q3.1 complete real-source compatibility CI](https://github.com/goodselldartangan-star/Music_Studio/actions/runs/43543937377) passed 37 tests and 140/140 exact performed-take matches across 36/36 distinct guitar-string strums. The WAV guitar stereo-side energy was relatively low (Harbor −65.51 dBFS, Silver −75.18 dBFS).
- Q4 now owns the *next* question: actual continuous instrument behavior (piano sustain pedal, resonance, note-off samples), rather than more codec or string mapping changes. Research real licensed performance layers before claiming that holding samples longer simulates physical pedaling.

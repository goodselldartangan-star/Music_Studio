# Music Studio — post-checklist sound-quality roadmap

**Operating rule:** Exactly one major sound/quality subsystem at a time. Begin with a reproducible defect or controlled hypothesis, verify using source recordings and offline tests, render one short isolated A/B only if needed, and keep all previously released audio intact. GPT is the only AI; sampled instruments and ordinary DSP are not AI systems. Never confuse automated pass/fail with subjective musical approval.

| Item | Status | Focus and evidence | Next technical/creative gate |
|---|---|---|---|
| **Q1 — Source recorded-note attack audit** | **DONE — no blanket trim justified** | [Q1 report](Q1_RECORDED_ATTACK_RESULTS.md): 1,075 source OGG files inspected, instrument/velocity attack timing documented, cross-string confound corrected | Preserve original pick/finger noise; targeted new issue only if a source-level defect is reproducible |
| **Q2 — Guitar physical-string sample selection** | **DONE — optional mapping and guitar chord voicing passed** | [Q2 report](Q2_GUITAR_STRING_RESULTS.md): 24/32 Harbor and 2/4 Silver strums conflicted before; 36/36 strums map to distinct physical strings with option enabled. Full source recordings and CI verified | Optional `--guitar-string-mapping`; subjective guitar feel not automatically approved |
| **Q3 — Production-quality source recording tier** | **DONE — stereo WAV playback and source identity verified** | [Q3 results](Q3_SOURCE_FIDELITY_RESULTS.md): all 1,075 OGG/WAV sources paired; 33 tests and clean real-source stereo A/B passed | Optional original 24-bit WAV backend stays opt-in; larger files and subjective preferences unapproved |
| **Q3.1 — Joint guitar string + stereo source verification** | **DONE — full guitar takes matched** | [Q3.1 report](Q3_COMBINED_GUITAR_STEREO_RESULTS.md): all 140 guitar notes matched exact OGG/WAV takes, 36 distinct strums, 37 CI tests, no piano/voice interference | No default changes; compatibility gate passed, guitar stereo width preference unjudged |
| **Q4 — Expressive continuous instruments** | **ACTIVE — full 641-FLAC standalone piano passed, instrument-in-context approval pending** | [Complete full-bank report](Q4_FULL_641_SALAMANDER_RESULTS.md): exact source-hash validation, 20 clean tests, Silver 64-note complete SFZ render across 2 independent piano processes and 1 shared pedal, measured memory/CPU and no clip | Next: level-matched Meta upright vs Salamander grand **in full unchanged mix**, separate technical compatibility from aesthetic preference; no default replacement |
| **Q5 — Combined musical decisions** | DEFERRED | Controlled pairwise combinations of approved optional changes only when context warrants | A single short, level-matched listener A/B only when a genuine musical-feel preference remains |

The [original P0–P9 engineering checklist](IMPROVEMENT_ROADMAP.md) remains completed. It does **not** certify a professionally produced or emotionally satisfying musical performance. Preserve old master files and use explicit opt-in switches for experimental treatments.

## Q3 and Q3.1 accepted (November 13, 2026)

- [Q3 stereo-source clean CI](https://github.com/goodselldartangan-star/Music_Studio/actions/runs/43532042435) passed all 33 tests and publisher original OGG/stereo WAV matched source A/Bs; original mono default preserved.
- [Q3.1 complete real-source compatibility CI](https://github.com/goodselldartangan-star/Music_Studio/actions/runs/43543937377) passed 37 tests and 140/140 exact performed-take matches across 36/36 distinct guitar-string strums. The WAV guitar stereo-side energy was relatively low (Harbor −65.51 dBFS, Silver −75.18 dBFS).
- Q4 now owns the *next* question: actual continuous instrument behavior (piano sustain pedal, resonance, note-off samples), rather than more codec or string mapping changes. Research real licensed performance layers before claiming that holding samples longer simulates physical pedaling.

## Q4 first piano-noteoff substage accepted (November 13, 2026)

- [Q4 focused real publisher-piano CI](https://github.com/goodselldartangan-star/Music_Studio/actions/runs/43545431132) passed 28 tests, audio A/B, and 352-source CC0 archive integrity. The first 32 piano note-offs were delayed in controlled windows; source recording selection and old default intro unchanged.
- [Q4 full recorded-instrument integration](https://github.com/goodselldartangan-star/Music_Studio/actions/runs/43545222979) passed Silver MP3 technical QA, older renderer regression and no-overwrite release publishing.
- This is accurate MIDI-style *key-release deferral*, not genuine damper noise or string resonance. A compatible ARIA-class SFZ engine and separately sampled release/pedal layers remain **unimplemented**. Do not mark Q4 as wholly complete or automatically enable this sound option.

## Q4 SFZ feasibility gate — verified November 26, 2026

- [Successful 10-test sfizz/SFZ clean build](https://github.com/goodselldartangan-star/Music_Studio/actions/runs/45920743367) downloaded and SHA-verified five genuine Salamander Grand Piano CC BY 3.0 FLAC recordings, with 19 short MIDI playback conditions and archived source attribution/derived test MP3s.
- The miniature SFZ triggered actual piano key releases, string resonance and pedal mechanism sounds. However the new short same-pitch note-off interrupted an earlier sounding C4 even with `note_polyphony=1` omitted: ~**0.98** post-noteoff waveform error, and only ~**12%** of expected old-note tail RMS. Different MIDI channel alone did not fix the collision.
- `studio7/sfz_voice_lanes.py` now schedules overlapping same-pitch notes on **separate future SFZ sampler instances**, with release-guard intervals and explicit pool-capacity errors. It is **pure planning only**; no full sampler has been plugged into the Music Studio renderer.
- **Decision:** retain the successful original Meta piano backend, no fake physical pedal/resonance claim, no default changes. Further work: efficient independent-instance audio rendering/mixing and complete SFZ/ARIA program compatibility, then musical preference.

## Q4 independent-instance SFZ audio verified (November 26, 2026)

- [14-test real publisher-SFZ audio CI](https://github.com/goodselldartangan-star/Music_Studio/actions/runs/45921081092) confirmed a standalone separate-process lane mix preserves the older ringing C4 after the newer short note-off, with relative waveform error **0.0** against independently rendered source PCM; single-synth playback had previously lost ~88% of the old-note RMS.
- [Final repeat + full Silver concurrency audit](https://github.com/goodselldartangan-star/Music_Studio/actions/runs/45921258338) passed; **64 original Silver piano events require 2 independent SFZ instances** both with and without optional pedal timing. Each lane has a 0.5-second same-note release guard.
- This is **not** a full production piano backend. The actual full Salamander SFZ includes 641 licensed sample files and ARIA controls; memory budget, complete voice/velocity behavior, and one-time pedal-mechanism routing are still untested. Leave Meta piano and published MP3s unchanged.

## Q4 full original piano demonstrated (November 26, 2026)

- [Full 20-test licensed bank and audio CI](https://github.com/goodselldartangan-star/Music_Studio/actions/runs/45923699850) passed after verifying **641/641** actual publisher FLAC bytes totaling **748,397,030**, including original natural/retuned tuning definitions and correct release-key mappings.
- The complete 40.647-second Silver piano part passed with **64 source notes**, **two isolated sfizz instances**, and **one physical pedal mechanism instance** for **16 MIDI CC64 edges**. Source waveform peak **0.077332**; a 12-second MP3 decoded successfully.
- Per-process peak RSS: **162,428 KiB**, **125,808 KiB** and **17,968 KiB** (the renders were sequential). No claim about simultaneous resource needs or musical superiority.
- [Q4 full-bank report](Q4_FULL_641_SALAMANDER_RESULTS.md) documents fixed source-include, portable-path and 102-BPM controller timing issues. Production audio remains unchanged; the full grand is a **separate optional prototype**, not yet an approved radio-ready piano sound.

# Music Studio — post-checklist sound-quality roadmap

**Operating rule:** Exactly one major sound/quality subsystem at a time. Begin with a reproducible defect or controlled hypothesis, verify using source recordings and offline tests, render one short isolated A/B only if needed, and keep all previously released audio intact. GPT is the only AI; sampled instruments and ordinary DSP are not AI systems. Never confuse automated pass/fail with subjective musical approval.

| Item | Status | Focus and evidence | Next technical/creative gate |
|---|---|---|---|
| **Q1 — Source recorded-note attack audit** | **DONE — no blanket trim justified** | [Q1 report](Q1_RECORDED_ATTACK_RESULTS.md): 1,075 source OGG files inspected, instrument/velocity attack timing documented, cross-string confound corrected | Preserve original pick/finger noise; targeted new issue only if a source-level defect is reproducible |
| **Q2 — Guitar physical-string sample selection** | **DONE — optional mapping and guitar chord voicing passed** | [Q2 report](Q2_GUITAR_STRING_RESULTS.md): 24/32 Harbor and 2/4 Silver strums conflicted before; 36/36 strums map to distinct physical strings with option enabled. Full source recordings and CI verified | Optional `--guitar-string-mapping`; subjective guitar feel not automatically approved |
| **Q3 — Production-quality source recording tier** | **DONE — stereo WAV playback and source identity verified** | [Q3 results](Q3_SOURCE_FIDELITY_RESULTS.md): all 1,075 OGG/WAV sources paired; 33 tests and clean real-source stereo A/B passed | Optional original 24-bit WAV backend stays opt-in; larger files and subjective preferences unapproved |
| **Q3.1 — Joint guitar string + stereo source verification** | **DONE — full guitar takes matched** | [Q3.1 report](Q3_COMBINED_GUITAR_STEREO_RESULTS.md): all 140 guitar notes matched exact OGG/WAV takes, 36 distinct strums, 37 CI tests, no piano/voice interference | No default changes; compatibility gate passed, guitar stereo width preference unjudged |
| **Q4 — Expressive continuous instruments** | **ENGINEERING DONE — piano, stopped-guitar and alternative recorded-bass gates passed; musical approval open** | [641-file grand](Q4_FULL_641_SALAMANDER_RESULTS.md), [Q4.2 stopped guitar](Q42_SOURCE_ARTICULATION_RESULTS.md), [Q4.3 real recorded bass](Q43_BASS_ARTICULATION_RESULTS.md): tested original piano release/pedal voices, stopped steel-guitar tails, 11 bass-pitch source release sweep and 426-WAV Fashionbass with level-matched full-band Harbor A/B | No default instrument replacement; Q5 may consider isolated listener-level source choices only when genuinely useful, and avoid unsupported bass slides |
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

## Q4 actual song-context source comparison accepted (November 26, 2026)

- [Final level-matched full real-library Q4 CI](https://github.com/goodselldartangan-star/Music_Studio/actions/runs/45924512479) passed **22 focused tests**, all 641 Salamander source files, original 64-note Silver score, and a real licensed nylon/electric guitar, bass and recorded kit backing.
- The only variant was the piano waveform (Meta upright CC0 versus Salamander grand CC BY 3.0 with CC64 pedal noise/release layers). All other processed stems were byte-identical and the 12-second 19–31s comparisons measured **−22.400 dBFS RMS each**. Piano stem difference was **+0.3096 dB**, both MP3s decoded, and excerpt peaks were **0.840000** and **0.619676**.
- [A/B technical and provenance report](Q4_PIANO_IN_MIX_COMPARISON.md) includes the small GM reference comparison and the definitive licensed recorded-instrument comparison. **This validates compatibility and reproducibility, not musical superiority or artistic listener preference.** Original released samples and defaults unchanged.
- Next single-subsystem quality topic may be guitar muting/connected bass articulation. Avoid arbitrary synthetic FX if no authentic performance/source evidence; treat choosing the grand as a separate optional artistic decision.

## Q4.2 real-guitar stopped-string release passed (November 26, 2026)

- [Source-label original bank audit](https://github.com/goodselldartangan-star/Music_Studio/actions/runs/45943940787) passed 5 tests: Meta steel **375** and nylon **348** guitar recordings, FreePats clean electric SF2 **13** samples, finger bass **12**, picked bass **13**; none have **named** mute/slide sample labels. Names alone do not establish total absence of incidental fret sounds.
- [Isolated sampled acoustic guitar](https://github.com/goodselldartangan-star/Music_Studio/actions/runs/45944126899) passed 6 tests: 24 selected Harbor upstroke note tails stopped with a 240ms hold + 42ms cosine release; original picked attacks and older independent notes preserved; level-matched 12-second isolated guitar examples.
- [Complete Harbor recorded-band A/B](https://github.com/goodselldartangan-star/Music_Studio/actions/runs/45944285311) passed 6 tests and non-guitar stem exact identity. Original/experimental excerpts both **−19.752 dBFS RMS**, no clipping; guitar change perceptible as nonzero waveform difference (full mix RMS **0.00854907**), *not* subjectively approved. [Q4.2 report](Q42_SOURCE_ARTICULATION_RESULTS.md).
- Original music, normal guitar rendering, and piano/bass processing are unchanged without optional explicit note tags. **Next focused topic:** source-backed bass note transitions; avoid pretending that finger/picked SF2 samples contain dedicated slides or hammer-ons.

## Q4.3 full original sampled-bass source and in-context comparison (November 27, 2026)

- [Existing finger and picked bass audio](https://github.com/goodselldartangan-star/Music_Studio/actions/runs/46049228743) passed 19 tests. A source-aware SFZ release guard changes **no waveform** versus the 0.12s current channel guard; [complete all-11-original-pitch sweep](https://github.com/goodselldartangan-star/Music_Studio/actions/runs/46049417742) found **0.0 waveform difference on 22 pitch/bank combinations**. **Keep current bass allocator**.
- [Pinned Karoryfer Fashionbass source/probe](https://github.com/goodselldartangan-star/Music_Studio/actions/runs/46049979343) verified **426 CC0 WAV paths**: 285 note samples, 76 physical key-release samples and 65 other sound samples. A real D2 recorded release triggered after noteoff with original note's pre-release attack identical (post-release A/B RMS difference **0.0003863**). No fake slides.
- [Complete 426 original WAV source test](https://github.com/goodselldartangan-star/Music_Studio/actions/runs/46050239756) hash/audio-verified **345,108,228 bytes** and rendered 36 original Harbor bass events over 38.556s in two independent SFZ instances. Peak source sample **0.120667**; derived MP3 decoded safely.
- [Final matched real-band Harbor bass A/B](https://github.com/goodselldartangan-star/Music_Studio/actions/runs/46050683878) passed **13 tests**; other recorded instrument stems were exactly unchanged, processed bass gain difference **−0.0345 dB**, 12-second full mix excerpts **−19.682 dBFS RMS each**, no clipping or original release overwrites. [Technical report](Q43_BASS_ARTICULATION_RESULTS.md) documents source hashes, performance and limitations. Recordings are authentic but **no subjective preference was established**.
- **Q5 remains deferred** pending a reason to compare musical treatments. Keep experimental bass/piano backends separate, do not combine them automatically, and do not invent per-note slide sounds when the source lacks such recordings.

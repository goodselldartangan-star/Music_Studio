# Q4.3 — Source-backed bass articulation and a real alternative bank

**Status: source inventory, per-note lifecycle and full recorded-band technical gates PASSED, November 27, 2026. Artistic bass choice NOT decided. Original released songs and Music Studio defaults untouched.**

## First measure the existing bass — do not change it just for larger numbers

The original FreePats finger- and picked-bass SFZ maps at `freepats/electric-bass-YR` declare release settings of **0.50 and 0.30 seconds**, while `studio7/articulation.py` reserves a same-pitch MIDI voice channel for **0.12 seconds** after noteoff.

- [Original source-repluck comparison](https://github.com/goodselldartangan-star/Music_Studio/actions/runs/46049228743) passed **19 tests** using genuine FreePats SF2 banks and the original publisher SFZ maps. A second B1 attack 0.18s after the first noteoff was rendered with both the current 0.12s channel guard and a 0.30/0.50s source-informed guard. The two output waveforms were **identical** in the tested scenario.
- [Full original score-pitch sweep](https://github.com/goodselldartangan-star/Music_Studio/actions/runs/46049417742) repeated the real-audio comparison across **all 11 distinct scored bass pitches** used in Harbor, After and Silver, with both finger/picked source banks. **22 pitch/bank combinations** had **0.0 measured waveform difference** between default and source-informed release guards.
- **Decision:** Leave the default 0.12s channel guard unchanged for these exact source banks; changing it without an audible/measurement defect would add complexity. `render_polyphonic(..., release_guard_s=...)` is a validated optional diagnostic argument only, default unchanged. This does not prove other SF2 banks have the same note lifecycle.

## What the current source banks lack, and the best new candidate

The [Q4.2 source inventory](Q42_SOURCE_ARTICULATION_RESULTS.md) found only pitched-note mappings with **no explicitly named release/slide/hammer-on sample zones** in the two current FreePats bass SF2s. Absence of a named label does not prove the recordings contain no incidental string noise.

The [Karoryfer Fashionbass publisher repository](https://github.com/sfzinstruments/karoryfer.fashionbass), original commit **`0703973b300a6bacb837602be9b588ab64732a72`**, provides actual **CC0 1.0 licensed** electric bass recordings. The original `fashionbass.sfz` maps the full source, including **19 separate key-release zone groups** and five velocity layers, three note round-robins and four release-noise round-robins. Its regular map includes recorded physical release noise, unlike a short MIDI gate that simply fades a note.

| Original recording category | Verified publisher WAV files |
|---|---:|
| Pitched bass note samples | 285 |
| Separately recorded key/string-release samples | 76 |
| Other distinct bass noise recordings | 65 |
| **Total** | **426** |

The original recordings total **345,108,228 bytes**. Every one is **44.1 kHz mono WAV** with a valid audio header, and the original fully mapped `fashionbass.sfz` references exactly these 426 files. The companion `fashionbass_clean.sfz` references the same notes/noises without the 76 release recordings. The real mapped bass range covers **all 11 bass pitches** used in all existing Music Studio songs. Other candidates were reviewed but not installed: Growlybass includes useful staccato and releases, but its principal mapped range does not cover all authored low bass pitches without changing pitches; the much larger Black And Blue Basses library can remain a future alternative.

## Source checks and real sound validation

1. [Pinned two-original-WAV release gate](https://github.com/goodselldartangan-star/Music_Studio/actions/runs/46049979343) passed **4 tests** and downloaded only original `notes/d2_mf_rr1.wav` and `release/d2_release_rr1.wav`, verified by their original Git blob hashes. Two derived programs played the **same original note**; one triggered its **actual recorded release** at MIDI noteoff. The pre-noteoff waveform difference was **0.0 RMS**, and after noteoff the recorded release produced **0.0003863 RMS** difference. This proves a genuine sample trigger without changing the picked attack.
2. [Full 426-WAV source and Harbor standalone run](https://github.com/goodselldartangan-star/Music_Studio/actions/runs/46050239756) passed **10 tests**, exact original-WAV Git hashes, SFZ file closure and valid WAV sample headers. The 36 unmodified Harbor bass notes rendered for **38.556 seconds** via **two separate sfizz processes** to preserve independent same-pitch tails. Output RMS **0.00924079**, peak **0.120667**, valid 44.1kHz center/mono audio, 12-second MP3 decoded successfully.
3. [Full original recorded-instrument Harbor A/B](https://github.com/goodselldartangan-star/Music_Studio/actions/runs/46050683878) passed **13 tests** and used the exact same source-backed Meta guitar/piano, FreePats electric-guitar and MuldjordKit drum instruments. The only change was the bass dry stem: existing FreePats finger-bass SF2 versus a new full CC0 Fashionbass SFZ stem. Non-bass source and processed stems were **sample-for-sample identical**; score, pitches, note lengths, start times and velocities were untouched.

| Full Harbor comparison | Existing FreePats finger bass | Optional Fashionbass |
|---|---:|---:|
| Processed bass level difference | Reference | −0.0345 dB |
| Level-matched 12-second entire-mix excerpt | −19.682 dBFS RMS | −19.682 dBFS RMS |
| Excerpt peak, safe headroom | 0.707194 | 0.820000 |
| MP3 decode and no clipping | Pass | Pass |

The complete master-waveform difference RMS is **0.07064476**. The Fashionbass preview used **×1.401492 excerpt-only level matching**, then both excerpts used common headroom **×0.841898**. These are *listening-comparison-only gains*, not new song mastering parameters. The short derived MP3s and technical reports are in the run artifact.

Separate sfizz process measurements on the successful final run were **0.21s / 53,848 KiB** and **0.23s / 46,400 KiB** wall time/peak RSS on the GitHub runner. Those processes ran sequentially, and the figures do not represent simultaneous or production RAM use.

## Architecture and future decisions

- `tools/probe_bass_release_q43.py`, `tools/sweep_bass_retrigger_q43.py` — research the *existing* SF2 renderer's real note lifecycle. Do not modify ordinary bass.
- `tools/probe_fashionbass_q43.py`, `tools/verify_fashionbass_full_q43.py` — source provenance and original sample/noise mapping, exact pinned original recording hashes and audio formats.
- `tools/render_fashionbass_full_q43.py` — deterministic original-score bass-to-independent-instance MIDI lanes and genuine source WAV rendering/mixing. Reuses the isolated voice-lane planner but does not alter `studio7/render.py`, guitars, piano or other channels.
- `tools/compare_fashionbass_in_mix_q43.py` — compares bass choices inside otherwise identical recorded Harbor backing, measures levels and exports **only short derived audio examples**. No original publisher WAV files are redistributed through CI artifacts.
- **Not established:** Which bass sounds musically better; no demonstrated recorded slide/hammer-on in Fashionbass and no reason to fake one; no promise that a successful parse certifies every ARIA/sampler-specific opcode. MIDI note rendering and selective source-release playback have passed, but general-purpose long-term instrument integration should be a separate opt-in change.
- **Next:** Pause bass-engine changes pending a genuine aesthetic decision on these matched-level full-mix A/Bs, or a reproducible musical deficiency in another part. Keep earlier note lifecycle, Q2/Q3 guitar improvements, real piano experiment and published music intact.

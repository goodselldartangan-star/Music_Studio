# Q3.1 — Physically mapped guitar strings with stereo master WAV sources

**Status: scoped engineering validation passed, November 13, 2026.** This is a focused **Q2 + Q3 compatibility gate**, not a replacement for Q4 expressive-continuous-instrument research. It changes no score, sample file, default audio, or existing release.

## Combined-source result

The [successful clean GitHub Actions run](https://github.com/goodselldartangan-star/Music_Studio/actions/runs/43543937377) passed **37 unit/regression tests**, including four Q3.1 source-combination fixtures. It downloaded the original licensed mono OGG previews and 24-bit/48kHz stereo WAV recordings, checked archive identities, then exercised the whole existing guitar score.

| Original score | Guitar source notes compared | Matching OGG/WAV performed takes | Physically distinct string strums | Remaining conflicts | WAV guitar stereo side RMS |
|---|---:|---:|---:|---:|---:|
| Harbor — steel guitar | 128 | 128/128 | 32/32 | 0 | −65.51 dBFS |
| Silver — nylon guitar | 12 | 12/12 | 4/4 | 0 | −75.18 dBFS |
| **Combined** | **140** | **140/140** | **36/36** | **0** | |

To make all Harbor B-minor gestures playable on separately recorded strings, the **optional** Q2 voicer rearranges 8 existing B-minor chord inversions (24 note pitches change, preserving the chord's pitch-class multiset). Silver did not require revoicing. This is **not** a default song edit. Guitar string identity and selected recording take matched exactly between the two codec tiers, not merely at the same pitch.

Both complete guitar stems rendered, stayed finite, and retained the WAV's distinct channels. WAV/OGG comparison excerpts were **11 seconds** per style, RMS-matched to less than 0.5 dB, MP3 encoded and decoded in CI. The guitar's original source side energy is relatively quiet: stereo source availability alone is not a guarantee of a wider-sounding guitar.

## Protected contracts

- Prior note attack, duration, velocity and independent same-pitch release tails remained intact in the playback fixtures.
- The newly added test for a long ringing guitar note plus a shorter same-pitch pluck passed with both physical source mapping and stereo WAV enabled.
- Guitar string selection did not modify **any piano note or recorded piano waveform**, even when the independent piano source was also rendered as stereo WAV.
- Different codec extensions/install locations did not alter selected **physical string, pitch, velocity layer or performed take**.
- The original OGG default remains unmodified. Existing stereo WAV sources and scores remain read-only.

## Files and reproduction

- `tests/test_combined_sources_q4.py` — small licensed-asset-independent stereo/mono playback and repluck fixtures.
- `tools/verify_string_stereo_q4.py` — full guitar-score source-selection/technical A/B.
- `.github/workflows/q3-stereo-source-playback.yml` — reuses the same publisher WAV/OGG download and provenance checks as Q3; no duplicate 1.8 GB download pipeline.

The `q4` filenames are historical internal labels for this cross-feature check; **roadmap item Q4 remains continuous-instrument expression**, and this completed task is recorded as **Q3.1**.

**Limits:** These are objective audio engineering checks of source identity, PCM/MP3 integrity and performance continuity, not proof of musical naturalness or an artistic preference for the stereo recordings. The stronger piano stereo information reported in [Q3](Q3_SOURCE_FIDELITY_RESULTS.md) does not make the comparatively narrow guitar WAV examples an automatic upgrade.

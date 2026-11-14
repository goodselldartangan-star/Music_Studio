# Q3 — Original stereo WAV source recordings versus mono OGG previews

**Scope:** preserve original recorded-instrument spatial information without changing notes, harmony, string mapping, the old sampler, effects or published music. The original OGG source tier remains the default.

## Evidence: verified publisher archives

The [official Meta Open Sound GitHub releases](https://github.com/facebookincubator/Meta-open-sound/releases) provide paired recordings. The [successful independent Q3 comparison](https://github.com/goodselldartangan-star/Music_Studio/actions/runs/43513020178) confirmed all expected filenames and matched 36 source waveforms by exact pitch, velocity, physical string and take identity.

| Source | OGG files / WAV files | OGG ZIP size | WAV ZIP size | Paired sample channels | Candidate same takes |
|---|---:|---:|---:|---|---:|
| Steel acoustic guitar | 375 / 375 | 25,440,465 B | 663,385,210 B | OGG mono / WAV stereo | 12/12 |
| Upright piano | 352 / 352 | 48,182,366 B | 752,311,261 B | OGG mono / WAV stereo | 12/12 |
| Nylon guitar | 348 / 348 | 16,483,193 B | 423,127,309 B | OGG mono / WAV stereo | 12/12 |
| **Total** | **1,075 / 1,075** | **90,106,024 B** | **1,838,823,780 B** | | **36/36** |

Every inspected WAV sample was 24-bit PCM at 48 kHz, with two channels. Every inspected OGG was mono at 48 kHz. The selected waveform similarities after WAV downmixing exceeded 0.99, consistent with the same performed takes. An original stereo source **can** contain spatial information impossible to recover from mono OGG, but dual channels and lossless encoding alone do **not** prove better musical sound.

The WAV ZIPs require about **20.4 times the compressed download/storage space** of the OGG ZIPs. Engine-side resampling to 44.1 kHz, decoding/caching, and the existing separate PCM note-release envelope remain possible.

## Important source-provenance event

On November 12, 2026 the publisher replaced the *piano OGG* asset under the same release tag. Its newly declared GitHub asset digest is SHA256 **6a021b55...d6639b58**; the previously pinned release had SHA256 **4ba8095f...3145e1c35d40**. The existing installer correctly rejected the newly published archive. Music Studio now explicitly accepts both verified digests and records which content was installed; it never treats any arbitrary change as safe.

The original stereo WAV archives are separately bound to exact publisher asset sizes and SHA256 values by the Q3 installer, and are extracted into a new folder only. No released MP3 or archived user-approved sound is replaced.

## Optional engine implementation

- New independent stereo renderer: **studio7/stereo_wav_q3.py** decodes and retunes left and right channels together, then applies the existing guitar/piano note-release envelope **independently** to each channel.
- Original steel/piano SourceBank and nylon Collection still own pitch, velocity and deterministic take/string selection. The optional WAV branch uses those same regions; overlapping same-pitch notes sum independently rather than stealing a voice.
- CLI: **--assets assets/v7 --wav-source-root assets/q3-stereo-wav** (optional **--guitar-string-mapping**). The GM fallback cannot silently enable WAV-source playback.
- The WAV installer **tools/install_wav_q3.py** refuses existing destinations, non-stereo files, non-24-bit sources, unexpected publisher hashes, unsafe archive members, and mismatched sample counts.
- The A/B builder **tools/compare_stereo_wav_q3.py** renders short, matched-level piano, steel and nylon phrases using original note selection, with MP3 outputs and reported recorded stereo-side energy.

## Test status

- Local isolated WAV/OGG pairing, stereo note/repluck and installer fixtures: **10/10 passed**.
- [Real paired archive research](https://github.com/goodselldartangan-star/Music_Studio/actions/runs/43513020178): **passed**, all three collections.
- [Completed Q3 stereo integration](https://github.com/goodselldartangan-star/Music_Studio/actions/runs/43532042435): **33 tests passed**, both workflow jobs succeeded, and the publisher-source stereo/mono A/B recordings were MP3-decode verified.

## Decision boundary

Q3 is not complete merely because lossless WAV exists. Accept only after full real-source MP3 decoding, preserved older OGG behavior, a measurable stereo/mono difference, and a clean published-source integrity report. Even then, **whether the stereo masters are preferred musically requires listening**, so the optional WAV flag should remain opt-in and original outputs remain preserved. Q4 continuous-instrument expressivity is next only after this engineering gate.

## Confirmed Q3 real-audio comparison (November 13, 2026)

The latest successful job generated short, matched-note comparisons with **identical source takes**, not different performances. Correlation of WAV downmix versus OGG mono mid is high but does not itself prove preference.

| Isolated phrase | Original mono OGG side (dBFS) | Stereo WAV side (dBFS) | RMS matching difference (dB) | Mid correlation |
|---|---:|---:|---:|---:|
| Steel guitar | −240 (effectively 0) | −70.27 | 0.000 | 0.99990 |
| Piano | −240 (effectively 0) | −38.96 | +0.321 | 0.99989 |
| Nylon guitar | −240 (effectively 0) | −69.99 | 0.000 | 0.99981 |

**Interpretation:** the stereo piano source retains significantly more measured side information than the two guitar examples. These are short selected takes, not comprehensive perceptual or music-quality tests. The originals were not overwritten. Technical Q3 acceptance is complete; the preferred sound is still an artistic choice.

**Next Q4 integration:** test *Q2 physical guitar-string mapping plus Q3 24-bit stereo WAV playback together* on full scored guitar parts and independent repeated-note tails, without touching other instruments or default rendering.

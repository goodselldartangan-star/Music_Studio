# Q4.2 — Recorded guitar/bass source audit and stopped-string proof

**Status:** Source inventory and **one narrow guitar release technique** passed offline engineering gates. **Not enabled by default; not a source-recorded palm mute, bass slide or musical preference verdict.**

## What the original licensed sources actually contain

[Source-articulation inventory CI](https://github.com/goodselldartangan-star/Music_Studio/actions/runs/45943940787) verified the publisher's original Git blob identities of the two Meta guitar manifests and three FreePats SFZ maps, then inspected the actual released SF2 files with a read-only RIFF/pdta parser. **Five unit tests passed.**

| Source bank | Exact inventory | Source-defined expression | Named muted/slide sample zones |
|---|---:|---|---|
| Meta CC0 steel acoustic | **375** recorded attacks, **125** string-pitch positions | 6 physical strings × 3 velocity layers | None found in labels |
| Meta CC0 nylon acoustic | **348** recorded attacks, **116** string-pitch positions | Fingerstyle soft; light/firm picked | None found in labels |
| FreePats CC0 clean electric, small SF2 | **13** sample headers / 13 SFZ note regions | Looped lower registers, release settings | None found in names |
| FreePats CC0 finger bass SF2 | **12** sample headers / 12 SFZ note regions | Finger-plucked pitched sample regions | None found in names |
| FreePats CC0 picked bass SF2 | **13** sample headers / 13 SFZ note regions | Picked pitched sample regions | None found in names |

**Interpretation:** Those sources do **not expose dedicated named palm-muted, hammer-on or sliding sample zones**. This is NOT proof that the source recordings contain no incidental finger/fret/string noise or that other libraries have none. A shorter MIDI note or pitch-bent single sample cannot truthfully be described as a sampled palm-mute/slide articulation.

## One isolated enhancement: a controlled post-pluck string stop

- [`studio7/guitar_damping_q42.py`](../studio7/guitar_damping_q42.py) contains the DSP and a pure optional score-copy annotator, separate from all piano, bass and other effects.
- `shape_harbor_stopped_upstrokes` marks **6 selected Harbor upstrokes** (**24 acoustic note events**). It does not change **pitch, attack time, duration, velocity or any other instrument**.
- In the recorded guitar sampler, only explicitly `technique="stopped_string_release"`-tagged notes get **a raised-cosine stop beginning 240 ms after each recorded attack and fading to zero over 42 ms**. The initial recording is bit-for-bit intact before that point.
- Damping applies to the **individual note's PCM**, never to the whole guitar bus, so a newer short stopped note cannot shorten an older ringing voice. The existing Q2 distinct-physical-string sample assignment and Q2 Harbor B-minor inversion remain identical in both A/B variants.
- The original guitar-bank selection, existing engine defaults and all previously published songs are unchanged. Do not call this a new muted sample or a true *palm-muted attack*.

### Reproducible technical evidence

[Isolated original 375-recording test](https://github.com/goodselldartangan-star/Music_Studio/actions/runs/45944126899) passed **6 focused tests**, publisher original archive checksum, complete guitar source loading, no old-note voice stealing, MP3 decode and RMS matching. The source guitar introduction was byte-identical; full-duration source waveform difference RMS **0.00162609**. Both 12-second isolated excerpts were **−38.134 dBFS RMS**.

[Complete recorded-instrument Harbor test](https://github.com/goodselldartangan-star/Music_Studio/actions/runs/45944285311) passed **6 focused tests** plus full-source MP3 checks. Both versions used genuine CC0 Meta guitar/piano, FreePats CC0 bass/electric and MuldjordKit CC BY 4.0 drums. The **same** optional Q2 Harbor guitar voicing/string assignment was applied before making the two variants.

| Full recorded-band A/B, 17.5–29.5 seconds | Original string ring | Selected stopped upstrokes |
|---|---:|---:|
| Level-matched excerpt RMS | **−19.752 dBFS** | **−19.752 dBFS** |
| Excerpt PCM peak | 0.816677 | 0.820000 |
| Recorded non-acoustic stems | Identical | Identical |

- Actual recorded guitar source change RMS: **0.00162609**; entire master waveform difference RMS: **0.00854907**, so the change survives mixing.
- The pre-stem-normalization guitar intro PCM was **exactly identical**. The post-processing guitar intro can acquire a tiny global level change because the current mixer sets target RMS across the **whole stem**. Do not mislabel the processed full mix as intro-bit-identical.
- The comparisons use explicit *preview-only* level matching (new version ×1.00407, then common headroom ×0.97223). This does not rewrite real mixer settings, historical masters or scores.
- Both preview MP3s decoded successfully. Tests establish technical playback and isolated signal changes, **not** a listener's preferred timbre.

## Remaining priority

**Next, and only after this guitar stage:** investigate **bass connected articulation** separately. The exact finger/pick SF2 labels contain no named slide or hammer-on samples, so first quantify real note transition problems and the sample/bend limitations; do not add automatic glissandos or extra fake fret noises. Keep bass articulation out of the guitar code and avoid changing the default player until an isolated recorded-source A/B solves a measurable issue.

### Source attribution

Meta Open Sound guitar/piano: **CC0 1.0**. FreePats finger/picked bass and clean electric guitar: **CC0 1.0**. MuldjordKit: **CC BY 4.0**. The CI artifacts contain only **derived short MP3 examples and JSON technical reports**; they do not redistribute the original instrument archives.

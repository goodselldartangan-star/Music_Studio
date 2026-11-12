# Q2 — Physically coherent recorded-guitar source strings

**Quality-review engineering result:** Optional guitar source-string assignment passed the isolated and full recorded-instrument checks. This is not a claim that the new voicing *sounds* artistically preferable. Original v7 scores and published MP3s remain intact.

## The audible-risk hypothesis, measured against publisher recordings

The original steel and nylon sample players chose a sample for each note independently. Because the same MIDI pitch is available from several guitar strings, one strum could use two distinct pitched recordings sourced from the **same physical string**. The old steel sample selector also includes note onset in its take hash, so nudging strum timing can unexpectedly change the selected string and timbre.

Read-only audit with the pinned Meta CC0 libraries:
- **Harbor:** 24 of 32 guitar strums contained a repeated physical string, totaling 32 excess same-strum string occupancies.
- **Silver:** 2 of 4 strums contained a repeated physical string, totaling 2 excess occupancies.

The underlying scored pitches were musically valid; it was the mapping from pitched notes to individually sampled physical strings that caused the mismatch.

## Opt-in, note-tail-preserving correction

`studio7/string_mapping.py::plan_guitar_samples` chooses source files for each already-authored 3–6-note ascending/descending stroke, requiring distinct and physically ordered guitar strings when the library has the corresponding pitches and velocity layers. The deterministic selection of other notes does **not** hash start time or duration. On a mapping failure, notes are retained using a documented fallback rather than dropped.

Exactly eight recurring Harbor B-minor strums were impossible to map on distinct recorded strings with the originally scored four-note pitch group `[47, 50, 54, 59]` (B2 D3 F♯3 B3). The sample bank's B2 was recorded on the A string alone. An **optional, targeted guitar-only chord inversion** replaces those ascending pitches with `[47, 54, 59, 62]` (B2 F♯3 B3 D4), or reverse for upstrokes. It retains B-minor chord pitch classes, four string attacks, event times, velocities, lengths and the piano, bass, lead and drum performances. The change affects eight strums (24 assigned note pitches); it does not rewrite the source harmony or generalize to other chords.

The existing note renderer and nylon collection now accept optional explicit source regions, while their original selection paths remain the defaults. CLI: `demo_v7.py --guitar-string-mapping`. Separate `-q2-strings` output filenames and metadata prevent overwriting historical masters.

**With the optional string planner and targeted B-minor inversion, all 36 of the current sketches' guitar strums map to distinct recorded strings: Harbor 32/32, Silver 4/4. Zero within-strum string conflicts remain.** Previously sounding note tails are not truncated, including repeated same-pitch plucks.

## Reproducible acceptance

- [Focused Q2 GitHub test and real-source comparison](https://github.com/goodselldartangan-star/Music_Studio/actions/runs/43158225482) **passed 12 tests**, exact source-file mapping checks, and isolated recordings made from the original licensed steel/nylon guitar files. All 36 chord assignments were verified as distinct.
- Controlled **RMS-level matched, short, fade-edged guitar A/B MP3s** were rendered and MP3-decode-tested by that run. Both comparisons have **0.0 dB reported RMS level difference**, measurable PCM waveform difference, and remain in GitHub Actions artifacts. They were **not** presented as listener-approved or released masters.
- [Full source-library integration on GitHub](https://github.com/goodselldartangan-star/Music_Studio/actions/runs/43158084194) **passed** its tests, original recordings and independent full **Harbor** and **Silver** Q2 builds using the actual CC0 instruments and conventional licensed drums/SoundFonts. The Q2 verification step and historical release-preservation publishing step both succeeded.

## Scope and limitations

This is a **source-string-selection model**, not a continuous physically simulated fretboard. It does not introduce muting when a later pluck uses a string already ringing from a previous gesture; preserving independent overlapping notes was an explicit user requirement. New or unusual scores can still lack a distinct-string assignment, in which case the planner reports its fallback instead of silently cutting notes.

The optional chord inversion and a string-specific sample timbre may sound different. Technical plausibility and correct stereo decoding do **not** establish subjective sound quality or a preferred guitar arrangement. The old playback remains the default. A future focused listening choice can compare the isolated level-matched A/B if that becomes relevant; no listener involvement is needed to verify the mapping.

Next isolated research candidate: compare Meta's source-quality 24-bit WAV recordings with the pinned mono OGG preview tier on identical notes, preserving provenance and not implying a guaranteed audible difference.

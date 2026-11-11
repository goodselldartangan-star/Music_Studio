# Music Studio v3: Design choices and measured gates

## Reference study (private audio stays outside repository)

Three reference MP3s were decoded locally with ffmpeg. Representative 12-second excerpts were compared using windowed PSD (Welch) and RMS in four bands. Median low-bass (35–150 Hz) spectral-energy ratios were 0.54, 0.54, 0.54 in the supplied recordings and 0.61 in the earlier *Porchlight Receiver*. In comparable excerpts the new song has more controlled low bass, while bright hats and shaker improve treble articulation. Statistics are sensitive to exact section selections, genre and mastering, so are directional rather than absolute targets.

Stereo correlation on three selected 8-second sections of each reference was ~0.73–0.93; v2 was ~0.986. v3 first-28-second correlation is ~0.868 after band-limited side widening. Tested full v3: 3:34.525 WAV, 2899 notes, 1506 drum events, −14.0 LUFS, 11.6 LU LRA, −1.7 dBTP WAV / −1.5 dBTP decoded MP3. Reference songs' melodies, lyrics, recordings, and voices are not used.

## Changes from v2

- One 25k-character script split into modules with one-way imports and short, predictable inputs/outputs. No need to copy a whole arrangement to change the bass synthesizer or drummer.
- A new songbook in B minor (moving through relative D major), with two verses, rise, first chorus, instrumental break, bridge and expanded second chorus. The lead performs an original repeated eight-bar motif with contrasting phrasing.
- Karplus–Strong/digital-waveguide plucks, additive-bandlimited synth timbres, filtered-noise cymbals and drum transient variation. Fixed random seeds make renders reproducible.
- Separate bass, drums, guitar, keys and lead buses with independent filtering, gentle kick ducking, stereo delay/reverb and highpassed widening. Two-times-oversampled saturation limits aliasing.
- Strict full/preview quality checks use playable MIDI, stereo 24-bit PCM, decoded MP3, section RMS contrast, sample and true peaks, LUFS/LRA, channel balance, phase correlation, and fade tails.
- No paid generation API or non-OpenAI model. Works with local DSP libraries and FFmpeg.

## Relevant technical references

- Julius O. Smith, *Sound synthesis based on physical models* (CIRMMT lecture): https://www.cirmmt.org/en/events/distinguished-lectures/Smith/smith-slides
- Review of string instrument synthesis methods (2026): https://doi.org/10.5334/tismir.267
- Frühauf, Kopiez and Platz, *Music on the timing grid* (2013): https://doi.org/10.1177/1029864913486793
- FFmpeg audio filters, EBU R128 and true-peak measurement: https://ffmpeg.org/ffmpeg-filters.html#ebur128-1
- SciPy digital filters and resample_poly documentation: https://docs.scipy.org/doc/scipy/reference/signal.html

Only high-level techniques were studied; algorithms were implemented from scratch with the above named licensed dependencies. Quality measurements do **not** constitute a subjective human listening evaluation.

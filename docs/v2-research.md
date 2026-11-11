# Music Studio v2 — research, implementation, and evidence

November 2026. Original offline Python implementation. **No third-party AI, samples, soundfonts, accounts, or API keys are used.**

## What was studied

1. **Plucked-string physical modeling.** [CMU Intro to Computer Music, §12.1](https://www.cs.cmu.edu/~15322/book/ch12/01.html) and [Digital Waveguides in Python](https://ringbuffer.org/sound_synthesis_introduction/Physical_Modeling/waveguides_python/) describe the Karplus–Strong/digital-waveguide family. `studio_v2.py` uses its own fractional-delay feedback implementation with deterministic noise excitation and pick-position filtering. No third-party implementation is pasted into the repository.
2. **Preventing nonlinear aliasing.** [SciPy `resample_poly`](https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.resample_poly.html) provides filtered polyphase resampling; the renderer uses 2× oversampling around mild saturation. A synthetic 8 kHz sine experiment with aggressive nonlinear drive reduced a third-harmonic alias at approximately 20.1 kHz by **19.6 dB** compared with non-oversampled saturation. This is one example, not a guarantee about all frequencies.
3. **Loudness and true peak.** [ITU-R BS.1770-5](https://www.itu.int/rec/R-REC-BS.1770/en) defines the measurement approach. [FFmpeg `ebur128`](https://ffmpeg.org/ffmpeg-filters.html#ebur128-1) provides integrated loudness, loudness range, and estimated true peak. Distinguish *sample peak* from *true peak*.
4. **Arrangement and groove.** Use an explicitly authored lead motif with repetition/development, constrained accent/velocity/timing variation, contrast among sections, tasteful silence, and independent bass/drum/keys/lead mixes. Randomness affects tiny performance details, not the melody's harmonic intent.
5. **Relative listening references.** The three user-provided MP3s informed only broad musical direction: plucked rhythms, bass groove, dynamic build and electronic atmosphere. They were not copied, uploaded, sampled, or added to this repository.

## Keep, change, remove from active workflow

- **Keep:** MIDI export, explicit editable score JSON, deterministic seeds, offline rendering, FFmpeg exports, automated QA, original composition.
- **Change:** add a reusable physical-model pluck, expressive lead/sustain, bounded groove timing variations, composition transpose/tempo/seed controls, individual bus equalization, 2× oversampled soft saturation, true-peak and LUFS tests.
- **Remove from the default workflow:** paid GPT/ElevenLabs APIs, hardcoded-only performance variants, a single aggressive global presence boost, and publishing files that fail QA. Historical source is preserved.

## Testing gates

1. Unit tests validate form, chord vocabulary, motivic recurrence, MIDI, deterministic variations and parameter validation.
2. DSP tests ensure every sound renders finite data, plucked-string tunings are within 10 cents for four test notes, decay is plausible, drum variations are reproducible, and the alias test improves by more than 10 dB.
3. Preview render (`--preview-bars 8`) is run before the complete production render, including an alternative 103 BPM / −3-semitone configuration.
4. Full render must pass `quality_v2.py`: valid 24-bit stereo WAV, MIDI, MP3 full decode, correct duration, no clipping, sufficient level, low rumble, stereo balance, ending fade, required sections and chorus lift, LUFS/LRA/true-peak limits.
5. GitHub Actions runs the unit tests **before** rendering; releases are updated only after all quality gates succeed.

## Current sample result

**Porchlight Receiver**, instrumental, 114 BPM, 88 bars, **3:08.76**, 2,432 pitched notes and 1,235 drum events. Local WAV measurement: **−13.8 LUFS**, **14.0 LU loudness range**, **−1.6 dBTP true peak**, **−0.17 dB channel balance**. The final chorus is about 3.2 dB RMS above the first verse. Its dynamic range is wider than the reference songs, a stylistic choice for a more spacious instrumental—not conclusive proof of improved musical quality.

## Boundaries and next research

- These tests establish output correctness and signal quality, **not human preference or a critical listening audition**. No claim is made that a model has heard and enjoyed the music.
- The digital-waveguide pluck is a **simple approximation**, not the same as a recorded acoustic guitar. Further research: pick/bow interaction, sympathetic strings, dispersion, cabinet resonances and transient variation. Avoid copied proprietary samples.
- The current piano and percussion remain synthetic. Further possible improvements include zero-cost curated CC0 samples **only if licensing/provenance is verified**, otherwise continue developing local synthesis.
- Tempo, transposition and deterministic variation are configurable. The sample's melody and section structure are authored, rather than algorithmically inferred from outside AI.
- High-memory use in the current full render (~0.9 GB peak locally) can be improved with chunked stem streaming in a later revision.
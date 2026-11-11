# Music Studio v6: recorded instruments and real performance differences

The previous three demos shared a repeating synth arrangement with different mix profiles. This experiment addresses the problem at the source: **real recordings for each exposed instrument and independently composed rhythmic parts**.

## Source libraries (verified at original publishers)

- [Meta Open Sound](https://github.com/facebookincubator/Meta-open-sound): steel-string acoustic guitar (375 samples, 3 velocities), upright piano (352, 4 velocities), **CC0-1.0**.
- [FreePats FSBS Clean Electric Guitar](https://freepats.zenvoid.org/ElectricGuitar/clean-electric-guitar.html): sampled Fender clean guitar, **CC0-1.0**. Uses the compact SF2 package (~6.6 MB).
- [FreePats Bass Guitar YR](https://freepats.zenvoid.org/ElectricGuitar/clean-electric-bass.html): recorded Yamaha bass, finger articulation, **CC0-1.0**, compact SF2 (~2.6 MB).
- [FreePats MuldjordKit](https://freepats.zenvoid.org/Percussion/acoustic-drum-kit.html): acoustic kick/snare/hi-hat/cymbals with dynamic layers, **CC BY 4.0**, SF2 (~55 MB). **Credit required: 'Drum samples provided by DrumGizmo.org.'**

No other generative AI, model download, credential, or paid music API is involved. Regular open-source audio tools (FluidSynth, FFmpeg, NumPy, SoundFile) are not generative AI models.

## Playback architecture

- `studio6/score.py` — stable score contract and three separately authored short compositions. Natural silence, syncopated bass, idiomatic guitar strums, sustained lead answers.
- `studio6/soundfonts.py` — small FluidSynth wrapper, note/preset selection, MIDI scheduling, independent waveform output.
- `studio6/render.py` — routes Meta recorded guitar and piano to the existing `SampleBank`, FreePats sampled guitar, bass and drums through SF2, and writes isolated stems and a conservatively mastered MP3.
- `studio6/qa.py`, `studio6/verify.py` — decode, duration, levels, stereo, minimum activity and sample-source provenance.
- `tools/install_soundfonts.py` — extracts original release files and records SHA-256 and license identifiers without committing large sample binaries.

## Demos

- **Porch Radio:** G major / E minor at 106 BPM, finger-strummed acoustic guitar and warm bass in a quieter, organic pocket.
- **Street Corner:** A minor at 122 BPM, tightly rhythmic clean electric guitar, syncopated bass, full backbeat, electric guitar hook.
- **Last Window:** D minor / F major at 98 BPM, exposed upright piano with acoustic guitar replies, restrained percussion and a later build.

Each is 12 bars plus a short natural ending, approximately 26–31 seconds. They are **not** three mixes of the same score. References were used for broad production goals; no reference master/voice/melody is included.

## Local use

Obtain the five official archives from their publisher GitHub releases (done by GitHub Actions automatically), unpack Meta through `tools/install_cc0.py` and FreePats through `tools/install_soundfonts.py`, then:

```bash
python -m unittest discover -s tests -v
python -m studio6.render --assets assets/v6 --out v6-demos
python -m studio6.verify --assets assets/v6 --out v6-demos
```

No source file of Music Studio v5 or earlier is overwritten. Test fixtures are not release audio. Audio QA confirms technical properties, not whether a listener considers an instrument emotionally compelling.
